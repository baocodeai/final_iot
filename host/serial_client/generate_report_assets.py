"""Generate high-resolution figures for the final DOCX report."""

from pathlib import Path
import csv
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from PIL import Image

PROJECT_ROOT = Path("D:/projects/iot-final")
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set matplotlib styling
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
})

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    print("Reading experimental results...")
    final_comp = read_csv(RESULTS_DIR / "final_codec_comparison.csv")
    pairwise = read_csv(RESULTS_DIR / "final_pairwise_tinycae_vs_jpeg_q70.csv")
    val_summary = read_csv(RESULTS_DIR / "jpeg_validation_bitrate_summary.csv")
    tiny_data = read_csv(RESULTS_DIR / "tinycae_esp32_20.csv")
    jpeg_q70_data = read_csv(RESULTS_DIR / "hardware_test_jpeg_q70.csv")
    
    # 1. Rate-Distortion: BPP vs PSNR
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    
    # Validation curve (500 images)
    val_bpp = [float(r["avg_bits_per_pixel"]) for r in val_summary]
    val_psnr = [float(r["avg_psnr_db"]) for r in val_summary]
    val_q = [r["quality"] for r in val_summary]
    ax.plot(val_bpp, val_psnr, "b--o", alpha=0.5, label="JPEG (Validation 500 ảnh)", markersize=6)
    for q, x, y in zip(val_q, val_bpp, val_psnr):
        ax.annotate(f"Q{q}", (x, y), textcoords="offset points", xytext=(-15, 8), fontsize=9, color="blue", alpha=0.7)

    # Hardware test 20 images
    # TinyCAE INT8
    tiny_bpp = float(final_comp[0]["mean_bpp"])
    tiny_psnr = float(final_comp[0]["mean_psnr_db"])
    tiny_psnr_std = float(final_comp[0]["std_psnr_db"])
    
    # JPEG Q70 locked
    jpeg_bpp = float(final_comp[1]["mean_bpp"])
    jpeg_psnr = float(final_comp[1]["mean_psnr_db"])
    jpeg_psnr_std = float(final_comp[1]["std_psnr_db"])
    
    ax.errorbar([tiny_bpp], [tiny_psnr], yerr=[tiny_psnr_std], fmt="s", color="#D9381E", markersize=9, 
                capsize=5, capthick=1.5, elinewidth=1.5, label=f"TinyCAE INT8 ({tiny_bpp:.1f} bpp, {tiny_psnr:.2f} dB)", zorder=5)
    ax.errorbar([jpeg_bpp], [jpeg_psnr], yerr=[jpeg_psnr_std], fmt="^", color="#2E86AB", markersize=9, 
                capsize=5, capthick=1.5, elinewidth=1.5, label=f"JPEG Q70 locked ({jpeg_bpp:.2f} bpp, {jpeg_psnr:.2f} dB)", zorder=5)
    
    ax.annotate(f"TinyCAE INT8\n{tiny_psnr:.2f} dB", (tiny_bpp, tiny_psnr), xytext=(12, -10), 
                textcoords="offset points", fontweight="bold", color="#D9381E",
                arrowprops=dict(arrowstyle="->", color="#D9381E", lw=1))
    ax.annotate(f"JPEG Q70\n{jpeg_psnr:.2f} dB", (jpeg_bpp, jpeg_psnr), xytext=(-65, -25), 
                textcoords="offset points", fontweight="bold", color="#2E86AB",
                arrowprops=dict(arrowstyle="->", color="#2E86AB", lw=1))

    ax.set_xlabel("Tốc độ bít (Bits Per Pixel - BPP)")
    ax.set_ylabel("Chất lượng đỉnh (PSNR - dB)")
    ax.set_title("Đường cong Đánh đổi Tốc độ bít - Chất lượng (BPP vs. PSNR)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", framealpha=0.95)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "bpp_psnr_comparison.png")
    plt.close(fig)
    print("Saved bpp_psnr_comparison.png")

    # 2. Rate-Distortion: BPP vs SSIM
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    
    val_ssim = [float(r["avg_ssim"]) for r in val_summary]
    ax.plot(val_bpp, val_ssim, "b--o", alpha=0.5, label="JPEG (Validation 500 ảnh)", markersize=6)
    for q, x, y in zip(val_q, val_bpp, val_ssim):
        ax.annotate(f"Q{q}", (x, y), textcoords="offset points", xytext=(-15, 8), fontsize=9, color="blue", alpha=0.7)

    tiny_ssim = float(final_comp[0]["mean_ssim"])
    tiny_ssim_std = float(final_comp[0]["std_ssim"])
    jpeg_ssim = float(final_comp[1]["mean_ssim"])
    jpeg_ssim_std = float(final_comp[1]["std_ssim"])

    ax.errorbar([tiny_bpp], [tiny_ssim], yerr=[tiny_ssim_std], fmt="s", color="#D9381E", markersize=9, 
                capsize=5, capthick=1.5, elinewidth=1.5, label=f"TinyCAE INT8 ({tiny_bpp:.1f} bpp, {tiny_ssim:.4f})", zorder=5)
    ax.errorbar([jpeg_bpp], [jpeg_ssim], yerr=[jpeg_ssim_std], fmt="^", color="#2E86AB", markersize=9, 
                capsize=5, capthick=1.5, elinewidth=1.5, label=f"JPEG Q70 locked ({jpeg_bpp:.2f} bpp, {jpeg_ssim:.4f})", zorder=5)

    ax.annotate(f"TinyCAE INT8\n{tiny_ssim:.4f}", (tiny_bpp, tiny_ssim), xytext=(12, -15), 
                textcoords="offset points", fontweight="bold", color="#D9381E",
                arrowprops=dict(arrowstyle="->", color="#D9381E", lw=1))
    ax.annotate(f"JPEG Q70\n{jpeg_ssim:.4f}", (jpeg_bpp, jpeg_ssim), xytext=(-65, -25), 
                textcoords="offset points", fontweight="bold", color="#2E86AB",
                arrowprops=dict(arrowstyle="->", color="#2E86AB", lw=1))

    ax.set_xlabel("Tốc độ bít (Bits Per Pixel - BPP)")
    ax.set_ylabel("Độ tương đồng cấu trúc (SSIM)")
    ax.set_title("Đường cong Đánh đổi Tốc độ bít - Độ tương đồng cấu trúc (BPP vs. SSIM)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", framealpha=0.95)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "bpp_ssim_comparison.png")
    plt.close(fig)
    print("Saved bpp_ssim_comparison.png")

    # 3. Latency comparison bar chart
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    methods = ["JPEG Q30", "JPEG Q50", "JPEG Q70 (Khóa)", "JPEG Q90", "TinyCAE INT8"]
    # Mean times in ms:
    # JPEG validation times: 2.27ms, 2.32ms, 2.41ms (2.43ms on hardware 20), 2.63ms
    times_ms = [2.27, 2.32, 2.43, 2.63, 60.70]
    colors = ["#7FB3D5", "#5499C7", "#2980B9", "#1B4F72", "#D9381E"]
    
    bars = ax.bar(methods, times_ms, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    ax.set_ylabel("Thời gian mã hóa lõi trên ESP32 (ms)")
    ax.set_title("So sánh Thời gian Mã hóa Lõi trên ESP32 (t_core)")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.2f} ms",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha="center", va="bottom", fontweight="bold", fontsize=10)
    
    ax.set_ylim(0, 72)
    # Add an annotation showing ratio
    ax.annotate("TinyCAE chậm hơn ~25.0× so với JPEG Q70\n(Do chi phí tính toán 338k MACs so với thuật toán DCT)",
                xy=(4, 60.70), xytext=(1.8, 50),
                arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
                bbox=dict(boxstyle="round,pad=0.5", fc="#FFF9C4", ec="#FBC02D", lw=1),
                fontsize=9.5)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "execution_time_comparison.png")
    plt.close(fig)
    print("Saved execution_time_comparison.png")

    # 4. Pairwise Delta PSNR & SSIM on 20 images
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=300, sharex=True)
    
    img_ids = [r["image_id"].replace("cifar10_test_", "") for r in pairwise]
    classes = [r["class_name"] for r in pairwise]
    labels = [f"{cls}\n#{iid}" for cls, iid in zip(classes, img_ids)]
    
    delta_psnr = [float(r["delta_psnr_db"]) for r in pairwise]
    delta_ssim = [float(r["delta_ssim"]) for r in pairwise]
    
    x = np.arange(len(img_ids))
    
    # Delta PSNR
    colors_psnr = ["#27AE60" if v >= 0 else "#C0392B" for v in delta_psnr]
    bars1 = ax1.bar(x, delta_psnr, color=colors_psnr, width=0.6, edgecolor="black", linewidth=0.6)
    ax1.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax1.set_ylabel("Δ PSNR (dB)\n(TinyCAE - JPEG Q70)")
    ax1.set_title("Chênh lệch Chất lượng Tái tạo Ghép cặp trên 20 ảnh Hardware Test (TinyCAE - JPEG Q70)")
    ax1.grid(True, linestyle=":", alpha=0.5)
    
    # Add mean line
    mean_d_psnr = np.mean(delta_psnr)
    ax1.axhline(mean_d_psnr, color="blue", linewidth=1.2, linestyle="-.", label=f"Trung bình Δ PSNR = +{mean_d_psnr:.3f} dB")
    ax1.legend(loc="upper left")

    # Delta SSIM
    colors_ssim = ["#27AE60" if v >= 0 else "#C0392B" for v in delta_ssim]
    bars2 = ax2.bar(x, delta_ssim, color=colors_ssim, width=0.6, edgecolor="black", linewidth=0.6)
    ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax2.set_ylabel("Δ SSIM\n(TinyCAE - JPEG Q70)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.5)
    ax2.grid(True, linestyle=":", alpha=0.5)
    
    mean_d_ssim = np.mean(delta_ssim)
    ax2.axhline(mean_d_ssim, color="blue", linewidth=1.2, linestyle="-.", label=f"Trung bình Δ SSIM = +{mean_d_ssim:.4f}")
    ax2.legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "pairwise_delta_analysis.png")
    plt.close(fig)
    print("Saved pairwise_delta_analysis.png")

    # 5. Visual reconstruction comparison grid for 4 representative test images
    # Diverse samples: airplane (high TinyCAE gain: +1.74 dB), cat (+1.63 dB), deer (+1.24 dB), dog (JPEG gain: -1.44 dB)
    sample_ids = [
        ("cifar10_test_01789", "airplane"),
        ("cifar10_test_03607", "cat"),
        ("cifar10_test_06822", "deer"),
        ("cifar10_test_01922", "dog")
    ]
    
    orig_dir = PROJECT_ROOT / "data/processed/hardware_test/png"
    tiny_dir = PROJECT_ROOT / "bitstreams/tinycae/golden/reconstruction_png"
    jpeg_dir = PROJECT_ROOT / "bitstreams/jpeg/hardware_test_q70"
    
    fig, axes = plt.subplots(4, 3, figsize=(7.2, 7.5), dpi=300)
    
    pw_dict = {r["image_id"]: r for r in pairwise}
    
    for row_idx, (img_id, cls_name) in enumerate(sample_ids):
        # Load Original
        orig_img = Image.open(orig_dir / f"{img_id}.png")
        tiny_img = Image.open(tiny_dir / f"{img_id}.png")
        jpeg_img = Image.open(jpeg_dir / f"{img_id}.jpg")
        
        info = pw_dict[img_id]
        t_psnr = float(info["tinycae_psnr_db"])
        t_ssim = float(info["tinycae_ssim"])
        j_psnr = float(info["jpeg_q70_psnr_db"])
        j_ssim = float(info["jpeg_q70_ssim"])
        j_bytes = int(info["jpeg_q70_bytes"])
        
        # Plot Original
        ax_orig = axes[row_idx, 0]
        ax_orig.imshow(orig_img, interpolation="nearest")
        ax_orig.set_ylabel(f"{cls_name.upper()}\n(#{img_id[-5:]})", fontsize=10, fontweight="bold")
        if row_idx == 0:
            ax_orig.set_title("Ảnh gốc RGB888\n(3072 B | 24 bpp)", fontsize=10, fontweight="bold", pad=8)
        ax_orig.set_xticks([])
        ax_orig.set_yticks([])
        
        # Plot TinyCAE
        ax_tiny = axes[row_idx, 1]
        ax_tiny.imshow(tiny_img, interpolation="nearest")
        ax_tiny.set_xlabel(f"{t_psnr:.2f} dB | {t_ssim:.4f}\n(1024 B)", fontsize=8.5)
        if row_idx == 0:
            ax_tiny.set_title("TinyCAE INT8\n(PSNR | SSIM | Kích thước)", fontsize=10, fontweight="bold", pad=8)
        ax_tiny.set_xticks([])
        ax_tiny.set_yticks([])
        
        # Plot JPEG Q70
        ax_jpeg = axes[row_idx, 2]
        ax_jpeg.imshow(jpeg_img, interpolation="nearest")
        ax_jpeg.set_xlabel(f"{j_psnr:.2f} dB | {j_ssim:.4f}\n({j_bytes} B)", fontsize=8.5)
        if row_idx == 0:
            ax_jpeg.set_title("JPEG Q70 Locked\n(PSNR | SSIM | Kích thước)", fontsize=10, fontweight="bold", pad=8)
        ax_jpeg.set_xticks([])
        ax_jpeg.set_yticks([])

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "visual_reconstruction_grid.png")
    plt.close(fig)
    print("Saved visual_reconstruction_grid.png")
    
    print("All figures generated successfully in", FIGURES_DIR)

if __name__ == "__main__":
    main()
