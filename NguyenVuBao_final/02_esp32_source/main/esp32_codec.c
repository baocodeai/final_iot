#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "driver/uart.h"
#include "esp_crc.h"
#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_jpeg_enc.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "sdkconfig.h"
#if CONFIG_SPIRAM
#include "esp_psram.h"
#endif
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "tinycae_runner.h"

#define HOST_UART UART_NUM_0
#define HOST_UART_BAUD_RATE 115200
#define HOST_UART_RX_BUFFER_SIZE 1024
#define COMMAND_BUFFER_SIZE 64
#define IMAGE_RAW_SIZE 3072
#define PAYLOAD_TIMEOUT_MS 5000
#define JPEG_OUTPUT_BUFFER_SIZE 8192

static const char *TAG = "esp32_codec";
static uint8_t image_buffer[IMAGE_RAW_SIZE] __attribute__((aligned(16)));
static uint8_t *jpeg_output_buffer;
static jpeg_enc_handle_t jpeg_encoder;
static int8_t tinycae_latent[TINYCAE_LATENT_BYTES] __attribute__((aligned(16)));

static void send_text(const char *text)
{
    uart_write_bytes(HOST_UART, text, strlen(text));
}

static bool receive_exact(uint8_t *buffer, size_t size)
{
    size_t total_received = 0;

    while (total_received < size) {
        const int received = uart_read_bytes(
            HOST_UART,
            buffer + total_received,
            size - total_received,
            pdMS_TO_TICKS(PAYLOAD_TIMEOUT_MS));

        if (received <= 0) {
            return false;
        }

        total_received += (size_t)received;
    }

    return true;
}

static bool receive_image(void)
{
    char response[32];
    snprintf(response, sizeof(response), "READY %u\r\n", IMAGE_RAW_SIZE);
    send_text(response);

    if (!receive_exact(image_buffer, IMAGE_RAW_SIZE)) {
        send_text("ERROR PAYLOAD_TIMEOUT\r\n");
        return false;
    }

    return true;
}

static bool receive_image_and_send_crc(void)
{
    char response[48];

    if (!receive_image()) {
        return false;
    }

    const uint32_t crc = esp_crc32_le(0, image_buffer, IMAGE_RAW_SIZE);
    snprintf(
        response,
        sizeof(response),
        "CRC32 %08" PRIX32 "\r\n",
        crc);
    send_text(response);
    return true;
}

