#include "tinycae_runner.h"

#include <cmath>
#include <cstring>
#include <new>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

namespace {

constexpr size_t kTensorArenaSize = 128 * 1024;
constexpr int kInputHeight = 32;
constexpr int kInputWidth = 32;
constexpr int kInputChannels = 3;
constexpr int kLatentHeight = 8;
constexpr int kLatentWidth = 8;
constexpr int kLatentChannels = 16;

const char *kTag = "tinycae";
const tflite::Model *g_model = nullptr;
tflite::MicroInterpreter *g_interpreter = nullptr;
TfLiteTensor *g_input = nullptr;
TfLiteTensor *g_output = nullptr;
uint8_t *g_tensor_arena = nullptr;

extern const uint8_t encoder_int8_tflite_start[]
    asm("_binary_encoder_int8_tflite_start");
extern const uint8_t encoder_int8_tflite_end[]
    asm("_binary_encoder_int8_tflite_end");

bool tensor_shape_is(
    const TfLiteTensor *tensor,
    int dimension_0,
    int dimension_1,
    int dimension_2,
    int dimension_3)
{
    return tensor != nullptr && tensor->dims != nullptr &&
           tensor->dims->size == 4 && tensor->dims->data[0] == dimension_0 &&
           tensor->dims->data[1] == dimension_1 &&
           tensor->dims->data[2] == dimension_2 &&
           tensor->dims->data[3] == dimension_3;
}

}  // namespace

extern "C" bool tinycae_initialize(void)
{
    if (g_interpreter != nullptr) {
        return true;
    }

    const size_t model_size =
        static_cast<size_t>(encoder_int8_tflite_end - encoder_int8_tflite_start);
    g_model = tflite::GetModel(encoder_int8_tflite_start);
    if (g_model == nullptr || g_model->version() != TFLITE_SCHEMA_VERSION) {
        ESP_LOGE(
            kTag,
            "Model schema mismatch: model=%d runtime=%d",
            g_model == nullptr ? -1 : g_model->version(),
            TFLITE_SCHEMA_VERSION);
        return false;
    }

    static tflite::MicroMutableOpResolver<2> resolver;
    if (resolver.AddConv2D() != kTfLiteOk ||
        resolver.AddDepthwiseConv2D() != kTfLiteOk) {
        ESP_LOGE(kTag, "Failed to register TinyCAE operators");
        return false;
    }

    g_tensor_arena = static_cast<uint8_t *>(heap_caps_aligned_alloc(
        16,
        kTensorArenaSize,
        MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    if (g_tensor_arena == nullptr) {
        ESP_LOGE(kTag, "Failed to allocate %u-byte tensor arena in PSRAM",
                 static_cast<unsigned int>(kTensorArenaSize));
        return false;
    }

    g_interpreter = new (std::nothrow) tflite::MicroInterpreter(
        g_model,
        resolver,
        g_tensor_arena,
        kTensorArenaSize);
    if (g_interpreter == nullptr) {
        ESP_LOGE(kTag, "Failed to create MicroInterpreter");
        heap_caps_free(g_tensor_arena);
        g_tensor_arena = nullptr;
        return false;
    }

    if (g_interpreter->AllocateTensors() != kTfLiteOk) {
        ESP_LOGE(kTag, "AllocateTensors failed; increase tensor arena if needed");
        return false;
    }

    g_input = g_interpreter->input(0);
    g_output = g_interpreter->output(0);
    if (g_input == nullptr || g_output == nullptr ||
        g_input->type != kTfLiteInt8 || g_output->type != kTfLiteInt8 ||
        !tensor_shape_is(g_input, 1, kInputHeight, kInputWidth, kInputChannels) ||
        !tensor_shape_is(
            g_output, 1, kLatentHeight, kLatentWidth, kLatentChannels) ||
        g_input->bytes != TINYCAE_INPUT_BYTES ||
        g_output->bytes != TINYCAE_LATENT_BYTES) {
        ESP_LOGE(kTag, "Unexpected TinyCAE input/output tensor metadata");
        return false;
    }

    ESP_LOGI(
        kTag,
        "TinyCAE ready: model=%u bytes arena=%u bytes input=(scale %.10f zp %d) "
        "output=(scale %.10f zp %d)",
        static_cast<unsigned int>(model_size),
        static_cast<unsigned int>(kTensorArenaSize),
        static_cast<double>(g_input->params.scale),
        g_input->params.zero_point,
        static_cast<double>(g_output->params.scale),
        g_output->params.zero_point);
    return true;
}

extern "C" bool tinycae_encode(
    const uint8_t *rgb888,
    int8_t *latent,
    size_t latent_size,
    int64_t *elapsed_us)
{
    if (rgb888 == nullptr || latent == nullptr || elapsed_us == nullptr ||
        latent_size != TINYCAE_LATENT_BYTES || g_interpreter == nullptr ||
        g_input == nullptr || g_output == nullptr ||
        g_input->params.scale <= 0.0f) {
        return false;
    }

    for (size_t index = 0; index < TINYCAE_INPUT_BYTES; ++index) {
        const float normalized = static_cast<float>(rgb888[index]) / 255.0f;
        int quantized = static_cast<int>(
            std::round(normalized / g_input->params.scale)) +
            g_input->params.zero_point;
        if (quantized < -128) {
            quantized = -128;
        } else if (quantized > 127) {
            quantized = 127;
        }
        g_input->data.int8[index] = static_cast<int8_t>(quantized);
    }

    const int64_t started_us = esp_timer_get_time();
    const TfLiteStatus status = g_interpreter->Invoke();
    *elapsed_us = esp_timer_get_time() - started_us;
    if (status != kTfLiteOk) {
        ESP_LOGE(kTag, "Invoke failed");
        return false;
    }

    std::memcpy(latent, g_output->data.int8, TINYCAE_LATENT_BYTES);
    return true;
}
