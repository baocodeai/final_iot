# Nhật ký triển khai TinyCAE INT8 và JPEG trên ESP32-CAM

## 1. Thông tin chung

| Mục | Giá trị |
|---|---|
| Đề tài | Triển khai và đánh giá bộ mã hóa TinyCAE lượng tử hóa INT8 cho nén ảnh trên ESP32 |
| Pipeline đối chứng | JPEG phần mềm trên cùng ESP32 |
| Người thực hiện | Nguyễn Vũ Bảo |
| Ngày bắt đầu triển khai | 22/09/2026 |
| Thư mục dự án | `D:\projects\iot-final` |
| Trạng thái hiện tại | Pipeline JPEG trên ESP32 đã tạo và truyền file JPEG hợp lệ |

## 2. Phần cứng đã xác định

### 2.1. Bo phát triển

Qua hình ảnh mặt trước, bo được nhận dạng sơ bộ là ESP32-CAM kiểu AI-Thinker, có camera OV2640. Người thực hiện cho biết mặt sau có ghi `ESP32-S` và có cổng Micro-USB.

`ESP32-S` là tên module sử dụng chip ESP32 đời đầu, không phải ESP32-S2 hoặc ESP32-S3. Vì vậy, target sử dụng trong ESP-IDF là:

```text
esp32
```

Việc nhận dạng model bo, dung lượng flash và PSRAM vẫn cần được xác nhận lại bằng ảnh rõ mặt sau hoặc log khởi động sau khi nạp chương trình.

### 2.2. Giao tiếp USB-UART

Windows ban đầu phát hiện thiết bị:

```text
FT232R USB UART
```

Thiết bị xuất hiện trong nhóm **Other devices** kèm dấu chấm than vàng, cho thấy Windows đã nhận phần cứng nhưng chưa có driver Virtual COM Port.

Sau khi cài driver FTDI, Device Manager hiển thị:

```text
USB Serial Port (COM5)
```

Kết luận:

- Driver FTDI đã hoạt động.
- Cáp USB đang dùng có khả năng truyền dữ liệu.
- Cổng giao tiếp dự kiến với ESP32 là `COM5`.
- Các cổng `COM3` và `COM4` là Bluetooth, không sử dụng cho ESP32.

## 3. Cài đặt ESP-IDF Installation Manager

### 3.1. Cài EIM bằng WinGet

Lệnh đã sử dụng:

```powershell
winget install Espressif.EIM
```

WinGet đã tải bộ cài từ kho phát hành chính thức của Espressif và xác minh hash trước khi cài đặt.

Kết quả kiểm tra:

```text
Name: eim
Id: Espressif.eim
Version: 0.19.0
Source: winget
```

Ứng dụng được cài tại:

```text
C:\Program Files\eim\eim.exe
```

Do ứng dụng hiển thị trong Windows với tên `eim`, lệnh sau đã được dùng để mở trực tiếp:

```powershell
& "C:\Program Files\eim\eim.exe"
```

## 4. Cấu hình cài đặt ESP-IDF

Chế độ **Expert Installation** được sử dụng để kiểm soát target, phiên bản và công cụ cài đặt.

### 4.1. Kiểm tra Python

EIM yêu cầu Python từ 3.10 đến dưới 3.14, có các thành phần:

- `pip`.
- `venv`.
- SSL support.

Máy chưa có phiên bản Python phù hợp được EIM nhận diện. Python đã được cài bằng nút **Install Python** trong EIM. Sau khi cài, bước **Python Sanity Check** đã được vượt qua và EIM chuyển sang chọn target.

Python này phục vụ:

- Chạy `idf.py`.
- Cấu hình và build firmware.
- Flash firmware vào ESP32.
- Quản lý công cụ ESP-IDF.

Môi trường Python dành riêng cho huấn luyện TinyCAE sẽ được tạo sau trong thư mục dự án bằng `.venv`, tách khỏi môi trường công cụ ESP-IDF.

### 4.2. Target chip

Tại bước **Select Target Chips**, chỉ target sau được chọn:

```text
esp32
```

Các target `esp32s2`, `esp32s3`, `esp32c3` và các dòng chip khác không được chọn.

### 4.3. Phiên bản ESP-IDF

Phiên bản stable đã chọn:

```text
ESP-IDF v5.5.5
```

