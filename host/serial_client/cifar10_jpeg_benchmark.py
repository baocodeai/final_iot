"""Benchmark ESP32 JPEG encoding on CIFAR-10 images.

By default this runs the fixed 20-image hardware-test set. For proposal-compliant
JPEG quality selection, use ``--split validation_bitrate`` to run the 500-image
validation-bitrate set before locking a final JPEG quality.
"""

from __future__ import annotations

import argparse
import csv
import io
import pickle
import re
import tarfile
import time
import zlib
from pathlib import Path

import numpy as np
import serial
from PIL import Image
from serial import SerialException
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARDWARE_MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "processed" / "hardware_test" / "manifest.csv"
)
VALIDATION_BITRATE_MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "splits" / "validation_bitrate_manifest.csv"
)
ARCHIVE_PATH = PROJECT_ROOT / "data" / "raw" / "cifar-10-python.tar.gz"
RAW_SIZE = 32 * 32 * 3
HEADER_PATTERN = re.compile(
    r"^JPEG (?P<size>\d+) (?P<crc>[0-9A-Fa-f]{8}) (?P<time_us>\d+)$"
)
CLASS_NAMES = (
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM5")
    parser.add_argument("--baud", type=int, default=115_200)
    parser.add_argument("--quality", type=int, default=50)
    parser.add_argument(
        "--split",
        choices=("hardware_test", "validation_bitrate"),
        default="hardware_test",
        help=(
            "Image set to benchmark. Use validation_bitrate for the 500-image "
            "proposal-compliant JPEG quality selection set."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional image limit for quick smoke tests.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per image after UART desynchronization or timeout.",
    )
    return parser.parse_args()


def load_cifar10_train_images() -> np.ndarray:
    batches: list[np.ndarray] = []
    with tarfile.open(ARCHIVE_PATH, mode="r:gz") as archive:
        for batch_id in range(1, 6):
            member_name = f"cifar-10-batches-py/data_batch_{batch_id}"
            member = archive.getmember(member_name)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Could not read {member_name}")
            batch = pickle.load(extracted, encoding="bytes")
            planar = np.asarray(batch[b"data"], dtype=np.uint8)
            images = planar.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1).copy()
            batches.append(images)

    images = np.concatenate(batches, axis=0)
    if images.shape != (50_000, 32, 32, 3):
        raise RuntimeError(f"Unexpected CIFAR-10 train image shape: {images.shape}")
    return images


def load_hardware_test_records() -> list[dict[str, object]]:
    with HARDWARE_MANIFEST_PATH.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 20:
        raise RuntimeError(f"Expected 20 hardware-test entries, found {len(records)}")

    images: list[dict[str, object]] = []
    for record in records:
        payload = (PROJECT_ROOT / record["raw_path"]).read_bytes()
        if len(payload) != RAW_SIZE:
            raise RuntimeError(f"{record['image_id']}: expected {RAW_SIZE} bytes")
        images.append(
            {
                "image_id": record["image_id"],
                "class_id": int(record["class_id"]),
                "class_name": record["class_name"],
                "payload": payload,
                "source_index": int(record["cifar10_test_index"]),
                "index_space": "original_test",
            }
        )
    return images


def load_validation_bitrate_records() -> list[dict[str, object]]:
    train_images = load_cifar10_train_images()
    with VALIDATION_BITRATE_MANIFEST_PATH.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 500:
        raise RuntimeError(
            f"Expected 500 validation-bitrate entries, found {len(records)}"
        )

    images: list[dict[str, object]] = []
    for record in records:
        index = int(record["index"])
        class_id = int(record["class_id"])
        payload = train_images[index].tobytes(order="C")
        if len(payload) != RAW_SIZE:
            raise RuntimeError(f"Index {index}: expected {RAW_SIZE} bytes")
        image_id = f"cifar10_train_{index:05d}"
        images.append(
            {
                "image_id": image_id,
                "class_id": class_id,
                "class_name": record.get("class_name") or CLASS_NAMES[class_id],
                "payload": payload,
                "source_index": index,
                "index_space": "original_train",
            }
        )
    return images


def load_records(split: str) -> list[dict[str, object]]:
    if split == "hardware_test":
        return load_hardware_test_records()
    if split == "validation_bitrate":
        return load_validation_bitrate_records()
    raise ValueError(f"Unsupported split: {split}")


def wait_for_line(device: serial.Serial, predicate, timeout: float = 10.0) -> str:
    deadline = time.monotonic() + timeout
    last_line = ""
    while time.monotonic() < deadline:
        raw = device.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        last_line = line
        if line.startswith("ERROR ") or predicate(line):
            return line
    raise TimeoutError(f"Timed out waiting for ESP32 response; last line={last_line!r}")


def read_exact(device: serial.Serial, size: int, timeout: float = 10.0) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < size and time.monotonic() < deadline:
        data.extend(device.read(size - len(data)))
    if len(data) != size:
        raise TimeoutError(f"Expected {size} JPEG bytes, received {len(data)}")
    return bytes(data)


def encode_one(device: serial.Serial, payload: bytes, quality: int) -> tuple[bytes, int]:
    # Drop any leftover binary bytes from the previous JPEG frame before the
    # next text command. This keeps the line-based UART protocol synchronized.
    device.reset_input_buffer()
    device.write(f"JPEG {quality}\r\n".encode("ascii"))
    device.flush()
    ready = wait_for_line(device, lambda line: line == f"READY {RAW_SIZE}")
    if ready != f"READY {RAW_SIZE}":
        raise RuntimeError(f"Unexpected ready response: {ready}")

    device.write(payload)
    device.flush()
    header = wait_for_line(device, lambda line: HEADER_PATTERN.fullmatch(line) is not None)
    match = HEADER_PATTERN.fullmatch(header)
    if match is None:
        raise RuntimeError(f"Unexpected JPEG response: {header}")

    jpeg_size = int(match.group("size"))
    expected_crc = int(match.group("crc"), 16)
    encode_time_us = int(match.group("time_us"))
    jpeg_data = read_exact(device, jpeg_size)
    actual_crc = zlib.crc32(jpeg_data) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise RuntimeError(
            f"CRC mismatch: ESP32={expected_crc:08X}, PC={actual_crc:08X}"
        )
    return jpeg_data, encode_time_us


def write_results_csv(path: Path, results: list[dict[str, object]]) -> None:
    if not results:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


def main() -> int:
    args = parse_args()
    if not 1 <= args.quality <= 100:
        raise ValueError("JPEG quality must be between 1 and 100")

    output_root = (
        PROJECT_ROOT / "bitstreams" / "jpeg" / f"{args.split}_q{args.quality}"
    )
    results_path = PROJECT_ROOT / "results" / f"{args.split}_jpeg_q{args.quality}.csv"
    summary_path = (
        PROJECT_ROOT / "results" / f"{args.split}_jpeg_q{args.quality}_summary.txt"
    )

    images = load_records(args.split)
    if args.limit is not None:
        images = images[: args.limit]
    if not images:
        raise RuntimeError("No images to benchmark")

    output_root.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    print(f"Opening {args.port} at {args.baud} baud...")
    with serial.Serial(args.port, args.baud, timeout=0.25) as device:
        device.dtr = False
        device.rts = False
        time.sleep(4.0)
        device.reset_input_buffer()

        total = len(images)
        for number, record in enumerate(images, start=1):
            image_id = str(record["image_id"])
            payload = bytes(record["payload"])

            last_error: Exception | None = None
            for attempt in range(1, args.retries + 2):
                try:
                    jpeg_data, encode_time_us = encode_one(device, payload, args.quality)
                    break
                except Exception as error:
                    last_error = error
                    device.reset_input_buffer()
                    time.sleep(0.25)
                    if attempt <= args.retries:
                        print(
                            f"[{number:03d}/{total}] {image_id}: retry "
                            f"{attempt}/{args.retries} after {error}"
                        )
            else:
                print(f"[{number:03d}/{total}] {image_id}: FAIL - {last_error}")
                write_results_csv(results_path, results)
                return 1

            try:
                decoded = np.asarray(Image.open(io.BytesIO(jpeg_data)).convert("RGB"))
                original = np.frombuffer(payload, dtype=np.uint8).reshape(32, 32, 3)
                psnr = peak_signal_noise_ratio(original, decoded, data_range=255)
                ssim = structural_similarity(
                    original, decoded, channel_axis=2, data_range=255
                )
                output_path = output_root / f"{image_id}.jpg"
                output_path.write_bytes(jpeg_data)
                jpeg_size = len(jpeg_data)
                result = {
                    "image_id": image_id,
                    "class_id": record["class_id"],
                    "class_name": record["class_name"],
                    "split": args.split,
                    "index_space": record["index_space"],
                    "source_index": record["source_index"],
                    "quality": args.quality,
                    "raw_bytes": RAW_SIZE,
                    "jpeg_bytes": jpeg_size,
                    "compression_ratio": RAW_SIZE / jpeg_size,
                    "bits_per_pixel": jpeg_size * 8 / (32 * 32),
                    "encode_time_us": encode_time_us,
                    "psnr_db": psnr,
                    "ssim": ssim,
                    "status": "PASS",
                }
                results.append(result)
                print(
                    f"[{number:03d}/{total}] {image_id} {record['class_name']}: "
                    f"{jpeg_size} B, {encode_time_us} us, "
                    f"PSNR={psnr:.2f} dB, SSIM={ssim:.4f}"
                )
                if number % 25 == 0:
                    write_results_csv(results_path, results)
            except Exception as error:
                print(f"[{number:03d}/{total}] {image_id}: FAIL - {error}")
                write_results_csv(results_path, results)
                return 1

    write_results_csv(results_path, results)

    numeric_fields = (
        "jpeg_bytes",
        "compression_ratio",
        "bits_per_pixel",
        "encode_time_us",
        "psnr_db",
        "ssim",
    )
    averages = {
        field: float(np.mean([float(row[field]) for row in results]))
        for field in numeric_fields
    }
    summary = (
        f"Split: {args.split}\n"
        f"Images: {len(results)}/{len(images)} PASS\n"
        f"JPEG quality: {args.quality}\n"
        f"Average JPEG size: {averages['jpeg_bytes']:.2f} bytes\n"
        f"Average compression ratio: {averages['compression_ratio']:.4f}:1\n"
        f"Average bits per pixel: {averages['bits_per_pixel']:.4f}\n"
        f"Average ESP32 encode time: {averages['encode_time_us']:.2f} us\n"
        f"Average PSNR: {averages['psnr_db']:.4f} dB\n"
        f"Average SSIM: {averages['ssim']:.6f}\n"
    )
    summary_path.write_text(summary, encoding="utf-8")
    print("\n" + summary)
    print(f"Results: {results_path}")
    print(f"JPEG files: {output_root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SerialException, OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(2)
