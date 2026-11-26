"""Cards follow the skills' rules (docs/plan-cards.md 3.3, decision 1).

A card's stage change (func_0206a2f8, through func_02054dec) moves a stat one stage at most: a raise is skipped on
a stat already above 0, a lowering on one already below 0, as the skills do; today the uses stack to four stages.
A card's sleep, paralysis, or stone on a regular enemy lands 70% of the time instead of always; bosses keep their
immunities and every other status still always lands. On a boss, a card's blind, silence (Phantom), or poison
lands 80% of the time; the game had blind and poison always land and silence never.
"""

from dsde.patching import CaveCode
from dsde.skills_common import RECORD_STAGES, hook
from dsde.skills_types import STATUS_CHANCE

STAGE_UP_CALL = 0x0206A398  # func_0206a2f8: `bl func_02054dec` for a raise
STAGE_DOWN_CALL = 0x0206A43C  # and for a lowering
STAGE_UP_WORD = 0xEBFFAA93
STAGE_DOWN_WORD = 0xEBFFAA6A
SET_STAGE = 0x02054DEC  # (stat record, stat, +1 / -1)
NOT_RESISTED = 0x0206A560  # the status loop, a regular enemy: `mov r0, #0` (it lands)
NOT_RESISTED_WORD = 0xE3A00000
ROLLED_STATUSES = (1, 4, 7)  # sleep, paralysis, stone: the ones that take turns away
# The status loop's boss switch (r4 = the status): an entry per status, `b 0x0206A558` (lands) or `b 0x0206A550`
# (resisted). Blind, silence, and poison go to a roll instead: 80% (docs/plan-cards.md 8, point 3)
BOSS_ENTRIES = {
    2: (0x0206A538, 0xEA000006),
    5: (0x0206A544, 0xEA000001),
    6: (0x0206A548, 0xEA000002),
}
BOSS_RESULT = 0x0206A564  # `cmp r0, #0`: 1 resisted, 0 lands
BOSS_CHANCE = 80

# r0 = the stat record, r1 = the stat, r2 = +1 or -1: func_02054dec unless the stat is already a stage past 0 in
# that direction.
STAGE_ASM = f"""
    add   r3, r0, #{RECORD_STAGES:#x}
    add   r3, r3, r1, lsl #1
    ldrsh r3, [r3]
    cmp   r2, #0
    bgt   stage_up
    cmp   r3, #0
    bxlt  lr
    b     {SET_STAGE:#x}
stage_up:
    cmp   r3, #0
    bxgt  lr
    b     {SET_STAGE:#x}
"""

# In place of `mov r0, #0` (r4 = the status, r5 = the target's roll of 0 to 99; r2 held a copy, but the boss test's
# call before this point overwrites it): r0 = 1 (resisted) for a rolled status when
# the roll misses, else 0.
ROLL_ASM = f"""
    mov   r0, #0
    cmp   r4, #{ROLLED_STATUSES[0]}
    cmpne r4, #{ROLLED_STATUSES[1]}
    cmpne r4, #{ROLLED_STATUSES[2]}
    bxne  lr
    cmp   r5, #{STATUS_CHANCE}
    movhs r0, #1
    bx    lr
"""


# Entered by `b` from the boss switch for blind, silence, and poison (r5 = the target's roll, 0 to 99): r0 = 1
# (resisted) when the roll is 80 or more, else 0.
BOSS_ROLL_ASM = f"""
    cmp   r5, #{BOSS_CHANCE}
    movhs r0, #1
    movlo r0, #0
    b     {BOSS_RESULT:#x}
"""


def rule_patches() -> tuple:
    return (
        CaveCode(
            "cave_card_boss_roll",
            BOSS_ROLL_ASM,
            "a card's blind, silence, or poison lands on a boss 80%",
        ),
        *(
            hook(
                addr,
                word,
                "b ${cave_card_boss_roll}",
                f"a card's status {status} lands on a boss 80%",
            )
            for status, (addr, word) in BOSS_ENTRIES.items()
        ),
        CaveCode("cave_card_stage", STAGE_ASM, "a card moves a stat one stage at most"),
        hook(
            STAGE_UP_CALL,
            STAGE_UP_WORD,
            "bl ${cave_card_stage}",
            "a card raises a stat one stage at most",
        ),
        hook(
            STAGE_DOWN_CALL,
            STAGE_DOWN_WORD,
            "bl ${cave_card_stage}",
            "a card lowers a stat one stage at most",
        ),
        CaveCode(
            "cave_card_roll", ROLL_ASM, "a card's sleep, paralysis, or stone lands 70%"
        ),
        hook(
            NOT_RESISTED,
            NOT_RESISTED_WORD,
            "bl ${cave_card_roll}",
            "a card's sleep, paralysis, or stone lands 70%",
        ),
    )
