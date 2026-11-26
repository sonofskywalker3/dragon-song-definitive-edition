"""Using a worn card from the Special list (docs/plan-cards.md 2.4 and 7.4).

The card ability is one spell id (skills_cards.CARD_SPELL). It is listed for a member who wears a battle card
(a monster card that is not one of the six field cards) with at least one use of points left; the menu takes it
as a spell on all targets, so no picker opens. When the action runs, the resolver (func_020514ec) finds the
member's command Special with that spell and turns it into the game's own item command (4) with the worn card,
before the Special branch's silence test and MP charge: the card's effect, animation, and the points it costs are
the game's, and silence does not stop a card.

The Item command opens the item list directly (the Tools / Cards page is skipped), and Back from the list goes to
the command page.
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
from dsde.feat_card_targets import BASIC_LEARNER
from dsde.patching import CaveCode, Patch
from dsde.skills_cards import CARD_SPELL
from dsde.skills_common import hook

CASTABLE = 0x02050A74  # func_02050a74 (member, spell, battle): `push {r4-sl, lr}`
CASTABLE_WORD = 0xE92D47F0
RESOLVE_COMMAND = (
    0x02051A08  # func_020514ec, party: `ldrsh r0, [r4, #0x84]` (r4 = the battler)
)
RESOLVE_COMMAND_WORD = 0xE1D408F4
BAR_NUMBER = 0x02044E88  # the name bar's spell case: `mov r3, r5` (r5 = the MP cost, r4 = 1 if it is short)
BAR_NUMBER_WORD = 0xE1A03005
MENU = 0x020B8800
MENU_BAR_ID = 0x94
MENU_BAR_MEMBER = 0x9C  # a battler index
BATTLERS_PTR = 0x020B8640
BATTLER_SIZE = 0x12C
BATTLER_RECORD = 0x10
RECORDS_PTR = 0x020B8620
RECORD_SIZE = 0x6C
RECORD_CHARACTER = 4
ITEM_BUTTON_CASE = 0x02036804  # the command page's button switch, case 5 (Item): `b 0x02036918` (to page 3)
ITEM_BUTTON_WORD = 0xEA000043
TOOLS_BUTTON = (
    0x02036F2C  # page 3's Tools button: build the item list and open it (page 4)
)
LIST_BACK_PAGE = 0x0203727C  # page 4's Back: `strh r4, [r2, #0xa]` with r4 = 3 (the Tools / Cards page)
LIST_BACK_WORD = 0xE1C240BA
PAGE_COMMANDS = 1
LOST_REMOVE = 0x0207F894  # func_0207f83c at 0 points: `bl func_0206b98c` (take the card out of the bag)
LOST_RETURN = 0x0207F898  # `mov r0, #0`: the caller then shows "Lost <name> card"
NOP = 0xE1A00000
ANY_POINTS = 0
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


# r0 = character id, r1 = the fewest points it must have -> r0 = the worn card if it is a battle card with at
# least that many points, else 0. Keeps r1 to r3.
WORN_BATTLE_ASM = f"""
    push  {{r2, r3, lr}}
    ldr   r2, cu_slots
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r0, r3, r2
    ldrh  r0, [r2, #{CARD_SLOT * 2}]
    sub   r2, r0, #{FIRST_CARD:#x}
    cmp   r2, #{MONSTER_CARD_COUNT}
    bhs   cu_none
    adr   r3, cu_kinds
    ldrb  r3, [r3, r2]
    cmp   r3, #{CARD_KIND_BATTLE}
    bne   cu_none
    ldr   r3, cu_points
    add   r3, r3, r2, lsl #1
    ldrsh r3, [r3]
    cmp   r3, r1
    bge   cu_done
cu_none:
    mov   r0, #0
cu_done:
    pop   {{r2, r3, pc}}
cu_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
cu_points:
    .word {CARD_POINTS:#x}
cu_kinds:
    .byte {_kinds()}
    .align 2
"""

# r0 = character id -> r0 = the worn battle card if it has a use of points left, else 0. Keeps r1 to r3.
USABLE_ASM = f"""
    push  {{r1, lr}}
    mov   r1, #{POINTS_PER_USE}
    bl    ${{cave_card_worn_battle}}
    pop   {{r1, pc}}
"""

# r0 = character id -> r0 = the worn battle card whatever its points (it is listed, greyed at 0), else 0.
LISTABLE_ASM = f"""
    push  {{r1, lr}}
    mov   r1, #{ANY_POINTS}
    bl    ${{cave_card_worn_battle}}
    pop   {{r1, pc}}
"""

# func_02050a74's first instruction, for the card spell: -1 (not listed) with no battle card worn or a card that
# enhances a skill the wearer knows (feat_card_boost.py), 0 (listed,
# greyed, refused) with fewer than 100 points, else 1, the "cost" the menu needs to accept a pick; no MP is ever
# taken for it.
CASTABLE_ASM = f"""
    cmp   r1, #{CARD_SPELL}
    beq   cc_card
    push  {{r4-r10, lr}}
    b     {CASTABLE + 4:#x}
cc_card:
    push  {{r1, r2, lr}}
    ldr   r1, cc_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r1, r0, r2, r1
    ldr   r1, [r1, #{BATTLER_RECORD:#x}]
    ldr   r0, cc_records
    ldr   r0, [r0]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r0, r1, r2, r0
    ldr   r0, [r0, #{RECORD_CHARACTER}]
    mov   r2, r0
    bl    ${{cave_card_listable}}
    cmp   r0, #0
    mvneq r0, #0
    beq   cc_done
    mov   r0, r2
    bl    ${{cave_card_basic}}
    cmp   r0, #{BASIC_LEARNER}
    mvneq r0, #0
    beq   cc_done
    mov   r0, r2
    bl    ${{cave_card_usable}}
    cmp   r0, #0
    movne r0, #1
cc_done:
    pop   {{r1, r2, pc}}
cc_battlers:
    .word {BATTLERS_PTR:#x}
cc_records:
    .word {RECORDS_PTR:#x}
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


# In place of `mov r3, r5` in the name bar: for the card spell, the number is the card's uses left (its points
# / 100) and is never shown as short of MP.
BAR_ASM = f"""
    mov   r3, r5
    push  {{r0-r2, lr}}
    ldr   r0, cb_menu
    ldr   r1, [r0, #{MENU_BAR_ID:#x}]
    cmp   r1, #{CARD_SPELL}
    bne   cb_done
    ldr   r0, [r0, #{MENU_BAR_MEMBER:#x}]
    ldr   r1, cb_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r1, r0, r2, r1
    ldr   r1, [r1, #{BATTLER_RECORD:#x}]
    ldr   r0, cb_records
    ldr   r0, [r0]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r0, r1, r2, r0
    ldr   r0, [r0, #{RECORD_CHARACTER}]
    ldr   r1, cb_slots
    mov   r2, #{CHAR_RECORD_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r0, [r1, #{CARD_SLOT * 2}]
    sub   r0, r0, #{FIRST_CARD:#x}
    ldr   r1, cb_points
    add   r1, r1, r0, lsl #1
    ldrsh r1, [r1]
    mov   r3, #0
cb_divide:
    cmp   r1, #{POINTS_PER_USE}
    subge r1, r1, #{POINTS_PER_USE}
    addge r3, r3, #1
    bge   cb_divide
    mov   r4, #0
cb_done:
    pop   {{r0-r2, pc}}
cb_menu:
    .word {MENU:#x}
cb_battlers:
    .word {BATTLERS_PTR:#x}
cb_records:
    .word {RECORDS_PTR:#x}
cb_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
cb_points:
    .word {CARD_POINTS:#x}
"""


# Page 4's Back goes to the command page (r2 = the menu); r4 keeps the Back sound it is passed on to.
LIST_BACK_ASM = f"""
    push  {{r4}}
    mov   r4, #{PAGE_COMMANDS}
    strh  r4, [r2, #0xa]
    pop   {{r4}}
    bx    lr
"""


def use_patches() -> tuple:
    return (
        hook(
            ITEM_BUTTON_CASE,
            ITEM_BUTTON_WORD,
            f"b {TOOLS_BUTTON:#x}",
            "Item opens the item list, no Tools / Cards",
        ),
        CaveCode(
            "cave_card_list_back",
            LIST_BACK_ASM,
            "back from the item list to the commands",
        ),
        hook(
            LIST_BACK_PAGE,
            LIST_BACK_WORD,
            "bl ${cave_card_list_back}",
            "back from the item list to the commands",
        ),
        CaveCode("cave_card_worn_battle", WORN_BATTLE_ASM, "a worn battle card"),
        CaveCode("cave_card_usable", USABLE_ASM, "a worn battle card with points left"),
        CaveCode("cave_card_listable", LISTABLE_ASM, "a worn battle card, listed"),
        Patch(LOST_REMOVE, 0xEBFFB03C, NOP, "a card at 0 points stays in the bag"),
        Patch(
            LOST_RETURN,
            0xE3A00000,
            0xE3A00001,
            'no "Lost" message for a card at 0 points',
        ),
        CaveCode("cave_card_castable", CASTABLE_ASM, "the card spell is castable"),
        hook(
            CASTABLE,
            CASTABLE_WORD,
            "b ${cave_card_castable}",
            "the card spell is castable",
        ),
        CaveCode("cave_card_bar", BAR_ASM, "the card's uses left on the name bar"),
        hook(
            BAR_NUMBER,
            BAR_NUMBER_WORD,
            "bl ${cave_card_bar}",
            "the card's uses left on the name bar",
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
