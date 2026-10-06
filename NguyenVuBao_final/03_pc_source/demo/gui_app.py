"""Demo Nén Ảnh Trên Bo Mạch ESP32: TinyCAE INT8 vs. JPEG.

Giao diện trực quan, đơn giản, tập trung vào trải nghiệm demo trực tiếp trên phần cứng.
Không chứa số liệu báo cáo có sẵn; toàn bộ kết quả được đo đạc thực tế từ ESP32.
"""

from __future__ import annotations

import base64
import io
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageTk, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from host.demo.codec_engine import ENGINE

IMAGE_SIZE = 220  # Phóng to từ 32x32 để nhìn rõ nét trên màn hình và video

CLASS_NAMES_VI = {
    "airplane": "Máy bay",
    "automobile": "Ô tô",
    "bird": "Chim",
    "cat": "Mèo",
    "deer": "Hươu",
    "dog": "Chó",
    "frog": "Ếch",
    "horse": "Ngựa",
    "ship": "Tàu thủy",
    "truck": "Xe tải",
}


class SimpleDemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Demo Nén Ảnh Trên ESP32: TinyCAE INT8 vs. JPEG")
        self.geometry("1120x800")
        self.minsize(1000, 720)
        self.configure(bg="#0b0f19")

        self.active_raw_bytes: bytes | None = None
        self.current_q = tk.IntVar(value=70)

        # Tạo ảnh giữ chỗ (placeholder)
        self.placeholder_img = self._create_placeholder("Chờ nén...")

        ENGINE.add_log_callback(self._on_engine_log)

        self._build_ui()
        self._load_sample_images()
        self._auto_connect_hardware()

    def _create_placeholder(self, text: str) -> ImageTk.PhotoImage:
        img = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(2, 2), (IMAGE_SIZE - 3, IMAGE_SIZE - 3)], outline=(51, 65, 85), width=2)
        draw.text((IMAGE_SIZE // 2 - 35, IMAGE_SIZE // 2 - 8), text, fill=(100, 116, 139))
        return ImageTk.PhotoImage(img)

    def _build_ui(self):
        # 1. Thanh tiêu đề & Kết nối phần cứng
        top_bar = tk.Frame(self, bg="#1e293b", padx=16, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_frame = tk.Frame(top_bar, bg="#1e293b")
        title_frame.pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="⚡ DEMO NÉN ẢNH TRÊN ESP32",
            font=("Segoe UI", 13, "bold"),
            fg="#60a5fa",
            bg="#1e293b",
        ).pack(anchor=tk.W)
        tk.Label(
            title_frame,
            text="So sánh trực tiếp: TinyCAE INT8 vs. JPEG phần mềm",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b",
        ).pack(anchor=tk.W)

        # Cụm kết nối phần cứng bên phải
        conn_frame = tk.Frame(top_bar, bg="#1e293b")
        conn_frame.pack(side=tk.RIGHT)

        self.dot_lbl = tk.Label(conn_frame, text="●", font=("Segoe UI", 16), fg="#ef4444", bg="#1e293b")
        self.dot_lbl.pack(side=tk.LEFT, padx=(0, 6))

        self.status_lbl = tk.Label(conn_frame, text="Chưa kết nối ESP32", font=("Segoe UI", 9, "bold"), fg="#f87171", bg="#1e293b")
        self.status_lbl.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(conn_frame, text="Cổng:", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b").pack(side=tk.LEFT, padx=(0, 4))
        self.port_combo = ttk.Combobox(conn_frame, width=9, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_connect = tk.Button(
            conn_frame, text="Kết nối", bg="#2563eb", fg="#fff",
            font=("Segoe UI", 9, "bold"), command=self._toggle_connect,
            padx=10, pady=2, relief=tk.FLAT, cursor="hand2"
        )
        self.btn_connect.pack(side=tk.LEFT, padx=4)

        btn_ping = tk.Button(
            conn_frame, text="Ping", bg="#334155", fg="#fff",
            font=("Segoe UI", 9), command=self._ping_device,
            padx=8, pady=2, relief=tk.FLAT, cursor="hand2"
        )
        btn_ping.pack(side=tk.LEFT, padx=4)

        # 2. Thanh điều khiển chính (Chọn ảnh & Nút thao tác)
        ctrl_bar = tk.Frame(self, bg="#111827", padx=16, pady=12)
        ctrl_bar.pack(fill=tk.X, padx=12, pady=(10, 0))

        # Chọn ảnh mẫu
        tk.Label(ctrl_bar, text="Ảnh mẫu:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#111827").pack(side=tk.LEFT, padx=(0, 6))
        self.combo_samples = ttk.Combobox(ctrl_bar, width=22, state="readonly")
        self.combo_samples.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_samples.bind("<<ComboboxSelected>>", self._on_sample_changed)

        btn_upload = tk.Button(
            ctrl_bar, text="📁 Chọn ảnh từ máy tính...",
            bg="#334155", fg="#f8fafc", font=("Segoe UI", 9),
            command=self._upload_custom, padx=10, pady=3, relief=tk.FLAT, cursor="hand2"
        )
        btn_upload.pack(side=tk.LEFT, padx=(0, 16))

        # Phân cách
        tk.Frame(ctrl_bar, bg="#334155", width=1, height=26).pack(side=tk.LEFT, padx=(0, 16))

        # JPEG Quality
        tk.Label(ctrl_bar, text="Chất lượng JPEG (Q):", font=("Segoe UI", 9), fg="#94a3b8", bg="#111827").pack(side=tk.LEFT, padx=(0, 4))
        q_scale = tk.Scale(
            ctrl_bar, from_=10, to=95, variable=self.current_q,
            orient=tk.HORIZONTAL, bg="#111827", fg="#fff",
            highlightthickness=0, length=80, relief=tk.FLAT
        )
        q_scale.pack(side=tk.LEFT, padx=(0, 20))

        # Các nút bấm hành động
        self.btn_run_both = tk.Button(
            ctrl_bar, text="🚀 NÉN & SO SÁNH CẢ HAI",
            bg="#8b5cf6", fg="#ffffff", font=("Segoe UI", 10, "bold"),
            command=self._run_both, padx=16, pady=4, relief=tk.FLAT, cursor="hand2"
        )
        self.btn_run_both.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_run_tiny = tk.Button(
            ctrl_bar, text="⚡ Nén TinyCAE",
            bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"),
            command=self._run_tinycae, padx=12, pady=4, relief=tk.FLAT, cursor="hand2"
        )
        self.btn_run_tiny.pack(side=tk.LEFT, padx=4)

        self.btn_run_jpeg = tk.Button(
            ctrl_bar, text="📷 Nén JPEG",
            bg="#0891b2", fg="#ffffff", font=("Segoe UI", 9, "bold"),
            command=self._run_jpeg, padx=12, pady=4, relief=tk.FLAT, cursor="hand2"
        )
        self.btn_run_jpeg.pack(side=tk.LEFT, padx=4)

        # 3. Dòng thông báo kết quả đối chứng nhanh
        self.result_bar = tk.Frame(self, bg="#0b0f19", padx=16, pady=6)
        self.result_bar.pack(fill=tk.X, padx=12)

        self.result_lbl = tk.Label(
            self.result_bar,
            text="Chọn một ảnh và bấm 'NÉN & SO SÁNH CẢ HAI' để gửi xuống bo ESP32 đo đạc trực tiếp.",
            font=("Segoe UI", 9, "italic"),
            fg="#94a3b8",
            bg="#0b0f19"
        )
        self.result_lbl.pack(anchor=tk.W)

        # 4. Khu vực hiển thị 3 khung ảnh (Gốc - TinyCAE - JPEG)
        display_frame = tk.Frame(self, bg="#0b0f19")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # Card 1: Ảnh gốc
        self.card_raw, self.canvas_raw, self.lbl_raw_info = self._create_image_card(
            display_frame, "1. ẢNH GỐC (RGB888)", "#94a3b8", "#334155"
        )
        self.card_raw.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
        self.lbl_raw_info.config(text="Kích thước: 3,072 bytes\nĐộ phân giải: 32 × 32 pixel\nTrạng thái: Chưa nén")

        # Card 2: TinyCAE INT8
        self.card_tiny, self.canvas_tiny, self.lbl_tiny_info = self._create_image_card(
            display_frame, "2. TINYCAE INT8 (ESP32)", "#60a5fa", "#2563eb"
        )
        self.card_tiny.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
        self.lbl_tiny_info.config(text="Trạng thái: Chờ nén...\nKích thước: --\nThời gian: --\nĐộ nét: --")

        # Card 3: JPEG
        self.card_jpeg, self.canvas_jpeg, self.lbl_jpeg_info = self._create_image_card(
            display_frame, "3. JPEG PHẦN MỀM (ESP32)", "#22d3ee", "#0891b2"
        )
        self.card_jpeg.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
        self.lbl_jpeg_info.config(text="Trạng thái: Chờ nén...\nKích thước: --\nThời gian: --\nĐộ nét: --")

        # 5. Khung nhật ký UART (Telemetry Console)
        term_frame = tk.Frame(self, bg="#050811", bd=1, relief=tk.SOLID)
        term_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        term_hdr = tk.Frame(term_frame, bg="#0f172a", padx=10, pady=3)
        term_hdr.pack(fill=tk.X)
        tk.Label(term_hdr, text="📡 Giao tiếp UART thời gian thực (ESP32 COM5)", font=("Consolas", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(side=tk.LEFT)
        tk.Button(term_hdr, text="Xóa log", font=("Segoe UI", 7), command=self._clear_terminal, bg="#1e293b", fg="#fff", relief=tk.FLAT).pack(side=tk.RIGHT)

        self.term_text = ScrolledText(
            term_frame, bg="#050811", fg="#38bdf8",
            font=("Consolas", 8), height=5, relief=tk.FLAT, padx=8, pady=4
        )
        self.term_text.pack(fill=tk.BOTH, expand=True)
        self.term_text.tag_config("tx", foreground="#facc15")
        self.term_text.tag_config("rx", foreground="#4ade80")
        self.term_text.tag_config("host", foreground="#c084fc")

    def _create_image_card(self, parent, title: str, title_color: str, border_color: str):
        card = tk.Frame(parent, bg="#1a233a", padx=12, pady=10, bd=1, relief=tk.SOLID, highlightbackground=border_color, highlightthickness=1)
        tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), fg=title_color, bg="#1a233a").pack(pady=(0, 6))

        img_box = tk.Frame(card, bg="#000000", bd=2, relief=tk.SOLID)
        img_box.pack(pady=(0, 8))

        canvas = tk.Label(img_box, bg="#000000", image=self.placeholder_img)
        canvas.image = self.placeholder_img
        canvas.pack()

        lbl_info = tk.Label(
            card, font=("Consolas", 9), fg="#e2e8f0", bg="#0f172a",
            justify=tk.LEFT, padx=10, pady=8, relief=tk.FLAT
        )
        lbl_info.pack(fill=tk.X)
        return card, canvas, lbl_info

    def _on_engine_log(self, msg: str):
        self.after(0, self._append_terminal, msg)

    def _append_terminal(self, msg: str):
        tag = None
        if "[UART TX]" in msg:
            tag = "tx"
        elif "[UART RX]" in msg:
            tag = "rx"
        elif "[Host PC]" in msg:
            tag = "host"
        self.term_text.insert(tk.END, msg + "\n", tag)
        self.term_text.see(tk.END)

    def _clear_terminal(self):
        self.term_text.delete("1.0", tk.END)

    def _load_sample_images(self):
        # Nạp cổng COM
        ports = ENGINE.list_available_ports()
        p_names = [p["device"] for p in ports]
        self.port_combo["values"] = p_names
        if "COM5" in p_names:
            self.port_combo.set("COM5")
        elif p_names:
            self.port_combo.set(p_names[0])

        # Nạp danh sách ảnh mẫu dạng trực quan dễ hiểu
        items = []
        for idx, item in enumerate(ENGINE.hardware_images, start=1):
            vn_name = CLASS_NAMES_VI.get(item["class_name"], item["class_name"])
            items.append(f"{idx:02d}. {vn_name} ({item['class_name']})")
        self.combo_samples["values"] = items

        if items:
            self.combo_samples.current(0)
            self._select_sample_by_index(0)

    def _on_sample_changed(self, event):
        idx = self.combo_samples.current()
        if idx >= 0:
            self._select_sample_by_index(idx)

    def _select_sample_by_index(self, index: int):
        item = ENGINE.hardware_images[index]
        raw_path = Path(item["raw_path"])
        if raw_path.exists():
            self.active_raw_bytes = raw_path.read_bytes()
            self._display_raw(self.active_raw_bytes)
            self._reset_result_cards()
            vn_name = CLASS_NAMES_VI.get(item["class_name"], item["class_name"])
            self.result_lbl.config(
                text=f"Đã chọn ảnh mẫu: {vn_name} (32×32 RGB888). Bấm nút nén để gửi xuống ESP32.",
                fg="#94a3b8"
            )

    def _reset_result_cards(self):
        self.canvas_tiny.config(image=self.placeholder_img)
        self.canvas_tiny.image = self.placeholder_img
        self.lbl_tiny_info.config(text="Trạng thái: Chờ nén...\nKích thước: --\nThời gian: --\nĐộ nét: --")

        self.canvas_jpeg.config(image=self.placeholder_img)
        self.canvas_jpeg.image = self.placeholder_img
        self.lbl_jpeg_info.config(text="Trạng thái: Chờ nén...\nKích thước: --\nThời gian: --\nĐộ nét: --")

    def _upload_custom(self):
        f = filedialog.askopenfilename(filetypes=[("Tệp hình ảnh", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")])
        if not f:
            return
        img = Image.open(f).convert("RGB")
        w, h = img.size
        side = min(w, h)
        cropped = img.crop(((w - side)//2, (h - side)//2, (w + side)//2, (h + side)//2))
        resized = cropped.resize((32, 32), Image.Resampling.LANCZOS)
        self.active_raw_bytes = resized.tobytes()
        self._display_raw(self.active_raw_bytes)
        self._reset_result_cards()
        self.result_lbl.config(
            text=f"Đã nạp ảnh tùy chọn ({w}×{h}) -> chuẩn hóa thành 32×32 pixel. Sẵn sàng nén.",
            fg="#38bdf8"
        )
        ENGINE.log(f"[Image] Đã nạp ảnh từ máy tính ({w}x{h}) -> chuẩn hóa 32x32 RGB888.")

    def _display_raw(self, raw_bytes: bytes):
        arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((32, 32, 3))
        # Phóng to bằng Nearest-Neighbor để ảnh 32x32 cực kỳ sắc nét
        pil_img = Image.fromarray(arr).resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
        photo = ImageTk.PhotoImage(pil_img)
        self.canvas_raw.config(image=photo)
        self.canvas_raw.image = photo

    def _auto_connect_hardware(self):
        threading.Thread(target=self._try_auto_connect, daemon=True).start()

    def _try_auto_connect(self):
        port = self.port_combo.get() or "COM5"
        ENGINE.connect(port, 115200)
        self.after(0, self._update_connection_ui)

    def _update_connection_ui(self):
        if ENGINE.is_connected:
            self.dot_lbl.config(fg="#10b981")
            self.status_lbl.config(text=f"Đã kết nối {ENGINE.port}", fg="#34d399")
            self.btn_connect.config(text="Ngắt kết nối", bg="#dc2626")
        else:
            self.dot_lbl.config(fg="#ef4444")
            self.status_lbl.config(text="Chưa kết nối ESP32", fg="#f87171")
            self.btn_connect.config(text="Kết nối", bg="#2563eb")

    def _toggle_connect(self):
        if ENGINE.is_connected:
            ENGINE.disconnect()
        else:
            port = self.port_combo.get() or "COM5"
            threading.Thread(target=lambda: (ENGINE.connect(port, 115200), self.after(0, self._update_connection_ui)), daemon=True).start()
        self._update_connection_ui()

    def _ping_device(self):
        threading.Thread(target=ENGINE._ping_device, daemon=True).start()

    def _run_tinycae(self):
        if not self.active_raw_bytes:
            return messagebox.showwarning("Thông báo", "Vui lòng chọn hoặc tải ảnh lên trước!")
        threading.Thread(target=self._run_tinycae_thread, daemon=True).start()

    def _run_tinycae_thread(self):
        self.btn_run_tiny.config(text="⏳ Đang nén...", state=tk.DISABLED)
        try:
            r = ENGINE.encode_tinycae(self.active_raw_bytes)
            self.after(0, self._update_tiny_ui, r)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi trên ESP32", str(e)))
        finally:
            self.btn_run_tiny.config(text="⚡ Nén TinyCAE", state=tk.NORMAL)

    def _update_tiny_ui(self, r):
        b64 = r["image_b64"].split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(b64))).resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
        photo = ImageTk.PhotoImage(img)
        self.canvas_tiny.config(image=photo)
        self.canvas_tiny.image = photo
        self.lbl_tiny_info.config(
            text=f"Dung lượng gói: {r['bytes']} bytes\n"
                 f"Thời gian ESP32: {r['time_ms']:.1f} ms\n"
                 f"Chất lượng PSNR: {r['psnr']:.2f} dB\n"
                 f"Độ tương đồng SSIM: {r['ssim']:.4f}"
        )

    def _run_jpeg(self):
        if not self.active_raw_bytes:
            return messagebox.showwarning("Thông báo", "Vui lòng chọn hoặc tải ảnh lên trước!")
        threading.Thread(target=self._run_jpeg_thread, daemon=True).start()

    def _run_jpeg_thread(self):
        self.btn_run_jpeg.config(text="⏳ Đang nén...", state=tk.DISABLED)
        q = self.current_q.get()
        try:
            r = ENGINE.encode_jpeg(self.active_raw_bytes, quality=q)
            self.after(0, self._update_jpeg_ui, r, q)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi trên ESP32", str(e)))
        finally:
            self.btn_run_jpeg.config(text="📷 Nén JPEG", state=tk.NORMAL)

    def _update_jpeg_ui(self, r, q):
        b64 = r["image_b64"].split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(b64))).resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
        photo = ImageTk.PhotoImage(img)
        self.canvas_jpeg.config(image=photo)
        self.canvas_jpeg.image = photo
        self.lbl_jpeg_info.config(
            text=f"Dung lượng JPEG Q{q}: {r['bytes']} bytes\n"
                 f"Thời gian ESP32: {r['time_ms']:.1f} ms\n"
                 f"Chất lượng PSNR: {r['psnr']:.2f} dB\n"
                 f"Độ tương đồng SSIM: {r['ssim']:.4f}"
        )

    def _run_both(self):
        if not self.active_raw_bytes:
            return messagebox.showwarning("Thông báo", "Vui lòng chọn hoặc tải ảnh lên trước!")
        threading.Thread(target=self._run_both_thread, daemon=True).start()

    def _run_both_thread(self):
        self.btn_run_both.config(text="⏳ Đang nén trên ESP32...", state=tk.DISABLED)
        q = self.current_q.get()
        try:
            res = ENGINE.benchmark_both(self.active_raw_bytes, quality=q)
            self.after(0, self._update_both_ui, res, q)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi trên ESP32", str(e)))
        finally:
            self.btn_run_both.config(text="🚀 NÉN & SO SÁNH CẢ HAI", state=tk.NORMAL)

    def _update_both_ui(self, res, q):
        t = res["tinycae"]
        j = res["jpeg"]
        self._update_tiny_ui(t)
        self._update_jpeg_ui(j, q)

        dp = res["delta_psnr"]
        speed = res["speedup"]

        better_text = "TinyCAE nét hơn" if dp >= 0 else f"JPEG nét hơn (+{abs(dp):.2f} dB)"
        if dp >= 0:
            better_text = f"TinyCAE nét hơn (+{dp:.2f} dB)"

        summary_msg = (
            f"✅ Kết quả đo từ ESP32: "
            f"TinyCAE {t['bytes']} bytes ({t['time_ms']:.1f} ms, {t['psnr']:.2f} dB)  |  "
            f"JPEG {j['bytes']} bytes ({j['time_ms']:.1f} ms, {j['psnr']:.2f} dB)  =>  "
            f"{better_text}, JPEG nhanh hơn {speed:.1f} lần."
        )
        self.result_lbl.config(text=summary_msg, fg="#34d399")


if __name__ == "__main__":
    app = SimpleDemoApp()
    app.mainloop()
