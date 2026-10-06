# THÔNG SỐ VÀ CẤU HÌNH PHẦN CỨNG THỰC NGHIỆM

## 1. Thông tin Bo mạch phát triển (Development Kit)
- **Tên thương mại**: Bo ESP32-CAM AI-Thinker
- **Module lõi**: ESP32-S (Espressif Systems)
- **Kiến trúc SoC**: Xtensa® Dual-Core 32-bit LX6 Microprocessor
- **Tần số xung nhịp CPU**: 240 MHz (Max)
- **Điện áp hoạt động**: 3.3V (Cấp nguồn qua cổng micro-USB 5V tích hợp trên đế nạp)

## 2. Thông số bộ nhớ (Memory Architecture)
- **ROM tích hợp**: 448 KB (Dành cho bootloader và core functions)
- **SRAM nội bộ**: 520 KB (Trong đó SRAM khả dụng cho Heap hệ thống: ~328 KB)
- **Bộ nhớ Flash ngoài (SPI Flash)**: 4 MB (DIO Mode, 40 MHz)
- **Bộ nhớ PSRAM ngoài (SPI PSRAM)**: 8 MB vật lý (Được ESP-IDF map 4 MB vào không gian heap địa chỉ ảo)

## 3. Phân bổ bộ nhớ cho hai Pipeline nén
- **Pipeline 1 - TinyCAE INT8**:
  - `Tensor Arena`: **128 KiB** cấp phát trên bộ nhớ PSRAM ngoài (`MALLOC_CAP_SPIRAM`).
  - Model weights: 9.560 Bytes nhúng trực tiếp vào Flash/ROData.
  - Vùng đệm ảnh đầu vào: 3.072 Bytes (32 × 32 × 3 RGB888).
  - Vùng đệm Latent ngõ ra: 1.024 Bytes (8 × 8 × 16 INT8).
- **Pipeline 2 - JPEG Software Encoder**:
  - `Output Buffer`: **8 KiB** cấp phát trên PSRAM (`MALLOC_CAP_SPIRAM`).
  - Bộ giải thuật: `esp_new_jpeg` v1.0.2 sử dụng bảng lượng tử hóa chuẩn DCT.

## 4. Giao diện truyền thông máy tính (Host Interface)
- **Chip chuyển đổi USB-UART**: FTDI FT232R USB UART IC
- **Cổng COM hệ thống**: `COM5` (Windows 11)
- **Tốc độ Baudrate**: 115.200 bps
- **Cấu hình khung truyền**: 8 data bits, no parity, 1 stop bit (8N1), không dùng luồng phần cứng (DTR/RTS = False).
- **Giao thức ứng dụng**: Giao thức nhị phân khung dữ liệu đồng bộ kèm mã kiểm tra lỗi CRC-32.
