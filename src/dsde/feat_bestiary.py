"""The bestiary's card picture (docs/plan-cards.md 2.7): the points box at the foot of the card shows the level.

The card picture is one background layer (engine B BG2, 8bpp). func_0207e060 builds each card's 12 x 16 tile map
from a frame template (file 0xED/0xEC, kept at [0x0213F144] + 0x10) and the species' art, then writes the
points box: the frame's "P" (tiles 0xF0 / 0xF1 at card column 1, rows 13 and 14) and four digit pairs (columns 4
to 7, tiles 1 + 2 * digit and 2 + 2 * digit). The card slots are 0x2C-byte entries at 0x0213F1F8: a picture
entry +0x5C (-1 when unused), +0x64 the entry whose +0x20 holds the map buffer, +0x78 / +0x7C the card's column
and row in that map.

The frame's own tiles for that stretch of the green bar (0xD2 + column on row 13, 0xDB + column on row 14, the
template's running order) are a plain bar, so the box is cleared with them: nothing is drawn. In the field menu
only (mode 5), so the battle's card pictures keep their points. The level is then written over the bar on the
text layer (BG1, drawn above BG2) with the menu's own short strings: "LV" (string 22) and digits.
"""

from dsde.jp_hint_pairs import USA_TABLE
from dsde.cards_common import CHAR_RECORD_SIZE, CHAR_RECORDS, CHARACTERS
from dsde.patching import AsmPatch, CaveCode, Feature, Patch
from dsde.skills_common import hook

GAME_MODE = 0x020B000C
FIELD_MENU_MODE = 5
CARD_SLOTS = 0x0213F1F8
CARD_SLOT_SIZE = 0x2C
CARD_PICTURES = 4
PICTURE_USED = 0x5C
PICTURE_OWNER = 0x64
OWNER_MAP = 0x20
PICTURE_COLUMN = 0x78
PICTURE_ROW = 0x7C
MAP_WIDTH_SHIFT = 5  # 32 entries a row
BOX_TOP_ROW = 13
BOX_FIRST_COLUMN = 1  # the "P"
BOX_END_COLUMN = 8  # past the last digit
BAR_TOP_TILE = 0xD2  # + column: the frame template's plain bar, row 13
BAR_BOTTOM_TILE = 0xDB  # + column: row 14
PALETTE_BITS = 0xF000
MAP_ROW_BYTES = 0x40

CARDS_DONE = (
    0x0207EABC  # func_0207e060: `mov r4, #1`, every card map built for this frame
)
CARDS_DONE_WORD = 0xE3A04001

VIEWER_TEXT = (
    0x0205D098  # card viewer text: the count's digit loop starts; sl = text handle
)
VIEWER_TEXT_WORDS = (0xE3A09000, 0xE59FB06C)
ATTRIBUTE_LABEL = 0x0205D260  # the "Attribute" label: drawn as before
DESCRIPTION_DRAW = 0x0205D42C  # `bl 0x02066c44`, the card's description
DESCRIPTION_DRAW_WORD = 0xEB002604
NOP = 0xE1A00000
DRAW_STRING = (
    0x02066F90  # (handle, string, column, row, [sp] 0, [sp + 4] 5, [sp + 8] 0xB)
)
GLYPHS = 0x020A6438  # u16 offsets of the menu's short strings: 0 to 9 the digits, 22 "LV", 23 "HP"
GLYPH_TEXT = 0x020A65F4
GLYPH_LV = 22
ITEM_PAGE = 0x02139FD4  # +0 the list cursor (1-based)
ITEM_LIST = 0x0213A008  # 8 bytes per entry: u32 item
ITEM_LIST_SHIFT = 3
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart
PARTY_SLOTS = 3
LEVEL_OFFSET = 0xC  # the level index: the level shown is one more
MAX_SHOWN_LEVEL = 99
LEVEL_ROW = 20  # text rows are 8 pixels: the bar is pixels 160 to 175
LV_COLUMN = 21
LEVEL_LAST_COLUMN = 25
VALUE_WIDTH = 6  # a value's last column, from its label's first

