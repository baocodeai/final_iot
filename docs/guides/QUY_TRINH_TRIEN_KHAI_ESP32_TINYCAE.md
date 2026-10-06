# Quy trình triển khai TinyCAE INT8 và JPEG trên ESP32-CAM

## 1. Mục tiêu tài liệu

Tài liệu này hướng dẫn từng bước triển khai đề tài nén ảnh trên ESP32, từ khi chưa có kinh nghiệm với bo mạch đến khi thu được kết quả thực nghiệm. Hệ thống triển khai hai pipeline trên cùng một thiết bị:

- **P1 TinyCAE:** PC gửi ảnh RGB888 32 x 32 xuống ESP32; ESP32 chạy encoder TinyCAE INT8 và trả latent; PC giải lượng tử, chạy decoder và tính chỉ số chất lượng.
- **P2 JPEG:** PC gửi cùng ảnh RGB888 xuống ESP32; ESP32 mã hóa JPEG phần mềm và trả toàn bộ luồng JPEG; PC giải mã và tính cùng các chỉ số.

Phiên bản cơ sở sử dụng ảnh CIFAR-10 và giao tiếp USB-UART. Camera gắn trên ESP32-CAM không phải đầu vào của thí nghiệm chính.

## 2. Phần cứng hiện có và giả định

Bo trong ảnh được nhận dạng sơ bộ là **ESP32-CAM kiểu AI-Thinker**, gắn camera OV2640. Cần chụp mặt sau và đọc dòng chữ trên module kim loại để xác nhận chính xác biến thể, dung lượng flash và PSRAM.

Trong ESP-IDF, target dự kiến là:

```powershell
idf.py set-target esp32
```

Không sử dụng target `esp32s3` cho bo này.

### 2.1. Thiết bị cần có

- ESP32-CAM.
- Một đế ESP32-CAM-MB có cổng USB, hoặc bộ chuyển USB-to-UART/FTDI.
- Cáp USB hỗ trợ truyền dữ liệu.
- Máy tính Windows.
- Nếu dùng USB-to-UART rời: dây cắm breadboard cái-cái.
- Nguồn 5 V ổn định nếu bộ USB-to-UART không cấp đủ dòng.

### 2.2. Cách kiểm tra cáp USB

Cắm thiết bị vào máy tính và mở **Device Manager**. Cáp có khả năng truyền dữ liệu khi Windows phát hiện thiết bị mới, thường xuất hiện trong **Ports (COM & LPT)** dưới một trong các tên:

- USB Serial Device.
- Silicon Labs CP210x.
- CH340 hoặc CH341.
- FTDI USB Serial Port.

Nếu bo chỉ sáng đèn nhưng không có thiết bị mới, cần thử cáp khác trước khi sửa driver hoặc firmware.

### 2.3. Nối USB-to-UART với ESP32-CAM

| USB-to-UART | ESP32-CAM | Ghi chú |
|---|---|---|
| 5V | 5V | Cấp nguồn cho bo qua chân 5V |
| GND | GND | Bắt buộc chung mass |
| TX | U0R | TX của bộ chuyển nối với RX của ESP32 |
| RX | U0T | RX của bộ chuyển nối với TX của ESP32 |
| GND | GPIO0 | Chỉ nối khi đưa bo vào chế độ nạp firmware |

Lưu ý an toàn:

- Mức logic TX/RX phải là 3,3 V.
- Không cấp 5 V trực tiếp vào chân 3V3.
- Chỉ thay đổi dây khi đã ngắt nguồn.
- Nếu bo reset liên tục hoặc báo brownout, cần kiểm tra nguồn và dây nối trước.

### 2.4. Chu trình nạp firmware bằng USB-to-UART

1. Ngắt nguồn bo.
2. Nối GPIO0 với GND.
3. Cấp nguồn hoặc cắm USB.
4. Chạy lệnh flash.
5. Sau khi flash hoàn tất, ngắt nguồn.
6. Tháo nối GPIO0-GND.
7. Cấp nguồn lại hoặc nhấn reset để chạy chương trình.

Nếu dùng đế ESP32-CAM-MB có mạch tự động đưa bo vào chế độ nạp, có thể không cần thao tác GPIO0 thủ công.

