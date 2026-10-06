"""Summarize ESP32 JPEG validation-bitrate benchmark CSV files."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_PATH = RESULTS_DIR / "jpeg_validation_bitrate_summary.csv"
QUALITIES = (30, 50, 70, 90)
NUMERIC_FIELDS = (
    "jpeg_bytes",
    "compression_ratio",
    "bits_per_pixel",
    "encode_time_us",
    "psnr_db",
    "ssim",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def summarize_quality(quality: int) -> dict[str, object]:
    path = RESULTS_DIR / f"validation_bitrate_jpeg_q{quality}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing benchmark CSV: {path}")

    rows = read_rows(path)
    if not rows:
        raise RuntimeError(f"No rows in {path}")

    summary: dict[str, object] = {
        "quality": quality,
        "passed": sum(row["status"] == "PASS" for row in rows),
        "total": len(rows),
    }
    for field in NUMERIC_FIELDS:
        values = np.asarray([float(row[field]) for row in rows], dtype=np.float64)
        summary[f"avg_{field}"] = float(np.mean(values))
        summary[f"median_{field}"] = float(np.median(values))
        summary[f"p95_{field}"] = float(np.percentile(values, 95))
    return summary


def main() -> int:
    summaries = [summarize_quality(quality) for quality in QUALITIES]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = list(summaries[0].keys())
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Wrote: {OUTPUT_PATH}")
    for row in summaries:
        print(
            "Q{quality}: {passed}/{total} PASS, "
            "avg_bytes={avg_jpeg_bytes:.2f}, "
            "avg_bpp={avg_bits_per_pixel:.4f}, "
            "avg_psnr={avg_psnr_db:.4f}, "
            "avg_ssim={avg_ssim:.6f}, "
            "avg_time={avg_encode_time_us:.2f} us".format(**row)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