FIRST_CARD = 0xD8
FIRST_BOSS_SPECIES = (
    34  # docs/re-enemies.md: species 0 to 33 have four rows each, bosses one
)
ROWS_PER_SPECIES_SHIFT = 2
BOSS_ROW_OFFSET = 0x66
DARK_JIAN_SPECIES = 151 - BOSS_ROW_OFFSET
ENEMY_TABLE = 0x02097CE4
ENEMY_ROW_SIZE = 0x54
STAT_LEVEL0 = 4  # s16 stats at level 0: HP, MP, ATK, DEF, AGI, INT, DEX, LUCK
STAT_LEVEL98 = 0x18
STAT_AT_LEVEL = 0x02069D7C  # (level 0 stat, level 98 stat, level) -> the stat, as the battle sets it
# The fight's lowest level, species 34 to 53 (docs/boss-exp.md); Dark Jian's entry is unused.
BOSS_LEVELS = (
    7,
    10,
    10,
    10,
    10,
    10,
    10,
    10,
    16,
    16,
    16,
    23,
    24,
    28,
    36,
    28,
    40,
    42,
    42,
    97,
)
# Dark Jian copies Jian (func_02069ad8, row 151): Jian's stats with his gear, as func_0206b030(0, buffer, 0)
# builds them (eight s16 in the enemy table's order), then HP x 6, ATK x 4 / 5, DEF x 6 / 5.
JIAN_STATS = 0x0206B030
JIAN = 0
WITH_GEAR = 0
STAT_BUFFER = 0x10
# The panel: (label string, stat index, Dark Jian's multiply, divide, column, row). Rows 9 and 11
# keep the game's Attribute and Weakness lines.
PANEL = (
    (23, 0, 6, 1, 1, 7),  # HP
    (25, 2, 4, 5, 1, 13),  # ATK
    (26, 3, 6, 5, 10, 13),  # DEF
    (27, 4, 1, 1, 1, 15),  # AGI
    (28, 5, 1, 1, 10, 15),  # INT
    (29, 6, 1, 1, 1, 17),  # DEX
    (30, 7, 1, 1, 10, 17),  # LUK
)
PANEL_ENTRY = 6
PANEL_ASM = "\n".join(
    "    .byte " + ", ".join(str(v) for v in entry) for entry in PANEL
)
BOSS_LEVELS_ASM = "    .byte " + ", ".join(str(v) for v in BOSS_LEVELS)

BOX_ASM = f"""
    push  {{r0-r8, lr}}
    ldr   r0, bx_mode
    ldr   r0, [r0]
    cmp   r0, #{FIELD_MENU_MODE}
    bne   bx_done
    ldr   r4, bx_slots
    mov   r5, #0
    mov   r8, #{CARD_SLOT_SIZE}
bx_picture:
    mla   r6, r5, r8, r4
    ldr   r1, [r6, #{PICTURE_USED}]
    cmn   r1, #1
    beq   bx_next
    ldr   r1, [r6, #{PICTURE_OWNER}]
    mla   r2, r1, r8, r4
    ldr   r2, [r2, #{OWNER_MAP}]
    cmp   r2, #0
    beq   bx_next
    ldr   r1, [r6, #{PICTURE_ROW}]
    add   r1, r1, #{BOX_TOP_ROW}
    ldr   r3, [r6, #{PICTURE_COLUMN}]
    add   r1, r3, r1, lsl #{MAP_WIDTH_SHIFT}
    add   r2, r2, r1, lsl #1
    ldrh  r3, [r2]
    and   r3, r3, #{PALETTE_BITS:#x}
    mov   r1, #{BOX_FIRST_COLUMN}
bx_tile:
    mov   r0, r1, lsl #1
    add   r7, r1, #{BAR_TOP_TILE:#x}
    orr   r7, r7, r3
    strh  r7, [r2, r0]
    add   r0, r0, #{MAP_ROW_BYTES:#x}
    add   r7, r1, #{BAR_BOTTOM_TILE:#x}
    orr   r7, r7, r3
    strh  r7, [r2, r0]
    add   r1, r1, #1
    cmp   r1, #{BOX_END_COLUMN}
    blt   bx_tile
bx_next:
    add   r5, r5, #1
    cmp   r5, #{CARD_PICTURES}
    blt   bx_picture
bx_done:
    pop   {{r0-r8, lr}}
    mov   r4, #1
    bx    lr
bx_mode:
    .word {GAME_MODE:#x}
bx_slots:
    .word {CARD_SLOTS:#x}
"""

