"""Getting and recharging cards (docs/plan-cards.md 2.6 and 7.5, approved build list point 7).

- Kills are counted per species during a battle: the normal drop routine func_02069f34 calls the roll
  func_02069e00(row, tier) once for each regular monster that dies (0x0206A008), and the species is row >> 2.
- The roll never lands on the card slot: a roll that would gives slot 0, as the game does once the card is owned.
- When the battle ends (0x0202AC58, right after the results are copied back, for every outcome), a won battle
  (result 0x020B85C4 at most 1) gives each species killed its card, at full points, if no copy is owned (the bag
  count includes a worn card), and otherwise adds 100 points per kill, capped at the card's full value. Escaping
  or losing gives nothing. The counts are cleared either way.
- Boss cards always drop: in the boss branch the card slot's roll always passes (a slot whose chance is 0 stays
  0: Gideon 2, Gideon 3, and Ignatius, which have no source yet).
"""

from dsde.cards_common import (
    BAG,
    CARD_FULL,
    CARD_FULL_SIZE,
    CARD_POINTS,
    FIRST_BOSS_CARD,
    FIRST_CARD,
    POINTS_PER_USE,
)
from dsde.patching import CaveCode
from dsde.skills_common import hook

SPECIES = FIRST_BOSS_CARD - FIRST_CARD  # 34 monster species with cards
ROW_SPECIES_SHIFT = 2  # four enemy rows (area variants) per species
ROLL_CALL = (
    0x0206A008  # func_02069f34: `bl func_02069e00` (r0 = the row, r1 = the tier)
)
ROLL_CALL_WORD = 0xEBFFFF7C
ROLL = 0x02069E00
CARD_SLOT_TEST = 0x02069ED8  # func_02069e00: `cmp r4, #2` (the slot rolled)
CARD_SLOT_TEST_WORD = 0xE3540002
CARD_DROP_SLOT = 2
BOSS_ROLL = 0x0206A170  # the boss branch: `cmp r2, r0, lsr #16` (r2 = slot sb's chance, r0 = the roll << 16)
BOSS_ROLL_WORD = 0xE1520820
BATTLE_END = 0x0202AC58  # func_020297d4, the battle's end: `mov r0, #2`
BATTLE_END_WORD = 0xE3A00002
BATTLE_RESULT = 0x020B85C4  # s16: 0 or 1 is a win
WON = 1
BAG_COUNT = 0x0206BA54  # (bag, item) -> how many
ADD_ITEM = 0x0206B98C  # (bag, item, count)

KILLS_ASM = f"""
    .space {SPECIES}
    .align 2
"""

# In place of `bl func_02069e00`: count the kill, then the roll (r0 and r1 kept).
COUNT_ASM = f"""
    push  {{r0-r2}}
    lsr   r0, r0, #{ROW_SPECIES_SHIFT}
    cmp   r0, #{SPECIES}
    bhs   ck_done
    ldr   r1, ck_kills
    ldrb  r2, [r1, r0]
    cmp   r2, #0xFF
    addlo r2, r2, #1
    strb  r2, [r1, r0]
ck_done:
    pop   {{r0-r2}}
    b     {ROLL:#x}
ck_kills:
    .word ${{cave_card_kills}}
"""

# In place of `cmp r4, #2`: the card slot gives slot 0, then the compare.
SLOT_ASM = f"""
    cmp   r4, #{CARD_DROP_SLOT}
    moveq r4, #0
    cmp   r4, #{CARD_DROP_SLOT}
    bx    lr
"""

# In place of `cmp r2, r0, lsr #16` in the boss branch (sb = the slot): the card slot always passes unless its chance
# is 0.
BOSS_ASM = f"""
    cmp   sb, #{CARD_DROP_SLOT}
    bne   bd_roll
    cmp   r2, #0
    beq   bd_roll
    cmp   r2, r2
    bx    lr
bd_roll:
    cmp   r2, r0, lsr #16
    bx    lr
"""

# In place of `mov r0, #2` at the battle's end: on a win each species killed gives its card (full points) or 100
# points per kill (capped); the counts are cleared whatever the outcome.
END_ASM = f"""
    push  {{r4-r8, lr}}
    ldr   r0, ce_result
    ldrsh r8, [r0]
    ldr   r4, ce_kills
    mov   r5, #0
ce_loop:
    ldrb  r6, [r4, r5]
    cmp   r6, #0
    beq   ce_next
    mov   r0, #0
    strb  r0, [r4, r5]
    cmp   r8, #{WON}
    bhi   ce_next
    add   r7, r5, #{FIRST_CARD}
    ldr   r0, ce_bag
    mov   r1, r7
    bl    {BAG_COUNT:#x}
    ldr   r1, ce_full
    add   r1, r1, r5, lsl #3
    ldr   r1, [r1]
    ldr   r2, ce_points
    add   r2, r2, r5, lsl #1
    cmp   r0, #0
    bgt   ce_recharge
    strh  r1, [r2]
    ldr   r0, ce_bag
    mov   r1, r7
    mov   r2, #1
    bl    {ADD_ITEM:#x}
    b     ce_next
ce_recharge:
    ldrsh r0, [r2]
    mov   r3, #{POINTS_PER_USE}
    mla   r0, r3, r6, r0
    cmp   r0, r1
    movgt r0, r1
    strh  r0, [r2]
ce_next:
    add   r5, r5, #1
    cmp   r5, #{SPECIES}
    blt   ce_loop
    pop   {{r4-r8, lr}}
    mov   r0, #2
    bx    lr
ce_result:
    .word {BATTLE_RESULT:#x}
ce_kills:
    .word ${{cave_card_kills}}
ce_bag:
    .word {BAG:#x}
ce_full:
    .word {CARD_FULL:#x}
ce_points:
    .word {CARD_POINTS:#x}
"""

assert CARD_FULL_SIZE == 1 << 3


def drop_patches() -> tuple:
    return (
        CaveCode("cave_card_kills", KILLS_ASM, "kills per species this battle"),
        CaveCode("cave_card_kill_count", COUNT_ASM, "count a kill"),
        hook(ROLL_CALL, ROLL_CALL_WORD, "bl ${cave_card_kill_count}", "count a kill"),
        CaveCode(
            "cave_card_no_card_roll", SLOT_ASM, "the drop roll never gives a card"
        ),
        hook(
            CARD_SLOT_TEST,
            CARD_SLOT_TEST_WORD,
            "bl ${cave_card_no_card_roll}",
            "the drop roll never gives a card",
        ),
        CaveCode("cave_card_boss_drop", BOSS_ASM, "boss cards always drop"),
        hook(
            BOSS_ROLL,
            BOSS_ROLL_WORD,
            "bl ${cave_card_boss_drop}",
            "boss cards always drop",
        ),
        CaveCode(
            "cave_card_battle_end", END_ASM, "a won battle gives and recharges cards"
        ),
        hook(
            BATTLE_END,
            BATTLE_END_WORD,
            "bl ${cave_card_battle_end}",
            "a won battle gives and recharges cards",
        ),
    )
