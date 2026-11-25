"""The Status page's equipment box scrolls over seven entries (docs/plan-cards.md 2.3 and 6).

The Status page (field menu func_02059f84, state word 0x020B0010) draws a member's page in state 8: a loop of
five rows, row i the name of the item in equipment slot i at text tile (5, 4 + 3 i), with the slot's icon (a
sprite of set 0x0213A058, entries 7 to 11, frame at +0x1A). State 7 opens the page and runs again on each L/R
member switch; state 9 waits for input. Here the rows show entries (offset + i) of a list of seven: the five
slots, then the ring slot (slot 6) and the card slot (slot 5); Up and Down in state 9 move the offset (0 to 2) and
redraw the page by going back to state 8; state 7 puts the offset back to 0; arrows beside the box show that
there is more above or below.

The ring row's icon is the game's own item icon of the plain "Ring" (item 0xD7, sysmenupack entry 54), added as
frame 20 (and its greyed twin, 21) to the menu icons: four tiles appended to their art (entry 42, two palettes and
52 tiles) and two frames to their cell list (entry 30).
"""

import struct
from functools import cache
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.patching import AsmPatch, CaveCode, DataPatch
from dsde.skills_common import hook

VANILLA_SYSMENUPACK = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "sysmenupack.dat"
)
ARCHIVE = "sysmenupack"
ICON_ART = 42  # NTC8: u16 tile count at +4, palette count at +6, palettes from 0x10, then 8x8 tiles
ICON_CELLS = 30  # CLT8: u16 frame count at +4, piece count at +6, frames {u16 first piece, u16 pieces}, pieces
ITEM_ICONS = 54  # a palette, then a 16x16 icon per item from item 1, tiles of 64 bytes in 2 x 2 order
RING_ITEM = 0xD7  # "Ring", a plain gold band
PALETTE_BYTES = 0x200
NTC_HEADER = 0x10
TILE_BYTES = 64
ICON_TILES = 4
ICON_BYTES = ICON_TILES * TILE_BYTES
CLT_HEADER = 8
FRAME_BYTES = 4
PIECE_BYTES = 12
TRANSPARENT = 0
SOURCE_FRAME = (
    0  # the sword's frame: the new frames copy its piece, with their own first tile
)
RING_FRAME = 20
SLOT_ORDER = (
    0,
    1,
    2,
    3,
    4,
    6,
    5,
)  # the box's entries: the five slots, the ring slot, the card slot
ENTRY_FRAMES = (
    0,
    2,
    6,
    4,
    8,
    RING_FRAME,
    12,
)  # weapon, armor, gloves, hat, accessory, ring, card
MAX_OFFSET = len(SLOT_ORDER) - 5

STATE7_FIRST = 0x0205AEE0  # `mov r0, #0x400`, the first instruction of state 7
STATE7_FIRST_WORD = 0xE3A00B01
NAME_TEST_LOAD = (
    0x0205B17C  # state 8: `ldrh r0, [r0, #0xe8]`, row sb's item, for the empty test
)
NAME_TEST_WORD = 0xE1D00EB8
NAME_DRAW_LOAD = (
    0x0205B1DC  # state 8: `ldrh r1, [r1, #0xe8]`, the same item, for its name
)
NAME_DRAW_WORD = 0xE1D11EB8
ROWS_DONE = 0x0205B220  # state 8 after the rows: `mov r0, #0x3c0`; the text handle is at [sp, #0x88]
ROWS_DONE_WORD = 0xE3A00D0F
STATE9_FIRST = 0x0205B364  # `mov r1, #0`, the first instruction of state 9
STATE9_FIRST_WORD = 0xE3A01000
PAD_NEW = 0x020AFF7A  # u16 keys newly pressed this frame
KEY_UP = 0x40
KEY_DOWN = 0x80
GAME_STATE = 0x020B0010
STATE_DRAW_PAGE = 8
SLOT_FIELD = 0xE8  # the loads' offset (after the +0x4000)
ICON_SET = 0x0213A058
FIRST_ROW_ICON = 7
SPRITE_ANIM = 0x1A
HANDLE_AT = 0x88
TEXT_MARK = 0x02067098  # the text calls around each draw, as the rows do
TEXT_RESET = 0x020670C8
TEXT_SPAN = 0x3DC
DRAW_STRING = 0x02066F90
GLYPHS = 0x020A6438
GLYPH_TEXT = 0x020A65F4
GLYPH_UP = 14
GLYPH_DOWN = 15
ARROW_COLUMN = 0x1D
ROW_COLOR = 1  # the rows' text colour argument (the Item page uses 5)
ARROW_TOP_ROW = 4
ARROW_BOTTOM_ROW = 16


def _vanilla(entry: int) -> bytes:
    return decompress(read_archive(VANILLA_SYSMENUPACK.read_bytes())[entry])


def _colors(data: bytes, at: int) -> list[tuple[int, int, int]]:
    words = struct.unpack_from("<256H", data, at)
    return [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in words]


