"""Manual targeting: the picker's blue cursor corners also frame the highlighted enemy on the battle field.

Jeff (2026-10-07): with the corners around the enemy itself, the player can watch the enemies instead
of the picker grid to see which one is selected.

How the battle draws sprites (docs/plan-targeting.md, "Cursor corners on the field"): every sprite of a
frame, battlers, effects and menu buttons alike, is a 0x30-byte request in the pool at *SPRITE_POOL.
func_02033804 turns the requests into OAM for both screens on one 256 x 384 canvas: y 0..191 is the touch
screen, y -192..-1 the top screen, so a request lands on whichever screen its position is on. The tiles of
the menu's cursor corners are in the shared OBJ tile buffer that both engines get, with the same palette,
so the corners draw correctly on either screen.

Each battler submits its own request just before the render call, keeping its pool index at +0x106.
Request: +0x00 flags (bit 0 in use, 0x100 mirrored), +0x14 pointer to the frame's pieces, +0x18 inverse scale
(0x1000 = 1; drawn size = 1 / it), +0x1C x, +0x20 y, +0x24 height (drawn at y - height), +0x2C piece count. A piece is 12
bytes: s16 x and y of its centre (scaled), u16 attributes with the OAM shape in bits 4..5 and the size in
bits 6..7.

The hook replaces the render call. While the enemy picker is up, it takes the highlighted enemy's
request and bounds the opaque pixels of its pieces (read from the OBJ tile buffer at *0x020B861C, which
both engines get each frame: a piece's tiles start at 64 * ((tile >> 1 for 4bpp) + request +0x28), laid
out row by row in 1D order; the enemy sprites are 64 x 64 pieces with wide transparent margins), and
submits a copy of each of the four corner buttons moved to that box with
the game's own button submit (func_02036360), then renders. The real corner buttons are not touched (the
copies go on the stack), so their animation and slide are as before.
"""

from dsde.patching import AsmPatch, CaveCode
from dsde.targeting_consts import (
    BATTLER_SIZE,
    BATTLERS_PTR,
    BUTTON_SIZE,
    BUTTONS_PTR,
    HOLE,
    MAX_ENTRIES,
    MENU,
    MENU_CURSOR,
    MENU_FIRST_SHOWN,
    MENU_PAGE,
    PAGE_LIST,
    POSITION_X,
    STATE_MAP,
    STATE_MODE,
)

RENDER_CALL = (
    0x02031C58  # bl func_02033804 in func_02031be0, after every battler's request
)
RENDER_CALL_WORD = 0xEB0006E9
RENDER_SPRITES = 0x02033804
SUBMIT_BUTTON = 0x02036360  # (button): one sprite request for a menu button
SPRITE_POOL = 0x020B8618  # pointer to the request pool
REQUEST_SIZE = 0x30
BATTLER_REQUEST = 0x106  # s16 pool index of the battler's request this frame
HALFWORD_OFFSET_MAX = 0xFF  # ldrsh takes an 8-bit offset
REQ_FLAGS = 0x00
REQ_PIECES = 0x14
REQ_SCALE = 0x18
REQ_X = 0x1C
REQ_Y = 0x20
REQ_HEIGHT = 0x24
REQ_COUNT = 0x2C
REQ_IN_USE = 1
REQ_MIRRORED = 0x100
SCALE_FRACTION = 0xFF  # dropped by the renderer
RECIPROCAL = 0x02001364  # (x) -> 0x1000000 / x: the request's scale is the inverse of the drawn size
SCALE_SHIFT = 12
PIECE_SIZE = 12
PIECE_Y = 2
PIECE_ATTR = 4
PIECE_TILE = 10  # u16 first tile (in 32-byte units)
PIECE_256_COLOURS = 8  # attribute bit: 8bpp tiles
REQ_TILE_BASE = 0x28  # u16 added to each piece's tile
OBJ_BUFFER = 0x020B861C  # pointer to the OBJ tile buffer both engines get each frame
OBJ_TILE_UNIT_SHIFT = (
    6  # OAM tile numbers count 64-byte units (1D mapping, 64-byte boundary)
)
TILE_INDEX_BITS = 10
TILE = 8
TILE_SHIFT = 3  # log2(TILE)
TILE4_SHIFT = 5  # 4bpp tile: 32 bytes, 4 bytes a row
ROW4_SHIFT = 2
TILE8_SHIFT = 6  # 8bpp tile: 64 bytes, 8 bytes a row
ROW8_SHIFT = 3
PIECE_SHAPE_SIZE_SHIFT = 4  # (attr >> 4) & 0xF = size * 4 + shape
PIECE_SHAPE_SIZE_MASK = 0xF
CORNERS = 4  # buttons 0..3 are the cursor corners: top-left, bottom-left, top-right, bottom-right
CORNER_RIGHT = 2  # corner index bits
CORNER_BOTTOM = 1
BUTTON_X = 4
BUTTON_Y = 8
BUTTON_HIDDEN = 0x80000000