static bool initialize_jpeg_encoder(void)
{
    jpeg_enc_config_t config = DEFAULT_JPEG_ENC_CONFIG();
    config.width = 32;
    config.height = 32;
    config.src_type = JPEG_PIXEL_FORMAT_RGB888;
    config.subsampling = JPEG_SUBSAMPLE_444;
    config.quality = 50;
    config.rotate = JPEG_ROTATE_0D;
    config.task_enable = false;

    jpeg_output_buffer = heap_caps_malloc(
        JPEG_OUTPUT_BUFFER_SIZE,
        MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (jpeg_output_buffer == NULL) {
        ESP_LOGE(TAG, "Failed to allocate JPEG output buffer in PSRAM");
        return false;
    }

    const jpeg_error_t result = jpeg_enc_open(&config, &jpeg_encoder);
    if (result != JPEG_ERR_OK) {
        ESP_LOGE(TAG, "jpeg_enc_open failed: %d", result);
        heap_caps_free(jpeg_output_buffer);
        jpeg_output_buffer = NULL;
        return false;
    }

    ESP_LOGI(
        TAG,
        "JPEG encoder ready: RGB888 32x32, 4:4:4, output buffer %u bytes",
        JPEG_OUTPUT_BUFFER_SIZE);
    return true;
}

static bool receive_image_encode_and_send_jpeg(int quality)
{
    char response[96];

    if (jpeg_encoder == NULL || jpeg_output_buffer == NULL) {
        send_text("ERROR JPEG_NOT_READY\r\n");
        return false;
    }

    if (quality < 1 || quality > 100) {
        send_text("ERROR JPEG_QUALITY\r\n");
        return false;
    }

    if (!receive_image()) {
        return false;
    }

    jpeg_error_t result = jpeg_enc_set_quality(jpeg_encoder, (uint8_t)quality);
    if (result != JPEG_ERR_OK) {
        snprintf(response, sizeof(response), "ERROR JPEG_QUALITY %d\r\n", result);
        send_text(response);
        return false;
    }

    int jpeg_size = 0;
    const int64_t start_us = esp_timer_get_time();
    result = jpeg_enc_process(
        jpeg_encoder,
        image_buffer,
        IMAGE_RAW_SIZE,
        jpeg_output_buffer,
        JPEG_OUTPUT_BUFFER_SIZE,
        &jpeg_size);
    const int64_t elapsed_us = esp_timer_get_time() - start_us;

    if (result != JPEG_ERR_OK || jpeg_size <= 0) {
        snprintf(response, sizeof(response), "ERROR JPEG_ENCODE %d\r\n", result);
        send_text(response);
        return false;
    }

    const uint32_t crc = esp_crc32_le(0, jpeg_output_buffer, jpeg_size);
    snprintf(
        response,
        sizeof(response),
        "JPEG %d %08" PRIX32 " %" PRId64 "\r\n",
        jpeg_size,
        crc,
        elapsed_us);
    send_text(response);
    uart_write_bytes(HOST_UART, jpeg_output_buffer, jpeg_size);
    return true;
}

static bool receive_image_encode_and_send_tinycae(void)
{
    char response[96];

    if (!receive_image()) {
        return false;
    }

    int64_t elapsed_us = 0;
    if (!tinycae_encode(
            image_buffer,
            tinycae_latent,
            TINYCAE_LATENT_BYTES,
            &elapsed_us)) {
        send_text("ERROR TINYCAE_INVOKE\r\n");
        return false;
    }

    const uint32_t crc = esp_crc32_le(
        0,
        (const uint8_t *)tinycae_latent,
        TINYCAE_LATENT_BYTES);
    snprintf(
        response,
        sizeof(response),
        "LATENT %u %08" PRIX32 " %" PRId64 "\r\n",
        TINYCAE_LATENT_BYTES,
        crc,
        elapsed_us);
    send_text(response);
    uart_write_bytes(HOST_UART, tinycae_latent, TINYCAE_LATENT_BYTES);
    return true;
}

static void send_memory_status(void)
{
    char response[192];
    const uint32_t internal_caps = MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT;
    const uint32_t psram_caps = MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT;

    snprintf(
        response,
        sizeof(response),
        "MEM INTERNAL_FREE %u INTERNAL_MIN %u INTERNAL_LARGEST %u "
        "PSRAM_FREE %u PSRAM_MIN %u PSRAM_LARGEST %u\r\n",
        (unsigned int)heap_caps_get_free_size(internal_caps),
        (unsigned int)heap_caps_get_minimum_free_size(internal_caps),
        (unsigned int)heap_caps_get_largest_free_block(internal_caps),
        (unsigned int)heap_caps_get_free_size(psram_caps),
        (unsigned int)heap_caps_get_minimum_free_size(psram_caps),
        (unsigned int)heap_caps_get_largest_free_block(psram_caps));
    send_text(response);
}

void app_main(void)
{
    const uart_config_t uart_config = {
        .baud_rate = HOST_UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    ESP_ERROR_CHECK(uart_driver_install(
        HOST_UART,
        HOST_UART_RX_BUFFER_SIZE,
        0,
        0,
        NULL,
        0));
    ESP_ERROR_CHECK(uart_param_config(HOST_UART, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(
        HOST_UART,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE));

#if CONFIG_SPIRAM
    if (esp_psram_is_initialized()) {
        ESP_LOGI(
            TAG,
            "PSRAM initialized: %u bytes",
            (unsigned int)esp_psram_get_size());
    } else {
        ESP_LOGW(TAG, "PSRAM support enabled but no PSRAM was initialized");
    }
#else
    ESP_LOGW(TAG, "PSRAM support is disabled in sdkconfig");
#endif

    ESP_LOGI(TAG, "UART PING-PONG ready at %d baud", HOST_UART_BAUD_RATE);
    initialize_jpeg_encoder();
    if (!tinycae_initialize()) {
        ESP_LOGE(TAG, "TinyCAE initialization failed");
    }
    send_text("READY\r\n");

    char command[COMMAND_BUFFER_SIZE] = {0};
    size_t command_length = 0;

    while (true) {
        uint8_t byte = 0;
        const int received = uart_read_bytes(
            HOST_UART,
            &byte,
            1,
            portMAX_DELAY);

        if (received != 1) {
            continue;
        }

        if (byte == '\r') {
            continue;
        }

        if (byte == '\n') {
            if (command_length == 0) {
                continue;
            }

            command[command_length] = '\0';

            if (strcmp(command, "PING") == 0) {
                send_text("PONG\r\n");
            } else if (strcmp(command, "IMAGE_CRC") == 0) {
                receive_image_and_send_crc();
            } else if (strncmp(command, "JPEG ", 5) == 0) {
                int quality = 0;
                if (sscanf(command + 5, "%d", &quality) == 1) {
                    receive_image_encode_and_send_jpeg(quality);
                } else {
                    send_text("ERROR JPEG_COMMAND\r\n");
                }
            } else if (strcmp(command, "TINYCAE") == 0) {
                receive_image_encode_and_send_tinycae();
            } else if (strcmp(command, "STATUS") == 0) {
                send_memory_status();
            } else {
                send_text("ERROR UNKNOWN_COMMAND\r\n");
            }

            command_length = 0;
            continue;
        }

        if (command_length < COMMAND_BUFFER_SIZE - 1) {
            command[command_length++] = (char)byte;
        } else {
            command_length = 0;
            send_text("ERROR COMMAND_TOO_LONG\r\n");
        }
    }
}
