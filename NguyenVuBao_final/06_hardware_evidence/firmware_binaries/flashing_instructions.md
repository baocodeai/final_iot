# Hướng dẫn nạp Firmware nhị phân ESP32 (Không cần build lại)

Thư mục này chứa đầy đủ các tệp nhị phân đã build sẵn của firmware `esp32_codec` hỗ trợ song song hai bộ mã hóa: **TinyCAE INT8** và **JPEG phần mềm**.

## 1. Danh sách tệp nhị phân và địa chỉ nạp Flash

| Tệp | Dung lượng | Địa chỉ Flash (Offset) | Mô tả |
|---|---|---|---|
| `bootloader.bin` | 26.128 Bytes | `0x1000` | Second stage bootloader của ESP-IDF v5.5.5 |
| `partition-table.bin` | 3.072 Bytes | `0x8000` | Bảng phân vùng (hỗ trợ app 2MB, PSRAM) |
| `esp32_codec.bin` | 384.592 Bytes | `0x10000` | Ứng dụng chính tích hợp TinyCAE INT8 & JPEG |

## 2. Lệnh nạp trực tiếp qua `esptool.py`

Kết nối bo mạch ESP32-CAM qua cổng USB-UART (`COM5`):

```bash
esptool.py --chip esp32 --port COM5 --baud 460800 --before default_reset --after hard_reset write_flash -z \
  0x1000 bootloader.bin \
  0x8000 partition-table.bin \
  0x10000 esp32_codec.bin
```

Hoặc qua `idf.py`:
```bash
idf.py -p COM5 flash
```
