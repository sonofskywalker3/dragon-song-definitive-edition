"""Battle pacing package: the "Fast" part of the battle speed setting (design 7).

Normal is the original game. Fast applies the changes below, measured and chosen in
docs/re-battle-pacing.md (candidates P2 to P12). Fastest is Fast plus the game's own animation
acceleration (feat_battle_speed.py). Every change asks the setting in cave_speed_state at run time,
so Normal stays exactly vanilla.

- P2: fixed-length action-script steps and moves (enemy lunges, Jian's leaps) count two frames per
  frame: the step counter (battler +0xCE, func_02031514) and the move counter (+0xB4,
  func_0202f230). Steps end on "counter >= duration" and the mover clamps to the duration, so they
  stay in step and cannot overshoot.
- P3: the white flash on a killed enemy holds 20 frames instead of 60, and the fade after it takes 16
  frames instead of 32: its counter (+0xD0, round state 0xD) counts down two per frame from the same
  start, and the blend is computed from the counter, so it follows the same curve twice as fast.
- P7: the camera turns to each actor (round state 5) and back at the end of a round (func_020297d4
  case 8) in 8 frames instead of 16 (func_02028540 duration).
- Victory: each battler's pose holds 30 frames instead of 60 after its animation (func_02067698, +0xC4),
  and after the EXP pour the wait before the result page is 15 + 20 frames instead of 30 + 40
  (+0x134 set in func_02052ac4, +0x130 set when the pour ends).
- P4: the back-row enemy flies into a freed front slot in 32 frames instead of 64 (its counter counts
  two per frame; the position curve depends only on the counter, so it ends in the same place).
- P5: damage numbers hold 24 frames after rising instead of 60.
- P6: the round does not wait for damage numbers before the next actor; they finish over its start.
- P10: the battle intro runs twice as fast: both enemy-row fades, each column popping in and the hold
  after the enemies appear (func_020297d4 states 4 and 5, counter work +0xD0; every limit is even).
- P11: the EXP pour advances every frame instead of every fourth (about 64 frames instead of 256), and
  A is checked every frame, so a tap always skips it (vanilla only sees A on one frame in four).
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
    (
        0x0202D67C,
        0xE3A02010,
        "r2",
        0x10,
        8,
        "cave_pace_camera_actor",
        "camera turns to each actor in 8 frames",
    ),
    (
        0x0202A744,
        0xE3A02010,
        "r2",
        0x10,
        8,
        "cave_pace_camera_end",
        "camera turns back at round end in 8 frames",
    ),
    (
        0x020676CC,
        0xE3A0B03C,
        "fp",
        0x3C,
        30,
        "cave_pace_pose_hold",
        "victory poses hold 30 frames",
    ),
    (
        0x02052BFC,
        0xE3A0201E,
        "r2",
        0x1E,
        15,
        "cave_pace_levelup_wait",
        "level-up wait 15 frames",
    ),
    (
        0x0202AA68,
        0xE3A03028,
        "r3",
        0x28,
        20,
        "cave_pace_levelup_hold",
        "level-up hold 20 frames",
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

INTRO_COUNTER_ADDS = (  # func_020297d4: add r1, r1, #1 (intro counter work +0xD0)
    (0x02029DD4, 0xE2811001, "first enemy row fades in faster"),
    (0x02029ECC, 0xE2811001, "second enemy row fades in faster"),
    (0x0202A030, 0xE2811001, "enemy columns pop in faster"),
    (0x0202A11C, 0xE2811001, "shorter hold after the enemies appear"),
)
KILL_FADE_SUB = (
    0x0202DED0,
    0xE2400001,
)  # func_0202d22c state 0xD: sub r0, r0, #1 (kill fade counter +0xD0)
POUR_GATE = (
    0x02052C70,
    0xE2110003,
)  # func_02052c2c: ands r0, r1, #3 (pour every fourth frame)


def count_asm(reg: str) -> str:
    """`reg` + 1 on Normal, + PACE_STEP otherwise. Keeps every other register and the flags."""
    scratch = "r2" if reg == "r1" else "r1"
    return f"""
    push  {{{scratch}, lr}}
    mrs   {scratch}, cpsr
    push  {{{scratch}}}
    ldr   {scratch}, count_state
    ldrb  {scratch}, [{scratch}]
    cmp   {scratch}, #0
    addeq {reg}, {reg}, #1
    addne {reg}, {reg}, #{PACE_STEP}
    pop   {{{scratch}}}
    msr   cpsr_f, {scratch}
    pop   {{{scratch}, pc}}
count_state:
    .word ${{cave_speed_state}}
"""


COUNT_ASM = count_asm("r0")

# Replaces `sub r0, r0, #1` of the kill fade counter: - PACE_STEP on Fast and Fastest. The flags are
# not read before the next compare, so they need not be kept.
FADE_ASM = f"""
    push  {{r1, lr}}
    ldr   r1, fade_state
    ldrb  r1, [r1]
    cmp   r1, #0
    subeq r0, r0, #1
    subne r0, r0, #{PACE_STEP}
    pop   {{r1, pc}}
fade_state:
    .word ${{cave_speed_state}}
"""

# Replaces `ands r0, r1, #3` (r1 = pour frame counter; the next instructions return unless Z is set):
# on Fast and Fastest r0 = 0 with Z set, so the pour step and its A check run every frame.
POUR_ASM = """
    ldr   r0, pour_state
    ldrb  r0, [r0]
    cmp   r0, #0
    bne   pour_fast
    ands  r0, r1, #3
    bx    lr
pour_fast:
    movs  r0, #0
    bx    lr
pour_state:
    .word ${cave_speed_state}
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
        CaveCode("cave_pace_count_r1", count_asm("r1"), "count frames faster (r1)"),
        *(
            _call(addr, old, "bl", "cave_pace_count_r1", note)
            for addr, old, note in INTRO_COUNTER_ADDS
        ),
        CaveCode("cave_pace_fade", FADE_ASM, "kill fade twice as fast on Fast"),
        _call(*KILL_FADE_SUB, "bl", "cave_pace_fade", "kill fade 16 frames"),
        CaveCode("cave_pace_pour", POUR_ASM, "EXP pour every frame, A always skips"),
        _call(*POUR_GATE, "bl", "cave_pace_pour", "EXP pour every frame, A skips"),
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
