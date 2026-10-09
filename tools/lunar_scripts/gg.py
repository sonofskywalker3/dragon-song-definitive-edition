"""Lunar: Sanposuru Gakuen / Walking School (Game Gear): the message engine, and the Japanese dump.

    python -I gg.py jp   JP.gg OUT.txt              # Japanese script in the shared format, by message id
    python -I gg.py pair JP.gg EN.gg OUT.txt        # side by side, Japanese then English, same ids
    python -I gg.py font JP.gg                      # draw the Japanese 8x8 font (byte = tile + 0x10)

EN.gg is the Aeon Genesis v1.00 patched ROM (1 MB). ips_text.py builds the same memory from
the IPS alone and imports the engine from here.

How the game finds a message (traced in the Japanese ROM):

- A message id is a 16-bit value. 0xF000 + block * 0x100 + index is "message `index` of
  `block`" (0x12F7). Below 0xF000 it is a plain pointer. Scripts store the id big-endian
  (`F2 3D` = block 2, message 0x3D), and code loads it with `LD HL,0xFE7D`.
- The block table is at 0x14AE: 15 entries of (bank, address lo, address hi). The bank goes
  in slot 1 and bank + 1 in slot 2, so the address is in a 32 KB window at 0x4000-0xBFFF.
  Block 3 is empty (all zero).
- 0x129E finds message `index` by skipping that many 00-terminated strings. Bytes below 0x10
  are controls; the table at 0x149D gives how many parameter bytes each one takes, and a
  parameter can be 00. The English patch rewrites only the block table (to 0x80000+) and
  keeps the engine, so the same ids reach the English text.
- Nothing stores a block's length. Skipping past the end runs into whatever follows (the
  next block or data), so BLOCK_LENGTHS lists where each block's text ends. Each length is
  the count where the next block starts (in either ROM) or where the text turns into
  data, checked against the other ROM: past these counts the two ROMs stop agreeing.

Text (both ROMs): 00 end, 01 line break, 0B wait for a key and clear the box, 09 xx portrait
(00 = none), 03 xx inserts word xx of the list at 0x76B0 (names, places, items; the English
patch moves it to 0x96800). Other controls (02, 04-08, 0A, 0C, 0D) set up windows, choices,
and actors; they print as {XX:params}.

Japanese table, read off the font at 0x48200 (tile = byte - 0x10): 10 space, 11 ! 12 ? 13 ~
14 note 15 sweat drop 16 middle dot (the game's ellipsis is three of them) 17 、 18 。
19 heart 1A ( 1B ) 1C ゛ 1D ゜ 1E 「 1F 」 20-29 digits 2A-43 A-Z 44-5D a-z 5E ー,
5F-8C あ-ん, 8D-95 small ぁぃぅぇぉゃゅょっ, 96-C3 ア-ン, C4-CC small ァィゥェォャュョッ.
CD-FF are the voiced kana (が-ぽ, ヴ, ガ-ポ). They have no tile of their own (tiles CD-FF are
window borders; the ゛ and ゜ at 1C/1D sit at the bottom of the tile, as if drawn on the row
above), so they are read from context (しゅうごうばしょ,
ドキドキ, ヴェーン, せんぱい). The game has no kanji.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, write_dump  # noqa: E402

LOG = logging.getLogger("gg")

BANK_SIZE = 0x4000
SLOT1 = 0x4000
BLOCK_TABLE = 0x14AE
BLOCK_ENTRY = 3
BLOCK_COUNT = 15
ID_BASE = 0xF000
PARAM_TABLE = 0x149D
# Parameter bytes per control 00-0F, as stored at 0x149D (the English patch keeps it).
PARAMS = bytes((0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 4, 0, 1, 3, 0, 0))
CONTROL_LIMIT = 0x10

BLOCK_LENGTHS: dict[int, int] = {
    0: 48,
    1: 13,
    2: 166,
    4: 227,
    5: 153,
    6: 95,
    7: 129,
    8: 102,
    9: 105,
    10: 127,
    11: 105,
    12: 125,
    13: 115,
    14: 139,
}

END = 0x00
NEWLINE = 0x01
NAME = 0x03
PORTRAIT = 0x09
NEW_BOX = 0x0B
NO_PORTRAIT = 0x00
EN_ITEM_NEWLINE = 0x07  # the English item descriptions use 07 as a one-byte line break

JP_NAMES = 0x76B0
EN_NAMES = 0x96800
# 03 xx in the Japanese script reaches words 00-2C. The English script spells names out
# and never uses 03, but its list keeps the same order.
WORD_COUNT = 0x2D
FONT_START = 0x48200
FONT_FIRST_BYTE = 0x10
FONT_TILES = 0xC0
TILE_BYTES = 8
TILES_PER_ROW = 16

HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
SMALL_HIRAGANA = "ぁぃぅぇぉゃゅょっ"
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
SMALL_KATAKANA = "ァィゥェォャュョッ"
VOICED = (
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
    "ヴガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
)

JP_TABLE: dict[int, str] = {
    NEWLINE: "\n",
    NEW_BOX: "\n\n",
    0x10: "　",
    0x11: "！",
    0x12: "？",
    0x13: "〜",
    0x14: "♪",
    0x15: "[sweat]",
    0x16: "・",
    0x17: "、",
    0x18: "。",
    0x19: "♥",
    0x1A: "（",
    0x1B: "）",
    0x1C: "゛",
    0x1D: "゜",
    0x1E: "「",
    0x1F: "」",
    0x5E: "ー",
}
JP_TABLE.update({0x20 + i: str(i) for i in range(10)})
JP_TABLE.update({0x2A + i: chr(ord("A") + i) for i in range(26)})
JP_TABLE.update({0x44 + i: chr(ord("a") + i) for i in range(26)})
for _start, _chars in (
    (0x5F, HIRAGANA),
    (0x8D, SMALL_HIRAGANA),
    (0x96, KATAKANA),
    (0xC4, SMALL_KATAKANA),
    (0xCD, VOICED),
):
    JP_TABLE.update({_start + i: c for i, c in enumerate(_chars)})


@dataclass(frozen=True)
class Raw:
    msg_id: int
    offset: int
    data: bytes


@dataclass(frozen=True)
class Rendered:
    text: str
    portraits: tuple[str, ...]


Reader = Callable[[int], int]


def window_offset(bank: int, addr: int) -> int:
    """File offset of addr with bank in slot 1 and bank + 1 in slot 2."""
    return bank * BANK_SIZE + (addr - SLOT1)


def block_starts(mem: bytes) -> dict[int, int]:
    starts = {}
    for b in range(BLOCK_COUNT):
        p = BLOCK_TABLE + BLOCK_ENTRY * b
        bank, lo, hi = mem[p], mem[p + 1], mem[p + 2]
        if bank == 0 and lo == 0:
            continue
        starts[b] = window_offset(bank, lo | hi << 8)
    return starts


def split(mem: bytes, offset: int, count: int) -> Iterator[tuple[int, bytes]]:
    """The engine's string skipper (0x129E): controls skip their parameter bytes."""
    p = offset
    for _ in range(count):
        start = p
        while mem[p] != END:
            x = mem[p]
            p += 1 + (PARAMS[x] if x < CONTROL_LIMIT else 0)
        yield start, mem[start:p]
        p += 1


