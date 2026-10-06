"""Train the FP32 TinyCAE baseline on deterministic CIFAR-10 splits."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import tarfile
import time
from pathlib import Path

import numpy as np
import tensorflow as tf


SEED = 2026
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PATH = PROJECT_ROOT / "data" / "raw" / "cifar-10-python.tar.gz"
SPLITS_PATH = PROJECT_ROOT / "data" / "splits" / "cifar10_seed2026_indices.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--limit-train", type=int)
    parser.add_argument("--limit-validation", type=int)
    parser.add_argument("--run-name", default="baseline")
    return parser.parse_args()


def read_batch(archive: tarfile.TarFile, member_name: str) -> np.ndarray:
    extracted = archive.extractfile(member_name)
    if extracted is None:
        raise RuntimeError(f"Could not read {member_name}")
    batch = pickle.load(extracted, encoding="bytes")
    planar = np.asarray(batch[b"data"], dtype=np.uint8)
    return planar.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1).copy()


def load_training_images() -> np.ndarray:
    with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
        batches = [
            read_batch(archive, f"cifar-10-batches-py/data_batch_{number}")
            for number in range(1, 6)
        ]
    images = np.concatenate(batches, axis=0)
    if images.shape != (50_000, 32, 32, 3):
        raise RuntimeError(f"Unexpected training shape: {images.shape}")
    return images


def make_dataset(images: np.ndarray, batch_size: int, training: bool) -> tf.data.Dataset:
    dataset = tf.data.Dataset.from_tensor_slices(images)
    if training:
        dataset = dataset.shuffle(
            min(len(images), 10_000), seed=SEED, reshuffle_each_iteration=True
        )
    dataset = dataset.map(
        lambda image: tf.cast(image, tf.float32) / 255.0,
        num_parallel_calls=tf.data.AUTOTUNE,
        deterministic=True,
    )
    dataset = dataset.map(
        lambda image: (image, image),
        num_parallel_calls=tf.data.AUTOTUNE,
        deterministic=True,
    )
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def build_models() -> tuple[tf.keras.Model, tf.keras.Model, tf.keras.Model]:
    encoder_input = tf.keras.Input((32, 32, 3), name="rgb_input")
    x = tf.keras.layers.Conv2D(
        32, 3, strides=2, padding="same", activation="relu", name="enc_conv_s2"
    )(encoder_input)
    x = tf.keras.layers.DepthwiseConv2D(
        3, strides=2, padding="same", activation="relu", name="enc_depthwise_s2"
    )(x)
    x = tf.keras.layers.Conv2D(
        32, 1, padding="same", activation="relu", name="enc_pointwise"
    )(x)
    latent = tf.keras.layers.Conv2D(
        16, 1, padding="same", activation=None, name="latent"
    )(x)
    encoder = tf.keras.Model(encoder_input, latent, name="tinycae_encoder")

    decoder_input = tf.keras.Input((8, 8, 16), name="latent_input")
    x = tf.keras.layers.Conv2D(
        64, 3, padding="same", activation="relu", name="dec_conv_64"
    )(decoder_input)
    x = tf.keras.layers.UpSampling2D(
        size=2, interpolation="nearest", name="dec_upsample_1"
    )(x)
    x = tf.keras.layers.Conv2D(
        32, 3, padding="same", activation="relu", name="dec_conv_32"
    )(x)
    x = tf.keras.layers.UpSampling2D(
        size=2, interpolation="nearest", name="dec_upsample_2"
    )(x)
    x = tf.keras.layers.Conv2D(
        16, 3, padding="same", activation="relu", name="dec_conv_16"
    )(x)
    reconstruction = tf.keras.layers.Conv2D(
        3, 3, padding="same", activation="sigmoid", name="rgb_output"
    )(x)
    decoder = tf.keras.Model(decoder_input, reconstruction, name="tinycae_decoder")

    autoencoder = tf.keras.Model(
        encoder_input, decoder(encoder(encoder_input)), name="tinycae"
    )
    return encoder, decoder, autoencoder


def reconstruction_loss(y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
    mse = tf.reduce_mean(tf.math.squared_difference(y_true, y_pred), axis=(1, 2, 3))
    ssim = tf.image.ssim(y_true, y_pred, max_val=1.0)
    return tf.reduce_mean(0.9 * mse + 0.1 * (1.0 - ssim))


def main() -> int:
    args = parse_args()
    tf.keras.utils.set_random_seed(SEED)
    try:
        tf.config.experimental.enable_op_determinism()
    except RuntimeError:
        pass

    run_dir = PROJECT_ROOT / "models" / "tinycae" / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    print("Loading CIFAR-10 from local archive...")
    all_train_images = load_training_images()
    with np.load(SPLITS_PATH) as splits:
        train_indices = splits["train_indices"]
        validation_indices = splits["validation_indices"]
    if args.limit_train is not None:
        train_indices = train_indices[: args.limit_train]
    if args.limit_validation is not None:
        validation_indices = validation_indices[: args.limit_validation]

    train_images = all_train_images[train_indices]
    validation_images = all_train_images[validation_indices]
    print(f"Train: {len(train_images)}, validation: {len(validation_images)}")

    train_dataset = make_dataset(train_images, args.batch_size, training=True)
    validation_dataset = make_dataset(
        validation_images, args.batch_size, training=False
    )
    encoder, decoder, autoencoder = build_models()
    if encoder.output_shape != (None, 8, 8, 16):
        raise RuntimeError(f"Wrong encoder output: {encoder.output_shape}")
    if autoencoder.output_shape != (None, 32, 32, 3):
        raise RuntimeError(f"Wrong reconstruction output: {autoencoder.output_shape}")

    autoencoder.compile(
        optimizer=tf.keras.optimizers.Adam(args.learning_rate),
        loss=reconstruction_loss,
        metrics=[
            tf.keras.metrics.MeanSquaredError(name="mse"),
        ],
    )
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            run_dir / "best.weights.h5",
            monitor="val_loss",
            save_best_only=True,
            save_weights_only=True,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=args.patience,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.CSVLogger(run_dir / "training_log.csv"),
    ]

    started = time.perf_counter()
    history = autoencoder.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=args.epochs,
        callbacks=callbacks,
        verbose=2,
    )
    elapsed = time.perf_counter() - started

    encoder.save(run_dir / "encoder.keras")
    decoder.save(run_dir / "decoder.keras")
    autoencoder.save(run_dir / "autoencoder.keras")

    predictions = autoencoder.predict(validation_dataset, verbose=0)
    references = validation_images.astype(np.float32) / 255.0
    mse_per_image = np.mean((references - predictions) ** 2, axis=(1, 2, 3))
    psnr_per_image = tf.image.psnr(references, predictions, max_val=1.0).numpy()
    ssim_per_image = tf.image.ssim(references, predictions, max_val=1.0).numpy()
    metrics = {
        "validation_images": int(len(validation_images)),
        "mse": float(np.mean(mse_per_image)),
        "psnr_db": float(np.mean(psnr_per_image)),
        "ssim": float(np.mean(ssim_per_image)),
        "training_seconds": elapsed,
        "epochs_completed": len(history.history["loss"]),
        "encoder_parameters": encoder.count_params(),
        "decoder_parameters": decoder.count_params(),
        "latent_shape": [8, 8, 16],
    }
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    with (run_dir / "history.csv").open("w", newline="", encoding="utf-8") as stream:
        names = list(history.history)
        writer = csv.DictWriter(stream, fieldnames=["epoch", *names])
        writer.writeheader()
        for epoch in range(len(history.history["loss"])):
            writer.writerow(
                {"epoch": epoch + 1, **{name: history.history[name][epoch] for name in names}}
            )

    print(json.dumps(metrics, indent=2))
    print(f"Saved run: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
