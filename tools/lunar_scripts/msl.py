"""Mahou Gakuen Lunar! (Saturn, 1997): Japanese dialogue via studio-lucia's msl_script_dump.

    python -I msl.py MSL_SCRIPT_DUMP_EXE FILES_DIR WORK_DIR OUT.txt

FILES_DIR holds the S00.FLD-S12.FLD map files (discfs.py extract ... "S??.FLD"). The tool
(https://github.com/studio-lucia/msl_script_tools, built with `cargo build --release`) writes
one CSV per file into WORK_DIR, with the chunk, the chunk-relative offset, and the text
decoded from Shift JIS. This script runs it, adds each chunk's start from the FLD header
so the offsets are file offsets, and writes the shared dump format.

What the tool does to the text: 08 (wait for a key) becomes a blank line, so it reads as
a box break here; 0C (clear the box and keep printing) becomes "\\c", printed here as a
box break; 0D (a printing delay) becomes "\\p", dropped here. 9E42 is the heart. The
format stores no speaker, so every message is "-" (the tool's character and expression
columns are always empty).

FLD header (magicaldata notes): 2048 bytes of (u32 BE start, u32 BE length) pairs, one per
chunk; a chunk with start 0 is empty and the tool skips it.
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, write_dump  # noqa: E402

LOG = logging.getLogger("msl")

HEADER_SIZE = 2048
ENTRY_SIZE = 8
SCRIPT_GLOB = "S??.FLD"
CLEAR_BOX = "\\c"
DELAY = "\\p"
DOS_EOF = "\x1a"
BLANK_RUN_RE = re.compile(r"\n{3,}")


def chunk_starts(fld: Path) -> list[int]:
    head = fld.read_bytes()[:HEADER_SIZE]
    return [
        int.from_bytes(head[i : i + 4], "big")
        for i in range(0, HEADER_SIZE, ENTRY_SIZE)
    ]


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace(DOS_EOF, "")
    text = text.replace(DELAY, "").replace(CLEAR_BOX, "\n\n")
    return BLANK_RUN_RE.sub("\n\n", text).strip()


def run_tool(exe: Path, files: list[Path], work: Path) -> None:
    work.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [str(exe), "--output", str(work), *map(str, files)],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in res.stdout.splitlines():
        LOG.debug("%s", line)
    if res.returncode != 0:
        raise RuntimeError(f"msl_script_dump failed: {res.stdout}{res.stderr}")


def collect(files: list[Path], work: Path) -> list[Message]:
    """Read the CSVs; a string reached from two header entries (same file offset) is kept once."""
    msgs = []
    for fld in files:
        starts = chunk_starts(fld)
        seen: set[int] = set()
        with (work / f"{fld.stem}.csv").open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                text = clean(row["japanese"])
                chunk = int(row["chunk"])
                offset = starts[chunk] + int(row["offset"], 16)
                if not text or offset in seen:
                    continue
                seen.add(offset)
                msgs.append(Message(f"{fld.name} chunk {chunk}", offset, text))
    return msgs


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", type=Path)
    ap.add_argument("files", type=Path)
    ap.add_argument("work", type=Path)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    files = sorted(a.files.glob(SCRIPT_GLOB))
    if not files:
        raise FileNotFoundError(f"no {SCRIPT_GLOB} in {a.files}")
    run_tool(a.exe, files, a.work)
    msgs = collect(files, a.work)
    write_dump(
        a.out,
        "Mahou Gakuen Lunar! (Saturn, Japan), via studio-lucia msl_script_dump",
        "msl.py",
        msgs,
    )
    LOG.info("wrote %d messages from %d files to %s", len(msgs), len(files), a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
