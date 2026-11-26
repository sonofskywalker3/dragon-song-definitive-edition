"""Boss card passives that need code (docs/plan-cards.md 4 and 8, approved build list point 5).

Moran and Orcus: a party member wearing the Moran (Orcus) card whose physical hit lands on an enemy has a 25%
chance to lower its DEF (ATK) one stage, once per action (Jian's combo and Double Strike's two swipes get one roll),
and only when the stage is not already below 0, bosses included. The hook is in func_02030b44 after the landed
hit's damage is worked out (0x02030DA8; r4 = the target's battler index; the attacker is the acting battler, since
the attack's own r7 is then the scratch copy, battler 12). It rolls only when the attack's attacker (r7) is a party
member or battler 12 and the target is an enemy battler, 4 to 11: an enemy's counter runs on battler 13 and can
target the party member's scratch copy, 12, while the acting battler is still the party member; the flag that the
roll was made is cleared at the start of each party action (feat_card_use.py's resolver hook).

New gear effect ids for the boss cards alone (cards_data.GEAR_STRONG_*, GEAR_HP_REGEN_3). func_0206ab6c totals a
member's gear effects into a block of bytes (r4 = 0x0213B908): +0x0B to +0x0E the damage percent taken from water,
earth, wind, and fire (100, and the game's guards take 25 off), +0x08 the HP regen percent each own turn. Its switch
covers ids 0 to 0x2D and sends anything higher to the loop's next slot (0x0206AC20); the new ids are handled there:
a dragon's element takes 50 off, Caucus's regen adds 3.
"""

from dsde.cards_common import CARD_SLOT, CHAR_RECORD_SIZE, CHAR_RECORDS, EQUIP_OFFSET
from dsde.cards_data import (
    GEAR_HP_REGEN_3,
    GEAR_STRONG_FIRE,
    GEAR_STRONG_WATER,
    MORAN,
    ORCUS,
)
from dsde.patching import CaveCode
from dsde.skills_common import (
    BATTLE_WORK_PTR,
    BATTLER_RECORD,
    BATTLER_SIZE,
    BATTLERS_PTR,
    RECORD_SIZE,
    RECORD_STAGES,
    RECORDS_PTR,
    hook,
)
from dsde.skills_types import STAT_ATK, STAT_DEF

GEAR_DEFAULT = 0x0206AC20  # func_0206ab6c: `b 0x0206AEC8`, an id past the switch (r0 = the id, r4 = the block)
GEAR_DEFAULT_WORD = 0xEA0000A8
GEAR_NEXT = 0x0206AEC8  # the loop's next slot
ELEMENT_BYTES = (
    0x0B,
    0x0C,
    0x0D,
    0x0E,
)  # water, earth, wind, fire (the order of the game's guards 0x1F to 0x22)
STRONG_GUARD = 50  # percent off
REGEN_BYTE = 0x08
REGEN_3 = 3

GEAR_ASM = f"""
    push  {{r1-r3}}
    subs  r1, r0, #{GEAR_STRONG_WATER:#x}
    blo   ge_done
    cmp   r1, #{GEAR_STRONG_FIRE - GEAR_STRONG_WATER}
    bhi   ge_regen
    adr   r2, ge_bytes
    ldrb  r2, [r2, r1]
    ldrb  r3, [r4, r2]
    sub   r3, r3, #{STRONG_GUARD}
    strb  r3, [r4, r2]
    b     ge_done
ge_regen:
    cmp   r0, #{GEAR_HP_REGEN_3:#x}
    bne   ge_done
    ldrb  r3, [r4, #{REGEN_BYTE:#x}]
    add   r3, r3, #{REGEN_3}
    strb  r3, [r4, #{REGEN_BYTE:#x}]
ge_done:
    pop   {{r1-r3}}
    b     {GEAR_NEXT:#x}
ge_bytes:
    .byte {", ".join(f"{b:#x}" for b in ELEMENT_BYTES)}
    .align 2
"""