def _nearest(colors: list[tuple[int, int, int]], rgb: tuple[int, int, int]) -> int:
    def distance(i: int) -> int:
        return sum((a - b) ** 2 for a, b in zip(colors[i], rgb, strict=True))

    return min(range(1, len(colors)), key=distance)


@cache
def ring_icon_tiles() -> bytes:
    """The Ring item's icon as four tiles in the menu icons' first palette (the greyed twin uses the second)."""
    items = _vanilla(ITEM_ICONS)
    art = _vanilla(ICON_ART)
    item_colors = _colors(items, 0)
    menu_colors = _colors(art, NTC_HEADER)
    icon = items[PALETTE_BYTES + (RING_ITEM - 1) * ICON_BYTES :][:ICON_BYTES]
    return bytes(
        TRANSPARENT if p == TRANSPARENT else _nearest(menu_colors, item_colors[p])
        for p in icon
    )


def _art_with_ring() -> tuple[bytes, bytes]:
    art = _vanilla(ICON_ART)
    tiles = struct.unpack_from("<H", art, 4)[0]
    new = bytearray(art + ring_icon_tiles())
    struct.pack_into("<H", new, 4, tiles + ICON_TILES)
    return art, bytes(new)


def _cells_with_ring() -> tuple[bytes, bytes]:
    cells = _vanilla(ICON_CELLS)
    frames, pieces = struct.unpack_from("<HH", cells, 4)
    if frames != RING_FRAME or pieces != RING_FRAME:
        raise ValueError(
            "the menu icon cells are not the 20 one-piece frames this patch expects"
        )
    art_tiles = struct.unpack_from("<H", _vanilla(ICON_ART), 4)[0]
    frame_table = cells[CLT_HEADER : CLT_HEADER + frames * FRAME_BYTES]
    pieces_at = CLT_HEADER + frames * FRAME_BYTES
    piece_table = cells[pieces_at : pieces_at + pieces * PIECE_BYTES]
    tail = cells[pieces_at + pieces * PIECE_BYTES :]
    new_frames = frame_table + struct.pack("<hhhh", pieces, 1, pieces + 1, 1)
    sword, grey_sword = (
        piece_table[
            (SOURCE_FRAME + i) * PIECE_BYTES : (SOURCE_FRAME + i + 1) * PIECE_BYTES
        ]
        for i in (0, 1)
    )
    new_pieces = piece_table + b"".join(
        struct.pack("<H", art_tiles) + piece[2:] for piece in (sword, grey_sword)
    )
    header = cells[:4] + struct.pack("<HH", frames + 2, pieces + 2)
    return cells, header + new_frames + new_pieces + tail


def _entry_asm(reg: str, icon: bool) -> str:
    """Return entry (sb + offset) of the box's list in `reg`, which points at slot sb's halfword - 0xE8; with
    `icon`, also set row sb's icon to the entry's frame."""
    icon_asm = (
        f"""
    push  {{r0, r1}}
    adr   r0, se_frames
    ldrb  r0, [r0, r2]
    ldr   r1, se_icons
    add   r1, r1, sb, lsl #5
    add   r1, r1, sb, lsl #4
    strh  r0, [r1, #{SPRITE_ANIM:#x}]
    pop   {{r0, r1}}"""
        if icon
        else ""
    )
    return f"""
    push  {{r2, r3}}
    ldr   r3, se_offset
    ldr   r3, [r3]
    add   r2, sb, r3{icon_asm}
    adr   r3, se_order
    ldrb  r3, [r3, r2]
    sub   r3, r3, sb
    add   {reg}, {reg}, r3, lsl #1
    ldrh  {reg}, [{reg}, #{SLOT_FIELD:#x}]
    pop   {{r2, r3}}
    bx    lr
se_offset:
    .word ${{cave_card_box_offset}}
se_icons:
    .word {ICON_SET + FIRST_ROW_ICON * 0x30:#x}
se_order:
    .byte {", ".join(str(s) for s in SLOT_ORDER)}
se_frames:
    .byte {", ".join(str(f) for f in ENTRY_FRAMES)}
    .align 2
"""


RESET_ASM = """
    ldr   r0, sr_offset
    mov   r1, #0
    str   r1, [r0]
    mov   r0, #0x400
    bx    lr
sr_offset:
    .word ${cave_card_box_offset}
"""

