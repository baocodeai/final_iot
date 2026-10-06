# HƯỚNG DẪN VÀ KỊCH BẢN QUAY VIDEO DEMO NGHIỆM THU

**Đề tài**: Triển khai và đánh giá bộ mã hóa TinyCAE lượng tử hóa INT8 cho nén ảnh trên ESP32 — Đối chứng với bộ mã hóa JPEG phần mềm trên cùng thiết bị  
**Học phần**: Trí tuệ nhân tạo cho IoT  
**Giảng viên hướng dẫn**: Thầy Hồ Nhựt Minh  
**Sinh viên thực hiện**: Nguyễn Vũ Bảo — MSSV: 23110079  
**Thời lượng video khuyến nghị**: 3 đến 5 phút  

---

## 1. Chuẩn bị trước khi quay

### 1.1. Phần cứng
- Cắm bo **ESP32-CAM** (gắn trên đế nạp FT232R) vào cổng USB máy tính.
- Đảm bảo Windows nhận diện cổng `COM5` (kiểm tra trong Device Manager).

### 1.2. Phần mềm
- **Khởi động ứng dụng Desktop GUI**:
  - Nhấp đúp chuột vào file **`run_demo_gui.bat`** tại thư mục gốc dự án (hoặc chạy lệnh `python host/demo/gui_app.py`).
  - Cửa sổ Desktop Native GUI chuyên nghiệp sẽ hiển thị với kích thước $1240 \times 860$, tự động kết nối với bo ESP32 trên cổng `COM5`.
- **Công cụ quay màn hình**:
  - Dùng **OBS Studio** (khuyên dùng): Bố trí màn hình chính quay cửa sổ Desktop App, góc dưới đặt khung camera quay bo mạch ESP32 thật có đèn LED/dây cáp kết nối để tăng tính thuyết phục.
  - Hoặc dùng **Windows Game Bar**: Nhấn tổ hợp phím `Win + Alt + R` để bắt đầu/dừng quay màn hình nhanh chóng.

---

## 2. Kịch bản quay video chi tiết (Thời lượng: ~4 phút)

### Phân đoạn 1: Giới thiệu đề tài và phần cứng (0:00 – 0:45)
- **Hình ảnh hiển thị**: Quay song song cửa sổ ứng dụng Desktop App và bo mạch ESP32-CAM vật lý trên bàn.
- **Lời thoại mẫu**:
  > *"Kính chào Thầy và các bạn. Em tên là Nguyễn Vũ Bảo, sinh viên lớp 261AIOT331185_01CLC, MSSV 23110079. Hôm nay em xin thực hiện video demo nghiệm thu đề tài: 'Triển khai và đánh giá bộ mã hóa TinyCAE lượng tử hóa INT8 cho nén ảnh trên ESP32, đối chứng với bộ mã hóa JPEG phần mềm trên cùng thiết bị'.*  
  > *Thiết bị thử nghiệm của em là bo mạch ESP32-CAM chạy chip Xtensa LX6 dual-core 240 MHz, có 4MB Flash và 8MB PSRAM ngoài, được kết nối với máy tính qua giao tiếp USB-UART COM5 ở tốc độ 115.200 baud."*

---

### Phân đoạn 2: Kết nối và kiểm tra thông số hệ thống (0:45 – 1:30)
- **Thao tác**:
  1. Trên thanh kết nối phần cứng của Desktop App, quan sát đèn trạng thái chuyển màu xanh lá cây `Online: COM5 @ 115200 baud`.
  2. Bấm nút **"Ping (PONG)"** $\to$ Quan sát khung Terminal UART bên dưới nhận phản hồi `[UART RX] PONG` tức thì.
  3. Rê chuột chỉ vào hộp **"THÔNG SỐ BỘ NHỚ ESP32"** ở cột trái.
- **Lời thoại mẫu**:
  > *"Sau khi kết nối cổng COM5, hệ thống lập tức thực hiện bắt tay UART PING/PONG thành công. Firmware trên ESP32 đã khởi tạo sẵn sàng cả hai bộ mã hóa: TinyCAE INT8 với Tensor Arena 128 KiB và JPEG phần mềm với buffer 8 KiB trên PSRAM. Bộ nhớ RAM nội của chip vẫn còn trống dồi dào hơn 287 KiB và PSRAM còn trống hơn 4 MiB, đảm bảo hệ thống hoạt động hoàn toàn an toàn và không bị tràn heap."*

---

### Phân đoạn 3: Thực nghiệm nén ảnh đối chứng trực tiếp (1:30 – 3:15)
- **Thao tác 1 (Ảnh máy bay - TinyCAE vượt trội)**:
  1. Chọn ảnh đầu tiên trong danh sách 20 ảnh: **Airplane** (`#01789`).
  2. Để thanh trượt Quality ở mức **Q = 70** (mức đã khóa trong đề cương).
  3. Bấm nút màu tím: **"🚀 SO SÁNH TRỰC TIẾP CẢ HAI (Side-by-Side)"**.
  4. Quan sát Terminal UART chạy các lệnh gửi ảnh 3.072 bytes, ESP32 nén và phản hồi bitstream nhị phân.
  5. Chỉ vào 3 khung ảnh hiển thị trực quan (kích thước lớn $220 \times 220$ sắc nét) và thanh kết quả đối chứng bên trên.
