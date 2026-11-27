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

from dsde.cards_common import (
    CARD_FULL,
    CARD_FULL_SIZE,
    CARD_POINTS,
    FIRST_BOSS_CARD,
    FIRST_CARD,
    LAST_CARD,
    CARD_SLOT,
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    EQUIP_OFFSET,
    ITEM_SIZE,
    ITEM_TABLE,
    ITEM_TYPE_SLOT,
    RING_ITEMS,
    RING_SLOT,
    WHO_BITS,
)
from dsde.patching import AsmPatch, CaveCode, Patch
from dsde.skills_common import hook

CATEGORY_CARDS = 7
CATEGORY_ACCESSORY = 5
LAST_EQUIP_CATEGORY = 5
ITEM_PAGE = 0x02139FD4  # +0 the list cursor (1-based), +4 the category
ITEM_PAGE_CATEGORY = 4
ITEM_PAGE_KIND = 3  # 1 the list page, 2 the equip page
LIST_PAGE = 1
ITEM_LIST = 0x0213A008  # 8 bytes per entry: u32 item, u8 count
ITEM_LIST_SHIFT = 3
MENU_WORK = 0x0213B27C  # +0x644: the party slot shown
MENU_WORK_MEMBER = 0x644
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart
FIRST_RING = RING_ITEMS[0]
RING_SPAN = len(RING_ITEMS) - 1

PAGE_KIND_TEST = (
    0x0205CC10  # state 0x17: `cmp r1, #5` (r1 = the category); ls = the equip page
)
PAGE_KIND_WORD = 0xE3510005
WORN_ICON = 0x0206482C  # func_02064824 after its prologue: the category switch and slot 0's lookup
WORN_ICON_END = 0x0206488C  # draws the icon of item r2
WORN_ICON_EXIT = 0x020648A8
WORN_NAME = 0x02064A5C  # func_02064a4c after `bl 0x02067098`: the category switch and slot 0's lookup
WORN_NAME_END = 0x02064AB8  # draws the name of item r2
WORN_NAME_EXIT = 0x02064CA4
WORN_STATS = (
    0x020652F0  # func_02065240: the category switch over func_0206b7ec(worn item, r1)
)
WORN_STATS_END = 0x020653B8
TAKE_OFF_STATS = 0x0206B7EC
BACK_VIEWER_TEST = 0x02057DD4  # func_0205747c, B: `cmp r0, #7`, Cards leave through the card viewer's exit
LIST_WORN = (
    0x02063EC4  # func_02063e5c: `bl func_0206b880`, the worn count kept out of the list
)
LIST_WORN_WORD = 0xEB001E6D
WEARERS = 0x0206B880
COUNT_BLOCK = 0x0205D788  # state 0x19, equip page: the highlighted entry's count ("x 01"), sl = the text handle
COUNT_BLOCK_END = 0x0205D830
COUNT_ROW = 0x11
DRAW_STRING = (
    0x02066F90  # (handle, string, column, row, [sp] 0, [sp + 4] 5, [sp + 8] 0xB)
)
GLYPHS = 0x020A6438  # u16 offsets of the menu's short strings: 0 to 9 the digits, 10 a blank, 11 "/", 32 "x"
GLYPH_TEXT = 0x020A65F4
GLYPH_BLANK = 10
GLYPH_SLASH = 11
GLYPH_TIMES = 0x20
COUNT_RIGHT = 0x1D  # the count's last column
COUNT_TIMES = 0x1A
WORN_HIDE_LOOPS = (
    0x0205CF60,
    0x0205D670,
)  # states 0x18 and 0x19: hide the worn icon (sprite 10) when the slot is empty
WORN_HIDE_LOOP_SIZE = 0x54
WORN_HIDE_FIRST = 0xE5D61004
WORN_HIDE_LAST = 0xBAFFFFEA
HIDE_SPRITE = 0x02027AE8
MARK_TEST = 0x02063D88  # func_02063d44: `cmp r0, #8` / `bhs`: Tools and Cards get the "usable here" mark

