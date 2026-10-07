"""Decode Lunar Genesis (JP Lunar: Dragon Song) script text, kanji included.

How the text works (docs/re-japanese.md): one byte per character; the byte is the index of an 8x16
cell in the dialogue font pack/005.bin (NTC4 header 0x30 bytes, then 4bpp 8x8 tiles; cell c is
tiles 2c (top) and 2c+1 (bottom)). The font is global, not per script: cells 0xCA-0xF8 hold the
47 kanji the whole game uses. wmpack/046.bin is the world-map variant, with Latin capitals in
0xC9-0xDF instead of kanji.

Usage:
  uv run python -m dsde.jp_text SCRIPT.bin [--font pack/005.bin] [--all] [--sheet OUT.png]

--all      decode every 0xFF-terminated string in the text area, not only the ones the
           script code references with opcode 0x0F (the default, )
--sheet    also write a labelled PNG of every font cell used, for checking glyphs by eye
           (needs pillow: uv run --with pillow python -m dsde.jp_text ...)
"""

import argparse
import logging
import struct
import sys
from pathlib import Path

logger = logging.getLogger("jp_decode")

DEFAULT_FONT = (
    Path(__file__).resolve().parents[2] / "build" / "unpacked_jp" / "pack" / "005.bin"
)
FONT_HEADER = 0x30
CELL_BYTES = 64
END, NEWLINE, PAGE, CTRL, PAGE_FORM = 0xFF, 0xFD, 0xFE, 0xFB, 0xFC
# Shown as [speaker], 〈place〉, 《item》. FB xx: 06 speaker name, 04 place name colour, 03 item colour; FB 07 ends any of them.
COLOR_RESET = 0x07
OPEN_MARK = {0x06: "[", 0x04: "〈", 0x03: "《"}
CLOSE_MARK = {0x06: "]", 0x04: "〉", 0x03: "》"}
MSG_OPCODE = 0x0F

HIRA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
SMALL_H, SMALL_K = "ぁぃぅぇぉっゃゅょ", "ァィゥェォッャュョ"
VOICED_H = "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
VOICED_K = "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"

# Read from the glyphs of pack/005.bin (cells.png) and checked against context in all 27 scripts.
SYMBOLS = {
    0x00: "　",
    0x01: "▼",
    0x02: "H",
    0x03: "L",
    0x04: "M",
    0x05: "P",
    0x06: "S",
    0x07: "V",
    0x08: "Z",
    0x09: "「",
    0x0A: "」",
    0x0B: "(",
    0x0C: ")",
    0x0D: "&",
    0x0E: "！",
    0x0F: "？",
    0x10: "ー",
    0x11: "。",
    0x12: "、",
    0x13: "：",
    0x14: "/",
    0xBF: "ヴ",
    0xC0: "〜",
    0xC1: "…",
    0xC2: "×",
    0xC3: "↑",
    0xC4: "↓",
    0xC5: "・",
    0xC6: "©",
    0xC7: "【",
    0xC8: "】",
    0xC9: "F",
    0xF9: "　",
}
KANJI = "必要世界女神竜使赤白青黒気来見行人間王言村町魔族法手中大陸心配地方天転呪生本当出存在入死剣悪獣"
KANJI_FIRST = 0xCA


def build_table() -> dict[int, str]:
    table = dict(SYMBOLS)
    for i in range(10):
        table[0x15 + i] = str(i)
    for base, chars in (
        (0x1F, HIRA),
        (0x4D, SMALL_H),
        (0x56, KATA),
        (0x84, SMALL_K),
        (0x8D, VOICED_H),
        (0xA6, VOICED_K),
    ):
        for i, ch in enumerate(chars):
            table[base + i] = ch
    for i, ch in enumerate(KANJI):
        table[KANJI_FIRST + i] = ch
    return table


TABLE = build_table()


def font_cells(font: bytes) -> list[bytes]:
    body = font[FONT_HEADER:]
    return [body[c * CELL_BYTES : (c + 1) * CELL_BYTES] for c in range(256)]