# In place of the count, "Card", and MAX Point: the level on the card's bar and the stats panel. r4 handle, r5
# species, r6 level index, r7 the enemy row (0 for Dark Jian, whose stats are in the buffer at sp), r8 the panel
# entry, r9 the character records.
STATS_ASM = f"""
    push  {{r4-r11, lr}}
    sub   sp, sp, #{STAT_BUFFER:#x}
    mov   r4, sl
    ldr   r0, st_page
    ldrb  r0, [r0]
    sub   r0, r0, #1
    ldr   r1, st_list
    ldr   r0, [r1, r0, lsl #{ITEM_LIST_SHIFT}]
    sub   r5, r0, #{FIRST_CARD:#x}
    ldr   r9, st_records
    cmp   r5, #{DARK_JIAN_SPECIES}
    bne   st_enemy
    mov   r7, #0
    ldr   r6, [r9, #{LEVEL_OFFSET:#x}]
    mov   r0, #{JIAN}
    mov   r1, sp
    mov   r2, #{WITH_GEAR}
    bl    {JIAN_STATS:#x}
    b     st_level
st_enemy:
    cmp   r5, #{FIRST_BOSS_SPECIES}
    blt   st_regular
    ldr   r0, st_boss_levels
    sub   r1, r5, #{FIRST_BOSS_SPECIES}
    ldrb  r6, [r0, r1]
    add   r0, r5, #{BOSS_ROW_OFFSET:#x}
    b     st_row
st_regular:
    ldr   r1, st_party
    mov   r6, #0
    mov   r8, #0
st_member:
    ldrsh r0, [r1]
    cmp   r0, #{CHARACTERS}
    bhs   st_skip
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r0, r3, r9
    ldr   r2, [r2, #{LEVEL_OFFSET:#x}]
    cmp   r2, r6
    movgt r6, r2
st_skip:
    add   r1, r1, #4
    add   r8, r8, #1
    cmp   r8, #{PARTY_SLOTS}
    blt   st_member
    mov   r0, r5, lsl #{ROWS_PER_SPECIES_SHIFT}
st_row:
    ldr   r1, st_enemies
    mov   r2, #{ENEMY_ROW_SIZE:#x}
    mla   r7, r0, r2, r1
st_level:
    mov   r0, #{GLYPH_LV}
    mov   r1, #{LV_COLUMN}
    mov   r2, #{LEVEL_ROW}
    bl    st_glyph
    add   r0, r6, #1
    cmp   r0, #{MAX_SHOWN_LEVEL}
    movgt r0, #{MAX_SHOWN_LEVEL}
    mov   r1, #{LEVEL_LAST_COLUMN}
    mov   r2, #{LEVEL_ROW}
    bl    st_number
    ldr   r8, st_panel
    mov   r10, #0
st_entry:
    ldrb  r0, [r8]
    ldrb  r1, [r8, #4]
    ldrb  r2, [r8, #5]
    bl    st_glyph
    cmp   r7, #0
    beq   st_jian
    ldrb  r3, [r8, #1]
    add   r11, r7, r3, lsl #1
    ldrsh r0, [r11, #{STAT_LEVEL0}]
    ldrsh r1, [r11, #{STAT_LEVEL98}]
    mov   r2, r6
    bl    {STAT_AT_LEVEL:#x}
    b     st_value
st_jian:
    ldrb  r3, [r8, #1]
    add   r3, sp, r3, lsl #1
    ldrsh r0, [r3]
    ldrb  r3, [r8, #2]
    mul   r0, r3, r0
    ldrb  r3, [r8, #3]
    mov   r1, #0
st_divide:
    cmp   r0, r3
    blt   st_divided
    sub   r0, r0, r3
    add   r1, r1, #1
    b     st_divide
st_divided:
    mov   r0, r1
st_value:
    cmp   r0, #0
    movlt r0, #0
    ldrb  r1, [r8, #4]
    add   r1, r1, #{VALUE_WIDTH}
    ldrb  r2, [r8, #5]
    bl    st_number
    add   r8, r8, #{PANEL_ENTRY}
    add   r10, r10, #1
    cmp   r10, #{len(PANEL)}
    blt   st_entry
    add   sp, sp, #{STAT_BUFFER:#x}
    pop   {{r4-r11, pc}}

@ r0 = value (0 or more), r1 = its last column, r2 = row: the digits, right-aligned. Keeps r4 to r11.
st_number:
    push  {{r5-r7, lr}}
    mov   r5, r0
    mov   r6, r1
    mov   r7, r2
st_digit:
    mov   r1, #0
st_tens:
    cmp   r5, #10
    blt   st_draw
    sub   r5, r5, #10
    add   r1, r1, #1
    b     st_tens
st_draw:
    mov   r0, r5
    mov   r5, r1
    mov   r1, r6
    mov   r2, r7
    bl    st_glyph
    sub   r6, r6, #1
    cmp   r5, #0
    bne   st_digit
    pop   {{r5-r7, pc}}

@ r0 = short string index, r1 = column, r2 = row; r4 = text handle. Keeps r4 to r11.
st_glyph:
    push  {{lr}}
    sub   sp, sp, #12
    mov   r3, #0
    str   r3, [sp]
    mov   r3, #5
    str   r3, [sp, #4]
    mov   r3, #0xb
    str   r3, [sp, #8]
    mov   r3, r2
    mov   r2, r1
    ldr   r1, st_glyphs
    add   r1, r1, r0, lsl #1
    ldrh  r1, [r1]
    ldr   r0, st_text
    add   r1, r0, r1
    mov   r0, r4
    bl    {DRAW_STRING:#x}
    add   sp, sp, #12
    pop   {{pc}}
st_page:
    .word {ITEM_PAGE:#x}
st_list:
    .word {ITEM_LIST:#x}
st_records:
    .word {CHAR_RECORDS:#x}
st_party:
    .word {PARTY:#x}
st_enemies:
    .word {ENEMY_TABLE:#x}
st_glyphs:
    .word {GLYPHS:#x}
st_text:
    .word {GLYPH_TEXT:#x}
st_panel:
    .word ${{cave_bestiary_tables}}
st_boss_levels:
    .word ${{cave_bestiary_tables}} + {len(PANEL) * PANEL_ENTRY}
"""

