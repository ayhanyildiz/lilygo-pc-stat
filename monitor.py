"""Windows CPU/RAM + NVIDIA GPU/VRAM telemetry for the T-Dongle-S3."""
import argparse
import ctypes
from ctypes import wintypes
import json
import logging
from pathlib import Path
import shutil
import subprocess
import time

import serial
from serial.tools import list_ports


class MemoryStatus(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
        (name, ctypes.c_ulonglong) for name in (
            "total", "available", "total_page", "available_page",
            "total_virtual", "available_virtual", "available_extended")]


class Metrics:
    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.GetSystemTimes.argtypes = [ctypes.POINTER(wintypes.FILETIME)] * 3
        self.kernel.GetSystemTimes.restype = wintypes.BOOL
        self.kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
        self.kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL
        self.previous = self.cpu_times()
        self.smi = shutil.which("nvidia-smi")

    def cpu_times(self):
        times = [wintypes.FILETIME() for _ in range(3)]
        if not self.kernel.GetSystemTimes(*(ctypes.byref(t) for t in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        return tuple((t.dwHighDateTime << 32) | t.dwLowDateTime for t in times)

    def sample(self):
        current = self.cpu_times()
        idle, kernel, user = (a - b for a, b in zip(current, self.previous))
        self.previous = current
        total = kernel + user  # Windows kernel time includes idle time.
        cpu = max(0, min(100, 100 * (total - idle) / total)) if total > 0 else 0
        memory = MemoryStatus()
        memory.length = ctypes.sizeof(memory)
        if not self.kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise ctypes.WinError(ctypes.get_last_error())
        gpu, vram = -1, -1
        if self.smi:
            try:
                output = subprocess.check_output([
                    self.smi, "--id=0",
                    "--query-gpu=utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits"], text=True, timeout=2,
                    creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL)
                raw = output.strip().split(",")
                try:
                    gpu = float(raw[0])
                except ValueError:
                    pass
                try:
                    used, capacity = float(raw[1]), float(raw[2])
                    vram = 100 * used / capacity if capacity else -1
                except ValueError:
                    pass
            except (OSError, subprocess.SubprocessError, IndexError):
                pass  # Unavailable metrics show --, never a stale percentage.
        return tuple(round(max(-1, min(100, n)), 1) for n in (
            cpu, gpu, 100 * (memory.total - memory.available) / memory.total, vram))


def connect(port):
    candidates = [port] if port else [p.device for p in list_ports.comports() if p.vid == 0x303A]
    for name in candidates:
        device = None
        try:
            device = serial.Serial()
            device.port, device.baudrate = name, 115200
            device.timeout, device.write_timeout = .3, 1
            device.dtr, device.rts = True, False
            device.open()
            device.reset_input_buffer()
            for _ in range(8):
                device.write(b"HELLO\n")
                if device.readline().strip() == b"PCMON,1":
                    logging.info("Connected to PC monitor on %s", name)
                    return device
                time.sleep(.2)
        except (OSError, serial.SerialException):
            pass
        if device:
            device.close()
    raise serial.SerialException("PC monitor not found; waiting for the dongle")


def run(args):
    metrics = Metrics()
    if args.sample:
        time.sleep(1)
        print(json.dumps(dict(zip(("cpu", "gpu", "ram", "vram"), metrics.sample()))))
        return
    device, seq, count = None, 0, 0
    while not args.frames or count < args.frames:
        started = time.monotonic()
        try:
            if device is None:
                device = connect(args.port)
            values = metrics.sample()
            seq += 1
            packet = f"M,{seq}," + ",".join(f"{n:.1f}" for n in values) + "\n"
            device.reset_input_buffer()
            device.write(packet.encode("ascii"))
            expected = f"ACK,{seq}".encode("ascii")
            deadline = time.monotonic() + 2
            while device.readline().strip() != expected:
                if time.monotonic() > deadline:
                    raise serial.SerialException("No display acknowledgement")
            count += 1
            if count == 1 or count % 30 == 0 or args.frames:
                logging.info("Display ACK %d: CPU %.1f%% GPU %.1f%% RAM %.1f%% VRAM %.1f%%", seq, *values)
            time.sleep(max(0, 1 - (time.monotonic() - started)))
        except (OSError, serial.SerialException) as error:
            logging.warning("%s", error)
            if device:
                device.close()
                device = None
            if args.frames:
                raise
            time.sleep(3)
    if device:
        device.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="Optional COM port; otherwise discovers Espressif USB devices")
    parser.add_argument("--frames", type=int, default=0, help="Exit after N acknowledged frames")
    parser.add_argument("--sample", action="store_true", help="Print one metric sample without USB")
    parser.add_argument("--log", type=Path, help="Log file for background operation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        filename=args.log)
    try:
        run(args)
    except KeyboardInterrupt:
        pass
    except Exception:
        logging.exception("PC monitor stopped unexpectedly")
        raise
