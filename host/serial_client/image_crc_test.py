"""Send one 32x32 RGB888 payload and compare CRC-32 with the ESP32."""

from __future__ import annotations

import argparse
import re
import sys
import time
import zlib

import serial
from serial import SerialException


IMAGE_RAW_SIZE = 32 * 32 * 3
DEFAULT_PORT = "COM5"
DEFAULT_BAUD_RATE = 115_200
STARTUP_DELAY_SECONDS = 3.0
LINE_TIMEOUT_SECONDS = 5.0
CRC_PATTERN = re.compile(r"^CRC32 ([0-9A-Fa-f]{8})$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a deterministic RGB888 payload and verify its CRC-32."
    )
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD_RATE)
    return parser.parse_args()


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


def run_test(port: str, baud_rate: int) -> bool:
    # The repeating 0..255 pattern is deterministic and exactly 3072 bytes long.
    payload = bytes(index & 0xFF for index in range(IMAGE_RAW_SIZE))
    expected_crc = zlib.crc32(payload) & 0xFFFFFFFF

    print(f"Opening {port} at {baud_rate} baud...")
    print(f"Payload: {len(payload)} bytes")
    print(f"PC CRC32: {expected_crc:08X}")

    with serial.Serial(port=port, baudrate=baud_rate, timeout=0.25) as device:
        device.dtr = False
        device.rts = False
        time.sleep(STARTUP_DELAY_SECONDS)
        device.reset_input_buffer()

        print("TX: IMAGE_CRC")
        device.write(b"IMAGE_CRC\r\n")
        device.flush()

        ready_line = read_nonempty_line(device, LINE_TIMEOUT_SECONDS)
        if ready_line != f"READY {IMAGE_RAW_SIZE}":
            print("FAIL: ESP32 did not request the expected payload size.", file=sys.stderr)
            return False

        print(f"TX: {len(payload)} raw bytes")
        device.write(payload)
        device.flush()

        crc_line = read_nonempty_line(device, LINE_TIMEOUT_SECONDS)
        if crc_line is None:
            print("FAIL: ESP32 did not return a CRC-32 value.", file=sys.stderr)
            return False

        match = CRC_PATTERN.fullmatch(crc_line)
        if match is None:
            print("FAIL: Unexpected ESP32 response.", file=sys.stderr)
            return False

        device_crc = int(match.group(1), 16)
        if device_crc != expected_crc:
            print(
                f"FAIL: CRC mismatch (PC={expected_crc:08X}, ESP32={device_crc:08X}).",
                file=sys.stderr,
            )
            return False

    print("PASS: 3072-byte payload and CRC-32 match.")
    return True


def main() -> int:
    args = parse_args()
    try:
        return 0 if run_test(args.port, args.baud) else 1
    except SerialException as error:
        print(f"SERIAL ERROR: {error}", file=sys.stderr)
        print("Close IDF Monitor and verify the COM port.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
