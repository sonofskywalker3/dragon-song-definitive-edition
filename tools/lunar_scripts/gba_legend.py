"""Lunar Legend (GBA): dialogue and plain-string dump.

    python -I gba_legend.py script  ROM.gba OUT.txt [--table 0x7FD564 --count 140] [--jp]
    python -I gba_legend.py strings ROM.gba OUT.txt [--start 0x92000 --end 0x98000]

Format (traced in BizHawk/mGBA, see lunar_scripts/legend_gba/README.md):

- Each map's event script is one LZSS block. A table of 140 ROM pointers (USA: 0x7FD564,
  one per map, 78 distinct blocks at 0x62DAE4-0x6BF042) points at the blocks.
- Block: u32 decompressed size, u32 data length, data bytes, then the flag bits (LSB
  first, one per token). Flag 0 = copy one literal byte. Flag 1 = u16 LE v from the data:
  copy (v >> 12) + 3 bytes from distance (v & 0xFFF) + 1 back. Decoder: 0x08000D9C.
- The block is loaded to EWRAM 0x02016000: 256 u16 event offsets, then bytecode from
  0x02016200 (opcode table 0x0862D6C0, 80 ops). Text sits inline in three ops:
  00 xx nnnn yyyy (dialogue), 17 xx xx xx nnnn (narration, nnnn = unit count) and
  33 nn ... (8-byte header, a choice), each followed by u16 units up to 0F00.
- A unit is u16 LE: high byte 0 = glyph (same table as the plain strings), else a
  control with its parameter in the low byte: 07 wait, 08 new box, 09 line break,
  0A auto-advance (frames), 0D/0E portrait, 0F end. High bit 0x10 marks a two-byte
  glyph (index ((hi & 0xEF) << 8) | lo): unused in English, the kanji path for Japanese.
"""

from __future__ import annotations

import argparse
import logging
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, looks_like_text, write_dump  # noqa: E402

LOG = logging.getLogger("gba_legend")

ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000

# ---- character table (shared by the plain strings and the script units) ----
END = 0xFF
SPACE = 0x00
LOWER = range(0x01, 0x1B)
UPPER = range(0xAC, 0xC6)
DIGITS = range(0xA2, 0xAC)
# Read off the dialogue font in VRAM (tile 2*code of the text charblock).
PUNCT = {
    0x1B: "'", 0x1C: "*", 0x1D: '"', 0x1E: "%", 0x1F: ",",
    0xC6: "[", 0xC7: "]", 0xC8: "「", 0xC9: "」", 0xCA: "(", 0xCB: ")",
    0xCC: "&", 0xCD: "@", 0xCE: "!", 0xCF: "?", 0xD0: "-", 0xD1: "=",
    0xD2: "。", 0xD3: ";", 0xD4: ".", 0xD5: ",", 0xD7: ":", 0xDD: "+",
}  # fmt: skip
MIN_LEN = 3


def glyph(x: int) -> str:
    if x == SPACE:
        return " "
    if x in LOWER:
        return chr(x - LOWER.start + ord("a"))
    if x in UPPER:
        return chr(x - UPPER.start + ord("A"))
    if x in DIGITS:
        return chr(x - DIGITS.start + ord("0"))
    return PUNCT.get(x, f"{{{x:02X}}}")


def decode(b: bytes) -> str:
    return "".join(glyph(x) for x in b)


# ---- LZSS blocks ----
HEADER = struct.Struct("<II")  # decompressed size, data length
MAX_BLOCK = 0x40000
DIST_MASK = 0xFFF
LEN_SHIFT = 12
MIN_COPY = 3


def decompress(rom: bytes, off: int) -> bytes:
    size, dlen = HEADER.unpack_from(rom, off)
    src = off + HEADER.size
    flags = src + dlen
    out = bytearray()
    bit = 0
    while len(out) < size:
        is_copy = (rom[flags + (bit >> 3)] >> (bit & 7)) & 1
        bit += 1
        if not is_copy:
            out.append(rom[src])
            src += 1
            continue
        v = rom[src] | rom[src + 1] << 8
        src += 2
        dist = (v & DIST_MASK) + 1
        if dist > len(out):
            raise ValueError(f"block 0x{off:X}: copy distance {dist} before start")
        for _ in range((v >> LEN_SHIFT) + MIN_COPY):
            out.append(out[-dist])
    return bytes(out[:size])


