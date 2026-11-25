"""Using a worn card from the Special list (docs/plan-cards.md 2.4 and 7.4).

The card ability is one spell id (skills_cards.CARD_SPELL). It is listed for a member who wears a battle card
(a monster card that is not one of the six field cards) with at least one use of points left; the menu takes it
as a spell on all targets, so no picker opens. When the action runs, the resolver (func_020514ec) finds the
member's command Special with that spell and turns it into the game's own item command (4) with the worn card,
before the Special branch's silence test and MP charge: the card's effect, animation, and the points it costs are
the game's, and silence does not stop a card.
"""

from dsde.cards_common import (
    CARD_POINTS,
    CARD_SLOT,
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    EQUIP_OFFSET,
    FIRST_BOSS_CARD,
    FIRST_CARD,
    POINTS_PER_USE,
)
from dsde.cards_data import FIELD_CARDS
from dsde.patching import CaveCode
from dsde.skills_cards import CARD_SPELL
from dsde.skills_common import hook

CASTABLE = 0x02050A74  # func_02050a74 (member, spell, battle): `push {r4-sl, lr}`
CASTABLE_WORD = 0xE92D47F0
RESOLVE_COMMAND = (
    0x02051A08  # func_020514ec, party: `ldrsh r0, [r4, #0x84]` (r4 = the battler)
)
RESOLVE_COMMAND_WORD = 0xE1D408F4
COMMAND_SPECIAL = 2
COMMAND_ITEM = 4
BATTLER_CHARACTER = 4
BATTLER_COMMAND = 0x84
BATTLER_ACTION_ID = 0x86
CARD_KIND_BATTLE = 1
MONSTER_CARD_COUNT = FIRST_BOSS_CARD - FIRST_CARD


def _kinds() -> str:
    """A byte per monster card: 1 for a battle card, 0 for a field card."""
    kinds = [
        0 if card in FIELD_CARDS else CARD_KIND_BATTLE
        for card in range(FIRST_CARD, FIRST_BOSS_CARD)
    ]
    return ", ".join(str(k) for k in kinds)


# r0 = character id -> r0 = the worn card if it is a battle card with a use of points left, else 0. Keeps r1 to r3.
USABLE_ASM = f"""
    push  {{r1, r2, lr}}
    ldr   r1, cu_slots
    mov   r2, #{CHAR_RECORD_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r0, [r1, #{CARD_SLOT * 2}]
    sub   r1, r0, #{FIRST_CARD:#x}
    cmp   r1, #{MONSTER_CARD_COUNT}
    bhs   cu_none
    adr   r2, cu_kinds
    ldrb  r2, [r2, r1]
    cmp   r2, #{CARD_KIND_BATTLE}
    bne   cu_none
    ldr   r2, cu_points
    add   r2, r2, r1, lsl #1
    ldrsh r2, [r2]
    cmp   r2, #{POINTS_PER_USE}
    bge   cu_done
cu_none:
    mov   r0, #0
cu_done:
    pop   {{r1, r2, pc}}
cu_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
cu_points:
    .word {CARD_POINTS:#x}
cu_kinds:
    .byte {_kinds()}
    .align 2
"""

# func_02050a74's first instruction: the card spell is castable (it is only listed when it can be used) and its
# "cost" is 1, which the menu needs to accept a pick; no MP is ever taken for it.
CASTABLE_ASM = f"""
    cmp   r1, #{CARD_SPELL}
    moveq r0, #1
    bxeq  lr
    push  {{r4-r10, lr}}
    b     {CASTABLE + 4:#x}
"""

# In place of `ldrsh r0, [r4, #0x84]`: a Special with the card spell becomes the item command with the worn card.
RESOLVE_ASM = f"""
    ldrsh r0, [r4, #{BATTLER_COMMAND:#x}]
    cmp   r0, #{COMMAND_SPECIAL}
    bxne  lr
    push  {{r1, lr}}
    ldrh  r1, [r4, #{BATTLER_ACTION_ID:#x}]
    cmp   r1, #{CARD_SPELL}
    bne   cr_keep
    ldr   r0, [r4, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_usable}}
    cmp   r0, #0
    beq   cr_keep
    strh  r0, [r4, #{BATTLER_ACTION_ID:#x}]
    mov   r0, #{COMMAND_ITEM}
    strh  r0, [r4, #{BATTLER_COMMAND:#x}]
    pop   {{r1, pc}}
cr_keep:
    mov   r0, #{COMMAND_SPECIAL}
    pop   {{r1, pc}}
"""


def use_patches() -> tuple:
    return (
        CaveCode("cave_card_usable", USABLE_ASM, "a worn battle card with points left"),
        CaveCode("cave_card_castable", CASTABLE_ASM, "the card spell is castable"),
        hook(
            CASTABLE,
            CASTABLE_WORD,
            "b ${cave_card_castable}",
            "the card spell is castable",
        ),
        CaveCode(
            "cave_card_resolve", RESOLVE_ASM, "the card spell becomes the card command"
        ),
        hook(
            RESOLVE_COMMAND,
            RESOLVE_COMMAND_WORD,
            "bl ${cave_card_resolve}",
            "the card spell becomes the card command",
        ),
    )
