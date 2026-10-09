"""Draw the Japanese Mega CD Lunar fonts, so their character tables can be checked by eye.

    uv run --with pillow --with numpy python -I jpfont.py sheet  eb  IDATA.BIN OUT.png [--table T]
    uv run --with pillow --with numpy python -I jpfont.py sheet  tss TOMI.DAT  OUT.png [--table T]
    uv run --with pillow --with numpy python -I jpfont.py align  TOMI.DAT OUT_TABLE.txt --base eb_jp_table.txt

`sheet` draws every glyph (index above it) and, with --table, the table's character
under it in a system font, 128 glyphs per PNG (OUT-0.png, OUT-1.png, ...). That is how
eb_jp_table.txt and tss_jp_table.txt were checked.

Fonts:
- Eternal Blue: IDATA.BIN, u16 offset table at 0x2044 (0x600 entries, relative to
  0x2044). Each glyph is two 16-bit row masks (left and right 8-pixel halves); for each
  set bit (top row first) one byte follows, and that byte is XORed into the running row,
  so a row repeats until a byte changes it. 0x544 glyphs are used.
- The Silver Star: TOMI.DAT, plain 1bpp 16x16 at 0x1D010, 0x400 glyphs.

`align` drafts the Silver Star table: kana and symbols (0-0xD8) are copied from --base
(both games share that layout), and the kanji from 0xD9 to 0x3C4 follow JIS X 0208
order, so each glyph is matched against MS Gothic renderings of the JIS kanji with a
monotonic alignment (dynamic programming), favoring kanji that Eternal Blue's font has.
The draft still needs the eye check: it got 11 of 748 wrong (e.g. 噂 for 雨, 膿 for 農), and 0x3C5-0x3DD are a hand-ordered tail.
"""

from __future__ import annotations

import argparse
import logging
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LOG = logging.getLogger("jpfont")

GOTHIC = "C:/Windows/Fonts/msgothic.ttc"
EB_LUT, EB_ENTRIES, EB_GLYPHS = 0x2044, 0x600, 0x544
TSS_FONT, TSS_GLYPHS = 0x1D010, 0x400
CELL = 16
SHEET_COLS, SHEET_ROWS = 16, 8
TSS_KANJI_FIRST, TSS_JIS_LAST = 0xD9, 0x3C5
FIRST_JIS_KANJI = "亜"
KNOWN_BONUS = 0.12
SHIFT = 2  # pixels of slack when matching a glyph to a rendered character


def eb_glyphs(data: bytes) -> np.ndarray:
    lut = struct.unpack(f">{EB_ENTRIES}H", data[EB_LUT : EB_LUT + 2 * EB_ENTRIES])
    out = np.zeros((EB_GLYPHS, CELL, CELL), np.uint8)
    for i in range(EB_GLYPHS):
        p = EB_LUT + lut[i]
        masks = struct.unpack(">HH", data[p : p + 4])
        p += 4
        for half, mask in enumerate(masks):
            row = 0
            for r in range(CELL):
                if mask & (0x8000 >> r):
                    row ^= data[p]
                    p += 1
                for c in range(8):
                    out[i, r, half * 8 + c] = (row >> (7 - c)) & 1
    return out


def tss_glyphs(data: bytes) -> np.ndarray:
    raw = np.frombuffer(data[TSS_FONT : TSS_FONT + TSS_GLYPHS * 32], np.uint8)
    return np.unpackbits(raw.reshape(TSS_GLYPHS, CELL, 2), axis=2).reshape(
        TSS_GLYPHS, CELL, CELL
    )


def load_table(path: Path) -> dict[int, str]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            table[int(k, 16)] = v
    return table


