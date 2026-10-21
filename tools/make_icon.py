"""Generate assets/ininet.ico without external dependencies (stdlib only).

The icon is a rounded dark tile with a red network glyph (a central node with
three satellites), matching the project palette (#0a0a0a background, #e63946
accent). Renders several sizes into a single multi-image ICO. PNG is used as
the embedded image format, which Windows Vista+ supports natively.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

BG = (10, 10, 10)
ACCENT = (230, 57, 70)
GREEN = (126, 231, 135)
CYAN = (86, 212, 221)

CANVAS = 256


def _rounded_mask(size: int, radius: int) -> list[list[bool]]:
    mask = [[False] * size for _ in range(size)]
    r2 = radius * radius
    for y in range(size):
        for x in range(size):
            cx = min(max(x, radius), size - 1 - radius)
            cy = min(max(y, radius), size - 1 - radius)
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r2:
                mask[y][x] = True
    return mask


def _disc(size: int, cx: float, cy: float, radius: float, color):
    def paint(px):
        for y in range(size):
            for x in range(size):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy <= radius * radius:
                    px[y][x] = color

    return paint


def _line(size: int, x0: float, y0: float, x1: float, y1: float, width: float, color):
    def paint(px):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 2
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for oy in range(int(y - width), int(y + width) + 1):
                for ox in range(int(x - width), int(x + width) + 1):
                    if 0 <= ox < size and 0 <= oy < size:
                        dx, dy = ox - x, oy - y
                        if dx * dx + dy * dy <= width * width:
                            px[oy][ox] = color

    return paint


def _render(size: int) -> bytes:
    """Return raw RGBA pixels (top-to-bottom) for a size×size icon."""
    s = size
    px = [[(0, 0, 0, 0)] * s for _ in range(s)]
    mask = _rounded_mask(s, max(4, s // 8))

    c = s / 2
    node = s * 0.13
    sat = s * 0.075
    off = s * 0.30
    lw = max(2.0, s * 0.022)

    _disc(s, c, c, node, (*ACCENT, 255))(px)
    for ang in (90, 210, 330):
        import math

        rad = math.radians(ang)
        nx, ny = c + off * math.cos(rad), c + off * math.sin(rad)
        _line(s, c, c, nx, ny, lw, (90, 90, 90, 255))(px)
        _disc(s, nx, ny, sat, (*(CYAN if ang == 90 else GREEN), 255))(px)

    out = bytearray()
    for y in range(s):
        for x in range(s):
            if not mask[y][x]:
                out += bytes((0, 0, 0, 0))
            else:
                r, g, b, a = px[y][x]
                if a == 0:
                    r, g, b, a = BG[0], BG[1], BG[2], 255
                out += bytes((r, g, b, a))
    return bytes(out)


def _png(size: int, rgba: bytes) -> bytes:
    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def write_ico(path: Path, sizes=(16, 32, 48, 64, 128, 256)) -> None:
    images = [_png(sz, _render(sz)) for sz in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    entries = bytearray()
    offset = 6 + 16 * len(images)
    for sz, data in zip(sizes, images, strict=True):
        w = 0 if sz == 256 else sz
        h = 0 if sz == 256 else sz
        entries += struct.pack(
            "<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset
        )
        offset += len(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(header)
        fh.write(entries)
        for data in images:
            fh.write(data)


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "assets" / "ininet.ico"
    write_ico(target)
    print(f"wrote {target} ({target.stat().st_size} bytes)")
