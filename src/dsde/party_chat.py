"""Party chat engine data: chats and vanilla hints, their conditions, and the bytes the build needs.

The Y button (or tapping the party chat figures) runs script 018 in a fresh script context that
holds a copy of the story flags (docs/re-party-chat.md). Vanilla 018 is one decision tree on story
flags. Here every chat is an entry with a place (map id ranges) and a flag condition; ARM code in
feat_party_chat picks the entry and starts 018 at that entry's code. Each entry has a "read" flag
(a free story flag, so it is saved): the chat icon bounces while the chosen entry is unread.

Which entry plays: entries are checked in order (party_chat_lines.CHATS, then the vanilla hints);
the first unread entry that matches plays, else the first matching one plays again. Entries in the
same chain (the vanilla hints are chain "hint") behave like vanilla's tree: once one matches, later
entries of that chain are out, so only the current story stage's hint can play.

Usage:
    uv run python -m dsde.party_chat seed      # print the vanilla hint table (party_chat_hints.py)
    uv run python -m dsde.party_chat tree      # every vanilla hint with its full condition
"""

import argparse
import logging
import struct
from dataclasses import dataclass, field

from dsde.archive import decompress, read_archive
from dsde.feat_text import (
    LINE_WIDTH,
    NEWLINE,
    PLACE_END,
    PLACE_START,
    VANILLA_SCRIPTS,
    encode_text,
)
from dsde.party_chat_places import Place

log = logging.getLogger(__name__)

SCRIPT = 18
OP_STOP = 0x00
OP_JUMP = 0x02
OP_MSG = 0x0F
OP_IF_ALL = 0x13
OP_IF_ANY = 0x14
OP_IF_NONE = 0x15
OP_PORTRAIT = 0x4F  # u16 face, u32 slot (0 center, 1 left, 2 right)
FLAG_OPS = (OP_IF_ALL, OP_IF_ANY, OP_IF_NONE)
TREE_START = 0x5124  # where the vanilla 018 code starts (its first op jumps here)

# Portrait faces: four expressions per character, in this order (seen in vanilla 018)
FACE_BASE = {"Jian": 1, "Lucia": 5, "Gabryel": 9, "Flora": 13, "Rufus": 17}
FACES_PER_CHARACTER = 4
SLOT_CENTER, SLOT_LEFT, SLOT_RIGHT = 0, 1, 2
SLOTS_BY_COUNT = {
    1: (SLOT_CENTER,),
    2: (SLOT_LEFT, SLOT_RIGHT),
    3: (SLOT_LEFT, SLOT_CENTER, SLOT_RIGHT),
}
PAGE_LINES = (
    5  # text lines a box shows under the speaker's name (vanilla 018 fills all 5)
)
ITEM_START = "["  # stands for FB 03, the item color (closed by FB 07)
ITEM_END = "]"
TEXT_FINISH = b"\xfe\xff"  # wait for a button, end of message
SPEAKER_TAG = b"\xfb\x06%s\xfb\x07\xfd"
COLOR = 0xFB  # FB n: 06 speaker name, 04 place, 03 item, 07 back to white
COLOR_NAME = 0x06
NEWLINE_CODE = 0xFD
PAGE_CODE = 0xFC
TEXT_END = 0xFF

HINT = "hint"  # the chain of the vanilla hints
# Chain bit indexes (0 = not in a chain)
CHAIN_IDS = {"": 0, HINT: 1}


@dataclass(frozen=True)
class Flags:
    """A story flag condition. on: all set; off: none set; any_on: at least one set;
    not_all_on: at least one clear."""

    on: tuple[int, ...] = ()
    off: tuple[int, ...] = ()
    any_on: tuple[int, ...] = ()
    not_all_on: tuple[int, ...] = ()

    def clauses(self) -> list[tuple[int, tuple[int, ...]]]:
        kinds = (
            (KIND_ON, self.on),
            (KIND_OFF, self.off),
            (KIND_ANY, self.any_on),
            (KIND_NOT_ALL, self.not_all_on),
        )
        return [(k, f) for k, f in kinds if f]