TABLES_ASM = f"""
{PANEL_ASM}
{BOSS_LEVELS_ASM}
    .align 2
"""

# TEMPORARY (Jeff, 2026-11-26): delete the Y path (Y_ASM, cave_bestiary_y and its hook) once the System list's
# Bestiary plank is approved.
# Y on the Cards equip page opens the bestiary: the game's own card list page (the viewer), on the same card.
# func_0205747c (the Item page's input) after its prologue: in place of `ldrh r1, [sp, #0x10]`. On Y it sets
# cave_card_list_once (feat_card_equip.py), asks for state 0x17 (which picks the page again) through the
# change state 0x4F, plays the menu's confirm sound, and leaves the function by its own epilogue; otherwise it
# puts back r2 and r3 (the arguments, still on the stack) and does the replaced load.
ITEM_INPUT = 0x02057484
ITEM_INPUT_WORD = 0xE1DD11B0
PAD = 0x020AFF74  # +6 the buttons pressed this frame
PAD_NEW = 6
BUTTON_Y = 0x800
ITEM_PAGE_NEXT = 1  # the state to go to through 0x4F
ITEM_PAGE_KIND = 3  # 1 the list page, 2 the equip page
ITEM_PAGE_CATEGORY = 4
CATEGORY_CARDS = 7
EQUIP_PAGE = 2
LIST_PAGE = 1
PICK_PAGE_STATE = 0x17
MENU_STATE = 0x020AFF84  # +0x8c the field menu's state
MENU_STATE_OFFSET = 0x8C
CHANGE_STATE = 0x4F
MENU_WORK = 0x0213B27C  # +0x610 set by the function's own epilogue
MENU_REFRESH = 0x610
# The equip page's portrait of the member (state 0x24: func_020275b4(0x0213AC70, 2, 2 * character, 0)); the
# list page does not use it, so Y hides it (func_02027ae8(set, 2, -1)).
HIDE_SPRITE = 0x02027AE8
SPRITES = 0x0213AC70
PORTRAIT_SPRITE = 2
PLAY_SOUND = 0x02043FD8  # (0, 1) the confirm sound
CONFIRM_SOUND = 1

Y_ASM = f"""
    ldr   r0, by_pad
    ldrh  r0, [r0, #{PAD_NEW}]
    tst   r0, #{BUTTON_Y:#x}
    beq   by_no
    ldr   r0, by_page
    ldrb  r1, [r0, #{ITEM_PAGE_CATEGORY}]
    cmp   r1, #{CATEGORY_CARDS}
    bne   by_no
    ldrb  r1, [r0, #{ITEM_PAGE_KIND}]
    cmp   r1, #{EQUIP_PAGE}
    bne   by_no
    ldr   r1, by_once
    mov   r2, #1
    strb  r2, [r1]
    mov   r2, #{PICK_PAGE_STATE:#x}
    strb  r2, [r0, #{ITEM_PAGE_NEXT}]
    ldr   r1, by_state
    mov   r2, #{CHANGE_STATE:#x}
    str   r2, [r1, #{MENU_STATE_OFFSET:#x}]
    mov   r0, #0
    mov   r1, #{CONFIRM_SOUND}
    bl    {PLAY_SOUND:#x}
    ldr   r0, by_sprites
    mov   r1, #{PORTRAIT_SPRITE}
    mvn   r2, #0
    bl    {HIDE_SPRITE:#x}
    ldr   r0, by_work
    mov   r1, #1
    str   r1, [r0, #{MENU_REFRESH:#x}]
    pop   {{r4, r5, r6, lr}}
    add   sp, sp, #0x10
    bx    lr
by_no:
    ldr   r2, [sp, #0x18]
    ldr   r3, [sp, #0x1c]
    ldrh  r1, [sp, #0x10]
    bx    lr
by_pad:
    .word {PAD:#x}
by_page:
    .word {ITEM_PAGE:#x}
by_once:
    .word ${{cave_card_list_once}}
by_state:
    .word {MENU_STATE:#x}
by_work:
    .word {MENU_WORK:#x}
by_sprites:
    .word {SPRITES:#x}
"""

# The card viewer's exit (state 0x59) frees the card pictures and goes to the categories with the category
# cleared. Leaving the bestiary (Cards), it goes back to the Cards equip page instead: in place of
# `strb r1, [r2, #4]` (r1 = 0, r2 the Item page, r4 the old category, r3 the next state, 0x14; r0 is live).
# Opened from the System list, it goes back there instead (state 0x33, the cursor on the Bestiary plank).
VIEWER_EXIT = 0x02061DC4
VIEWER_EXIT_WORD = 0xE5C21004

