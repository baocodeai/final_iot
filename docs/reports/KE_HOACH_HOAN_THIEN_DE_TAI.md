# Ke hoach hoan thien de tai ESP32 TinyCAE

Ngay cap nhat: 2026-09-28

## Muc tieu

Hoan thien san pham va bao cao theo de cuong `docs/proposal/Nguyen_Vu_Bao_De_cuong_da_chinh_sua.docx`. Trong tam la dam bao quy trinh thi nghiem co the tai lap, dung chia tap du lieu, co so sanh TinyCAE INT8 voi JPEG tren ESP32, va co bang chung do dac thoi gian/bo nho.

## Trang thai hien tai

Da hoan thanh phan loi ky thuat ban dau:

- Cai dat ESP-IDF v5.5.5.
- Build va flash firmware ESP32 thanh cong.
- Kiem tra UART `PING/PONG` thanh cong.
- Kiem tra CRC anh RGB888 thanh cong.
- Chay JPEG tren ESP32 thanh cong.
- Chay TinyCAE INT8 tren ESP32 thanh cong.
- Co so sanh TinyCAE INT8 voi JPEG Q30/Q50/Q70/Q90 tren tap hardware 20 anh.
- Co thong tin bo nho ESP32/PSRAM.

Da sua ngay 2026-09-28:

- `host/dataset/prepare_splits.py` da duoc sua thanh chia du lieu stratified theo tung lop.
- Tao lai `data/splits/cifar10_seed2026_indices.npz`.
- Tao lai `data/splits/cifar10_seed2026_manifest.json`.
- Tao them CSV manifest cho cac tap:
  - `data/splits/train_manifest.csv`
  - `data/splits/validation_manifest.csv`
  - `data/splits/calibration_manifest.csv`
  - `data/splits/validation_bitrate_manifest.csv`
  - `data/splits/test_manifest.csv`
- Tao lai `data/processed/hardware_test/manifest.csv` va `manifest.json` voi path dung `data/processed/hardware_test/...`.
- Kiem tra cu phap cac script bang `py_compile`: dat.

Ghi chu moi truong:

- Smoke test train TensorFlow chua chay duoc trong terminal hien tai vi Windows Application Control chan DLL `ml_dtypes._ml_dtypes_ext` khi import TensorFlow.
- Loi nay xay ra truoc khi vao code train, nen khong phai loi split du lieu.
- Can chay lai train trong moi truong Python/TensorFlow khong bi policy chan, hoac sua/cai lai moi truong `.venv` neu van gap loi.

## Checklist can lam de dat de cuong

### 1. Du lieu

Trang thai: da sua xong.

Yeu cau da dat:

- Train: 45,000 anh, moi lop 4,500 anh.
- Validation: 5,000 anh, moi lop 500 anh.
- Calibration: 500 anh, moi lop 50 anh.
- Validation bitrate: 500 anh, moi lop 50 anh.
- Test PC: 10,000 anh, moi lop 1,000 anh.
- Hardware test: 20 anh, moi lop 2 anh.

Bang chung:

- `data/splits/cifar10_seed2026_manifest.json`
- `data/processed/hardware_test/manifest.csv`

### 2. Train lai TinyCAE FP32

Trang thai: chua chay lai sau khi sua split.

Can lam:

- Chay lai notebook `notebooks/01_tinycae_fp32.ipynb` hoac script `host/tinycae/train_fp32.py`.
- Luu model vao mot run moi, nen dat ten `stratified_baseline`.
- Luu lai:
  - `encoder.keras`
  - `decoder.keras`
  - `autoencoder.keras`
  - `training_log.csv`
  - `metrics.json`

Lenh goi y:

```powershell
.\.venv\Scripts\Activate.ps1
python .\host\tinycae\train_fp32.py --run-name stratified_baseline --epochs 100 --batch-size 128 --patience 10
```

Lenh smoke test nho truoc khi train dai:

```powershell
python .\host\tinycae\train_fp32.py --run-name stratified_smoke --epochs 1 --batch-size 64 --limit-train 256 --limit-validation 64 --patience 1
```

### 3. Quantize INT8

Trang thai: chua chay lai sau khi sua split.

Can lam:

- Dung calibration set moi trong `data/splits/calibration_manifest.csv`.
- Export lai `models/tinycae/int8/encoder_int8.tflite`.
- Cap nhat `manifests/model_manifest.json`.
- Ghi lai:
  - input scale
  - input zero point
  - output scale
  - output zero point
  - SHA256 model
  - kich thuoc model
  - operators

Notebook lien quan:

- `notebooks/02_tinycae_int8.ipynb`

### 4. Tao golden vector TinyCAE

Trang thai: can chay lai sau khi co model INT8 moi.

Can lam:

- Chay lai golden latent tren 20 anh hardware test.
- Luu lai:
  - input int8
  - latent int8
  - reconstruction PNG
  - CSV summary

Notebook lien quan:

- `notebooks/03_tinycae_golden_vectors.ipynb`

