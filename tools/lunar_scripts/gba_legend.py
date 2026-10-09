"""Lunar Legend (GBA, USA): PARTIAL text dump -- plain FF-terminated strings only.

    python -I gba_legend.py ROM.gba OUT.txt [--start 0x92000 --end 0x98000]

What was found (see lunar_scripts/legend_gba/README.md): names, item and menu text sit
uncompressed around 0x93000-0x97000 in a one-byte table (00 space, 01-1A a-z,
AC-C5 A-Z, A2-AB 0-9, FF end of string; a few punctuation bytes guessed below).
Dialogue is NOT stored this way: no plain, BIOS-LZ77 or BIOS-Huffman block holds the
encoded words, so it is compressed with a scheme still to be traced (emulator
breakpoint on the text renderer). This tool only dumps the uncompressed strings.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, looks_like_text, write_dump  # noqa: E402

LOG = logging.getLogger("gba_legend")

END = 0xFF
SPACE = 0x00
LOWER = range(0x01, 0x1B)
UPPER = range(0xAC, 0xC6)
DIGITS = range(0xA2, 0xAC)
# Guessed from item descriptions ("Luna's favorite fry pan.", "What's so Wow...?").
PUNCT = {0x1B: "'", 0x1F: ",", 0xCE: ".", 0xCF: "?", 0xD4: ".", 0xD0: "-"}
MIN_LEN = 3


def decode(b: bytes) -> str:
    out = []
    for x in b:
        if x == SPACE:
            out.append(" ")
        elif x in LOWER:
            out.append(chr(x - LOWER.start + ord("a")))
        elif x in UPPER:
            out.append(chr(x - UPPER.start + ord("A")))
        elif x in DIGITS:
            out.append(chr(x - DIGITS.start + ord("0")))
        elif x in PUNCT:
            out.append(PUNCT[x])
        else:
            out.append(f"{{{x:02X}}}")
    return "".join(out)


def run(rom: Path, out: Path, start: int, end: int) -> int:
    d = rom.read_bytes()
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
            msgs.append(Message(rom.name, pos, text))
        pos = stop + 1
    write_dump(
        out,
        "Lunar Legend (GBA, USA) -- uncompressed strings only, NOT dialogue",
        "gba_legend.py",
        msgs,
    )
    LOG.info("wrote %d strings to %s", len(msgs), out)
    return len(msgs)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--start", type=lambda s: int(s, 0), default=0x92000)
    ap.add_argument("--end", type=lambda s: int(s, 0), default=0x98000)
    a = ap.parse_args()
    run(a.rom, a.out, a.start, a.end)
    return 0


if __name__ == "__main__":
    sys.exit(main())