KIND_ON, KIND_OFF, KIND_ANY, KIND_NOT_ALL = 1, 2, 3, 4
KIND_SHIFT = 12
ALWAYS = Flags()


@dataclass(frozen=True)
class Say:
    """One text box: who speaks, up to 5 lines of up to 30 characters, and the face (0 to 3).
    {Place names} show blue, [items] show in the item color; braces and brackets take no width."""

    who: str
    text: str
    face: int = 1


@dataclass(frozen=True)
class Chat:
    """A new party chat: where, when, the talk, and the hint (shown last)."""

    where: Place | None
    when: Flags
    talk: tuple[Say, ...]
    hint: Say | None
    chain: str = ""
    note: str = ""


@dataclass(frozen=True)
class Hint:
    """A vanilla 018 line, played from its own code at leaf (offset in script 018)."""

    leaf: int
    when: Flags
    said: str
    where: Place | None = None


@dataclass
class Entry:
    """One row of the ARM table."""

    lo: int
    hi: int
    read_flag: int
    code: int
    chain: int
    when: Flags
    note: str = field(default="")


# --- text -----------------------------------------------------------------


def shown_width(line: str) -> int:
    return len(
        line.replace(PLACE_START, "")
        .replace(PLACE_END, "")
        .replace(ITEM_START, "")
        .replace(ITEM_END, "")
    )


def check_say(say: Say) -> None:
    if say.who not in FACE_BASE:
        raise ValueError(f"no portrait for {say.who!r}; known: {sorted(FACE_BASE)}")
    if not 0 <= say.face < FACES_PER_CHARACTER:
        raise ValueError(f"face {say.face} out of 0..3 in {say.text!r}")
    lines = say.text.split(NEWLINE)
    if len(lines) > PAGE_LINES:
        raise ValueError(f"over {PAGE_LINES} lines: {say.text!r}")
    for line in lines:
        if shown_width(line) > LINE_WIDTH:
            raise ValueError(f"line over {LINE_WIDTH} characters: {line!r}")


def encode_line_text(text: str) -> bytes:
    """encode_text plus [item] colors; a full-width line wraps by itself (no newline stored)."""
    out = b""
    lines = text.split(NEWLINE)
    for i, line in enumerate(lines):
        for part_i, part in enumerate(
            line.replace(ITEM_END, ITEM_START).split(ITEM_START)
        ):
            if part_i:
                out += b"\xfb\x03" if part_i % 2 else b"\xfb\x07"
            out += encode_text(part)
        if i < len(lines) - 1 and shown_width(line) < LINE_WIDTH:
            out += encode_text(NEWLINE)
    return out


def say_bytes(say: Say) -> bytes:
    check_say(say)
    return SPEAKER_TAG % encode_text(say.who) + encode_line_text(say.text) + TEXT_FINISH


def decode(data: bytes) -> str:
    """Vanilla text as plain words (for notes): 'Name: words', pages joined by ' / '."""
    letters = {0x02 + n: chr(65 + n) for n in range(26)} | {
        0x3A + n: chr(97 + n) for n in range(26)
    }
    letters |= {0x30 + n: str(n) for n in range(10)}
    letters |= {
        0x00: " ",
        0x29: ",",
        0x2A: ".",
        0x24: "!",
        0x25: "?",
        0x2D: ":",
        0x54: "'",
        0x26: "-",
    }
    out = []
    in_name = False
    i = 0
    while i < len(data) and data[i] != TEXT_END:
        c = data[i]
        if c == COLOR:
            if data[i + 1] == COLOR_NAME:
                in_name = True
            elif in_name:
                out.append(": ")
                in_name = False
            i += 2
            continue
        out.append({NEWLINE_CODE: " ", PAGE_CODE: " / "}.get(c, letters.get(c, "")))
        i += 1
    return " ".join("".join(out).split())


# --- the vanilla tree -------------------------------------------------------


def vanilla_script() -> bytes:
    return decompress(read_archive(VANILLA_SCRIPTS.read_bytes())[SCRIPT])


def _flag_op(data: bytes, pc: int) -> tuple[int, int, tuple[int, ...]]:
    op, count, target = struct.unpack_from("<HHI", data, pc)
    return op, target, struct.unpack_from(f"<{count}I", data, pc + 8)


