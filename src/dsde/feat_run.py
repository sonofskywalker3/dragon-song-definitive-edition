"""Field running (design 1): no HP cost, and a timed run with a cooldown. See docs/re-field-battle.md section 1."""

from dsde.patching import AsmPatch, CaveCode, Feature, Patch

# Field running, see docs/re-field-battle.md section 1. The run state lives in the player's
# 8-bit counter at +0x40 bits 5..12 (the old HP drain counter): 0 = ready, 1..RUN_TICKS =
# running, then cooldown until RUN_TICKS + COOLDOWN_TICKS. One tick = 2 frames at 60 fps.
# As in Lunar 1 and 2, holding B runs once: after the cooldown the state waits at its end until B is
# released, so running again needs a fresh press.
FRAMES_PER_TICK = 2
RUN_TICKS = 90  # 3 seconds
COOLDOWN_TICKS = 90  # 3 seconds
FRAME_COUNTER = 0x020B05BC
FIELD_MAP = 0x020B6BE4  # s16 current map id (field state block)
TIMED_RUN_BODY_ADDR = 0x020251AC
TIMED_RUN_EXIT = 0x02024C58
DPAD_MASK = 0xF0
# Bits 5..12 (0x1FE0) is not an ARM immediate, so it is cleared in two parts
COUNTER_MASK_HIGH = 0x1FC0
COUNTER_MASK_LOW = 0x20

# Part 1 sits in the freed too-tired check block: load the run state, then jump to part 2.
TIMED_RUN_ASM_ENTRY = f"""
    ldr   r1, [r2]
    mov   r3, r1, lsl #19
    mov   r3, r3, lsr #24
    ldr   r0, [sp, #8]
    ldr   r12, frame_counter
    ldrh  r12, [r12]
    bl    ${{cave_run_area}}
    b     {TIMED_RUN_BODY_ADDR:#x}
frame_counter:
    .word {FRAME_COUNTER:#x}
"""

# A new area starts with the run ready (Jeff, 2026-10-07): running through a door used to carry the 3 s
# cooldown into the next map. In: r3 = run state; out: r3 = 0 on the first frame of a different map.
RUN_AREA_ASM = f"""
    push  {{r0, r1, r12}}
    ldr   r0, area_map
    ldrh  r0, [r0]
    ldr   r1, area_last
    ldrh  r12, [r1]
    cmp   r0, r12
    strhne r0, [r1]
    movne r3, #0
    pop   {{r0, r1, r12}}
    bx    lr
area_map:
    .word {FIELD_MAP:#x}
area_last:
    .word ${{cave_run_area_last}}
"""

# Part 2 sits in the freed HP drain block. In: r0 = B held, r1 = player flags, r2 = &flags,
# r3 = run state, r5 = held keys, r12 = frame counter.
TIMED_RUN_ASM_BODY = f"""
    cmp   r3, #0
    bne   active
    cmp   r0, #0
    tstne r5, #{DPAD_MASK:#x}
    movne r3, #1
    b     store
active:
    cmp   r3, #{RUN_TICKS}
    bhi   tick
    cmp   r0, #0
    moveq r3, #{RUN_TICKS + 1}
    beq   store
tick:
    tst   r12, #{FRAMES_PER_TICK - 1}
    addeq r3, r3, #1
    cmp   r3, #{RUN_TICKS + COOLDOWN_TICKS}
    bls   store
    cmp   r0, #0
    movne r3, #{RUN_TICKS + COOLDOWN_TICKS}
    moveq r3, #0
store:
    bic   r1, r1, #{COUNTER_MASK_HIGH:#x}
    bic   r1, r1, #{COUNTER_MASK_LOW:#x}
    orr   r1, r1, r3, lsl #5
    str   r1, [r2]
    sub   r0, r3, #1
    cmp   r0, #{RUN_TICKS}
    movlo r0, #1
    movhs r0, #0
    str   r0, [sp, #8]
    b     {TIMED_RUN_EXIT:#x}
"""

# Branch encodings: 0xEA000000 | ((target - (addr + 8)) >> 2).
NO_RUN_HP_COST = Feature(
    "no-run-hp-cost",
    (
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        Patch(
            0x02024BF8,
            0x0A000016,
            0xEA000016,
            "beq -> b: skip the HP <= 1/3 too-tired check",
        ),
    ),
)

TIMED_RUN = Feature(
    "timed-run",
    (
        CaveCode("cave_run_area_last", "    .word 0", "map the run state belongs to"),
        CaveCode("cave_run_area", RUN_AREA_ASM, "run ready again in a new area"),
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        AsmPatch(
            0x02024BF8,
            0x02024C58,
            0x0A000016,
            0xBAFFFFEA,
            TIMED_RUN_ASM_ENTRY,
            "load run state",
        ),
        AsmPatch(
            TIMED_RUN_BODY_ADDR,
            0x02025228,
            0xE5902000,
            0xEB013188,
            TIMED_RUN_ASM_BODY,
            "3 s run, 3 s cooldown",
        ),
    ),
)