- **Lời thoại mẫu**:
  > *"Em chọn bức ảnh máy bay trong tập 20 ảnh hardware test và bấm 'So sánh trực tiếp cả hai'. Trên terminal UART, máy tính gửi 3.072 bytes ảnh thô RGB888 xuống ESP32. ESP32 chạy TinyCAE mất 61,7 ms, trả về đúng 1.024 bytes latent; sau đó chạy JPEG mất 2,8 ms, trả về 932 bytes.*  
  > *Về chất lượng tái tạo: TinyCAE đạt PSNR 34,21 dB và SSIM 0,9833; vượt trội hơn JPEG Q70 đạt 32,49 dB và 0,9730 (+1,72 dB PSNR). Nhìn vào ảnh phóng to sắc nét trên màn hình, bề mặt thân máy bay của TinyCAE rất mượt mà, không hề bị hiện tượng vỡ khối hạt (blocking artifact) của lưới 8x8 như bên JPEG.*  
  > *Tuy nhiên, về tốc độ: JPEG mã hóa chỉ mất 2,8 ms, nhanh hơn TinyCAE tới 22 lần do thuật toán DCT không phải tính toán hàng trăm nghìn phép nhân ma trận."*

- **Thao tác 2 (Ảnh con chó - JPEG vượt trội)**:
  1. Chọn ảnh **Dog** (`#01922`).
  2. Bấm nút **"🚀 SO SÁNH TRỰC TIẾP CẢ HAI"**.
- **Lời thoại mẫu**:
  > *"Tiếp theo, em thử nghiệm với bức ảnh con chó có nhiều kết cấu sợi lông phức tạp. Ở hoạt cảnh này, JPEG Q70 lại nhỉnh hơn TinyCAE 1,44 dB PSNR. Điều này phản ánh đúng thực tế nghiên cứu: mạng tích chập thu nhỏ thiên về làm mượt và bảo tồn cấu trúc tổng thể, trong khi biến đổi DCT của JPEG giữ tốt hơn các biến thiên tần số cao tại bitrate cao. Kết quả này hoàn toàn khớp với số liệu trong báo cáo và bảng ghép cặp pairwise."*

---

### Phân đoạn 4: Thử nghiệm tải ảnh tùy chọn ngoài tập dữ liệu (3:15 – 4:00)
- **Thao tác**:
  1. Bấm nút **"📁 Tải ảnh tùy chọn từ máy tính..."**.
  2. Chọn một bức ảnh bất kỳ từ ổ đĩa (ví dụ: ảnh phong cảnh, ảnh chụp logo trường hoặc ảnh cá nhân).
  3. Hệ thống tự động cắt vuông và resize về $32 \times 32$ pixel.
  4. Bấm **"🚀 SO SÁNH TRỰC TIẾP CẢ HAI"**.
- **Lời thoại mẫu**:
  > *"Để chứng minh hệ thống không bị overfit hay chỉ chạy được trên 20 ảnh mẫu cố định, em bấm tải một bức ảnh bất kỳ từ máy tính lên. Chương trình tự động chuẩn hóa về kích thước 32x32 RGB888 và đẩy trực tiếp xuống ESP32 qua UART.*  
  > *Kết quả cho thấy ESP32 nén và máy tính tái tạo hoàn hảo bức ảnh mới, chứng minh pipeline hoạt động thực tế 100% trên dữ liệu thực tế."*

---

### Phân đoạn 5: Tự động chạy hàng loạt và kết luận (4:00 – 4:45)
- **Thao tác**:
  1. Bấm nút màu cam: **"⚡ Chạy tự động 20 ảnh"** $\to$ quan sát hệ thống tự động lướt qua từng ảnh và cập nhật chỉ số trực tiếp.
  2. Tóm tắt kết luận.
- **Lời thoại mẫu**:
  > *"Cuối cùng, em cho chạy chế độ kiểm thử tự động trên toàn bộ 20 ảnh hardware test.*  
  > *Tóm lại, đề tài đã đạt được 3 kết luận then chốt:*  
  > *1. TinyCAE INT8 hoàn toàn khả thi trên vi điều khiển ESP32 với bộ nhớ mô hình chỉ 9,5 KB và độ chính xác số học sai lệch tối đa 1 LSB.*  
  > *2. TinyCAE tạo ra kích thước gói cố định tuyệt đối 1.024 bytes (8 bpp), cực kỳ thuận lợi cho truyền thông không dây IoT băng hẹp để tránh phân mảnh MTU.*  
  > *3. Đổi lại, JPEG có lợi thế áp đảo về tốc độ tính toán (2,4 ms so với 60,7 ms), rất thích hợp cho các cảm biến chạy pin cần ngủ sâu ngay lập tức.*  
  > *Em xin chân thành cảm ơn Thầy Hồ Nhựt Minh đã hướng dẫn em hoàn thành đề tài này!"*

---

## 3. Mẹo để video đạt điểm tuyệt đối

1. **Hiển thị cả phần cứng thật**: Trong khung hình, hãy đặt bo ESP32-CAM có cắm cáp USB để Thầy thấy đây là thí nghiệm chạy thật trên kit phần cứng, không phải chạy giả lập trên máy tính.
2. **Nói rõ về trade-off (đánh đổi kỹ thuật)**: Đừng chỉ khen TinyCAE hay JPEG, mà hãy nhấn mạnh tính chất *đánh đổi* (Trade-off: Tốc độ vs. Kích thước cố định vs. Méo dạng khối) — đây là điểm giảng viên đánh giá rất cao về tư duy kỹ thuật.
3. **Mở sẵn terminal**: Terminal UART hiển thị các dòng byte thực tế là bằng chứng thép chứng minh giao thức truyền nhận nhị phân hoạt động ổn định trên phần cứng thật.
