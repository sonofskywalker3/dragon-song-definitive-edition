"""Pair every USA script 018 (Y-button hint) line with its Japanese original, by the flag tree.

Both releases' 018 are the same first-match tree of flag tests (ops 0x13/0x14/0x15), so each path
is identified by its full flag condition, not by its order or offset. This walks both trees, pairs
paths whose conditions are equal, and prints every message of each leaf in both languages (with
the portrait faces the leaf shows, which tell who speaks). Used for docs/re-party-chat-japanese.md.

Usage:
  uv run python -m dsde.jp_hint_pairs [--usa build/unpacked/script/018.bin]
                                      [--jp build/unpacked_jp/script/018.bin]
"""

import argparse
import logging
import struct
import sys
from pathlib import Path

from dsde.jp_text import TABLE as JP_TABLE
from dsde.script import op_length

logger = logging.getLogger("jp_hint_pairs")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USA = ROOT / "build" / "unpacked" / "script" / "018.bin"
DEFAULT_JP = ROOT / "build" / "unpacked_jp" / "script" / "018.bin"

OP_STOP, OP_JUMP, OP_RET, OP_MSG, OP_PORTRAIT = 0x00, 0x02, 0x04, 0x0F, 0x4F
OP_ALL, OP_ANY, OP_NONE = 0x13, 0x14, 0x15
FLAG_OPS = frozenset({OP_ALL, OP_ANY, OP_NONE})
END_OPS = frozenset({OP_STOP, OP_RET})
CTRL, NEWLINE, PAGE, PAGE_FORM, END = 0xFB, 0xFD, 0xFE, 0xFC, 0xFF
SPEAKER, PLACE, ITEM, COLOR_RESET = 0x06, 0x04, 0x03, 0x07
OPENERS = {SPEAKER: "<", PLACE: "{", ITEM: "["}
CLOSERS = {SPEAKER: ">", PLACE: "}", ITEM: "]"}
# condition kinds: taken branch, or the negation of a branch passed by
POSITIVE = {OP_ALL: "on", OP_ANY: "any", OP_NONE: "off"}
NEGATED = {OP_ALL: "notall", OP_ANY: "off", OP_NONE: "any"}
USA_LINE_WIDTH = 30
LONG_TALK_OPS = frozenset({0x32, 0x33, 0x36})  # inside a few long talks; not text
FACE_NAMES = {0: "Jian", 1: "Lucia", 2: "Gabryel", 3: "Flora", 4: "Rufus"}
FACES_PER_CHARACTER = 4

USA_PUNCT = {
    0x00: " ", 0x24: "!", 0x25: "?", 0x26: "-", 0x29: ",", 0x2A: ".", 0x2D: ":", 0x54: "'",
}  # fmt: skip
USA_TABLE = (
    USA_PUNCT
    | {0x02 + i: chr(65 + i) for i in range(26)}
    | {0x3A + i: chr(97 + i) for i in range(26)}
    | {0x30 + i: str(i) for i in range(10)}
)

Condition = frozenset[tuple[str, tuple[int, ...]]]


def tree(data: bytes) -> list[tuple[int, Condition]]:
    """Every path of the tree in first-match order: (leaf offset, full condition)."""
    start = struct.unpack_from("<I", data, 4)[0]
    paths: list[tuple[int, Condition]] = []

    def walk(pc: int, cond: list[tuple[str, tuple[int, ...]]]) -> None:
        while True:
            op = struct.unpack_from("<H", data, pc)[0]
            if op in FLAG_OPS:
                count, target = struct.unpack_from("<HI", data, pc + 2)
                flags = tuple(sorted(struct.unpack_from(f"<{count}I", data, pc + 8)))
                walk(target, cond + [(POSITIVE[op], flags)])
                cond = cond + [(NEGATED[op], flags)]
                pc += op_length(data, pc)
            elif op == OP_JUMP:
                pc = struct.unpack_from("<I", data, pc + 4)[0]
            else:
                paths.append((pc, frozenset(cond)))
                return

    walk(start, [])
    return paths


def decode(data: bytes, offset: int, table: dict[int, str], wrap: int = 0) -> str:
    """Message text: '<Name>' speakers, {place} and [item] colors, \n line breaks, ' | ' pages.

    wrap > 0 adds the line break the box makes by itself after a full line (the USA text stores
    none there, so a raw dump shows 'istake' where the game shows 'is' / 'take').
    """
    out: list[str] = []
    i = offset
    col = 0
    closer = ""
    while data[i] != END:
        b = data[i]
        if b == CTRL:
            arg = data[i + 1]
            if arg == COLOR_RESET:
                out.append(closer)
                closer = ""
            else:
                out.append(OPENERS.get(arg, f"<FB{arg:02X}>"))
                closer = CLOSERS.get(arg, "")
            i += 2
            continue
        if b in (NEWLINE, PAGE):
            out.append("\n" if b == NEWLINE else " | ")
            col = 0
        elif b != PAGE_FORM:
            if wrap and col == wrap and closer != ">":
                # the break goes before a color that opens right at the wrap
                at = len(out) - 1 if out and out[-1] in OPENERS.values() else len(out)
                out.insert(at, "\n")
                col = 0
            out.append(table.get(b, f"<{b:02x}>"))
            col += 0 if closer == ">" else 1
        i += 1
    return "".join(out)