BESTIARY_CURSOR = (
    6  # the System list's Bestiary plank (the cursor counts two per plank)
)
SYSTEM_RETURN_CURSOR = BESTIARY_CURSOR
SYSTEM_SETUP_STATE = 0x33
SYSTEM_ENTRY_STATE = (
    0x5A  # the top menu's way into the System list (it goes on to 0x33)
)
# Leaving the Item page as B on its categories does (func_0205747c): the header tab, then the Item page's three
# heap blocks freed (func_02005224(0, -1, block)): the two at 0x02139F2C and the screen block at 0x02139EF0.
HEADER_TAB = 0x02059BCC
HEADER_TAB_LEAVE_ITEMS = 2
FREE = 0x02005224
ITEM_BLOCKS = 0x02139F2C
SCREEN_BLOCK = 0x02139EF0
# The top screen's panels: the categories (state 0x14) show panel 4 (the portrait's backdrop) and the System list
# (0x33) does not, since it is always entered from the top menu, which has it; so the way back shows it.
SHOW_PANEL = 0x02018ADC
PANELS = 0x020B05B0
TOP_PANEL = 4

EXIT_ASM = f"""
    ldr   ip, ex_from_system
    ldrb  r1, [ip]
    cmp   r1, #0
    mov   r1, #0
    beq   ex_cards
    push  {{r0, r2, lr}}
    strb  r1, [ip]
    strb  r1, [r2, #{ITEM_PAGE_CATEGORY}]
    mov   r0, #0
    mov   r1, #{HEADER_TAB_LEAVE_ITEMS}
    bl    {HEADER_TAB:#x}
    ldr   r3, ex_blocks
    ldr   r2, [r3]
    mov   r0, #0
    mvn   r1, #0
    bl    {FREE:#x}
    ldr   r3, ex_blocks
    ldr   r2, [r3, #4]
    mov   r0, #0
    mvn   r1, #0
    bl    {FREE:#x}
    ldr   r3, ex_screen_block
    ldr   r2, [r3]
    mov   r0, #0
    mvn   r1, #0
    bl    {FREE:#x}
    ldr   r0, ex_panels
    mov   r1, #{TOP_PANEL}
    bl    {SHOW_PANEL:#x}
    pop   {{r0, r2, lr}}
    mov   r1, #0
    mov   r3, #{SYSTEM_ENTRY_STATE:#x}
    mov   r4, #{SYSTEM_RETURN_CURSOR // 2 + 1}
    bx    lr
ex_cards:
    cmp   r4, #{CATEGORY_CARDS}
    moveq r3, #{PICK_PAGE_STATE:#x}
    strbne r1, [r2, #{ITEM_PAGE_CATEGORY}]
    bx    lr
ex_from_system:
    .word ${{cave_bestiary_from_system}}
ex_blocks:
    .word {ITEM_BLOCKS:#x}
ex_screen_block:
    .word {SCREEN_BLOCK:#x}
ex_panels:
    .word {PANELS:#x}
"""

# The System list (field menu states 0x33 to 0x35) gets a Bestiary plank between Music Hall and Quit Game. The
# list is the menu table at 0x020A5968 (u16 6, u16 entry count, pointer to 0x10-byte entries): two sprites a
# plank, the blank plank (sprite bank 5, cell 0, selected 1) and its lettering (cells 4 and 5 Message Speed, 2 and
# 3 Save, 16 and 17 Music Hall, 6 and 7 Quit Game), at x 128 and y 24, 60, 96, 132. The cursor steps by 2 and
# stops at count - 2. The new table in the cave has five planks 29 pixels apart; the Bestiary plank's second
# entry is the blank plank again, and its word is written in the menu font (text handle 0, the bottom screen's
# text layer) by the hint line's drawer, so it is redrawn whenever that line is.
SYSTEM_LIST = 0x020A5968
SYSTEM_LIST_HEAD = 0x00080006  # u16 6, u16 8 entries
SYSTEM_LIST_HEAD_NEW = 0x000A0006
SYSTEM_LIST_ENTRIES = 0x020A596C
SYSTEM_LIST_ENTRIES_OLD = 0x020A5E68
# State 0x33 greys the Save plank out when saving is not allowed, through its own pointer to the entries.
SAVE_PLANK_POOL = 0x02060454
PLANK_YS = (26, 55, 84, 113, 142)  # the word's text row 13 sits on the Bestiary plank
PLANK_BASE = "0x05, 0x00, 0x01, 0x05"
PLANK_BASE_TAIL = "0x0001, 0x8000, 0x0009, 0x0000"
LETTERING_TAIL = "0x0000, 0xA027, 0x0009, 0x0000"
PLANK_LETTERING = ((0x04, 0x05), (0x02, 0x03), (0x10, 0x11), None, (0x06, 0x07))