## 3. Kiến trúc hệ thống

```text
Ảnh CIFAR-10 RGB888 32 x 32 x 3 trên PC
                    |
                    | 3.072 byte raw qua USB-UART
                    v
                 ESP32-CAM
             +------+------+
             |             |
      P1 TinyCAE INT8    P2 JPEG
             |             |
      latent INT8       luồng JPEG
             +------+------+
                    |
                    v
                   PC
      giải mã, PSNR, SSIM, BPP, CR và lưu log
```

Ba loại dung lượng phải được tách riêng:

- `B_codec`: dữ liệu cần để giải mã ảnh; dùng để tính BPP và CR.
- `B_transport`: header khung UART, CRC và metadata truyền.
- `B_model`: model TFLite, decoder, manifest và firmware cài sẵn.

Không được dùng kích thước model làm kích thước ảnh nén.

## 4. Công nghệ và phiên bản

### 4.1. Firmware

- ESP-IDF: sử dụng bản vá mới nhất thuộc nhánh 5.5.x.
- Target: `esp32`.
- TensorFlow Lite Micro: component `esp-tflite-micro` của Espressif.
- JPEG: component `espressif/esp_new_jpeg`, khóa phiên bản sau khi build thành công.
- Ngôn ngữ: C/C++.

Không nâng phiên bản thư viện giữa lúc đo thực nghiệm. Cần commit các tệp `dependencies.lock`, `sdkconfig` hoặc `sdkconfig.defaults` sau khi cấu hình ổn định.

### 4.2. Phần mềm trên PC

- Python 3.11 64-bit.
- TensorFlow.
- NumPy.
- scikit-image.
- Pillow.
- PySerial.
- pandas và matplotlib.

Sau khi môi trường chạy ổn định, lưu phiên bản bằng:

```powershell
pip freeze > requirements.txt
```

## 5. Cấu trúc thư mục dự án

```text
iot-final/
├── configs/
├── manifests/
├── models/
│   ├── checkpoints/
│   ├── encoder_fp32/
│   ├── encoder_int8.tflite
│   └── decoder.keras
├── firmware/
│   ├── hello_world/
│   ├── tflm_hello_world/
│   └── esp32_codec/
├── host/
│   ├── dataset/
│   ├── training/
│   ├── quantization/
│   ├── serial_client/
│   └── evaluation/
├── bitstreams/
│   ├── tinycae/
│   └── jpeg/
├── reconstructions/
├── logs/
├── report/
├── requirements.txt
└── QUY_TRINH_TRIEN_KHAI_ESP32_TINYCAE.md
```

Không cần tạo toàn bộ thư mục ngay từ đầu. Chỉ tạo khi bắt đầu sử dụng để tránh sinh cấu trúc rỗng khó quản lý.

## 6. Lộ trình triển khai

## Giai đoạn 0. Xác nhận phần cứng

### Công việc

- [ ] Chụp rõ mặt trước và mặt sau bo.
- [ ] Ghi model in trên vỏ kim loại.
- [ ] Xác định có đế ESP32-CAM-MB hay chỉ có bo rời.
- [ ] Xác định chip USB-to-UART nếu dùng bộ chuyển rời.
- [ ] Xác định cổng COM trong Device Manager.
- [ ] Kiểm tra cáp USB có truyền dữ liệu.

### Điều kiện hoàn thành

- Biết chính xác loại chip, cổng COM và cách đưa bo vào chế độ flash.
- Không có dấu hiệu nguồn yếu hoặc reset liên tục.

## Giai đoạn 1. Cài ESP-IDF và chạy Hello World

### 1.1. Cài đặt

1. Cài Visual Studio Code.
2. Cài extension **ESP-IDF** của Espressif.
3. Mở Command Palette và chọn **ESP-IDF: Open ESP-IDF Installation Manager**.
4. Chọn cài đặt tùy chỉnh và cài bản mới nhất thuộc nhánh ESP-IDF 5.5.x.
5. Sau khi cài, mở **ESP-IDF Terminal** từ Installation Manager hoặc VS Code.

Kiểm tra:

