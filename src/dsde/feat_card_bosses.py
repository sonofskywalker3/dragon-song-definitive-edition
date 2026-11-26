"""Boss card passives that need code (docs/plan-cards.md 4 and 8, approved build list point 5).

New gear effect ids for the boss cards alone (cards_data.GEAR_STRONG_*, GEAR_HP_REGEN_3). func_0206ab6c totals a
member's gear effects into a block of bytes (r4 = 0x0213B908): +0x0B to +0x0E the damage percent taken from water,
earth, wind, and fire (100, and the game's guards take 25 off), +0x08 the HP regen percent each own turn. Its switch
covers ids 0 to 0x2D and sends anything higher to the loop's next slot (0x0206AC20); the new ids are handled there:
a dragon's element takes 50 off, Caucus's regen adds 3.
"""

from dsde.cards_data import (
    GEAR_HP_REGEN_3,
    GEAR_STRONG_FIRE,
    GEAR_STRONG_WATER,
)
from dsde.patching import CaveCode
from dsde.skills_common import hook

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


def boss_patches() -> tuple:
    return (
        CaveCode("cave_card_gear_extra", GEAR_ASM, "the boss cards' own gear effects"),
        hook(
            GEAR_DEFAULT,
            GEAR_DEFAULT_WORD,
            "b ${cave_card_gear_extra}",
            "the boss cards' own gear effects",
        ),
    )