Không chọn:

- ESP-IDF v6.1.
- Các nhánh pre-release.
- Master branch.

Lý do chọn v5.5.5:

- Đây là bản vá stable mới nhất của nhánh 5.5 hiển thị trong EIM.
- Nhánh 5.5 nằm trong phạm vi hỗ trợ của `esp-tflite-micro`.
- Stable release phù hợp hơn pre-release cho dự án cần kết quả có thể tái lập.

### 4.4. Download mirror

Máy ở ngoài Trung Quốc đại lục nên sử dụng các nguồn tải mặc định:

| Thành phần | Mirror ưu tiên |
|---|---|
| ESP-IDF repository | `https://github.com` |
| ESP-IDF tools | `https://dl.espressif.com/github_assets` |
| Python packages | `https://pypi.org/simple` |

EIM có hiển thị trạng thái timeout trong bước thử tốc độ mirror. Quá trình vẫn được tiếp tục với nguồn mặc định; nếu tải thực tế thất bại, mirror sẽ được kiểm tra lại.

### 4.5. ESP-IDF features

Chỉ feature bắt buộc sau được cài:

```text
core
```

Các feature tùy chọn chưa cần cho đề tài nên không chọn:

- `gdbgui`.
- `pytest`.
- `test-specific`.
- `ci`.
- `docs`.
- `ide`.

### 4.6. Development tools

Giữ nguyên 11 công cụ bắt buộc do EIM tự chọn cho target ESP32 và ESP-IDF v5.5.5. Một số công cụ hiển thị gồm:

- `xtensa-esp-elf-gdb`.
- `xtensa-esp-elf`.
- `esp-clang`.
- `esp-clang-libs`.

Công cụ tùy chọn `qemu-xtensa` không được chọn vì dự án sử dụng bo ESP32 thật, không cần giả lập.

### 4.7. Đường dẫn cài đặt

Đường dẫn đã chọn:

```text
C:\esp
```

Đây là đường dẫn hợp lệ, ngắn và không có khoảng trắng, giúp tránh một số lỗi công cụ build trên Windows.

Tùy chọn custom tool download/install folders không được bật. Có thể bật xóa file cài đặt tạm sau khi quá trình hoàn tất để tiết kiệm dung lượng.

## 5. Trạng thái hiện tại

Tại thời điểm cập nhật nhật ký:

- [x] Đã nhận dạng sơ bộ ESP32-CAM và camera OV2640.
- [x] Đã xác định target ESP-IDF là `esp32`.
- [x] Đã cài driver FT232R.
- [x] Đã xác định cổng `COM5`.
- [x] Đã cài EIM 0.19.0.
- [x] Đã cài Python phù hợp qua EIM.
- [x] Đã chọn ESP-IDF v5.5.5.
- [x] Đã chọn target `esp32`.
- [x] Đã chọn feature `core` và các tool bắt buộc.
- [x] Đã chọn đường dẫn `C:\esp`.
- [x] ESP-IDF đã được cài đặt hoàn tất.
- [x] Đã mở IDF PowerShell và kích hoạt môi trường.
- [x] `idf.py --version` trả về ESP-IDF v5.5.5.
- [x] Đã tạo dự án Hello World tại `firmware/hello_world`.
- [x] Đã cấu hình target `esp32`.
- [x] Đã build firmware thành công.
- [x] Đã flash firmware qua COM5.
- [x] Đã chạy Hello World và thu log phần cứng.

## 6. Kết quả Hello World

### 6.1. Môi trường đã xác nhận

```text
ESP-IDF v5.5.5
IDF_PATH = C:\esp\v5.5.5\esp-idf
Python 3.11.15
```

### 6.2. Kết quả build

Firmware và bootloader được tạo thành công. Log kết thúc bằng:

```text
Successfully created esp32 image.
Project build complete.
```

Bootloader có kích thước `0x6610` byte và còn khoảng 9% trong phân vùng bootloader được cấu hình.

### 6.3. Kết quả flash

Firmware được nạp qua `COM5`. Log kết thúc bằng:

```text
Leaving...
Hard resetting via RTS pin...
Done
```

Điều này xác nhận đế nạp hỗ trợ reset qua RTS và hiện chưa cần thao tác GPIO0 thủ công.

### 6.4. Log chạy trên thiết bị

