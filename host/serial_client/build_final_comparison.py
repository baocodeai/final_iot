"""Build the final TinyCAE-vs-JPEG comparison from locked hardware results."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
TINYCAE_PATH = RESULTS_DIR / "tinycae_esp32_20.csv"
JPEG_Q70_PATH = RESULTS_DIR / "hardware_test_jpeg_q70.csv"
LOCKED_QUALITY_PATH = RESULTS_DIR / "jpeg_locked_quality.json"
FINAL_CSV = RESULTS_DIR / "final_codec_comparison.csv"
PAIRWISE_CSV = RESULTS_DIR / "final_pairwise_tinycae_vs_jpeg_q70.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def summarize(
    codec: str,
    sizes: list[float],
    bpp: list[float],
    ratios: list[float],
    times_us: list[float],
    psnr: list[float],
    ssim: list[float],
) -> dict[str, object]:
    return {
        "codec": codec,
        "images": len(sizes),
        "mean_bytes": float(np.mean(sizes)),
        "mean_bpp": float(np.mean(bpp)),
        "mean_compression_ratio": float(np.mean(ratios)),
        "mean_time_us": float(np.mean(times_us)),
        "median_time_us": float(np.median(times_us)),
        "p95_time_us": float(np.percentile(times_us, 95)),
        "mean_psnr_db": float(np.mean(psnr)),
        "std_psnr_db": float(np.std(psnr)),
        "mean_ssim": float(np.mean(ssim)),
        "std_ssim": float(np.std(ssim)),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    tinycae = read_csv(TINYCAE_PATH)
    jpeg_q70 = read_csv(JPEG_Q70_PATH)
    if len(tinycae) != 20 or len(jpeg_q70) != 20:
        raise RuntimeError(
            f"Expected 20 rows each, got TinyCAE={len(tinycae)} JPEG={len(jpeg_q70)}"
        )

    tiny_by_id = {row["image_id"]: row for row in tinycae}
    jpeg_by_id = {row["image_id"]: row for row in jpeg_q70}
    if set(tiny_by_id) != set(jpeg_by_id):
        raise RuntimeError("TinyCAE and JPEG image_id sets do not match")

    tiny_sizes = [float(row["latent_bytes"]) for row in tinycae]
    tiny_summary = summarize(
        "TinyCAE INT8",
        tiny_sizes,
        [size * 8 / (32 * 32) for size in tiny_sizes],
        [3072 / size for size in tiny_sizes],
        [float(row["invoke_time_us"]) for row in tinycae],
        [float(row["esp32_psnr_db"]) for row in tinycae],
        [float(row["esp32_ssim"]) for row in tinycae],
    )
    jpeg_summary = summarize(
        "JPEG Q70 locked",
        [float(row["jpeg_bytes"]) for row in jpeg_q70],
        [float(row["bits_per_pixel"]) for row in jpeg_q70],
        [float(row["compression_ratio"]) for row in jpeg_q70],
        [float(row["encode_time_us"]) for row in jpeg_q70],
        [float(row["psnr_db"]) for row in jpeg_q70],
        [float(row["ssim"]) for row in jpeg_q70],
    )
    write_csv(FINAL_CSV, [tiny_summary, jpeg_summary])

    pairwise_rows: list[dict[str, object]] = []
    for image_id in sorted(tiny_by_id):
        tiny = tiny_by_id[image_id]
        jpeg = jpeg_by_id[image_id]
        pairwise_rows.append(
            {
                "image_id": image_id,
                "class_name": tiny["class_name"],
                "tinycae_bytes": int(float(tiny["latent_bytes"])),
                "jpeg_q70_bytes": int(float(jpeg["jpeg_bytes"])),
                "tinycae_bpp": float(tiny["latent_bytes"]) * 8 / (32 * 32),
                "jpeg_q70_bpp": float(jpeg["bits_per_pixel"]),
                "tinycae_time_us": float(tiny["invoke_time_us"]),
                "jpeg_q70_time_us": float(jpeg["encode_time_us"]),
                "tinycae_psnr_db": float(tiny["esp32_psnr_db"]),
                "jpeg_q70_psnr_db": float(jpeg["psnr_db"]),
                "delta_psnr_db": float(tiny["esp32_psnr_db"])
                - float(jpeg["psnr_db"]),
                "tinycae_ssim": float(tiny["esp32_ssim"]),
                "jpeg_q70_ssim": float(jpeg["ssim"]),
                "delta_ssim": float(tiny["esp32_ssim"]) - float(jpeg["ssim"]),
            }
        )
    write_csv(PAIRWISE_CSV, pairwise_rows)

    if LOCKED_QUALITY_PATH.exists():
        locked = json.loads(LOCKED_QUALITY_PATH.read_text(encoding="utf-8"))
        locked["hardware_test_csv"] = "results/hardware_test_jpeg_q70.csv"
        locked["final_comparison_csv"] = "results/final_codec_comparison.csv"
        LOCKED_QUALITY_PATH.write_text(
            json.dumps(locked, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"Wrote: {FINAL_CSV}")
    print(f"Wrote: {PAIRWISE_CSV}")
    for row in (tiny_summary, jpeg_summary):
        print(
            "{codec}: {mean_bytes:.2f} B, {mean_bpp:.4f} bpp, "
            "PSNR {mean_psnr_db:.4f} dB, SSIM {mean_ssim:.6f}, "
            "mean time {mean_time_us:.2f} us".format(**row)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