# r1 = the category -> the flags of `cmp r1, #5`, with Cards counted as an equipment category, unless
# cave_card_list_once is set (the System list's Bestiary plank, feat_bestiary.py): then Cards opens the game's card list page
# once, and the flag is cleared. r1 is overwritten right after by the page kind, and r2 and r3 are reloaded,
# so they may change here.
PAGE_KIND_ASM = f"""
    cmp   r1, #{CATEGORY_CARDS}
    bne   pk_test
    ldr   r3, pk_once
    ldrb  r2, [r3]
    cmp   r2, #0
    moveq r1, #0
    movne r2, #0
    strbne r2, [r3]
pk_test:
    cmp   r1, #{LAST_EQUIP_CATEGORY}
    bx    lr
pk_once:
    .word ${{cave_card_list_once}}
"""

# B on the Item page, r0 = the category, r2 the Item page -> eq to leave through the card viewer's exit (state
# 0x59): Cards on the list page only (which the bestiary opens, feat_bestiary.py); the Cards equip page goes
# back to the categories as the equipment pages do. r3 is set before its next use on both paths.
BACK_KIND_ASM = f"""
    cmp   r0, #{CATEGORY_CARDS}
    bxne  lr
    ldrb  r3, [r2, #{ITEM_PAGE_KIND}]
    cmp   r3, #{LIST_PAGE}
    bx    lr
"""


# -> r0 = the item the shown member wears in the slot the Item page's category compares with, 0 if none or if
# the category is not an equipment one. Keeps every other register.
def worn_asm(rings: bool, cards: bool) -> str:
    """The worn item lookup for a mix: Cards compares with the card slot, a highlighted ring with the ring slot."""
    card = (
        f"""    cmp   r2, #{CATEGORY_CARDS}
    moveq r2, #{CARD_SLOT}
    beq   worn_slot
"""
        if cards
        else ""
    )
    ring = (
        f"""    bne   worn_slot
    ldrb  r3, [r1]
    subs  r3, r3, #1
    bmi   worn_slot
    ldr   r0, worn_list
    add   r0, r0, r3, lsl #{ITEM_LIST_SHIFT}
    ldrh  r0, [r0]
    sub   r0, r0, #{FIRST_RING:#x}
    cmp   r0, #{RING_SPAN}
    movls r2, #{RING_SLOT}
"""
        if rings
        else ""
    )
    return f"""
    push  {{r1-r3, lr}}
    ldr   r1, worn_page
    ldrb  r2, [r1, #{ITEM_PAGE_CATEGORY}]
{card}    sub   r2, r2, #1
    cmp   r2, #{CATEGORY_ACCESSORY - 1}
    bhi   worn_none
{ring}worn_slot:
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


# Called in place of the list builder's `bl func_0206b880` (r0 = the item -> r0 = how many are worn): a dragon
# ring or a card anyone may wear counts as none worn, so it stays listed while someone wears it and can be moved
# or taken off from the list.
def list_worn_asm(rings: bool, cards: bool) -> str:
    """The list's worn count for a mix: a dragon ring, or a card anyone may wear, counts as none worn."""
    ring = (
        f"""    sub   r1, r0, #{FIRST_RING:#x}
    cmp   r1, #{RING_SPAN}
    bls   list_none
"""
        if rings
        else ""
    )
    card = (
        f"""    ldr   r1, list_items
    mov   r2, #{ITEM_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r1, [r1]
    and   r2, r1, #{ITEM_TYPE_SLOT:#x}
    cmp   r2, #{CARD_SLOT}
    bne   list_count
    tst   r1, #{WHO_BITS:#x}
    bne   list_none
"""
        if cards
        else ""
    )
    return f"""
{ring}{card}list_count:
    b     {WEARERS:#x}
list_none:
    mov   r0, #0
    bx    lr
list_items:
    .word {ITEM_TABLE:#x}
"""


