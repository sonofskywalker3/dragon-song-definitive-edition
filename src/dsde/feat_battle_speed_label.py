"""The battle speed is shown on the top screen: a small plank under the status bar (Jeff, 2026-11-22).

Tapping R only played the menu click, so nothing said which speed a battle was on. A plank one tile high
and six wide now hangs under the right end of the status bar, over the wooden sign's column, and reads
NORMAL, FAST, or FASTER in the sign's lettering (feat_mic_sign.py). It is there during command input and
through the round, so it also shows the switch to Faster that picking Auto makes.

The top screen's interface is engine B BG0: a tilemap the game keeps in RAM (TILEMAPS + 0xC, copied to
VRAM whenever its dirty bit is set) over the battle UI tile set at character base 0xC000. The set fills
tiles 0..0x11F (btldata entry 3) and the text font starts at 0x180; nothing loads the tiles between, so
the plank takes six of them. Every frame of command input and the round the speed cave copies the current
speed's six tiles there and puts the six cells back if anything wiped them; in the other battle states
(intro, victory, result pages) it removes its own cells and touches nothing else.
"""

from dsde.feat_mic_sign import (
    GLYPHS,
    INK_BY_ROW,
    NIBBLE_BITS,
    OUTLINE,
    STROKE,
    TILE_BYTES,
    TILE_SIZE,
    WOOD_BY_ROW,
)
from dsde.patching import CaveCode

SPEED_NAMES = (
    "NORMAL",
    "FAST",
    "FASTER",
)  # by setting, as feat_battle_speed.SPEED_LEVELS
LABEL_TILES = 6
LABEL_WIDTH = LABEL_TILES * TILE_SIZE
LABEL_ROW = 5  # the tile row under the status bar (rows 0..4)
LABEL_COLUMN = (
    26  # the wooden sign's left column; the plank ends at the screen's right edge
)
TILEMAP_WIDTH = 32
FIRST_TILE = 0x120  # after the UI tile set, before the font
SIGN_PALETTE = 8  # BG palette bank of the wooden sign
PALETTE_SHIFT = 12
FIRST_CELL = SIGN_PALETTE << PALETTE_SHIFT | FIRST_TILE
UI_TILES_VRAM = 0x0620C000  # engine B BG character base 0xC000
TILEMAPS = 0x02139D20  # battle window work
TILEMAP_TOP = 0xC  # pointer to the top screen's tilemap in RAM
TILEMAP_DIRTY = 0x14  # u16: bit 0 = copy the top tilemap to VRAM
DIRTY_TOP = 1
GAME_STATE = 0x020B0010  # the battle mode's state (func_020297d4)
FIRST_BATTLE_STATE = 3  # states 3..13 run with the battle loaded
BATTLE_STATES = 11
STATE_COMMAND = 7
STATE_ROUND = 8
WORD = 4
LETTER_GAP = 2
TRANSPARENT = 0
LETTER_TOP = 1  # the letters fill rows 1..6 of the plank's eight
# Wood color of the six letter rows: the sign plank's middle shades (rows 27..32 of the sign)
WOOD = WOOD_BY_ROW[1:7]

