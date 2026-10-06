"""Generate presentation slides (PowerPoint .pptx) for ESP32 TinyCAE vs JPEG project.

Creates a professional, 16:9 widescreen academic presentation deck.
"""

from __future__ import annotations

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "results/figures"
HARDWARE_EVID_DIR = ROOT / "submission_package/07_hardware_evidence"
OUT_PPTX_ROOT = ROOT / "docs/reports/SLIDE_THUYET_TRINH_ESP32_TINYCAE.pptx"
OUT_PPTX_PKG = ROOT / "submission_package/01_report_slide/SLIDE_THUYET_TRINH_ESP32_TINYCAE.pptx"

# Color Palette (Dark Theme / Modern Tech)
BG_COLOR = RGBColor(11, 15, 25)         # #0B0F19 Dark Navy
CARD_BG = RGBColor(26, 35, 58)          # #1A233A Card Slate
CARD_BORDER = RGBColor(51, 65, 85)      # #334155
TEXT_WHITE = RGBColor(248, 250, 252)    # #F8FAFC White
TEXT_MUTED = RGBColor(148, 163, 184)    # #94A3B8 Slate Gray
ACCENT_BLUE = RGBColor(96, 165, 250)    # #60A5FA Sky Blue
ACCENT_CYAN = RGBColor(56, 189, 248)    # #38BDF8 Cyan
ACCENT_GREEN = RGBColor(52, 211, 153)   # #34D399 Emerald
ACCENT_AMBER = RGBColor(251, 191, 36)   # #FBBF24 Amber
ACCENT_PURPLE = RGBColor(192, 132, 252) # #C084FC Purple


def set_slide_background(slide):
    # Add a full-bleed rectangle as background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.fill.background()
    return bg


def add_header(slide, title_text: str, category_text: str = "TIỂU LUẬN CUỐI KỲ - TRÍ TUỆ NHÂN TẠO CHO IOT"):
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(1.1))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Segoe UI"
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_CYAN

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE


