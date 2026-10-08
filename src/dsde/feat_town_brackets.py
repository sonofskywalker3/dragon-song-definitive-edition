"""Town and world map menus: the field menu's corner brackets frame the selected place (Jeff, 2026-10-08).

With the D-pad (feat_town_menu.py) the row highlight alone did not show clearly which place was picked. The
field menu's System screen frames its selected option with four small white-and-blue corner brackets; the
"Select place to go" menu now shows the same brackets around its selected row.

How the System menu draws them (vanilla, docs/re-field-battle.md "Selection brackets"): buttons 0..3 of the
System screen's button list (0x0213A664) are static sprites of frame 0x1F of the field menu sheet, sysmenupack
entries 0x26 (8bpp tiles, three palettes) and 0x1A (frames), each an 8 x 8 corner centred on its point, flipped
by the submit flags (8 horizontal, 0x10 vertical). The points are 16 px in from the row sprite's ends and on its
top and bottom edges, so the corners sit in the gaps above and below the row.

The place menu draws its bottom screen through sprite manager *0x020AFF50 (engine B). The manager shares its
tile store and resource table with the top-screen manager, so the menu's own loads (state 0) are followed by one
more: the field menu sheet, palettes into OBJ extended palette slots 4..6 (the menu itself uses slot 0). Each
frame, after the menu's buttons are submitted, four corner sprites are submitted around the row sprite of the
selected entry (+0x30) when it is on the shown tab (+0x32), in menu states 2..8 (select, input, confirm, leave).
"""

from dsde.patching import AsmPatch, CaveCode

LOAD_CALL = (
    0x02042F34  # bl func_0201c334 (the menu's last sprite load, top-screen map icons)
)
LOAD_CALL_WORD = 0xEBFF64FE
LOAD_SPRITES = 0x0201C334  # (manager, archive, tiles entry, frames entry, [sp] palette slot) -> resource
BUTTONS_CALL = 0x02043D64  # bl func_020276fc for the bottom-screen buttons 0x020B7F28
BUTTONS_CALL_WORD = 0xEBFF8E64
SUBMIT_BUTTONS = 0x020276FC
SUBMIT_SPRITE = (
    0x0201B898  # (manager, resource, frame, flags, [sp] x, y, palette, depth)
)
BOTTOM_MANAGER = 0x020AFF50  # pointer to the bottom-screen sprite manager
SYSMENU_ARCHIVE = 4  # sysmenupack.dat
SHEET_TILES = 0x26
SHEET_FRAMES = 0x1A
BRACKET_FRAME = 0x1F
BRACKET_PALETTE = 4  # OBJ extended palette slot (the sheet's three palettes take 4..6)
BRACKET_DEPTH = (
    2  # sort key: above the tabs (1) and rows (0), so a corner is never under a tab
)
MENU_STATE = 0x020B0010  # the place menu's state word
FIRST_SHOWN_STATE = 2  # first frame (preselect)
LAST_SHOWN_STATE = 8  # leaving after a confirmed pick
MENU = 0x020B8C2C
MENU_SELECTED = 0x30  # s16, -1 none
MENU_TAB = 0x32  # s16
TAB_SHIFT = 2  # four rows a tab
ROWS_PER_TAB = 4
BUTTONS = 0x020B7F28
BUTTON_FIRST = 0x0C  # buttons start after the list header
BUTTON_SIZE = 0x30
BUTTON_X = 4  # s16 centre of the button's sprite
BUTTON_Y = 6
FIRST_ROW_BUTTON = 4  # row r of the page is button 4 + r
CORNERS = 4  # top-left, top-right, bottom-left, bottom-right
CORNER_RIGHT = 1
CORNER_BOTTOM = 2
FLIP_SHIFT = (
    3  # corner c is drawn with flags c << 3: 8 mirrors it sideways, 0x10 upside down
)
BRACKET_DX = 100  # corner points: 16 px in from the ends of the 240 px row sprite
BRACKET_DY = 16  # and on its top and bottom edges (the row sprite is 32 px high)
LOAD_FRAME = 8  # stack: the palette slot argument, kept 8-byte aligned
LOAD_ARG = LOAD_FRAME + 8  # the caller's own stack argument (above r4, lr)
ARG_X, ARG_Y, ARG_PALETTE, ARG_DEPTH = 0, 4, 8, 12
SUBMIT_FRAME = (
    0x14  # four stack arguments, kept 8-byte aligned with the seven pushed registers
)

