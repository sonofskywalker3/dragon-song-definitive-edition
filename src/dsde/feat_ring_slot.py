"""Dragon Magic for whoever wears the ring (docs/plan-cards.md 7.3, design.md 10).

func_02050c50 ("is this spell listed for this member") lists a Dragon Magic spell (spell flags 0x100000 to
0x800000, one bit per ring) for Jian when the ring is in the bag, and for nobody else. Every branch of it ends at
one test (`cmp r6, #1` at 0x02050DDC, r6 = listed, r5 = the character, r8 = the spell) before the max MP test;
there a ring spell is listed exactly when the member wears its ring in the ring slot (slot 6), for anyone, and no
longer from the bag. Casting follows: func_02050a74 lets a listed spell be cast by anyone but Jian with no other
test, and for Jian it asks func_0206b8ec, which looks through all seven slots.
"""

from dsde.cards_common import (
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    EQUIP_OFFSET,
    RING_ITEMS,
    RING_SLOT,
)
from dsde.patching import CaveCode
from dsde.skills_common import RING_FLAGS, SPELL_ENTRY_SIZE, SPELL_TABLE, hook

LIST_TAIL = 0x02050DDC  # func_02050c50: `cmp r6, #1`
LIST_TAIL_WORD = 0xE3560001
RING_FLAG_SHIFT = 20  # the lowest ring bit, 0x100000, is the Blazing Ring's

# In place of `cmp r6, #1`: for a ring spell, r6 = 1 when the member (r5) wears that ring in the ring slot, else
# 0; then the compare. Keeps every register but r6.
LISTED_ASM = f"""
    push  {{r0-r3, lr}}
    ldr   r0, rl_table
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
rl_done:
    cmp   r6, #1
    pop   {{r0-r3, pc}}
rl_table:
    .word {SPELL_TABLE:#x}
rl_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
"""


def ring_patches() -> tuple:
    return (
        CaveCode(
            "cave_ring_listed",
            LISTED_ASM,
            "a ring's spell is listed for whoever wears the ring",
        ),
        hook(
            LIST_TAIL,
            LIST_TAIL_WORD,
            "bl ${cave_ring_listed}",
            "a ring's spell is listed for whoever wears it",
        ),
    )
