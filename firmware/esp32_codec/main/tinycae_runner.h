#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TINYCAE_INPUT_BYTES 3072
#define TINYCAE_LATENT_BYTES 1024

bool tinycae_initialize(void);

bool tinycae_encode(
    const uint8_t *rgb888,
    int8_t *latent,
    size_t latent_size,
    int64_t *elapsed_us);

#ifdef __cplusplus
}
#endif
