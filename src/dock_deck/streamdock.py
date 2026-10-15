"""Driver for the Mirabox HSV293S V3 stream dock (VID 0x6603, PID 0x1014), protocol v3.

A small Python implementation of the protocol as implemented by the mirajazz
and opendeck-akp153 projects (github.com/4ndv). Keys are addressed by
position = row * 6 + col; column 5 is the right-hand display, which takes
three images but has no buttons.
"""
import io
import logging

import hid
from PIL import Image

VID, PID = 0x6603, 0x1014
PACKET = 1024
COLS = 6
KEY_SIZE = 95
SIDE_KEY_SIZE = 82
POS_TO_DEVICE = [12, 9, 6, 3, 0, 15, 13, 10, 7, 4, 1, 16, 14, 11, 8, 5, 2, 17]
DEVICE_TO_POS = [4, 10, 16, 3, 9, 15, 2, 8, 14, 1, 7, 13, 0, 6, 12, 5, 11, 17]
log = logging.getLogger("dock-deck")
CRT = [0x00, 0x43, 0x52, 0x54, 0x00, 0x00]


def key_size(pos):
    return SIDE_KEY_SIZE if pos % COLS == 5 else KEY_SIZE


class StreamDock:
    def __init__(self):
        path = next(
            (d["path"] for d in hid.enumerate(VID, PID) if d["usage_page"] == 0xFFA0 and d["usage"] == 1),
            None,
        )
        if path is None:
            raise OSError("stream dock not connected")
        self._dev = hid.device()
        self._dev.open_path(path)

    def close(self):
        self._dev.close()

    def _cmd(self, payload):
        self._dev.write(bytes(CRT + payload).ljust(1 + PACKET, b"\x00"))

    def wake(self, brightness=100):
        self._cmd([0x44, 0x49, 0x53])  # DIS
        self._cmd([0x4C, 0x49, 0x47, 0x00, 0x00, brightness])  # LIG

    def clear(self):
        self._cmd([0x43, 0x4C, 0x45, 0x00, 0x00, 0x00, 0xFF])  # CLE all
        self.flush()

    def keep_alive(self):
        self._cmd([0x43, 0x4F, 0x4E, 0x4E, 0x45, 0x43, 0x54])  # CONNECT

    def flush(self):
        self._cmd([0x53, 0x54, 0x50])  # STP

    def set_image(self, pos, img):
        """Queue an image for a key; call flush() to show it."""
        size = key_size(pos)
        img = img.convert("RGB").resize((size, size), Image.LANCZOS)
        img = img.transpose(Image.ROTATE_90)  # device expects rot90 + mirror both
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90)
        data = buf.getvalue()
        n = len(data)
        self._cmd([0x42, 0x41, 0x54, 0x00, 0x00, n >> 8, n & 0xFF, POS_TO_DEVICE[pos] + 1])  # BAT
        for i in range(0, n, PACKET):
            self._dev.write(b"\x00" + data[i : i + PACKET].ljust(PACKET, b"\x00"))

    def read_key(self, timeout_ms):
        """Return (pos, pressed) for a key event, or None on timeout/other data."""
        data = self._dev.read(512, timeout_ms)
        if data:
            log.debug("raw %s", bytes(data[:16]).hex(" "))
        if len(data) < 11 or bytes(data[:3]) != b"ACK" or not 1 <= data[9] <= len(DEVICE_TO_POS):
            return None
        return DEVICE_TO_POS[data[9] - 1], data[10] == 1