# r0 = the text handle, r1 = the row: the highlighted entry's count on the equip page. A monster card shows its
# points as current/max; a boss card shows nothing; anything else "x" and two digits, as the game does.
COUNT_ASM = f"""
    push  {{r4-r9, lr}}
    mov   r4, r0
    mov   r5, r1
    ldr   r0, cnt_page
    ldrb  r1, [r0]
    sub   r1, r1, #1
    ldr   r0, cnt_list
    add   r0, r0, r1, lsl #{ITEM_LIST_SHIFT}
    ldrh  r6, [r0]
    ldrb  r7, [r0, #4]
    sub   r0, r6, #{FIRST_CARD:#x}
    cmp   r0, #{FIRST_BOSS_CARD - FIRST_CARD - 1}
    bls   cnt_points
    cmp   r0, #{LAST_CARD - FIRST_CARD}
    bls   cnt_done
    mov   r0, r7
    mov   r1, #{COUNT_RIGHT:#x}
    mov   r2, #2
    mov   r3, #0
    bl    cnt_number
    mov   r0, #{GLYPH_TIMES:#x}
    mov   r1, #{COUNT_TIMES:#x}
    bl    cnt_glyph
    b     cnt_done
cnt_points:
    ldr   r1, cnt_points_base
    add   r1, r1, r0, lsl #1
    ldrsh r8, [r1]
    ldr   r1, cnt_full
    mov   r2, #{CARD_FULL_SIZE}
    mla   r1, r0, r2, r1
    ldrh  r9, [r1]
    mov   r0, r9
    mov   r1, #{COUNT_RIGHT:#x}
    mov   r2, #4
    mov   r3, #1
    bl    cnt_number
    mov   r0, #{GLYPH_SLASH}
    mov   r1, #{COUNT_RIGHT - 4:#x}
    bl    cnt_glyph
    mov   r0, r8
    mov   r1, #{COUNT_RIGHT - 5:#x}
    mov   r2, #4
    mov   r3, #1
    bl    cnt_number
cnt_done:
    pop   {{r4-r9, pc}}

@ r0 = value, r1 = its last column, r2 = digits, r3 = 1 to blank leading zeros; r4 handle, r5 row
cnt_number:
    push  {{r6-r10, lr}}
    mov   r6, r0
    mov   r7, r1
    mov   r8, r2
    mov   r9, r3
    mov   r10, #1
num_next:
    cmp   r10, #0
    bne   num_digit
    cmp   r9, #0
    beq   num_digit
    cmp   r6, #0
    moveq r0, #{GLYPH_BLANK}
    beq   num_draw
num_digit:
    mov   r1, #0
num_div:
    cmp   r6, #10
    blt   num_split
    sub   r6, r6, #10
    add   r1, r1, #1
    b     num_div
num_split:
    mov   r0, r6
    mov   r6, r1
num_draw:
    mov   r1, r7
    bl    cnt_glyph
    mov   r10, #0
    sub   r7, r7, #1
    subs  r8, r8, #1
    bne   num_next
    pop   {{r6-r10, pc}}

@ r0 = glyph index, r1 = column; r4 handle, r5 row
cnt_glyph:
    push  {{lr}}
    sub   sp, sp, #12
    mov   r3, #0
    str   r3, [sp]
    mov   r3, #5
    str   r3, [sp, #4]
    mov   r3, #0xb
    str   r3, [sp, #8]
    mov   r2, r1
    ldr   r3, cnt_glyphs
    add   r3, r3, r0, lsl #1
    ldrh  r3, [r3]
    ldr   r1, cnt_text
    add   r1, r1, r3
    mov   r0, r4
    mov   r3, r5
    bl    {DRAW_STRING:#x}
    add   sp, sp, #12
    pop   {{pc}}
cnt_page:
    .word {ITEM_PAGE:#x}
cnt_list:
    .word {ITEM_LIST:#x}
cnt_points_base:
    .word {CARD_POINTS:#x}
cnt_full:
    .word {CARD_FULL:#x}
cnt_glyphs:
    .word {GLYPHS:#x}
cnt_text:
    .word {GLYPH_TEXT:#x}
"""

COUNT_BLOCK_ASM = f"""
    mov   r0, sl
    mov   r1, #{COUNT_ROW:#x}
    bl    ${{cave_card_count}}
    mov   sb, #2
    add   fp, sp, #0x108
    b     {COUNT_BLOCK_END:#x}
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


def _worn_hide_asm(end: int, cards: bool) -> str:
    """In place of a loop over slots 0 to 4 that hides the worn icon (r6 = the Item page, fp the sprite set,
    r8 = 10, r7 = -1): hide it on an equipment page, Cards included, when cave_card_worn finds nothing."""
    card = (
        f"""    cmp   r1, #{CATEGORY_CARDS}
    beq   hide_check
