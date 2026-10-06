"""Check the PC-to-ESP32 serial link with a PING/PONG exchange."""

from __future__ import annotations

import argparse
import sys
import time

import serial
from serial import SerialException


DEFAULT_PORT = "COM5"
DEFAULT_BAUD_RATE = 115_200
STARTUP_DELAY_SECONDS = 3.0
RESPONSE_TIMEOUT_SECONDS = 2.0
MAX_ATTEMPTS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send PING to the ESP32 and require a PONG response."
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        help=f"Serial port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD_RATE,
        help=f"Baud rate (default: {DEFAULT_BAUD_RATE})",
    )
    return parser.parse_args()


def run_ping_test(port: str, baud_rate: int) -> bool:
    print(f"Opening {port} at {baud_rate} baud...")

    with serial.Serial(port=port, baudrate=baud_rate, timeout=0.25) as device:
        # Do not leave the ESP32 auto-reset circuit asserted after opening FT232R.
        device.dtr = False
        device.rts = False

        # Opening the port can still produce a short reset pulse. Allow boot to finish.
        time.sleep(STARTUP_DELAY_SECONDS)
        device.reset_input_buffer()

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"TX: PING (attempt {attempt}/{MAX_ATTEMPTS})")
            device.write(b"PING\r\n")
            device.flush()

            deadline = time.monotonic() + RESPONSE_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                raw_line = device.readline()
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                print(f"RX: {line}")
                if line == "PONG":
                    return True

    return False


def main() -> int:
    args = parse_args()

    try:
        success = run_ping_test(args.port, args.baud)
    except SerialException as error:
        print(f"SERIAL ERROR: {error}", file=sys.stderr)
        print("Close IDF Monitor and verify the COM port, cable, and driver.")
        return 2

    if not success:
        print("FAIL: PONG was not received before the timeout.", file=sys.stderr)
        return 1

    print("PASS: ESP32 replied with PONG.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
