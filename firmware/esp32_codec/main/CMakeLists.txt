idf_component_register(
    SRCS "esp32_codec.c" "tinycae_runner.cc"
    INCLUDE_DIRS "."
    REQUIRES esp_driver_uart esp_hw_support esp_psram esp_timer esp-tflite-micro
    EMBED_FILES "encoder_int8.tflite"
)
