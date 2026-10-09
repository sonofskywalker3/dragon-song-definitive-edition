"""Lunar: Silver Star Harmony (PSP) dialogue dump.

    python -I harmony.py ScriptPack.dat WORKDIR OUT.txt

ScriptPack.dat ("FPAC"): u32 at 4, then 8-byte entries (u32 size, u16 1, u16 sector)
from 0x8 until a zero size; member data at 0x1000 + sector*0x800, each a gzip stream
named TEXTnnn.dat. Each TEXTnnn.dat ("LTCV"): u32 size, u32 block count, u32 data
start, then (u16 id, u16 size, u32 offset) per block. Blocks are event scripts in
16-bit little-endian words; dialogue is UTF-16LE text inside them:

    [0067 <char id>] 0002 [042E|044E <portrait id>] [042A <expression>] text...
    0401 newline, 0414 wait for button, 0419 clear box, 0417 next speaker
    (another 0067 header follows), 0416 end of text.

Character ids match the PS1 portrait ids (0x1A Luna, 0x38/0x39 Nall, ...).
Text outside a 0067 header (system lines) is caught by a second pass that keeps any
run of text words ending in a 04xx text code. Japanese UMDs should decode the same
way (UTF-16 covers kana and kanji); untested.
"""

from __future__ import annotations

import argparse
import logging
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, looks_like_text, write_dump  # noqa: E402

LOG = logging.getLogger("harmony")

FPAC_MAGIC = b"FPAC"
LTCV_MAGIC = b"LTCV"
FPAC_DATA = 0x1000
FPAC_SECTOR = 0x800
GZIP_AUTO = 31
MSG_OP = 0x0067
MSG_MARK = 0x0002
PORTRAIT_L, PORTRAIT_R = 0x042E, 0x044E
EXPRESSION = 0x042A
NEWLINE, WAIT, CLEAR, END, NEXT = 0x0401, 0x0414, 0x0419, 0x0416, 0x0417
CODE_LO, CODE_HI = 0x0400, 0x0500
SPACE = 0x20
NOT_CHAR = 0xFFFF
MIN_RUN = 6
HEADER_LOOKAHEAD = 16


def unpack_pack(pack: Path, outdir: Path) -> list[Path]:
    d = pack.read_bytes()
    if d[:4] != FPAC_MAGIC:
        raise ValueError("not an FPAC file")
    outdir.mkdir(parents=True, exist_ok=True)
    out = []
    pos = 8
    while pos + 8 <= len(d):
        size, _flag, sector = struct.unpack_from("<IHH", d, pos)
        if size == 0:
            break
        blob = d[
            FPAC_DATA + sector * FPAC_SECTOR : FPAC_DATA + sector * FPAC_SECTOR + size
        ]
        name = blob[10 : blob.index(b"\0", 10)].decode("ascii")
        dst = outdir / name
        dst.write_bytes(zlib.decompress(blob, GZIP_AUTO))
        out.append(dst)
        pos += 8
    return out


def is_char(w: int) -> bool:
    return w >= SPACE and w != NOT_CHAR and not (CODE_LO <= w < CODE_HI)


def words_of(d: bytes, a: int, b: int) -> list[int]:
    return list(struct.unpack_from(f"<{(b - a) // 2}H", d, a))


def parse_header(w: list[int], i: int) -> tuple[int, str | None] | None:
    """At a 0002 text header return (index of first text word, speaker tag or None).

    Forms seen: [0067 id] 0002 042E|044E pid [042A expr] text, and 0002 042A expr text
    (same speaker continues)."""
    if i + 2 >= len(w) or w[i] != MSG_MARK:
        return None
    if w[i + 1] not in (PORTRAIT_L, PORTRAIT_R, EXPRESSION) and not plain_start(
        w, i + 1
    ):
        return None
    j = i + 1
    sp = None
    if w[j] in (PORTRAIT_L, PORTRAIT_R):
        side = "L" if w[j] == PORTRAIT_L else "R"
        sp = f"{side}{w[j + 1]:02X}"
        j += 2
    if j + 1 < len(w) and w[j] == EXPRESSION:
        j += 2
    if sp is None and i >= 2 and w[i - 2] == MSG_OP:  # "0067 id 0002 text"
        sp = f"C{w[i - 1]:02X}"
    if j >= len(w) or not is_char(w[j]):
        return None
    return j, sp


