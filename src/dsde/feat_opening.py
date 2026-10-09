"""Opening: Jian walks out of the inn (playtest feedback item 2), in two features (docs/plan-two-editions.md).

Both are in the Retold edition only; the Classic edition's opening is the original's (Jeff, 2026-10-09).

- `opening-run` (no wording changed): the vanilla wake-up and Jian's self-introduction play
  as written; after his last line ("Right then! I'd better go looking for Lucia...") the script walks him
  out of the inn and sets the story flags that make Cherenkov and Jack optional (both can still be talked
  to, and say their vanilla lines).
- `opening-text` (after opening-run): Cherenkov's wake-up call from downstairs replaces the
  self-introduction, Jian's thoughts show as asides while he walks (one per map, closing by themselves as
  the walk ends: feat_opening_asides.py), and Cherenkov's lobby line sends Jian to Fountain Square.

Mechanics in docs/re-opening.md. The walk crosses three maps, and a script cannot survive a map change
(op 0x10 ends it), so each leg ends with a map change and the next leg starts from the new map's entry
event: the script's entry dispatcher (event type 1, var 1 = map id) is pointed at a new block that sends the
hall (160) and the lobby (155) to their legs while RUN_FLAG is set. The last leg clears the flag and leaves
for the street (285), where the player gets control. Each leg has an aside slot, a jump to the next op that
opening-text overwrites with a message op.

Appended bytes go after the messages text-fixes moves to the end of script 001. opening-run writes those
same bytes too, so the layout is the same whether or not text-fixes is in the build; opening-text's code
goes after opening-run's.
"""

import struct
from dataclasses import dataclass

from dsde.archive import decompress, read_archive
from dsde.feat_text import ARCHIVE, VANILLA_SCRIPTS, encode_text, text_patches
from dsde.patching import DataPatch, Feature

SCRIPT = 1
ALIGN = 4
# In-place sites in script 001
ENTRY_DISPATCH_TARGET = 0x54C0  # u32 target of "if var0 == 1 (map entry) goto 0x56B4"
VANILLA_MAP_ENTRY = 0x56B4
WAKE_MESSAGE_OP = (
    0x62CC  # msg "....It's morning...?", the first op after the wake-up fade-in
)
# The op after the vanilla wake-up's last line ("Right then! I'd better go looking for Lucia..."): a stop,
# then a dead goto_map nothing jumps to (docs/re-opening.md 1). The jump to the walk overwrites both halves.
WAKE_END = 0x63C4
JUMP_SIZE = 8
# opening-flags (Classic edition) writes three ops over those 12 bytes (0x63C4..0x63CF; 0x63D0 is a stop):
# set 0xC, set 0xD, stop. The vanilla intro has already set 0x1 and 0x1E2 (0x6304).
FLAGS_END = WAKE_END + 12
WAKE_ANIMATION = (
    0x62D4,
    0x6304,
)  # Jian's waking pose ops and the 90-frame wait after them
POSE_RESET = (0x6318, 0x6328)  # ops 0x38 + 0x40 that put Jian back in his normal pose
# Flags the run sets: 0x1 and 0x1E2 as the vanilla wake-up (0x1 = woken up, skips it on re-entry), and the
# two that send Jian to Lucia. Vanilla: Cherenkov's first lobby line sets LUCIA_LEFT (0x5F94), then Jack,
# seeing it, says "I just saw Lucia in Fountain Square" and sets LUCIA_AT_FOUNTAIN (0x6788); only with that
# flag does map 164's entry code keep the Lucia meeting (object 200, script 001 0x56E0). The run takes Jian
# past Cherenkov without talking, so Lucia never waited at the fountain (Jeff, 2026-10-07).
LUCIA_LEFT = 0xC
LUCIA_AT_FOUNTAIN = 0xD
STORY_FLAGS = (0x1, 0x1E2, LUCIA_LEFT, LUCIA_AT_FOUNTAIN)
# Cherenkov's lobby lines branch on flags (script 001 0x5F40): with LUCIA_AT_FOUNTAIN he says 0x0CA9 ("Get
# over to the Fountain Square, on the double!"), with only LUCIA_LEFT 0x0C78 ("Impressive! You know where to
# go!"), with neither his first line 0x0BD2, which repeats the wake-up joke. All three show our line.
CHERENKOV_LINES = (  # (u32 text offset of the message op, vanilla text)
    (0x5FBC, 0xCA9),
    (0x5FA8, 0xC78),
    (0x5F90, 0xBD2),
)
# Map 164 (Fountain Square) keeps the Lucia meeting only with LUCIA_AT_FOUNTAIN, which only Jack sets: now it
# checks LUCIA_LEFT, set by the run or by Cherenkov, so no one has to find Jack (and saves made after the run
# with Cherenkov talked to work too).
FOUNTAIN_ENTRY_FLAG = 0x56E8  # u16 flag in `if all of [0x0D] goto 0x56F0`
# A flag no script tests or sets (0x1D1..0x1E0 are free; 0x1E0 + n are destination flags)
RUN_FLAG = 0x1DF

