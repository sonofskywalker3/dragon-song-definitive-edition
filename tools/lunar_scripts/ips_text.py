"""IPS patch reader and Lunar: Walking School (Game Gear) English text dump from the patch alone.

    python -I ips_text.py records PATCH.ips            # every record: offset, size, RLE
    python -I ips_text.py regions PATCH.ips            # contiguous records merged
    python -I ips_text.py font PATCH.ips [START END]   # draw the 1bpp 8x8 tiles the patch writes
    python -I ips_text.py stats PATCH.ips              # bytes the table does not cover, in text
    python -I ips_text.py dump PATCH.ips OUT.txt       # Walking School script in the shared format

Built for the Aeon Genesis v1.00 patch (2009) of "Lunar - Sanposuru Gakuen (Japan)". The
patch expands the ROM to 1 MB and writes the whole English script into the new half
(0x80000-0xAE9F3), plus a new 8x8 font at 0x48200 and a name list at 0x76B0.

Text table (from the patch's own font: glyph tile = byte - 0x10, tile 0 at 0x48200):
    00 end of string      01 line break        09 xx portrait xx (00 = none)
    0B wait for key, new box                   10 space
    11 !  12 ?  14 note  15 :  16 .  17 ,  18 ..  1A open quote  1B close quote
    07 line break in item and menu windows   19 heart   1E '  1F sweat drop   20-29 0-9   2A-43 A-Z   44-5D a-z
    5E -  5F il  60 li  62 ll  63 close quote  6C ,  6D '
Bytes outside the table print as {XX}. 07, 14, 17, 19, 1A, 1B, 1E and 5E have no tile in the
patch (it keeps the Japanese ROM's glyph there), so they are read from context.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, looks_like_text, write_dump  # noqa: E402

LOG = logging.getLogger("ips_text")

IPS_MAGIC = b"PATCH"
IPS_EOF = b"EOF"
RLE_SIZE = 0

FONT_START = 0x48200
FONT_END = 0x48700
FONT_FIRST_BYTE = 0x10
TILE_BYTES = 8
TILES_PER_ROW = 8

SCRIPT_START = 0x80000
NAMES_START = 0x76B0
SOURCES = ((NAMES_START, "names 0x76B0"), (SCRIPT_START, "script 0x80000"))

END = 0x00
NEWLINE = 0x01
PORTRAIT = 0x09
NEW_BOX = 0x0B
NO_PORTRAIT = 0x00

TABLE: dict[int, str] = {
    NEWLINE: "\n",
    NEW_BOX: "\n\n",
    0x10: " ",
    0x11: "!",
    0x12: "?",
    0x14: "♪",
    0x15: ":",
    0x16: ".",
    0x17: ",",
    0x18: "..",
    0x1A: "“",
    0x1B: "”",
    0x1E: "'",
    0x1F: "[sweat]",
    0x19: "♥",
    0x07: "\n",
    0x5E: "-",
    0x5F: "il",
    0x60: "li",
    0x62: "ll",
    0x63: "”",
    0x6C: ",",
    0x6D: "'",
}
TABLE.update({0x20 + i: str(i) for i in range(10)})
TABLE.update({0x2A + i: chr(ord("A") + i) for i in range(26)})
TABLE.update({0x44 + i: chr(ord("a") + i) for i in range(26)})

MIN_LETTERS = 2
UNKNOWN_PER_LETTER = 4
UNKNOWN_RE = re.compile(r"\{[0-9A-F]{2}\}")
SYMBOL_RE = re.compile(r"[♪♥“”]|\[sweat\]")


@dataclass(frozen=True)
class Record:
    offset: int
    data: bytes
    rle: bool


@dataclass(frozen=True)
class RawString:
    offset: int
    portraits: tuple[str, ...]
    text: str


def read_ips(path: Path) -> list[Record]:
    d = path.read_bytes()
    if not d.startswith(IPS_MAGIC):
        raise ValueError(f"{path} is not an IPS patch")
    recs = []
    p = len(IPS_MAGIC)
    while d[p : p + 3] != IPS_EOF:
        if p + 5 > len(d):
            raise ValueError(f"{path}: truncated record at 0x{p:X}")
        off = int.from_bytes(d[p : p + 3], "big")
        size = int.from_bytes(d[p + 3 : p + 5], "big")
        p += 5
        if size == RLE_SIZE:
            n = int.from_bytes(d[p : p + 2], "big")
            recs.append(Record(off, d[p + 2 : p + 3] * n, True))
            p += 3
        else:
            recs.append(Record(off, d[p : p + size], False))
            p += size
    tail = d[p + 3 :]
    if tail:
        LOG.info("truncation size after EOF: %s", tail.hex())
    return recs


def merge_regions(recs: list[Record]) -> list[tuple[int, bytes]]:
    """Concatenate records that touch; later records overwrite earlier ones."""
    mem: dict[int, int] = {}
    for r in recs:
        for i, x in enumerate(r.data):
            mem[r.offset + i] = x
    regions: list[tuple[int, bytearray]] = []
    for a in sorted(mem):
        if regions and regions[-1][0] + len(regions[-1][1]) == a:
            regions[-1][1].append(mem[a])
        else:
            regions.append((a, bytearray([mem[a]])))
    return [(o, bytes(b)) for o, b in regions]


def region_at(regions: list[tuple[int, bytes]], start: int) -> bytes:
    for o, b in regions:
        if o == start:
            return b
    raise KeyError(f"no patched region starts at 0x{start:X}")


def split_strings(b: bytes, base: int) -> Iterator[RawString]:
    """Decode every END-terminated string; 09 always takes one parameter byte."""
    i = 0
    while i < len(b):
        start = i
        parts: list[str] = []
        portraits: list[str] = []
        while i < len(b) and b[i] != END:
            x = b[i]
            if x == PORTRAIT and i + 1 < len(b):
                val = b[i + 1]
                i += 2
                if val == NO_PORTRAIT:
                    continue
                tag = f"P{val:02X}"
                portraits.append(tag)
                if "".join(parts).strip():
                    parts.append(f"[{tag}] ")
                continue
            parts.append(TABLE.get(x, f"{{{x:02X}}}"))
            i += 1
        yield RawString(base + start, tuple(portraits), "".join(parts))
        i += 1


def is_text(text: str) -> bool:
    """English if it has letters, reads as text, and untabled bytes are rare."""
    letters = sum(c.isalpha() for c in text)
    if letters < MIN_LETTERS:
        return False
    if text.count("{") * UNKNOWN_PER_LETTER > letters:
        return False
    return looks_like_text(SYMBOL_RE.sub("", UNKNOWN_RE.sub("", text)))


def collect(regions: list[tuple[int, bytes]]) -> list[Message]:
    msgs = []
    for start, label in SOURCES:
        for s in split_strings(region_at(regions, start), start):
            if is_text(s.text):
                msgs.append(
                    Message(label, s.offset, s.text.strip("\n"), list(s.portraits))
                )
    return msgs


def cmd_records(recs: list[Record]) -> None:
    for r in recs:
        kind = "RLE" if r.rle else "data"
        print(f"0x{r.offset:06X} {len(r.data):6d} {kind}")
    print(f"{len(recs)} records")


def cmd_regions(regions: list[tuple[int, bytes]]) -> None:
    for o, b in regions:
        print(f"0x{o:06X}-0x{o + len(b) - 1:06X} {len(b):6d} bytes")


def cmd_font(regions: list[tuple[int, bytes]], lo: int, hi: int) -> None:
    mem = {o + i: x for o, b in regions for i, x in enumerate(b)}
    step = TILE_BYTES * TILES_PER_ROW
    for t in range(lo, hi, step):
        tiles = [t + k * TILE_BYTES for k in range(TILES_PER_ROW)]
        print(
            "  ".join(
                f"byte {FONT_FIRST_BYTE + (a - FONT_START) // TILE_BYTES:02X}"
                for a in tiles
            )
        )
        for r in range(TILE_BYTES):
            row = []
            for a in tiles:
                x = mem.get(a + r)
                row.append(
                    "????????"
                    if x is None
                    else "".join("#" if x >> (7 - k) & 1 else "." for k in range(8))
                )
            print("  ".join(row))


def cmd_stats(regions: list[tuple[int, bytes]]) -> None:
    """Count untabled bytes inside strings that otherwise read as English."""
    unknown: Counter[str] = Counter()
    for s in split_strings(region_at(regions, SCRIPT_START), SCRIPT_START):
        if sum(c.isalpha() for c in s.text) >= MIN_LETTERS and looks_like_text(s.text):
            for chunk in s.text.split("{")[1:]:
                unknown[chunk[:2]] += 1
    for k, v in unknown.most_common():
        print(k, v)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("records", "regions", "font", "stats", "dump"))
    ap.add_argument("patch", type=Path)
    ap.add_argument("rest", nargs="*")
    a = ap.parse_args()
    recs = read_ips(a.patch)
    regions = merge_regions(recs)
    if a.cmd == "records":
        cmd_records(recs)
    elif a.cmd == "regions":
        cmd_regions(regions)
    elif a.cmd == "font":
        lo, hi = (int(x, 0) for x in a.rest) if a.rest else (FONT_START, FONT_END)
        cmd_font(regions, lo, hi)
    elif a.cmd == "stats":
        cmd_stats(regions)
    else:
        msgs = collect(regions)
        write_dump(
            Path(a.rest[0]),
            "Lunar: Walking School (Game Gear), Aeon Genesis v1.00 English, from the IPS patch alone",
            "ips_text.py",
            msgs,
        )
        LOG.info("wrote %d messages to %s", len(msgs), a.rest[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
