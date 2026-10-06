# Audit so lieu bao cao

Ngay audit: 2026-09-28

File duoc kiem tra:

- `docs/reports/BAO_CAO_HOAN_CHINH_ESP32_TINYCAE.docx`
- `submission_package/01_report_slide/BAO_CAO_HOAN_CHINH_ESP32_TINYCAE.docx`

## Ket luan

So lieu chinh trong bao cao da khop voi cac file nguon trong `models`, `manifests`, `data/splits` va `results`.

Da phat hien va sua mot loi dem theo tung anh:

- Truoc sua: TinyCAE hon JPEG Q70 ve PSNR o `13/20` anh va SSIM o `14/20` anh.
- Dung theo `results/final_pairwise_tinycae_vs_jpeg_q70.csv`: PSNR `11/20` anh va SSIM `12/20` anh.
- Bao cao DOCX da duoc sua thanh `11/20` va `12/20`.

## So lieu nguon da doi chieu

### Train FP32

Nguon: `models/tinycae/stratified_baseline/metrics.json`

- Validation images: `5000`
- MSE: `0.0007575090`
- PSNR: `31.846918 dB`
- SSIM: `0.963764`
- Epochs: `100`
- Encoder parameters: `2800`
- Decoder parameters: `32803`
- Latent shape: `8 x 8 x 16`

### INT8 PC evaluation

Nguon: `models/tinycae/int8/pc_evaluation.json`

- Evaluation images: `10000`
- FP32 PSNR: `31.845419 dB`
- FP32 SSIM: `0.963669`
- INT8 PSNR: `31.583109 dB`
- INT8 SSIM: `0.960281`
- Delta PSNR: `-0.262308 dB`
- Delta SSIM: `-0.003388`

### Model manifest

Nguon: `manifests/model_manifest.json`

- Encoder size: `9560 bytes`
- Encoder SHA-256: `badfe7f849a7d71ba91b87505ba3fc58442df8982c2eee643a626535862bb8c6`
- Input shape: `1 x 32 x 32 x 3`
- Output shape: `1 x 8 x 8 x 16`
- Input scale / zero point: `0.003921568859368563`, `-128`
- Output scale / zero point: `0.004770447965711355`, `-5`
- MACs: `337920`

### Golden vector PC

Nguon: `results/tinycae_golden_20_summary.json`

- Images: `20`
- Passed: `20`
- Latent bytes per image: `1024`
- BPP: `8.0`
- Compression ratio: `3.0`
- Mean PSNR: `31.321335 dB`
- Mean SSIM: `0.967381`

### JPEG validation bitrate

Nguon: `results/jpeg_validation_bitrate_summary.csv`

- Q30: `805.432 B`, `6.2924 bpp`, `27.6138 dB`, `0.908786`, `2.271 ms`
- Q50: `872.186 B`, `6.8140 bpp`, `29.3744 dB`, `0.935867`, `2.323 ms`
- Q70: `960.090 B`, `7.5007 bpp`, `31.3125 dB`, `0.956445`, `2.406 ms`
- Q90: `1238.602 B`, `9.6766 bpp`, `36.2813 dB`, `0.983670`, `2.629 ms`

Quyet dinh: khoa `JPEG Q70`.

### Final hardware comparison

Nguon: `results/final_codec_comparison.csv`

- TinyCAE INT8: `1024.00 B`, `8.0000 bpp`, PSNR `31.3254 dB`, SSIM `0.967408`, mean time `60.704 ms`, P95 `60.712 ms`.
- JPEG Q70 locked: `968.55 B`, `7.5668 bpp`, PSNR `31.1838 dB`, SSIM `0.964415`, mean time `2.432 ms`, P95 `2.534 ms`.

Nguon: `results/final_pairwise_tinycae_vs_jpeg_q70.csv`

- TinyCAE PSNR cao hon JPEG Q70: `11/20` anh.
- TinyCAE SSIM cao hon JPEG Q70: `12/20` anh.
- Delta PSNR trung binh: `+0.14157 dB`.
- Delta SSIM trung binh: `+0.002993`.

## Gioi han kiem tra

Render DOCX bang tool noi bo khong thuc hien duoc do thieu LibreOffice `soffice.exe` trong PATH. Vi vay audit nay xac nhan noi dung va so lieu, con layout nen mo bang Microsoft Word va xuat PDF lan cuoi truoc khi nop.