def add_card(slide, left: float, top: float, width: float, height: float, bg_color=CARD_BG, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
    else:
        card.line.fill.background()
    return card


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Decorative Card in center
    add_card(s1, 1.2, 1.2, 10.933, 5.1, bg_color=RGBColor(15, 23, 42), border_color=ACCENT_BLUE)

    t_box = s1.shapes.add_textbox(Inches(1.8), Inches(1.6), Inches(9.733), Inches(4.3))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH\nKHOA CÔNG NGHỆ THÔNG TIN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    p = tf1.add_paragraph()
    p.text = "\nBÁO CÁO NGHIỆM THU ĐỀ TÀI TIỂU LUẬN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf1.add_paragraph()
    p.text = "TRIỂN KHAI VÀ ĐÁNH GIÁ BỘ MÃ HÓA TINYCAE LƯỢNG TỬ HÓA INT8 CHO NÉN ẢNH TRÊN ESP32"
    p.font.name = "Segoe UI"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p = tf1.add_paragraph()
    p.text = "Đối chứng với bộ mã hóa JPEG phần mềm trên cùng thiết bị phần cứng"
    p.font.name = "Segoe UI"
    p.font.size = Pt(15)
    p.font.italic = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf1.add_paragraph()
    p.text = "\n• Sinh viên thực hiện: NGUYỄN VŨ BẢO — MSSV: 23110079 (Lớp: 261AIOT331185_01CLC)\n• Giảng viên hướng dẫn: Thầy HỒ NHỰT MINH\n• Thời gian thực nghiệm: Tháng 09/2026"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: Problem & Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "1. Đặt Vấn Đề & Tính Cấp Thiết Trong Edge IoT")

    c1 = add_card(s2, 0.8, 1.8, 5.6, 5.0)
    tb = s2.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Thách Thức Nén Ảnh Trên Thiết Bị Biên IoT"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = ACCENT_CYAN

    items = [
        ("Băng thông hẹp & Năng lượng pin:", "Các mạng LPWAN (LoRaWAN, NB-IoT) và BLE có tốc độ truyền thấp. Giảm kích thước gói truyền là ưu tiên số 1 để tiết kiệm pin."),
        ("Hạn chế tài nguyên vi điều khiển:", "ESP32 có bộ nhớ SRAM hạn hẹp (< 328 KB free heap), không thể chạy các mô hình AI thị giác cồng kềnh."),
        ("Hiện tượng Blocking Artifact của JPEG:", "Ở bitrate thấp và ảnh độ phân giải nhỏ, JPEG phân khối 8x8 tạo ra các vết răng cưa lưới gây biến dạng hình ảnh nghiêm trọng."),
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.text = f"\n• {title} {desc}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    c2 = add_card(s2, 6.8, 1.8, 5.7, 5.0)
    tb = s2.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Mục Tiêu & Đóng Góp Nghiên Cứu"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = ACCENT_GREEN

    items = [
        ("Mã hóa Deep Learning siêu nhẹ (TinyCAE):", "Xây dựng Encoder tích chập chỉ 2.800 tham số, lượng tử hóa INT8 chạy trực tiếp trên ESP32 thông qua TFLite Micro."),
        ("Đối chứng công bằng với JPEG phần mềm:", "Triển khai JPEG phần mềm (esp_new_jpeg) trên chính con chip ESP32 đó với cùng ranh giới đo đạc."),
        ("Khóa siêu tham số độc lập:", "Khóa chất lượng JPEG Q=70 trên tập validation bitrate riêng biệt (500 ảnh) để so sánh khách quan với TinyCAE (8.00 bpp)."),
        ("Xác thực thực nghiệm nghiêm ngặt:", "Đo đạc 5 warmup + 30 repeat, kiểm tra sai số số học, đo bộ nhớ heap/PSRAM và đánh giá toàn diện Trade-off."),
    ]
    for title, desc in items:
        p = tf.add_paragraph()
        p.text = f"\n• {title} {desc}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 3: System Architecture
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "2. Kiến Trúc Hệ Thống Bất Đối Xứng (Asymmetric Framework)")

    c_left = add_card(s3, 0.8, 1.8, 5.6, 5.0)
    tb = s3.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Pipeline 1: TinyCAE INT8 (Edge-to-Cloud)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_BLUE

    steps = [
        "1. Host PC nạp ảnh RGB888 (32 × 32 × 3 = 3.072 Bytes).",
        "2. Truyền qua UART COM5 xuống ESP32 kèm mã băm CRC-32.",
        "3. ESP32 thực thi TinyCAE Encoder INT8 (Tensor Arena 128 KB PSRAM).",
        "4. Sinh ra Latent vector cố định: 8 × 8 × 16 = 1.024 Bytes INT8 (8.00 bpp).",
        "5. ESP32 gửi ngược Latent 1.024 Bytes về Host PC qua UART.",
        "6. Host PC dùng Decoder FP32 (Keras) giải mã ảnh tái tạo x̂.",
    ]
    for s in steps:
        p = tf.add_paragraph()
        p.text = f"\n{s}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    c_right = add_card(s3, 6.8, 1.8, 5.7, 5.0)
    tb = s3.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Pipeline 2: JPEG Software (Baseline Đối Chứng)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_CYAN

    steps2 = [
        "1. Host PC gửi cùng ảnh 3.072 Bytes xuống cùng bo ESP32.",
        "2. ESP32 dùng thư viện esp_new_jpeg v1.0.2 mã hóa DCT.",
        "3. Mức chất lượng cố định Q = 70 (khóa từ tập validation).",
        "4. Sinh ra dòng bitstream JPEG chuẩn (~968 Bytes trung bình).",
        "5. ESP32 gửi dòng JPEG nhị phân về Host PC qua UART.",
        "6. Host PC giải mã bằng PIL.Image, tính toán PSNR và SSIM.",
    ]
    for s in steps2:
        p = tf.add_paragraph()
        p.text = f"\n{s}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    p = tf.add_paragraph()
    p.text = "\n★ Ranh giới đo t_core: Chỉ đo thời gian thực thi mã hóa trên CPU ESP32 bằng esp_timer_get_time() (microsecond), loại trừ hoàn toàn độ trễ truyền UART."
    p.font.size = Pt(11)
    p.font.italic = True
    p.font.color.rgb = ACCENT_AMBER

    # =========================================================================
    # SLIDE 4: Hardware Setup & Evidence
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "3. Cấu Hình Phần Cứng Thực Nghiệm ESP32-CAM")

    c1 = add_card(s4, 0.8, 1.8, 5.6, 5.0)
    tb = s4.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Thông Số Bo Mạch & Vi Điều Khiển"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_GREEN

    specs = [
        ("Bo phát triển:", "AI-Thinker ESP32-CAM (Module ESP32-S)."),
        ("CPU:", "Xtensa® Dual-core 32-bit LX6 @ 240 MHz."),
        ("Flash ngoài:", "4 MB SPI Flash (DIO Mode, 40 MHz)."),
        ("PSRAM ngoài:", "8 MB vật lý (ESP-IDF ánh xạ 4 MB heap ảo)."),
        ("Bộ nhớ SRAM nội:", "520 KB (Khả dụng tự do ~287 KB)."),
        ("Giao tiếp Host:", "FTDI FT232R USB-UART @ COM5, 115.200 baud."),
        ("Phần mềm lõi:", "ESP-IDF v5.5.5, FreeRTOS kernel."),
        ("Khung AI nhúng:", "esp-tflite-micro v1.4.x (tối ưu ESP-NN)."),
    ]
    for k, v in specs:
        p = tf.add_paragraph()
        p.text = f"• {k} {v}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    c2 = add_card(s4, 6.8, 1.8, 5.7, 5.0)
    # Check if monitor ready image exists
    img_path = HARDWARE_EVID_DIR / "esp32_monitor_ready.png"
    if img_path.exists():
        s4.shapes.add_picture(str(img_path), Inches(7.0), Inches(2.0), width=Inches(5.3))
    tb2 = s4.shapes.add_textbox(Inches(7.0), Inches(5.6), Inches(5.3), Inches(1.1))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Minh chứng thực nghiệm khởi động ESP32:"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_CYAN
    p = tf2.add_paragraph()
    p.text = "Log monitor xác nhận cấp phát 128 KiB Tensor Arena trên PSRAM, JPEG buffer 8 KiB, sẵn sàng xử lý lệnh PING, TINYCAE, JPEG."
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 5: Dataset & Stratified Split
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "4. Tập Dữ Liệu CIFAR-10 & Phân Chia Phân Tầng (Stratified Split)")

    c1 = add_card(s5, 0.8, 1.8, 11.733, 5.0)
    tb = s5.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Chiến Lược Phân Chia Cố Định Seed 2026 Đảm Bảo Tính Tái Lập Tuyệt Đối"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_CYAN

    p = tf.add_paragraph()
    p.text = "Để khắc phục triệt để hiện tượng rò rỉ dữ liệu (data leakage) và đảm bảo tính đại diện đồng đều trên 10 lớp đối tượng, toàn bộ 60.000 ảnh CIFAR-10 được phân chia phân tầng:"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_WHITE

    # Add a styled table for splits
    rows, cols = 7, 4
    table_shape = s5.shapes.add_table(rows, cols, Inches(1.1), Inches(2.9), Inches(11.1), Inches(3.4))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.4)
    tbl.columns[1].width = Inches(1.8)
    tbl.columns[2].width = Inches(2.5)
    tbl.columns[3].width = Inches(4.4)

    headers = ["Tập Dữ Liệu", "Số Lượng Ảnh", "Phân Bố Mỗi Lớp", "Mục Đích Sử Dụng Trong Đề Tài"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_BLUE

    split_data = [
        ("Train (Huấn luyện)", "45.000 ảnh", "4.500 ảnh / lớp (10 lớp)", "Huấn luyện đồng thời Encoder + Decoder FP32"),
        ("Validation", "5.000 ảnh", "500 ảnh / lớp", "Đánh giá loss, kích hoạt Early Stopping (patience=10)"),
        ("Calibration (PTQ)", "500 ảnh", "50 ảnh / lớp", "Thu thập dải động activation phục vụ lượng tử hóa INT8"),
        ("Validation Bitrate", "500 ảnh", "50 ảnh / lớp", "Quét sweep Q30-Q90 để khóa siêu tham số JPEG"),
        ("Test (Đánh giá PC)", "10.000 ảnh", "1.000 ảnh / lớp", "Đo suy hao lượng tử hóa giữa FP32 và INT8 trên PC"),
        ("Hardware Test (ESP32)", "20 ảnh", "Đúng 2 ảnh / lớp (10 lớp)", "Thực nghiệm đo đạc trực tiếp trên bo mạch ESP32"),
    ]
    for r_idx, row in enumerate(split_data, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 28, 48)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10.5)
                p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 6: TinyCAE Architecture & PTQ
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "5. Mạng TinyCAE & Kỹ Thuật Lượng Tử Hóa PTQ INT8")

    c1 = add_card(s6, 0.8, 1.8, 5.6, 5.0)
    tb = s6.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Kiến Trúc Bộ Mã Hóa TinyCAE"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_BLUE

    points = [
        ("Thiết kế tối giản cho Edge:", "Encoder chỉ gồm 2 lớp Conv2D (stride=2) rút gọn kích thước từ 32x32 xuống 8x8."),
        ("Lớp 1:", "Conv2D(32 filter, kernel 3x3, stride 2, padding same, ReLU) -> 16x16x32."),
        ("Lớp 2 (Bottleneck):", "Conv2D(16 filter, kernel 3x3, stride 2, padding same) -> 8x8x16."),
        ("Kích thước tham số cực nhỏ:", "Tổng cộng chỉ 2.800 trọng số (11,2 KB FP32, nén còn 9,56 KB INT8)."),
        ("Khối lượng tính toán nhẹ:", "Chỉ 337.920 phép tính MACs cho toàn bộ encoder."),
        ("Kích thước Latent cố định:", "8 × 8 × 16 = 1.024 bytes INT8 (8.00 bpp cố định tuyệt đối)."),
    ]
    for k, v in points:
        p = tf.add_paragraph()
        p.text = f"• {k} {v}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    c2 = add_card(s6, 6.8, 1.8, 5.7, 5.0)
    tb = s6.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Lượng Tử Hóa Sau Huấn Luyện (PTQ INT8)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_AMBER

    points2 = [
        ("Mục tiêu:", "Chuyển toàn bộ phép tính dấu phẩy động FP32 sang số nguyên có dấu 8-bit (int8) để tận dụng tập lệnh nhân cộng nguyên của ESP32."),
        ("Tập hiệu chuẩn (Calibration):", "500 ảnh phân tầng từ tập train, thu thập phân phối giá trị kích hoạt."),
        ("Thông số lượng tử hóa đầu vào:", "Input scale = 0.00392157, zero-point = -128 (ánh xạ chuẩn hóa [0, 1] sang [-128, 127])."),
        ("Thông số lượng tử hóa Latent:", "Output scale = 0.00477045, zero-point = -5."),
        ("Kiểm tra sai số số học (Golden Test):", "Sai lệch tuyệt đối giữa ESP32 và TFLite máy tính tối đa đúng 1 LSB do làm tròn số học, không tràn số."),
    ]
    for k, v in points2:
        p = tf.add_paragraph()
        p.text = f"• {k} {v}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 7: Baseline JPEG Quality Locking
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "6. Phương Pháp Khóa Siêu Tham Số Đối Chứng JPEG Q70")

    c1 = add_card(s7, 0.8, 1.8, 11.733, 5.0)
    tb = s7.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Quy Trình Khóa Chất Lượng Trên Tập Validation Bitrate (500 Ảnh)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_GREEN

    p = tf.add_paragraph()
    p.text = "Để tránh việc chọn thông số thiên vị (cherry-picking) sau khi nhìn thấy kết quả test, đề tài tiến hành quét sweep 4 mức chất lượng JPEG trên 500 ảnh validation bitrate độc lập trước khi thử nghiệm phần cứng:"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_WHITE

    # Table of validation bitrate sweep
    rows, cols = 5, 6
    tbl_shape = s7.shapes.add_table(rows, cols, Inches(1.1), Inches(2.9), Inches(11.1), Inches(2.6))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(1.8)
    tbl.columns[1].width = Inches(1.8)
    tbl.columns[2].width = Inches(1.8)
    tbl.columns[3].width = Inches(1.8)
    tbl.columns[4].width = Inches(1.8)
    tbl.columns[5].width = Inches(2.1)

    headers = ["Mức Quality", "Dung Lượng (B)", "Tốc Độ Bít (bpp)", "Tỉ Số Nén", "PSNR (dB)", "Đánh Giá Lựa Chọn"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_CYAN

    val_data = [
        ("JPEG Q30", "597.10 B", "4.66 bpp", "5.15 : 1", "27.53 dB", "Bitrate quá thấp, méo khối nặng"),
        ("JPEG Q50", "771.55 B", "6.03 bpp", "3.98 : 1", "29.50 dB", "Thấp hơn bitrate TinyCAE"),
        ("★ JPEG Q70 (Khóa)", "960.09 B", "7.50 bpp", "3.21 : 1", "31.31 dB", "GẦN NHẤT VỚI TINYCAE (8.00 bpp)"),
        ("JPEG Q90", "1545.92 B", "12.08 bpp", "1.99 : 1", "35.32 dB", "Dung lượng vượt quá xa (+51%)"),
    ]
    for r_idx, row in enumerate(val_data, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            if "Khóa" in row[0]:
                cell.fill.fore_color.rgb = RGBColor(30, 58, 60)
            else:
                cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 28, 48)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10.5)
                p.font.bold = ("Khóa" in row[0])
                p.font.color.rgb = ACCENT_GREEN if "Khóa" in row[0] else TEXT_WHITE

    p_note = tf.add_paragraph()
    p_note.text = "\n=> KẾT LUẬN: Mức Q = 70 được khóa cứng và ghi nhận vào tệp jpeg_locked_quality.json. Cả hai thuật toán bước vào vòng kiểm thử phần cứng với cùng ngân sách tốc độ bít (~7.5 - 8.0 bpp)."
    p_note.font.size = Pt(11)
    p_note.font.bold = True
    p_note.font.color.rgb = ACCENT_AMBER

    # =========================================================================
    # SLIDE 8: Main Results Comparison (Table & Summary)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "7. Kết Quả Thực Nghiệm Trên 20 Ảnh Phần Cứng ESP32")

    c1 = add_card(s8, 0.8, 1.8, 11.733, 5.0)
    tb = s8.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Bảng So Sánh Tổng Hợp Đa Chỉ Số (Rate - Distortion - Latency)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_CYAN

    # Table of final comparison
    rows, cols = 3, 7
    tbl_shape = s8.shapes.add_table(rows, cols, Inches(1.1), Inches(2.6), Inches(11.1), Inches(1.8))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.2)
    tbl.columns[1].width = Inches(1.4)
    tbl.columns[2].width = Inches(1.5)
    tbl.columns[3].width = Inches(1.5)
    tbl.columns[4].width = Inches(1.5)
    tbl.columns[5].width = Inches(1.5)
    tbl.columns[6].width = Inches(1.5)

    headers = ["Thuật Toán", "Dung Lượng (B)", "Tốc Độ Bít", "Tỉ Số Nén", "PSNR (dB)", "SSIM", "Thời Gian ESP32"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(10.5)
            p.font.color.rgb = ACCENT_BLUE

    final_rows = [
        ("TinyCAE INT8", "1.024,00 B", "8,0000 bpp", "3,00 : 1", "31,33 ± 1,90 dB", "0,9674 ± 0,013", "60,70 ms"),
        ("JPEG Q70 (Khóa)", "968,55 B", "7,5668 bpp", "3,18 : 1", "31,18 ± 1,55 dB", "0,9644 ± 0,015", "2,43 ms"),
    ]
    for r_idx, row in enumerate(final_rows, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 28, 48)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)
                p.font.color.rgb = TEXT_WHITE

    p_concl = tf.add_paragraph()
    p_concl.text = "\nPhân Tích Đánh Đổi Kỹ Thuật (Trade-off Analysis):"
    p_concl.font.size = Pt(13)
    p_concl.font.bold = True
    p_concl.font.color.rgb = ACCENT_AMBER

    analysis = [
        "1. Chất lượng tái tạo: TinyCAE nhỉnh hơn JPEG Q70 (+0,14 dB PSNR và +0,0030 SSIM trung bình), đặc biệt vượt trội trên các ảnh có bề mặt mượt và viền cong.",
        "2. Kích thước bitstream: TinyCAE tạo kích thước cố định tuyệt đối 1.024 Bytes (8.00 bpp), cực kỳ thuận lợi cho truyền thông IoT đóng gói MTU không phân mảnh; JPEG biến thiên từ 813 B đến 1.139 B phụ thuộc nội dung ảnh.",
        "3. Tốc độ thực thi: JPEG có lợi thế áp đảo khi chỉ mất 2,43 ms, nhanh hơn TinyCAE (60,70 ms) tới 25 lần, rất phù hợp cho cảm biến tiết kiệm pin cần chuyển chế độ Deep Sleep ngay.",
    ]
    for a in analysis:
        p = tf.add_paragraph()
        p.text = f"• {a}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 9: Rate-Distortion & Latency Curves
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "8. Đồ Thị Phân Tích Rate - Distortion & Thời Gian Thực Thi")

    c1 = add_card(s9, 0.8, 1.8, 5.6, 5.0)
    fig_psnr = FIG_DIR / "bpp_psnr_comparison.png"
    if fig_psnr.exists():
        s9.shapes.add_picture(str(fig_psnr), Inches(0.9), Inches(1.9), width=Inches(5.4))

    c2 = add_card(s9, 6.8, 1.8, 5.7, 5.0)
    fig_time = FIG_DIR / "execution_time_comparison.png"
    if fig_time.exists():
        s9.shapes.add_picture(str(fig_time), Inches(6.9), Inches(1.9), width=Inches(5.5))

    # =========================================================================
    # SLIDE 10: Pairwise Delta Analysis
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "9. Phân Tích Độ Lệch Ghép Cặp Từng Ảnh (Pairwise Analysis)")

    c1 = add_card(s10, 0.8, 1.8, 6.5, 5.0)
    fig_pair = FIG_DIR / "pairwise_delta_analysis.png"
    if fig_pair.exists():
        s10.shapes.add_picture(str(fig_pair), Inches(0.9), Inches(1.9), width=Inches(6.3))

    c2 = add_card(s10, 7.6, 1.8, 4.9, 5.0)
    tb = s10.shapes.add_textbox(Inches(7.8), Inches(2.0), Inches(4.5), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Đặc Điểm Phân Hóa Theo Nội Dung Ảnh"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = ACCENT_CYAN

    insights = [
        ("Nhóm ảnh TinyCAE vượt trội (ΔPSNR > 0):", "Bao gồm các lớp Máy bay (+1,72 dB), Ô tô (+1,12 dB), Tàu thủy (+0,95 dB). Bề mặt vật thể nhân tạo có gradient liên tục giúp tích chập học sâu tái tạo viền mượt mà."),
        ("Nhóm ảnh JPEG vượt trội (ΔPSNR < 0):", "Bao gồm các lớp Con chó (-1,44 dB), Con chim (-0,25 dB), Con ếch (-0,58 dB). Các họa tiết tần số cao như lông thú, da sần sùi được biểu diễn DCT ở bitrate cao giữ chi tiết tốt hơn mạng thu nhỏ."),
        ("Ý nghĩa khoa học:", "Kết quả chứng minh không có thuật toán nào tối ưu tuyệt đối cho mọi thể loại ảnh; lựa chọn bộ mã hóa trên IoT cần căn cứ theo hoạt cảnh cảm biến quan sát."),
    ]
    for k, v in insights:
        p = tf.add_paragraph()
        p.text = f"\n• {k} {v}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 11: Visual Reconstruction Comparison
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "10. So Sánh Chất Lượng Tái Tạo Trực Quan (Visual Comparison)")

    c1 = add_card(s11, 0.8, 1.8, 11.733, 5.0)
    fig_grid = FIG_DIR / "visual_reconstruction_grid.png"
    if fig_grid.exists():
        s11.shapes.add_picture(str(fig_grid), Inches(1.0), Inches(2.0), width=Inches(11.3))

    # =========================================================================
    # SLIDE 12: Memory & Hardware Profiling
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "11. Đánh Giá Tiêu Thụ Bộ Nhớ & Tài Nguyên ESP32")

    c1 = add_card(s12, 0.8, 1.8, 11.733, 5.0)
    tb = s12.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Phân Bổ Vùng Nhớ Thực Tế Khi Hệ Thống Vận Hành"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_GREEN

    # Memory table
    rows, cols = 6, 4
    tbl_shape = s12.shapes.add_table(rows, cols, Inches(1.1), Inches(2.6), Inches(11.1), Inches(2.8))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(2.2)
    tbl.columns[2].width = Inches(2.2)
    tbl.columns[3].width = Inches(3.5)

    headers = ["Thành Phần Bộ Nhớ", "Vị Trí Cấp Phát", "Dung Lượng Sử Dụng", "Trạng Thái & Mức Độ An Toàn"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_CYAN

    mem_rows = [
        ("Kích thước tệp mô hình (Flash)", "SPI Flash (ROData)", "9.560 Bytes (~9,5 KB)", "Rất nhỏ, chiếm < 0,25% Flash 4 MB"),
        ("Tensor Arena (TFLite Micro)", "SPI PSRAM ngoài", "131.072 Bytes (128 KiB)", "Được cấp phát từ PSRAM, không ảnh hưởng SRAM nội"),
        ("Bộ đệm mã hóa JPEG (Output)", "SPI PSRAM ngoài", "8.192 Bytes (8 KiB)", "Cấp phát an toàn trên PSRAM"),
        ("SRAM nội bộ tự do (Internal Free Heap)", "Internal SRAM", "287.155 Bytes (~280 KiB)", "Rất dồi dào, đảm bảo hệ điều hành FreeRTOS ổn định"),
        ("PSRAM tự do (PSRAM Free Heap)", "External PSRAM", "4.050.484 Bytes (> 4,05 MiB)", "Dung lượng còn trống tới 96%"),
    ]
    for r_idx, row in enumerate(mem_rows, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 28, 48)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10.5)
                p.font.color.rgb = TEXT_WHITE

    p_note = tf.add_paragraph()
    p_note.text = "\n★ KẾT LUẬN TÀI NGUYÊN: Chiến lược đưa Tensor Arena lên PSRAM ngoài giúp hệ thống chạy hoàn toàn ổn định, không gây tràn ngăn xếp (Stack Overflow) hay thiếu hụt heap nội bộ của chip."
    p_note.font.size = Pt(11)
    p_note.font.bold = True
    p_note.font.color.rgb = ACCENT_AMBER

    # =========================================================================
    # SLIDE 13: Live Desktop Demo Application
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_header(s13, "12. Ứng Dụng Desktop Demo Tương Tác Trực Tiếp")

    c1 = add_card(s13, 0.8, 1.8, 11.733, 5.0)
    tb = s13.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Sản Phẩm Trình Diễn Nghiệm Thu: Desktop GUI (Tkinter Native)"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_BLUE

    points = [
        ("Khởi chạy nhanh chóng bằng 1 cú nhấp chuột:", "Tệp run_demo_gui.bat tự động kích hoạt môi trường Python và mở giao diện ứng dụng desktop."),
        ("Giao tiếp phần cứng thực tế 100%:", "Kết nối trực tiếp qua USB-UART COM5 @ 115200 baud với bo ESP32 thật; không dùng chế độ mô phỏng."),
        ("Hiển thị ảnh kích thước lớn & cực nét (220 × 220 pixel):", "Sử dụng thuật toán nội suy Nearest-Neighbor để phóng đại ảnh gốc 32x32 và ảnh tái tạo rõ từng pixel khi quay video màn hình."),
        ("Thao tác trực quan & Linh hoạt:", "Cho phép chọn các ảnh mẫu CIFAR-10 hoặc tải ảnh bất kỳ từ máy tính cá nhân lên để kiểm tra tính tổng quát."),
        ("Thanh kết quả đối chứng tức thì:", "Hiển thị tức thì chênh lệch ΔPSNR, ΔSSIM, tỷ lệ tăng tốc độ và dung lượng gói dữ liệu sau mỗi lượt nén."),
        ("Bảng điều khiển UART Telemetry:", "Quan sát trực tiếp các byte lệnh PING, TINYCAE, JPEG gửi đi và phản hồi nhị phân trả về từ bo ESP32."),
    ]
    for k, v in points:
        p = tf.add_paragraph()
        p.text = f"• {k} {v}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 14: Technical Contributions & Limitations
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "13. Đóng Góp Kỹ Thuật & Giới Hạn Của Đề Tài")

    c1 = add_card(s14, 0.8, 1.8, 5.6, 5.0)
    tb = s14.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Đóng Góp Kỹ Thuật Nổi Bật"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_GREEN

    contribs = [
        ("Khả thi hóa TinyML nén ảnh:", "Chứng minh mạng nén ảnh tích chập hoàn toàn có thể chạy ổn định trên vi điều khiển giá rẻ ESP32 với bộ nhớ mô hình chỉ 9,5 KB."),
        ("Lợi thế kích thước cố định trong IoT:", "Gói dữ liệu 1.024 Bytes cố định giúp thiết kế giao thức mạng không dây đơn giản, không bị phân mảnh gói và dự đoán chính xác chi phí năng lượng truyền."),
        ("Quy trình thực nghiệm chuẩn mực:", "Xây dựng pipeline có thể tái lập 100%, khóa tham số đối chứng minh bạch, đo thời gian t_core loại trừ nhiễu UART."),
    ]
    for k, v in contribs:
        p = tf.add_paragraph()
        p.text = f"\n• {k} {v}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    c2 = add_card(s14, 6.8, 1.8, 5.7, 5.0)
    tb = s14.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Các Giới Hạn Còn Tồn Tại"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_AMBER

    limits = [
        ("Kích thước ảnh còn nhỏ:", "Mô hình mới thử nghiệm trên ảnh 32 × 32 (CIFAR-10), chưa mở rộng lên ảnh camera thực tế độ phân giải cao (QVGA / VGA)."),
        ("Tốc độ xử lý chưa tối ưu:", "Thời gian 60,7 ms của TinyCAE chậm hơn 25 lần so với JPEG (2,4 ms) do chip ESP32 đời đầu chưa có tập lệnh SIMD/Vector chuyên dụng cho AI."),
        ("Chưa tích hợp Entropy Coding:", "Bitstream latent INT8 được truyền trực tiếp dạng thô, chưa kết hợp Huffman/rANS để giảm dung lượng sâu hơn."),
    ]
    for k, v in limits:
        p = tf.add_paragraph()
        p.text = f"\n• {k} {v}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 15: Future Work
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_header(s15, "14. Hướng Phát Triển Tiếp Theo")

    c1 = add_card(s15, 0.8, 1.8, 11.733, 5.0)
    tb = s15.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Định Hướng Nâng Cấp Hệ Thống Cho Ứng Dụng Thực Tế"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = ACCENT_CYAN

    future = [
        ("Nâng cấp vi điều khiển lên ESP32-S3:", "Tận dụng tập lệnh tăng tốc trí tuệ nhân tạo (ESP-NN Vector Instructions - PIE) trên chip ESP32-S3, dự kiến có thể giảm thời gian nén của TinyCAE xuống dưới 10 ms."),
        ("Nén ảnh độ phân giải lớn theo khối (Patch-based Compression):", "Chia nhỏ khung hình camera QVGA (320 × 240) thành các khối 32 × 32 hoặc 64 × 64 để nén song song mà không làm tràn bộ nhớ SRAM của thiết bị."),
        ("Kết hợp mã hóa Entropy trên vi điều khiển:", "Áp dụng thuật toán Huffman rút gọn hoặc Range Coder (rANS) cho phân phối latent INT8, kỳ vọng giảm kích thước gói từ 1.024 Bytes xuống còn 400 - 600 Bytes mà không suy giảm chất lượng."),
        ("Truyền thông không dây thời gian thực:", "Tích hợp giao thức truyền không dây MQTT qua Wi-Fi hoặc ESP-NOW để xây dựng hệ thống cảm biến thị giác IoT hoàn chỉnh."),
    ]
    for k, v in future:
        p = tf.add_paragraph()
        p.text = f"\n• {k} {v}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 16: Conclusion & Q&A
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16)

    add_card(s16, 1.2, 1.2, 10.933, 5.1, bg_color=RGBColor(15, 23, 42), border_color=ACCENT_GREEN)

    t_box = s16.shapes.add_textbox(Inches(1.8), Inches(1.8), Inches(9.733), Inches(4.0))
    tf16 = t_box.text_frame
    tf16.word_wrap = True

    p = tf16.paragraphs[0]
    p.text = "KẾT LUẬN TỔNG THỂ"
    p.font.name = "Segoe UI"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    p = tf16.add_paragraph()
    p.text = "\nĐề tài đã hoàn thành 100% mục tiêu nghiên cứu và sản phẩm bàn giao theo đề cương:\n" \
             "• Triển khai thành công bộ mã hóa TinyCAE INT8 trên phần cứng ESP32-CAM.\n" \
             "• Đo đạc thực tế, minh bạch và đối chứng khoa học với JPEG phần mềm khóa Q70.\n" \
             "• Phân tích rõ ràng bài toán đánh đổi kỹ thuật (Trade-off) giữa Chất lượng, Kích thước gói và Thời gian tính toán."
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    p = tf16.add_paragraph()
    p.text = "\n\nCHÂN THÀNH CẢM ƠN THẦY HỒ NHỰT MINH VÀ HỘI ĐỒNG ĐÁNH GIÁ!\nQ & A — HỎI VÀ ĐÁP"
    p.font.name = "Segoe UI"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.alignment = PP_ALIGN.CENTER
    p.font.color.rgb = ACCENT_AMBER

    # Save to both locations
    OUT_PPTX_ROOT.parent.mkdir(parents=True, exist_ok=True)
    OUT_PPTX_PKG.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT_PPTX_ROOT))
    prs.save(str(OUT_PPTX_PKG))
    print(f"Presentation saved successfully:")
    print(f" - {OUT_PPTX_ROOT}")
    print(f" - {OUT_PPTX_PKG}")


if __name__ == "__main__":
    build_presentation()