def _plank_rows() -> str:
    rows = []
    for y, letters in zip(PLANK_YS, PLANK_LETTERING, strict=True):
        rows.append(f"    .byte {PLANK_BASE}\n    .short 128, {y}, {PLANK_BASE_TAIL}")
        if letters is None:
            rows.append(
                f"    .byte {PLANK_BASE}\n    .short 128, {y}, {PLANK_BASE_TAIL}"
            )
        else:
            rows.append(
                f"    .byte 0x05, {letters[0]:#x}, {letters[1]:#x}, 0xff\n    .short 128, {y}, {LETTERING_TAIL}"
            )
    return "\n".join(rows)


PLANKS_ASM = _plank_rows()

QUIT_KEY_OLD = 12  # state 0x35: the key code is 6 + the cursor
BESTIARY_KEY = 6 + BESTIARY_CURSOR
QUIT_KEY_NEW = 6 + BESTIARY_CURSOR + 2
NOTHING_KEY = 7  # a code the jump table ignores
# B on Quit Game's prompts (states 0x44 and 0x48) puts the cursor back on Quit Game: 6 before, 8 now.
QUIT_RETURNS = (
    (0x020611D8, 0xE3A06006, 0xE3A06008),
    (0x020613E4, 0xE3A03006, 0xE3A03008),
)
# A on Quit Game puts its brackets on the plank's entry (func_02058fe4(list, 6, ...)): 8 now.
QUIT_BRACKETS = (0x02060010, 0xE3A01006, 0xE3A01008)
LAST_KEY = 0xC

# State 0x35 dispatches the key code with `cmp r0, #0xc` / `addls pc, pc, r0, lsl #2` (0x0205FE78). Quit Game's
# code moves from 12 to 14 and is turned back into 12; 12 is now the Bestiary plank: it opens the game's card list
# page as Y does, notes that it came from here, and hands the jump table a code it ignores.
SYSTEM_KEY = 0x0205FE78
SYSTEM_KEY_WORD = 0xE350000C
MENU_CURSOR = 0x02139F40  # the shown list's cursor; state 0x18 opens the card list at cursor / 2 + 1
# In as the top menu's Items does (func_02059f84 case 10): the header tab, the Item page's screen block
# (func_02066c88(4, 0x3A, 0x1A1, 0) kept at 0x02139EF0), then state 0x53, which goes to the categories (0x14).
HEADER_TAB_ENTER_ITEMS = 0
ALLOC = 0x02066C88
ALLOC_KIND = 4
ITEM_SCREEN_ID = 0x3A
ITEM_SCREEN_SIZE = 0x1A1
ITEMS_ENTRY_STATE = 0x53

SYSTEM_KEY_ASM = f"""
    cmp   r0, #{QUIT_KEY_NEW}
    moveq r0, #{QUIT_KEY_OLD}
    beq   sk_done
    cmp   r0, #{BESTIARY_KEY}
    bne   sk_done
    push  {{r1-r3, lr}}
    mov   r0, #0
    mov   r1, #{CONFIRM_SOUND}
    bl    {PLAY_SOUND:#x}
    mov   r0, #0
    mov   r1, #{HEADER_TAB_ENTER_ITEMS}
    bl    {HEADER_TAB:#x}
    mov   r0, #{ALLOC_KIND}
    mov   r1, #{ITEM_SCREEN_ID:#x}
    ldr   r2, sk_screen_size
    mov   r3, #0
    bl    {ALLOC:#x}
    ldr   r1, sk_screen_block
    str   r0, [r1]
    ldr   r1, sk_once
    mov   r0, #1
    strb  r0, [r1]
    ldr   r1, sk_from_system
    strb  r0, [r1]
    ldr   r1, sk_page
    mov   r0, #{ITEMS_ENTRY_STATE:#x}
    strb  r0, [r1, #{ITEM_PAGE_NEXT}]
    ldr   r1, sk_state
    mov   r0, #{CHANGE_STATE:#x}
    str   r0, [r1, #{MENU_STATE_OFFSET:#x}]
    pop   {{r1-r3, lr}}
    mov   r0, #{NOTHING_KEY}
sk_done:
    cmp   r0, #{LAST_KEY:#x}
    bx    lr
sk_once:
    .word ${{cave_card_list_once}}
sk_from_system:
    .word ${{cave_bestiary_from_system}}
sk_page:
    .word {ITEM_PAGE:#x}
sk_state:
    .word {MENU_STATE:#x}
sk_screen_block:
    .word {SCREEN_BLOCK:#x}
sk_screen_size:
    .word {ITEM_SCREEN_SIZE:#x}
"""

# The Item page's categories (state 0x15, `strb r3, [r1, #1]` with r3 = 0x16, r1 the Item page): while the
# bestiary is on its way in from the System list (cave_card_list_once still set), they go on to Cards' page
# (state 0x17, category 7, the list's cursor at the first card) as an A on Cards would.
CATEGORIES_NEXT = 0x0205CA8C
CATEGORIES_NEXT_WORD = 0xE5C13001

