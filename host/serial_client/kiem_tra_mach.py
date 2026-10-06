"""Script kiem tra toan dien bo mach ESP32-CAM truoc khi demo hoac nghiem thu.

Kiem tra:
1. Nhan dien cong COM5 (FT232R USB-UART).
2. Bat tay UART PING/PONG.
3. Kiem tra trang thai bo nho (Internal RAM, PSRAM).
4. Kiem tra bo ma hoa JPEG tren ESP32 (gui anh, nhan bitstream, do thoi gian).
5. Kiem tra bo ma hoa TinyCAE INT8 tren ESP32 (gui anh, nhan 1024B latent, do thoi gian).
"""

from __future__ import annotations

import io
import sys
import time
import zlib
from pathlib import Path

import serial
import serial.tools.list_ports
from PIL import Image
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORT_DEFAULT = "COM5"
BAUD_DEFAULT = 115200


def print_banner(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_serial_ports() -> str | None:
    print("\n[Bước 1/5] Quét các cổng COM trên máy tính...")
    ports = list(serial.tools.list_ports.comports())
    found_port = None
    for p in ports:
        desc = p.description or ""
        hwid = p.hwid or ""
        is_esp = ("USB" in desc or "FTDI" in desc or "UART" in desc or "0403:6001" in hwid)
        tag = "-> (Có khả năng là ESP32-CAM)" if is_esp else ""
        print(f"  - {p.device}: {desc} {tag}")
        if p.device == PORT_DEFAULT or (found_port is None and is_esp):
            found_port = p.device

    if found_port:
        print(f"  ==> Đã chọn cổng kiểm tra: {found_port}")
        return found_port
    else:
        print("  [!] Không tìm thấy thiết bị USB-UART nào. Vui lòng kiểm tra lại cáp kết nối.")
        return None


def run_diagnostics(port: str = PORT_DEFAULT, baud: int = BAUD_DEFAULT):
    print_banner(f"BẮT ĐẦU KIỂM TRA PHẦN CỨNG BO MẠCH ESP32 TRÊN {port}")

    try:
        ser = serial.Serial(port=port, baudrate=baud, timeout=1.5, write_timeout=2.0)
    except serial.SerialException as e:
        print(f"\n[LỖI] Không thể mở cổng {port}: {e}")
        print("Gợi ý khắc phục:")
        print("  1. Đóng ứng dụng Desktop Demo nếu đang mở (đang chiếm cổng COM5).")
        print("  2. Rút cáp USB ra và cắm lại.")
        print("  3. Kiểm tra Device Manager xem COM5 đã xuất hiện chưa.")
        return False

    ser.dtr = False
    ser.rts = False
    time.sleep(1.0)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    results = {}

    # -------------------------------------------------------------
    # BƯỚC 2: BẮT TAY PING / PONG
    # -------------------------------------------------------------
    print(f"\n[Bước 2/5] Gửi lệnh PING kiểm tra giao tiếp UART...")
    ping_ok = False
    for attempt in range(1, 4):
        print(f"  -> Gửi: PING (lần thử {attempt}/3)")
        ser.write(b"PING\n")
        ser.flush()
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                print(f"  <- Nhận từ ESP32: '{line}'")
                if line == "PONG":
                    ping_ok = True
                    break
        if ping_ok:
            break
        time.sleep(0.3)

    if ping_ok:
        print("  ==> [PASS] Bắt tay UART thành công! Bo ESP32 đang phản hồi tốt.")
        results["ping"] = True
    else:
        print("  ==> [FAIL] ESP32 không phản hồi PONG. Firmware chưa sẵn sàng hoặc sai baudrate.")
        ser.close()
        return False

    # -------------------------------------------------------------
    # BƯỚC 3: KIỂM TRA BỘ NHỚ (STATUS)
    # -------------------------------------------------------------
    print(f"\n[Bước 3/5] Gửi lệnh STATUS truy vấn bộ nhớ SRAM & PSRAM...")
    ser.write(b"STATUS\n")
    ser.flush()
    status_line = ""
    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line.startswith("MEM"):
            status_line = line
            print(f"  <- Nhận từ ESP32: {line}")
            break

    if status_line:
        parts = status_line.split()
        mem_dict = {}
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                mem_dict[parts[i]] = int(parts[i+1])
        
        int_free = mem_dict.get("INTERNAL_FREE", 0) / 1024.0
        psram_free = mem_dict.get("PSRAM_FREE", 0) / (1024.0 * 1024.0)
        print(f"  ==> [PASS] Thông số bộ nhớ:")
        print(f"      + SRAM nội bộ tự do:  {int_free:.1f} KiB")
        print(f"      + PSRAM ngoài tự do:   {psram_free:.2f} MiB")
        results["memory"] = (int_free, psram_free)
    else:
        print("  ==> [WARN] Không nhận được phản hồi MEM từ lệnh STATUS.")

    # -------------------------------------------------------------
    # TẠO ẢNH KIỂM THỬ 32x32 RGB888 (3072 BYTES)
    # -------------------------------------------------------------
    # Tạo một ảnh gradient mẫu có độ tương phản rõ nét
    test_img = np.zeros((32, 32, 3), dtype=np.uint8)
    for y in range(32):
        for x in range(32):
            test_img[y, x, 0] = int(x * 8)
            test_img[y, x, 1] = int(y * 8)
            test_img[y, x, 2] = int((x + y) * 4)
    raw_bytes = test_img.tobytes()
    raw_crc = zlib.crc32(raw_bytes) & 0xFFFFFFFF
    raw_crc_hex = f"{raw_crc:08X}"

    # -------------------------------------------------------------
    # BƯỚC 4: KIỂM TRA BỘ MÃ HÓA JPEG TRÊN ESP32
    # -------------------------------------------------------------
    print(f"\n[Bước 4/5] Kiểm tra bộ mã hóa JPEG phần mềm trên ESP32...")
    cmd_jpeg = f"JPEG 70 3072 {raw_crc_hex}\n".encode("ascii")
    print(f"  -> Gửi lệnh: {cmd_jpeg.strip().decode('ascii')} + truyền 3.072 bytes ảnh...")
    ser.write(cmd_jpeg)
    ser.write(raw_bytes)
    ser.flush()

    jpeg_header = None
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line.startswith("JPEG "):
            jpeg_header = line
            print(f"  <- Nhận header: {line}")
            break
        elif line.startswith("ERR"):
            print(f"  <- [LỖI TỪ ESP32]: {line}")
            break

    if jpeg_header:
        parts = jpeg_header.split()
        jpeg_size = int(parts[1])
        jpeg_expected_crc = parts[2].upper()
        jpeg_time_us = int(parts[3])

        # Đọc dữ liệu JPEG nhị phân
        jpeg_bytes = ser.read(jpeg_size)
        jpeg_actual_crc = f"{zlib.crc32(jpeg_bytes) & 0xFFFFFFFF:08X}"

        if len(jpeg_bytes) == jpeg_size and jpeg_actual_crc == jpeg_expected_crc:
            # Giải mã thử bằng PIL
            try:
                img_dec = Image.open(io.BytesIO(jpeg_bytes))
                print(f"  ==> [PASS] Mã hóa JPEG thành công!")
                print(f"      + Dung lượng JPEG:      {len(jpeg_bytes)} Bytes")
                print(f"      + Thời gian mã hóa:     {jpeg_time_us / 1000.0:.2f} ms")
                print(f"      + Mã băm CRC32:         {jpeg_actual_crc} (Khớp hoàn toàn)")
                print(f"      + Kích thước ảnh nén:   {img_dec.size[0]}x{img_dec.size[1]} RGB")
                results["jpeg"] = (len(jpeg_bytes), jpeg_time_us / 1000.0)
            except Exception as e:
                print(f"  ==> [LỖI] Nhận đủ byte nhưng không thể giải mã JPEG: {e}")
        else:
            print(f"  ==> [FAIL] Lỗi CRC hoặc thiếu byte JPEG: nhận {len(jpeg_bytes)}/{jpeg_size}")
    else:
        print("  ==> [FAIL] ESP32 không phản hồi kết quả JPEG.")

    time.sleep(0.2)

    # -------------------------------------------------------------
    # BƯỚC 5: KIỂM TRA BỘ MÃ HÓA TINYCAE INT8 TRÊN ESP32
    # -------------------------------------------------------------
    print(f"\n[Bước 5/5] Kiểm tra bộ mã hóa TinyCAE INT8 trên ESP32...")
    cmd_tiny = f"TINYCAE 3072 {raw_crc_hex}\n".encode("ascii")
    print(f"  -> Gửi lệnh: {cmd_tiny.strip().decode('ascii')} + truyền 3.072 bytes ảnh...")
    ser.write(cmd_tiny)
    ser.write(raw_bytes)
    ser.flush()

    tiny_header = None
    deadline = time.monotonic() + 4.0
    while time.monotonic() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line.startswith("LATENT "):
            tiny_header = line
            print(f"  <- Nhận header: {line}")
            break
        elif line.startswith("ERR"):
            print(f"  <- [LỖI TỪ ESP32]: {line}")
            break

    if tiny_header:
        parts = tiny_header.split()
        latent_size = int(parts[1])
        latent_expected_crc = parts[2].upper()
        latent_time_us = int(parts[3])

        latent_bytes = ser.read(latent_size)
        latent_actual_crc = f"{zlib.crc32(latent_bytes) & 0xFFFFFFFF:08X}"

        if len(latent_bytes) == 1024 and latent_actual_crc == latent_expected_crc:
            print(f"  ==> [PASS] Suy luận TinyCAE INT8 thành công!")
            print(f"      + Dung lượng Latent:    {len(latent_bytes)} Bytes (Đúng 1024 B / 8.00 bpp)")
            print(f"      + Thời gian suy luận:   {latent_time_us / 1000.0:.2f} ms")
            print(f"      + Mã băm CRC32:         {latent_actual_crc} (Khớp hoàn toàn)")
            results["tinycae"] = (len(latent_bytes), latent_time_us / 1000.0)
        else:
            print(f"  ==> [FAIL] Lỗi CRC hoặc sai kích thước latent: nhận {len(latent_bytes)}/{latent_size}")
    else:
        print("  ==> [FAIL] ESP32 không phản hồi kết quả TinyCAE.")

    ser.close()

    # -------------------------------------------------------------
    # TỔNG KẾT KẾT QUẢ
    # -------------------------------------------------------------
    print_banner("TỔNG KẾT KẾT QUẢ KIỂM TRA PHẦN CỨNG ESP32-CAM")
    print(f"  [1] Kết nối cổng {port}:            [OK] Đã kết nối")
    print(f"  [2] Giao tiếp UART (PING/PONG):     [{'OK' if results.get('ping') else 'FAIL'}]")
    if "memory" in results:
        print(f"  [3] Bộ nhớ SRAM nội / PSRAM:        [OK] SRAM: {results['memory'][0]:.1f} KB | PSRAM: {results['memory'][1]:.2f} MB")
    if "jpeg" in results:
        print(f"  [4] Bộ mã hóa JPEG phần mềm:        [OK] {results['jpeg'][0]} Bytes ({results['jpeg'][1]:.2f} ms)")
    if "tinycae" in results:
        print(f"  [5] Bộ mã hóa TinyCAE INT8:         [OK] {results['tinycae'][0]} Bytes ({results['tinycae'][1]:.2f} ms)")

    all_passed = (results.get("ping") and "jpeg" in results and "tinycae" in results)
    if all_passed:
        print("\n  >>> KẾT LUẬN: BO MẠCH ESP32 HOẠT ĐỘNG HOÀN HẢO 100%! <<<")
        print("  Hệ thống đã sẵn sàng tuyệt đối để chạy Demo hoặc quay video nghiệm thu.")
    else:
        print("\n  >>> KẾT LUẬN: CÓ MỤC KIỂM TRA CHƯA ĐẠT. VUI LÒNG KIỂM TRA LOG Ở TRÊN. <<<")
    print("=" * 70 + "\n")
    return all_passed


if __name__ == "__main__":
    port = check_serial_ports() or PORT_DEFAULT
    run_diagnostics(port=port)