```powershell
idf.py --version
```

### 1.2. Sao chép ví dụ Hello World

```powershell
New-Item -ItemType Directory -Force D:\projects\iot-final\firmware

Copy-Item "$env:IDF_PATH\examples\get-started\hello_world" `
  "D:\projects\iot-final\firmware\hello_world" -Recurse

Set-Location D:\projects\iot-final\firmware\hello_world
idf.py set-target esp32
idf.py build
```

### 1.3. Flash và theo dõi log

Thay `COM5` bằng cổng thực tế:

```powershell
idf.py -p COM5 flash monitor
```

Thoát monitor bằng `Ctrl+]`.

Nếu dùng USB-to-UART rời và flash thất bại:

1. Xác nhận GPIO0 đang nối GND.
2. Nhấn reset ngay khi lệnh bắt đầu kết nối.
3. Kiểm tra TX-RX đã nối chéo.
4. Giảm baud flash nếu kết nối không ổn định:

```powershell
idf.py -p COM5 -b 115200 flash
```

### Điều kiện hoàn thành

- [ ] `idf.py build` thành công.
- [ ] Flash thành công.
- [ ] Monitor hiển thị `Hello world`.
- [ ] Ghi lại model chip, flash size và thông tin PSRAM từ log.

## Giai đoạn 2. Giao tiếp PC và ESP32

Không tích hợp JPEG hoặc TinyCAE trước khi truyền dữ liệu ổn định.

### 2.1. Mốc PING-PONG

Firmware nhận lệnh `PING` và trả `PONG`. Phiên bản đầu có thể dùng văn bản để dễ gỡ lỗi.

### 2.2. Mốc truyền ảnh raw

PC tạo hoặc đọc một ảnh RGB888 32 x 32 và gửi đúng 3.072 byte. Firmware:

1. Đọc đủ header.
2. Kiểm tra `payload_length` bằng 3.072.
3. Đọc đủ payload vào buffer.
4. Tính CRC-32.
5. Trả CRC và trạng thái cho PC.

Ban đầu sử dụng baud 115200. Sau khi chạy ổn định mới thử 460800 hoặc 921600. Baud UART không được tính vào thời gian mã hóa chính.

### 2.3. Khung truyền nhị phân đề xuất

Mọi số nguyên nhiều byte sử dụng little-endian.

```text
Request
magic[4] | version:u8 | command:u8 | sequence_id:u16
image_id:u32 | payload_length:u32 | payload[...] | crc32:u32