def plausible_block(rom: bytes, ptr: int) -> bool:
    off = ptr - ROM_BASE
    if not (ROM_BASE <= ptr < ROM_LIMIT and off + HEADER.size <= len(rom)):
        return False
    size, dlen = HEADER.unpack_from(rom, off)
    return 0 < dlen < size <= MAX_BLOCK and off + HEADER.size + dlen < len(rom)


def find_table(rom: bytes, min_run: int = 32) -> tuple[int, int]:
    """Longest 4-aligned run of pointers that all lead to plausible LZSS block headers."""
    best = (0, 0)
    pos = 0
    while pos < len(rom) - 4:
        run = 0
        while pos + 4 * run + 4 <= len(rom) and plausible_block(
            rom, struct.unpack_from("<I", rom, pos + 4 * run)[0]
        ):
            run += 1
        if run > best[1]:
            best = (pos, run)
        pos += 4 * run + 4 if run else 4
    if best[1] < min_run:
        raise ValueError("no script block pointer table found")
    return best


# ---- script text ----
SCRIPT_START = 0x200  # after the 256 u16 event offsets
OP_TALK, OP_NARRATE, OP_CHOICE = 0x00, 0x17, 0x33
CHOICE_HEADER = 8
MAX_UNITS = 2000
MAX_CHOICES = 6
C_WAIT = 0x07  # wait for a button
C_BOX = 0x08  # clear the box
C_LINE = 0x09
C_AUTO = 0x0A  # advance after <param> frames
C_FACE_D = 0x0D  # portrait
C_FACE_E = 0x0E  # portrait (second set)
C_END = 0x0F
CONTROLS = frozenset({0, C_WAIT, C_BOX, C_LINE, C_AUTO, C_FACE_D, C_FACE_E, C_END})
WIDE = 0x10
WIDE_END = 0x20  # two-byte glyphs: high byte 0x10-0x1F
GLYPHS = frozenset(range(0x00, 0x20)) | frozenset(range(0xA2, 0xDF))
ANY_GLYPH = frozenset(range(0x100))  # --jp: kana may sit in 0x20-0xA1 (unverified)
END_UNIT = C_END << 8


def units(b: bytes, pos: int, n: int) -> list[int]:
    return [b[pos + 2 * k] | b[pos + 2 * k + 1] << 8 for k in range(n)]


def valid(us: list[int], jp: bool = False) -> bool:
    if not us or us[-1] != END_UNIT:
        return False
    for u in us:
        hi, lo = u >> 8, u & 0xFF
        if hi == 0 and lo not in (ANY_GLYPH if jp else GLYPHS):
            return False
        if hi not in CONTROLS and not (jp and WIDE <= hi < WIDE_END):
            return False
    # Exact unit count plus the 0F00 terminator is what rules out bytecode; silent
    # boxes ("...", a lone space with an auto-advance) are real messages.
    return any(u >> 8 == 0 or u >> 8 & WIDE for u in us[:-1])


def message_at(b: bytes, p: int, jp: bool = False) -> tuple[int, list[int]] | None:
    """(header length, units) when a text op starts at p, else None."""
    op = b[p]
    if op in (OP_TALK, OP_NARRATE):
        n = struct.unpack_from("<H", b, p + (2 if op == OP_TALK else 4))[0]
        if 0 < n < MAX_UNITS and p + 6 + 2 * n <= len(b):
            us = units(b, p + 6, n)
            if valid(us, jp):
                return 6, us
    elif op == OP_CHOICE and 0 < b[p + 1] <= MAX_CHOICES:
        us, q = [], p + CHOICE_HEADER
        while q + 1 < len(b) and len(us) < MAX_UNITS:
            us.append(b[q] | b[q + 1] << 8)
            q += 2
            if us[-1] == END_UNIT:
                break
        if valid(us, jp):
            return CHOICE_HEADER, us
    return None


