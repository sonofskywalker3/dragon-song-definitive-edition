"""Dump every message of every event script (script.dat), USA and Japanese side by side.

Each message op (0x0F) in a script's code is listed in code order with the text it shows, the USA
text first and the Japanese text of the same op under it. The two releases' scripts have the same
code structure (the same message ops in the same order), so the n-th message op of a USA script is
the n-th of the Japanese one; a script where the counts differ is paired by op order only up to the
shorter list and flagged. Message ops are found by a 4-byte-aligned scan of the code (a linear sweep
desyncs on data inside the code), keeping only ops whose text offset lies in the text block.

Speakers are '<Name>' (FB 06 .. FB 07), places '{Place}', items '[item]'; ' | ' is a page break.
Used for docs/story-characters.md, which cites lines as `script NNN #k` (k = message op index here)
or `script NNN @ 0xOFFSET` (USA text offset).

Usage:
  uv run python -m dsde.text_dump [--out build/text] [--usa-only]
  uv run python -m dsde.text_dump --grep "Ignatius"      # print matching messages with their ids
"""

import argparse
import logging
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from dsde.jp_hint_pairs import USA_LINE_WIDTH, USA_TABLE, decode
from dsde.jp_text import TABLE as JP_TABLE

logger = logging.getLogger("text_dump")

ROOT = Path(__file__).resolve().parents[2]
USA_DIR = ROOT / "build" / "unpacked" / "script"
JP_DIR = ROOT / "build" / "unpacked_jp" / "script"
DEFAULT_OUT = ROOT / "build" / "text"
OP_MSG = 0x0F
OP_ALIGN = 4
HEADER = 8  # the jump to the code
CODE_PTR = 4
EXTRA_PUNCT = {0x23: '"', 0x5A: "!", 0x5B: "-"}  # rare codes, read from context


@dataclass(frozen=True)
class Message:
    op: int  # code address of the message op
    text: int  # file offset of the text


def message_ops(data: bytes) -> list[Message]:
    """Every message op in code order (4-aligned scan), with its text offset."""
    if len(data) < HEADER:
        return []
    code = struct.unpack_from("<I", data, CODE_PTR)[0]
    out = []
    for pc in range(code, len(data) - 7, OP_ALIGN):
        if struct.unpack_from("<H", data, pc)[0] != OP_MSG:
            continue
        text = struct.unpack_from("<I", data, pc + 4)[0]
        if HEADER <= text < code:
            out.append(Message(pc, text))
    return out


def unreferenced(data: bytes, refs: set[int]) -> list[int]:
    """Text starts in the text block that no message op points at."""
    if len(data) < HEADER:
        return []
    code = struct.unpack_from("<I", data, CODE_PTR)[0]
    starts, s = [], HEADER
    while s < code:
        if s not in refs and s + 1 not in refs:  # a lead byte before a referenced start
            starts.append(s)
        e = data.find(b"\xff", s, code)
        if e < 0:
            break
        s = e + 1
        while s < code and data[s] == 0:
            s += 1
    return starts


def dump_script(n: int, usa_only: bool) -> list[str]:
    usa = (USA_DIR / f"{n:03d}.bin").read_bytes()
    jp_path = JP_DIR / f"{n:03d}.bin"
    jp = jp_path.read_bytes() if jp_path.exists() and not usa_only else b""
    table = USA_TABLE | EXTRA_PUNCT
    u_ops, j_ops = message_ops(usa), message_ops(jp)
    lines = [f"######## script {n:03d}: {len(u_ops)} USA message ops, {len(j_ops)} JP"]
    if jp and len(u_ops) != len(j_ops):
        lines.append("# WARNING: op counts differ; JP pairing by order is approximate")
    for k, m in enumerate(u_ops):
        lines.append(f"=== {n:03d} #{k} op {m.op:#x} @ {m.text:#x}")
        lines.append(decode(usa, m.text, table, USA_LINE_WIDTH))
        if k < len(j_ops):
            lines.append("--- JP @ " + f"{j_ops[k].text:#x}")
            lines.append(decode(jp, j_ops[k].text, JP_TABLE))
        lines.append("")
    for off in unreferenced(usa, {m.text for m in u_ops}):
        lines.append(f"=== {n:03d} unreferenced @ {off:#x}")
        lines.append(decode(usa, off, table, USA_LINE_WIDTH))
        lines.append("")
    return lines


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="dsde.text_dump")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--usa-only", action="store_true")
    ap.add_argument(
        "--grep", help="print only messages matching this regex (USA or JP)"
    )
    args = ap.parse_args()
    scripts = sorted(int(p.stem) for p in USA_DIR.glob("*.bin"))
    if args.grep:
        pat = re.compile(args.grep)
        for n in scripts:
            block: list[str] = []
            for line in dump_script(n, args.usa_only) + ["=== end"]:
                if line.startswith("=== ") and block:
                    if pat.search("\n".join(block)):
                        print("\n".join(block))
                    block = []
                if line.startswith("=== "):
                    block = [line]
                elif block:
                    block.append(line)
        return
    args.out.mkdir(parents=True, exist_ok=True)
    total = 0
    for n in scripts:
        lines = dump_script(n, args.usa_only)
        (args.out / f"script_{n:03d}.txt").write_text(
            "\n".join(lines), encoding="utf-8"
        )
        total += sum(1 for line in lines if line.startswith("=== "))
    logger.info(
        "wrote %d messages from %d scripts to %s", total, len(scripts), args.out
    )


if __name__ == "__main__":
    main()