```text
Hello world!
This is esp32 chip with 2 CPU core(s), WiFi/BTBLE,
silicon revision v3.1, 2MB external flash
Minimum free heap size: 304988 bytes
```

Thông tin phần cứng đã xác nhận:

| Thuộc tính | Giá trị |
|---|---|
| Chip target | ESP32 |
| Số lõi CPU | 2 |
| Silicon revision | v3.1 |
| Kết nối tích hợp | Wi-Fi, Bluetooth và BLE |
| Flash ngoài | 4 MB vật lý; firmware hiện cần đổi cấu hình từ 2 MB lên 4 MB |
| Minimum free heap trong Hello World | 304.988 byte |

Log Hello World chưa xác nhận PSRAM. Cần kiểm tra riêng trước khi tích hợp TensorFlow Lite Micro.

### 6.5. Xác nhận dung lượng flash vật lý

Firmware `esp32_codec` phát hiện chip flash 4 MB, trong khi image header ban đầu được cấu hình 2 MB:

```text
Detected size(4096k) larger than the size in the binary image header(2048k)
```

Kết luận: phần cứng có flash 4 MB. Cần đổi `Serial flasher config > Flash size` thành 4 MB và build lại trước khi tích hợp các component lớn.

### 6.6. Firmware PING-PONG

Firmware cơ sở đã được tạo tại:

```text
D:\projects\iot-final\firmware\esp32_codec
```

Chương trình cấu hình UART0 ở 115200 baud và xử lý lệnh văn bản. Log khởi động:

```text
UART PING-PONG ready at 115200 baud
READY
```

Kết quả kiểm tra:

```text
PING -> PONG
lệnh khác -> ERROR UNKNOWN_COMMAND
```

Điều này xác nhận:

- PC gửi được dữ liệu đến ESP32 qua COM5.
- ESP32 nhận, phân tích và phản hồi lệnh.
- UART0, đế FT232R và baud 115200 hoạt động.
- Có thể phát triển giao thức nhị phân và truyền ảnh trên kết nối hiện tại.

### 6.7. Kết quả kiểm tra PSRAM

Đã bật `CONFIG_SPIRAM`, chọn tự động phát hiện, tốc độ 40 MHz và kiểm tra bộ nhớ khi khởi động. Log thiết bị:

```text
esp_psram: Found 8MB PSRAM device
esp_psram: Speed: 40MHz
esp_psram: PSRAM initialized, cache is in low/high (2-core) mode.
esp_psram: Virtual address not enough for PSRAM, map as much as we can. 4MB is mapped
esp_psram: SPI SRAM memory test OK
esp_psram: Adding pool of 4096K of PSRAM memory to heap allocator
esp32_codec: PSRAM initialized: 8388608 bytes
```

Kết luận:

- Bo có chip PSRAM vật lý 8 MB.
- API nhận dạng đầy đủ dung lượng vật lý 8.388.608 byte.
- Do giới hạn vùng địa chỉ của ESP32 đời đầu, 4 MB được ánh xạ và thêm vào heap.
- PSRAM chạy ở 40 MHz.
- Kiểm tra đọc/ghi PSRAM khi khởi động thành công.
- Phần bộ nhớ khả dụng này đủ thuận lợi để thử JPEG và tensor arena của TinyCAE.

Flash vật lý cũng được cấu hình và báo đúng 4 MB trong bootloader.

### 6.8. Kiểm tra PING-PONG tự động từ Python

Đã tạo môi trường Python riêng của dự án tại `.venv`, cài PySerial 3.5 và chạy chương trình:

```text
host/serial_client/ping_test.py
```

Kết quả:

```text
Opening COM5 at 115200 baud...
TX: PING (attempt 1/3)
RX: PONG
PASS: ESP32 replied with PONG.
```

Lần chạy đầu không nhận được PONG do trạng thái DTR/RTS khi Python mở FT232R. Chương trình được sửa để nhả DTR/RTS, chờ ESP32 khởi động và thử lại tối đa ba lần. Sau thay đổi, giao tiếp tự động thành công ngay lần thử đầu.

### 6.9. Truyền payload ảnh và đối chiếu CRC-32

Firmware được mở rộng với lệnh `IMAGE_CRC`. Khi nhận lệnh, ESP32 yêu cầu đúng 3.072 byte, tương ứng ảnh RGB888 32 x 32 x 3, sau đó tính CRC-32 và trả kết quả về PC.