"""
        if cards
        else ""
    )
    return f"""
    ldrb  r1, [r6, #{ITEM_PAGE_CATEGORY}]
{card}    sub   r1, r1, #1
    cmp   r1, #{LAST_EQUIP_CATEGORY - 1}
    bhi   hide_done
hide_check:
    bl    ${{cave_card_worn}}
    cmp   r0, #0
    bne   hide_done
    mov   r0, fp
    mov   r1, r8
    mov   r2, r7
    bl    {HIDE_SPRITE:#x}
hide_done:
    mov   sl, #{LAST_EQUIP_CATEGORY}
    b     {end:#x}
"""


def equip_patches() -> tuple[CaveCode | AsmPatch | Patch, ...]:
    """The Cards category's own patches on the Item page."""
    return (
        CaveCode(
            "cave_card_back_kind",
            BACK_KIND_ASM,
            "B on the Cards equip page goes back to the categories, not through the card viewer's exit",
        ),
        hook(
            BACK_VIEWER_TEST,
            0xE3500007,
            "bl ${cave_card_back_kind}",
            "B on the Cards equip page goes back to the categories, not through the card viewer's exit",
        ),
        CaveCode(
            "cave_card_list_once",
            "    .word 0",
            "set to open the Cards category's list page once instead of the equip page",
        ),
        CaveCode(
            "cave_card_page_kind",
            PAGE_KIND_ASM,
            "the Cards category opens an equip page",
        ),
        hook(
            PAGE_KIND_TEST,
            PAGE_KIND_WORD,
            "bl ${cave_card_page_kind}",
            "the Cards category opens an equip page",
        ),
        Patch(
            MARK_TEST,
            0xE3500008,
            0xE3500007,
            "a card's mark on the list is whether the member can wear it",
        ),
        CaveCode(
            "cave_card_count",
            COUNT_ASM,
            "equip page: a card's points in place of the count",
        ),
        AsmPatch(
            COUNT_BLOCK,
            COUNT_BLOCK_END,
            0xE5D12000,
            0xEB0025D7,
            COUNT_BLOCK_ASM,
            "equip page: a card's points",
        ),
    )


def shared_equip_patches(rings: bool, cards: bool) -> tuple[CaveCode | AsmPatch, ...]:
    """The equip page for a mix of the ring slot and the card overhaul: the worn item it compares with, and the
    worn rings and cards kept listed."""
    return (
        CaveCode(
            "cave_card_list_worn",
            list_worn_asm(rings, cards),
            "worn cards and dragon rings stay listed",
        ),
        hook(
            LIST_WORN,
            LIST_WORN_WORD,
            "bl ${cave_card_list_worn}",
            "worn cards and dragon rings stay listed",
        ),
        CaveCode(
            "cave_card_worn",
            worn_asm(rings, cards),
            "the worn item an equip page compares with",
        ),
        *(
            AsmPatch(
                loop,
                loop + WORN_HIDE_LOOP_SIZE,
                WORN_HIDE_FIRST,
                WORN_HIDE_LAST,
                _worn_hide_asm(loop + WORN_HIDE_LOOP_SIZE, cards),
                "equip page: the worn icon hidden by the slot the page compares with",
            )
            for loop in WORN_HIDE_LOOPS
        ),
        AsmPatch(
            WORN_ICON,
            WORN_ICON_END,
            0xE59F01F0,
            0x012FFF1E,
            WORN_ICON_ASM,
            "equip page: the worn item's icon",
        ),
        AsmPatch(
            WORN_NAME,
            WORN_NAME_END,
            0xE59F125C,
            0x0A00007A,
            WORN_NAME_ASM,
            "equip page: the worn item's name",
        ),
        AsmPatch(
            WORN_STATS,
            WORN_STATS_END,
            0xE59F0460,
            0xEB00190C,
            WORN_STATS_ASM,
            "equip page: the worn item's stats",
        ),
    )