MAP_HALL = 160
MAP_LOBBY = 155
MAP_STREET = 285
# Entrance ids from the door link records (map table +0x20): room -> hall 400, hall -> lobby 101,
# lobby -> street 0
HALL_FROM_ROOM = 400
LOBBY_FROM_HALL = 101
STREET_FROM_LOBBY = 0

# Directions (route data, op 0x46/0x49 facing, op 0x10 bits 13..15)
UP, UP_RIGHT, RIGHT, DOWN_RIGHT, DOWN, DOWN_LEFT, LEFT, UP_LEFT = range(8)
FACING_SHIFT = 13
SPEED_WALK = 0x1000
SPEED_RUN = 0x2000
ROUTE_END = (0xFFFF, 0, SPEED_WALK)
PLAYER = 0  # actor id of Jian in the movement ops

OP_STOP = 0x00
OP_WAIT = 0x01
OP_JUMP = 0x02
OP_IF_CMP_GOTO = 0x0D
OP_MSG = 0x0F
OP_GOTO_MAP = 0x10
OP_IF_NONE_SET_GOTO = 0x15
OP_SET_FLAG = 0x19
OP_CLEAR_FLAG = 0x1A
OP_FADE = 0x1D
OP_WAIT_FADE = 0x1E
OP_FIELD = 0x32  # handler func_0203e5c8, a switch on its first argument
FIELD_RELOAD = 1  # reload the current map (func_0201d92c); with RELOAD_WITH_HUD also the bottom screen
RELOAD_WITH_HUD = 1  # load flags 0xFFFFFF5F (0x100: HUD rebuilt), func_02071518 (field screens back), and the
# message window marked closed (ctx +0x29A = 0), as an event's end does (field states 0x4D..0x4F). The vanilla
# self-introduction's subroutine 0x7508 uses the same op. Without it the bottom screen keeps the last message box
# ("Right then!") during the walk, under the HUD once the map changes.
RESTORE_SLOT = "restore"
OP_ROUTE = 0x44
OP_WAIT_ROUTE = 0x45
GOTO_MAP_WARP = 2
CMP_VAR_EQ_IMM = 0x0002  # operand 0 from var (+0x204), operand 1 immediate, compare ==
VAR_MAP = 1  # map entry events: var 0 = 1, var 1 = the map id
MSG_BOX = 0x0001  # the flag the vanilla wake-up messages use
FADE_BOTH = 3
FADE_FULL = 0x80
FADE_DEFAULT_FRAMES = -1  # 30 frames
PAGE_BREAK = b"\xfe\xfd\xfd"  # end of page, then the layout the game's own messages use
TEXT_END = b"\xff"

# Dialogue (decided with Jeff 2026-10-06, revised 2026-10-07, docs/playtest-feedback.md item 2). Each
# tuple is the pages of one message. Jian's run lines are his inner voice: every line in the alternate
# color, no name tag, as the vanilla monologue.
WAKE_CALL = (
    "<Cherenkov>\nJian, get your lazy bones\nout of bed! Lucia's gonna\nskin you alive!",
)
WAKE_REPLY = ("<Jian>\nWha...? She left already?!",)
WAKE_PUSH = ("<Cherenkov>\nKeep this up and I'll rent\nyour room to someone useful!",)
WAKE_UP = ("<Jian>\nI'm up! I'm up!",)
# The room walk is short (about 2 s), so it gets one line; the hall walk (about 6 s) gets the most text.
RUN_ROOM = ("<I'm Jian. I'm a courier for>\n<Gad's Express.>",)
RUN_HALL = (
    (
        "<Lucia and I haven't been>\n<partners long, but she's>\n"
        "<great. Except for her temper.>\n\n"
        "<The job gets risky sometimes,>\n<but honestly, that's why I>\n<love it.>"
    ),
)
RUN_LOBBY = (
    (
        "<Well, that and getting to>\n<work with Lucia every day.>\n"
        "<If only we started later,>\n<I'd have it made!>"
    ),
)
CHERENKOV_LOBBY = (
    (
        "<Cherenkov>\nJian, what are you doing?!\nGet to {Fountain Square}!\n"
        "Don't keep Lucia waiting!"
    ),
)

