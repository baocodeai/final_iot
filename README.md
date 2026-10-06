# ESP32 TinyCAE INT8 và JPEG

Dự án đánh giá hai pipeline nén ảnh CIFAR-10 trên ESP32-CAM:

- JPEG chạy trực tiếp trên ESP32.
- Encoder TinyCAE INT8 chạy trên ESP32, decoder chạy trên máy tính.

## Cấu trúc thư mục

```text
iot-final/
├── README.md
├── requirements.txt
├── docs/
│   ├── proposal/             # Đề cương gốc
│   ├── guides/               # Quy trình triển khai
│   └── reports/              # Nhật ký và báo cáo
├── notebooks/                # Thử nghiệm từng bước trước khi đóng gói thành .py
├── host/
│   ├── dataset/              # Script chuẩn bị dữ liệu và chia tập
│   ├── serial_client/        # Giao tiếp UART và benchmark JPEG
│   └── tinycae/              # Script TinyCAE ổn định
├── firmware/
│   ├── hello_world/          # Kiểm tra ESP-IDF ban đầu
│   └── esp32_codec/          # Firmware codec chính
├── data/
│   ├── raw/                  # File CIFAR-10 gốc, không chỉnh sửa
│   ├── processed/            # Ảnh/raw đã chuẩn bị cho phần cứng
│   └── splits/               # Chỉ số train/validation/calibration cố định
├── models/                   # Checkpoint, encoder, decoder và TFLite
├── manifests/                # Metadata, checksum và thông số lượng tử hóa model
├── bitstreams/               # JPEG/latent do codec tạo
└── results/                  # CSV và chỉ số đánh giá
```

## Nguyên tắc làm việc

1. Thử và hiểu từng bước trong `notebooks/`.
2. Khi notebook chạy đúng, đồng bộ phần ổn định sang `host/*.py`.
3. Không dùng tập test để chọn kiến trúc hoặc checkpoint.
4. Không chỉnh sửa dữ liệu trong `data/raw/`.
5. Mỗi lần đo chính thức phải lưu cấu hình và kết quả vào `results/`.

## Notebook hiện tại

- `notebooks/01_tinycae_fp32.ipynb`: đọc CIFAR-10 cục bộ, kiểm tra phép chia, xây dựng TinyCAE, smoke test và huấn luyện FP32.
- `notebooks/02_tinycae_int8.ipynb`: lượng tử hóa encoder INT8 và so sánh với FP32 trên PC.
- `notebooks/03_tinycae_golden_vectors.ipynb`: tạo input/latent chuẩn cho 20 ảnh để đối chiếu với ESP32.
- `notebooks/04_tinycae_esp32_validation.ipynb`: gửi ảnh qua UART và đối chiếu latent ESP32 với PC.
- `notebooks/05_final_comparison.ipynb`: tổng hợp bảng và biểu đồ TinyCAE–JPEG trên cùng 20 ảnh.

## Môi trường

Trong PowerShell:

```powershell
Set-Location D:\projects\iot-final
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ipykernel install --user --name iot-final --display-name "Python (iot-final)"
```

Sau đó mở notebook và chọn kernel `Python (iot-final)`.