# Stack frame: the box (screen pixels), the piece being scanned and its opaque pixels (piece
# pixels), then a copy of one corner button
BOX_LEFT, BOX_TOP, BOX_RIGHT, BOX_BOTTOM = 0, 4, 8, 12
PIECE_W, PIECE_H, PIECE_BPP8 = 16, 20, 24
OPAQUE_LEFT, OPAQUE_TOP, OPAQUE_RIGHT, OPAQUE_BOTTOM = 28, 32, 36, 40
COPY = 44
FRAME = COPY + BUTTON_SIZE

# OAM sizes (width, height) by size * 4 + shape; shape 3 does not exist
OAM_SIZES = (
    (8, 8), (16, 8), (8, 16), (0, 0),
    (16, 16), (32, 8), (8, 32), (0, 0),
    (32, 32), (32, 16), (16, 32), (0, 0),
    (64, 64), (64, 32), (32, 64), (0, 0),
)  # fmt: skip

BRACKETS_ASM = f"""
    push  {{r4-r11, lr}}
    sub   sp, sp, #{FRAME:#x}
    ldr   r4, br_state
    ldrb  r0, [r4, #{STATE_MODE}]
    cmp   r0, #0
    beq   br_done
    ldr   r5, br_menu
    ldrsh r0, [r5, #{MENU_PAGE:#x}]
    cmp   r0, #{PAGE_LIST}
    bne   br_done
    ldr   r0, [r5, #{MENU_CURSOR:#x}]
    cmp   r0, #0
    blt   br_done
    ldr   r1, [r5, #{MENU_FIRST_SHOWN:#x}]
    add   r0, r0, r1
    cmp   r0, #{MAX_ENTRIES}
    bge   br_done
    add   r1, r4, #{STATE_MAP}
    ldrb  r0, [r1, r0]
    cmp   r0, #{HOLE:#x}
    beq   br_done
    ldr   r1, br_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r6, r0, r2, r1
    add   r0, r6, #{BATTLER_REQUEST & ~HALFWORD_OFFSET_MAX:#x}
    ldrsh r0, [r0, #{BATTLER_REQUEST & HALFWORD_OFFSET_MAX:#x}]
    cmp   r0, #0
    blt   br_done
    ldr   r1, br_pool
    ldr   r1, [r1]
    mov   r2, #{REQUEST_SIZE:#x}
    mla   r7, r0, r2, r1
    ldr   r0, [r7, #{REQ_FLAGS}]
    tst   r0, #{REQ_IN_USE}
    beq   br_done
    ldr   r0, [r7, #{REQ_X:#x}]
    ldr   r1, [r6, #{POSITION_X:#x}]
    cmp   r0, r1
    bne   br_done
    ldr   r8, [r7, #{REQ_PIECES:#x}]
    ldrh  r9, [r7, #{REQ_COUNT:#x}]
    cmp   r9, #0
    beq   br_done
    ldr   r0, [r7, #{REQ_SCALE:#x}]
    bl    {RECIPROCAL:#x}
    bic   r10, r0, #{SCALE_FRACTION:#x}
    ldr   r11, [r7, #{REQ_Y:#x}]
    ldr   r0, [r7, #{REQ_HEIGHT:#x}]
    sub   r11, r11, r0
    mvn   r0, #0x80000000
    mov   r1, #0x80000000
    str   r0, [sp, #{BOX_LEFT}]
    str   r0, [sp, #{BOX_TOP}]
    str   r1, [sp, #{BOX_RIGHT}]
    str   r1, [sp, #{BOX_BOTTOM}]
br_piece:
    ldrh  r2, [r8, #{PIECE_ATTR}]
    and   r3, r2, #{PIECE_256_COLOURS}
    str   r3, [sp, #{PIECE_BPP8}]
    mov   r2, r2, lsr #{PIECE_SHAPE_SIZE_SHIFT}
    and   r2, r2, #{PIECE_SHAPE_SIZE_MASK:#x}
    adr   r3, br_sizes
    add   r3, r3, r2, lsl #1
    ldrb  r0, [r3]
    ldrb  r1, [r3, #1]
    str   r0, [sp, #{PIECE_W}]
    str   r1, [sp, #{PIECE_H}]
    cmp   r0, #0
    beq   br_next_piece
    ldrh  r0, [r8, #{PIECE_TILE}]
    ldr   r3, [sp, #{PIECE_BPP8}]
    cmp   r3, #0
    moveq r0, r0, lsr #1
    ldrh  r1, [r7, #{REQ_TILE_BASE:#x}]
    add   r0, r0, r1
    mov   r0, r0, lsl #{32 - TILE_INDEX_BITS}
    mov   r0, r0, lsr #{32 - TILE_INDEX_BITS}
    ldr   r4, br_objbuf
    ldr   r4, [r4]
    add   r4, r4, r0, lsl #{OBJ_TILE_UNIT_SHIFT}
    ldr   r0, [sp, #{PIECE_W}]
    str   r0, [sp, #{OPAQUE_LEFT}]
    ldr   r0, [sp, #{PIECE_H}]
    str   r0, [sp, #{OPAQUE_TOP}]
    mvn   r0, #0
    str   r0, [sp, #{OPAQUE_RIGHT}]
    str   r0, [sp, #{OPAQUE_BOTTOM}]
    mov   r5, #0
br_row:
    mov   r6, #0
br_col:
    ldr   r1, [sp, #{PIECE_W}]
    mov   r1, r1, lsr #{TILE_SHIFT}
    mov   r0, r5, lsr #{TILE_SHIFT}
    mul   r2, r0, r1
    add   r2, r2, r6, lsr #{TILE_SHIFT}
    ldr   r3, [sp, #{PIECE_BPP8}]
    cmp   r3, #0
    bne   br_px8
    add   r0, r4, r2, lsl #{TILE4_SHIFT}
    and   r1, r5, #{TILE - 1}
    add   r0, r0, r1, lsl #{ROW4_SHIFT}
    and   r1, r6, #{TILE - 1}
    ldrb  r3, [r0, r1, lsr #1]
    tst   r6, #1
    movne r3, r3, lsr #4
    ands  r3, r3, #0xF
    b     br_px_done
br_px8:
    add   r0, r4, r2, lsl #{TILE8_SHIFT}
    and   r1, r5, #{TILE - 1}
    add   r0, r0, r1, lsl #{ROW8_SHIFT}
    and   r1, r6, #{TILE - 1}
    ldrb  r3, [r0, r1]
    cmp   r3, #0
br_px_done:
    beq   br_px_next
    ldr   r0, [sp, #{OPAQUE_LEFT}]
    cmp   r6, r0
    strlt r6, [sp, #{OPAQUE_LEFT}]
    ldr   r0, [sp, #{OPAQUE_RIGHT}]
    cmp   r6, r0
    strgt r6, [sp, #{OPAQUE_RIGHT}]
    ldr   r0, [sp, #{OPAQUE_TOP}]
    cmp   r5, r0
    strlt r5, [sp, #{OPAQUE_TOP}]
    ldr   r0, [sp, #{OPAQUE_BOTTOM}]
    cmp   r5, r0
    strgt r5, [sp, #{OPAQUE_BOTTOM}]
br_px_next:
    add   r6, r6, #1
    ldr   r0, [sp, #{PIECE_W}]
    cmp   r6, r0
    blt   br_col
    add   r5, r5, #1
    ldr   r0, [sp, #{PIECE_H}]
    cmp   r5, r0
    blt   br_row
    ldr   r0, [sp, #{OPAQUE_RIGHT}]
    cmp   r0, #0
    blt   br_next_piece
    ldr   r1, [r7, #{REQ_FLAGS}]
    tst   r1, #{REQ_MIRRORED:#x}
    beq   br_place
    ldr   r2, [sp, #{PIECE_W}]
    sub   r2, r2, #1
    ldr   r0, [sp, #{OPAQUE_LEFT}]
    ldr   r1, [sp, #{OPAQUE_RIGHT}]
    sub   r3, r2, r1
    sub   r12, r2, r0
    str   r3, [sp, #{OPAQUE_LEFT}]
    str   r12, [sp, #{OPAQUE_RIGHT}]
br_place:
    ldrsh r0, [r8]
    ldr   r1, [r7, #{REQ_FLAGS}]
    tst   r1, #{REQ_MIRRORED:#x}
    rsbne r0, r0, #0
    mul   r0, r10, r0
    ldr   r1, [r7, #{REQ_X:#x}]
    add   r0, r1, r0, asr #{SCALE_SHIFT}
    ldrsh r1, [r8, #{PIECE_Y}]
    mul   r1, r10, r1
    add   r1, r11, r1, asr #{SCALE_SHIFT}
    ldr   r2, [sp, #{PIECE_W}]
    mov   r2, r2, lsr #1
    ldr   r3, [sp, #{OPAQUE_LEFT}]
    sub   r3, r3, r2
    mul   r3, r10, r3
    add   r12, r0, r3, asr #{SCALE_SHIFT}
    ldr   lr, [sp, #{BOX_LEFT}]
    cmp   r12, lr
    strlt r12, [sp, #{BOX_LEFT}]
    ldr   r3, [sp, #{OPAQUE_RIGHT}]
    add   r3, r3, #1
    sub   r3, r3, r2
    mul   r3, r10, r3
    add   r12, r0, r3, asr #{SCALE_SHIFT}
    ldr   lr, [sp, #{BOX_RIGHT}]
    cmp   r12, lr
    strgt r12, [sp, #{BOX_RIGHT}]
    ldr   r2, [sp, #{PIECE_H}]
    mov   r2, r2, lsr #1
    ldr   r3, [sp, #{OPAQUE_TOP}]
    sub   r3, r3, r2
    mul   r3, r10, r3
    add   r12, r1, r3, asr #{SCALE_SHIFT}
    ldr   lr, [sp, #{BOX_TOP}]
    cmp   r12, lr
    strlt r12, [sp, #{BOX_TOP}]
    ldr   r3, [sp, #{OPAQUE_BOTTOM}]
    add   r3, r3, #1
    sub   r3, r3, r2
    mul   r3, r10, r3
    add   r12, r1, r3, asr #{SCALE_SHIFT}
    ldr   lr, [sp, #{BOX_BOTTOM}]
    cmp   r12, lr
    strgt r12, [sp, #{BOX_BOTTOM}]
br_next_piece:
    add   r8, r8, #{PIECE_SIZE}
    subs  r9, r9, #1
    bne   br_piece
    ldr   r0, [sp, #{BOX_LEFT}]
    ldr   r1, [sp, #{BOX_RIGHT}]
    cmp   r1, r0
    blt   br_done
    ldr   r4, br_buttons
    ldr   r4, [r4]
    ldr   r0, [r4]
    tst   r0, #{BUTTON_HIDDEN:#x}
    bne   br_done
    mov   r5, #0
br_corner:
    mov   r0, #{BUTTON_SIZE}
    mla   r1, r5, r0, r4
    add   r0, sp, #{COPY}
    mov   r2, #{BUTTON_SIZE}
br_copy:
    ldr   r3, [r1], #4
    str   r3, [r0], #4
    subs  r2, r2, #4
    bne   br_copy
    tst   r5, #{CORNER_RIGHT}
    ldreq r0, [sp, #{BOX_LEFT}]
    ldrne r0, [sp, #{BOX_RIGHT}]
    tst   r5, #{CORNER_BOTTOM}
    ldreq r1, [sp, #{BOX_TOP}]
    ldrne r1, [sp, #{BOX_BOTTOM}]
    str   r0, [sp, #{COPY + BUTTON_X}]
    str   r1, [sp, #{COPY + BUTTON_Y}]
    add   r0, sp, #{COPY}
    bl    {SUBMIT_BUTTON:#x}
    add   r5, r5, #1
    cmp   r5, #{CORNERS}
    blt   br_corner
br_done:
    add   sp, sp, #{FRAME:#x}
    pop   {{r4-r11, lr}}
    b     {RENDER_SPRITES:#x}
br_state:
    .word ${{cave_tgt_state}}
br_menu:
    .word {MENU:#x}
br_battlers:
    .word {BATTLERS_PTR:#x}
br_pool:
    .word {SPRITE_POOL:#x}
br_buttons:
    .word {BUTTONS_PTR:#x}
br_objbuf:
    .word {OBJ_BUFFER:#x}
br_sizes:
    .byte {", ".join(f"{w}, {h}" for w, h in OAM_SIZES)}
"""

BRACKET_PATCHES = (
    CaveCode("cave_tgt_brackets", BRACKETS_ASM, "cursor corners around the enemy"),
    AsmPatch(
        RENDER_CALL,
        RENDER_CALL + 4,
        RENDER_CALL_WORD,
        RENDER_CALL_WORD,
        "bl ${cave_tgt_brackets}",
        "cursor corners around the enemy, then the sprite render",
    ),
)
