"""Lunar: Silver Star Story Complete (PS1) dialogue dump, via MrConan1/lsb.

    python -I sssc.py LUNADATA.FIL LSB_EXE LSB_DATA_DIR WORKDIR OUT.txt [--ienc 4] [--title T]

LUNADATA.FIL : the archive from the disc (identical on both US discs).
LSB_EXE      : lsb built with lsb_file_offset.patch (adds "(file-offset X)" to each
               run-commands/options node so the dump can cite offsets).
LSB_DATA_DIR : folder holding lsb's lsss_txtcmpstr_us.bin, font_table.txt and bpe.table
               (lsb loads them from the current directory).
--ienc       : lsb text mode. 4 = PS1 English (compressed 1-byte). For the Japanese PS1
               disc try 0 (2-byte, font_table.txt) -- see README. The Saturn discs go
               through sss_saturn.py, which reuses decode_texts().
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, write_dump  # noqa: E402

LOG = logging.getLogger("sssc")

FIL_SECTOR = 0x800
FIL_HEADER = 0x20
FIL_ENTRY = 0x20
TEXT_RE = re.compile(r"TEXT\d+\.DAT$")
# TEXT100.DAT parses as a script but its strings use another encoding (font indices),
# TEXT000/TEXT200 hold no dialogue and lsb rejects them.
SKIP_DEFAULT = ("TEXT100.DAT",)
LSB_TABLES = ("lsss_txtcmpstr_us.bin", "font_table.txt", "bpe.table")
PRINT_RE = re.compile(r"^\s*\(print-line `(.*)`\)\s*$")
CTRL_RE = re.compile(r"^\s*\(control-code ([0-9A-F]+)\)")
PORTRAIT_RE = re.compile(r"^\s*\(show-portrait-(left|right) ([0-9A-F]+)\)")
OFFSET_RE = re.compile(r"^\s*\(file-offset ([0-9A-F]+)\)")
NODE_RE = re.compile(r"^\((run-commands|options) id=")
NEWLINE = "FF02"
BOX_END = "FF00"
OPT_START = "(opt1)"
OPT2_START = "(opt2)"
CLEAR_PORTRAIT = 0

# Optional portrait id -> name table. Left empty: portraits are expression variants and a
# shown portrait is not always the speaker, so the dump cites raw ids (see README).
PORTRAITS: dict[int, str] = {}


def unpack_fil(fil: Path, outdir: Path) -> list[Path]:
    data = fil.read_bytes()
    count = struct.unpack_from("<I", data, 0x14)[0]
    out = []
    outdir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        base = FIL_HEADER + i * FIL_ENTRY
        name = data[base : base + 16].split(b"\0")[0].decode("ascii")
        sector, size = struct.unpack_from("<II", data, base + 20)
        dst = outdir / name
        dst.write_bytes(data[sector * FIL_SECTOR : sector * FIL_SECTOR + size])
        out.append(dst)
    return out


def speaker(side: str, pid: int) -> str:
    tag = f"{side[0].upper()}{pid:02X}"
    name = PORTRAITS.get(pid)
    return f"{tag} {name}" if name else tag


def parse_lsb(script: Path, source: str, encoding: str = "latin-1") -> list[Message]:
    """Read lsb's script output. English PS1 text is latin-1; the 2-byte (JP) modes write UTF-8."""
    msgs: list[Message] = []
    cur: Message | None = None
    for raw in script.read_text(encoding=encoding).splitlines():
        if NODE_RE.match(raw):
            cur = Message(source, 0, "")
            if raw.startswith("(options"):
                cur.speakers.append("CHOICE")
            continue
        if cur is None:
            continue
        if raw.startswith(")"):
            if cur.text.strip():
                msgs.append(cur)
            cur = None
            continue
        if m := OFFSET_RE.match(raw):
            cur.offset = int(m.group(1), 16)
        elif m := PORTRAIT_RE.match(raw):
            pid = int(m.group(2), 16)
            if pid != CLEAR_PORTRAIT:
                sp = speaker(m.group(1), pid)
                cur.speakers.append(sp)
                if cur.text:
                    cur.text += f"[{sp}] "
        elif m := PRINT_RE.match(raw):
            cur.text += m.group(1)
        elif m := CTRL_RE.match(raw):
            code = m.group(1)
            if code == NEWLINE:
                cur.text += "\n"
            elif code == BOX_END:
                cur.text += "\n\n"
        elif raw.strip() == OPT2_START:
            cur.text += "\n/ "
    return msgs


def decode_texts(
    texts: list[Path],
    lsb: Path,
    lsb_data: Path,
    run_dir: Path,
    ienc: int,
    extra: tuple[str, ...] = (),
    encoding: str = "latin-1",
) -> list[Message]:
    """Run lsb decode on each TEXTnnn.DAT and parse its output into messages."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for t in LSB_TABLES:
        shutil.copy(lsb_data / t, run_dir / t)
    messages: list[Message] = []
    for t in texts:
        stem = t.stem
        res = subprocess.run(
            [str(lsb.resolve()), "decode", str(t.resolve()), stem, str(ienc), *extra],
            cwd=run_dir,
            capture_output=True,
            text=True,
            errors="replace",
        )
        script = run_dir / stem
        if res.returncode != 0 or "FAILED" in res.stdout or not script.exists():
            LOG.warning(
                "%s: lsb could not parse (%s)",
                t.name,
                res.stdout.strip().splitlines()[-1:],
            )
            continue
        got = parse_lsb(script, t.name, encoding)
        LOG.info("%s: %d messages", t.name, len(got))
        messages.extend(got)
    return messages


def run(
    fil: Path,
    lsb: Path,
    lsb_data: Path,
    work: Path,
    out: Path,
    ienc: int,
    title: str,
    skip: tuple[str, ...],
) -> int:
    files = unpack_fil(fil, work / "fil")
    texts = sorted(p for p in files if TEXT_RE.search(p.name) and p.name not in skip)
    messages = decode_texts(texts, lsb, lsb_data, work / "lsb", ienc)
    write_dump(
        out,
        title,
        f"lsb decode ienc={ienc} (MrConan1/lsb + file-offset patch)",
        messages,
    )
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("fil", type=Path)
    ap.add_argument("lsb", type=Path)
    ap.add_argument("lsb_data", type=Path)
    ap.add_argument("work", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--ienc", type=int, default=4)
    ap.add_argument("--skip", nargs="*", default=list(SKIP_DEFAULT))
    ap.add_argument("--title", default="Lunar: Silver Star Story Complete (PS1, USA)")
    a = ap.parse_args()
    run(a.fil, a.lsb, a.lsb_data, a.work, a.out, a.ienc, a.title, tuple(a.skip))
    return 0


if __name__ == "__main__":
    sys.exit(main())