CATEGORIES_ASM = f"""
    ldr   ip, ct_once
    ldrb  ip, [ip]
    cmp   ip, #0
    beq   ct_done
    mov   ip, #{CATEGORY_CARDS}
    strb  ip, [r1, #{ITEM_PAGE_CATEGORY}]
    ldr   ip, ct_cursor
    mov   r3, #0
    strb  r3, [ip]
    mov   r3, #{PICK_PAGE_STATE:#x}
ct_done:
    strb  r3, [r1, #{ITEM_PAGE_NEXT}]
    bx    lr
ct_once:
    .word ${{cave_card_list_once}}
ct_cursor:
    .word {MENU_CURSOR:#x}
"""

# The System list's hint is message cursor / 2 + 0x15 (states 0x33 and 0x35: `add r1, r1, #0x15`). Quit Game's
# moves down a plank; the Bestiary plank's is a message of its own (BESTIARY_HINT, a number no message uses).
SYSTEM_HINTS = (0x0205FBE8, 0x02060094)
SYSTEM_HINT_WORD = 0xE2811015
FIRST_SYSTEM_HINT = 0x15
BESTIARY_HINT = -101
BESTIARY_PLANK = BESTIARY_CURSOR // 2

HINT_PICK_ASM = f"""
    cmp   r1, #{BESTIARY_PLANK}
    mvneq r1, #{-BESTIARY_HINT - 1}
    bxeq  lr
    subgt r1, r1, #1
    add   r1, r1, #{FIRST_SYSTEM_HINT:#x}
    bx    lr
"""

# The hint line's drawer (0x02062000, `add r1, r4, r1`: r4 the strings, r1 the message's offset; r0 the text
# handle, r2 column 4, r3 row 0x15): our message's text instead, and while the hint is one of the System list's,
# the Bestiary plank's word as well.
HINT_DRAW = 0x02062000
HINT_DRAW_WORD = 0xE0841001
HELP = 0x02139EE8  # +2 the message shown (s8)
LAST_SYSTEM_HINT = 0x18
SYSTEM_IDLE_STATE = (
    0x35  # the plank's word only while the System list is up (states 0x33 to 0x35)
)
PLANK_TEXT_COLUMN = 12
PLANK_TEXT_ROW = 13
HINT_TEXT = "Monsters beaten"
PLANK_TEXT = "Bestiary"

QUIT_PROMPT_STATE = 0x43  # the word also stays under Quit Game's two prompts (0x43, 0x44 and 0x47, 0x48)
QUIT_PROMPT_IDLE = 0x44
QUIT_SURE_STATE = 0x47
QUIT_SURE_IDLE = 0x48

HINT_DRAW_ASM = f"""
    push  {{r0-r6, lr}}
    mov   r5, r0
    ldr   r6, hd_help
    ldrsb r6, [r6, #2]
    ldr   r0, hd_state
    ldr   r0, [r0, #{MENU_STATE_OFFSET:#x}]
    cmp   r0, #{SYSTEM_SETUP_STATE:#x}
    blt   hd_no_plank
    cmp   r0, #{SYSTEM_IDLE_STATE:#x}
    ble   hd_plank
    sub   r0, r0, #{QUIT_PROMPT_STATE:#x}
    cmp   r0, #{QUIT_PROMPT_IDLE - QUIT_PROMPT_STATE}
    bls   hd_plank
    sub   r0, r0, #{QUIT_SURE_STATE - QUIT_PROMPT_STATE}
    cmp   r0, #{QUIT_SURE_IDLE - QUIT_SURE_STATE}
    bhi   hd_no_plank
hd_plank:
    sub   sp, sp, #12
    mov   r0, #0
    str   r0, [sp]
    str   r0, [sp, #4]
    mov   r0, #10
    str   r0, [sp, #8]
    mov   r0, r5
    ldr   r1, hd_plank_text
    mov   r2, #{PLANK_TEXT_COLUMN}
    mov   r3, #{PLANK_TEXT_ROW}
    bl    {DRAW_STRING:#x}
    add   sp, sp, #12
hd_no_plank:
    cmn   r6, #{-BESTIARY_HINT}
    bne   hd_game
    pop   {{r0-r6, lr}}
    ldr   r1, hd_hint_text
    bx    lr
hd_game:
    pop   {{r0-r6, lr}}
    add   r1, r4, r1
    bx    lr
hd_help:
    .word {HELP:#x}
hd_state:
    .word {MENU_STATE:#x}
hd_plank_text:
    .word ${{cave_bestiary_words}}
hd_hint_text:
    .word ${{cave_bestiary_words}} + {len(PLANK_TEXT) + 1}
"""

_CODES = {char: code for code, char in USA_TABLE.items()}
TEXT_END = 0xFF


def _encode(text: str) -> str:
    return (
        "    .byte " + ", ".join(f"{_CODES[c]:#x}" for c in text) + f", {TEXT_END:#x}"
    )