def sheet(glyphs: np.ndarray, table: dict[int, str], out: Path) -> None:
    big = ImageFont.truetype(GOTHIC, 36)
    small = ImageFont.truetype(GOTHIC, 12)
    per = SHEET_COLS * SHEET_ROWS
    for page, start in enumerate(range(0, len(glyphs), per)):
        img = Image.new("L", (SHEET_COLS * 52, SHEET_ROWS * 100), 255)
        dr = ImageDraw.Draw(img)
        for k, i in enumerate(range(start, min(start + per, len(glyphs)))):
            x, y = (k % SHEET_COLS) * 52, (k // SHEET_COLS) * 100
            g = Image.fromarray(((1 - glyphs[i]) * 255).astype(np.uint8))
            img.paste(g.resize((48, 48), Image.NEAREST), (x + 2, y + 12))
            dr.text((x + 2, y), f"{i:X}", font=small, fill=0)
            if i in table:
                dr.text((x + 6, y + 60), table[i], font=big, fill=0)
            dr.rectangle((x, y, x + 51, y + 99), outline=180)
        path = out.with_name(f"{out.stem}-{page}{out.suffix}")
        img.save(path)
        LOG.info("wrote %s", path)


def jis_kanji() -> str:
    chars = []
    for hi in [*range(0x81, 0xA0), *range(0xE0, 0xEB)]:
        for lo in range(0x40, 0xFD):
            try:
                c = bytes([hi, lo]).decode("cp932")
            except UnicodeDecodeError:
                continue
            if len(c) == 1 and c not in chars:
                chars.append(c)
    s = "".join(chars)
    return s[s.index(FIRST_JIS_KANJI) :]


def render(chars: str) -> np.ndarray:
    font = ImageFont.truetype(GOTHIC, CELL)
    out = []
    for c in chars:
        im = Image.new("L", (CELL, CELL), 0)
        ImageDraw.Draw(im).text((0, 0), c, font=font, fill=255)
        out.append((np.array(im) > 127).astype(np.uint8))
    r = np.array(out)
    return r | np.pad(r, ((0, 0), (0, 0), (1, 0)))[:, :, :CELL]  # the game font is bold


def _shift(x: np.ndarray, dy: int, dx: int) -> np.ndarray:
    y = np.zeros_like(x)
    ys, yd = (
        slice(max(dy, 0), CELL + min(dy, 0)),
        slice(max(-dy, 0), CELL + min(-dy, 0)),
    )
    xs, xd = (
        slice(max(dx, 0), CELL + min(dx, 0)),
        slice(max(-dx, 0), CELL + min(-dx, 0)),
    )
    y[:, ys, xs] = x[:, yd, xd]
    return y


def _norm_blur(x: np.ndarray) -> np.ndarray:
    k = (0.25, 0.5, 0.25)
    p = np.pad(x.astype(np.float32), ((0, 0), (1, 1), (1, 1)))
    v = k[0] * p[:, :-2, :] + k[1] * p[:, 1:-1, :] + k[2] * p[:, 2:, :]
    b = k[0] * v[:, :, :-2] + k[1] * v[:, :, 1:-1] + k[2] * v[:, :, 2:]
    f = b.reshape(len(b), -1)
    f = f - f.mean(1, keepdims=True)
    return f / (np.linalg.norm(f, axis=1, keepdims=True) + 1e-6)


def similarity(glyphs: np.ndarray, cands: np.ndarray) -> np.ndarray:
    cn = _norm_blur(cands)
    best = np.full((len(glyphs), len(cands)), -2, np.float32)
    for dy in range(-SHIFT, SHIFT + 1):
        for dx in range(-SHIFT, SHIFT + 1):
            np.maximum(best, _norm_blur(_shift(glyphs, dy, dx)) @ cn.T, out=best)
    return best


def monotonic(score: np.ndarray) -> list[int]:
    """Pick one candidate per glyph, strictly increasing, with the highest total score."""
    n, m = score.shape
    total = score[0].copy()
    back = np.zeros((n, m), np.int32)
    for i in range(1, n):
        best_before = np.maximum.accumulate(total)
        arg = np.zeros(m, np.int64)
        cur, ci = -np.inf, 0
        for j in range(m):
            if total[j] > cur:
                cur, ci = total[j], j
            arg[j] = ci
        new = np.full(m, -np.inf, np.float32)
        new[1:] = score[i, 1:] + best_before[:-1]
        back[i, 1:] = arg[:-1]
        total = new
    j = int(np.argmax(total))
    path = [j]
    for i in range(n - 1, 0, -1):
        j = int(back[i, j])
        path.append(j)
    return path[::-1]


def align(tomi: Path, out: Path, base: Path) -> None:
    glyphs = tss_glyphs(tomi.read_bytes())
    table = {i: c for i, c in load_table(base).items() if i < TSS_KANJI_FIRST}
    kanji = jis_kanji()
    score = similarity(glyphs[TSS_KANJI_FIRST:TSS_JIS_LAST], render(kanji))
    # prefer kanji Eternal Blue's font also has: the games share most of their vocabulary
    known = set(load_table(base).values())
    score += np.array([KNOWN_BONUS if c in known else 0.0 for c in kanji], np.float32)
    for k, j in enumerate(monotonic(score)):
        table[TSS_KANJI_FIRST + k] = kanji[j]
    out.write_text(
        "".join(f"{i:X}={c}\n" for i, c in sorted(table.items())),
        encoding="utf-8",
        newline="\n",
    )
    LOG.info(
        "wrote draft table %s (%d entries); check it with `sheet`", out, len(table)
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("game", choices=("eb", "tss"))
    s.add_argument("font", type=Path)
    s.add_argument("out", type=Path)
    s.add_argument("--table", type=Path)
    a_ = sub.add_parser("align")
    a_.add_argument("font", type=Path)
    a_.add_argument("out", type=Path)
    a_.add_argument("--base", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "sheet":
        data = a.font.read_bytes()
        glyphs = eb_glyphs(data) if a.game == "eb" else tss_glyphs(data)
        sheet(glyphs, load_table(a.table) if a.table else {}, a.out)
    else:
        align(a.font, a.out, a.base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
