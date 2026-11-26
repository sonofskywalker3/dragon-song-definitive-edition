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
    ),
)