def plain_start(w: list[int], j: int) -> bool:
    """0002 followed straight by text (NPC lines): demand MIN_RUN text words first."""
    run = w[j : j + MIN_RUN]
    return len(run) == MIN_RUN and all(is_char(c) for c in run)


def find_header(w: list[int], i: int) -> int | None:
    for k in range(i, min(i + HEADER_LOOKAHEAD, len(w))):
        if parse_header(w, k) is not None:
            return k
        if w[k] == END:
            return None
    return None


def read_message(w: list[int], i: int) -> tuple[int, str, list[str]] | None:
    hdr = parse_header(w, i)
    if hdr is None:
        return None
    j, sp = hdr
    speakers = [sp] if sp else []
    text = ""
    while j < len(w):
        c = w[j]
        if c == END:
            return j + 1, text, speakers
        if c == NEXT:
            k = find_header(w, j + 1)
            if k is None:
                return j + 1, text, speakers
            j, sp = parse_header(w, k)  # type: ignore[misc]
            text = text.rstrip("\n") + "\n\n"
            if sp:
                speakers.append(sp)
                text += f"[{sp}] "
            continue
        if c == NEWLINE:
            text += "\n"
        elif c == WAIT:
            text += "\n\n"
        elif c in (PORTRAIT_L, PORTRAIT_R):
            j += 1  # portrait clear/change carries one argument
        elif c == CLEAR:
            pass
        elif is_char(c):
            text += chr(c)
        elif CODE_LO <= c < CODE_HI:
            if j + 1 < len(w) and w[j + 1] < SPACE:
                j += 1  # in-text code with one argument (e.g. 0411 xx); not shown
        else:
            return j, text, speakers
        j += 1
    return None


def loose_runs(w: list[int], covered: list[bool]) -> list[tuple[int, str]]:
    """Text runs not under a 0067 header: >= MIN_RUN text words ended by a 04xx code."""
    out = []
    i = 0
    while i < len(w):
        if covered[i] or not is_char(w[i]):
            i += 1
            continue
        j = i
        text = ""
        while (
            j < len(w)
            and not covered[j]
            and (is_char(w[j]) or w[j] in (NEWLINE, WAIT, CLEAR))
        ):
            text += (
                chr(w[j])
                if is_char(w[j])
                else ("\n" if w[j] == NEWLINE else "\n\n" if w[j] == WAIT else "")
            )
            j += 1
        if (
            j < len(w)
            and CODE_LO <= w[j] < CODE_HI
            and j - i >= MIN_RUN
            and " " in text
        ):
            out.append((i, text))
        i = j + 1
    return out


def scan_ltcv(path: Path) -> list[Message]:
    d = path.read_bytes()
    if d[:4] != LTCV_MAGIC:
        LOG.warning("%s: not LTCV", path.name)
        return []
    count, base = struct.unpack_from("<II", d, 8)
    msgs: list[Message] = []
    for n in range(count):
        _bid, size, off = struct.unpack_from("<HHI", d, 0x10 + 8 * n)
        start = base + off
        w = words_of(d, start, start + size - (size & 1))
        covered = [False] * len(w)
        i = 0
        while i < len(w):
            got = read_message(w, i) if w[i] == MSG_MARK else None
            if got is None:
                i += 1
                continue
            end, text, speakers = got
            for k in range(i, end):
                covered[k] = True
            msgs.append(Message(path.name, start + 2 * i, text, speakers))
            i = end
        for k, text in loose_runs(w, covered):
            msgs.append(Message(path.name, start + 2 * k, text, []))
    msgs = [m for m in msgs if looks_like_text(m.text)]
    msgs.sort(key=lambda m: m.offset)
    return msgs


def run(pack: Path, work: Path, out: Path) -> int:
    files = unpack_pack(pack, work / "text")
    messages: list[Message] = []
    for f in sorted(files):
        got = scan_ltcv(f)
        LOG.info("%s: %d messages", f.name, len(got))
        messages.extend(got)
    write_dump(
        out,
        "Lunar: Silver Star Harmony (PSP, USA)",
        "harmony.py (ScriptPack/LTCV UTF-16 reader)",
        messages,
    )
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", type=Path)
    ap.add_argument("work", type=Path)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    run(a.pack, a.work, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