# Legs of the run (direction, ticks, speed); one tick per frame. A tick moves speed / 0x1000 pixels:
# 1 px straight at SPEED_WALK, (0.875, 0.4375) px diagonally (the 2:1 screen diagonal, two buttons held).
# Jeff: walk, not run, so the asides can be read on the way; diagonals through doors, not zigzags.
# Each leg ends with our own map change, so the endpoints only need to look right.
ROOM_ROUTE = (  # (174,154) -> a step down from the bed, then straight over the doormat (x 230..250)
    (DOWN, 26, SPEED_WALK),
    (DOWN_RIGHT, 76, SPEED_WALK),
)  # -> (240,213), the mat's front edge
HALL_ROUTE = (  # (366,187) -> out of the door, along the corridor, up-left into the stairway
    (DOWN_RIGHT, 24, SPEED_WALK),
    (DOWN_LEFT, 292, SPEED_WALK),
    (UP_LEFT, 46, SPEED_WALK),
)  # -> (91,305), where the walked path changed maps (y 307..317)
LOBBY_ROUTE = (  # (96,215) -> front door (366,315), down and away from the counter at once
    (DOWN_RIGHT, 120, SPEED_WALK),
    (RIGHT, 70, SPEED_WALK),
    (DOWN_RIGHT, 108, SPEED_WALK),
)


@dataclass(frozen=True)
class Label:
    name: str


@dataclass(frozen=True)
class Ref:
    """A u32 file offset of a label (resolved at assembly)."""

    name: str


Item = bytes | Label | Ref


def _op(code: int, arg: int = 0) -> bytes:
    return struct.pack("<HH", code, arg & 0xFFFF)


def msg(label: str) -> list[Item]:
    return [_op(OP_MSG, MSG_BOX), Ref(label)]


def jump(label: str) -> list[Item]:
    return [_op(OP_JUMP), Ref(label)]


def if_map_goto(map_id: int, label: str) -> list[Item]:
    return [
        _op(OP_IF_CMP_GOTO, CMP_VAR_EQ_IMM),
        struct.pack("<II", VAR_MAP, map_id),
        Ref(label),
    ]


def if_flag_clear_goto(flag: int, target: int) -> bytes:
    return _op(OP_IF_NONE_SET_GOTO, 1) + struct.pack("<II", target, flag)


def run(route: str) -> list[Item]:
    return [_op(OP_ROUTE, PLAYER), Ref(route)]


def goto_map(map_id: int, entrance: int, facing: int) -> bytes:
    return _op(OP_GOTO_MAP, GOTO_MAP_WARP) + struct.pack(
        "<HH", facing << FACING_SHIFT | map_id, entrance
    )


def fade_in(screens: int = FADE_BOTH) -> bytes:
    return _op(OP_FADE, screens) + struct.pack("<hh", FADE_FULL, FADE_DEFAULT_FRAMES)


def route_data(legs: tuple[tuple[int, int, int], ...]) -> bytes:
    return b"".join(struct.pack("<HHH", *leg) for leg in (*legs, ROUTE_END))


def message(pages: tuple[str, ...]) -> bytes:
    return PAGE_BREAK.join(encode_text(page) for page in pages) + b"\xfe" + TEXT_END


def assemble(items: list[Item], base: int) -> tuple[bytes, dict[str, int]]:
    """Lay items out from file offset base; Refs become the u32 offsets of their Labels."""
    labels: dict[str, int] = {}
    at = base
    for item in items:
        if isinstance(item, Label):
            labels[item.name] = at
        else:
            at += 4 if isinstance(item, Ref) else len(item)
    out = bytearray()
    for item in items:
        if isinstance(item, Ref):
            out += struct.pack("<I", labels[item.name])
        elif isinstance(item, bytes):
            out += item
    return bytes(out), labels