def messages(mem: bytes) -> list[Raw]:
    out = []
    starts = block_starts(mem)
    for b, n in BLOCK_LENGTHS.items():
        for i, (off, data) in enumerate(split(mem, starts[b], n)):
            out.append(Raw(ID_BASE + b * 0x100 + i, off, data))
    return out


def word_list(mem: bytes, offset: int, count: int) -> list[bytes]:
    return [d for _, d in split(mem, offset, count)]


def render(
    data: bytes,
    table: dict[int, str],
    names: list[str],
    one_byte: frozenset[int] = frozenset(),
) -> Rendered:
    parts: list[str] = []
    portraits: list[str] = []
    i = 0
    while i < len(data):
        x = data[i]
        if x in table and (
            x >= CONTROL_LIMIT or x in (NEWLINE, NEW_BOX) or x in one_byte
        ):
            parts.append(table[x])
            i += 1
            continue
        if x >= CONTROL_LIMIT:
            parts.append(f"{{{x:02X}}}")
            i += 1
            continue
        args = data[i + 1 : i + 1 + PARAMS[x]]
        i += 1 + PARAMS[x]
        if x == PORTRAIT and args:
            if args[0] == NO_PORTRAIT:
                continue
            tag = f"P{args[0]:02X}"
            portraits.append(tag)
            if "".join(parts).strip():
                parts.append(f"[{tag}] ")
        elif x == NAME and args and args[0] < len(names):
            parts.append(names[args[0]])
        else:
            parts.append(f"{{{x:02X}:{args.hex()}}}" if args else f"{{{x:02X}}}")
    return Rendered("".join(parts).strip("\n"), tuple(portraits))