WORDS_ASM = _encode(PLANK_TEXT) + "\n" + _encode(HINT_TEXT) + "\n    .align 2"


BESTIARY = Feature(
    "bestiary",
    (
        CaveCode(
            "cave_bestiary_box",
            BOX_ASM,
            "the card's points box shows a plain bar in the menu",
        ),
        hook(
            CARDS_DONE,
            CARDS_DONE_WORD,
            "bl ${cave_bestiary_box}",
            "the card's points box shows a plain bar in the menu",
        ),
        CaveCode(
            "cave_bestiary_tables",
            TABLES_ASM,
            "the bestiary's panel layout and boss levels",
        ),
        CaveCode(
            "cave_bestiary_stats",
            STATS_ASM,
            "the card viewer shows the level and the enemy's stats",
        ),
        AsmPatch(
            VIEWER_TEXT,
            VIEWER_TEXT + 8,
            VIEWER_TEXT_WORDS[0],
            VIEWER_TEXT_WORDS[1],
            f"bl ${{cave_bestiary_stats}}\n    b {ATTRIBUTE_LABEL:#x}",
            "the card viewer shows the level and the enemy's stats, not the count and MAX Point",
        ),
        Patch(
            DESCRIPTION_DRAW,
            DESCRIPTION_DRAW_WORD,
            NOP,
            "the card viewer shows no description",
        ),
        CaveCode(
            "cave_bestiary_y", Y_ASM, "Y on the Cards equip page opens the bestiary"
        ),
        hook(
            ITEM_INPUT,
            ITEM_INPUT_WORD,
            "bl ${cave_bestiary_y}",
            "Y on the Cards equip page opens the bestiary",
        ),
        CaveCode(
            "cave_bestiary_exit",
            EXIT_ASM,
            "B in the bestiary goes back to the Cards equip page",
        ),
        hook(
            VIEWER_EXIT,
            VIEWER_EXIT_WORD,
            "bl ${cave_bestiary_exit}",
            "B in the bestiary goes back to the Cards equip page",
        ),
        CaveCode(
            "cave_bestiary_from_system",
            "    .word 0",
            "set while the bestiary was opened from the System list",
        ),
        CaveCode("cave_system_planks", PLANKS_ASM, "the System list's five planks"),
        Patch(
            SYSTEM_LIST,
            SYSTEM_LIST_HEAD,
            SYSTEM_LIST_HEAD_NEW,
            "the System list has five planks",
        ),
        AsmPatch(
            SYSTEM_LIST_ENTRIES,
            SYSTEM_LIST_ENTRIES + 4,
            SYSTEM_LIST_ENTRIES_OLD,
            SYSTEM_LIST_ENTRIES_OLD,
            ".word ${cave_system_planks}",
            "the System list's five planks",
        ),
        AsmPatch(
            SAVE_PLANK_POOL,
            SAVE_PLANK_POOL + 4,
            SYSTEM_LIST_ENTRIES_OLD,
            SYSTEM_LIST_ENTRIES_OLD,
            ".word ${cave_system_planks}",
            "the Save plank still greys out where saving is not allowed",
        ),
        CaveCode(
            "cave_system_key",
            SYSTEM_KEY_ASM,
            "the Bestiary plank opens the bestiary; Quit Game moves down",
        ),
        hook(
            SYSTEM_KEY,
            SYSTEM_KEY_WORD,
            "bl ${cave_system_key}",
            "the Bestiary plank opens the bestiary",
        ),
        CaveCode(
            "cave_bestiary_categories",
            CATEGORIES_ASM,
            "from the System list, the categories go on to Cards",
        ),
        hook(
            CATEGORIES_NEXT,
            CATEGORIES_NEXT_WORD,
            "bl ${cave_bestiary_categories}",
            "from the System list, the categories go on to Cards",
        ),
        CaveCode(
            "cave_system_hint",
            HINT_PICK_ASM,
            "the System list's hints with the Bestiary plank",
        ),
        *(
            hook(
                addr,
                SYSTEM_HINT_WORD,
                "bl ${cave_system_hint}",
                "the System list's hints with the Bestiary plank",
            )
            for addr in SYSTEM_HINTS
        ),
        CaveCode(
            "cave_bestiary_words", WORDS_ASM, "the Bestiary plank's word and hint"
        ),
        CaveCode(
            "cave_hint_draw",
            HINT_DRAW_ASM,
            "the Bestiary plank's word and hint drawn on the bottom screen",
        ),
        hook(
            HINT_DRAW,
            HINT_DRAW_WORD,
            "bl ${cave_hint_draw}",
            "the Bestiary plank's word and hint",
        ),
        *(
            Patch(
                addr,
                old,
                new,
                "B on Quit Game's prompts goes back to Quit Game, a plank lower",
            )
            for addr, old, new in QUIT_RETURNS
        ),
        Patch(*QUIT_BRACKETS, "Quit Game's prompt keeps its brackets on Quit Game"),
    ),
)
