"""Rogue-agent meme generator for make.fun Meme Sprint 3.

Writes one 1024x1024 PNG meme to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png). Pure stdlib: no fonts, no network, no
randomness, no wall clock -- two runs are byte-identical.

The joke: asked to cancel free trials, the agent cancelled a wedding.
"""
import os
import struct
import zlib

W = H = 1024
CHARS = "ACDEFGHILMNORSTWY."
# 5x7 bitmap font, 35 bits per glyph, rows top to bottom, 5 bits a row.
FONT = (
    "01110100011000111111100011000110001"  # A
    "01110100011000010000100001000101110"  # C
    "11110100011000110001100011000111110"  # D
    "11111100001000011110100001000011111"  # E
    "11111100001000011110100001000010000"  # F
    "01110100011000010111100011000101111"  # G
    "10001100011000111111100011000110001"  # H
    "01110001000010000100001000010001110"  # I
    "10000100001000010000100001000011111"  # L
    "10001110111010110101100011000110001"  # M
    "10001110011010110011100011000110001"  # N
    "01110100011000110001100011000101110"  # O
    "11110100011000111110101001001010001"  # R
    "01111100001000001110000010000111110"  # S
    "11111001000010000100001000010000100"  # T
    "10001100011000110101101011101110001"  # W
    "10001100010101000100001000010000100"  # Y
    "00000000000000000000000000110001100"  # .
)

WHITE = b"\xff\xff\xff"
BLACK = b"\x00\x00\x00"
RED = b"\xeb\x2d\x2d"
GREY = b"\x99\x99\x99"
STEEL = b"\xd9\xde\xe3"
DARK = b"\x5a\x60\x68"
MID = b"\x96\x9e\xa6"
INK = b"\x14\x14\x14"

px = bytearray(W * H * 3)


def rect(x0, y0, x1, y1, c):
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = c * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        px[i:i + len(row)] = row


def disc(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        dx = int((r * r - (y - cy) ** 2) ** 0.5)
        rect(cx - dx, y, cx + dx + 1, y + 1, c)


def rrect(x0, y0, x1, y1, r, c):
    rect(x0 + r, y0, x1 - r, y1, c)
    rect(x0, y0 + r, x1, y1 - r, c)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                   (x0 + r, y1 - r), (x1 - r, y1 - r)):
        disc(cx, cy, r, c)


def line(x0, y0, x1, y1, c, t=4):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for s in range(n + 1):
        x = x0 + (x1 - x0) * s // n
        y = y0 + (y1 - y0) * s // n
        rect(x - t // 2, y - t // 2, x + t // 2 + 1, y + t // 2 + 1, c)


def text(s, x, y, sc, c):
    cx = x
    for ch in s:
        if ch == " ":
            cx += 6 * sc
            continue
        g = FONT[CHARS.index(ch) * 35:]
        for row in range(7):
            bits = g[row * 5:row * 5 + 5]
            for col in range(5):
                if bits[col] == "1":
                    rect(cx + col * sc, y + row * sc,
                         cx + (col + 1) * sc + 1, y + (row + 1) * sc, c)
        cx += 6 * sc
    return cx - x - sc


def ctext(s, y, sc, c):
    w = len(s) * 6 * sc - sc
    text(s, (W - w) // 2, y, sc, c)


def robot():
    # antenna
    rect(506, 196, 518, 224, MID)
    disc(512, 182, 15, RED)
    # ears
    rect(258, 330, 282, 420, DARK)
    rect(742, 330, 766, 420, DARK)
    # head
    rrect(274, 216, 750, 566, 52, DARK)
    rrect(282, 224, 742, 558, 46, STEEL)
    # left eye: wide and innocent
    rrect(352, 318, 472, 402, 18, WHITE)
    disc(412, 360, 22, INK)
    disc(404, 352, 7, WHITE)
    # right eye: narrowed, looking sideways
    rrect(552, 336, 672, 388, 14, WHITE)
    disc(622, 362, 15, INK)
    # raised eyebrow over the right eye
    line(556, 306, 664, 288, INK, 7)
    # smirk: rises on the right side
    for x in range(428, 612):
        y = 478 + (x - 520) ** 2 // 9000 - (x - 428) // 7
        rect(x, y, x + 1, y + 7, INK)
    # body
    rrect(352, 576, 672, 736, 30, DARK)
    rrect(360, 584, 664, 728, 24, MID)
    rect(452, 616, 572, 692, INK)
    disc(512, 654, 11, RED)
    # left arm down
    rect(296, 596, 352, 716, DARK)
    disc(324, 716, 22, DARK)
    # right arm raised, holding the card
    rect(672, 452, 724, 620, DARK)
    disc(698, 452, 22, DARK)
    # cancellation card
    rrect(648, 330, 962, 452, 10, RED)
    rrect(656, 338, 954, 444, 6, WHITE)
    text("CANCELLED", 700, 374, 4, RED)


def png_bytes():
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c +
                struct.pack(">I", zlib.crc32(c) & 0xffffffff))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    ctext("I TOLD MY AI AGENT TO", 44, 7, WHITE)
    ctext("CANCEL MY FREE TRIALS", 112, 7, WHITE)
    robot()
    ctext("IT CANCELLED MY WEDDING", 788, 7, RED)
    ctext("THE TRIAL WAS FREE. THE WEDDING WAS NOT.", 884, 3, GREY)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.png"), "wb") as f:
        f.write(png_bytes())


if __name__ == "__main__":
    main()