def max_name_index(raws: list[Raw]) -> int:
    top = 0
    for r in raws:
        d = r.data
        i = 0
        while i < len(d):
            x = d[i]
            if x == NAME and i + 1 < len(d):
                top = max(top, d[i + 1])
            i += 1 + (PARAMS[x] if x < CONTROL_LIMIT else 0)
    return top


def jp_names(rom: bytes, count: int) -> list[str]:
    return [render(w, JP_TABLE, []).text for w in word_list(rom, JP_NAMES, count)]


def msg_label(msg_id: int) -> str:
    return f"msg {msg_id:04X}"


def jp_dump(rom: bytes) -> list[Message]:
    raws = messages(rom)
    n_names = max(max_name_index(raws) + 1, WORD_COUNT)
    names = jp_names(rom, n_names)
    out = []
    for i, (off, w) in enumerate(split(rom, JP_NAMES, n_names)):
        out.append(Message(f"word 03:{i:02X}", off, render(w, JP_TABLE, []).text))
    for r in raws:
        rr = render(r.data, JP_TABLE, names)
        out.append(Message(msg_label(r.msg_id), r.offset, rr.text, list(rr.portraits)))
    return out


def en_table() -> dict[int, str]:
    from ips_text import TABLE  # noqa: PLC0415  (ips_text imports this module)

    return TABLE


def en_names(mem: bytes, count: int) -> list[str]:
    tab = en_table()
    return [render(w, tab, []).text for w in word_list(mem, EN_NAMES, count)]


def en_render(data: bytes, names: list[str]) -> Rendered:
    return render(data, en_table(), names, frozenset({EN_ITEM_NEWLINE}))


def pair_text(jp: bytes, en: bytes) -> tuple[str, dict[str, int]]:
    jr, er = messages(jp), messages(en)
    n_names = max(max_name_index(jr), max_name_index(er)) + 1
    jn, enn = jp_names(jp, n_names), en_names(en, n_names)
    stats = {"pairs": 0, "same_portraits": 0, "both_none": 0, "differ": 0}
    lines = [
        "# Lunar: Walking School (Game Gear), Japanese and Aeon Genesis English by message id",
        "# produced by gg.py pair; ids are the game's own (F2 3D = block 2, message 0x3D)",
        "",
    ]
    for a, b in zip(jr, er, strict=True):
        ra, rb = render(a.data, JP_TABLE, jn), en_render(b.data, enn)
        stats["pairs"] += 1
        if ra.portraits == rb.portraits:
            stats["both_none" if not ra.portraits else "same_portraits"] += 1
        else:
            stats["differ"] += 1
        who = ", ".join(dict.fromkeys(ra.portraits)) or "-"
        lines.append(
            f"=== {a.msg_id:04X} | JP @0x{a.offset:X} | EN @0x{b.offset:X} | {who} ==="
        )
        lines.append(ra.text)
        lines.append("---")
        lines.append(rb.text)
        lines.append("")
    return "\n".join(lines), stats


def cmd_font(rom: bytes) -> None:
    for row in range(0, FONT_TILES, TILES_PER_ROW):
        first = FONT_FIRST_BYTE + row
        print(f"bytes {first:02X}-{first + TILES_PER_ROW - 1:02X}")
        for r in range(TILE_BYTES):
            cells = []
            for k in range(TILES_PER_ROW):
                x = rom[FONT_START + (row + k) * TILE_BYTES + r]
                cells.append(
                    "".join("#" if x >> (7 - b) & 1 else "." for b in range(8))
                )
            print("  ".join(cells))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("jp", "pair", "font"))
    ap.add_argument("rom", type=Path)
    ap.add_argument("rest", nargs="*")
    a = ap.parse_args()
    rom = a.rom.read_bytes()
    if rom[PARAM_TABLE : PARAM_TABLE + len(PARAMS)] != PARAMS:
        raise ValueError("control parameter table at 0x149D differs: not this game")
    if a.cmd == "font":
        cmd_font(rom)
    elif a.cmd == "jp":
        msgs = jp_dump(rom)
        write_dump(
            Path(a.rest[0]),
            "Lunar: Sanposuru Gakuen (Game Gear, Japan), by message id",
            "gg.py jp",
            msgs,
        )
        LOG.info("wrote %d entries to %s", len(msgs), a.rest[0])
    else:
        en = Path(a.rest[0]).read_bytes()
        text, stats = pair_text(rom, en)
        out = Path(a.rest[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        LOG.info("wrote %s: %s", out, stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
