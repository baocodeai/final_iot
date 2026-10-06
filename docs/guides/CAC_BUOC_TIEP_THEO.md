# Các bước tiếp theo sau huấn luyện TinyCAE FP32

## Thứ tự thực hiện

1. Đợi notebook `01_tinycae_fp32.ipynb` huấn luyện xong.
2. Chạy cell vẽ loss và kiểm tra không có overfitting nghiêm trọng.
3. Chạy cell đánh giá PSNR/SSIM và xem ảnh tái tạo.
4. Chạy cell lưu `encoder.keras`, `decoder.keras` và `autoencoder.keras`.
5. Mở `02_tinycae_int8.ipynb` và chạy từng cell để lượng tử hóa.
6. Kiểm tra model TFLite có input/output `int8`, latent `8 x 8 x 16` và chỉ dùng toán tử tương thích.
7. So sánh FP32–INT8 trên PC, lưu mức suy giảm PSNR/SSIM.
8. Chỉ khi INT8 trên PC PASS mới tích hợp TensorFlow Lite Micro vào ESP32.
9. So sánh latent của cùng một ảnh giữa PC và ESP32.
10. Benchmark 20 ảnh phần cứng và lập bảng TinyCAE–JPEG cuối cùng.

## Điều kiện chuyển từ FP32 sang INT8

- Có thư mục `models/tinycae/notebook_baseline/`.
- Có `encoder.keras`, `decoder.keras` và `autoencoder.keras`.
- Ảnh tái tạo có đúng shape và miền `[0, 1]`.
- PSNR/SSIM đã được ghi lại.
- Không sử dụng tập test để chọn checkpoint.

## Điều kiện chuyển từ INT8 sang ESP32

- `encoder_int8.tflite` tạo thành công.
- Input và output đều là `int8`.
- Output có shape `[1, 8, 8, 16]`, tương đương 1.024 byte latent.
- `input_scale`, `input_zero_point`, `output_scale`, `output_zero_point` đã lưu trong manifest.
- Model chạy được trên PC và decoder tái tạo được ảnh từ latent INT8.
- Đã đo suy giảm chất lượng so với FP32.
