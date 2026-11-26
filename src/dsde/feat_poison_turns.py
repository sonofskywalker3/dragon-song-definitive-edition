"""Poison wears off after 2 to 4 turns, on monsters and on the party alike (docs/plan-cards.md 8, point 3).

In the game a battler's status has a turn counter (stat record +0x4C, s16) that the status setter func_0205511c
fills (2 to 4 for statuses 1 to 5, 4 to 6 for stone) and func_02055070 counts down at the start of the battler's own
turn, clearing the status at 0. Poison was the exception: its counter is set to 0 and never counted, so it lasted
the battle. Here poison's counter is set to 3 to 5 (two coin flips) and counted like the others; the poison tick
that follows the count only comes while the status is still on, so poison takes its HP 2 to 4 times.
"""

from dsde.patching import AsmPatch, CaveCode, Feature
from dsde.skills_common import RECORDS_PTR, hook

RANDOM = 0x02011424
RECORD_TURNS = 0x4C
POISON_TURNS = 3  # plus two coin flips: 3 to 5 on the counter, so 2 to 4 ticks

# func_02055070's switch on the status: poison's entry, `bx lr` (never counted)
COUNT_POISON = 0x020550C4
COUNT_POISON_WORD = 0xE12FFF1E
COUNT_DOWN = 0x020550CC  # the count shared by statuses 1 to 5 and 7
# func_0205511c's switch on the new status: poison's entry, `b 0x020551FC` (counter 0); r4 = the record offset
SET_POISON = 0x0205518C
SET_POISON_WORD = 0xEA00001A
SET_DONE = 0x0205520C

# Entered by `b` from the setter's switch for poison (r4 = record index * 0x6C): the counter gets 3 to 5.
SET_ASM = f"""
    bl    {RANDOM:#x}
    and   r5, r0, #1
    bl    {RANDOM:#x}
    and   r0, r0, #1
    add   r5, r5, r0
    add   r5, r5, #{POISON_TURNS}
    ldr   r0, pt_records
    ldr   r0, [r0]
    add   r0, r0, r4
    strh  r5, [r0, #{RECORD_TURNS:#x}]
    b     {SET_DONE:#x}
pt_records:
    .word {RECORDS_PTR:#x}
"""

PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    hook(
        COUNT_POISON,
        COUNT_POISON_WORD,
        f"b {COUNT_DOWN:#x}",
        "poison's turns are counted",
    ),
    CaveCode("cave_poison_turns", SET_ASM, "poison lasts 2 to 4 turns"),
    hook(
        SET_POISON,
        SET_POISON_WORD,
        "b ${cave_poison_turns}",
        "poison lasts 2 to 4 turns",
    ),
)

POISON_TURNS_FEATURE = Feature("poison-turns", PATCHES)