SPEED_GLYPHS = {
    **GLYPHS,
    "F": ("####", "#...", "###.", "#...", "#...", "#..."),
    "A": (".##.", "#..#", "#..#", "####", "#..#", "#..#"),
    "S": (".###", "#...", ".##.", "...#", "...#", "###."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "E": ("####", "#...", "###.", "#...", "#...", "####"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", ".###."),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#"),
}


def _strokes(text: str) -> set[tuple[int, int]]:
    """Plank pixels (x, y) of the lettering, centered."""
    width = sum(len(SPEED_GLYPHS[c][0]) for c in text) + LETTER_GAP * (len(text) - 1)
    x = (LABEL_WIDTH - width) // 2
    strokes = set()
    for char in text:
        glyph = SPEED_GLYPHS[char]
        for row, line in enumerate(glyph):
            strokes.update(
                (x + col, LETTER_TOP + row) for col, c in enumerate(line) if c == STROKE
            )
        x += len(glyph[0]) + LETTER_GAP
    return strokes


def plank_pixels(text: str) -> list[list[int]]:
    """A 48 x 8 plank: a black border with open corners, wood shaded by row, and the outlined word."""
    strokes = _strokes(text)
    last_x, last_y = LABEL_WIDTH - 1, TILE_SIZE - 1
    pixels = []
    for y in range(TILE_SIZE):
        row = []
        for x in range(LABEL_WIDTH):
            if x in (0, last_x) and y in (0, last_y):
                row.append(TRANSPARENT)
            elif x in (0, last_x) or y in (0, last_y):
                row.append(OUTLINE)
            elif (x, y) in strokes:
                row.append(INK_BY_ROW[y - LETTER_TOP])
            elif any(
                (x + dx, y + dy) in strokes for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            ):
                row.append(OUTLINE)
            else:
                row.append(WOOD[y - LETTER_TOP])
        pixels.append(row)
    return pixels


def plank_tiles(text: str) -> bytes:
    """The plank as six 4bpp tiles, left to right."""
    pixels = plank_pixels(text)
    out = bytearray()
    for tile in range(LABEL_TILES):
        left = tile * TILE_SIZE
        for y in range(TILE_SIZE):
            for x in range(left, left + TILE_SIZE, 2):
                out.append(pixels[y][x] | pixels[y][x + 1] << NIBBLE_BITS)
    return bytes(out)


LABEL_BYTES = LABEL_TILES * TILE_BYTES
TILES_ASM = "\n".join(
    "    .byte " + ", ".join(str(byte) for byte in plank_tiles(name))
    for name in SPEED_NAMES
)

# In: r0 = the speed setting. Called every frame from the speed cave.
LABEL_ASM = f"""
    push  {{r4-r7, lr}}
    mov   r4, r0
    ldr   r0, lbl_state
    ldr   r5, [r0]
    sub   r0, r5, #{FIRST_BATTLE_STATE}
    cmp   r0, #{BATTLE_STATES}
    pophs {{r4-r7, pc}}
    ldr   r7, lbl_maps
    ldr   r6, [r7, #{TILEMAP_TOP:#x}]
    cmp   r6, #0
    popeq {{r4-r7, pc}}
    add   r6, r6, #{(LABEL_ROW * TILEMAP_WIDTH + LABEL_COLUMN) * 2:#x}
    ldr   r1, lbl_cell
    mov   r3, #{LABEL_TILES}
    mov   r12, #0
    cmp   r5, #{STATE_COMMAND}
    cmpne r5, #{STATE_ROUND}
    bne   lbl_erase
lbl_cells:
    ldrh  r0, [r6]
    cmp   r0, r1
    strhne r1, [r6]
    movne r12, #1
    add   r6, r6, #2
    add   r1, r1, #1
    subs  r3, r3, #1
    bne   lbl_cells
    ldr   r1, lbl_tiles
    mov   r0, #{LABEL_BYTES}
    mla   r1, r0, r4, r1
    ldr   r2, lbl_vram
    mov   r3, #{LABEL_BYTES // WORD}
lbl_copy:
    ldr   r0, [r1], #4
    str   r0, [r2], #4
    subs  r3, r3, #1
    bne   lbl_copy
    b     lbl_dirty
lbl_erase:
    ldrh  r0, [r6]
    cmp   r0, r1
    moveq r0, #0
    strheq r0, [r6]
    moveq r12, #1
    add   r6, r6, #2
    add   r1, r1, #1
    subs  r3, r3, #1
    bne   lbl_erase
lbl_dirty:
    cmp   r12, #0
    ldrhne r0, [r7, #{TILEMAP_DIRTY:#x}]
    orrne r0, r0, #{DIRTY_TOP}
    strhne r0, [r7, #{TILEMAP_DIRTY:#x}]
    pop   {{r4-r7, pc}}
lbl_state:
    .word {GAME_STATE:#x}
lbl_maps:
    .word {TILEMAPS:#x}
lbl_cell:
    .word {FIRST_CELL:#x}
lbl_vram:
    .word {UI_TILES_VRAM + FIRST_TILE * TILE_BYTES:#x}
lbl_tiles:
    .word ${{cave_speed_tiles}}
"""

LABEL_CAVES = (
    CaveCode("cave_speed_tiles", TILES_ASM, "battle speed plank tiles, six per speed"),
    CaveCode("cave_speed_label", LABEL_ASM, "battle speed plank under the status bar"),
)
