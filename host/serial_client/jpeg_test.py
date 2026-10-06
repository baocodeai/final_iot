"""Send a 32x32 RGB888 test image, receive JPEG from ESP32, and verify it."""

from __future__ import annotations

import argparse
import re
import sys
import time
import zlib
from pathlib import Path

import serial
from PIL import Image
from serial import SerialException


WIDTH = 32
HEIGHT = 32
CHANNELS = 3
IMAGE_RAW_SIZE = WIDTH * HEIGHT * CHANNELS
DEFAULT_PORT = "COM5"
DEFAULT_BAUD_RATE = 115_200
STARTUP_DELAY_SECONDS = 4.0
LINE_TIMEOUT_SECONDS = 10.0
JPEG_HEADER_PATTERN = re.compile(
    r"^JPEG (?P<size>\d+) (?P<crc>[0-9A-Fa-f]{8}) (?P<time_us>\d+)$"
)
DEFAULT_OUTPUT = Path("bitstreams/jpeg/test_q50.jpg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Encode a generated RGB test image as JPEG on ESP32."
    )
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD_RATE)
    parser.add_argument("--quality", type=int, default=50)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def make_test_image() -> bytes:
    pixels = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            red = round(255 * x / (WIDTH - 1))
            green = round(255 * y / (HEIGHT - 1))
            blue = 255 - red
            pixels.extend((red, green, blue))
    return bytes(pixels)


def read_nonempty_line(device: serial.Serial, timeout_seconds: float) -> str | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        raw_line = device.readline()
        if not raw_line:
            continue
        line = raw_line.decode("utf-8", errors="replace").strip()
        if line:
            print(f"RX: {line}")
            return line
    return None


def wait_for_line(
    device: serial.Serial,
    predicate,
    timeout_seconds: float,
) -> str | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        line = read_nonempty_line(device, min(remaining, 0.5))
        if line is None:
            continue
        if line.startswith("ERROR "):
            return line
        if predicate(line):
            return line
    return None


def read_exact(device: serial.Serial, size: int, timeout_seconds: float) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout_seconds
    while len(result) < size and time.monotonic() < deadline:
        chunk = device.read(size - len(result))
        if chunk:
            result.extend(chunk)
    return bytes(result)


def run_test(
    port: str,
    baud_rate: int,
    quality: int,
    output_path: Path,
) -> bool:
    if not 1 <= quality <= 100:
        raise ValueError("JPEG quality must be between 1 and 100")

    payload = make_test_image()
    print(f"Opening {port} at {baud_rate} baud...")
    print(f"Input: RGB888 {WIDTH}x{HEIGHT}, {len(payload)} bytes")

    with serial.Serial(port=port, baudrate=baud_rate, timeout=0.25) as device:
        device.dtr = False
        device.rts = False
        time.sleep(STARTUP_DELAY_SECONDS)
        device.reset_input_buffer()

        print(f"TX: JPEG {quality}")
        device.write(f"JPEG {quality}\r\n".encode("ascii"))
        device.flush()

        ready_line = wait_for_line(
            device,
            lambda line: line == f"READY {IMAGE_RAW_SIZE}",
            LINE_TIMEOUT_SECONDS,
        )
        if ready_line != f"READY {IMAGE_RAW_SIZE}":
            print(
                f"FAIL: ESP32 did not request the expected input size (last={ready_line!r}).",
                file=sys.stderr,
            )
            return False

        print(f"TX: {len(payload)} raw bytes")
        device.write(payload)
        device.flush()

        header_line = wait_for_line(
            device,
            lambda line: JPEG_HEADER_PATTERN.fullmatch(line) is not None,
            LINE_TIMEOUT_SECONDS,
        )
        if header_line is None:
            print("FAIL: JPEG response header timed out.", file=sys.stderr)
            return False

        match = JPEG_HEADER_PATTERN.fullmatch(header_line)
        if match is None:
            print("FAIL: Unexpected JPEG response header.", file=sys.stderr)
            return False

        jpeg_size = int(match.group("size"))
        expected_crc = int(match.group("crc"), 16)
        encode_time_us = int(match.group("time_us"))
        jpeg_data = read_exact(device, jpeg_size, LINE_TIMEOUT_SECONDS)

    if len(jpeg_data) != jpeg_size:
        print(
            f"FAIL: Expected {jpeg_size} JPEG bytes, received {len(jpeg_data)}.",
            file=sys.stderr,
        )
        return False

    actual_crc = zlib.crc32(jpeg_data) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        print(
            f"FAIL: JPEG CRC mismatch (ESP32={expected_crc:08X}, PC={actual_crc:08X}).",
            file=sys.stderr,
        )
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(jpeg_data)

    with Image.open(output_path) as decoded:
        decoded.load()
        if decoded.size != (WIDTH, HEIGHT):
            print(f"FAIL: Decoded size is {decoded.size}.", file=sys.stderr)
            return False
        decoded_mode = decoded.mode

    print(f"JPEG bytes: {jpeg_size}")
    print(f"JPEG CRC32: {actual_crc:08X}")
    print(f"ESP32 core encode time: {encode_time_us} us")
    print(f"Decoded image: {WIDTH}x{HEIGHT}, mode={decoded_mode}")
    print(f"Saved: {output_path.resolve()}")
    print("PASS: ESP32 JPEG stream is complete and decodes correctly.")
    return True


def main() -> int:
    args = parse_args()
    try:
        return 0 if run_test(args.port, args.baud, args.quality, args.output) else 1
    except (SerialException, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
