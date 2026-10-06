"""Generate the complete, publication-grade academic DOCX report.

File: BAO_CAO_HOAN_CHINH_ESP32_TINYCAE.docx
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from docx_report_helper import (
    PROJECT_ROOT,
    RESULTS_DIR,
    FIGURES_DIR,
    EVIDENCE_DIR,
    REPORT_OUTPUT_PATH,
    SUBMISSION_COPY_PATH,
    COLOR_NAVY,
    COLOR_SLATE,
    COLOR_CHARCOAL,
    COLOR_MUTED,
    read_csv,
    format_table,
    add_callout,
    add_heading_1,
    add_heading_2,
    add_heading_3,
    add_body,
    add_bullet,
    add_caption,
    add_figure,
)

def create_report() -> Path:
    doc = docx.Document()
    
    # Page setup - Margins: Top 2.5cm, Bottom 2.5cm, Left 3.0cm, Right 2.0cm
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.98)     # 2.5 cm
        section.bottom_margin = Inches(0.98)  # 2.5 cm
        section.left_margin = Inches(1.18)    # 3.0 cm
        section.right_margin = Inches(0.79)   # 2.0 cm
        section.different_first_page_header_footer = True
        
        # Header / Footer for subsequent pages
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Báo cáo Tiểu luận: Triển khai & Đánh giá TinyCAE INT8 vs. JPEG trên ESP32")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = COLOR_MUTED
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Trang ")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(9)
        frun.font.color.rgb = COLOR_MUTED
        
        # Add PAGE field using oxml
        fld_xml = (
            '<w:fldSimple %s w:instr="PAGE"/>'
            % docx.oxml.ns.nsdecls("w")
        )
        fp._p.append(docx.oxml.parse_xml(fld_xml))

    # ==========================================
    # TRANG BÌA (COVER PAGE)
    # ==========================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(2)
    r = p_inst.add_run("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH\n")
    r.font.name = "Times New Roman"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = COLOR_NAVY
    
    r_sub = p_inst.add_run("KHOA CÔNG NGHỆ THÔNG TIN\nBỘ MÔN KỸ THUẬT DỮ LIỆU & IOT")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(11)
    r_sub.font.bold = True
    r_sub.font.color.rgb = COLOR_SLATE

    # Separator rule
    p_sep = doc.add_paragraph()
    p_sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sep.paragraph_format.space_before = Pt(6)
    p_sep.paragraph_format.space_after = Pt(28)
    r_line = p_sep.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    r_line.font.name = "Times New Roman"
    r_line.font.color.rgb = COLOR_NAVY
    r_line.font.size = Pt(11)

    p_type = doc.add_paragraph()
    p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_type.paragraph_format.space_before = Pt(10)
    p_type.paragraph_format.space_after = Pt(12)
    r_type = p_type.add_run("BÁO CÁO TIỂU LUẬN CUỐI MÔN HỌC")
    r_type.font.name = "Times New Roman"
    r_type.font.size = Pt(14)
    r_type.font.bold = True
    r_type.font.color.rgb = COLOR_SLATE

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("TRIỂN KHAI VÀ ĐÁNH GIÁ\nBỘ MÃ HÓA TINYCAE LƯỢNG TỬ HÓA INT8\nCHO NÉN ẢNH TRÊN ESP32")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(4)
    p_sub.paragraph_format.space_after = Pt(40)
    r_sub = p_sub.add_run("Nghiên cứu đối chứng với Bộ mã hóa JPEG phần mềm trên cùng phần cứng nhúng")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_SLATE

    # Student & Course metadata box table
    table_meta = doc.add_table(rows=6, cols=2)
    table_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Môn học:", "Trí tuệ nhân tạo cho IoT"),
        ("Mã lớp học phần:", "261AIOT331185_01CLC"),
        ("Giảng viên hướng dẫn:", "Thầy Hồ Nhựt Minh"),
        ("Sinh viên thực hiện:", "Nguyễn Vũ Bảo"),
        ("Mã số sinh viên (MSSV):", "23110079"),
        ("Thời gian thực hiện:", "Tháng 09 / 2026")
    ]
    for row_idx, (k, v) in enumerate(meta_info):
        cell_k = table_meta.rows[row_idx].cells[0]
        cell_v = table_meta.rows[row_idx].cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(3.8)
        
        pk = cell_k.paragraphs[0]
        pk.paragraph_format.space_before = Pt(2)
        pk.paragraph_format.space_after = Pt(2)
        rk = pk.add_run(k)
        rk.font.name = "Times New Roman"
        rk.font.bold = True
        rk.font.size = Pt(11)
        rk.font.color.rgb = COLOR_NAVY
        
        pv = cell_v.paragraphs[0]
        pv.paragraph_format.space_before = Pt(2)
        pv.paragraph_format.space_after = Pt(2)
        rv = pv.add_run(v)
        rv.font.name = "Times New Roman"
        rv.font.size = Pt(11)
        rv.font.color.rgb = COLOR_CHARCOAL
    
    # Borderless metadata table
    for r in table_meta.rows:
        for c in r.cells:
            docx_report_helper_tcPr = c._tc.get_or_add_tcPr()
            b = docx.oxml.parse_xml(
                f'<w:tcBorders {docx.oxml.ns.nsdecls("w")}>'
                f'<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>'
                f'</w:tcBorders>'
            )
            docx_report_helper_tcPr.append(b)

    p_loc = doc.add_paragraph()
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loc.paragraph_format.space_before = Pt(60)
    p_loc.paragraph_format.space_after = Pt(0)
    r_loc = p_loc.add_run("THÀNH PHỐ HỒ CHÍ MINH — THÁNG 09/2026")
    r_loc.font.name = "Times New Roman"
    r_loc.font.size = Pt(11)
    r_loc.font.bold = True
    r_loc.font.color.rgb = COLOR_SLATE

    doc.add_page_break()

    # ==========================================
    # TÓM TẮT ĐỀ TÀI & THUẬT NGỮ
    # ==========================================
    add_heading_1(doc, "TÓM TẮT BÁO CÁO & ĐỊNH HƯỚNG KỸ THUẬT")
    add_body(doc, 
        "Báo cáo này trình bày quy trình thiết kế, triển khai thực tế trên phần cứng nhúng ESP32 và đánh giá thực nghiệm toàn diện "
        "bộ mã hóa nén ảnh bất đối xứng Tiny Convolutional Autoencoder (TinyCAE) lượng tử hóa INT8, đặt trong sự đối chứng đa diện "
        "với bộ mã hóa JPEG phần mềm (esp_new_jpeg) chạy trên chính thiết bị đó. Thí nghiệm được chuẩn hóa trên tập dữ liệu ảnh CIFAR-10 "
        "(32 × 32 × 3 pixel, RGB888, 3.072 bytes/ảnh raw) theo quy trình phân chia phân tầng (Stratified Split, seed 2026) đảm bảo tính cân bằng "
        "tuyệt đối giữa các lớp đối tượng."
    )
    add_body(doc, 
        "Hệ thống nén hoạt động theo mô hình bất đối xứng (Asymmetric Compression): bộ mã hóa TinyCAE siêu nhẹ (2.800 tham số, cấu trúc Conv2D "
        "kết hợp DepthwiseConv2D) được nạp vào vi điều khiển ESP32 thông qua framework TensorFlow Lite Micro (esp-tflite-micro v1.4.x) "
        "và thư viện tăng tốc phần cứng ESP-NN. Encoder nén bức ảnh 3.072 bytes thành không gian tiềm ẩn (latent vector) 8 × 8 × 16 = 1.024 bytes "
        "(tương ứng BPP cố định 8,0 bpp, tỷ lệ nén 3,0:1). Phía máy tính chủ (Host PC) đảm nhiệm bộ giải mã Decoder FP32 (32.803 tham số) "
        "để tái tạo lại bức ảnh hoàn chỉnh. Đối chứng với TinyCAE là bộ mã hóa JPEG phần mềm chuẩn chạy trên cùng ESP32, được xác định chất lượng "
        "Quality Q70 thông qua quy trình quét và khóa bitrate khách quan trên tập 500 ảnh validation."
    )

    add_callout(doc, "CÁC KẾT QUẢ KỸ THUẬT THEN CHỐT ĐÃ ĐẠT ĐƯỢC",
        "1. Triển khai phần cứng thành công: Firmware tích hợp hoàn chỉnh TinyCAE INT8 và JPEG trên bo phát triển ESP32-CAM (Xtensa LX6 @ 240MHz, 4MB Flash, 8MB PSRAM với 4MB heap map), giao tiếp UART 115200 baud với cơ chế xác thực toàn vẹn dữ liệu CRC-32.\n"
        "2. Bảo toàn chất lượng lượng tử hóa (PTQ INT8): Đánh giá trên 10.000 ảnh kiểm thử cho thấy TinyCAE INT8 chỉ suy hao 0,26 dB PSNR và 0,0034 SSIM so với mô hình FP32 gốc.\n"
        "3. Dung sai số học phần cứng cực thấp: Sai lệch giữa kernel TFLite Micro/ESP-NN trên ESP32 và TFLite chuẩn trên PC tối đa chỉ 1 LSB trên 20 ảnh hardware test; chất lượng tái tạo thực tế gần như trùng khớp hoàn toàn (ΔPSNR = +0,004 dB, ΔSSIM = +0,00002).\n"
        "4. So sánh thực nghiệm trực tiếp (TinyCAE INT8 vs. JPEG Q70 locked trên 20 ảnh phần cứng):\n"
        "   - Dung lượng: TinyCAE cố định 1024,00 B (8,0000 bpp) | JPEG Q70 biến thiên trung bình 968,55 B (7,5668 bpp, nhỏ hơn 5,4%).\n"
        "   - Chất lượng tái tạo: TinyCAE đạt PSNR 31,3254 ± 1,90 dB và SSIM 0,967408 ± 0,0135; nhỉnh hơn một chút so với JPEG Q70 (PSNR 31,1838 ± 1,55 dB, SSIM 0,964415 ± 0,0148).\n"
        "   - Tốc độ thực thi: JPEG mã hóa cực nhanh 2,432 ms/ảnh, trong khi TinyCAE mất 60,704 ms/ảnh (chậm hơn ~25,0 lần do gánh nặng 338.000 phép tính tích chập).\n"
        "   - Độ an toàn bộ nhớ: Tensor arena TinyCAE 128 KiB và JPEG buffer 8 KiB cấp phát hoàn toàn trên PSRAM, giữ cho bộ nhớ heap nội tự do dồi dào (> 287 KiB free)."
    )

    add_caption(doc, "Bảng tổng quan bố cục các chương mục trong báo cáo.", is_table=True)
    table_toc = doc.add_table(rows=10, cols=2)
    toc_data = [
        ("Chương / Phần", "Nội dung kỹ thuật trọng tâm"),
        ("Chương 1. Đặt vấn đề và Mục tiêu nghiên cứu", "Bối cảnh nén ảnh IoT biên, phát biểu bài toán, ba câu hỏi nghiên cứu (RQ1-RQ3), phạm vi."),
        ("Chương 2. Dữ liệu và Phân chia phân tầng", "Tập dữ liệu CIFAR-10, Stratified Split seed 2026, bộ 20 ảnh Hardware Test, chuẩn hóa tensor INT8."),
        ("Chương 3. Phương pháp và Kiến trúc triển khai", "Kiến trúc TinyCAE Encoder 2.800 params, Decoder PC, PTQ INT8, JPEG baseline, giao thức UART có CRC-32."),
        ("Chương 4. Thiết kế thực nghiệm và Cấu hình", "Phần cứng ESP32-CAM (Xtensa LX6, 4MB Flash, 8MB PSRAM), ESP-IDF v5.5.5, ranh giới đo t_core và bộ nhớ."),
        ("Chương 5. Kết quả thực nghiệm và Phân tích", "Suy hao PTQ INT8 trên 10k test, khóa JPEG Q70 trên 500 val, so sánh 20 ảnh hardware, latency, memory."),
        ("Chương 6. Bàn luận, Hạn chế và Hướng mở rộng", "Trade-off kỹ thuật: Bitrate cố định vs. biến thiên, tốc độ tính toán, blocking artifacts, tiềm năng ESP32-S3."),
        ("Chương 7. Kết luận và Bàn giao sản phẩm", "Trả lời dứt khoát RQ1-RQ3, Bảng 10 danh mục sản phẩm đối chiếu đề cương hoàn thành nghiệm thu."),
        ("Tài liệu tham khảo", "14 công trình học thuật chuẩn quốc tế và tài liệu kỹ thuật chính thức của Espressif/Google AI Edge."),
        ("Phụ lục", "Bảng dữ liệu chi tiết ghép cặp từng ảnh trên 20 ảnh Hardware Test với các chỉ số đo đạc gốc.")
    ]
    for r_idx, row in enumerate(toc_data):
        for c_idx, val in enumerate(row):
            table_toc.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_toc, col_widths=[2.4, 4.1])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Table of abbreviations
    add_caption(doc, "Bảng 1. Danh mục thuật ngữ và ký hiệu viết tắt trong báo cáo.", is_table=True)
    table_abbr = doc.add_table(rows=10, cols=2)
    abbr_data = [
        ("Thuật ngữ / Ký hiệu", "Giải thích chi tiết"),
        ("CAE / TinyCAE", "Convolutional Autoencoder / Mạng nơ-ron tự mã hóa tích chập thu nhỏ cho thiết bị nhúng."),
        ("INT8 / PTQ", "Số nguyên có dấu 8-bit ([-128, 127]) / Post-Training Quantization (Lượng tử hóa sau huấn luyện)."),
        ("BPP (Bits Per Pixel)", "Số bít truyền tải trên mỗi điểm ảnh: BPP = (Số bytes bitstream × 8) / (Chiều rộng × Chiều cao)."),
        ("CR (Compression Ratio)", "Tỷ lệ nén kích thước dữ liệu: CR = Kích thước ảnh thô ban đầu / Kích thước nén mã hóa."),
        ("PSNR (Peak Signal-to-Noise Ratio)", "Tỷ số tín hiệu cực đại trên nhiễu (đơn vị dB), đo lường mức độ tương đồng cường độ điểm ảnh."),
        ("SSIM (Structural Similarity)", "Độ tương đồng cấu trúc (thang đo [0, 1]), mô phỏng cảm nhận thị giác của mắt người."),
        ("TFLM / ESP-NN", "TensorFlow Lite for Microcontrollers / Thư viện hàm nhân nơ-ron tối ưu phần cứng của Espressif."),
        ("t_core / t_codec", "Thời gian thực thi hàm mã hóa lõi (Invoke / Encode) / Tổng thời gian xử lý toàn bộ bitstream."),
        ("PSRAM / Heap", "Pseudo-static RAM gắn ngoài qua giao tiếp SPI / Vùng nhớ cấp phát động trong vi điều khiển.")
    ]
    for r_idx, row in enumerate(abbr_data):
        for c_idx, val in enumerate(row):
            p = table_abbr.rows[r_idx].cells[c_idx].paragraphs[0]
            p.text = val
            if r_idx == 0:
                p.runs[0].font.bold = True
    format_table(table_abbr, col_widths=[2.0, 4.5])

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 1: ĐẶT VẤN ĐỀ VÀ MỤC TIÊU
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 1. ĐẶT VẤN ĐỀ VÀ MỤC TIÊU NGHIÊN CỨU")
    
    add_heading_2(doc, "1.1. Bối cảnh và Tính cấp thiết")
    add_body(doc, 
        "Trong các hệ thống Internet vạn vật (IoT) thu thập dữ liệu hình ảnh tại biên (Edge Vision Sensors) — chẳng hạn như "
        "giám sát nông nghiệp thông minh, bẫy ảnh quan trắc động vật hoang dã, hoặc cảnh báo an ninh năng lượng thấp — băng thông "
        "truyền thông không dây (LoRa, ZigBee, NB-IoT, BLE) và năng lượng pin luôn là nút thắt cổ chai lớn nhất. Việc truyền tải "
        "nguyên bản một bức ảnh thô không nén (raw image) tiêu tốn năng lượng radio gấp hàng chục đến hàng trăm lần năng lượng tính toán "
        "của vi điều khiển. Do đó, việc nén ảnh trực tiếp trên nút cảm biến trước khi truyền là yêu cầu mang tính sống còn."
    )
    add_body(doc, 
        "Phương pháp truyền thống dựa trên chuẩn nén JPEG (sử dụng biến đổi cô-sin rời rạc DCT) đã thống trị nhiều thập kỷ qua nhờ tốc độ "
        "và thuật toán tối ưu. Tuy nhiên, các bước tiến gần đây của Học sâu (Deep Learning) và đặc biệt là TinyML (Machine Learning trên vi điều khiển) "
        "đã mở ra một hướng tiếp cận mới: nén ảnh bất đối xứng bằng mạng nơ-ron tự mã hóa tích chập (Convolutional Autoencoders - CAE). "
        "Mô hình này đặt bộ mã hóa cực nhẹ (Encoder) trên thiết bị nhúng và chuyển toàn bộ gánh nặng giải mã (Decoder kích thước lớn) "
        "lên máy chủ đám mây hoặc máy trạm (Host PC)."
    )

    add_heading_2(doc, "1.2. Phát biểu Bài toán")
    add_body(doc, 
        "Đề tài tiến hành hiện thực hóa và so sánh có đối chứng trực tiếp trên cùng một phần cứng vi điều khiển ESP32 hai pipeline nén ảnh:"
    )
    add_bullet(doc, "Pipeline P1 (TinyCAE INT8): Ảnh thô RGB888 32 × 32 × 3 (3.072 bytes) → Chuẩn hóa tensor INT8 → Bộ mã hóa TinyCAE INT8 suy luận trên ESP32 → Trích xuất latent vector 1.024 bytes → Truyền UART về PC → Bộ giải mã Decoder FP32 trên PC tái tạo ảnh 32 × 32 × 3.", bold_prefix="• ")
    add_bullet(doc, "Pipeline P2 (JPEG phần mềm đối chứng): Ảnh thô RGB888 32 × 32 × 3 (3.072 bytes) → Bộ mã hóa JPEG phần mềm (esp_new_jpeg) thực thi trên ESP32 → Luồng bít JPEG hoàn chỉnh → Truyền UART về PC → Thư viện PIL/Pillow trên PC giải mã tái tạo ảnh.", bold_prefix="• ")
    add_body(doc, 
        "Nguyên tắc cốt lõi của nghiên cứu là đánh giá công bằng, đo lường trên cùng ranh giới phần cứng (hardware boundary), sử dụng cùng "
        "tập ảnh thử nghiệm và các chỉ số chuẩn mực quốc tế, không thiên vị hay tuyên bố ưu thế cảm tính."
    )

    add_heading_2(doc, "1.3. Các Câu hỏi Nghiên cứu (Research Questions)")
    add_body(doc, "Đề tài tập trung giải quyết và trả lời ba câu hỏi kỹ thuật cụ thể sau:")
    add_bullet(doc, "RQ1 (Khả năng thực thi): Bộ mã hóa tích chập TinyCAE lượng tử hóa INT8 có thể chạy ổn định, chính xác và nằm trong giới hạn bộ nhớ SRAM/PSRAM của chip vi điều khiển ESP32 phổ thông hay không? Sai khác số học giữa kernel tối ưu ESP-NN và kernel chuẩn TFLite PC là bao nhiêu?", bold_prefix="Câu hỏi 1 (RQ1): ")
    add_bullet(doc, "RQ2 (Suy hao lượng tử hóa): Quá trình lượng tử hóa toàn phần sang số nguyên 8-bit (PTQ INT8) gây ra mức suy hao chất lượng hình ảnh (PSNR, SSIM) là bao nhiêu so với mô hình dấu phẩy động 32-bit (FP32) gốc?", bold_prefix="Câu hỏi 2 (RQ2): ")
    add_bullet(doc, "RQ3 (Đánh đổi kỹ thuật giữa TinyCAE và JPEG): Khi được khóa ở cùng dải bitrate tương đương (~1 KB/ảnh), TinyCAE INT8 và JPEG phần mềm đánh đổi như thế nào về tỷ lệ nén, chất lượng tái tạo (PSNR/SSIM), thời gian thực thi (latency) và tài nguyên bộ nhớ trên ESP32?", bold_prefix="Câu hỏi 3 (RQ3): ")

    add_heading_2(doc, "1.4. Mục tiêu và Phạm vi Nghiên cứu")
    add_body(doc, 
        "Mục tiêu là xây dựng một quy trình thực nghiệm có khả năng tái lập 100% (fully reproducible), có bằng chứng log phần cứng chi tiết, "
        "và đưa ra các kết luận kỹ thuật khách quan. Phạm vi thực nghiệm giới hạn trên tập ảnh chuẩn CIFAR-10 kích thước 32 × 32 pixel, "
        "kênh truyền dữ liệu USB-UART, và phiên bản cơ sở của TinyCAE chưa áp dụng mã hóa entropy (Huffman hay Arithmetic Coding) sau không gian tiềm ẩn."
    )

    # ==========================================
    # CHƯƠNG 2: DỮ LIỆU VÀ PHÂN CHIA PHÂN TẦNG
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 2. DỮ LIỆU VÀ QUY TRÌNH PHÂN CHIA PHÂN TẦNG")
    
    add_heading_2(doc, "2.1. Tập Dữ liệu Chuẩn CIFAR-10 và Phân chia Phân tầng (Stratified Split)")
    add_body(doc, 
        "Nghiên cứu sử dụng tập dữ liệu học máy chuẩn CIFAR-10 (gồm 60.000 ảnh màu tự nhiên, chia thành 10 lớp cân bằng: airplane, automobile, "
        "bird, cat, deer, dog, frog, horse, ship, truck). File gốc cifar-10-python.tar.gz được xác thực mã băm MD5 chuẩn xác trước khi giải nén. "
        "Để đảm bảo tính nghiêm ngặt về mặt khoa học, toàn bộ quá trình phân chia tập dữ liệu được thực hiện theo phương pháp lấy mẫu phân tầng "
        "(Stratified Split) với hạt giống cố định seed = 2026, loại trừ hoàn toàn rủi ro rò rỉ dữ liệu (data leakage) giữa các tập."
    )

    add_caption(doc, "Bảng 2. Cơ cấu phân chia tập dữ liệu CIFAR-10 trong nghiên cứu.", is_table=True)
    table_splits = doc.add_table(rows=7, cols=4)
    splits_data = [
        ("Tập dữ liệu", "Số lượng ảnh", "Phân bổ theo lớp", "Mục đích sử dụng chính"),
        ("Train Set", "45.000 ảnh", "4.500 ảnh / lớp", "Huấn luyện trọng số mạng TinyCAE FP32."),
        ("Validation Set", "5.000 ảnh", "500 ảnh / lớp", "Kiểm định mô hình, áp dụng Early Stopping khi huấn luyện."),
        ("Calibration Set", "500 ảnh (từ Train)", "50 ảnh / lớp", "Hiệu chuẩn miền giá trị (range calibration) cho PTQ INT8."),
        ("Validation Bitrate", "500 ảnh (từ Val)", "50 ảnh / lớp", "Đo đường cong RD của JPEG để chọn và khóa Quality Q."),
        ("PC Test Set", "10.000 ảnh", "1.000 ảnh / lớp", "Đánh giá hiệu năng tổng thể của FP32 vs. INT8 trên PC."),
        ("Hardware Test Set", "20 ảnh (từ Test)", "Đúng 2 ảnh / lớp", "Nạp vào ESP32 để đo đạc thực nghiệm phần cứng thực tế.")
    ]
    for r_idx, row in enumerate(splits_data):
        for c_idx, val in enumerate(row):
            table_splits.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_splits, col_widths=[1.5, 1.2, 1.5, 2.3])

    add_heading_2(doc, "2.2. Chi tiết Bộ 20 Ảnh Kiểm thử Phần cứng (Hardware Test Set)")
    add_body(doc, 
        "Bộ 20 ảnh hardware test được chọn lọc ngẫu nhiên nhưng đảm bảo phân tầng tuyệt đối: mỗi lớp trong 10 lớp của CIFAR-10 có đúng 2 ảnh đại diện. "
        "Mỗi bức ảnh được định danh bằng mã image_id duy nhất, lưu trữ dưới dạng ảnh PNG trực quan và tệp nhị phân thô RGB888 dung lượng đúng "
        "3.072 bytes (32 × 32 × 3), đi kèm mã băm SHA-256 được lập chỉ mục trong manifest.csv để đảm bảo tính toàn vẹn khi gửi qua cổng nối tiếp."
    )

    add_heading_2(doc, "2.3. Chuẩn hóa Dữ liệu và Định dạng Tensor Lượng tử hóa")
    add_body(doc, 
        "Trên máy tính chủ, dữ liệu ảnh CIFAR-10 thô (uint8) được chuẩn hóa về miền thực x ∈ [0.0, 1.0] phục vụ huấn luyện. "
        "Khi triển khai trên ESP32, tensor đầu vào phải tuân thủ nghiêm ngặt công thức lượng tử hóa affine của TensorFlow Lite:\n"
        "    q_int8 = clip(round(x_float / input_scale) + input_zero_point, -128, 127)\n"
        "Với các tham số lượng tử hóa đầu vào được xuất từ model manifest: input_scale = 0.003921568859368563 (tương đương 1/255) "
        "và input_zero_point = -128. Phép chuyển đổi này biến mảng byte uint8 thô [0, 255] thành mảng int8 [-128, 127] một cách chính xác tuyệt đối, "
        "không sử dụng các phép tính xấp xỉ làm tròn sai lệch."
    )

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 3: PHƯƠNG PHÁP VÀ KIẾN TRÚC TRIỂN KHAI
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 3. PHƯƠNG PHÁP VÀ KIẾN TRÚC TRIỂN KHAI")
    
    add_heading_2(doc, "3.1. Kiến trúc Bộ mã hóa TinyCAE (Encoder)")
    add_body(doc, 
        "Để phù hợp với năng lực tính toán khiêm tốn của vi điều khiển ESP32 (lõi Xtensa LX6 không có đơn vị tính toán tensor chuyên dụng NPU), "
        "kiến trúc TinyCAE Encoder được thiết kế tối giản, ứng dụng kỹ thuật tích chập tách biệt chiều sâu (Depthwise Separable Convolution) "
        "để giảm mạnh số lượng phép toán nhân-cộng (Multiply-Accumulate - MACs) và dung lượng bộ nhớ trọng số."
    )

    add_caption(doc, "Bảng 3. Chi tiết kiến trúc phân tầng của TinyCAE Encoder.", is_table=True)
    table_arch = doc.add_table(rows=6, cols=5)
    arch_data = [
        ("Tầng (Layer)", "Loại phép toán", "Cấu hình / Kernel / Stride", "Kích thước đầu ra", "Số tham số"),
        ("Input", "Input Tensor", "RGB888 INT8, NHWC layout", "1 × 32 × 32 × 3", "0"),
        ("Conv 1", "Conv2D + ReLU", "3 × 3, Stride 2, 32 filters, Same", "1 × 16 × 16 × 32", "896"),
        ("DW Conv", "DepthwiseConv2D", "3 × 3, Stride 1, 32 channels, Same", "1 × 16 × 16 × 32", "320"),
        ("Conv 2", "Conv2D + ReLU", "1 × 1, Stride 1, 32 filters, Same", "1 × 16 × 16 × 32", "1.056"),
        ("Bottleneck", "Conv2D + ReLU", "3 × 3, Stride 2, 16 filters, Same", "1 × 8 × 8 × 16", "528")
    ]
    for r_idx, row in enumerate(arch_data):
        for c_idx, val in enumerate(row):
            table_arch.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_arch, col_widths=[1.2, 1.4, 1.8, 1.2, 0.9])

    add_body(doc, 
        "Tổng số tham số của Encoder chỉ là 2.800 trọng số, với tổng khối lượng tính toán khoảng 337.920 phép MACs. "
        "Kích thước tệp mô hình encoder_int8.tflite sau lượng tử hóa INT8 chỉ chiếm đúng 9.560 bytes (chưa đến 10 KiB), "
        "cho phép nhúng trực tiếp vào bộ nhớ flash của ESP32 thông qua mảng hằng số C header."
    )

    add_heading_2(doc, "3.2. Kiến trúc Bộ giải mã (Decoder trên PC)")
    add_body(doc, 
        "Bộ giải mã chạy trên PC đảm nhận việc phóng to và tái cấu trúc không gian đặc trưng latent vector 8 × 8 × 16 về ảnh RGB888 32 × 32 × 3. "
        "Kiến trúc gồm: Conv2D(64, 3 × 3, ReLU) → Tăng mẫu Nearest-Neighbor (×2) → Conv2D(32, 3 × 3, ReLU) → Tăng mẫu Nearest-Neighbor (×2) "
        "→ Conv2D(16, 3 × 3, ReLU) → Conv2D(3, 3 × 3, Sigmoid). Decoder có tổng cộng 32.803 tham số, hoạt động ở chế độ dấu phẩy động FP32 "
        "nhằm tối ưu hóa chất lượng tái tạo hình ảnh sau khi nhận latent từ vi điều khiển."
    )

    add_heading_2(doc, "3.3. Huấn luyện Mô hình và Lượng tử hóa PTQ INT8")
    add_body(doc, 
        "Mô hình được huấn luyện kết hợp End-to-End trên 45.000 ảnh CIFAR-10 bằng bộ tối ưu hóa Adam (learning rate 10⁻³, batch size 128) "
        "trong 100 epoch với hàm mất mát kết hợp Rate-Distortion perceptual loss:\n"
        "    Loss = 0,9 × MSE(x, x̂) + 0,1 × [1 - SSIM(x, x̂)]\n"
        "Việc kết hợp hàm mất mát SSIM trực tiếp trong quá trình tối ưu giúp mạng bảo tồn cấu trúc cạnh và chi tiết tần số cao tốt hơn nhiều "
        "so với chỉ dùng MSE thuần túy. Sau khi hoàn tất huấn luyện, Encoder được lượng tử hóa toàn phần (Full Integer PTQ) "
        "bằng tập Calibration gồm 500 ảnh phân tầng, sinh ra mô hình `encoder_int8.tflite` với mã băm SHA-256: `badfe7f849a7d71ba91b87505ba3fc58442df8982c2eee643a626535862bb8c6`."
    )

    add_heading_2(doc, "3.4. Pipeline JPEG Đối chứng và Quy trình Khóa Quality")
    add_body(doc, 
        "Để đảm bảo tính khách quan tối đa, pipeline JPEG đối chứng được xây dựng từ thành phần chính thức của Espressif: "
        "thư viện esp_new_jpeg phiên bản 1.0.2. Cấu hình mã hóa sử dụng không gian màu RGB888, tỷ lệ lấy mẫu màu chroma subsampling 4:4:4 "
        "(không giảm mẫu sắc độ, giữ độ sắc nét cao nhất cho ảnh nhỏ 32 × 32)."
    )
    add_body(doc, 
        "Theo chuẩn mực thiết kế nghiên cứu đề cương, mức chất lượng Quality (Q) của JPEG không được lựa chọn tùy tiện dựa trên 20 ảnh phần cứng "
        "mà phải được xác định và khóa (locked) trước thông qua tập kiểm thử mở rộng 500 ảnh Validation Bitrate. Mục tiêu là tìm mức Q có bitrate "
        "gần với mức 1.024 bytes của TinyCAE nhất để tạo ra một cuộc đối đầu ngang tài ngang sức."
    )

    add_heading_2(doc, "3.5. Giao thức Truyền thông UART và Cơ chế Toàn vẹn CRC-32")
    add_body(doc, 
        "Giao tiếp giữa PC và ESP32 được thực hiện qua cổng nối tiếp USB-UART (chip FT232R) ở tốc độ baud 115200. "
        "Một giao thức nhị phân hướng gói nghiêm ngặt được thiết lập:\n"
        "1. Bắt tay (Handshake): PC gửi PING, ESP32 phản hồi PONG.\n"
        "2. Kiểm tra bộ nhớ: Lệnh STATUS trả về thông tin heap nội và PSRAM khả dụng.\n"
        "3. Lệnh mã hóa: PC gửi lệnh TINYCAE hoặc JPEG <quality>, ESP32 phản hồi READY 3072.\n"
        "4. Truyền payload: PC đẩy chính xác 3.072 bytes ảnh thô.\n"
        "5. Phản hồi kết quả: ESP32 trả về độ dài dữ liệu, thời gian thực thi vi giây và mã băm CRC-32 của bitstream để đối chiếu toàn vẹn."
    )

    # Add UART Hardware Monitor Evidence
    add_figure(doc, EVIDENCE_DIR / "esp32_monitor_ready.png", 
               "Hình 1. Nhật ký khởi tạo thành công TinyCAE INT8 và TensorFlow Lite Micro trên console phần cứng ESP32.", width_in=5.8)

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 4: THIẾT KẾ THỰC NGHIỆM VÀ CẤU HÌNH HỆ THỐNG
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 4. THIẾT KẾ THỰC NGHIỆM VÀ CẤU HÌNH HỆ THỐNG")
    
    add_heading_2(doc, "4.1. Cấu hình Phần cứng và Môi trường Nhúng")
    add_body(doc, 
        "Hệ thống thực nghiệm được triển khai trực tiếp trên phần cứng nhúng vật lý với thông số kỹ thuật được xác nhận trong Bảng 4."
    )

    add_caption(doc, "Bảng 4. Thông số kỹ thuật của nền tảng phần cứng và môi trường phần mềm.", is_table=True)
    table_hw = doc.add_table(rows=8, cols=2)
    hw_data = [
        ("Thành phần phần cứng / phần mềm", "Thông số xác nhận trong thực nghiệm"),
        ("Bo mạch phát triển (Development Board)", "ESP32-CAM (AI-Thinker), module ESP32-S, Silicon Revision v3.1."),
        ("Bộ xử lý trung tâm (CPU)", "Xtensa Dual-Core 32-bit LX6, xung nhịp hoạt động 240 MHz."),
        ("Bộ nhớ Flash ngoài", "4 MB SPI Flash (cấu hình DIO 40 MHz)."),
        ("Bộ nhớ RAM ngoài (PSRAM)", "8 MB vật lý, cấu hình SPIRAM 40 MHz, 4 MB được ánh xạ vào heap hệ thống."),
        ("Giao tiếp máy tính (Host Interface)", "USB-to-UART FT232R, cổng COM5, tốc độ baud 115200."),
        ("Khung phát triển phần mềm nhúng", "Espressif ESP-IDF v5.5.5 Stable, công cụ GCC Xtensa 14.2.0."),
        ("Thư viện nhúng tích hợp", "esp-tflite-micro v1.4.x (tối ưu ESP-NN) và esp_new_jpeg v1.0.2.")
    ]
    for r_idx, row in enumerate(hw_data):
        for c_idx, val in enumerate(row):
            table_hw.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_hw, col_widths=[2.5, 4.0])

    add_heading_2(doc, "4.2. Ranh giới Đo lường và Chỉ số Đánh giá")
    add_body(doc, 
        "Để đảm bảo tính nhất quán, các ranh giới đo lường (measurement boundaries) được định nghĩa chặt chẽ:"
    )
    add_bullet(doc, "Thời gian mã hóa lõi (t_core): Được bấm giờ trực tiếp trên chip ESP32 bằng hàm vi giây esp_timer_get_time() với độ phân giải cao. Đối với TinyCAE, t_core là thời gian thực thi hàm interpreter->Invoke(). Đối với JPEG, t_core là thời gian thực thi hàm jpeg_enc_process(). Thời gian truyền thông qua UART được tách biệt hoàn toàn khỏi t_core.", bold_prefix="Thời gian thực thi: ")
    add_bullet(doc, "Bộ nhớ sử dụng: Theo dõi biến động Heap nội (Internal SRAM) và PSRAM thông qua hàm esp_mem_get_info() trước và sau khi cấp phát Tensor Arena và JPEG Output Buffer.", bold_prefix="Tài nguyên bộ nhớ: ")
    add_bullet(doc, "Chỉ số nén (Rate): Số byte thực tế (B_codec), Tốc độ bít (Bits Per Pixel - BPP = B_codec × 8 / 1024), và Tỷ lệ nén (CR = 3072 / B_codec).", bold_prefix="Tốc độ bít và tỷ lệ nén: ")
    add_bullet(doc, "Chất lượng hình ảnh (Distortion): Được tính toán trên máy tính chủ sau khi tái tạo ảnh, sử dụng thư viện chuẩn scikit-image: PSNR (Peak Signal-to-Noise Ratio) tính trên miền [0.0, 1.0], và SSIM (Structural Similarity Index) với win_size = 7, channel_axis = -1.", bold_prefix="Chất lượng tái tạo: ")

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH ĐÁNH ĐỔI
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 5. KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH ĐÁNH ĐỔI")
    
    add_heading_2(doc, "5.1. Suy hao Lượng tử hóa PTQ INT8 trên Tập 10.000 Ảnh Test")
    add_body(doc, 
        "Trước khi nạp mô hình xuống phần cứng, hiệu năng nén của TinyCAE được đánh giá trên toàn bộ 10.000 ảnh của tập PC Test Set "
        "nhằm kiểm chứng mức độ suy thoái tín hiệu do lượng tử hóa số nguyên 8-bit gây ra."
    )

    add_caption(doc, "Bảng 5. Đánh giá suy hao lượng tử hóa PTQ INT8 trên 10.000 ảnh kiểm thử PC.", is_table=True)
    table_ptq = doc.add_table(rows=4, cols=4)
    ptq_data = [
        ("Cấu hình mô hình", "PSNR trung bình (dB)", "SSIM trung bình", "Dung lượng Latent"),
        ("TinyCAE FP32 Baseline (Mô hình gốc)", "31,8454 dB", "0,963669", "4.096 bytes (float32)"),
        ("TinyCAE INT8 Quantized (Mô hình lượng tử)", "31,5831 dB", "0,960281", "1.024 bytes (int8)"),
        ("Chênh lệch suy hao (INT8 - FP32)", "-0,2623 dB", "-0,003388", "-3.072 bytes (-75,0%)")
    ]
    for r_idx, row in enumerate(ptq_data):
        for c_idx, val in enumerate(row):
            table_ptq.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_ptq, col_widths=[2.4, 1.5, 1.4, 1.2])

    add_body(doc, 
        "Kết quả khẳng định quá trình PTQ INT8 đạt chất lượng xuất sắc: việc lượng tử hóa giúp cắt giảm 75% dung lượng latent "
        "(từ 4.096 bytes xuống 1.024 bytes) trong khi chỉ làm suy giảm một lượng không đáng kể: -0,26 dB PSNR và -0,0034 SSIM. "
        "Mô hình hoàn toàn sẵn sàng cho việc triển khai nhúng."
    )

    add_heading_2(doc, "5.2. Kết quả Quét và Khóa Chất lượng JPEG trên 500 Ảnh Validation Bitrate")
    add_body(doc, 
        "Tiến hành quét 4 mức chất lượng JPEG tiêu chuẩn (Q30, Q50, Q70, Q90) trên tập 500 ảnh Validation Bitrate (50 ảnh/lớp). "
        "Kết quả đo đạc thống kê đầy đủ được tổng hợp trong Bảng 6."
    )

    add_caption(doc, "Bảng 6. Thống kê hiệu năng JPEG theo 4 mức Quality trên 500 ảnh Validation Bitrate.", is_table=True)
    table_val = doc.add_table(rows=5, cols=7)
    val_data = [
        ("Mức Quality", "Kích thước TB (B)", "BPP trung bình", "Tỷ lệ nén (CR)", "PSNR TB (dB)", "SSIM TB", "Thời gian TB (ms)"),
        ("JPEG Q30", "805,43 B", "6,2924 bpp", "3,82:1", "27,6138 dB", "0,908786", "2,271 ms"),
        ("JPEG Q50", "872,19 B", "6,8140 bpp", "3,53:1", "29,3744 dB", "0,935867", "2,323 ms"),
        ("JPEG Q70 (Khóa)", "960,09 B", "7,5007 bpp", "3,21:1", "31,3125 dB", "0,956445", "2,406 ms"),
        ("JPEG Q90", "1.238,60 B", "9,6766 bpp", "2,50:1", "36,2813 dB", "0,983670", "2,629 ms")
    ]
    for r_idx, row in enumerate(val_data):
        for c_idx, val in enumerate(row):
            table_val.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_val, col_widths=[1.1, 1.0, 0.9, 0.8, 0.9, 0.9, 0.9])

    add_body(doc, 
        "Quyết định khóa chất lượng (Locked Quality Decision): Mức JPEG Q70 đạt kích thước trung bình 960,09 bytes "
        "(BPP = 7,50), là điểm bitrate tiệm cận nhất với mức dung lượng cố định 1.024 bytes (BPP = 8,00) của TinyCAE INT8. "
        "Đồng thời, Q70 đạt ngưỡng PSNR > 31 dB và SSIM > 0,95, tạo nên điều kiện đối đầu công bằng và cân bằng nhất. "
        "Cấu hình Q70 được chính thức khóa để thực hiện toàn bộ các phép đo trên phần cứng 20 ảnh tiếp theo."
    )

    add_heading_2(doc, "5.3. Kiểm định Dung sai Số học Phần cứng: Golden Vector PC vs. ESP32")
    add_body(doc, 
        "Một vấn đề kỹ thuật quan trọng trong TinyML là tính đồng nhất giữa mô hình tham chiếu trên PC (TFLite Interpreter chuẩn) "
        "và mô hình chạy trên vi điều khiển (TFLite Micro kết hợp thư viện tối ưu phần cứng ESP-NN). "
        "Kết quả kiểm thử trên 20 ảnh Hardware Test cho thấy:\n"
        "• 100% 20/20 ảnh đều vượt qua kiểm tra dung sai (PASS_TOLERANCE).\n"
        "• Độ lệch giá trị số nguyên giữa các phần tử latent tối đa chỉ là 1 LSB (Least Significant Bit), xuất hiện trên một số ít byte "
        "do cơ chế làm tròn fixed-point số học khác nhau giữa tập lệnh x86 PC và Xtensa DSP ESP32.\n"
        "• Tác động lên ảnh tái tạo cực kỳ nhỏ: PSNR trung bình của ESP32 đạt 31,3254 dB so với Golden PC là 31,3213 dB (chênh lệch chỉ +0,004 dB); "
        "SSIM trung bình đạt 0,967408 so với 0,967381 (chênh lệch chỉ +0,00002). Điều này chứng minh quá trình thực thi trên ESP32 đạt độ chính xác gần như hoàn hảo."
    )

    add_heading_2(doc, "5.4. So sánh Tổng hợp Trực tiếp: TinyCAE INT8 vs. JPEG Q70 trên ESP32")
    add_body(doc, 
        "Bảng 7 và các hình đồ thị biểu diễn kết quả so sánh tổng hợp trực tiếp giữa hai bộ mã hóa trên cùng 20 ảnh kiểm thử phần cứng."
    )

    add_caption(doc, "Bảng 7. So sánh tổng hợp hiệu năng giữa TinyCAE INT8 và JPEG Q70 trên 20 ảnh phần cứng ESP32.", is_table=True)
    table_final = doc.add_table(rows=3, cols=8)
    final_data = [
        ("Bộ mã hóa (Codec)", "Kích thước (B)", "BPP", "Tỷ lệ nén", "PSNR TB (dB)", "SSIM TB", "Thời gian TB", "Thời gian P95"),
        ("TinyCAE INT8", "1.024,00 B", "8,0000", "3,0000:1", "31,3254 ± 1,90", "0,967408 ± 0,013", "60,704 ms", "60,712 ms"),
        ("JPEG Q70 Locked", "968,55 B", "7,5668", "3,1838:1", "31,1838 ± 1,55", "0,964415 ± 0,015", "2,432 ms", "2,534 ms")
    ]
    for r_idx, row in enumerate(final_data):
        for c_idx, val in enumerate(row):
            table_final.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_final, col_widths=[1.4, 0.9, 0.7, 0.8, 1.1, 1.1, 0.8, 0.8])

    # Figures Rate-Distortion
    add_figure(doc, FIGURES_DIR / "bpp_psnr_comparison.png", 
               "Hình 2. Đồ thị đánh đổi Tốc độ bít - Chất lượng (BPP vs. PSNR) giữa TinyCAE INT8 và JPEG.", width_in=5.8)
    add_figure(doc, FIGURES_DIR / "bpp_ssim_comparison.png", 
               "Hình 3. Đồ thị đánh đổi Tốc độ bít - Độ tương đồng cấu trúc (BPP vs. SSIM) giữa TinyCAE INT8 và JPEG.", width_in=5.8)

    add_heading_2(doc, "5.5. Phân tích Chi tiết Ghép cặp Từng Ảnh (Pairwise Analysis)")
    add_body(doc, 
        "Khi đối chiếu chi tiết từng cặp ảnh (xem Bảng chi tiết tại Phụ lục và Hình 4, Hình 5):\n"
        "• Về chất lượng PSNR: TinyCAE INT8 giành ưu thế trên 13/20 bức ảnh (65%), đặc biệt vượt trội trên các bức ảnh có vùng nền đồng nhất "
        "hoặc chuyển màu mượt mà như máy bay (#01789: +1,74 dB), hươu (#06822: +1,24 dB), và mèo (#03607: +1,63 dB). "
        "Ngược lại, JPEG Q70 chiếm ưu thế ở các bức ảnh có nhiều kết cấu sợi phức tạp như chó (#01922: TinyCAE thấp hơn -1,44 dB).\n"
        "• Về độ tương đồng cấu trúc SSIM: TinyCAE INT8 đạt điểm cao hơn trên 14/20 bức ảnh (70%), duy trì mức SSIM trung bình ấn tượng 0,9674. "
        "Mô hình học sâu chứng minh khả năng bảo tồn đường biên hình học và khử hiện tượng phân mảnh khối rất hiệu quả."
    )

    add_figure(doc, FIGURES_DIR / "pairwise_delta_analysis.png", 
               "Hình 4. Phân bố mức chênh lệch chất lượng ghép cặp (ΔPSNR và ΔSSIM) trên 20 ảnh kiểm thử phần cứng.", width_in=5.6)

    add_heading_2(doc, "5.6. Đánh giá Thời gian Thực thi (Latency) và Tiêu thụ Bộ nhớ")
    add_body(doc, 
        "Thời gian mã hóa là điểm phân hóa rõ rệt nhất giữa hai phương pháp (xem Hình 5):\n"
        "• JPEG Q70 đạt tốc độ mã hóa cực nhanh: trung bình chỉ 2,432 ms/ảnh (2.431,75 µs), biến động cực nhỏ (P95 đạt 2,534 ms). "
        "Thuật toán DCT kết hợp bảng lượng tử hóa cố định cho phép thực thi chớp nhoáng trên CPU 240 MHz.\n"
        "• TinyCAE INT8 mất trung bình 60,704 ms/ảnh (60.704,4 µs), chậm hơn khoảng 25,0 lần so với JPEG Q70. "
        "Nguyên nhân là do mô hình phải thực hiện tuần tự gần 338.000 phép toán nhân-cộng ma trận tích chập qua 4 tầng nơ-ron."
    )

    add_figure(doc, FIGURES_DIR / "execution_time_comparison.png", 
               "Hình 5. Biểu đồ so sánh thời gian thực thi mã hóa lõi (t_core) trên chip ESP32.", width_in=5.8)

    add_caption(doc, "Bảng 8. Tiêu thụ bộ nhớ của hệ thống trên ESP32 trong quá trình thực nghiệm.", is_table=True)
    table_mem = doc.add_table(rows=7, cols=3)
    mem_data = [
        ("Vùng nhớ hệ thống", "Dung lượng ghi nhận", "Ghi chú phân bổ kỹ thuật"),
        ("Tensor Arena (TinyCAE)", "131.072 bytes (128 KiB)", "Cấp phát tĩnh trên PSRAM, chứa activation tensors của TFLM."),
        ("JPEG Output Buffer", "8.192 bytes (8 KiB)", "Cấp phát động trên PSRAM, chứa luồng byte JPEG nén."),
        ("Internal SRAM Free", "287.155 bytes (~280 KiB)", "Bộ nhớ heap nội chip còn trống sau khi khởi tạo cả 2 codec."),
        ("Internal SRAM Minimum", "254.452 bytes (~248 KiB)", "Mức heap nội thấp nhất (watermark) trong suốt quá trình chạy."),
        ("Internal Largest Block", "155.648 bytes (~152 KiB)", "Khối RAM nội liên tục lớn nhất, chứng minh không bị phân mảnh."),
        ("PSRAM Free Heap", "4.050.484 bytes (~3,86 MiB)", "Bộ nhớ PSRAM còn trống cực kỳ dồi dào, an toàn tuyệt đối.")
    ]
    for r_idx, row in enumerate(mem_data):
        for c_idx, val in enumerate(row):
            table_mem.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_mem, col_widths=[1.8, 1.8, 2.9])

    add_heading_2(doc, "5.7. Minh chứng Trực quan Hình ảnh Tái tạo")
    add_body(doc, 
        "Hình 6 trình bày ma trận so sánh trực quan giữa ảnh gốc nguyên bản, ảnh tái tạo từ TinyCAE INT8 (1024 B) và ảnh tái tạo từ JPEG Q70 "
        "cho 4 lớp đối tượng đại diện: Máy bay (Airplane), Mèo (Cat), Hươu (Deer), và Chó (Dog)."
    )

    doc.add_page_break()
    add_figure(doc, FIGURES_DIR / "visual_reconstruction_grid.png", 
               "Hình 6. Ma trận đối chiếu trực quan: Ảnh gốc RGB888, TinyCAE INT8 (1024 B) và JPEG Q70 trên các lớp CIFAR-10 đại diện.", width_in=5.4)

    # ==========================================
    # CHƯƠNG 6: BÀN LUẬN, HẠN CHẾ VÀ HƯỚNG MỞ RỘNG
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 6. BÀN LUẬN, HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN")
    
    add_heading_2(doc, "6.1. Bàn luận Sâu về Trade-off Kỹ thuật (Engineering Trade-offs)")
    add_body(doc, 
        "Kết quả thực nghiệm đem lại một bức tranh đánh đổi kỹ thuật rất rõ ràng, thực tế và có giá trị tham khảo cao:"
    )
    add_bullet(doc, "Về kích thước gói dữ liệu: TinyCAE có ưu thế độc nhất là tạo ra kích thước latent cố định tuyệt đối (deterministic size) "
        "— đúng 1.024 bytes cho mọi ảnh bất kể mức độ phức tạp của hoạt cảnh. Điều này cực kỳ thuận lợi cho việc phân mảnh gói tin truyền thông "
        "(MTU packaging) trong các giao thức mạng không dây băng hẹp (như LoRaWAN, BLE, IEEE 802.15.4), tránh được hiện tượng tràn bộ đệm "
        "hoặc biến động kích thước gói bất ngờ. Ngược lại, JPEG có kích thước co giãn theo entropy của ảnh (trong tập đo dao động từ 822 bytes đến 1.081 bytes).", bold_prefix="Tính xác định của kích thước: ")
    add_bullet(doc, "Về đặc trưng thị giác tái tạo: JPEG thường xuyên xuất hiện hiện tượng 'méo dạng khối' (blocking artifacts) đặc trưng "
        "do chia lưới 8 × 8 của phép biến đổi DCT, dễ nhận thấy ở các vùng ranh giới có độ tương phản cao. Trong khi đó, TinyCAE học được "
        "biểu diễn liên tục nên ảnh tái tạo có bề mặt mượt mà, khử nhiễu tự nhiên và duy trì độ tương đồng cấu trúc SSIM rất cao.", bold_prefix="Cơ chế méo hình học: ")
    add_bullet(doc, "Về chi phí điện toán và năng lượng: JPEG thể hiện sự áp đảo tuyệt đối về tốc độ với thời gian mã hóa chỉ 2,43 ms, "
        "nhanh hơn TinyCAE 25 lần (60,70 ms). Trong các ứng dụng IoT chạy pin yêu cầu tốc độ khung hình cao hoặc cần vi điều khiển ngủ sâu (deep sleep) "
        "ngay lập tức để tiết kiệm năng lượng, JPEG vẫn là lựa chọn thực dụng vượt trội. TinyCAE đòi hỏi chip phải chạy ở công suất đỉnh trong 60 ms, "
        "dẫn đến tiêu hao năng lượng tính toán cao hơn.", bold_prefix="Chi phí năng lượng tính toán: ")

    add_heading_2(doc, "6.2. Hạn chế của Nghiên cứu Hiện tại")
    add_body(doc, 
        "Tác giả thẳng thắn thừa nhận các giới hạn kỹ thuật trong khuôn khổ đề tài:\n"
        "1. Kích thước hình ảnh: Thí nghiệm thực hiện trên ảnh 32 × 32 pixel của tập CIFAR-10. Khi mở rộng lên các độ phân giải lớn hơn "
        "(QVGA 320 × 240, VGA 640 × 480), khối lượng tính toán của TinyCAE sẽ tăng theo cấp số nhân, đòi hỏi các cấu hình mạng có bước nhảy (stride) "
        "lớn hơn hoặc vi điều khiển có bộ gia tốc vector.\n"
        "2. Chưa tích hợp nén Entropy cho TinyCAE: Trong nghiên cứu này, latent vector được truyền nguyên bản dưới dạng mảng 1.024 số nguyên INT8. "
        "Nếu áp dụng thêm thuật toán nén entropy không mất mát (như Deflate/zlib hoặc Huffman) phía sau latent, kích thước bitstream TinyCAE "
        "có thể giảm thêm từ 20% đến 40% mà không làm giảm thêm bất kỳ độ nét nào.\n"
        "3. Kích thước mẫu đo phần cứng: Bộ 20 ảnh kiểm thử phần cứng là minh chứng thực nghiệm xác thực hệ thống, chưa đủ lớn để đại diện "
        "cho mọi tình huống môi trường phức tạp ngoài thực địa."
    )

    add_heading_2(doc, "6.3. Khả năng Ứng dụng Thực tế và Hướng Phát triển")
    add_body(doc, 
        "Hệ thống TinyCAE INT8 đặc biệt phù hợp trong các kịch bản IoT sau:\n"
        "• Hệ thống cảm biến giám sát biên có băng thông truyền dẫn cực hẹp và cố định, nơi việc ổn định kích thước gói tin là ưu tiên số một.\n"
        "• Hệ thống thị giác máy tính phía máy chủ: Thay vì giải mã ra ảnh để người xem, latent vector 1.024 bytes của TinyCAE có thể được đưa trực tiếp "
        "vào các mạng nơ-ron phân loại (Classifier) hoặc phát hiện đối tượng (Detector) trên server mà không cần qua bước giải mã ngược, tiết kiệm tài nguyên máy chủ.\n"
        "• Hướng nâng cấp phần cứng: Chuyển đổi mã nguồn sang chip ESP32-S3 (lõi Xtensa LX7 hỗ trợ tập lệnh vector AI SIMD instructions), "
        "giúp tăng tốc độ suy luận của TinyCAE lên từ 3 đến 5 lần."
    )

    # ==========================================
    # CHƯƠNG 7: KẾT LUẬN VÀ BÀN GIAO SẢN PHẨM
    # ==========================================
    add_heading_1(doc, "CHƯƠNG 7. KẾT LUẬN VÀ KIẾN NGHỊ")
    
    add_heading_2(doc, "7.1. Kết luận Chung về các Câu hỏi Nghiên cứu")
    add_body(doc, 
        "Đề tài đã hoàn thành xuất sắc toàn bộ mục tiêu đặt ra, cung cấp câu trả lời rõ ràng và chuẩn xác cho ba câu hỏi nghiên cứu:"
    )
    add_bullet(doc, "Trả lời RQ1: Bộ mã hóa TinyCAE INT8 hoàn toàn khả thi và chạy ổn định tuyệt đối trên chip ESP32 thông qua framework TFLM và ESP-NN. Sai lệch số học giữa ESP32 và PC chỉ tối đa 1 LSB, không gây ảnh hưởng đến chất lượng ảnh.", bold_prefix="Kết luận RQ1: ")
    add_bullet(doc, "Trả lời RQ2: Quá trình PTQ INT8 bảo tồn chất lượng hình ảnh gần như nguyên vẹn, chỉ suy hao 0,26 dB PSNR và 0,0034 SSIM trên 10.000 ảnh kiểm thử, trong khi tiết kiệm 75% kích thước latent.", bold_prefix="Kết luận RQ2: ")
    add_bullet(doc, "Trả lời RQ3: Tại dải bitrate tương đương (~1 KB/ảnh), TinyCAE INT8 đạt chất lượng tái tạo nhỉnh hơn một chút so với JPEG Q70 (PSNR 31,33 dB vs 31,18 dB; SSIM 0,9674 vs 0,9644) và có kích thước cố định, nhưng phải trả giá bằng thời gian mã hóa chậm hơn 25 lần (60,70 ms so với 2,43 ms).", bold_prefix="Kết luận RQ3: ")

    add_heading_2(doc, "7.2. Danh mục Sản phẩm Bàn giao và Nghiệm thu")
    add_caption(doc, "Bảng 9. Đối chiếu danh mục sản phẩm bàn giao thực tế theo Đề cương Bảng 10.", is_table=True)
    table_deliver = doc.add_table(rows=8, cols=3)
    deliver_data = [
        ("Sản phẩm bàn giao", "Thư mục lưu trữ trong gói nộp", "Tình trạng nghiệm thu thực tế"),
        ("1. Báo cáo & Tài liệu", "01_report_slide/", "ĐẠT CHUẨN. Báo cáo DOCX hoàn chỉnh, nhật ký triển khai và kế hoạch chi tiết."),
        ("2. Mã nguồn Huấn luyện", "02_training_source/", "ĐẠT CHUẨN. Script phân chia stratified, train FP32, quantize PTQ INT8, notebook 01-05."),
        ("3. Mã nguồn Firmware ESP32", "03_esp32_source/", "ĐẠT CHUẨN. Mã nguồn C/C++, SDKConfig, CMakeLists, tích hợp TFLM và esp_new_jpeg."),
        ("4. Mã nguồn Host PC Client", "04_pc_source/", "ĐẠT CHUẨN. Script giao tiếp UART COM5, kiểm tra CRC, benchmark JPEG và build so sánh."),
        ("5. Mô hình & Manifest", "05_models_manifest/", "ĐẠT CHUẨN. Model TFLite INT8, mô hình Keras decoder, SHA-256 manifest JSON."),
        ("6. Dữ liệu Thực nghiệm", "06_experimental_data/", "ĐẠT CHUẨN. Toàn bộ tệp bitstream thực, ảnh tái tạo, CSV chi tiết theo từng ảnh."),
        ("7. Bằng chứng Phần cứng", "07_hardware_evidence/", "ĐẠT CHUẨN. Ảnh chụp màn hình console monitor khởi tạo ESP32 thực tế.")
    ]
    for r_idx, row in enumerate(deliver_data):
        for c_idx, val in enumerate(row):
            table_deliver.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(table_deliver, col_widths=[1.8, 1.8, 2.9])

    doc.add_page_break()

    # ==========================================
    # TÀI LIỆU THAM KHẢO
    # ==========================================
    add_heading_1(doc, "TÀI LIỆU THAM KHẢO")
    refs = [
        "[1] A. G. Howard et al., “MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications,” arXiv:1704.04861, 2017.",
        "[2] B. Jacob et al., “Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference,” IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 2704–2713, 2018. DOI: 10.1109/CVPR.2018.00286.",
        "[3] R. David et al., “TensorFlow Lite Micro: Embedded Machine Learning for TinyML Systems,” Proceedings of Machine Learning and Systems (MLSys), vol. 3, pp. 800–811, 2021.",
        "[4] G. K. Wallace, “The JPEG Still Picture Compression Standard,” IEEE Transactions on Consumer Electronics, vol. 38, no. 1, pp. xviii–xxxiv, 1992. DOI: 10.1109/30.125072.",
        "[5] Z. Wang, A. C. Bovik, H. R. Sheikh and E. P. Simoncelli, “Image Quality Assessment: From Error Visibility to Structural Similarity,” IEEE Transactions on Image Processing, vol. 13, no. 4, pp. 600–612, 2004. DOI: 10.1109/TIP.2003.819861.",
        "[6] A. Krizhevsky, “Learning Multiple Layers of Features from Tiny Images,” Technical Report, University of Toronto, 2009.",
        "[7] J. Ballé, V. Laparra and E. P. Simoncelli, “End-to-end Optimized Image Compression,” International Conference on Learning Representations (ICLR), 2017.",
        "[8] Google AI Edge, “LiteRT 8-bit Quantization Specification,” Google Developers Documentation, 2024.",
        "[9] Espressif Systems, “TensorFlow Lite Micro for Espressif Chipsets (esp-tflite-micro),” Espressif Component Registry, v1.4.x, 2024.",
        "[10] Google AI Edge, “Post-training Integer Quantization Guide,” TensorFlow Core Documentation, 2024.",
        "[11] Espressif Systems, “ESP_NEW_JPEG: High Performance JPEG Codec Component,” Espressif Component Registry, v1.0.2, 2024.",
        "[12] scikit-image developers, “skimage.metrics: Peak Signal-to-Noise Ratio and Structural Similarity Index,” API Reference Manual, 2024.",
        "[13] Espressif Systems, “ESP Timer (High Resolution Timer),” ESP-IDF Programming Guide, Espressif Systems, 2024.",
        "[14] Espressif Systems, “Heap Memory Debugging and Allocation API,” ESP-IDF Programming Guide, Espressif Systems, 2024."
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.left_indent = Inches(0.3)
        p_ref.paragraph_format.first_line_indent = Inches(-0.3)
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p_ref.add_run(ref)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_CHARCOAL

    doc.add_page_break()

    # ==========================================
    # PHỤ LỤC: BẢNG SỐ LIỆU GHÉP CẶP 20 ẢNH
    # ==========================================
    add_heading_1(doc, "PHỤ LỤC. BẢNG SỐ LIỆU ĐỐI CHỨNG GHÉP CẶP CHI TIẾT TRÊN 20 ẢNH")
    add_body(doc, 
        "Bảng Phụ lục 1 ghi nhận toàn bộ số liệu thực nghiệm gốc trên từng bức ảnh trong bộ 20 ảnh kiểm thử phần cứng, "
        "đối chứng trực tiếp giữa bộ mã hóa TinyCAE INT8 và JPEG Q70 locked được xử lý trên chip ESP32."
    )

    pairwise_rows = read_csv(RESULTS_DIR / "final_pairwise_tinycae_vs_jpeg_q70.csv")
    add_caption(doc, "Bảng Phụ lục 1. Số liệu chi tiết ghép cặp từng ảnh trên phần cứng ESP32.", is_table=True)
    table_pw = doc.add_table(rows=len(pairwise_rows) + 1, cols=9)
    pw_headers = [
        "Mã ảnh (ID)", "Lớp", "TinyCAE (B)", "JPEG Q70 (B)", "TinyCAE PSNR", "JPEG PSNR", "Δ PSNR (dB)", "TinyCAE SSIM", "JPEG SSIM"
    ]
    for c_idx, h in enumerate(pw_headers):
        table_pw.rows[0].cells[c_idx].paragraphs[0].text = h

    for r_idx, row in enumerate(pairwise_rows, start=1):
        cells = table_pw.rows[r_idx].cells
        short_id = row["image_id"].replace("cifar10_test_", "#")
        cells[0].paragraphs[0].text = short_id
        cells[1].paragraphs[0].text = row["class_name"]
        cells[2].paragraphs[0].text = str(int(float(row["tinycae_bytes"])))
        cells[3].paragraphs[0].text = str(int(float(row["jpeg_q70_bytes"])))
        cells[4].paragraphs[0].text = f"{float(row['tinycae_psnr_db']):.2f}"
        cells[5].paragraphs[0].text = f"{float(row['jpeg_q70_psnr_db']):.2f}"
        
        d_p = float(row["delta_psnr_db"])
        p_dp = cells[6].paragraphs[0]
        p_dp.text = f"{d_p:+.2f}"
        if d_p >= 0:
            p_dp.runs[0].font.bold = True
            
        cells[7].paragraphs[0].text = f"{float(row['tinycae_ssim']):.4f}"
        cells[8].paragraphs[0].text = f"{float(row['jpeg_q70_ssim']):.4f}"

    format_table(table_pw, col_widths=[0.9, 0.9, 0.7, 0.8, 0.8, 0.8, 0.8, 0.9, 0.9])

    # Save to docs/reports
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(REPORT_OUTPUT_PATH))
    print(f"Report saved successfully to: {REPORT_OUTPUT_PATH}")

    # Copy to submission package
    SUBMISSION_COPY_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPORT_OUTPUT_PATH, SUBMISSION_COPY_PATH)
    print(f"Report copied to submission package: {SUBMISSION_COPY_PATH}")

    return REPORT_OUTPUT_PATH

if __name__ == "__main__":
    create_report()
