"""Download CIFAR-10 and create the fixed 20-image ESP32 hardware test set."""

from __future__ import annotations

import csv
import hashlib
import json
import pickle
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image


DATASET_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
ARCHIVE_MD5 = "c58f30108f718f92721af3b95e74349a"
SEED = 2026
IMAGES_PER_CLASS = 2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
ARCHIVE_PATH = DATA_DIR / "cifar-10-python.tar.gz"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "hardware_test"
RAW_DIR = OUTPUT_DIR / "raw"
PNG_DIR = OUTPUT_DIR / "png"
CSV_MANIFEST = OUTPUT_DIR / "manifest.csv"
JSON_MANIFEST = OUTPUT_DIR / "manifest.json"

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


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ARCHIVE_PATH.exists() and md5_file(ARCHIVE_PATH) == ARCHIVE_MD5:
        print(f"Using verified archive: {ARCHIVE_PATH}")
        return

    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    print(f"Downloading CIFAR-10 from {DATASET_URL}")
    urllib.request.urlretrieve(DATASET_URL, ARCHIVE_PATH)

    actual_md5 = md5_file(ARCHIVE_PATH)
    if actual_md5 != ARCHIVE_MD5:
        ARCHIVE_PATH.unlink(missing_ok=True)
        raise RuntimeError(
            f"CIFAR-10 checksum mismatch: expected {ARCHIVE_MD5}, got {actual_md5}"
        )

    print(f"Archive checksum OK: {actual_md5}")


def load_test_batch() -> tuple[np.ndarray, np.ndarray]:
    member_name = "cifar-10-batches-py/test_batch"
    with tarfile.open(ARCHIVE_PATH, mode="r:gz") as archive:
        member = archive.getmember(member_name)
        extracted = archive.extractfile(member)
        if extracted is None:
            raise RuntimeError(f"Could not read {member_name}")
        batch = pickle.load(extracted, encoding="bytes")

    planar = np.asarray(batch[b"data"], dtype=np.uint8)
    labels = np.asarray(batch[b"labels"], dtype=np.int64)
    images = planar.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1).copy()

    if images.shape != (10_000, 32, 32, 3):
        raise RuntimeError(f"Unexpected CIFAR-10 test shape: {images.shape}")
    return images, labels


def choose_indices(labels: np.ndarray) -> list[int]:
    rng = np.random.default_rng(SEED)
    selected: list[int] = []
    for class_id in range(len(CLASS_NAMES)):
        candidates = np.flatnonzero(labels == class_id)
        chosen = rng.choice(candidates, size=IMAGES_PER_CLASS, replace=False)
        selected.extend(int(index) for index in sorted(chosen.tolist()))
    return selected


def write_hardware_test_set(images: np.ndarray, labels: np.ndarray) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    for test_index in choose_indices(labels):
        class_id = int(labels[test_index])
        class_name = CLASS_NAMES[class_id]
        image_id = f"cifar10_test_{test_index:05d}"
        raw_data = images[test_index].tobytes(order="C")

        if len(raw_data) != 32 * 32 * 3:
            raise RuntimeError(f"Unexpected raw size for {image_id}: {len(raw_data)}")

        raw_path = RAW_DIR / f"{image_id}.rgb"
        png_path = PNG_DIR / f"{image_id}.png"
        raw_path.write_bytes(raw_data)
        Image.fromarray(images[test_index], mode="RGB").save(png_path)

        records.append(
            {
                "image_id": image_id,
                "cifar10_test_index": test_index,
                "class_id": class_id,
                "class_name": class_name,
                "raw_bytes": len(raw_data),
                "sha256": hashlib.sha256(raw_data).hexdigest(),
                "raw_path": raw_path.relative_to(PROJECT_ROOT).as_posix(),
                "png_path": png_path.relative_to(PROJECT_ROOT).as_posix(),
            }
        )

    with CSV_MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    JSON_MANIFEST.write_text(
        json.dumps(
            {
                "dataset": "CIFAR-10 official test batch",
                "source": DATASET_URL,
                "archive_md5": ARCHIVE_MD5,
                "selection_seed": SEED,
                "selection_rule": "2 images per class, sampled without replacement",
                "image_format": "RGB888, HWC, uint8, row-major",
                "images": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Created {len(records)} hardware-test images")
    print(f"CSV manifest: {CSV_MANIFEST}")
    print(f"JSON manifest: {JSON_MANIFEST}")
    print("Class counts:")
    for class_name in CLASS_NAMES:
        count = sum(record["class_name"] == class_name for record in records)
        print(f"  {class_name}: {count}")


def main() -> None:
    download_archive()
    images, labels = load_test_batch()
    write_hardware_test_set(images, labels)


if __name__ == "__main__":
    main()
