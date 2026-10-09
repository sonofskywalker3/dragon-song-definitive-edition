"""Shorter enemy action scripts on Fast and Faster (docs/plan-enemy-attacks.md, levers 1 and 3).

Enemy actions run 16-byte step lists (docs/re-enemy-attacks.md 3). func_02068034 stores the chosen list in
the actor (+0xC8) in round state 5; the hook here runs right after it (the `bl func_02068034` in
func_02068890, the enemy branch only) and, unless the speed setting is Normal, swaps a known list for a
cut copy kept in ITCM. Normal keeps the original lists to the byte; party actions never pass this branch.

Move semantics (func_0202fdf0 / func_020303e8, confirmed in code): a step with 0x200000 stores the start
(+0x50) and the target (+0x5C, 14/16 of the way to the target battler). A move step (0x7000 kind, duration
= its frame count, +0xB0) heads for an absolute point: the target, or home (+0x50) with 0x8000. Only 0x10000
without 0x20000 makes it a partial hop (current + a quarter of start-to-target), which is how the
four-hop script 0x02095FC0 walks in. One move without 0x10000 therefore lands on the same contact point the
fourth hop reached (its 0x31016 also aims at the absolute target), and one move with 0x8000 lands home.

Steps keep their flags except where a cut says otherwise; the hit step (0x40/0x80/0xC1), the last-step bit,
end and wait-for-effects bits (0x20, 0x80000000, 0x2000000) are never dropped, so damage, flinch, sound and
the interrupt path (-2 from a 0x80 step) stay where they were.

Two features share the hook and so cannot be built together (the second fails its patch check):
- enemy-short-moves (lever 1): movement only. Four hops in and out become one, the 60-frame glides 20, the
  lunge's pause and travel shorter. Every animation step is kept whole.
- enemy-quick-steps (lever 3): lever 1 plus caps: idle, landing, wind-up and cast-pose animation waits become
  short fixed steps (the animation starts and is cut), the landing animation between a hop and the attack is
  dropped, and long fixed pauses are cut.
"""

import struct
from dataclasses import dataclass
from pathlib import Path

from dsde.patching import ARM9_BASE, AsmPatch, CaveCode, Feature

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARM9_BIN = PROJECT_ROOT / "extract" / "arm9" / "arm9.bin"

SETUP_CALL = (
    0x020688A4  # func_02068890: bl func_02068034 (enemy action setup), r0 = the actor
)
SETUP_CALL_WORD = 0xEBFFFDE2
ACTION_SETUP = 0x02068034
SCRIPT_FIELD = 0xC8
NORMAL = 0
STEP_SIZE = 0x10
LAST = 0x80000000
KIND_MASK = 3
KIND_ANIM = 1
KIND_FIXED = 2
MOVING = 0x10  # the mover advances while the current step has it
PARTIAL_HOP = 0x10000  # move a quarter of the way (with 0x20000 clear)


@dataclass(frozen=True)
class Cut:
    """One step of a cut script: a copy of step `src` of the original, with optional overrides."""

    src: int
    flags: int | None = None
    frames: int | None = None
    last: bool = False


def keep(*indexes: int) -> tuple[Cut, ...]:
    return tuple(Cut(i) for i in indexes)


def land(src: int) -> Cut:
    """Cap the settle animation after a hop home, keeping the moving bit (0x10) so a hop that is still in
    the air when the step starts (a lag frame after an interrupt) finishes instead of freezing mid-arc
    (the mover only counts while the current step has 0x10)."""
    return Cut(src, frames=LAND, flags=-2)


def cap(src: int, frames: int, last: bool = False) -> Cut:
    """Turn an animation wait into a fixed step of `frames` (Normal frames; Fast counts two per frame)."""
    return Cut(src, frames=frames, last=last, flags=-1)


def read_script(data: bytes, script: int) -> list[bytes]:
    steps = []
    offset = script - ARM9_BASE
    while True:
        raw = data[offset : offset + STEP_SIZE]
        steps.append(raw)
        if struct.unpack_from("<I", raw)[0] & LAST:
            return steps
        offset += STEP_SIZE


def build_steps(data: bytes, script: int, cuts: tuple[Cut, ...]) -> list[bytes]:
    """The cut script's bytes: last-step bit only on the final step."""
    original = read_script(data, script)
    out = []
    for n, cut in enumerate(cuts):
        raw = bytearray(original[cut.src])
        flags = struct.unpack_from("<I", raw)[0]
        if cut.flags == -1:  # cap: animation wait -> fixed
            flags = (flags & ~KIND_MASK) | KIND_FIXED
        elif cut.flags == -2:  # land: cap that keeps the mover running
            flags = (flags & ~KIND_MASK) | KIND_FIXED | MOVING
        elif cut.flags is not None:
            flags = cut.flags
        flags &= ~LAST
        if n == len(cuts) - 1:
            flags |= LAST
        struct.pack_into("<I", raw, 0, flags)
        if cut.frames is not None:
            struct.pack_into("<h", raw, 0xC, cut.frames)
        out.append(bytes(raw))
    return out