ON_HIT = 0x02030DA8  # func_02030b44, a landed hit: `ldr r1, [r5]` after the damage (r0) is worked out
ON_HIT_WORD = 0xE5951000
FIRST_ENEMY = 4
LAST_ENEMY = 11  # enemy battlers 4 to 11; 12 and 13 are the scratch copies a party attack and an enemy counter run on
PARTY_SCRATCH = 12
WORK_ACTOR = 0x32  # battle work: the acting battler (the attack's r7 can be the scratch copy, battler 12)
BATTLER_CHARACTER = 4
PARTY_SLOTS = 3
BREAK_CHANCE = 25
PERCENT = 100
RANDOM = 0x02011424
DIVMOD = 0x02015F80
ADD_STAGE = 0x02054DEC
RECOMPUTE_ENEMY = 0x02069AD8

# In place of `ldr r1, [r5]` after a landed hit's damage: the Moran or Orcus roll. Keeps every register but r1,
# which gets the replaced load.
ON_HIT_ASM = f"""
    push  {{r0, r2-r7, ip, lr}}
    cmp   r7, #{PARTY_SCRATCH}
    beq   oh_attacker
    cmp   r7, #{PARTY_SLOTS}
    bhs   oh_done
oh_attacker:
    cmp   r4, #{FIRST_ENEMY}
    blo   oh_done
    cmp   r4, #{LAST_ENEMY}
    bhi   oh_done
    ldr   r7, oh_work
    ldr   r7, [r7]
    ldrsh r7, [r7, #{WORK_ACTOR:#x}]
    cmp   r7, #{PARTY_SLOTS}
    bhs   oh_done
    ldr   r6, oh_rolled
    ldrb  r0, [r6]
    cmp   r0, #0
    bne   oh_done
    ldr   r2, oh_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r0, r7, r3, r2
    ldr   r0, [r0, #{BATTLER_CHARACTER}]
    ldr   r1, oh_slots
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r1, r0, r3, r1
    ldrh  r0, [r1, #{CARD_SLOT * 2}]
    subs  r0, r0, #{MORAN}
    moveq r5, #{STAT_DEF}
    beq   oh_roll
    cmp   r0, #{ORCUS - MORAN}
    bne   oh_done
    mov   r5, #{STAT_ATK}
oh_roll:
    mov   r0, #1
    strb  r0, [r6]
    bl    {RANDOM:#x}
    bic   r0, r0, #0x80000000
    mov   r1, #{PERCENT}
    bl    {DIVMOD:#x}
    cmp   r1, #{BREAK_CHANCE}
    bhs   oh_done
    ldr   r2, oh_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r0, r4, r3, r2
    ldr   r0, [r0, #{BATTLER_RECORD:#x}]
    ldr   r2, oh_records
    ldr   r2, [r2]
    mov   r3, #{RECORD_SIZE:#x}
    mla   r6, r0, r3, r2
    add   r0, r6, r5, lsl #1
    ldrsh r0, [r0, #{RECORD_STAGES:#x}]
    cmp   r0, #0
    blt   oh_done
    mov   r0, r6
    mov   r1, r5
    mvn   r2, #0
    bl    {ADD_STAGE:#x}
    mov   r0, r6
    mov   r1, #1
    bl    {RECOMPUTE_ENEMY:#x}
oh_done:
    pop   {{r0, r2-r7, ip, lr}}
    ldr   r1, [r5]
    bx    lr
oh_rolled:
    .word ${{cave_card_hit_rolled}}
oh_work:
    .word {BATTLE_WORK_PTR:#x}
oh_battlers:
    .word {BATTLERS_PTR:#x}
oh_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
oh_records:
    .word {RECORDS_PTR:#x}
"""


ROLLED_ASM = """
    .byte 0
    .align 2
"""


def boss_patches() -> tuple:
    return (
        CaveCode("cave_card_gear_extra", GEAR_ASM, "the boss cards' own gear effects"),
        hook(
            GEAR_DEFAULT,
            GEAR_DEFAULT_WORD,
            "b ${cave_card_gear_extra}",
            "the boss cards' own gear effects",
        ),
        CaveCode("cave_card_hit_rolled", ROLLED_ASM, "the Moran or Orcus roll is made"),
        CaveCode(
            "cave_card_on_hit", ON_HIT_ASM, "Moran and Orcus lower a stat on a hit"
        ),
        hook(
            ON_HIT,
            ON_HIT_WORD,
            "bl ${cave_card_on_hit}",
            "Moran and Orcus lower a stat on a hit",
        ),
    )
