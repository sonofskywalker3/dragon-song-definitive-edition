"""Dragon Magic for whoever wears the ring (docs/plan-cards.md 7.3, design.md 10).

func_02050c50 ("is this spell listed for this member") lists a Dragon Magic spell (spell flags 0x100000 to
0x800000, one bit per ring) for Jian when the ring is in the bag, and for nobody else. Every branch of it ends at
one test (`cmp r6, #1` at 0x02050DDC, r6 = listed, r5 = the character, r8 = the spell) before the max MP test;
there a ring spell is listed exactly when the member wears its ring in the ring slot (slot 6), for anyone, and no
longer from the bag. Casting follows: func_02050a74 lets a listed spell be cast by anyone but Jian with no other
test, and for Jian it asks func_0206b8ec, which looks through all seven slots.

The cast: the action setup puts Jian's Dragon Magic file (his body) in animation slot 0 for any caster; for anyone
else it now puts the caster's own Special file there, so the wearer casts in their own pose and the ring's
pillar, which does not come from that file, plays as it does for Jian (Jeff, 2026-11-25).
"""

from dsde.cards_common import (
    CARD_SLOT,
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    EQUIP_OFFSET,
    RING_ITEMS,
    RING_SLOT,
)
from dsde.patching import CaveCode
from dsde.cards_data import MORUS
from dsde.skills_cards import CARD_SPELL, STEAL_SPELL
from dsde.skills_common import RING_FLAGS, SPELL_ENTRY_SIZE, SPELL_TABLE, hook

LIST_TAIL = 0x02050DDC  # func_02050c50: `cmp r6, #1`
LIST_TAIL_WORD = 0xE3560001
RING_FLAG_SHIFT = 20
LOOK_SWITCH = 0x020686A8  # func_02068308, a party Special: `sub r1, r1, #0xa`, then a switch on spell - 10
LOOK_SWITCH_WORD = 0xE241100A
OUT_OF_SWITCH = (
    6  # past the switch's cases: the default, the caster's own Special file in slot 0
)
JIAN_FILES = 0x020953D4  # r4 = the caster's row of the character file table (0x12 each, Jian's first)  # the lowest ring bit, 0x100000, is the Blazing Ring's

# In place of `cmp r6, #1`: Steal is listed in battle for a member wearing the Morus card; the card spell is
# listed in battle for a member with a usable worn card
# (cave_card_usable); for a ring spell, r6 = 1 when the member (r5) wears that ring in the ring slot, else
# 0; then the compare. Keeps every register but r6.
LISTED_HEAD = """
    push  {r0-r3, lr}
"""
LISTED_CARDS = f"""    cmp   r8, #{STEAL_SPELL}
    beq   rl_steal
    cmp   r8, #{CARD_SPELL}
    bne   rl_spell
    mov   r6, #0
    cmp   r7, #0
    beq   rl_done
    mov   r0, r5
    bl    ${{cave_card_listable}}
    cmp   r0, #0
    movne r6, #1
    b     rl_done
rl_steal:
    mov   r6, #0
    cmp   r7, #0
    beq   rl_done
    ldr   r2, rl_slots
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r5, r3, r2
    ldrh  r2, [r2, #{CARD_SLOT * 2}]
    cmp   r2, #{MORUS}
    moveq r6, #1
    b     rl_done
"""
LISTED_RINGS = f"""    ldr   r0, rl_table
    mov   r1, #{SPELL_ENTRY_SIZE:#x}
    mla   r0, r8, r1, r0
    ldr   r0, [r0]
    ands  r0, r0, #{RING_FLAGS:#x}
    beq   rl_done
    lsr   r0, r0, #{RING_FLAG_SHIFT}
    mov   r1, #{RING_ITEMS[0]:#x}
rl_bit:
    tst   r0, #1
    bne   rl_ring
    add   r1, r1, #1
    lsr   r0, r0, #1
    b     rl_bit
rl_ring:
    ldr   r2, rl_slots
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r5, r3, r2
    ldrh  r2, [r2, #{RING_SLOT * 2}]
    cmp   r2, r1
    moveq r6, #1
    movne r6, #0
"""
LISTED_TAIL = f"""rl_done:
    cmp   r6, #1
    pop   {{r0-r3, pc}}
rl_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
"""
LISTED_TABLE = f"""rl_table:
    .word {SPELL_TABLE:#x}
"""


def listed_asm(rings: bool, cards: bool) -> str:
    """In place of `cmp r6, #1` for a mix: Steal and the card spell (cards); a ring's spell for its wearer
    (rings). With no ring slot, a ring spell keeps the game's own listing."""
    cards_asm = LISTED_CARDS if cards else ""
    rings_asm = LISTED_RINGS if rings else ""
    table = LISTED_TABLE if rings else ""
    tail = LISTED_TAIL.replace("rl_slots:", table + "rl_slots:")
    return LISTED_HEAD + cards_asm + "rl_spell:\n" + rings_asm + tail


# In place of `sub r1, r1, #0xa`: the switch puts Jian's Dragon Magic file (btldata 19 to 22, his body in the
# cast) in animation slot 0 for spells 10 to 13 whoever casts; for anyone else the switch's default puts the
# caster's own Special file there, so they cast in their own pose and the ring's pillar plays all the same.
LOOK_ASM = f"""
    sub   r1, r1, #10
    ldr   r2, look_jian
    cmp   r4, r2
    movne r1, #{OUT_OF_SWITCH}
    bx    lr
look_jian:
    .word {JIAN_FILES:#x}
"""


def listed_patches(rings: bool, cards: bool) -> tuple:
    """The spell listing for a mix of the ring slot and the card overhaul."""
    return (
        CaveCode(
            "cave_ring_listed",
            listed_asm(rings, cards),
            "a ring's spell is listed for whoever wears the ring",
        ),
        hook(
            LIST_TAIL,
            LIST_TAIL_WORD,
            "bl ${cave_ring_listed}",
            "a ring's spell is listed for whoever wears it",
        ),
    )


def ring_patches() -> tuple:
    """The ring slot's own: a ring's spell cast in the wearer's own pose."""
    return (
        CaveCode("cave_ring_look", LOOK_ASM, "a ring's spell in the caster's own pose"),
        hook(
            LOOK_SWITCH,
            LOOK_SWITCH_WORD,
            "bl ${cave_ring_look}",
            "a ring's spell in the caster's own pose",
        ),
    )
