"""Tiny RGBA PNG writer/reader (no dependencies)."""
import struct
import zlib


def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write(path, width, height, pixels):
    """pixels: list of rows, each a list of (r, g, b, a) tuples."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


def read_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


class Canvas:
    """RGBA canvas with simple drawing helpers."""

    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.px = [[fill for _ in range(w)] for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if len(c) == 3:
                c = (*c, 255)
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x]

    def blend(self, x, y, c, alpha):
        if 0 <= x < self.w and 0 <= y < self.h:
            r, g, b, a = self.px[y][x]
            self.px[y][x] = (
                int(r + (c[0] - r) * alpha),
                int(g + (c[1] - g) * alpha),
                int(b + (c[2] - b) * alpha),
                max(a, 255 if alpha > 0 else a),
            )

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def save(self, path):
        write(path, self.w, self.h, self.px)
