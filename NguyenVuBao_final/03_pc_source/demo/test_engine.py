import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from host.demo.codec_engine import ENGINE

print("Connecting to COM5...")
connected = ENGINE.connect("COM5", 115200)
print(f"Connected: {connected}")

status = ENGINE.get_device_status()
print(f"Status: {status}")

raw_path = Path("data/processed/hardware_test/raw/cifar10_test_01789.rgb")
raw_img = raw_path.read_bytes()

print("Testing TinyCAE on hardware...")
t_res = ENGINE.encode_tinycae(raw_img)
print(f"TinyCAE result: {t_res['codec']}, {t_res['bytes']} B, {t_res['time_ms']:.2f} ms, PSNR={t_res['psnr']:.2f} dB, SSIM={t_res['ssim']:.4f}")

print("Testing JPEG on hardware...")
j_res = ENGINE.encode_jpeg(raw_img, quality=70)
print(f"JPEG result: {j_res['codec']}, {j_res['bytes']} B, {j_res['time_ms']:.2f} ms, PSNR={j_res['psnr']:.2f} dB, SSIM={j_res['ssim']:.4f}")

ENGINE.disconnect()
print("Engine test completed successfully!")