Chương trình kiểm tra:

```text
host/serial_client/image_crc_test.py
```

Kết quả thực tế:

```text
Opening COM5 at 115200 baud...
Payload: 3072 bytes
PC CRC32: 4FCAC72D
TX: IMAGE_CRC
RX: READY 3072
TX: 3072 raw bytes
RX: CRC32 4FCAC72D
PASS: 3072-byte payload and CRC-32 match.
```

Kết luận:

- PC gửi đủ 3.072 byte qua COM5.
- ESP32 nhận đúng thứ tự và số lượng byte.
- CRC-32 phía PC và ESP32 khớp chính xác.
- Kết nối hiện đủ điều kiện để thay payload mẫu bằng ảnh CIFAR-10 và triển khai JPEG.
- Mốc M2 về truyền dữ liệu raw đã hoàn thành.

### 6.10. JPEG RGB888 32 x 32 trên ESP32

Đã thêm component:

```text
espressif/esp_new_jpeg 1.0.2
```

Firmware được mở rộng với lệnh `JPEG <quality>`. Cấu hình thử nghiệm đầu tiên:

- Input: RGB888 32 x 32 x 3, 3.072 byte.
- Quality: 50.
- Chroma subsampling: 4:4:4.
- Rotation: 0 độ.
- Output buffer: 8.192 byte trong PSRAM.
- Dữ liệu test: ảnh gradient RGB sinh trên PC.

Kết quả:

```text
TX: JPEG 50
RX: READY 3072
TX: 3072 raw bytes
RX: JPEG 783 7896453D 2488
JPEG bytes: 783
JPEG CRC32: 7896453D
ESP32 core encode time: 2488 us
Decoded image: 32x32, mode=RGB
PASS: ESP32 JPEG stream is complete and decodes correctly.
```

File bằng chứng:

```text
bitstreams/jpeg/test_q50.jpg
```

Ảnh đầu ra đã được kiểm tra trực quan: gradient đỏ-xanh-lam xuất hiện đúng hướng, không có dấu hiệu đảo kênh, lệch hàng hoặc hỏng luồng JPEG.

Chỉ số sơ bộ cho ảnh test này:

- `B_codec = 783` byte.
- `BPP = 783 x 8 / (32 x 32) = 6,1171875` bit/pixel.
- `CR = 3.072 / 783` xấp xỉ `3,923`.
- `t_core = 2.488 us = 2,488 ms`.

Đây là một ảnh gradient tổng hợp, chưa phải kết quả CIFAR-10 và chưa được dùng để kết luận chất lượng hoặc hiệu năng trung bình.

## 7. Kiểm thử JPEG với 20 ảnh CIFAR-10

Đã xác minh file dữ liệu chính thức `data/cifar-10-python.tar.gz` bằng MD5, sau đó dùng seed 2026 chọn cố định 20 ảnh từ test batch, gồm đúng 2 ảnh cho mỗi lớp. Mỗi ảnh được lưu ở cả dạng PNG và RGB888 thô 3.072 byte; danh sách được ghi vào `data/hardware_test/manifest.csv`.

Đã gửi lần lượt cả 20 ảnh qua UART COM5 cho ESP32 nén JPEG ở quality 50, chroma 4:4:4. PC xác minh CRC, giải mã từng JPEG và tính chất lượng so với ảnh gốc.

Kết quả tổng hợp:

- 20/20 ảnh PASS.
- Dung lượng JPEG trung bình: 877,60 byte.
- Tỷ lệ nén trung bình: 3,5092:1.
- BPP trung bình: 6,8563 bit/pixel.
- Thời gian mã hóa lõi ESP32 trung bình: 2.304,40 us, tương đương 2,3044 ms.
- PSNR trung bình: 29,1380 dB.
- SSIM trung bình: 0,945990.

File bằng chứng:

```text
results/cifar10_jpeg_q50.csv
results/cifar10_jpeg_q50_summary.txt
bitstreams/jpeg/cifar10_q50/
```

### Bước tiếp theo