def check_font(font: bytes) -> None:
    """Warn when the font's kanji cells are not the ones the KANJI table was read from."""
    ref = font_cells(DEFAULT_FONT.read_bytes())
    cur = font_cells(font)
    bad = [c for c in range(256) if ref[c] != cur[c]]
    if bad:
        logger.warning(
            "font differs from pack/005.bin in cells %s; table may be wrong there",
            " ".join(f"{c:02X}" for c in bad),
        )


def decode(data: bytes, start: int, used: set[int]) -> str:
    out: list[str] = []
    closer = ""
    i = start
    while i < len(data):
        b = data[i]
        if b == END:
            break
        if b == CTRL:
            arg = data[i + 1]
            if arg in OPEN_MARK:
                closer = CLOSE_MARK[arg]
                out.append(OPEN_MARK[arg])
            elif arg == COLOR_RESET:
                out.append(closer or "<FB07>")
                closer = ""
            else:
                out.append(f"<FB{arg:02X}>")
            i += 2
            continue
        if b == NEWLINE:
            out.append("\n")
        elif b == PAGE:
            out.append("\n[page]\n")
        elif b == PAGE_FORM:
            out.append("<FC>")
        else:
            used.add(b)
            out.append(TABLE.get(b, f"{{{b:02X}}}"))
        i += 1
    return "".join(out)


def referenced(data: bytes, code: int) -> set[int]:
    """Text offsets the script code passes to the message opcode (0x0F)."""
    refs = set()
    for pc in range(code, len(data) - 7, 4):
        if struct.unpack_from("<H", data, pc)[0] == MSG_OPCODE:
            refs.add(struct.unpack_from("<I", data, pc + 4)[0])
    return {r for r in refs if 8 <= r < code}


def message_starts(data: bytes, every: bool) -> tuple[list[int], set[int]]:
    """Message offsets to print, and the subset the code references."""
    if len(data) < 8:
        logger.warning("file too short to hold a script header (%d bytes)", len(data))
        return [], set()
    code = struct.unpack_from("<I", data, 4)[0]
    refs = referenced(data, code)
    if not every:
        return sorted(refs), refs
    starts, s = [], 8
    while s < code:
        starts.append(s)
        e = data.find(bytes([END]), s, code)
        if e < 0:
            break
        s = e + 1
        while s < code and data[s] == 0:  # alignment padding before the code area
            s += 1
    return sorted(set(starts) | refs), refs


def write_sheet(font: bytes, codes: list[int], out: Path) -> None:
    from PIL import Image, ImageDraw

    cells = font_cells(font)
    scale, cols = 6, 16
    cw, ch = 8 * scale + 10, 16 * scale + 16
    img = Image.new(
        "RGB", (cols * cw, ((len(codes) + cols - 1) // cols) * ch), (30, 30, 50)
    )
    draw = ImageDraw.Draw(img)
    for n, c in enumerate(codes):
        gx, gy = (n % cols) * cw, (n // cols) * ch
        draw.text((gx + 2, gy + 1), f"{c:02X}", fill=(255, 255, 0))
        for y in range(16):
            for x in range(8):
                v = ((cells[c][y * 4 + x // 2] >> ((x & 1) * 4)) & 15) * 17
                x0, y0 = gx + 4 + x * scale, gy + 14 + y * scale
                draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=(v, v, v))
    img.save(out)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("script", type=Path)
    ap.add_argument("--font", type=Path, default=DEFAULT_FONT)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sheet", type=Path)
    args = ap.parse_args()
    font = args.font.read_bytes()
    check_font(font)
    data = args.script.read_bytes()
    used: set[int] = set()
    starts, refs = message_starts(data, args.all)
    for s in starts:
        note = "" if s in refs else "  (not referenced by the script code)"
        print(f"--- @{s:#x}{note}\n{decode(data, s, used)}")
    unknown = sorted(c for c in used if c not in TABLE)
    if unknown:
        logger.warning(
            "codes without a table entry: %s", " ".join(f"{c:02X}" for c in unknown)
        )
    if args.sheet:
        write_sheet(font, sorted(used), args.sheet)


if __name__ == "__main__":
    main()