def steps_asm(steps: list[bytes]) -> str:
    words = [w for raw in steps for w in struct.unpack("<4I", raw)]
    return "\n".join(f"    .word {w:#010x}" for w in words)


# ---- lever 1: movement only ----------------------------------------------------------------------------
HOP_IN_FULL = (
    0x00031016  # the fourth hop in: arc 0x20 (0x10000) to the absolute target (0x20000)
)
HOP_OUT_FULL = 0x00039016  # the fourth hop home (0x8000); arc 0x40 left the screen top
GLIDE_FRAMES = 20  # was 60 (0x020955E0, 0x02095820)
LUNGE_PAUSE = 2  # was 8
LUNGE_TRAVEL = 16  # was 30
HOP_FRAMES = 8  # one hop covering four hops' distance

LUNGE = (
    Cut(0, frames=LUNGE_PAUSE),
    Cut(1, frames=LUNGE_TRAVEL),
    *keep(2, 3),
    Cut(4, frames=LUNGE_TRAVEL),
)
SHORT_MOVES: dict[int, tuple[Cut, ...]] = {
    # Blob, Ice Mongrel: four hops (anim, move 4, land 4) each way -> one
    0x02095FC0: (
        Cut(0),
        Cut(1, flags=HOP_IN_FULL, frames=HOP_FRAMES),
        Cut(2),
        *keep(12, 13, 14, 15),
        Cut(16, flags=HOP_OUT_FULL, frames=HOP_FRAMES),
        Cut(17),
        Cut(27),
    ),
    # slow glide in and out (Dagon, Shaitan, Phantom, Ghoula, Morus) and Morus' steal
    0x020955E0: (
        Cut(0),
        Cut(1, frames=GLIDE_FRAMES),
        *keep(2, 3, 4, 5),
        Cut(6, frames=GLIDE_FRAMES),
        Cut(7),
    ),
    0x02095820: (
        Cut(0),
        Cut(1, frames=GLIDE_FRAMES),
        *keep(2, 3, 4, 5, 6, 7),
        Cut(8, frames=GLIDE_FRAMES),
        Cut(9),
    ),
    0x020952E4: LUNGE,
    0x02095334: LUNGE,
    0x02095384: LUNGE,
}

# ---- lever 3: lever 1 plus animation caps and shorter pauses ------------------------------------------
PREP = 8  # crouch before a hop or glide (anim seq 0)
LAND = 8  # landing / settle at the end
WINDUP = 16  # attack wind-up (anim slot 0 seq 0)
CAST_POSE = 24  # cast pose before the spell effect
PAUSE = 16  # long fixed pauses inside skill scripts

