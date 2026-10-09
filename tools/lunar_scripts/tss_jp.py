"""Japanese Lunar: The Silver Star (Mega CD) dialogue dump.

    python -I tss_jp.py FILES_DIR OUT.txt [--table tss_jp_table.txt]

No Japanese ripper exists for this game, so this one is written from Supper's notes
(wdtools/notes/lunartss_notes) and the disc:

- Font: 1bpp 16x16, 0x400 glyphs at 0x1D010 of TOMI.DAT (TOMISUB.BIN on the US disc).
  `tss_jp_table.txt` maps glyph index to Unicode. It was read off that font (see
  `jpfont.py`): kana and symbols share Eternal Blue's layout, the kanji from 0xD9 to
  0x3C5 follow JIS X 0208 order, and 0x3C5-0x3DD are a hand-ordered tail.
- Text: a byte >= 0x20 is glyph (byte - 0x20). A byte 0x10-0x1F starts a two-byte
  kanji: glyph = (b0 << 8 | b1) - 0xF20. 00 ends the string, 01 is a line break, 02 a
  box break, 04 xx a portrait, 09 xx an item icon.
- Strings sit between the 68000 routines of each map's first block (block pointers at
  0 and 4), like the US version. The map code points at them with LEA d16(PC),An.

Finding the strings: every LEA d16(PC),An whose target decodes as a Japanese string is
an anchor; from each anchor the following null-terminated strings are read while they
stay valid. Then a fallback scan (as in wdtools scriptrip_tss) picks up runs of valid
strings that no LEA reaches (tables read through pointers), and drops a leading RTS
(4E 75), which also decodes as kana.
"""

from __future__ import annotations

import argparse
import logging
import re
import math
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, write_dump  # noqa: E402

LOG = logging.getLogger("tss_jp")

TITLE = "Lunar: The Silver Star (Mega CD, Japan)"
MAP_GLOB = "C*.MAP"
DEFAULT_TABLE = Path(__file__).resolve().parent / "tss_jp_table.txt"

END, NEWLINE, BOX, PORTRAIT, ITEM = 0x00, 0x01, 0x02, 0x04, 0x09
KANJI_FIRST, KANJI_LAST = 0x10, 0x1F
KANJI_BIAS = 0xF20
GLYPH_BIAS = 0x20
FONT_GLYPHS = 0x400
RTS = b"\x4e\x75"
# 68000 words that decode as kana but never start a glyph in real text: RTS, and
# MOVEM.L to and from the stack (a routine's first and last instruction).
CODE_WORDS = frozenset({0x4E75, 0x48E7, 0x4CDF})
LEA_PC_RE = re.compile(rb"(?s)[\x41\x43\x45\x47\x49\x4b\x4d]\xfa(..)")

# A real string has at least this many glyphs and is mostly kana/kanji.
MIN_GLYPHS = 2
MIN_JP_RATIO = 0.6
# Fallback scan: a run of unreferenced strings must have this many strings, with this
# many glyphs in all, to count.
MIN_RUN_STRINGS = 2
MIN_RUN_GLYPHS = 12
# Text-model thresholds (mean log-likelihood ratio per glyph). Anchored dialogue has a
# median near 0.5; code decoded as text scores below -1.
SMOOTH = 0.5
MIN_LLR = -0.6
SHORT_GLYPHS = 4
SHORT_LLR = 0.0
TAG_OR_SPACE_RE = re.compile(r"\[[^\]]*\]|\s")  # \s includes the ideographic space
WIDE_ALNUM_RE = re.compile(r"[０-９Ａ-Ｚ]")
JP_RE = re.compile(r"[ぁ-ヿ一-鿿々ー]")


def load_table(path: Path) -> dict[int, str]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            table[int(k, 16)] = v
    return table


def glyph_text(index: int, table: dict[int, str]) -> str | None:
    """A glyph's text; {xxx} for a font glyph the table lacks; None past the font."""
    if index in table:
        return table[index]
    if 0 <= index < FONT_GLYPHS:
        return f"{{{index:X}}}"
    return None


