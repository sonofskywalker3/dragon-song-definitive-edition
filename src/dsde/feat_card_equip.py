"""Equipping cards and dragon rings on the Item page (docs/plan-cards.md 2.2).

The Item page's category is kept at 0x02139FD4 + 4: 1 to 5 the equipment slots (weapon to accessory), 6 Tools,
7 Cards, 8 Rare Items, 9 Quest Items. State 0x17 of the field menu (func_02059f84) opens the per-member equip page
(state 0x24) for categories 1 to 5 and the shared list page (state 0x1C) for the rest; the Cards category is sent
to the equip page as well, so a card is equipped the way an accessory is (the equip itself, func_0206b46c, puts a
card in slot 5 by its type).

The equip page compares the worn item with the highlighted one. Three routines look up the worn item with one
hard-coded case per slot: its icon (func_02064824), its name (func_02064a4c), and its stats taken off for the
comparison (inside func_02065240). Each now asks cave_card_worn, which also knows slot 5 for the Cards category
and, on the Accessories page, slot 6 while a dragon ring is highlighted.
"""

from dsde.cards_common import CARD_SLOT, CHAR_RECORD_SIZE, CHAR_RECORDS, EQUIP_OFFSET, RING_ITEMS, RING_SLOT
from dsde.patching import AsmPatch, CaveCode, Patch
from dsde.skills_common import hook

CATEGORY_CARDS = 7
CATEGORY_ACCESSORY = 5
LAST_EQUIP_CATEGORY = 5
ITEM_PAGE = 0x02139FD4  # +0 the list cursor (1-based), +4 the category
ITEM_PAGE_CATEGORY = 4
ITEM_LIST = 0x0213A008  # 8 bytes per entry: u32 item, u8 count
ITEM_LIST_SHIFT = 3
MENU_WORK = 0x0213B27C  # +0x644: the party slot shown
MENU_WORK_MEMBER = 0x644
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart
FIRST_RING = RING_ITEMS[0]
RING_SPAN = len(RING_ITEMS) - 1

PAGE_KIND_TEST = 0x0205CC10  # state 0x17: `cmp r1, #5` (r1 = the category); ls = the equip page
PAGE_KIND_WORD = 0xE3510005
WORN_ICON = 0x0206482C  # func_02064824 after its prologue: the category switch and slot 0's lookup
WORN_ICON_END = 0x0206488C  # draws the icon of item r2
WORN_ICON_EXIT = 0x020648A8
WORN_NAME = 0x02064A5C  # func_02064a4c after `bl 0x02067098`: the category switch and slot 0's lookup
WORN_NAME_END = 0x02064AB8  # draws the name of item r2
WORN_NAME_EXIT = 0x02064CA4
WORN_STATS = 0x020652F0  # func_02065240: the category switch over func_0206b7ec(worn item, r1)
WORN_STATS_END = 0x020653B8
TAKE_OFF_STATS = 0x0206B7EC
BACK_VIEWER_TEST = 0x02057DD4  # func_0205747c, B: `cmp r0, #7`, Cards leave through the card viewer's exit
NO_CATEGORY = 0xFF

# r1 = the category -> the flags of `cmp r1, #5`, with Cards counted as an equipment category; r1 is
# overwritten right after by the page kind, so it may change here.
PAGE_KIND_ASM = f"""
    cmp   r1, #{CATEGORY_CARDS}
    moveq r1, #0
    cmp   r1, #{LAST_EQUIP_CATEGORY}
    bx    lr
"""

# -> r0 = the item the shown member wears in the slot the Item page's category compares with, 0 if none or if
# the category is not an equipment one. Keeps every other register.
WORN_ASM = f"""
    push  {{r1-r3, lr}}
    ldr   r1, worn_page
    ldrb  r2, [r1, #{ITEM_PAGE_CATEGORY}]
    cmp   r2, #{CATEGORY_CARDS}
    moveq r2, #{CARD_SLOT}
    beq   worn_slot
    sub   r2, r2, #1
    cmp   r2, #{CATEGORY_ACCESSORY - 1}
    bhi   worn_none
    bne   worn_slot
    ldrb  r3, [r1]
    subs  r3, r3, #1
    bmi   worn_slot
    ldr   r0, worn_list
    add   r0, r0, r3, lsl #{ITEM_LIST_SHIFT}
    ldrh  r0, [r0]
    sub   r0, r0, #{FIRST_RING:#x}
    cmp   r0, #{RING_SPAN}
    movls r2, #{RING_SLOT}
worn_slot:
    ldr   r0, worn_work
    ldr   r0, [r0, #{MENU_WORK_MEMBER:#x}]
    ldr   r1, worn_party
    add   r1, r1, r0, lsl #2
    ldrsh r1, [r1]
    mov   r0, #{CHAR_RECORD_SIZE:#x}
    mul   r3, r1, r0
    ldr   r0, worn_slots
    add   r0, r0, r3
    add   r0, r0, r2, lsl #1
    ldrh  r0, [r0]
    pop   {{r1-r3, pc}}
worn_none:
    mov   r0, #0
    pop   {{r1-r3, pc}}
worn_page:
    .word {ITEM_PAGE:#x}
worn_list:
    .word {ITEM_LIST:#x}
worn_work:
    .word {MENU_WORK:#x}
worn_party:
    .word {PARTY:#x}
worn_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
"""

WORN_ICON_ASM = f"""
    bl    ${{cave_card_worn}}
    movs  r2, r0
    beq   {WORN_ICON_EXIT:#x}
    b     {WORN_ICON_END:#x}
"""

WORN_NAME_ASM = f"""
    mov   r4, r0
    bl    ${{cave_card_worn}}
    movs  r2, r0
    beq   {WORN_NAME_EXIT:#x}
    b     {WORN_NAME_END:#x}
"""

# r8 = the character id; the stats buffer is sp + 0x8c + 16 * character, as in each of the game's cases
WORN_STATS_ASM = f"""
    bl    ${{cave_card_worn}}
    add   r1, sp, #0x8c
    add   r1, r1, r8, lsl #4
    bl    {TAKE_OFF_STATS:#x}
    b     {WORN_STATS_END:#x}
"""


def equip_patches() -> tuple[CaveCode | AsmPatch | Patch, ...]:
    return (
        Patch(
            BACK_VIEWER_TEST,
            0xE3500007,
            0xE3500000 | NO_CATEGORY,
            "B on the Cards equip page goes back to the categories, not through the card viewer's exit",
        ),
        CaveCode("cave_card_page_kind", PAGE_KIND_ASM, "the Cards category opens an equip page"),
        hook(PAGE_KIND_TEST, PAGE_KIND_WORD, "bl ${cave_card_page_kind}", "the Cards category opens an equip page"),
        CaveCode("cave_card_worn", WORN_ASM, "the worn item an equip page compares with"),
        AsmPatch(WORN_ICON, WORN_ICON_END, 0xE59F01F0, 0x012FFF1E, WORN_ICON_ASM, "equip page: the worn item's icon"),
        AsmPatch(WORN_NAME, WORN_NAME_END, 0xE59F125C, 0x0A00007A, WORN_NAME_ASM, "equip page: the worn item's name"),
        AsmPatch(
            WORN_STATS, WORN_STATS_END, 0xE59F0460, 0xEB00190C, WORN_STATS_ASM, "equip page: the worn item's stats"
        ),
    )
