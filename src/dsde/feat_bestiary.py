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
from dsde.patching import CaveCode, Feature
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

VIEWER_TEXT = 0x0205D228  # field menu, card viewer: `mov r0, #0` after the MAX Point digits; sl = text handle
VIEWER_TEXT_WORD = 0xE3A00000
DRAW_STRING = (
    0x02066F90  # (handle, string, column, row, [sp] 0, [sp + 4] 5, [sp + 8] 0xB)
)
GLYPHS = 0x020A6438  # u16 offsets of the menu's short strings: 0 to 9 the digits, 10 a blank, 22 "LV"
GLYPH_TEXT = 0x020A65F4
GLYPH_BLANK = 10
GLYPH_LV = 22
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart
PARTY_SLOTS = 3
LEVEL_OFFSET = 0xC  # the level index: the level shown is one more
MAX_SHOWN_LEVEL = 99
LEVEL_ROW = 20  # text rows are 8 pixels: the bar is pixels 160 to 175
LV_COLUMN = 21
TENS_COLUMN = 24

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

LEVEL_ASM = f"""
    push  {{r0-r6, lr}}
    mov   r4, sl
    ldr   r1, lv_party
    mov   r6, #0
    mov   r5, #0
lv_member:
    ldrsh r0, [r1]
    cmp   r0, #{CHARACTERS}
    bhs   lv_skip
    ldr   r2, lv_records
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r0, r3, r2
    ldr   r2, [r2, #{LEVEL_OFFSET:#x}]
    cmp   r2, r6
    movgt r6, r2
lv_skip:
    add   r1, r1, #4
    add   r5, r5, #1
    cmp   r5, #{PARTY_SLOTS}
    blt   lv_member
    add   r6, r6, #1
    cmp   r6, #{MAX_SHOWN_LEVEL}
    movgt r6, #{MAX_SHOWN_LEVEL}
    mov   r0, #{GLYPH_LV}
    mov   r1, #{LV_COLUMN}
    bl    lv_glyph
    mov   r5, #0
lv_div:
    cmp   r6, #10
    blt   lv_digits
    sub   r6, r6, #10
    add   r5, r5, #1
    b     lv_div
lv_digits:
    cmp   r5, #0
    moveq r0, #{GLYPH_BLANK}
    movne r0, r5
    mov   r1, #{TENS_COLUMN}
    bl    lv_glyph
    mov   r0, r6
    mov   r1, #{TENS_COLUMN + 1}
    bl    lv_glyph
    pop   {{r0-r6, lr}}
    mov   r0, #0
    bx    lr

@ r0 = short string index, r1 = column; r4 = text handle
lv_glyph:
    push  {{lr}}
    sub   sp, sp, #12
    mov   r3, #0
    str   r3, [sp]
    mov   r3, #5
    str   r3, [sp, #4]
    mov   r3, #0xb
    str   r3, [sp, #8]
    mov   r2, r1
    ldr   r3, lv_glyphs
    add   r3, r3, r0, lsl #1
    ldrh  r3, [r3]
    ldr   r1, lv_text
    add   r1, r1, r3
    mov   r0, r4
    mov   r3, #{LEVEL_ROW}
    bl    {DRAW_STRING:#x}
    add   sp, sp, #12
    pop   {{pc}}
lv_party:
    .word {PARTY:#x}
lv_records:
    .word {CHAR_RECORDS:#x}
lv_glyphs:
    .word {GLYPHS:#x}
lv_text:
    .word {GLYPH_TEXT:#x}
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
        CaveCode("cave_bestiary_level", LEVEL_ASM, "the level on the card's bar"),
        hook(
            VIEWER_TEXT,
            VIEWER_TEXT_WORD,
            "bl ${cave_bestiary_level}",
            "the level on the card's bar",
        ),
    ),
)