def render(us: list[int]) -> tuple[str, list[str]]:
    out: list[str] = []
    speakers: list[str] = []
    for i, u in enumerate(us):
        hi, lo = u >> 8, u & 0xFF
        nxt = us[i + 1] >> 8 if i + 1 < len(us) else C_END
        if hi == 0:
            out.append(glyph(lo))
        elif hi & WIDE:
            out.append(f"{{W{((hi & ~WIDE) << 8) | lo:04X}}}")
        elif hi == C_LINE:
            out.append("\n")
        elif hi == C_BOX:
            out.append("\n\n")
        elif hi == C_WAIT:
            if nxt not in (C_BOX, C_END):
                out.append("[wait]")
        elif hi == C_END:
            break
        elif hi == C_AUTO:
            out.append(f"[auto {lo}]")
        elif hi in (C_FACE_D, C_FACE_E):
            tag = f"{'D' if hi == C_FACE_D else 'E'}{lo:02X}"
            if "".join(out).strip():
                out.append(f"[{tag}] ")
            speakers.append(tag)
        else:
            out.append(f"[C{hi:X}:{lo:02X}]")
    return "".join(out), speakers


def script_messages(
    rom: bytes, table: int, count: int, jp: bool = False
) -> list[Message]:
    ptrs = [struct.unpack_from("<I", rom, table + 4 * i)[0] for i in range(count)]
    maps: dict[int, list[int]] = {}
    for i, p in enumerate(ptrs):
        maps.setdefault(p - ROM_BASE, []).append(i)
    msgs: list[Message] = []
    for off in sorted(maps):
        b = decompress(rom, off)
        ids = maps[off]
        label = f"maps {ids[0]}" if len(ids) == 1 else f"maps {ids[0]}+{len(ids) - 1}"
        source = f"block 0x{off:X} ({label})"
        p = SCRIPT_START
        while p < len(b) - 6:
            hit = message_at(b, p, jp)
            if hit is None:
                p += 1
                continue
            hdr, us = hit
            text, speakers = render(us)
            if b[p] == OP_CHOICE:
                speakers = ["choice", *speakers]
            msgs.append(Message(source, p, text, speakers))
            p += hdr + 2 * len(us)
    return msgs


def run_script(
    rom_path: Path, out: Path, table: int | None, count: int | None, jp: bool = False
) -> int:
    rom = rom_path.read_bytes()
    if table is None:
        table, found = find_table(rom)
        count = count or found
        LOG.info("pointer table at 0x%X, %d entries", table, count)
    msgs = script_messages(rom, table, count or 0, jp)
    write_dump(
        out,
        f"Lunar Legend (GBA) -- event script dialogue, {rom_path.name}",
        "gba_legend.py script",
        msgs,
    )
    LOG.info("wrote %d messages to %s", len(msgs), out)
    return len(msgs)


def run_strings(rom_path: Path, out: Path, start: int, end: int) -> int:
    d = rom_path.read_bytes()
    msgs = []
    pos = start
    while pos < end:
        stop = d.find(bytes([END]), pos, end)
        if stop < 0:
            break
        text = decode(d[pos:stop])
        if (
            stop - pos >= MIN_LEN
            and "{" not in text
            and any(c.isupper() for c in text)
            and looks_like_text(text)
        ):
            msgs.append(Message(rom_path.name, pos, text))
        pos = stop + 1
    write_dump(
        out,
        "Lunar Legend (GBA, USA) -- uncompressed strings (menus, items, names)",
        "gba_legend.py strings",
        msgs,
    )
    LOG.info("wrote %d strings to %s", len(msgs), out)
    return len(msgs)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    num = lambda s: int(s, 0)  # noqa: E731
    sc = sub.add_parser("script", help="event script dialogue (LZSS blocks)")
    sc.add_argument("rom", type=Path)
    sc.add_argument("out", type=Path)
    sc.add_argument("--table", type=num, help="pointer table offset (default: search)")
    sc.add_argument("--count", type=num, help="pointer count (default: the run found)")
    sc.add_argument(
        "--jp",
        action="store_true",
        help="accept any glyph byte (Japanese ROM, untested)",
    )
    st = sub.add_parser("strings", help="uncompressed FF-terminated strings")
    st.add_argument("rom", type=Path)
    st.add_argument("out", type=Path)
    st.add_argument("--start", type=num, default=0x92000)
    st.add_argument("--end", type=num, default=0x98000)
    a = ap.parse_args()
    if a.cmd == "script":
        run_script(a.rom, a.out, a.table, a.count, a.jp)
    else:
        run_strings(a.rom, a.out, a.start, a.end)
    return 0


if __name__ == "__main__":
    sys.exit(main())
