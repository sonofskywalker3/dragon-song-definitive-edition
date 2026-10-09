"""Party chat: the Y button (script 018) knows where you are, and its icon bounces for a new chat.

docs/re-party-chat.md has the research and the table format. Three hooks:
- Both places that start script 018 (field Y / the figures at 0x02020188, the System menu at
  0x0205F368) call cave_chat_start instead of func_02041988: it starts the script, puts the map id in
  var 1 (as map entry events have it), picks the entry (cave_chat_select), points the script at the
  entry's code, and sets the entry's read flag (in the hint context, which the game copies back to the
  story flags when the chat ends, and in the story flags themselves).
- The per-frame HUD pulse call (0x02022108) also runs cave_chat_frame: while the entry chosen for
  this map and these flags is unread, the party chat figures (HUD button 6) use their own affine
  matrix 6 and pulse like vanilla's figures (scale 1 + sin / 8, 32 frames); otherwise they are drawn
  without a matrix and stand still. Works with or without still-hud (which stills matrix 5).

The entry table is in ITCM (halfwords): per entry [length, map lo, map hi, read flag, code / 4, chain
bit], then clauses [kind << 12 | count, flags...]; a zero length ends it. The chats' code and text are
appended to script 018 after the messages text-edits moves there (same bytes, as feat_opening does).
"""

import logging
import struct
from dataclasses import dataclass

from dsde.archive import decompress, read_archive
from dsde.feat_text import ARCHIVE, VANILLA_SCRIPTS, text_patches
from dsde.party_chat import (
    CHAIN_IDS,
    FACE_BASE,
    KIND_SHIFT,
    OP_MSG,
    OP_PORTRAIT,
    OP_STOP,
    SCRIPT,
    SLOTS_BY_COUNT,
    Chat,
    Entry,
    Hint,
    Say,
    say_bytes,
    tree_paths,
)
from dsde.party_chat_asm import (
    FRAME_ASM,
    HINT_START_FIELD,
    HINT_START_FIELD_WORD,
    HINT_START_MENU,
    HINT_START_MENU_WORD,
    PULSE_CALL,
    PULSE_CALL_WORD,
    SELECT_ASM,
    START_ASM,
)
from dsde.party_chat_hints import HINTS
from dsde.party_chat_lines import CHATS
from dsde.patching import AsmPatch, CaveCode, DataPatch, Feature
from dsde.script import OP_FLAG_LISTS, linear, reachable

ALIGN = 4
ANY_MAP = (0, 0xFFFE)
ENTRY_HEADER = 6  # halfwords
MAX_FLAGS_PER_CLAUSE = 0xFF
# Read flags: story flags no script tests or sets and engine code does not read (scan in
# _check_free; engine reads are listed in docs/re-field-battle.md section 5). 0x1E0..0x220 is left
# alone: the engine sets 0x1E0 + n for each place visited.
READ_FLAGS = (
    *range(0x84, 0xC9),
    *range(0xDE, 0x12D),
    *range(0x14B, 0x18E),
    *range(0x221, 0x243),
    *range(0x244, 0x260),
)


@dataclass(frozen=True)
class Layout:
    """Where the new script bytes go and what they are."""

    base: int
    moved: tuple[DataPatch, ...]
    code: bytes
    chat_code: dict[int, int]  # id(chat) -> code offset


def _op(code: int, arg: int = 0, word: int = 0) -> bytes:
    return struct.pack("<HHI", code, arg, word)


def _speakers(chat: Chat) -> list[str]:
    says = list(chat.talk) + ([chat.hint] if chat.hint else [])
    order = list(dict.fromkeys(s.who for s in says))
    if len(order) not in SLOTS_BY_COUNT:
        raise ValueError(f"{chat.note or chat}: 1 to 3 speakers, not {order}")
    return order


def _says(chat: Chat) -> list[Say]:
    says = list(chat.talk) + ([chat.hint] if chat.hint else [])
    if not says:
        raise ValueError(f"{chat.note or chat}: nothing to say")
    return says


def _chat_program(chat: Chat, text_at: int) -> tuple[bytes, bytes]:
    """Code (portraits, one message per Say, stop) and its text, the text placed at text_at."""
    order = _speakers(chat)
    slot = dict(zip(order, SLOTS_BY_COUNT[len(order)], strict=True))
    face: dict[str, int] = {}
    says = _says(chat)
    for say in says:
        face.setdefault(say.who, say.face)
    code = b"".join(_op(OP_PORTRAIT, FACE_BASE[w] + face[w], slot[w]) for w in order)
    text = b""
    for say in says:
        if face[say.who] != say.face:
            face[say.who] = say.face
            code += _op(OP_PORTRAIT, FACE_BASE[say.who] + say.face, slot[say.who])
        code += _op(OP_MSG, 0, text_at + len(text))
        text += say_bytes(say)
    return code + struct.pack("<I", OP_STOP), text


def _all_chats() -> list[Chat]:
    return list(CHATS) + [e for e in HINTS if isinstance(e, Chat)]