1. Kiểm tra trực quan một số cặp ảnh gốc/JPEG.
2. Chạy thêm các mức quality để tạo đường cong chất lượng–dung lượng.
3. Hoàn thiện xử lý timeout và frame lỗi trước đợt đo chính thức.
4. Bắt đầu tích hợp mô hình TinyCAE INT8 sau khi chốt cấu hình JPEG.

### So sánh nhiều mức JPEG quality

Đã chạy lại cùng tập cố định 20 ảnh tại bốn mức quality. Tất cả 80 lượt mã hóa đều PASS kiểm tra truyền, CRC và giải mã JPEG.

| Quality | JPEG trung bình (byte) | Tỷ lệ nén | BPP | Thời gian ESP32 (ms) | PSNR (dB) | SSIM |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 810,15 | 3,7976:1 | 6,3293 | 2,2615 | 27,3945 | 0,921914 |
| 50 | 877,60 | 3,5092:1 | 6,8563 | 2,3044 | 29,1380 | 0,945990 |
| 70 | 968,55 | 3,1838:1 | 7,5668 | 2,4000 | 31,1838 | 0,964415 |
| 90 | 1.245,80 | 2,4839:1 | 9,7328 | 2,6139 | 36,3437 | 0,987201 |

`Q=70` được chọn làm cấu hình ứng viên cân bằng: PSNR vượt 30 dB và SSIM trên 0,96, trong khi dung lượng trung bình vẫn dưới 1 KB/ảnh. `Q=50` vẫn được giữ làm mốc nén mạnh hơn để so sánh với TinyCAE.

Bảng tổng hợp máy đọc được lưu tại `results/jpeg_quality_comparison.csv`.

## 10. Chuẩn bị huấn luyện TinyCAE FP32

Đã cài và xác minh TensorFlow 2.21.0 trong môi trường `.venv` của dự án. TensorFlow chạy bằng CPU trên Windows native.

Đã tạo phép chia CIFAR-10 cố định với seed 2026:

- Train: 45.000 ảnh.
- Validation: 5.000 ảnh.
- Calibration: 500 ảnh thuộc train.
- Validation bitrate: 500 ảnh thuộc validation.
- PC test: toàn bộ 10.000 ảnh test.

Manifest và chỉ số được lưu tại:

```text
data/splits/cifar10_seed2026_manifest.json
data/splits/cifar10_seed2026_indices.npz
```

Đã tạo `host/tinycae/train_fp32.py` theo đúng kiến trúc encoder đầu ra 8 x 8 x 16 và decoder đầu ra 32 x 32 x 3. Smoke test dùng 256 ảnh train, 64 ảnh validation và 1 epoch đã PASS:

- Encoder: 2.800 tham số.
- Decoder: 32.803 tham số.
- Latent: 8 x 8 x 16.
- Model encoder, decoder và autoencoder đều lưu thành công.

Kết quả smoke test chỉ dùng kiểm tra pipeline, không dùng làm kết quả nghiên cứu. Bước tiếp theo là huấn luyện chính thức trên 45.000/5.000 ảnh với early stopping.

## 11. TinyCAE FP32, INT8 và golden vectors

Encoder FP32 đã được lượng tử hóa toàn phần sang INT8 bằng 500 ảnh calibration thuộc tập train. Model `encoder_int8.tflite` có thông tin:

- Kích thước: 9.560 byte.
- SHA-256: `d46a8c3da4df0937128e9926d42619c8716fadec31c647d900187795d10af14d`.
- Input: `[1, 32, 32, 3]`, INT8, scale `0.003921568859368563`, zero point `-128`.
- Output: `[1, 8, 8, 16]`, INT8, scale `0.005573478527367115`, zero point `-7`.
- Latent: 1.024 byte, BPP 8,0, tỷ lệ nén raw/latent 3:1.

Đánh giá trên toàn bộ 10.000 ảnh test:

| Model | PSNR (dB) | SSIM |
|---|---:|---:|
| TinyCAE FP32 | 31,612825 | 0,965454 |
| Encoder INT8 + decoder FP32 | 30,683941 | 0,959357 |
| Chênh lệch INT8 - FP32 | -0,928887 | -0,006097 |

Golden vectors trên đúng 20 ảnh hardware test:

- 20/20 PASS.
- 20 input INT8 đúng 3.072 byte.
- 20 latent INT8 đúng 1.024 byte.
- PSNR trung bình: 30,559910 dB.
- SSIM trung bình: 0,967998.
- Mỗi ảnh chạy hai lần trên PC cho latent giống tuyệt đối.

