"""Post-Training Integer Quantization (PTQ INT8) for TinyCAE Encoder.

Produces integer-only TFLite model compatible with ESP-NN and TFLite Micro.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models/tinycae/stratified_baseline"
CALIB_DATA_PATH = ROOT / "data/splits/cifar10_seed2026_indices.npz"
OUTPUT_TFLITE = ROOT / "models/tinycae/int8/encoder_int8.tflite"


def representative_dataset_gen():
    cifar = tf.keras.datasets.cifar10
    (x_train, _), _ = cifar.load_data()
    indices = np.load(CALIB_DATA_PATH)["calibration_indices"]
    calib_images = x_train[indices].astype(np.float32) / 255.0
    for img in calib_images:
        yield [np.expand_dims(img, axis=0)]


def run_quantization():
    encoder = tf.keras.models.load_model(MODEL_DIR / "encoder.keras")
    converter = tf.lite.TFLiteConverter.from_keras_model(encoder)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_quant_model = converter.convert()
    OUTPUT_TFLITE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TFLITE.write_bytes(tflite_quant_model)
    print(f"Quantized INT8 model saved to {OUTPUT_TFLITE} ({len(tflite_quant_model)} bytes)")


if __name__ == "__main__":
    run_quantization()
