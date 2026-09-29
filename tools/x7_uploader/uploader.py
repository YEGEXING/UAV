#!/usr/bin/env python3
"""Upload a raw CUAV X7+ application image through its USB bootloader."""

import argparse
import struct
import sys
import time
import zlib

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print(
        "pyserial is required: python -m pip install -r "
        "tools/x7_uploader/requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)


INSYNC = 0x12
OK = 0x10
EOC = 0x20
GET_SYNC = 0x21
GET_DEVICE = 0x22
CHIP_ERASE = 0x23
CHIP_VERIFY = 0x24
PROG_MULTI = 0x27
READ_MULTI = 0x28
GET_CRC = 0x29
REBOOT = 0x30

INFO_BL_REV = 0x01
INFO_BOARD_ID = 0x02
INFO_BOARD_REV = 0x03
INFO_FLASH_SIZE = 0x04

EXPECTED_BOARD_ID = 1010
EXPECTED_APP_FLASH_SIZE = 1920 * 1024
TRANSFER_MAX = 224


class BootloaderError(RuntimeError):
    pass


class Firmware:
    def __init__(self, path):
        with open(path, "rb") as stream:
            self.image = bytearray(stream.read())
        if not self.image:
            raise BootloaderError("Firmware file is empty.")
        while len(self.image) % 4:
            self.image.append(0xFF)

    @property
    def size(self):
        return len(self.image)

    def crc(self, flash_size):
        if self.size > flash_size:
            raise BootloaderError(
                f"Firmware is too large: {self.size} > {flash_size} bytes."
            )

        state = zlib.crc32(self.image, 0xFFFFFFFF) ^ 0xFFFFFFFF
        remaining = flash_size - self.size
        padding = b"\xFF" * 4096
        while remaining:
            count = min(remaining, len(padding))
            state = zlib.crc32(
                padding[:count], state ^ 0xFFFFFFFF
            ) ^ 0xFFFFFFFF
            remaining -= count
        return state & 0xFFFFFFFF


class Uploader:
    def __init__(self, port, baud):
        self.port_name = port
        self.serial = serial.Serial(
            port=port, baudrate=baud, timeout=1.0, write_timeout=2.0
        )
        self.bootloader_revision = None
        self.board_id = None
        self.board_revision = None
        self.flash_size = None

    def close(self):
        try:
            self.serial.close()
        except Exception:
            pass

    def send(self, data):
        self.serial.write(data)
        self.serial.flush()

    def receive(self, count, timeout=1.0):
        previous_timeout = self.serial.timeout
        self.serial.timeout = timeout
        try:
            data = self.serial.read(count)
        finally:
            self.serial.timeout = previous_timeout
        if len(data) != count:
            raise BootloaderError(
                f"Timeout on {self.port_name}: wanted {count} bytes, "
                f"got {len(data)}."
            )
        return data

    def receive_status(self, timeout=2.0):
        reply = self.receive(2, timeout)
        if reply != bytes([INSYNC, OK]):
            raise BootloaderError(f"Bootloader returned status {reply.hex()}.")

    def synchronize(self):
        self.serial.reset_input_buffer()
        self.send(bytes([GET_SYNC, EOC]))
        self.receive_status(1.0)

    def get_info(self, info_id):
        self.send(bytes([GET_DEVICE, info_id, EOC]))
        value = struct.unpack("<I", self.receive(4))[0]
        self.receive_status()
        return value

    def identify(self):
        self.synchronize()
        self.bootloader_revision = self.get_info(INFO_BL_REV)
        if not 2 <= self.bootloader_revision <= 5:
            raise BootloaderError(
                f"Unsupported bootloader revision {self.bootloader_revision}."
            )
        self.board_id = self.get_info(INFO_BOARD_ID)
        self.board_revision = self.get_info(INFO_BOARD_REV)
        self.flash_size = self.get_info(INFO_FLASH_SIZE)

    def validate_target(self):
        if self.board_id != EXPECTED_BOARD_ID:
            raise BootloaderError(
                f"Wrong board: bootloader reports ID {self.board_id}, "
                f"X7 requires {EXPECTED_BOARD_ID}."
            )
        if self.flash_size != EXPECTED_APP_FLASH_SIZE:
            raise BootloaderError(
                f"Unexpected application area: {self.flash_size} bytes, "
                f"expected {EXPECTED_APP_FLASH_SIZE}."
            )

    def erase(self):
        print("Erase   : starting...")
        self.send(bytes([CHIP_ERASE, EOC]))
        self.receive_status(30.0)
        print("Erase   : 100%")

    def program(self, firmware):
        total = firmware.size
        for start in range(0, total, TRANSFER_MAX):
            block = firmware.image[start:start + TRANSFER_MAX]
            packet = bytes([PROG_MULTI, len(block)]) + block + bytes([EOC])
            self.send(packet)
            self.receive_status()
            progress = min(start + len(block), total) * 100 // total
            print(f"\rProgram : {progress:3d}%", end="", flush=True)
        print()

    def verify(self, firmware):
        if self.bootloader_revision == 2:
            self.send(bytes([CHIP_VERIFY, EOC]))
            self.receive_status()
            for start in range(0, firmware.size, TRANSFER_MAX):
                expected = bytes(firmware.image[start:start + TRANSFER_MAX])
                self.send(bytes([READ_MULTI, len(expected), EOC]))
                actual = self.receive(len(expected), 2.0)
                self.receive_status()
                if actual != expected:
                    raise BootloaderError(
                        f"Verify failed near offset 0x{start:X}."
                    )
        else:
            expected_crc = firmware.crc(self.flash_size)
            self.send(bytes([GET_CRC, EOC]))
            actual_crc = struct.unpack("<I", self.receive(4, 30.0))[0]
            self.receive_status()
            print(
                f"CRC     : board=0x{actual_crc:08X}, "
                f"file=0x{expected_crc:08X}"
            )
            if actual_crc != expected_crc:
                raise BootloaderError("CRC verification failed.")
        print("Verify  : 100%")

    def reboot(self):
        print("Rebooting board...")
        try:
            self.send(bytes([REBOOT, EOC]))
        except Exception:
            pass


def describe_port(item):
    return f"{item.device}: {item.description} [{item.hwid}]"


def bootloader_candidates(port_items):
    non_bluetooth = [
        item
        for item in port_items
        if "BTHENUM" not in (item.hwid or "").upper()
    ]
    markers = (
        "VID:PID=1209:5741",
        "VID:PID=0483:5740",
        "ARDUPILOT",
        "STMICROELECTRONICS VIRTUAL COM PORT",
    )
    preferred = [
        item
        for item in non_bluetooth
        if any(
            marker in f"{item.description} {item.hwid}".upper()
            for marker in markers
        )
    ]
    return preferred if preferred else non_bluetooth


def find_bootloader(port, baud, wait_seconds, verbose=False):
    deadline = time.time() + wait_seconds
    announced = False
    seen_ports = set()
    last_errors = {}

    while time.time() < deadline:
        port_items = list(list_ports.comports())
        if port:
            candidates = [port]
        else:
            candidates = [item.device for item in bootloader_candidates(port_items)]

        current_ports = {item.device for item in port_items}
        if current_ports != seen_ports:
            if port_items:
                print("Serial ports detected:")
                for item in port_items:
                    print(f"  {describe_port(item)}")
            else:
                print("No serial ports are currently detected by Windows.")
            seen_ports = current_ports

        for candidate in candidates:
            uploader = None
            try:
                uploader = Uploader(candidate, baud)
                uploader.identify()
                return uploader
            except Exception as error:
                message = f"{type(error).__name__}: {error}"
                if verbose and last_errors.get(candidate) != message:
                    print(f"  {candidate} handshake failed: {message}")
                last_errors[candidate] = message
                if uploader:
                    uploader.close()

        if not announced:
            print(
                "Waiting for the X7 bootloader; unplug and reconnect "
                "the Type-C cable..."
            )
            announced = True
        time.sleep(0.5)

    details = "; ".join(
        f"{name}: {error}" for name, error in last_errors.items()
    )
    if not details:
        details = "Windows did not expose any serial port"
    raise BootloaderError(
        f"No compatible serial bootloader was found ({details})."
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="CUAV X7+ FMT USB bootloader uploader"
    )
    parser.add_argument("--firmware", help="Raw application .bin file")
    parser.add_argument("--port", help="Serial port, for example COM7")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--wait", type=int, default=30)
    parser.add_argument(
        "--verbose", action="store_true", help="Show per-port handshake errors"
    )
    parser.add_argument(
        "--identify", action="store_true", help="Identify only; do not write"
    )
    parser.add_argument(
        "--yes", action="store_true", help="Required to erase and program"
    )
    args = parser.parse_args()
    if not args.identify and not args.firmware:
        parser.error("--firmware is required unless --identify is used")
    return args


def main():
    args = parse_args()
    firmware = Firmware(args.firmware) if args.firmware else None
    uploader = None

    try:
        uploader = find_bootloader(
            args.port, args.baud, args.wait, args.verbose
        )
        print("Bootloader found")
        print(f"  Port           : {uploader.port_name}")
        print(f"  Bootloader rev : {uploader.bootloader_revision}")
        print(f"  Board ID       : {uploader.board_id}")
        print(f"  Board revision : {uploader.board_revision}")
        print(f"  App flash size : {uploader.flash_size} bytes")
        uploader.validate_target()
        print("  Target check   : CUAV X7+ compatible")

        if args.identify:
            print("Identify-only mode: nothing was written.")
            return 0
        if firmware.size > uploader.flash_size:
            raise BootloaderError(
                "Firmware does not fit in the application area."
            )
        if not args.yes:
            print("Nothing was written. Re-run with --yes after checking the target.")
            return 2

        uploader.erase()
        uploader.program(firmware)
        uploader.verify(firmware)
        uploader.reboot()
        print("Upload completed successfully.")
        return 0
    except (BootloaderError, serial.SerialException, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        if uploader:
            uploader.close()


if __name__ == "__main__":
    raise SystemExit(main())