def leaf_body(
    data: bytes, leaf: int, table: dict[int, str], wrap: int = 0
) -> list[str]:
    """The leaf's ops until it stops: portraits (faces) and messages, in order."""
    out: list[str] = []
    pc = leaf
    while True:
        op = struct.unpack_from("<H", data, pc)[0]
        if op in END_OPS:
            return out
        if op == OP_JUMP:
            pc = struct.unpack_from("<I", data, pc + 4)[0]
            continue
        if op == OP_PORTRAIT:
            face, slot = struct.unpack_from("<HI", data, pc + 2)
            who = FACE_NAMES.get((face - 1) // FACES_PER_CHARACTER, f"face{face}")
            out.append(f"  [face {face} {who} slot {slot}]")
        elif op == OP_MSG:
            text = struct.unpack_from("<I", data, pc + 4)[0]
            out.append("  " + decode(data, text, table, wrap))
        elif op in FLAG_OPS:
            out.append(f"  [op {op:#x} inside leaf]")
        elif op not in LONG_TALK_OPS:
            out.append(f"  [op {op:#x}]")
        pc += op_length(data, pc)


def set_flags(cond: Condition) -> frozenset[tuple[str, tuple[int, ...]]]:
    """Only the flags the path requires set (for pairing when one release added a branch)."""
    return frozenset(c for c in cond if c[0] == "on")


def fmt(cond: Condition) -> str:
    order = ("on", "off", "any", "notall")
    parts = sorted(cond, key=lambda c: (order.index(c[0]), c[1]))
    return "; ".join(f"{k} {' '.join(f'{f:X}' for f in fl)}" for k, fl in parts)


def pair_paths(
    usa: bytes, jp: bytes
) -> tuple[list[tuple[int, Condition, int | None, bool]], list[tuple[int, Condition]]]:
    """(USA leaf, condition, JP leaf or None, loose) per USA path, and the JP paths left unpaired.

    A path pairs exactly when both conditions are equal; failing that, loosely when exactly one JP
    path requires the same flags set (the USA tree has one more branch, so the flags a later path
    must find clear differ).
    """
    jp_paths = tree(jp)
    exact = {cond: leaf for leaf, cond in jp_paths}
    loose: dict[frozenset, list[tuple[int, Condition]]] = {}
    for leaf, cond in jp_paths:
        loose.setdefault(set_flags(cond), []).append((leaf, cond))
    used: set[Condition] = set()
    out: list[tuple[int, Condition, int | None, bool]] = []
    for leaf, cond in tree(usa):
        if cond in exact:
            out.append((leaf, cond, exact[cond], False))
            used.add(cond)
        elif len(loose.get(set_flags(cond), [])) == 1:
            jleaf, jcond = loose[set_flags(cond)][0]
            out.append((leaf, cond, jleaf, True))
            used.add(jcond)
        else:
            out.append((leaf, cond, None, False))
    return out, [(leaf, cond) for leaf, cond in jp_paths if cond not in used]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="dsde.jp_hint_pairs")
    ap.add_argument("--usa", type=Path, default=DEFAULT_USA)
    ap.add_argument("--jp", type=Path, default=DEFAULT_JP)
    args = ap.parse_args()
    usa, jp = args.usa.read_bytes(), args.jp.read_bytes()
    pairs, jp_only = pair_paths(usa, jp)
    logger.info("USA paths: %d; JP paths left unpaired: %d", len(pairs), len(jp_only))
    for n, (leaf, cond, jleaf, is_loose) in enumerate(pairs, 1):
        where = (
            "none"
            if jleaf is None
            else f"{jleaf:#x}" + (" (loose)" if is_loose else "")
        )
        print(f"### {n} USA {leaf:#x} JP {where}")
        print(f"cond: {fmt(cond)}")
        print("USA:")
        print("\n".join(leaf_body(usa, leaf, USA_TABLE, USA_LINE_WIDTH)))
        if jleaf is not None:
            print("JP:")
            print("\n".join(leaf_body(jp, jleaf, JP_TABLE)))
        print()
    for leaf, cond in jp_only:
        print(f"### JP only {leaf:#x}")
        print(f"cond: {fmt(cond)}")
        print("\n".join(leaf_body(jp, leaf, JP_TABLE)))


if __name__ == "__main__":
    main()
