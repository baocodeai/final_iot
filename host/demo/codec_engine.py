"""Core Codec Engine for Demo: handles ESP32 UART communication, local simulation,

decoding, and metric calculations.
"""

from __future__ import annotations

import io
import json
import re
import threading
import time
import zlib
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
import serial
from serial.tools import list_ports

PROJECT_ROOT = Path("D:/projects/iot-final")
MODEL_DIR = PROJECT_ROOT / "models/tinycae"
MANIFEST_PATH = PROJECT_ROOT / "manifests/model_manifest.json"
DECODER_PATH = MODEL_DIR / "stratified_baseline/decoder.keras"
ENCODER_TFLITE_PATH = MODEL_DIR / "int8/encoder_int8.tflite"
HARDWARE_TEST_DIR = PROJECT_ROOT / "data/processed/hardware_test"

LATENT_HEADER_REGEX = re.compile(
    r"^LATENT\s+(?P<size>\d+)\s+(?P<crc>[0-9A-Fa-f]{8})\s+(?P<time_us>\d+)$"
)
JPEG_HEADER_REGEX = re.compile(
    r"^JPEG\s+(?P<size>\d+)\s+(?P<crc>[0-9A-Fa-f]{8})\s+(?P<time_us>\d+)$"
)
STATUS_REGEX = re.compile(
    r"^MEM\s+INTERNAL_FREE\s+(?P<int_free>\d+)\s+INTERNAL_MIN\s+(?P<int_min>\d+)\s+INTERNAL_LARGEST\s+(?P<int_large>\d+)\s+PSRAM_FREE\s+(?P<psram_free>\d+)\s+PSRAM_MIN\s+(?P<psram_min>\d+)\s+PSRAM_LARGEST\s+(?P<psram_large>\d+)$"
)

class CodecEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.serial_conn: Optional[serial.Serial] = None
        self.port: str = "COM5"
        self.baud: int = 115200
        self.is_connected: bool = False
        self.force_simulation: bool = False
        self.log_callbacks: List[Callable[[str], None]] = []
        
        # Load manifest
        self.manifest = {}
        if MANIFEST_PATH.exists():
            self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.output_scale = float(self.manifest.get("output_scale", 0.004770447965711355))
        self.output_zero_point = int(self.manifest.get("output_zero_point", -5))
        self.input_scale = float(self.manifest.get("input_scale", 0.003921568859368563))
        self.input_zero_point = int(self.manifest.get("input_zero_point", -128))

        # Lazy loaded models
        self.decoder_model = None
        self.tflite_interpreter = None
        
        # Preloaded hardware test items
        self.hardware_images: List[Dict[str, str]] = []
        self._load_hardware_manifest()

    def add_log_callback(self, cb: Callable[[str], None]):
        self.log_callbacks.append(cb)

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"
        formatted = f"[{timestamp}] {message}"
        try:
            print(formatted)
        except Exception:
            try:
                print(formatted.encode("ascii", errors="replace").decode("ascii"))
            except Exception:
                pass
        for cb in self.log_callbacks:
            try:
                cb(formatted)
            except Exception:
                pass

    def _ensure_decoder(self):
        if self.decoder_model is None:
            self.log("[System] Đang nạp bộ giải mã Decoder FP32 (Keras)...")
            import keras
            self.decoder_model = keras.models.load_model(DECODER_PATH, compile=False)
            self.log("[System] Đã nạp Decoder FP32 sẵn sàng.")

    def _ensure_tflite_simulation(self):
        if self.tflite_interpreter is None:
            self.log("[System] Đang nạp mô hình TFLite INT8 phục vụ mô phỏng...")
            import tensorflow as tf
            self.tflite_interpreter = tf.lite.Interpreter(model_path=str(ENCODER_TFLITE_PATH))
            self.tflite_interpreter.allocate_tensors()
            self.log("[System] Đã nạp TFLite INT8 Interpreter sẵn sàng.")

    def _load_hardware_manifest(self):
        manifest_file = HARDWARE_TEST_DIR / "manifest.csv"
        if manifest_file.exists():
            import csv
            with manifest_file.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.hardware_images.append({
                        "image_id": row["image_id"],
                        "class_name": row["class_name"],
                        "png_path": str(HARDWARE_TEST_DIR / "png" / f"{row['image_id']}.png"),
                        "raw_path": str(HARDWARE_TEST_DIR / "raw" / f"{row['image_id']}.rgb")
                    })

    def list_available_ports(self) -> List[Dict[str, str]]:
        ports = list_ports.comports()
        res = []
        for p in ports:
            res.append({
                "device": p.device,
                "description": p.description,
                "is_likely_esp": "USB" in p.description or "FTDI" in p.description or "UART" in p.description
            })
        return res

    def connect(self, port: str = "COM5", baud: int = 115200) -> bool:
        with self.lock:
            self.port = port
            self.baud = baud
            self.log(f"[Serial] Đang mở kết nối {port} tại {baud} baud...")
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=baud,
                    timeout=1.0,
                    write_timeout=2.0
                )
                self.serial_conn.dtr = False
                self.serial_conn.rts = False
                time.sleep(0.3)
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Test ping
                if self._ping_device():
                    self.is_connected = True
                    self.log(f"[Serial] ✅ Kết nối thành công tới ESP32 trên {port}!")
                    return True
                else:
                    self.log(f"[Serial] ⚠️ Mở được cổng {port} nhưng ESP32 không phản hồi PONG.")
                    self.is_connected = False
                    return False
            except Exception as e:
                self.log(f"[Serial] ❌ Lỗi kết nối {port}: {e}")
                self.is_connected = False
                return False

    def disconnect(self):
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.serial_conn = None
            self.is_connected = False
            self.log("[Serial] Đã đóng cổng kết nối.")

    def _ping_device(self) -> bool:
        ok, _ = self.ping_with_latency()
        return ok

    def ping_with_latency(self) -> Tuple[bool, float]:
        if not self.serial_conn or not self.serial_conn.is_open:
            return False, 0.0
        for attempt in range(1, 4):
            t0 = time.monotonic()
            self.log(f"[UART TX] PING (kiểm tra I/O phần cứng)")
            self.serial_conn.write(b"PING\n")
            self.serial_conn.flush()
            deadline = time.monotonic() + 1.5
            while time.monotonic() < deadline:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.log(f"[UART RX] {line}")
                    if line == "PONG":
                        rtt_ms = (time.monotonic() - t0) * 1000.0
                        return True, rtt_ms
            time.sleep(0.2)
        return False, 0.0

    def get_device_status(self) -> Dict[str, Any]:
        with self.lock:
            if not self.is_connected or not self.serial_conn:
                return {
                    "online": False,
                    "mode": "Simulation (Mô phỏng)" if self.force_simulation else "Offline",
                    "internal_free": 287155,
                    "internal_min": 254452,
                    "psram_free": 4050484,
                    "psram_min": 4050484,
                    "tensor_arena": 131072,
                    "jpeg_buffer": 8192
                }
            try:
                self.log("[UART TX] STATUS")
                self.serial_conn.write(b"STATUS\n")
                self.serial_conn.flush()
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline:
                    line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self.log(f"[UART RX] {line}")
                        m = STATUS_REGEX.match(line)
                        if m:
                            return {
                                "online": True,
                                "mode": "ESP32 Hardware (COM5)",
                                "internal_free": int(m.group("int_free")),
                                "internal_min": int(m.group("int_min")),
                                "internal_largest": int(m.group("int_large")),
                                "psram_free": int(m.group("psram_free")),
                                "psram_min": int(m.group("psram_min")),
                                "psram_largest": int(m.group("psram_large")),
                                "tensor_arena": 131072,
                                "jpeg_buffer": 8192
                            }
            except Exception as e:
                self.log(f"[UART] Lỗi đọc STATUS: {e}")
        return {"online": self.is_connected, "mode": "Hardware Connected"}

    def compute_metrics(self, ref_rgb: np.ndarray, rec_rgb: np.ndarray) -> Tuple[float, float]:
        """Compute PSNR (dB) and SSIM on [0, 1] float images."""
        ref_f = ref_rgb.astype(np.float32) / 255.0
        rec_f = np.clip(rec_rgb.astype(np.float32) / 255.0, 0.0, 1.0)
        
        mse = float(np.mean((ref_f - rec_f) ** 2))
        if mse == 0:
            psnr = 100.0
        else:
            psnr = float(10.0 * np.log10(1.0 / mse))

        from skimage.metrics import structural_similarity
        ssim = float(structural_similarity(ref_f, rec_f, win_size=7, channel_axis=-1, data_range=1.0))
        return psnr, ssim

    def encode_tinycae(self, raw_rgb: bytes) -> Dict[str, Any]:
        """Execute TinyCAE INT8 on ESP32 (or simulation) and decode on PC."""
        self._ensure_decoder()
        
        if len(raw_rgb) != 3072:
            raise ValueError(f"Expected 3072 raw bytes, got {len(raw_rgb)}")
            
        pc_crc = f"{zlib.crc32(raw_rgb):08X}"
        ref_img_np = np.frombuffer(raw_rgb, dtype=np.uint8).reshape((32, 32, 3))

        with self.lock:
            if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                raise RuntimeError("Bo mạch ESP32 chưa được kết nối! Vui lòng cắm cáp USB vào cổng COM5 và nhấn Kết nối.")
            
            self.log("[Pipeline P1] Bắt đầu mã hóa TinyCAE INT8 trên phần cứng ESP32...")
            self.log("[UART TX] TINYCAE")
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(b"TINYCAE\n")
            self.serial_conn.flush()
            
            # Wait for READY 3072
            deadline = time.monotonic() + 3.0
            ready = False
            while time.monotonic() < deadline:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.log(f"[UART RX] {line}")
                    if "READY 3072" in line:
                        ready = True
                        break
            if not ready:
                raise RuntimeError("ESP32 không phản hồi READY 3072 cho lệnh TINYCAE")
            
            # Send 3072 raw bytes
            self.log(f"[UART TX] Đang gửi 3072 bytes ảnh thô (CRC32: {pc_crc})...")
            self.serial_conn.write(raw_rgb)
            self.serial_conn.flush()
            
            # Read response header: LATENT <size> <crc32> <time_us>
            deadline = time.monotonic() + 5.0
            header_line = ""
            while time.monotonic() < deadline:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.log(f"[UART RX] {line}")
                    if LATENT_HEADER_REGEX.match(line):
                        header_line = line
                        break
                        
            m = LATENT_HEADER_REGEX.match(header_line)
            if not m:
                raise RuntimeError(f"ESP32 phản hồi header không hợp lệ: {header_line}")
                
            latent_size = int(m.group("size"))
            latent_crc = m.group("crc").upper()
            time_us = int(m.group("time_us"))
            
            # Read latent bytes
            latent_bytes = self.serial_conn.read(latent_size)
            if len(latent_bytes) != latent_size:
                raise RuntimeError(f"Chỉ nhận được {len(latent_bytes)}/{latent_size} bytes latent")
            
            actual_crc = f"{zlib.crc32(latent_bytes):08X}"
            if actual_crc != latent_crc:
                self.log(f"[UART Warning] CRC không khớp: dự kiến {latent_crc}, nhận {actual_crc}")

        # PC Decoder Reconstruction
        self.log("[Host PC] Đang giải lượng tử hóa Latent và giải mã qua Decoder FP32...")
        latent_int8 = np.frombuffer(latent_bytes, dtype=np.int8).reshape(1, 8, 8, 16)
        latent_float = (latent_int8.astype(np.float32) - self.output_zero_point) * self.output_scale
        rec_float = self.decoder_model(latent_float, training=False)[0].numpy()
        rec_uint8 = np.clip(np.round(rec_float * 255.0), 0, 255).astype(np.uint8)

        psnr, ssim = self.compute_metrics(ref_img_np, rec_uint8)
        self.log(f"[Host PC] ✅ Tái tạo thành công: PSNR = {psnr:.2f} dB, SSIM = {ssim:.4f}")

        # Convert to PNG base64
        rec_pil = Image.fromarray(rec_uint8)
        buf = io.BytesIO()
        rec_pil.save(buf, format="PNG")
        import base64
        b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "codec": "TinyCAE INT8",
            "bytes": latent_size,
            "bpp": latent_size * 8.0 / 1024.0,
            "compression_ratio": 3072.0 / latent_size,
            "time_ms": time_us / 1000.0,
            "time_us": time_us,
            "psnr": psnr,
            "ssim": ssim,
            "crc32": actual_crc,
            "image_b64": f"data:image/png;base64,{b64_img}"
        }

    def encode_jpeg(self, raw_rgb: bytes, quality: int = 70) -> Dict[str, Any]:
        """Execute JPEG on ESP32 (or simulation) and decode on PC."""
        if len(raw_rgb) != 3072:
            raise ValueError(f"Expected 3072 raw bytes, got {len(raw_rgb)}")
            
        pc_crc = f"{zlib.crc32(raw_rgb):08X}"
        ref_img_np = np.frombuffer(raw_rgb, dtype=np.uint8).reshape((32, 32, 3))

        with self.lock:
            if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                raise RuntimeError("Bo mạch ESP32 chưa được kết nối! Vui lòng cắm cáp USB vào cổng COM5 và nhấn Kết nối.")
            
            self.log(f"[Pipeline P2] Bắt đầu mã hóa JPEG Quality {quality} trên phần cứng ESP32...")
            self.log(f"[UART TX] JPEG {quality}")
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(f"JPEG {quality}\n".encode("utf-8"))
            self.serial_conn.flush()
            
            # Wait for READY 3072
            deadline = time.monotonic() + 3.0
            ready = False
            while time.monotonic() < deadline:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.log(f"[UART RX] {line}")
                    if "READY 3072" in line:
                        ready = True
                        break
            if not ready:
                raise RuntimeError(f"ESP32 không phản hồi READY 3072 cho lệnh JPEG {quality}")
            
            # Send 3072 raw bytes
            self.log(f"[UART TX] Đang gửi 3072 bytes ảnh thô (CRC32: {pc_crc})...")
            self.serial_conn.write(raw_rgb)
            self.serial_conn.flush()
            
            # Read response header: JPEG <size> <crc32> <time_us>
            deadline = time.monotonic() + 5.0
            header_line = ""
            while time.monotonic() < deadline:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.log(f"[UART RX] {line}")
                    if JPEG_HEADER_REGEX.match(line):
                        header_line = line
                        break
                        
            m = JPEG_HEADER_REGEX.match(header_line)
            if not m:
                raise RuntimeError(f"ESP32 phản hồi header không hợp lệ: {header_line}")
                
            jpeg_size = int(m.group("size"))
            jpeg_crc = m.group("crc").upper()
            time_us = int(m.group("time_us"))
            
            # Read jpeg bytes
            jpeg_bytes = self.serial_conn.read(jpeg_size)
            if len(jpeg_bytes) != jpeg_size:
                raise RuntimeError(f"Chỉ nhận được {len(jpeg_bytes)}/{jpeg_size} bytes JPEG")
            
            actual_crc = f"{zlib.crc32(jpeg_bytes):08X}"
            if actual_crc != jpeg_crc:
                self.log(f"[UART Warning] CRC không khớp: dự kiến {jpeg_crc}, nhận {actual_crc}")

        # Decode JPEG on PC
        self.log(f"[Host PC] Đang giải mã luồng bitstream JPEG ({len(jpeg_bytes)} bytes)...")
        dec_pil = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
        rec_uint8 = np.array(dec_pil)

        psnr, ssim = self.compute_metrics(ref_img_np, rec_uint8)
        self.log(f"[Host PC] ✅ Tái tạo JPEG thành công: PSNR = {psnr:.2f} dB, SSIM = {ssim:.4f}")

        import base64
        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")

        return {
            "codec": f"JPEG Q{quality}",
            "quality": quality,
            "bytes": len(jpeg_bytes),
            "bpp": len(jpeg_bytes) * 8.0 / 1024.0,
            "compression_ratio": 3072.0 / len(jpeg_bytes),
            "time_ms": time_us / 1000.0,
            "time_us": time_us,
            "psnr": psnr,
            "ssim": ssim,
            "crc32": actual_crc,
            "image_b64": f"data:image/jpeg;base64,{b64_img}"
        }

    def benchmark_both(self, raw_rgb: bytes, quality: int = 70) -> Dict[str, Any]:
        """Run TinyCAE then JPEG and provide pairwise comparison."""
        t_res = self.encode_tinycae(raw_rgb)
        j_res = self.encode_jpeg(raw_rgb, quality=quality)
        
        speedup = t_res["time_ms"] / j_res["time_ms"] if j_res["time_ms"] > 0 else 0
        delta_psnr = t_res["psnr"] - j_res["psnr"]
        delta_ssim = t_res["ssim"] - j_res["ssim"]
        delta_bytes = t_res["bytes"] - j_res["bytes"]
        
        return {
            "tinycae": t_res,
            "jpeg": j_res,
            "speedup": speedup,
            "delta_psnr": delta_psnr,
            "delta_ssim": delta_ssim,
            "delta_bytes": delta_bytes
        }

ENGINE = CodecEngine()