Response
magic[4] | version:u8 | status:u8 | sequence_id:u16
metadata_length:u32 | payload_length:u32
metadata[...] | payload[...] | crc32:u32
```

Command tối thiểu:

| Giá trị | Tên | Chức năng |
|---:|---|---|
| `0x01` | `PING` | Kiểm tra kết nối |
| `0x10` | `ENCODE_TINYCAE` | Chạy pipeline P1 |
| `0x11` | `ENCODE_JPEG` | Chạy pipeline P2 |
| `0x20` | `GET_DEVICE_INFO` | Đọc cấu hình thiết bị và phiên bản |

Không in log văn bản xen giữa các frame nhị phân. Trong giai đoạn đo chính thức, một cổng COM chỉ được một chương trình sử dụng tại một thời điểm.

### Điều kiện hoàn thành

- [ ] 100 lần PING liên tiếp thành công.
- [ ] Truyền 100 ảnh raw liên tiếp không thiếu byte.
- [ ] CRC trên PC và ESP32 luôn giống nhau.
- [ ] Phát hiện được frame lỗi, payload sai kích thước và timeout.

## Giai đoạn 3. Triển khai JPEG trên ESP32

JPEG được triển khai trước TinyCAE để kiểm chứng trọn vẹn đường truyền và cách lưu bitstream.

### 3.1. Thêm thư viện

Tại thư mục dự án firmware:

```powershell
idf.py add-dependency "espressif/esp_new_jpeg^1.0.2"
idf.py reconfigure
idf.py build
```

Nếu phiên bản này không tương thích với ESP-IDF đã cài, kiểm tra Component Registry, chọn phiên bản tương thích gần nhất và ghi rõ phiên bản thực tế trong manifest. Không tự động nâng phiên bản sau khi đã khóa thí nghiệm.

### 3.2. Trình tự phát triển

1. Tạo một ảnh RGB 32 x 32 đơn sắc trong firmware.
2. Mã hóa ảnh bằng JPEG quality 50, subsampling 4:4:4.
3. Gửi toàn bộ output JPEG về PC.
4. Lưu output thành `.jpg` và mở bằng Pillow.
5. Thay ảnh cố định bằng payload RGB nhận qua UART.
6. Kiểm tra ảnh gradient và ảnh có các kênh R/G/B riêng để phát hiện đảo kênh hoặc sai stride.
7. Chạy quality `5, 15, 25, 35, 45, 55, 65, 75, 85, 95` trên tập validation ghép bitrate.

### 3.3. Dữ liệu phải lưu

- Luồng JPEG đầy đủ, bao gồm header.
- Quality và subsampling.
- Số byte JPEG thực tế.
- Trạng thái encoder.
- Thời gian chuẩn bị, thời gian lõi và tổng thời gian codec.
- Heap tối thiểu, stack còn lại và mọi lỗi bộ nhớ.

### Điều kiện hoàn thành

- [ ] JPEG được tạo trực tiếp trên ESP32.
- [ ] PC giải mã được về RGB 32 x 32.
- [ ] File nhận có đúng số byte firmware báo cáo.
- [ ] Không đảo RGB/BGR, không lệch hàng ảnh.
- [ ] Chạy lặp lại không rò rỉ bộ nhớ rõ ràng.

## Giai đoạn 4. Chuẩn bị dữ liệu CIFAR-10

### 4.1. Chia dữ liệu

Sử dụng seed `2026` và lưu toàn bộ chỉ số ảnh vào manifest.

| Tập | Số ảnh | Mục đích |
|---|---:|---|
| Train | 45.000 | Huấn luyện |
| Validation | 5.000 | Chọn checkpoint và cấu hình |
| Calibration | 500 từ train | PTQ INT8 |
| Validation bitrate | 500 từ validation | Khóa quality JPEG |
| PC test | 10.000 | So sánh TinyCAE FP32 và INT8 |
| Hardware test | 20 từ test | Đánh giá P1/P2 trên ESP32 |

Hardware test lấy đúng hai ảnh mỗi lớp trước khi xem kết quả nén. Với từng ảnh, lưu:

- `image_id`.
- Chỉ số gốc trong CIFAR-10.
- Nhãn lớp.
- SHA-256 của dữ liệu raw.
- Đường dẫn file raw hoặc PNG tham chiếu.

### 4.2. Định dạng raw

- Kích thước: 32 x 32 x 3.
- Thứ tự tensor: HWC.
- Kênh màu: RGB.
- Dtype: `uint8`.
- Liên tiếp theo hàng.
- Tổng kích thước: 3.072 byte.

CIFAR-10 gốc có thể lưu các mặt phẳng màu tách biệt. Phải chuyển thành RGB xen kẽ trước khi gửi ESP32.

## Giai đoạn 5. Huấn luyện TinyCAE trên PC

### 5.1. Tạo môi trường Python

```powershell
Set-Location D:\projects\iot-final
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install tensorflow numpy scikit-image pillow pyserial pandas matplotlib
pip freeze > requirements.txt
```

### 5.2. Encoder cơ sở

```text
Input: 32 x 32 x 3
Conv2D: 3 x 3, stride 2, 32 kênh, ReLU
DepthwiseConv2D: 3 x 3, stride 2, multiplier 1, ReLU
Conv2D: 1 x 1, 32 kênh, ReLU
Conv2D: 1 x 1, C_z = 16, linear
Output: 8 x 8 x 16
```

### 5.3. Decoder cơ sở

```text
Input: 8 x 8 x 16
Conv2D 64, 3 x 3, ReLU
Upsample nearest x2
Conv2D 32, 3 x 3, ReLU
Upsample nearest x2
Conv2D 16, 3 x 3, ReLU
Conv2D 3, 3 x 3, sigmoid
Output: 32 x 32 x 3
```

### 5.4. Cấu hình huấn luyện ban đầu

- Optimizer: Adam.
- Learning rate: `1e-3`.
- Batch size: 128.
- Tối đa: 100 epoch.
- Early stopping patience: 10.
- Khôi phục checkpoint có validation loss tốt nhất.
- Loss đề xuất:

```text
L = 0,9 x MSE + 0,1 x (1 - SSIM)
```

Nếu loss kết hợp gây lỗi, dùng MSE làm baseline nhưng phải ghi thay đổi trước khi đánh giá test.

### Điều kiện hoàn thành

- [ ] Encoder và decoder được lưu riêng.
- [ ] Có checkpoint tốt nhất và cấu hình tương ứng.
- [ ] Ảnh tái tạo đúng shape và miền giá trị.
- [ ] Có log train/validation loss.
- [ ] Có PSNR và SSIM trên validation.
- [ ] Chưa sử dụng test để chọn cấu hình.

## Giai đoạn 6. Lượng tử hóa encoder thành INT8

### 6.1. Cấu hình PTQ

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

Tập đại diện gồm 500 ảnh calibration lấy từ train, không lấy từ test.

### 6.2. Manifest model

Tạo `manifests/model_manifest.json` tối thiểu gồm:

```json
{
  "model_id": 1,
  "encoder_sha256": "...",
  "decoder_sha256": "...",
  "input_shape": [1, 32, 32, 3],
  "input_dtype": "int8",
  "input_scale": 0.0,
  "input_zero_point": 0,
  "output_shape": [1, 8, 8, 16],
  "output_dtype": "int8",
  "output_scale": 0.0,
  "output_zero_point": 0,
  "layout": "NHWC"
}
```

Các giá trị scale và zero-point phải được đọc từ file TFLite thực tế, không điền theo ví dụ.

### 6.3. Lượng tử hóa đầu vào

Với ảnh raw `uint8`:

```text
x_float = raw / 255
q = round(x_float / input_scale) + input_zero_point
q = clip(q, -128, 127)
```

Không cast trực tiếp `uint8` sang `int8`, không mặc định chỉ trừ 128.

### 6.4. Kiểm tra FP32 và INT8

Trên cùng 10.000 ảnh test:

- A: encoder FP32 và decoder gốc.
- B: encoder INT8, giải lượng tử latent và cùng decoder gốc.

Lưu chênh lệch PSNR và SSIM theo từng ảnh. Không gán bitrate INT8 cho encoder FP32.

### Điều kiện hoàn thành

- [ ] Model TFLite chỉ dùng toán tử INT8 tương thích.
- [ ] Input và output đều là `int8`.
- [ ] Manifest khớp model thực tế.
- [ ] Decoder nhận đúng latent đã giải lượng tử.
- [ ] Đã định lượng suy giảm chất lượng do PTQ.

## Giai đoạn 7. Chạy TensorFlow Lite Micro trên ESP32

### 7.1. Chạy ví dụ chính thức

```powershell
Set-Location D:\projects\iot-final\firmware
idf.py create-project-from-example "esp-tflite-micro:hello_world"
Rename-Item hello_world tflm_hello_world
Set-Location tflm_hello_world
idf.py set-target esp32
idf.py build
idf.py -p COM5 flash monitor
```

Chỉ tiếp tục khi ví dụ TFLite Micro chạy thành công.

### 7.2. Tích hợp component vào firmware chính

```powershell
Set-Location D:\projects\iot-final\firmware\esp32_codec
idf.py add-dependency "esp-tflite-micro"
idf.py reconfigure
idf.py build
```

Ban đầu dùng `AllOpsResolver` để đưa model lên chạy. Khi ổn định, chuyển sang `MicroMutableOpResolver` và chỉ đăng ký các toán tử thực sự có trong model. Kiến trúc dự kiến cần ít nhất Conv2D và DepthwiseConv2D, nhưng danh sách cuối phải lấy từ file TFLite đã chuyển đổi.

### 7.3. Tensor arena

Khởi đầu với tensor arena khoảng 128-256 KiB rồi điều chỉnh theo kết quả thực tế. Ưu tiên làm cho model chạy đúng trước, sau đó mới tối ưu kích thước và vị trí arena.

Ghi lại:

- Số byte arena cấp phát.
- Số byte arena thực dùng nếu API cung cấp.
- Heap nhỏ nhất.
- Stack high-water mark.
- Model size.
- Firmware size.

### Điều kiện hoàn thành

- [ ] Model schema hợp lệ.
- [ ] `AllocateTensors()` thành công.
- [ ] Input/output tensor đúng dtype và shape.
- [ ] `Invoke()` thành công.
- [ ] Không reset, watchdog hoặc tràn bộ nhớ khi chạy lặp lại.

## Giai đoạn 8. So sánh latent giữa PC và ESP32

Đây là bước bắt buộc trước khi đánh giá ảnh tái tạo.

1. Chọn một ảnh raw có hash cố định.
2. Chạy `encoder_int8.tflite` trên PC.
3. Chạy cùng model và cùng byte input trên ESP32.
4. ESP32 gửi toàn bộ latent 8 x 8 x 16 về PC.
5. So sánh 1.024 phần tử INT8.

Chỉ số cần lưu:

- Số phần tử khác nhau.
- Tỷ lệ phần tử khác nhau.
- Sai lệch nguyên lớn nhất.
- Sai lệch tuyệt đối trung bình.
- PSNR/SSIM sau khi đưa hai latent qua cùng decoder.

Mong muốn là bit-exact. Nếu backend có khác biệt làm tròn, phải định lượng và giải thích thay vì bỏ qua.

### Điều kiện hoàn thành

- [ ] ESP32 trả đúng 1.024 byte latent cho `C_z = 16`.
- [ ] `model_id`, shape và quantization parameters đúng.
- [ ] Sai khác với PC đã được xác định và chấp nhận có lý do.
- [ ] Decoder tạo ảnh hợp lệ từ latent ESP32.

## Giai đoạn 9. Đóng gói codec TinyCAE

Phiên bản cơ sở không dùng entropy coding. Với `C_z = 16`:

- Latent: 8 x 8 x 16 = 1.024 byte.
- Header codec đề xuất: 16 byte.
- Tổng dự kiến: 1.040 byte.
- BPP thiết kế: `1.040 x 8 / 1.024 = 8,125`.
- CR thiết kế: `3.072 / 1.040` xấp xỉ `2,95`.

Header codec 16 byte đề xuất:

```text
magic[4] | version:u8 | codec:u8 | model_id:u16
H:u16 | W:u16 | channels:u8 | layout:u8 | flags:u16
```

Kích thước báo cáo cuối phải lấy từ chuỗi byte thực tế, không dùng con số dự kiến nếu cấu trúc đã thay đổi.

## Giai đoạn 10. Đo thời gian và bộ nhớ

### 10.1. Ranh giới thời gian

```text
t0: ảnh raw đã nằm đầy đủ và hợp lệ trong RAM
t1: chuẩn bị input hoàn tất
t2: lời gọi encoder lõi hoàn tất
t3: B_codec và header đã hoàn chỉnh trong buffer
```

```text
t_prepare = t1 - t0
t_core    = t2 - t1
t_codec   = t3 - t0
```

Dùng `esp_timer_get_time()` và đổi microsecond sang millisecond. Không tính thời gian UART, CRC của khung truyền, giải mã trên PC, ghi file hoặc tính PSNR/SSIM vào `t_codec`.

### 10.2. Quy trình lặp

Với mỗi ảnh và mỗi cấu hình:

- 5 lần warm-up.
- 30 lần đo.
- Lưu mọi lần chạy.
- Báo cáo median và P95.
- Ghi số lần lỗi, timeout và thử lại.

Không xem 20 ảnh x 30 lượt là 600 ảnh độc lập. Đơn vị đánh giá chất lượng vẫn là ảnh.

### 10.3. Bộ nhớ và kích thước

Ghi tối thiểu:

- Kích thước file encoder.
- Kích thước firmware.
- Tensor arena cấp phát và sử dụng.
- Buffer raw và buffer output.
- Heap nhỏ nhất.
- Stack high-water mark.
- Có hoặc không sử dụng PSRAM.
- Lỗi cấp phát hoặc tràn buffer.

Không gọi riêng chênh lệch heap là tổng RAM.

## Giai đoạn 11. Đánh giá thực nghiệm

### 11.1. Chỉ số

Tính trên ảnh RGB `uint8` 32 x 32 x 3:

```text
MSE  = trung bình bình phương sai khác trên H, W và 3 kênh
PSNR = 10 log10(255^2 / MSE)
BPP  = 8 x B_codec / (H x W)
CR   = B_raw / B_codec
```

Trước khi trừ hai ảnh, chuyển về kiểu số có dấu hoặc float để tránh tràn `uint8`.

SSIM được tính theo cấu hình thống nhất cho cả hai pipeline. Lưu rõ các tham số `data_range`, `channel_axis`, `win_size`, `sigma`, `gaussian_weights`, `K1` và `K2`.

### 11.2. Chọn JPEG để ghép bitrate

1. Chạy các quality JPEG trên 500 ảnh validation đã khóa.
2. So sánh BPP trung bình với BPP TinyCAE.
3. Chọn hai mức JPEG kẹp hai phía bitrate TinyCAE nếu có.
4. Khóa quality trước khi chạy 20 ảnh hardware test.
5. Không bỏ header JPEG và không chọn lại ảnh test.

Nếu không có JPEG nào đủ gần bitrate TinyCAE, ghi rõ không có cặp bitrate phù hợp và trình bày các điểm vận hành thực tế.

### 11.3. Bảng kết quả chất lượng

| Cấu hình | Byte TB | BPP TB | CR gộp | PSNR TB | SSIM TB |
|---|---:|---:|---:|---:|---:|
| TinyCAE INT8, C_z = 16 |  |  |  |  |  |
| JPEG mức thấp |  |  |  |  |  |
| JPEG mức cao |  |  |  |  |  |

### 11.4. Bảng tài nguyên

| Cấu hình | t_codec median | t_codec P95 | Arena | Heap tối thiểu | Lượt lỗi |
|---|---:|---:|---:|---:|---:|
| TinyCAE |  |  |  |  |  |
| JPEG |  |  | Không áp dụng |  |  |

## 7. Kế hoạch bốn tuần

| Tuần | Công việc | Điều kiện kết thúc |
|---|---|---|
| 1 | Xác nhận bo; cài ESP-IDF; Hello World; UART; CRC; JPEG | PC gửi ảnh, ESP32 tạo JPEG, PC mở được JPEG |
| 2 | Chia dữ liệu; huấn luyện TinyCAE; PTQ INT8; kiểm tra trên PC | Encoder INT8 và decoder hoạt động, manifest đầy đủ |
| 3 | Chạy TFLite Micro; tích hợp model; so sánh latent PC-ESP32 | Latent ESP32 hợp lệ, decoder tái tạo được ảnh |
| 4 | Ghép hai pipeline; chạy 20 ảnh; đo thời gian/bộ nhớ; tổng hợp | Có bitstream, log, bảng, đồ thị và bằng chứng phần cứng |

Với người mới, bốn tuần là kế hoạch nén. Nếu gặp lỗi phần cứng hoặc tương thích thư viện, nên dành thêm một đến hai tuần dự phòng.

## 8. Kế hoạch một ngày đầu tiên

Mục tiêu hợp lý trong ngày đầu:

1. Xác nhận bo và bộ nạp.
2. Cài ESP-IDF.
3. Chạy Hello World.
4. Gửi PING-PONG qua serial.
5. Nếu còn thời gian, gửi 3.072 byte và kiểm tra CRC.

Không đặt mục tiêu hoàn thành huấn luyện, TinyCAE trên ESP32 và toàn bộ phép đo trong cùng một ngày.

## 9. Các mốc kiểm soát

| Mốc | Tiêu chí |
|---|---|
| M0 | Xác định chính xác bo, bộ nạp và cổng COM |
| M1 | Hello World build, flash và chạy thành công |
| M2 | PC gửi 3.072 byte, CRC hai phía giống nhau |
| M3 | ESP32 tạo JPEG và PC giải mã được |
| M4 | TinyCAE FP32 chạy đúng trên PC |
| M5 | Encoder TFLite INT8 chạy đúng trên PC |
| M6 | Ví dụ TFLite Micro chạy trên ESP32 |
| M7 | Latent ESP32 khớp hoặc gần khớp PC có giải thích |
| M8 | Hai pipeline chạy trong cùng firmware |
| M9 | Thu đủ log 20 ảnh và các lần lặp |
| M10 | Sinh bảng, đồ thị và báo cáo tự động từ log |

Không tiếp tục xây tầng sau khi tầng trước chưa đạt tiêu chí.

## 10. Lỗi thường gặp

### Không thấy cổng COM

- Cáp chỉ hỗ trợ sạc.
- Thiếu driver CH340, CP210x hoặc FTDI.
- USB-to-UART hoặc cổng USB bị lỗi.
- Bo ESP32-CAM không có USB tích hợp và chưa nối bộ chuyển.

### Không flash được

- GPIO0 chưa nối GND khi khởi động vào chế độ flash.
- TX/RX chưa nối chéo.
- Chọn sai cổng COM.
- Nguồn yếu.
- Chọn sai target.
- Một chương trình khác đang giữ cổng COM.

### Flash xong nhưng chương trình không chạy

- Chưa tháo nối GPIO0-GND.
- Chưa reset hoặc cấp nguồn lại.
- Monitor dùng sai baud.
- Firmware reset vì brownout hoặc thiếu bộ nhớ.

### Ảnh sai màu hoặc méo

- Nhầm RGB và BGR.
- Nhầm CIFAR planar với RGB interleaved.
- Sai thứ tự HWC/CHW.
- Sai stride hoặc độ dài hàng.
- Buffer JPEG không căn chỉnh theo yêu cầu của thư viện.

### TinyCAE cho kết quả sai

- Cast thẳng `uint8` sang `int8`.
- Dùng sai scale hoặc zero-point.
- Nhầm decoder/model_id.
- Sai tensor layout.
- Danh sách toán tử TFLite Micro chưa đủ.
- Tensor arena quá nhỏ.

## 11. Nhật ký triển khai

Mỗi phiên làm việc nên bổ sung một dòng:

| Ngày giờ | Mốc | Việc đã làm | Kết quả | Lỗi hoặc quyết định | Bằng chứng |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Mỗi build chính thức cần lưu:

- Commit Git.
- Phiên bản ESP-IDF.
- Phiên bản component.
- Hash model và firmware.
- `sdkconfig`.
- Cổng COM và baud.
- Ảnh hoặc video bo đang chạy.
- Log thô, không chỉ ảnh chụp terminal.

## 12. Tài liệu kỹ thuật chính

- ESP-IDF Get Started: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/>
- Cài ESP-IDF trên Windows: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/windows-setup.html>
- Bắt đầu dự án trên Windows: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/windows-start-project.html>
- ESP-TFLite-Micro: <https://github.com/espressif/esp-tflite-micro>
- ESP New JPEG: <https://components.espressif.com/components/espressif/esp_new_jpeg>
- TensorFlow pip installation: <https://www.tensorflow.org/install/pip>
- Post-training quantization: <https://www.tensorflow.org/model_optimization/guide/quantization/post_training>
- TFLiteConverter API: <https://www.tensorflow.org/api_docs/python/tf/lite/TFLiteConverter>

## 13. Trạng thái hiện tại

- [x] Đã có đề cương nghiên cứu.
- [x] Đã xác định sơ bộ bo là ESP32-CAM kiểu AI-Thinker.
- [ ] Chưa xác nhận mặt sau module, flash và PSRAM.
- [ ] Chưa xác nhận bộ nạp USB-to-UART hoặc ESP32-CAM-MB.
- [ ] Chưa xác nhận cổng COM.
- [ ] Chưa cài hoặc xác minh ESP-IDF.
- [ ] Chưa chạy Hello World.
- [ ] Chưa tạo mã nguồn firmware và host.

Việc tiếp theo là chụp mặt sau bo, chuẩn bị bộ nạp, xác định cổng COM và hoàn thành mốc M1.