Đã chuẩn bị mã tích hợp `esp-tflite-micro` 1.4.x vào firmware, nhúng model có checksum khớp và thêm lệnh UART `TINYCAE`. Trạng thái tại thời điểm ghi: **chưa build, chưa flash và chưa có kết quả ESP32**, do người thực hiện sẽ chủ động chạy các lệnh kiểm thử.

### Build, flash và khởi tạo TinyCAE trên ESP32

Firmware tích hợp TensorFlow Lite Micro đã build đủ 1.230 bước và flash thành công qua COM5. Binary ứng dụng có kích thước `0x5dcf0` byte; phân vùng ứng dụng 1 MB còn trống 63%.

Log khởi động xác nhận:

```text
tinycae: TinyCAE ready: model=9560 bytes arena=131072 bytes
input=(scale 0.0039215689 zp -128)
output=(scale 0.0055734785 zp -7)
READY
```

PSRAM, tensor arena, schema model và metadata tensor đều đã khởi tạo thành công. Mốc kế tiếp là gửi cùng 20 ảnh qua lệnh `TINYCAE` và so sánh latent ESP32 với golden latent PC.

### Đối chiếu latent và chất lượng PC–ESP32

ESP32 đã xử lý đủ 20 ảnh hardware test, mỗi ảnh trả đúng 1.024 byte latent và CRC hợp lệ. Do PC dùng kernel TFLite tham chiếu còn ESP32 dùng kernel TFLite Micro/ESP-NN tối ưu, latent không bit-exact:

- 17/20 ảnh lệch tối đa 1 LSB.
- 3/20 ảnh lệch tối đa 2 LSB.
- Không ảnh nào lệch quá 2 LSB.
- Thời gian `Invoke()` trung bình: 60.723,55 us, tương đương 60,724 ms/ảnh.

Tác động lên ảnh tái tạo khi hai latent được đưa qua cùng decoder FP32:

| Chỉ số | Golden PC | ESP32 | ESP32 - PC |
|---|---:|---:|---:|
| PSNR (dB) | 30,555948 | 30,554998 | -0,000951 |
| SSIM | 0,96797591 | 0,96793222 | -0,00004374 |

Sai khác tuyệt đối trung bình giữa hai ảnh tái tạo là `0,00091629`, cực đại `0,02590036` trong miền `[0,1]`. Ảnh hưởng thực tế của khác biệt kernel là không đáng kể; triển khai TinyCAE INT8 trên ESP32 được đánh giá **PASS với dung sai số học tối đa 2 LSB**.

## 12. So sánh TinyCAE INT8 và JPEG trên cùng 20 ảnh

| Codec | Byte/ảnh | BPP | Tỷ lệ nén | PSNR (dB) | SSIM | Thời gian lõi ESP32 (ms) |
|---|---:|---:|---:|---:|---:|---:|
| TinyCAE INT8 | 1.024,00 | 8,0000 | 3,0000:1 | 30,5550 | 0,967932 | 60,724 |
| JPEG Q30 | 810,15 | 6,3293 | 3,7976:1 | 27,3945 | 0,921914 | 2,261 |
| JPEG Q50 | 877,60 | 6,8563 | 3,5092:1 | 29,1380 | 0,945990 | 2,304 |
| JPEG Q70 | 968,55 | 7,5668 | 3,1838:1 | 31,1838 | 0,964415 | 2,400 |
| JPEG Q90 | 1.245,80 | 9,7328 | 2,4839:1 | 36,3437 | 0,987201 | 2,614 |

JPEG Q70 là điểm bitrate gần TinyCAE nhất trong các cấu hình đã đo. So với JPEG Q70, TinyCAE:

- Dùng nhiều hơn 55,45 byte/ảnh, tương đương BPP cao hơn 0,4332.
- PSNR thấp hơn khoảng 0,6288 dB.
- SSIM cao hơn khoảng 0,00352.
- Chậm hơn khoảng 25,3 lần về thời gian lõi trên ESP32.

Kết quả không cho thấy TinyCAE cơ sở vượt JPEG toàn diện. TinyCAE chứng minh khả năng triển khai encoder học sâu INT8 với latent cố định trên ESP32; JPEG nổi trội về tốc độ, khả năng điều chỉnh quality và hiệu quả rate–distortion ở cấu hình hiện tại. Các biểu đồ được lưu tại `results/figures/`.

