"""Lunar Sega CD dialogue dumps via Supper's wdtools rippers.

    python -I segacd.py tss FILES_DIR SCRIPTRIP_TSS_EXE OUT.txt [--subs SUBS.txt]
    python -I segacd.py eb  FILES_DIR SCRIPTRIP_EXE     OUT.txt [--subs SUBS.txt]
    python -I segacd.py ebjp FILES_DIR SCRIPTRIP_JP_EXE OUT.txt --table scriptrip_jp_thingy.txt
                                                    (Japanese Eternal Blue, untested here)

FILES_DIR is the disc's root as extracted by discfs.py. The Silver Star keeps its
dialogue in C*.MAP, Eternal Blue in M*.GRP. The text on disc is upper case only; the
rippers guess sentence case and the optional substitution file restores proper nouns
(wdtools format: "orig | Replacement;").
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Message, apply_subs, load_subs, write_dump  # noqa: E402

LOG = logging.getLogger("segacd")

GAMES = {
    "tss": ("C*.MAP", "Lunar: The Silver Star (Sega CD, USA)"),
    "eb": ("M*.GRP", "Lunar: Eternal Blue (Sega CD, USA)"),
    "ebjp": ("M*.GRP", "Lunar: Eternal Blue (Mega CD, Japan)"),
}
HEADER_RE = re.compile(r"^=== ([0-9a-f]+) \| ([0-9a-f]+) \| ([0-9a-f]+) ===$", re.M)
PORTRAIT_RE = re.compile(r"\[(POR|ROR)(\d+)\]\n?")
END = "[END]"
BRK = "[BRK]\n\n"
SIDE = {"POR": "L", "ROR": "R"}
RAW_CODE_RE = re.compile(r"\[0x[0-9a-f]+\]|\[[0-9a-f]{1,2}\]")
SILENCE_RE = re.compile(r"[.!?\s]+")


def parse(output: str, source: str) -> list[Message]:
    msgs = []
    heads = list(HEADER_RE.finditer(output))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(output)
        body = output[h.end() + 1 : end].rstrip()
        if body.endswith(END):
            body = body[: -len(END)]
        speakers = []
        first = True

        def tag(m: re.Match[str]) -> str:
            nonlocal first
            sp = f"{SIDE[m.group(1)]}{int(m.group(2))}"
            speakers.append(sp)
            at_start = first and m.start() == 0
            first = False
            return "" if at_start else f"[{sp}] "

        body = PORTRAIT_RE.sub(tag, body)
        body = body.replace(BRK, "\n\n").replace("[BRK]", "\n\n")
        msgs.append(Message(source, int(h.group(2), 16), body, speakers))
    return msgs


def junk(text: str) -> bool:
    """Drop heuristic misdetections: empty strings, symbol soup, or mostly raw byte codes.

    A message of only dots/!/? (a silent "...." box) is kept."""
    bare = RAW_CODE_RE.sub("", text).strip()
    letters = len(re.findall(r"[A-Za-z]", bare))
    if not bare:
        return True
    if letters == 0:
        return not SILENCE_RE.fullmatch(bare)
    return len(RAW_CODE_RE.findall(text)) > letters


def run(
    game: str,
    files: Path,
    exe: Path,
    out: Path,
    subs: Path | None,
    table: Path | None = None,
) -> int:
    pattern, title = GAMES[game]
    rules = load_subs(subs) if subs else []
    messages: list[Message] = []
    for f in sorted(files.glob(pattern)):
        cmd = [str(exe.resolve()), str(f.resolve())]
        if table:
            cmd.append(str(table.resolve()))
        res = subprocess.run(cmd, capture_output=True)
        text = res.stdout.decode(
            "utf-8" if game == "ebjp" else "latin-1", "replace"
        ).replace("\r\n", "\n")
        got = [m for m in parse(text, f.name) if not junk(m.text)]
        for m in got:
            m.text = apply_subs(m.text, rules)
        LOG.info("%s: %d messages", f.name, len(got))
        messages.extend(got)
    tool = f"wdtools {exe.stem}" + (f" with substitutions {subs.name}" if subs else "")
    write_dump(out, title, tool, messages)
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("game", choices=sorted(GAMES))
    ap.add_argument("files", type=Path)
    ap.add_argument("exe", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--subs", type=Path)
    ap.add_argument("--table", type=Path, help="Thingy table (scriptrip_jp needs it)")
    a = ap.parse_args()
    if a.game == "ebjp" and not a.table:
        ap.error("ebjp needs --table (wdtools src/scriptrip_jp_thingy.txt)")
    run(a.game, a.files, a.exe, a.out, a.subs, a.table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
