"""Lunar 2: Eternal Blue (Saturn, Japan) dialogue dump.

    python -I l2eb_saturn.py FILE1 FILE2 FONT_TABLE WORKDIR OUT.txt

FILE1, FILE2 : the files named "1" (index) and "2" (data) in the disc root. Both discs
               carry identical copies, so disc 1 is enough.
FONT_TABLE   : lunar2_font_table.txt from MrConan1/lunar2_eb_sat_tools (glyph index ->
               character, "n,<tab>c" lines, # comments).

Format, from MrConan1's l2extract.c and l2_txt_decode main.c, ported here:

- Archive: "1" holds 5-byte entries (u24 BE start sector, u16 BE sector count) into "2",
  the same layout as the PS1 DATA.IDX/PAK. Saturn has no name list, so files are numbered
  from 1 (as l2extract numbers them).
- Dialogue lives in "ES" blocks (magic 45 53 00 01), at the start of a file or inside
  it. Relative to the block: u32 BE at +0x04 = portrait section, at +0x1C = text section.
  The text section is a run of dialogues, each u16 BE size (bytes, including the size
  word) followed by u16 BE words, up to the portrait section or a size of 0.
- Words below 0x1000 are 16x16 font indices. Above that the top nibble is a control:
  1 line break (three in a row end the dialogue), 2/7/8 wait and clear the box,
  3 a half-width glyph (index in the low 12 bits), 5 a choice of n options, each
  ending in 1000, 9 a space, B item name, C/F portrait, D animation, E pause.

A glyph the table lacks is printed as {XXXX}.

The upstream table (v1.0) has errors, found by drawing every glyph of its font sheets
(font_table/font1-6.BMP, glyph n at cell n + 13, palette index 1 = glyph body) next to
the table's character. TABLE_FIXES corrects them: the table skips 奥 at 288, so 288-332
were one early (１壊戦 for １回戦, 結歌 for 結果, 参可 for 参加), and seven single entries
were wrong (mostly duplicates of a neighbour).
"""

from __future__ import annotations

import argparse
import logging
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, write_dump  # noqa: E402

LOG = logging.getLogger("l2eb_saturn")

SECTOR = 0x800
IDX_ENTRY = 5
ES_MAGIC = b"ES\x00\x01"
PORTRAIT_PTR = 0x04
TEXT_PTR = 0x1C
GLYPH_LIMIT = 0x1000
SIZE_WORD = 2
NIB_NEWLINE = 0x1
NIB_BOX = frozenset({0x2, 0x7, 0x8})
NIB_HALF = 0x3
NIB_CHOICE = 0x5
NIB_SPACE = 0x9
NIB_ITEM = 0xB
NIB_PORTRAIT = frozenset({0xC, 0xF})
LOW12 = 0xFFF
TABLE_RE = re.compile(r"^(\d+),\s*(\S)")
SKIPPED_GLYPH = 288
SHIFT_END = 333
TABLE_FIXES: dict[int, str] = {
    16: "×",
    63: "え",
    269: "影",
    508: "劇",
    613: "砂",
    671: "飼",
    802: "寝",
    SKIPPED_GLYPH: "奥",
}
TITLE = "Lunar 2: Eternal Blue (Saturn, Japan, 1998)"


def load_table(path: Path) -> dict[int, str]:
    table: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if m := TABLE_RE.match(line):
            table[int(m.group(1))] = m.group(2)
    for i in range(SHIFT_END, SKIPPED_GLYPH, -1):
        table[i] = table[i - 1]
    table.update(TABLE_FIXES)
    return table


def unpack(file1: Path, file2: Path, outdir: Path) -> list[tuple[str, bytes]]:
    idx = file1.read_bytes()
    out = []
    outdir.mkdir(parents=True, exist_ok=True)
    with open(file2, "rb") as fh:
        for n in range(len(idx) // IDX_ENTRY):
            e = idx[n * IDX_ENTRY : (n + 1) * IDX_ENTRY]
            sector = int.from_bytes(e[:3], "big")
            count = int.from_bytes(e[3:5], "big")
            fh.seek(sector * SECTOR)
            data = fh.read(count * SECTOR)
            name = str(n + 1)
            (outdir / name).write_bytes(data)
            out.append((name, data))
    return out


def glyph(table: dict[int, str], code: int) -> str:
    return table.get(code, f"{{{code:04X}}}")


def decode_dialogue(
    table: dict[int, str], words: tuple[int, ...]
) -> tuple[str, list[str], bool]:
    text = ""
    speakers: list[str] = []
    choice = False
    for w in words:
        if w < GLYPH_LIMIT:
            text += glyph(table, w)
            continue
        nib = w >> 12
        if nib == NIB_NEWLINE:
            text += "\n"
        elif nib in NIB_BOX:
            text += "\n\n"
        elif nib == NIB_HALF:
            text += glyph(table, w & LOW12)
        elif nib == NIB_CHOICE:
            choice = True
            text += "\n"
        elif nib == NIB_SPACE:
            text += " "
        elif nib == NIB_ITEM:
            text += f"[item {w & LOW12:X}]"
        elif nib in NIB_PORTRAIT:
            sp = f"P{w:04X}"
            if text.strip():
                text += f"[{sp}] "
            speakers.append(sp)
    if choice:
        speakers.insert(0, "CHOICE")
    return text, speakers, choice


def scan(name: str, data: bytes, table: dict[int, str]) -> list[Message]:
    msgs: list[Message] = []
    start = data.find(ES_MAGIC)
    while start >= 0:
        if start + TEXT_PTR + 4 <= len(data):
            portrait = struct.unpack_from(">I", data, start + PORTRAIT_PTR)[0]
            pos = struct.unpack_from(">I", data, start + TEXT_PTR)[0]
            end = min(start + portrait, len(data))
            pos += start
            while pos + SIZE_WORD <= end:
                size = struct.unpack_from(">H", data, pos)[0]
                if size < SIZE_WORD or pos + size > end:
                    break
                n = (size - SIZE_WORD) // 2
                words = struct.unpack_from(f">{n}H", data, pos + SIZE_WORD)
                text, speakers, _ = decode_dialogue(table, words)
                if text.strip():
                    msgs.append(Message(name, pos, text, speakers))
                pos += size
        start = data.find(ES_MAGIC, start + len(ES_MAGIC))
    return msgs


def run(file1: Path, file2: Path, font: Path, work: Path, out: Path) -> int:
    table = load_table(font)
    messages: list[Message] = []
    for name, data in unpack(file1, file2, work / "data"):
        got = scan(name, data, table)
        if got:
            LOG.info("%s: %d messages", name, len(got))
        messages.extend(got)
    write_dump(out, TITLE, "l2eb_saturn.py (port of MrConan1 l2_txt_decode)", messages)
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    for a in ("file1", "file2", "font", "work", "out"):
        ap.add_argument(a, type=Path)
    a = ap.parse_args()
    run(a.file1, a.file2, a.font, a.work, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
