#!/usr/bin/env python3
"""Generate build/icon.icns for the yt-dlp GUI .app bundle.

Draws a dark rounded-rectangle with a red play triangle. Pure stdlib (no PIL)
so it runs inside the GUI virtualenv without extra dependencies. Re-run this
only when the icon design changes.
"""

import os
import struct
import zlib
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ICONSET = BUILD / 'icon.iconset'


def write_png(path: Path, size: int) -> None:
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # no filter
        for x in range(size):
            raw += bytes(icon_px(x, y, size))

    def chunk(typ: bytes, data: bytes) -> bytes:
        body = typ + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', zlib.compress(bytes(raw), 9)))
        f.write(chunk(b'IEND', b''))


def icon_px(x: float, y: float, size: int):
    m = size * 0.04
    r = size * 0.22
    inx = m <= x <= size - m
    iny = m <= y <= size - m
    if inx and iny:
        bg = (24, 26, 32, 255)
    else:
        bg = (0, 0, 0, 0)
        for ccx, ccy, sx, sy in (
            (m + r, m + r, -1, -1),
            (size - m - r, m + r, 1, -1),
            (m + r, size - m - r, -1, 1),
            (size - m - r, size - m - r, 1, 1),
        ):
            if (x - ccx) * sx > 0 and (y - ccy) * sy > 0 and (x - ccx) ** 2 + (y - ccy) ** 2 <= r * r:
                bg = (24, 26, 32, 255)
                break

    # Red play triangle centered in the icon.
    ax, ay = 0.40 * size, 0.32 * size
    bx, by = 0.40 * size, 0.68 * size
    cx, cy = 0.76 * size, 0.50 * size

    def sign(px, py, qx, qy, rx, ry):
        return (px - rx) * (qy - ry) - (qx - rx) * (py - ry)

    d1 = sign(x, y, ax, ay, bx, by)
    d2 = sign(x, y, bx, by, cx, cy)
    d3 = sign(x, y, cx, cy, ax, ay)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    if not (has_neg and has_pos):
        return (255, 60, 60, 255)
    return bg


def main() -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        write_png(ICONSET / f'icon_{s}x{s}.png', s)
        write_png(ICONSET / f'icon_{s}x{s}@2x.png', s * 2)
    out = BUILD / 'icon.icns'
    os.system(f'iconutil -c icns "{ICONSET}" -o "{out}"')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