def layout(vanilla: bytes) -> Layout:
    moved = tuple(
        p
        for p in text_patches()
        if p.entry == SCRIPT and not p.old and p.offset >= len(vanilla)
    )
    end = max((p.offset + len(p.new) for p in moved), default=len(vanilla))
    base = -(-end // ALIGN) * ALIGN
    chats = _all_chats()
    # Code first (4-byte ops), then all text. Code size does not depend on text offsets.
    sizes = [len(_chat_program(c, 0)[0]) for c in chats]
    text_at = base + sum(sizes)
    code = b""
    text = b""
    chat_code = {}
    for chat in chats:
        chat_code[id(chat)] = base + len(code)
        c, t = _chat_program(chat, text_at + len(text))
        code += c
        text += t
    return Layout(base, moved, b"\x00" * (base - end) + code + text, chat_code)


def _script_flags() -> set[int]:
    """Every story flag a script op tests, sets, or clears (any script)."""
    used: set[int] = set()
    script_log = logging.getLogger("dsde.script")
    level = script_log.level
    script_log.setLevel(
        logging.ERROR
    )  # the sweeps warn where data follows code; that is fine here
    try:
        for entry in read_archive(VANILLA_SCRIPTS.read_bytes()):
            used |= _flags_in(decompress(entry))
    finally:
        script_log.setLevel(level)
    return used


def _flags_in(data: bytes) -> set[int]:
    used: set[int] = set()
    if len(data) >= 2 * ALIGN:
        for pc in set(linear(data)) | set(reachable(data)):
            op, arg = struct.unpack_from("<Hh", data, pc)
            if op in OP_FLAG_LISTS:
                used.update(struct.unpack_from(f"<{arg}I", data, pc + 8))
            elif op in (0x19, 0x1A):
                used.add(arg)
    return used


def _check_free(flags: list[int]) -> None:
    clash = sorted(set(flags) & _script_flags())
    if clash:
        raise ValueError(
            f"party chat read flags used by scripts: {[hex(f) for f in clash]}"
        )


def entries(vanilla: bytes, code_of: dict[int, int]) -> list[Entry]:
    """The ARM table rows: chats, then the vanilla hints, one row per map range."""
    leaves = {leaf for leaf, _, _ in tree_paths(vanilla)}
    hint_leaves = sorted({e.leaf for e in HINTS if isinstance(e, Hint)})
    missing = [hex(x) for x in hint_leaves if x not in leaves]
    if missing:
        raise ValueError(f"not vanilla 018 hint code: {missing}")
    chats = _all_chats()
    if len(hint_leaves) + len(chats) > len(READ_FLAGS):
        raise ValueError(f"over {len(READ_FLAGS)} party chat entries")
    read = dict(zip(hint_leaves, READ_FLAGS, strict=False))
    read |= {
        id(c): f for c, f in zip(chats, READ_FLAGS[len(hint_leaves) :], strict=False)
    }
    _check_free(list(read.values()))
    rows = []
    for item in (*CHATS, *HINTS):
        key = item.leaf if isinstance(item, Hint) else id(item)
        code = item.leaf if isinstance(item, Hint) else code_of[id(item)]
        chain = CHAIN_IDS["hint"] if isinstance(item, Hint) else CHAIN_IDS[item.chain]
        ranges = item.where.maps if item.where else (ANY_MAP,)
        note = item.said if isinstance(item, Hint) else item.note
        rows += [
            Entry(lo, hi, read[key], code, chain, item.when, note) for lo, hi in ranges
        ]
    return rows


def table_halfwords(rows: list[Entry]) -> list[int]:
    out = []
    for row in rows:
        clauses = []
        for kind, flags in row.when.clauses():
            if len(flags) > MAX_FLAGS_PER_CLAUSE:
                raise ValueError(f"too many flags in one clause: {row.note}")
            clauses += [kind << KIND_SHIFT | len(flags), *flags]
        if row.code % ALIGN:
            raise ValueError(f"code at {row.code:#x} is not aligned")
        out += [ENTRY_HEADER + len(clauses), row.lo, row.hi, row.read_flag]
        out += [row.code // ALIGN, row.chain, *clauses]
    return out + [0]


def _hook(addr: int, word: int, cave: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, word, word, f"bl ${{{cave}}}", note)


def party_chat_patches() -> tuple[DataPatch | CaveCode | AsmPatch, ...]:
    vanilla = decompress(read_archive(VANILLA_SCRIPTS.read_bytes())[SCRIPT])
    lay = layout(vanilla)
    end = max((p.offset + len(p.new) for p in lay.moved), default=len(vanilla))
    rows = entries(vanilla, lay.chat_code)
    table = "\n".join(f"    .hword {h:#x}" for h in table_halfwords(rows))
    return (
        *(
            DataPatch(
                ARCHIVE,
                SCRIPT,
                p.offset,
                b"",
                p.new,
                f"party chat: same bytes as {p.note}",
            )
            for p in lay.moved
        ),
        DataPatch(
            ARCHIVE, SCRIPT, end, b"", lay.code, "party chat: new chats (code, text)"
        ),
        CaveCode(
            "cave_chat_select",
            SELECT_ASM,
            "party chat: pick the entry for this map and these flags",
        ),
        CaveCode(
            "cave_chat_start", START_ASM, "party chat: start 018 at the chosen entry"
        ),
        CaveCode(
            "cave_chat_frame",
            FRAME_ASM,
            "party chat: figures bounce for an unread chat",
        ),
        CaveCode("cave_chat_phase", "    .word 0", "party chat: bounce phase"),
        CaveCode(
            "cave_chat_table",
            table + "\n    .align 2",
            f"party chat: {len(rows)} entries",
        ),
        _hook(
            HINT_START_FIELD,
            HINT_START_FIELD_WORD,
            "cave_chat_start",
            "Y chat starts at the chosen entry",
        ),
        _hook(
            HINT_START_MENU,
            HINT_START_MENU_WORD,
            "cave_chat_start",
            "menu hint starts at the chosen entry",
        ),
        _hook(
            PULSE_CALL,
            PULSE_CALL_WORD,
            "cave_chat_frame",
            "party chat icon bounces for a new chat",
        ),
    )


PARTY_CHAT = Feature("party-chat", party_chat_patches())
