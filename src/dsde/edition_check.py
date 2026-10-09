"""Lists every script message a build changes, and checks the Classic edition changes only fixes.

Compares a built script.dat with the original's, message op by message op: for each message op (0x0F) of
an original script, the text it shows in the original and in the build (or that the op is gone), plus
every message op the build adds. With --classic, each change must be one of the text-fixes renames
(feat_text.TEXT_FIX_EDITS) and the build must add no message op; anything else fails the check.

Usage:
    uv run python -m dsde.edition_check build/editions/classic_extract/files/script.dat --classic
    uv run python -m dsde.edition_check build/editions/retold_extract/files/script.dat
"""

import argparse
import logging
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.feat_text import TEXT_FIX_EDITS, VANILLA_SCRIPTS, encode_text
from dsde.jp_hint_pairs import USA_LINE_WIDTH, USA_TABLE, decode

logger = logging.getLogger(__name__)

OP_MSG = 0x0F
OP_ALIGN = 4
CODE_PTR = 4
HEADER = 8
TEXT_END = 0xFF
CHECK_FAILED = 1


@dataclass(frozen=True)
class Change:
    script: int
    op: int  # code address of the message op
    old: bytes | None  # None: the build added this message op
    new: bytes | None  # None: the build replaced the op with another one


def _texts(data: bytes, code_start: int) -> dict[int, bytes]:
    """{message op address: its text, terminator included} from a 4-aligned scan of the code."""
    out = {}
    for pc in range(code_start, len(data) - 7, OP_ALIGN):
        if struct.unpack_from("<H", data, pc)[0] != OP_MSG:
            continue
        text = struct.unpack_from("<I", data, pc + 4)[0]
        end = data.find(bytes([TEXT_END]), text)
        if HEADER <= text < len(data) and end != -1:
            out[pc] = data[text : end + 1]
    return out


def changes(vanilla_dat: bytes, built_dat: bytes) -> list[Change]:
    out = []
    old_entries = read_archive(vanilla_dat)
    new_entries = read_archive(built_dat)
    for script, (old_raw, new_raw) in enumerate(
        zip(old_entries, new_entries, strict=True)
    ):
        old, new = decompress(old_raw), decompress(new_raw)
        if old == new or len(old) < HEADER:
            continue
        code = struct.unpack_from("<I", old, CODE_PTR)[0]
        # original ops: only those whose text lies in the original text block (as dsde.text_dump)
        old_texts = {
            pc: t
            for pc, t in _texts(old, code).items()
            if struct.unpack_from("<I", old, pc + 4)[0] < code
        }
        new_texts = _texts(new, code)
        for pc, text in old_texts.items():
            if new_texts.get(pc) != text:
                out.append(Change(script, pc, text, new_texts.get(pc)))
        out += [
            Change(script, pc, None, text)
            for pc, text in new_texts.items()
            if pc >= len(old)
        ]
    return out


def _is_fix(change: Change) -> bool:
    if change.old is None or change.new is None:
        return False
    fixed = change.old
    for edit in TEXT_FIX_EDITS:
        if edit.script == change.script:
            fixed = fixed.replace(encode_text(edit.old), encode_text(edit.new))
    return fixed == change.new and fixed != change.old


def _show(text: bytes | None) -> str:
    if text is None:
        return "(no message op)"
    return decode(text, 0, USA_TABLE, USA_LINE_WIDTH).replace("\n", " / ")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.edition_check")
    parser.add_argument("script_dat", type=Path, help="script.dat of a build")
    parser.add_argument(
        "--classic",
        "--engine",
        dest="classic",
        action="store_true",
        help="fail unless every change is a text-fixes rename (--engine: the old name)",
    )
    args = parser.parse_args()
    found = changes(VANILLA_SCRIPTS.read_bytes(), args.script_dat.read_bytes())
    bad = 0
    for change in found:
        fix = _is_fix(change)
        bad += not fix
        kind = "fix" if fix else "CHANGE"
        logger.info(
            "%s script %03d op %#06x\n  was: %s\n  now: %s",
            kind,
            change.script,
            change.op,
            _show(change.old),
            _show(change.new),
        )
    logger.info("%d changed messages, %d not text-fixes renames", len(found), bad)
    if args.classic and bad:
        sys.exit(CHECK_FAILED)


if __name__ == "__main__":
    main()