### 5. Kiem tra TinyCAE tren ESP32

Trang thai: can chay lai sau khi flash model INT8 moi.

Can lam:

- Copy model INT8 moi vao firmware.
- Build lai firmware.
- Flash ESP32.
- Chay lai validation 20 anh.
- Chap nhan sai khac latent nho neu chat luong anh gan nhu khong doi, nhung phai bao cao ro:
  - so byte khac
  - delta PSNR
  - delta SSIM
  - mean/max reconstruction delta

Notebook lien quan:

- `notebooks/04_tinycae_esp32_validation.ipynb`

### 6. Chon JPEG Q dung quy trinh

Trang thai: can lam lai.

Van de cu:

- Q30/Q50/Q70/Q90 da duoc chay tren 20 anh hardware test.
- De cuong yeu cau chon Q tren 500 anh validation bitrate truoc, sau do moi khoa Q va test 20 anh hardware.

Can lam:

- Chay JPEG Q30/Q50/Q70/Q90 tren `validation_bitrate` 500 anh.
- Tinh trung binh:
  - bytes
  - BPP
  - PSNR
  - SSIM
  - encode time
- Chon mot Q co bitrate gan TinyCAE nhat.
- Khoa Q duoc chon trong bao cao.
- Sau do moi chay Q da khoa tren 20 anh hardware test.

### 7. Chuan hoa bitstream TinyCAE

Trang thai: can lam.

Van de cu:

- Dang bao cao TinyCAE theo latent 1024 bytes.
- De cuong yeu cau tinh theo goi codec thuc te `B_codec`.

Can lam:

- Them header codec toi thieu cho TinyCAE:
  - magic
  - version
  - model_id
  - width
  - height
  - payload_len
  - crc32
- Tinh lai:
  - `B_codec = header_bytes + latent_bytes`
  - BPP
  - compression ratio

Ghi chu:

- Neu header 16 bytes, TinyCAE se la 1040 bytes thay vi 1024 bytes.
- BPP se la 1040 * 8 / (32 * 32) = 8.125 bpp.

### 8. Do timing dung de cuong

Trang thai: can lam.

Can lam:

- Moi anh/config chay:
  - 5 lan warmup
  - 30 lan do chinh thuc
- Bao cao:
  - mean
  - median
  - p95
  - min/max neu can
- Tach it nhat:
  - `t_core`: thoi gian invoke TinyCAE hoac JPEG encode
  - `t_codec`: thoi gian xu ly day du tu buffer dau vao den bitstream dau ra

### 9. Do bo nho va firmware

Trang thai: da co mot phan, can ghi lai thanh bang chuan.

Da co:

```text
INTERNAL_FREE 287155
INTERNAL_MIN 254452
INTERNAL_LARGEST 155648
PSRAM_FREE 4050484
PSRAM_MIN 4050484
PSRAM_LARGEST 3997696
```

Can bo sung:

- Tensor arena size.
- Stack high-water neu co the.
- Firmware binary size.
- SHA256 firmware hoac ELF neu can truy xuat.

### 10. Bao cao va notebook

Trang thai: can don lai.

Can lam:

- Doi markdown trong notebook sang van phong bao cao, khong viet nhu chat.
- Dam bao notebook chay tu dau den cuoi.
- Tao bao cao tong hop trong `docs/reports/BAO_CAO_HOAN_CHINH.md`.
- Tao bang ket qua cuoi:
  - TinyCAE INT8
  - JPEG Q da khoa
  - bytes
  - BPP
  - compression ratio
  - PSNR
  - SSIM
  - time
  - memory
- Tao hinh minh hoa:
  - anh goc
  - TinyCAE reconstruction
  - JPEG reconstruction
  - bieu do PSNR/BPP
  - bieu do SSIM/BPP
  - bieu do thoi gian
  - anh phan cung ESP32

## Thu tu thuc hien tiep theo

1. Train lai FP32 tren split stratified.
2. Quantize lai INT8.
3. Build/flash firmware voi model INT8 moi.
4. Chay lai TinyCAE ESP32 20 anh.
5. Chay JPEG validation bitrate 500 anh de chon Q.
6. Chay JPEG Q da khoa tren 20 anh hardware.
7. Do timing 5 warmup + 30 repeat.
8. Chuan hoa TinyCAE bitstream va BPP/CR.
9. Cap nhat bang ket qua.
10. Viet bao cao hoan chinh.

## Tieu chi hoan thanh

De tai duoc xem la san sang nop khi co du cac muc sau:

- Split stratified dung de cuong.
- Model TinyCAE INT8 moi co manifest va hash.
- ESP32 chay duoc TinyCAE INT8 va JPEG.
- JPEG Q duoc chon tu 500 anh validation bitrate.
- Ket qua 20 anh hardware test duoc luu thanh CSV.
- Timing co warmup/repeat.
- Memory co bang so lieu.
- Bao cao chinh co ket qua, hinh, bang, nhan xet va ket luan.
- Notebook khong con markdown dang chat.