class Decoded:
    __slots__ = ("text", "speakers", "length", "glyphs")

    def __init__(
        self, text: str, speakers: list[str], length: int, glyphs: int
    ) -> None:
        self.text, self.speakers, self.length, self.glyphs = (
            text,
            speakers,
            length,
            glyphs,
        )


def decode(data: bytes, pos: int, end: int, table: dict[int, str]) -> Decoded | None:
    """Decode one null-terminated string at pos, or None if the bytes are not text."""
    out: list[str] = []
    speakers: list[str] = []
    glyphs = 0
    p = pos
    while p < end:
        b = data[p]
        if p + 1 < end and (b << 8 | data[p + 1]) in CODE_WORDS:
            return None
        if b == END:
            if glyphs == 0:
                return None
            return Decoded("".join(out), speakers, p + 1 - pos, glyphs)
        if b == NEWLINE:
            out.append("\n")
            p += 1
        elif b == BOX:
            out.append("\n\n")
            p += 1
        elif b == PORTRAIT and p + 1 < end:
            sp = f"L{data[p + 1]}"
            speakers.append(sp)
            # a portrait at the very start is the message's speaker, not an inline change
            if out:
                out.append(f"[{sp}] ")
            p += 2
        elif b == ITEM and p + 1 < end:
            out.append(f"[9][{data[p + 1]:x}]")
            p += 2
        elif KANJI_FIRST <= b <= KANJI_LAST and p + 1 < end:
            ch = glyph_text((b << 8 | data[p + 1]) - KANJI_BIAS, table)
            if ch is None:
                return None
            out.append(ch)
            glyphs += 1
            p += 2
        elif b >= GLYPH_BIAS:
            ch = glyph_text(b - GLYPH_BIAS, table)
            if ch is None:
                return None
            out.append(ch)
            glyphs += 1
            p += 1
        else:
            return None
    return None


def is_text(d: Decoded | None) -> bool:
    if d is None or d.glyphs < MIN_GLYPHS:
        return False
    bare = TAG_OR_SPACE_RE.sub("", d.text)
    return bool(bare) and len(JP_RE.findall(bare)) / len(bare) >= MIN_JP_RATIO


def glyph_chars(text: str) -> list[str]:
    return list(TAG_OR_SPACE_RE.sub("", text))


class TextModel:
    """Unigram log-likelihood ratio: dialogue glyphs vs glyphs decoded from map code.

    68000 code also decodes as kana (most bytes are glyphs), so a valid-looking string
    is kept only if its glyphs are, on average, likelier under the dialogue model. The
    dialogue model is trained on the LEA-anchored strings of all maps, the background on
    every byte offset of every map's first block."""

    def __init__(self) -> None:
        self.text: Counter[str] = Counter()
        self.code: Counter[str] = Counter()

    def train(self, data: bytes, table: dict[int, str]) -> None:
        start, end = block(data)
        for p in range(start, end):
            ch = glyph_at(data, p, end, table)
            if ch:
                self.code[ch] += 1
        for a in anchors(data, start, end):
            d = decode(data, a, end, table)
            if is_text(d):
                self.text.update(glyph_chars(d.text))

    def finish(self, vocab: int) -> None:
        nt, nc = sum(self.text.values()), sum(self.code.values())
        self.lt = math.log(nt + SMOOTH * vocab)
        self.lc = math.log(nc + SMOOTH * vocab)

    def score(self, text: str) -> float:
        # full-width digits and letters (floors, prices) are left out: rare in dialogue
        # but legitimate, and code is caught by its kana anyway
        chars = [c for c in glyph_chars(text) if not WIDE_ALNUM_RE.match(c)]
        total = sum(
            math.log(self.text[c] + SMOOTH)
            - self.lt
            - math.log(self.code[c] + SMOOTH)
            + self.lc
            for c in chars
        )
        return total / max(len(chars), 1)

    def accept(self, d: Decoded | None) -> bool:
        if not is_text(d):
            return False
        floor = SHORT_LLR if d.glyphs < SHORT_GLYPHS else MIN_LLR
        return self.score(d.text) >= floor