KEYS_ASM = f"""
    push  {{r0, r2, r3, lr}}
    ldr   r2, ss_pad
    ldrh  r2, [r2]
    ldr   r3, ss_offset
    ldr   r0, [r3]
    tst   r2, #{KEY_UP:#x}
    beq   ss_down
    cmp   r0, #0
    ble   ss_done
    sub   r0, r0, #1
    b     ss_redraw
ss_down:
    tst   r2, #{KEY_DOWN:#x}
    beq   ss_done
    cmp   r0, #{MAX_OFFSET}
    bge   ss_done
    add   r0, r0, #1
ss_redraw:
    str   r0, [r3]
    ldr   r2, ss_state
    mov   r0, #{STATE_DRAW_PAGE}
    str   r0, [r2]
ss_done:
    pop   {{r0, r2, r3, lr}}
    mov   r1, #0
    bx    lr
ss_pad:
    .word {PAD_NEW:#x}
ss_state:
    .word {GAME_STATE:#x}
ss_offset:
    .word ${{cave_card_box_offset}}
"""

# After the rows: an arrow at the box's top right when entries are hidden above, at its bottom right when some
# are hidden below. Ends with the instruction it replaces.
ARROWS_ASM = f"""
    push  {{r4-r7, lr}}
    ldr   r4, [sp, #{HANDLE_AT + 20:#x}]
    ldr   r5, sa_offset
    ldr   r5, [r5]
    cmp   r5, #0
    beq   sa_no_up
    mov   r0, #{GLYPH_UP}
    mov   r1, #{ARROW_TOP_ROW}
    bl    sa_draw
sa_no_up:
    cmp   r5, #{MAX_OFFSET}
    bge   sa_done
    mov   r0, #{GLYPH_DOWN}
    mov   r1, #{ARROW_BOTTOM_ROW}
    bl    sa_draw
sa_done:
    mov   r0, #0x3c0
    pop   {{r4-r7, pc}}

@ r0 = glyph, r1 = row; r4 = the text handle
sa_draw:
    push  {{r5, r6, lr}}
    sub   sp, sp, #12
    mov   r5, r0
    mov   r6, r1
    bl    {TEXT_MARK:#x}
    mov   r7, r0
    mov   r3, #0
    str   r3, [sp]
    mov   r3, #{ROW_COLOR}
    str   r3, [sp, #4]
    mov   r3, #0xb
    str   r3, [sp, #8]
    ldr   r1, sa_glyphs
    add   r1, r1, r5, lsl #1
    ldrh  r1, [r1]
    ldr   r2, sa_text
    add   r1, r2, r1
    mov   r0, r4
    mov   r2, #{ARROW_COLUMN:#x}
    mov   r3, r6
    bl    {DRAW_STRING:#x}
    rsb   r0, r7, #{TEXT_SPAN:#x}
    lsl   r0, r0, #16
    lsr   r0, r0, #16
    bl    {TEXT_RESET:#x}
    add   sp, sp, #12
    pop   {{r5, r6, pc}}
sa_offset:
    .word ${{cave_card_box_offset}}
sa_glyphs:
    .word {GLYPHS:#x}
sa_text:
    .word {GLYPH_TEXT:#x}
"""


def status_patches() -> tuple[CaveCode | AsmPatch | DataPatch, ...]:
    art_old, art_new = _art_with_ring()
    cells_old, cells_new = _cells_with_ring()
    return (
        DataPatch(
            ARCHIVE,
            ICON_ART,
            0,
            art_old,
            art_new,
            "menu icons: the ring slot's icon",
            whole=True,
        ),
        DataPatch(
            ARCHIVE,
            ICON_CELLS,
            0,
            cells_old,
            cells_new,
            "menu icons: frames for the ring icon",
            whole=True,
        ),
        CaveCode(
            "cave_card_box_offset",
            "    .word 0",
            "Status page: the equipment box's scroll",
        ),
        CaveCode(
            "cave_card_box_reset", RESET_ASM, "Status page: the box starts at the top"
        ),
        CaveCode(
            "cave_card_box_r0",
            _entry_asm("r0", True),
            "Status page: a row's entry and icon",
        ),
        CaveCode(
            "cave_card_box_r1", _entry_asm("r1", False), "Status page: a row's entry"
        ),
        CaveCode(
            "cave_card_box_keys", KEYS_ASM, "Status page: Up and Down scroll the box"
        ),
        CaveCode(
            "cave_card_box_arrows", ARROWS_ASM, "Status page: arrows for more rows"
        ),
        hook(
            STATE7_FIRST,
            STATE7_FIRST_WORD,
            "bl ${cave_card_box_reset}",
            "Status page: the box starts at the top",
        ),
        hook(
            NAME_TEST_LOAD,
            NAME_TEST_WORD,
            "bl ${cave_card_box_r0}",
            "Status page: a row's entry and icon",
        ),
        hook(
            NAME_DRAW_LOAD,
            NAME_DRAW_WORD,
            "bl ${cave_card_box_r1}",
            "Status page: a row's entry",
        ),
        hook(
            ROWS_DONE,
            ROWS_DONE_WORD,
            "bl ${cave_card_box_arrows}",
            "Status page: arrows for more rows",
        ),
        hook(
            STATE9_FIRST,
            STATE9_FIRST_WORD,
            "bl ${cave_card_box_keys}",
            "Status page: Up and Down scroll the box",
        ),
    )