HOP_QUICK = (  # 0x02095780 family: crouch, hop, (landing dropped), wind-up, hit, hop home
    cap(0, PREP),
    *keep(1, 2),
    cap(4, WINDUP),
    Cut(5),
    *keep(7, 8),
    land(9),
)
QUICK_STEPS: dict[int, tuple[Cut, ...]] = {
    0x02095FC0: (
        cap(0, PREP),
        Cut(1, flags=HOP_IN_FULL, frames=HOP_FRAMES),
        Cut(2),
        cap(13, WINDUP),
        Cut(14),
        Cut(16, flags=HOP_OUT_FULL, frames=HOP_FRAMES),
        Cut(17),
        land(27),
    ),
    0x02095780: HOP_QUICK,
    # two hits (0x41 then 0xC1): Deuce, Orcus, Gideon
    0x02095BB0: (
        cap(0, PREP),
        *keep(1, 2),
        cap(4, WINDUP),
        Cut(5),
        cap(6, WINDUP),
        Cut(7),
        *keep(9, 10),
        land(11),
    ),
    # Zethos x8010: hits 0x41, 0x41, 0xC1
    0x02095DF0: (
        cap(0, PREP),
        *keep(1, 2),
        cap(4, WINDUP),
        *keep(5, 6),
        cap(7, WINDUP),
        Cut(8),
        *keep(10, 11),
        land(12),
    ),
    # Dark Jian: hits 0x41, 0x41, 0xC1
    0x02095C70: (
        cap(0, PREP),
        *keep(1, 2),
        cap(4, WINDUP),
        *keep(5, 6, 7),
        *keep(9, 10),
        land(11),
    ),
    # Zethos skill 21: hop in, two 30-frame effect pauses, hop home
    0x02095D30: (
        cap(0, PREP),
        *keep(1, 2),
        cap(4, CAST_POSE),
        Cut(5, frames=PAUSE),
        Cut(6, frames=PAUSE),
        Cut(7),
        *keep(9, 10),
        land(11),
    ),
    0x020955E0: (
        cap(0, PREP),
        Cut(1, frames=GLIDE_FRAMES),
        cap(2, PREP),
        cap(3, WINDUP),
        Cut(4),
        cap(5, PREP),
        Cut(6, frames=GLIDE_FRAMES),
        land(7),
    ),
    0x02095820: (
        cap(0, PREP),
        Cut(1, frames=GLIDE_FRAMES),
        cap(2, PREP),
        cap(3, WINDUP),
        Cut(4),
        cap(5, WINDUP),
        Cut(6),
        cap(7, PREP),
        Cut(8, frames=GLIDE_FRAMES),
        land(9),
    ),
    0x020952E4: (
        Cut(0, frames=LUNGE_PAUSE),
        Cut(1, frames=LUNGE_TRAVEL),
        cap(2, WINDUP),
        Cut(3),
        Cut(4, frames=LUNGE_TRAVEL),
    ),
    0x02095334: (
        Cut(0, frames=LUNGE_PAUSE),
        Cut(1, frames=LUNGE_TRAVEL),
        cap(2, WINDUP),
        Cut(3),
        Cut(4, frames=LUNGE_TRAVEL),
    ),
    0x02095384: (
        Cut(0, frames=LUNGE_PAUSE),
        Cut(1, frames=LUNGE_TRAVEL),
        cap(2, WINDUP),
        Cut(3),
        Cut(4, frames=LUNGE_TRAVEL),
    ),
    # casts: pose capped; the release step still waits for its animation and the spell effect
    0x02094E84: (cap(0, CAST_POSE), Cut(1)),
    0x02094E64: (cap(0, CAST_POSE), Cut(1)),
    0x02094F44: (cap(0, CAST_POSE), Cut(1, frames=PAUSE), Cut(2)),
    0x02095294: (
        cap(0, CAST_POSE),
        Cut(1, frames=PAUSE),
        Cut(2, frames=PAUSE),
        Cut(3, frames=PAUSE),
        Cut(4),
    ),
    0x020950C4: (cap(0, CAST_POSE), Cut(1, frames=2 * PAUSE), Cut(2)),
    0x020951B4: (cap(0, CAST_POSE), Cut(1, frames=PAUSE), Cut(2, frames=PAUSE), Cut(3)),
    0x020951F4: (cap(0, CAST_POSE), Cut(1, frames=PAUSE), *keep(2, 3, 4)),
    0x02095660: (
        cap(0, CAST_POSE),
        Cut(1, frames=PAUSE),
        *(Cut(i, frames=PAUSE // 2) for i in range(2, 8)),
        Cut(8),
    ),
    0x02094FA4: (cap(0, WINDUP), Cut(1, frames=PAUSE), Cut(2)),
}


def label(prefix: str, script: int) -> str:
    return f"cave_{prefix}_{script:08x}"


def swap_asm(table: str) -> str:
    """Replaces `bl func_02068034` (r0 = actor). After the setup, on Fast and Faster, looks the actor's
    script up in the (original, cut) table and swaps it in. Keeps r4..r11."""
    return f"""
    push  {{r4, lr}}
    mov   r4, r0
    bl    {ACTION_SETUP:#x}
    ldr   r0, sw_state
    ldrb  r0, [r0]
    cmp   r0, #{NORMAL}
    popeq {{r4, pc}}
    ldr   r1, [r4, #{SCRIPT_FIELD:#x}]
    ldr   r2, sw_table
sw_next:
    ldr   r3, [r2], #8
    cmp   r3, #0
    popeq {{r4, pc}}
    cmp   r3, r1
    bne   sw_next
    ldr   r3, [r2, #-4]
    str   r3, [r4, #{SCRIPT_FIELD:#x}]
    pop   {{r4, pc}}
sw_state:
    .word ${{cave_speed_state}}
sw_table:
    .word ${{{table}}}
"""


def cut_scripts(cuts: dict[int, tuple[Cut, ...]]) -> dict[int, list[bytes]]:
    data = ARM9_BIN.read_bytes()
    return {script: build_steps(data, script, c) for script, c in cuts.items()}


def swap_feature(name: str, prefix: str, cuts: dict[int, tuple[Cut, ...]]) -> Feature:
    scripts = cut_scripts(cuts)
    table = f"cave_{prefix}_table"
    table_asm = "\n".join(
        f"    .word {script:#010x}, ${{{label(prefix, script)}}}" for script in scripts
    )
    return Feature(
        name,
        (
            *(
                CaveCode(label(prefix, s), steps_asm(steps), f"cut script {s:#010x}")
                for s, steps in scripts.items()
            ),
            CaveCode(table, table_asm + "\n    .word 0, 0", "cut script table"),
            CaveCode(f"cave_{prefix}_swap", swap_asm(table), "swap in cut scripts"),
            AsmPatch(
                SETUP_CALL,
                SETUP_CALL + 4,
                SETUP_CALL_WORD,
                SETUP_CALL_WORD,
                f"bl ${{cave_{prefix}_swap}}",
                "enemy action scripts: cut copies on Fast and Faster",
            ),
        ),
    )


ENEMY_SHORT_MOVES = swap_feature("enemy-short-moves", "esm", SHORT_MOVES)
ENEMY_QUICK_STEPS = swap_feature("enemy-quick-steps", "eqs", QUICK_STEPS)
# label prefix -> cuts, for the recorder (dsde.enemy_anims_run) to decode cut scripts in ITCM
CUT_SETS = {"esm": SHORT_MOVES, "eqs": QUICK_STEPS}