def block(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[:8])


def glyph_at(data: bytes, p: int, end: int, table: dict[int, str]) -> str | None:
    b = data[p]
    if KANJI_FIRST <= b <= KANJI_LAST and p + 1 < end:
        return table.get((b << 8 | data[p + 1]) - KANJI_BIAS)
    if b >= GLYPH_BIAS:
        return table.get(b - GLYPH_BIAS)
    return None


def anchors(data: bytes, start: int, end: int) -> list[int]:
    targets = {
        m.start() + 2 + struct.unpack(">h", m.group(1))[0]
        for m in LEA_PC_RE.finditer(data, start, end)
    }
    return sorted(t for t in targets if start <= t < end)


def run_from(
    data: bytes,
    pos: int,
    end: int,
    table: dict[int, str],
    covered: bytearray,
    model: TextModel,
) -> list[tuple[int, Decoded]]:
    """Read consecutive strings from pos while they read as dialogue and are not taken."""
    run = []
    while pos < end:
        d = decode(data, pos, end, table)
        if not model.accept(d) or any(covered[pos : pos + d.length]):
            break
        run.append((pos, d))
        pos += d.length
    return run


def rip(
    data: bytes, table: dict[int, str], model: TextModel
) -> tuple[list[tuple[int, Decoded]], int]:
    """Return the strings of one map and how many came from LEA anchors."""
    start, end = block(data)
    found: dict[int, Decoded] = {}
    covered = bytearray(len(data))

    def take(run: list[tuple[int, Decoded]]) -> None:
        for p, d in run:
            found[p] = d
            covered[p : p + d.length] = bytes([1]) * d.length

    for a in anchors(data, start, end):
        if not covered[a]:
            take(run_from(data, a, end, table, covered, model))
    # Place names and some system lines follow a routine's RTS directly.
    rts = data.find(RTS, start, end)
    while rts >= 0:
        after = rts + len(RTS)
        if after < end and not covered[after]:
            take(run_from(data, after, end, table, covered, model))
        rts = data.find(RTS, after, end)
    by_anchor = len(found)

    pos = start
    while pos < end:
        if covered[pos]:
            pos += 1
            continue
        run = run_from(data, pos, end, table, covered, model)
        if (
            len(run) >= MIN_RUN_STRINGS
            and sum(d.glyphs for _, d in run) >= MIN_RUN_GLYPHS
        ):
            first_pos, first = run[0]
            rts = data.find(RTS, first_pos, first_pos + first.length)
            if rts >= 0:
                # code ran into the strings: restart after the RTS
                pos = rts + len(RTS)
                continue
            take(run)
            pos = run[-1][0] + run[-1][1].length
        else:
            pos += 1
    return sorted(found.items()), by_anchor


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("files", type=Path, help="disc root extracted by discfs.py")
    ap.add_argument("out", type=Path)
    ap.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    a = ap.parse_args()
    table = load_table(a.table)
    maps = sorted(a.files.glob(MAP_GLOB))
    model = TextModel()
    for f in maps:
        model.train(f.read_bytes(), table)
    model.finish(len(set(table.values())))
    messages: list[Message] = []
    for f in maps:
        got, n_anchor = rip(f.read_bytes(), table, model)
        for p, d in got:
            messages.append(Message(f.name, p, d.text, d.speakers))
        LOG.info(
            "%s: %d messages (%d from LEA, %d from scan)",
            f.name,
            len(got),
            n_anchor,
            len(got) - n_anchor,
        )
    write_dump(a.out, TITLE, f"tss_jp.py with {a.table.name}", messages)
    LOG.info("wrote %d messages to %s", len(messages), a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