LOAD_ASM = f"""
    push  {{r4, lr}}
    sub   sp, sp, #{LOAD_FRAME}
    ldr   r12, [sp, #{LOAD_ARG}]
    str   r12, [sp]
    bl    {LOAD_SPRITES:#x}
    mov   r4, r0
    mov   r0, #{BRACKET_PALETTE}
    str   r0, [sp]
    ldr   r0, pl_manager
    ldr   r0, [r0]
    mov   r1, #{SYSMENU_ARCHIVE}
    mov   r2, #{SHEET_TILES:#x}
    mov   r3, #{SHEET_FRAMES:#x}
    bl    {LOAD_SPRITES:#x}
    ldr   r1, pl_res
    str   r0, [r1]
    mov   r0, r4
    add   sp, sp, #{LOAD_FRAME}
    pop   {{r4, pc}}
pl_manager:
    .word {BOTTOM_MANAGER:#x}
pl_res:
    .word ${{cave_place_bracket_res}}
"""

BRACKETS_ASM = f"""
    push  {{r4-r9, lr}}
    sub   sp, sp, #{SUBMIT_FRAME:#x}
    mov   r4, r1
    bl    {SUBMIT_BUTTONS:#x}
    ldr   r0, pb_state
    ldr   r0, [r0]
    cmp   r0, #{FIRST_SHOWN_STATE}
    blt   pb_done
    cmp   r0, #{LAST_SHOWN_STATE}
    bgt   pb_done
    ldr   r5, pb_menu
    ldrsh r0, [r5, #{MENU_SELECTED:#x}]
    cmp   r0, #0
    blt   pb_done
    ldrsh r1, [r5, #{MENU_TAB:#x}]
    sub   r0, r0, r1, lsl #{TAB_SHIFT}
    cmp   r0, #{ROWS_PER_TAB}
    bhs   pb_done
    add   r0, r0, #{FIRST_ROW_BUTTON}
    mov   r1, #{BUTTON_SIZE:#x}
    ldr   r2, pb_buttons
    mla   r6, r0, r1, r2
    ldrsh r7, [r6, #{BUTTON_FIRST + BUTTON_X:#x}]
    ldrsh r8, [r6, #{BUTTON_FIRST + BUTTON_Y:#x}]
    ldr   r9, pb_res
    ldr   r9, [r9]
    mov   r5, #0
pb_corner:
    tst   r5, #{CORNER_RIGHT}
    subeq r0, r7, #{BRACKET_DX}
    addne r0, r7, #{BRACKET_DX}
    str   r0, [sp, #{ARG_X}]
    tst   r5, #{CORNER_BOTTOM}
    subeq r0, r8, #{BRACKET_DY}
    addne r0, r8, #{BRACKET_DY}
    str   r0, [sp, #{ARG_Y}]
    mov   r0, #{BRACKET_PALETTE}
    str   r0, [sp, #{ARG_PALETTE}]
    mov   r0, #{BRACKET_DEPTH}
    str   r0, [sp, #{ARG_DEPTH}]
    mov   r0, r4
    mov   r1, r9
    mov   r2, #{BRACKET_FRAME:#x}
    mov   r3, r5, lsl #{FLIP_SHIFT}
    bl    {SUBMIT_SPRITE:#x}
    add   r5, r5, #1
    cmp   r5, #{CORNERS}
    blt   pb_corner
pb_done:
    add   sp, sp, #{SUBMIT_FRAME:#x}
    pop   {{r4-r9, pc}}
pb_state:
    .word {MENU_STATE:#x}
pb_menu:
    .word {MENU:#x}
pb_buttons:
    .word {BUTTONS:#x}
pb_res:
    .word ${{cave_place_bracket_res}}
"""

NOTE = "map menus: the field menu's corner brackets frame the selected place"

TOWN_BRACKET_PATCHES = (
    CaveCode(
        "cave_place_bracket_res", "    .word 0", "map menus: bracket sprite resource"
    ),
    CaveCode("cave_place_bracket_load", LOAD_ASM, NOTE),
    CaveCode("cave_place_brackets", BRACKETS_ASM, NOTE),
    AsmPatch(
        LOAD_CALL,
        LOAD_CALL + 4,
        LOAD_CALL_WORD,
        LOAD_CALL_WORD,
        "bl ${cave_place_bracket_load}",
        NOTE,
    ),
    AsmPatch(
        BUTTONS_CALL,
        BUTTONS_CALL + 4,
        BUTTONS_CALL_WORD,
        BUTTONS_CALL_WORD,
        "bl ${cave_place_brackets}",
        NOTE,
    ),
)
