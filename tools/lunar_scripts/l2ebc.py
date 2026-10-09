"""Lunar 2: Eternal Blue Complete (PS1, USA) dialogue dump.

    python -I l2ebc.py DATA.IDX DATA.PAK DATA.UPD WORKDIR OUT.txt [--prefix SCN]

Unpacks the DATA archive (wdtools l2eb_data, ported) and scans every file under the
chosen folder prefix for text boxes, using the string reader Supper left commented out
in wdtools l2eb_txt.cpp (readL2ebString), ported here unchanged in its rules:

  halfwords, little endian; Bxxx opens a box (xxx = portrait), Axxx is a special box,
  06xx enters text mode; in text mode each byte is a character (low 7 bits + 0x1F),
  a set high bit or FF leaves text mode; 10xx = line break, 20xx = wait/new box,
  00xx = end. A string needs 4+ printed characters.

All three US discs carry an identical DATA.PAK/IDX/UPD, so disc 1 is enough.
"""

from __future__ import annotations

import argparse
import logging
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, looks_like_text, write_dump  # noqa: E402

LOG = logging.getLogger("l2ebc")

SECTOR = 0x800
UPD_NAMES_PTR = 0x10
IDX_ENTRY = 5
TEXT_ON = 0x06
END_MARK = 0xFF
HIGH = 0x80
LOW7 = 0x7F
CHAR_BIAS = 0x1F
CHAR_LIMIT = 0x60
MIN_CHARS = 4
BOX_TYPES = (0xA0, 0xB0)
SIMPLE_CODES = {
    0x01: "\n\n",
    0x10: "\n",
    0x20: "\n\n",
    0x30: "",
    0x40: "[4000]\n",
    0x50: "[5000]\n",
    0x60: "[6000]\n",
    0xD0: "[D000]\n",
}
NIB_END, NIB_SPECIAL, NIB_PORTRAIT = 0x0, 0xA, 0xB


def unpack(idx: Path, pak: Path, upd: Path, outdir: Path) -> list[tuple[str, bytes]]:
    names_blob = upd.read_bytes()
    names = names_blob[struct.unpack_from("<I", names_blob, UPD_NAMES_PTR)[0] :].split(
        b"\0"
    )
    idx_b = idx.read_bytes()
    out = []
    with open(pak, "rb") as fh:
        for n in range(len(idx_b) // IDX_ENTRY):
            e = idx_b[n * IDX_ENTRY : (n + 1) * IDX_ENTRY]
            sector = int.from_bytes(e[:3], "big")
            count = int.from_bytes(e[3:5], "big")
            name = (
                names[n].decode("ascii", "replace").replace("\\", "/")
                if n < len(names)
                else str(n)
            )
            fh.seek(sector * SECTOR)
            data = fh.read(count * SECTOR)
            dst = outdir / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            out.append((name, data))
    return out


class Reader:
    def __init__(self) -> None:
        self.text = ""
        self.textmode = False

    def put(self, c: int) -> bool:
        low = c & LOW7
        if c == END_MARK:
            self.textmode = False
            return True
        if low == 0 or low >= CHAR_LIMIT:
            return False
        self.text += chr(low + CHAR_BIAS)
        if c & HIGH:
            self.textmode = False
        return True


def read_string(src: bytes, pos: int) -> tuple[int, str, list[str]] | None:
    first = src[pos + 1]
    if (first & 0xF0) not in BOX_TYPES and first != TEXT_ON:
        return None
    r = Reader()
    speakers: list[str] = []
    printed = 0
    end = len(src) & ~1
    for i in range(pos, end, 2):
        nxt = src[i] | (src[i + 1] << 8)
        if r.textmode:
            if not r.put(src[i + 1]) or not r.put(src[i]):
                return None
            printed += 2
            continue
        cmd = nxt >> 8
        if cmd == TEXT_ON:
            r.textmode = True
            if not r.put(nxt & 0xFF):
                return None
        elif cmd in SIMPLE_CODES:
            r.text += SIMPLE_CODES[cmd]
        else:
            nib = nxt >> 12
            if nib == NIB_END:
                return (i, r.text, speakers) if printed >= MIN_CHARS else None
            if nib == NIB_SPECIAL:
                r.text += f"[A{nxt & 0xFFF}]\n"
            elif nib == NIB_PORTRAIT:
                sp = f"P{nxt & 0xFFF}"
                if r.text.strip():
                    r.text += f"[{sp}] "
                speakers.append(sp)
            else:
                return None
    return None


def scan(name: str, data: bytes) -> list[Message]:
    msgs = []
    pos = 0
    end = len(data) & ~1
    while pos < end - 1:
        got = read_string(data, pos)
        if got is None:
            pos += 2
            continue
        stop, text, speakers = got
        if looks_like_text(text):
            msgs.append(Message(name, pos, text, speakers))
        pos = stop
    return msgs


def run(idx: Path, pak: Path, upd: Path, work: Path, out: Path, prefix: str) -> int:
    files = unpack(idx, pak, upd, work / "data")
    messages: list[Message] = []
    for name, data in files:
        if not name.upper().startswith(prefix.upper()):
            continue
        got = scan(name, data)
        if got:
            LOG.info("%s: %d messages", name, len(got))
        messages.extend(got)
    write_dump(
        out,
        "Lunar 2: Eternal Blue Complete (PS1, USA)",
        "l2ebc.py (port of wdtools l2eb_txt readL2ebString)",
        messages,
    )
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    for a in ("idx", "pak", "upd", "work", "out"):
        ap.add_argument(a, type=Path)
    ap.add_argument("--prefix", default="SCN/")
    a = ap.parse_args()
    run(a.idx, a.pak, a.upd, a.work, a.out, a.prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