def _walk_program() -> list[Item]:
    """The walk out of the inn and the story flags; no text. Each leg has an aside slot: a jump to the
    next op, which opening-text turns into a message op (both are 8 bytes)."""
    flags = b"".join(_op(OP_SET_FLAG, f) for f in (*STORY_FLAGS, RUN_FLAG))
    stop = _op(OP_STOP)
    return [
        Label("walk"),
        flags,
        Label(RESTORE_SLOT),
        _op(OP_FIELD, FIELD_RELOAD) + struct.pack("<HH", RELOAD_WITH_HUD, 0),
        *run("r_room"),
        *aside_slot("slot_room"),
        _op(OP_WAIT_ROUTE, PLAYER),
        goto_map(MAP_HALL, HALL_FROM_ROOM, DOWN_RIGHT),
        stop,
        Label("entry"),
        *if_map_goto(MAP_HALL, "hall"),
        *if_map_goto(MAP_LOBBY, "lobby"),
        _op(OP_JUMP) + struct.pack("<I", VANILLA_MAP_ENTRY),
        Label("hall"),
        if_flag_clear_goto(RUN_FLAG, VANILLA_MAP_ENTRY),
        fade_in(),
        *run("r_hall"),
        *aside_slot("slot_hall"),
        _op(OP_WAIT_ROUTE, PLAYER),
        goto_map(MAP_LOBBY, LOBBY_FROM_HALL, DOWN_RIGHT),
        stop,
        Label("lobby"),
        if_flag_clear_goto(RUN_FLAG, VANILLA_MAP_ENTRY),
        fade_in(),
        *run("r_lobby"),
        *aside_slot("slot_lobby"),
        _op(OP_WAIT_ROUTE, PLAYER),
        _op(OP_CLEAR_FLAG, RUN_FLAG),
        goto_map(MAP_STREET, STREET_FROM_LOBBY, DOWN_RIGHT),
        stop,
        Label("r_room"),
        route_data(ROOM_ROUTE),
        Label("r_hall"),
        route_data(HALL_ROUTE),
        Label("r_lobby"),
        route_data(LOBBY_ROUTE),
    ]


def aside_slot(name: str) -> list[Item]:
    """A jump to the next op: does nothing, and has a message op's size for opening-text to fill."""
    return [Label(name), *jump(name + "_end"), Label(name + "_end")]


def _text_program(vanilla: bytes, walk: int) -> list[Item]:
    """The new wake-up call, then on to opening-run's walk; and the text of the asides."""
    wake_pose = vanilla[WAKE_ANIMATION[0] : WAKE_ANIMATION[1]]
    pose_reset = vanilla[POSE_RESET[0] : POSE_RESET[1]]
    return [
        Label("wake"),
        *msg("t_wake_call"),
        wake_pose,
        *msg("t_wake_reply"),
        *msg("t_wake_push"),
        *msg("t_wake_up"),
        pose_reset,
        _op(OP_JUMP) + struct.pack("<I", walk),
        Label("t_wake_call"),
        message(WAKE_CALL),
        Label("t_wake_reply"),
        message(WAKE_REPLY),
        Label("t_wake_push"),
        message(WAKE_PUSH),
        Label("t_wake_up"),
        message(WAKE_UP),
        Label("t_run_room"),
        message(RUN_ROOM),
        Label("t_run_hall"),
        message(RUN_HALL),
        Label("t_run_lobby"),
        message(RUN_LOBBY),
        Label("t_cherenkov"),
        message(CHERENKOV_LOBBY),
    ]


