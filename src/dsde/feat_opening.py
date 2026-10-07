"""Opening: Jian is woken from downstairs and runs out of the inn (playtest feedback item 2).

Final dialogue; mechanics in docs/re-opening.md. Script 001's wake-up in Jian's room (map 163)
jumps to new code appended to the script: an off-screen wake-up call, then a scripted run. The run
crosses three maps, and a script cannot survive a map change (op 0x10 ends it), so each leg ends with
a map change and the next leg starts from the new map's entry event: the script's entry dispatcher
(event type 1, var 1 = map id) is pointed at a new block that sends the hall (160) and the lobby (155)
to their legs while RUN_FLAG is set. The last leg clears the flag and leaves for the street (285),
where the player gets control.

Appended bytes go after the messages text-edits moves to the end of script 001. This feature writes
those same bytes too, so the layout is the same whether or not text-edits is in the build.
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
WAKE_ANIMATION = (
    0x62D4,
    0x6304,
)  # Jian's waking pose ops and the 90-frame wait after them
POSE_RESET = (0x6318, 0x6328)  # ops 0x38 + 0x40 that put Jian back in his normal pose
# Flags the run sets: 0x1 and 0x1E2 as the vanilla wake-up (0x1 = woken up, skips it on re-entry), and
# LUCIA_AT_FOUNTAIN, which vanilla sets after Cherenkov's first lobby line (0x5F94). The run takes Jian past
# Cherenkov without talking, so without it Lucia never waited at Fountain Square (Jeff, 2026-10-07). Jack
# tests it too ("I just saw Lucia in Fountain Square", 0x6764).
LUCIA_AT_FOUNTAIN = 0xC
STORY_FLAGS = (0x1, 0x1E2, LUCIA_AT_FOUNTAIN)
# Cherenkov's lobby lines branch on flags; with LUCIA_AT_FOUNTAIN set he says "Impressive! You know where to
# go!" (0x0C78), which makes no sense after the run, so that message op shows our Fountain Square line.
CHERENKOV_AFTER_RUN_LINE = (
    0x5FA8  # u32 text offset of the LUCIA_AT_FOUNTAIN branch's message op
)
CHERENKOV_AFTER_RUN_TEXT = 0xC78
# Without LUCIA_AT_FOUNTAIN (a save made after the run before this fix) he gives his first line, which
# repeats the wake-up joke: that one shows our line too, and it sets LUCIA_AT_FOUNTAIN as before.
CHERENKOV_FIRST_LINE = 0x5F90
CHERENKOV_FIRST_TEXT = 0xBD2
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


def fade_in() -> bytes:
    return _op(OP_FADE, FADE_BOTH) + struct.pack("<hh", FADE_FULL, FADE_DEFAULT_FRAMES)


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


def _program(vanilla: bytes) -> list[Item]:
    wake_pose = vanilla[WAKE_ANIMATION[0] : WAKE_ANIMATION[1]]
    pose_reset = vanilla[POSE_RESET[0] : POSE_RESET[1]]
    flags = b"".join(_op(OP_SET_FLAG, f) for f in (*STORY_FLAGS, RUN_FLAG))
    stop = _op(OP_STOP)
    return [
        Label("wake"),
        *msg("t_wake_call"),
        wake_pose,
        *msg("t_wake_reply"),
        *msg("t_wake_push"),
        *msg("t_wake_up"),
        flags,
        pose_reset,
        *run("r_room"),
        *msg("t_run_room"),
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
        *msg("t_run_hall"),
        _op(OP_WAIT_ROUTE, PLAYER),
        goto_map(MAP_LOBBY, LOBBY_FROM_HALL, DOWN_RIGHT),
        stop,
        Label("lobby"),
        if_flag_clear_goto(RUN_FLAG, VANILLA_MAP_ENTRY),
        fade_in(),
        *run("r_lobby"),
        *msg("t_run_lobby"),
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


def opening_patches() -> tuple[DataPatch, ...]:
    vanilla = decompress(read_archive(VANILLA_SCRIPTS.read_bytes())[SCRIPT])
    moved = [
        p
        for p in text_patches()
        if p.entry == SCRIPT and not p.old and p.offset >= len(vanilla)
    ]
    end = max((p.offset + len(p.new) for p in moved), default=len(vanilla))
    base = -(-end // ALIGN) * ALIGN
    code, labels = assemble(_program(vanilla), base)
    gap = b"\x00" * (base - end)
    patches = [
        DataPatch(
            ARCHIVE, SCRIPT, p.offset, b"", p.new, f"opening: same bytes as {p.note}"
        )
        for p in moved
    ]
    patches += [
        DataPatch(ARCHIVE, SCRIPT, end, b"", gap + code, "opening: new code"),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            WAKE_MESSAGE_OP,
            vanilla[WAKE_MESSAGE_OP : WAKE_MESSAGE_OP + 8],
            _op(OP_JUMP) + struct.pack("<I", labels["wake"]),
            "opening: wake-up jumps to the new wake-up call and run",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            ENTRY_DISPATCH_TARGET,
            struct.pack("<I", VANILLA_MAP_ENTRY),
            struct.pack("<I", labels["entry"]),
            "opening: map entry events check the hall and lobby legs of the run first",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            CHERENKOV_AFTER_RUN_LINE,
            struct.pack("<I", CHERENKOV_AFTER_RUN_TEXT),
            struct.pack("<I", labels["t_cherenkov"]),
            "opening: after the run Cherenkov sends Jian to Fountain Square",
        ),
        DataPatch(
            ARCHIVE,
            SCRIPT,
            CHERENKOV_FIRST_LINE,
            struct.pack("<I", CHERENKOV_FIRST_TEXT),
            struct.pack("<I", labels["t_cherenkov"]),
            "opening: Cherenkov's first lobby line sends Jian to Fountain Square",
        ),
    ]
    return tuple(patches)


OPENING = Feature("opening-run", opening_patches())