## 13. Bộ nhớ ESP32 sau khi khởi tạo codec

Firmware trả kết quả lệnh `STATUS`:

```text
MEM INTERNAL_FREE 287155 INTERNAL_MIN 254452 INTERNAL_LARGEST 155648
PSRAM_FREE 4050484 PSRAM_MIN 4050484 PSRAM_LARGEST 3997696
```

Diễn giải:

- RAM nội còn trống: 287.155 byte.
- RAM nội thấp nhất kể từ khi boot: 254.452 byte.
- Khối RAM nội liên tục lớn nhất: 155.648 byte.
- PSRAM còn trống: 4.050.484 byte.
- PSRAM thấp nhất kể từ khi boot: 4.050.484 byte.
- Khối PSRAM liên tục lớn nhất: 3.997.696 byte.
- Tensor arena TinyCAE: 131.072 byte trong PSRAM.
- Buffer JPEG: 8.192 byte trong PSRAM.

Các số liệu cho thấy firmware còn biên bộ nhớ lớn sau khi đồng thời khởi tạo JPEG và TinyCAE. Không xuất hiện dấu hiệu cạn heap hoặc phân mảnh nghiêm trọng trong phạm vi thí nghiệm.

## 14. Trạng thái hoàn thành phần thực nghiệm

- [x] UART PC–ESP32 ổn định và có CRC.
- [x] PSRAM và flash được cấu hình đúng.
- [x] JPEG chạy trên ESP32 và được đo ở bốn mức quality.
- [x] TinyCAE FP32 được huấn luyện và đánh giá.
- [x] Encoder được lượng tử hóa toàn phần INT8.
- [x] TinyCAE INT8 chạy trên PC và toàn bộ 10.000 ảnh test.
- [x] TinyCAE INT8 chạy trên ESP32 với 20 ảnh hardware test.
- [x] Sai khác PC–ESP32 đã được định lượng.
- [x] Đã đo BPP, tỷ lệ nén, PSNR, SSIM, thời gian và bộ nhớ.
- [x] Đã tạo bảng và biểu đồ so sánh TinyCAE–JPEG.

Phần thực nghiệm cốt lõi của đề tài đã hoàn thành. Công việc còn lại là biên tập báo cáo, chọn hình minh họa, trình bày hạn chế và viết kết luận.

### Ghi chú cấu hình flash

Log cảnh báo chip flash được nhận dạng theo driver generic của ESP-IDF và đề xuất bật `SPI_FLASH_SUPPORT_BOYA_CHIP`. Hiện tại các thao tác build, flash và chạy firmware đều thành công; tùy chọn này sẽ được xem xét trước giai đoạn đo chính thức thay vì thay đổi ngay trong lúc kiểm tra UART.

## 8. Bảng sự cố đã xử lý

| Sự cố | Nguyên nhân | Cách xử lý | Kết quả |
|---|---|---|---|
| FT232R có dấu chấm than | Thiếu driver VCP | Cài driver FTDI | Xuất hiện `USB Serial Port (COM5)` |
| Không tìm thấy EIM trong Start Menu | Ứng dụng hiển thị tên `eim` | Mở trực tiếp `C:\Program Files\eim\eim.exe` | EIM mở thành công |
| EIM không đạt Python Sanity Check | Chưa có Python phù hợp | Dùng nút Install Python trong EIM | Chuyển được sang Select Target |
| Phân vân giữa ESP32-S và ESP32-S3 | `ESP32-S` là tên module, không phải target S3 | Chọn target `esp32` | Cấu hình target đúng |

## 9. Bằng chứng cần bổ sung

- [ ] Ảnh rõ mặt sau module ESP32-CAM.
- [ ] Ảnh màn hình EIM báo Installation Complete.
- [x] Kết quả `idf.py --version`.
- [x] Log build Hello World.
- [x] Log flash qua COM5.
- [x] Log khởi động và thông tin chip/flash.
- [x] Thông tin PSRAM.
- [ ] Ảnh hoặc video bo chạy Hello World.

Nhật ký này sẽ tiếp tục được cập nhật sau mỗi mốc triển khai.