def _align(offset: int) -> int:
    return -(-offset // ALIGN) * ALIGN


@dataclass(frozen=True)
class Layout:
    vanilla: bytes
    moved: tuple[DataPatch, ...]  # text-fixes' grown messages at the end of script 001
    end: int  # end of those messages
    code: bytes  # opening-run's program, from base
    labels: dict[str, int]

    @property
    def base(self) -> int:
        return _align(self.end)

    @property
    def code_end(self) -> int:
        return self.base + len(self.code)


def _layout() -> Layout:
    vanilla = decompress(read_archive(VANILLA_SCRIPTS.read_bytes())[SCRIPT])
    moved = tuple(
        p
        for p in text_patches()
        if p.entry == SCRIPT and not p.old and p.offset >= len(vanilla)
    )
    end = max((p.offset + len(p.new) for p in moved), default=len(vanilla))
    code, labels = assemble(_walk_program(), _align(end))
    return Layout(vanilla, moved, end, code, labels)


def opening_patches() -> tuple[DataPatch, ...]:
    """The vanilla wake-up and self-introduction play as written, then Jian walks out."""
    layout = _layout()
    patches = [
        DataPatch(
            ARCHIVE, SCRIPT, p.offset, b"", p.new, f"opening: same bytes as {p.note}"
        )
        for p in layout.moved
    ]
    patches += [
        DataPatch(
            ARCHIVE,
            SCRIPT,
            layout.end,
            b"",
            b"\x00" * (layout.base - layout.end) + layout.code,
            "opening: the walk out of the inn",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            WAKE_END,
            FLAG_OPS[:JUMP_SIZE],
            _op(OP_JUMP) + struct.pack("<I", layout.labels["walk"]),
            "opening: after 'Right then!' Jian walks out of the inn",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            ENTRY_DISPATCH_TARGET,
            struct.pack("<I", VANILLA_MAP_ENTRY),
            struct.pack("<I", layout.labels["entry"]),
            "opening: map entry events check the hall and lobby legs of the walk first",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            FOUNTAIN_ENTRY_FLAG,
            struct.pack("<H", LUCIA_AT_FOUNTAIN),
            struct.pack("<H", LUCIA_LEFT),
            "opening: Lucia waits at Fountain Square once Cherenkov has sent Jian there",
        ),
    ]
    return tuple(patches)


ASIDE_SLOTS = (
    ("slot_room", "t_run_room"),
    ("slot_hall", "t_run_hall"),
    ("slot_lobby", "t_run_lobby"),
)


def opening_text_patches() -> tuple[DataPatch, ...]:
    """On top of opening-run: the new wake-up call, the asides, and Cherenkov's line."""
    layout = _layout()
    vanilla = layout.vanilla
    base = _align(layout.code_end)
    code, labels = assemble(_text_program(vanilla, layout.labels["walk"]), base)
    patches = [
        DataPatch(
            ARCHIVE,
            SCRIPT,
            layout.code_end,
            b"",
            b"\x00" * (base - layout.code_end) + code,
            "opening text: the wake-up call and the asides",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            WAKE_MESSAGE_OP,
            vanilla[WAKE_MESSAGE_OP : WAKE_MESSAGE_OP + JUMP_SIZE],
            _op(OP_JUMP) + struct.pack("<I", labels["wake"]),
            "opening text: Cherenkov's wake-up call replaces the self-introduction",
        ),
    ]
    slots = [
        (slot, _op(OP_MSG, MSG_BOX) + struct.pack("<I", labels[text]), "an aside")
        for slot, text in ASIDE_SLOTS
    ]
    slots.append(
        (
            RESTORE_SLOT,
            _op(OP_JUMP) + struct.pack("<I", layout.labels[RESTORE_SLOT] + JUMP_SIZE),
            "no field restore: the aside replaces the box",
        )
    )
    for slot, new, what in slots:
        at = layout.labels[slot] - layout.base
        patches.append(
            DataPatch(
                ARCHIVE,
                SCRIPT,
                layout.labels[slot],
                layout.code[at : at + len(new)],
                new,
                f"opening text: {what} ({slot})",
            )
        )
    patches += [
        DataPatch(
            ARCHIVE,
            SCRIPT,
            site,
            struct.pack("<I", line),
            struct.pack("<I", labels["t_cherenkov"]),
            "opening text: Cherenkov sends Jian to Fountain Square",
        )
        for site, line in CHERENKOV_LINES
    ]
    return tuple(patches)


# Classic edition: the vanilla intro, then the flags that send Jian straight to Lucia (Jeff, 2026-10-09: "keep
# the flags that let me go straight to Lucia even on Classic"). Cherenkov and Jack keep their vanilla lines for
# that flag state, and Fountain Square's vanilla check (0xD) keeps Lucia there.
FLAG_OPS = (
    _op(OP_SET_FLAG, LUCIA_LEFT) + _op(OP_SET_FLAG, LUCIA_AT_FOUNTAIN) + _op(OP_STOP)
)


def opening_flags_patches() -> tuple[DataPatch, ...]:
    vanilla = decompress(read_archive(VANILLA_SCRIPTS.read_bytes())[SCRIPT])
    return (
        DataPatch(
            ARCHIVE,
            SCRIPT,
            WAKE_END,
            vanilla[WAKE_END:FLAGS_END],
            FLAG_OPS,
            "opening flags: after 'Right then!' Lucia has left and waits at Fountain Square",
        ),
    )


OPENING_FLAGS = Feature("opening-flags", opening_flags_patches())
# Retold edition: the walk-out and the flags (opening-run, after opening-flags and text-speed, the asides'
# auto-close cave), then opening-text, which must come after opening-run.
OPENING = Feature(
    "opening-run", tuple(opening_patches())
)  # needs text-speed (the auto-close cave)
OPENING_TEXT = Feature("opening-text", opening_text_patches())
