"""Battle pacing package: the "Fast" part of the battle speed setting (design 7).

Normal is the original game. Fast applies the changes below, measured and chosen in
docs/re-battle-pacing.md (candidates P2 to P12). Fastest is Fast plus the game's own animation
acceleration (feat_battle_speed.py). Every change asks the setting in cave_speed_state at run time,
so Normal stays exactly vanilla.

- P2: fixed-length action-script steps and moves (enemy lunges, Jian's leaps) count two frames per
  frame: the step counter (battler +0xCE, func_02031514) and the move counter (+0xB4,
  func_0202f230). Steps end on "counter >= duration" and the mover clamps to the duration, so they
  stay in step and cannot overshoot.
- P3 (part): the white flash on a killed enemy holds 20 frames instead of 60 (the fade after it is
  unchanged: its blend is computed from the start value, so a shorter start would jump).
- P4: the back-row enemy flies into a freed front slot in 32 frames instead of 64 (its counter counts
  two per frame; the position curve depends only on the counter, so it ends in the same place).
- P5: damage numbers hold 24 frames after rising instead of 60.
- P6: the round does not wait for damage numbers before the next actor; they finish over its start.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

PACE_STEP = 2  # frames counted per frame on Fast and Fastest
STEP_COUNTER_ADD = (
    0x0203153C,
    0xE2800001,
)  # func_02031514: add r0, r0, #1 (step counter)
MOVE_COUNTER_ADDS = (  # func_0202f230: conditional add r0, r0, #1 (move counter)
    (0x0202F258, 0x02800001, "bleq"),
    (0x0202F270, 0x12800001, "blne"),
)

REFILL_COUNTER_ADD = (
    0x0205393C,
    0xE2800001,
)  # func_02053918: add r0, r0, #1 (refill counter)
NUMBER_WAIT_CALL = (
    0x0202DF84,
    0xEBFFF917,
)  # round state 0xE: bl func_0202c3e8 (numbers still up?)
NUMBERS_ACTIVE = 0x0202C3E8
# (address, original word, register, vanilla value, Fast value, label, note)
CONSTANTS = (
    (
        0x0202C1F8,
        0xE3A0203C,
        "r2",
        0x3C,
        24,
        "cave_pace_number_hold",
        "damage numbers hold 24 frames",
    ),
    (
        0x02053338,
        0xE3A0603C,
        "r6",
        0x3C,
        20,
        "cave_pace_kill_hold",
        "kill flash holds 20 frames",
    ),
)


def pick_asm(reg: str, normal: int, fast: int) -> str:
    """`reg` = normal on Normal, fast otherwise. Keeps every other register; flags change."""
    return f"""
    push  {{r0, lr}}
    ldr   r0, pick_state
    ldrb  r0, [r0]
    cmp   r0, #0
    moveq {reg}, #{normal:#x}
    movne {reg}, #{fast:#x}
    pop   {{r0, pc}}
pick_state:
    .word ${{cave_speed_state}}
"""


# Replaces `bl func_0202c3e8` in round state 0xE: r0 = 0 (no numbers to wait for) on Fast and Fastest.
NUMBER_WAIT_ASM = f"""
    ldr   r0, nw_state
    ldrb  r0, [r0]
    cmp   r0, #0
    movne r0, #0
    bxne  lr
    b     {NUMBERS_ACTIVE:#x}
nw_state:
    .word ${{cave_speed_state}}
"""

# r0 = counter -> r0 + 1 on Normal, + PACE_STEP otherwise. Keeps every other register and the flags.
COUNT_ASM = f"""
    push  {{r1, lr}}
    mrs   r1, cpsr
    push  {{r1}}
    ldr   r1, pace_state
    ldrb  r1, [r1]
    cmp   r1, #0
    addeq r0, r0, #1
    addne r0, r0, #{PACE_STEP}
    pop   {{r1}}
    msr   cpsr_f, r1
    pop   {{r1, pc}}
pace_state:
    .word ${{cave_speed_state}}
"""


def _call(addr: int, old: int, op: str, cave: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, f"{op} ${{{cave}}}", note)


BATTLE_PACE = Feature(
    "battle-pace",
    (
        CaveCode("cave_pace_count", COUNT_ASM, "count frames faster on Fast"),
        _call(*STEP_COUNTER_ADD, "bl", "cave_pace_count", "action steps run faster"),
        *(
            _call(addr, old, op, "cave_pace_count", "moves run faster")
            for addr, old, op in MOVE_COUNTER_ADDS
        ),
        _call(
            *REFILL_COUNTER_ADD, "bl", "cave_pace_count", "front-row refill runs faster"
        ),
        CaveCode(
            "cave_pace_number_wait", NUMBER_WAIT_ASM, "no wait for damage numbers"
        ),
        _call(
            *NUMBER_WAIT_CALL,
            "bl",
            "cave_pace_number_wait",
            "no wait for damage numbers",
        ),
        *(
            item
            for addr, old, reg, normal, fast, label, note in CONSTANTS
            for item in (
                CaveCode(label, pick_asm(reg, normal, fast), note),
                _call(addr, old, "bl", label, note),
            )
        ),
    ),
)