def tree_paths(
    data: bytes,
) -> list[
    tuple[int, list[tuple[int, tuple[int, ...]]], list[tuple[int, tuple[int, ...]]]]
]:
    """Every path through the vanilla tree in first-match order: (leaf, taken clauses, all clauses).

    taken holds only the branches the path follows (enough inside the "hint" chain, where order
    does the rest); full adds the negation of each branch passed by (the exact condition).
    """
    paths = []
    negate = {OP_IF_ALL: KIND_NOT_ALL, OP_IF_ANY: KIND_OFF, OP_IF_NONE: KIND_ANY}
    positive = {OP_IF_ALL: KIND_ON, OP_IF_ANY: KIND_ANY, OP_IF_NONE: KIND_OFF}

    def walk(pc: int, taken: list, full: list) -> None:
        while True:
            op = struct.unpack_from("<H", data, pc)[0]
            if op in FLAG_OPS:
                _, target, flags = _flag_op(data, pc)
                clause = (positive[op], flags)
                walk(target, taken + [clause], full + [clause])
                kind = negate[op]
                if kind == KIND_NOT_ALL and len(flags) == 1:
                    kind = KIND_OFF
                if kind == KIND_ANY and len(flags) == 1:
                    kind = KIND_ON
                full = full + [(kind, flags)]
                pc += 8 + 4 * len(flags)
            elif op == OP_JUMP:
                pc = struct.unpack_from("<I", data, pc + 4)[0]
            else:
                paths.append((pc, taken, full))
                return

    walk(TREE_START, [], [])
    return paths


def flags_of(clauses: list[tuple[int, tuple[int, ...]]]) -> Flags:
    merged: dict[int, list[int]] = {
        KIND_ON: [],
        KIND_OFF: [],
        KIND_ANY: [],
        KIND_NOT_ALL: [],
    }
    anys = [f for k, f in clauses if k == KIND_ANY]
    not_alls = [f for k, f in clauses if k == KIND_NOT_ALL]
    if len(anys) > 1 or len(not_alls) > 1:
        raise ValueError(f"more than one any/not-all group: {clauses}")
    for kind, flags in clauses:
        merged[kind] += [f for f in flags if f not in merged[kind]]
    return Flags(
        tuple(merged[KIND_ON]),
        tuple(merged[KIND_OFF]),
        tuple(merged[KIND_ANY]),
        tuple(merged[KIND_NOT_ALL]),
    )


def leaf_text(data: bytes, leaf: int) -> str:
    """The first message the leaf shows, as plain words."""
    pc = leaf
    while struct.unpack_from("<H", data, pc)[0] != OP_MSG:
        pc += 8
    offset = struct.unpack_from("<I", data, pc + 4)[0]
    return decode(data[offset : data.index(0xFF, offset) + 1])


def fmt_flags(flags: Flags) -> str:
    parts = []
    for name in ("on", "off", "any_on", "not_all_on"):
        values = getattr(flags, name)
        if values:
            inner = ", ".join(f"{v:#x}" for v in values)
            parts.append(f"{name}=({inner}{',' if len(values) == 1 else ''})")
    return f"Flags({', '.join(parts)})"


def seed_source() -> str:
    """party_chat_hints.py as generated from vanilla 018 (place restrictions are added by hand)."""
    data = vanilla_script()
    rows = []
    for leaf, taken, _ in tree_paths(data):
        said = leaf_text(data, leaf).replace('"', "'")
        rows.append(
            f'    Hint({leaf:#06x}, {fmt_flags(flags_of(taken))},\n         "{said[:70]}"),'
        )
    return "\n".join(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.party_chat")
    parser.add_argument("what", choices=("seed", "tree"))
    args = parser.parse_args()
    if args.what == "seed":
        log.info(seed_source())
        return
    data = vanilla_script()
    for leaf, _, full in tree_paths(data):
        log.info(
            "| %#06x | %s | %s |",
            leaf,
            fmt_flags(flags_of(full)),
            leaf_text(data, leaf)[:80],
        )


if __name__ == "__main__":
    main()
