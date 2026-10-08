"""Town map menus work with the D-pad (Jeff, 2026-10-07).

A town's "Select place to go" menu (game mode 2, func_02042c08, the same code for every hub map 0x104..0x126)
lists the places as pages of four rows behind tabs on the touch screen; only touch could switch tabs, and the
D-pad dragged the Jian icon around the town map instead. In towns now: Up/Down move through the rows of the
tab, Left/Right switch tabs, A goes (vanilla), and touch works as before. The overworld hubs (0x104..0x11C,
where func_0204273c is true) keep their free D-pad cursor, which scrolls the world map.

Menu state at S = 0x020B8C2C: +0x30 selected entry (index into the visible list, -1 none), +0x32 tab (page of
four), +0x38 number of visible entries. Research and tests: docs/re-field-battle.md "Town map menu".

- Each frame the menu asks TOUCH_HIT which bottom-screen sprite was touched (rows are ids 4..7). The hook
  returns that when something was touched; otherwise a new D-pad press becomes a touch of a row (setting the
  tab first for Left/Right), so the vanilla touch path plays the sound, switches the page, highlights the row,
  moves the Jian icon to the place and shows YES/NO, ready for A.
- The free-cursor test (`ands r0, held, #0xF0`) sees no D-pad in towns, so a held key does not drag the icon.
"""

from dsde.patching import AsmPatch, CaveCode

TOUCH_HIT_CALL = (
    0x020434D0  # bl func_020273b0: touched bottom-screen sprite id, -1 none
)
TOUCH_HIT_CALL_WORD = 0xEBFF8FB6
TOUCH_HIT = 0x020273B0
FREE_CURSOR_TEST = 0x0204364C  # ands r0, r0, #0xF0 (held D-pad keys)
FREE_CURSOR_TEST_WORD = 0xE21000F0
IS_OVERWORLD = 0x0204273C  # () -> true on the scrolling overworld hubs
PAD_NEW = 0x020AFF7A  # u16 keys newly pressed this frame (pad struct 0x020AFF74 + 6)
MENU = 0x020B8C2C
MENU_SELECTED = 0x30  # s16, -1 none
MENU_TAB = 0x32  # s16
MENU_COUNT = 0x38  # s32
ROWS_PER_TAB = 4
TAB_SHIFT = 2  # log2(ROWS_PER_TAB)
FIRST_ROW_SPRITE = 4  # row r of the page is bottom-screen sprite 4 + r
KEY_RIGHT = 0x10
KEY_LEFT = 0x20
KEY_UP = 0x40
KEY_DOWN = 0x80
DPAD = 0xF0

TOWN_KEYS_ASM = f"""
    push  {{r4-r8, lr}}
    bl    {TOUCH_HIT:#x}
    cmn   r0, #1
    popne {{r4-r8, pc}}
    bl    {IS_OVERWORLD:#x}
    cmp   r0, #0
    mvnne r0, #0
    popne {{r4-r8, pc}}
    ldr   r1, tk_pad
    ldrh  r1, [r1]
    ldr   r4, tk_menu
    ldr   r5, [r4, #{MENU_COUNT:#x}]
    cmp   r5, #0
    mvnle r0, #0
    pople {{r4-r8, pc}}
    ldrsh r6, [r4, #{MENU_TAB:#x}]
    ldrsh r7, [r4, #{MENU_SELECTED:#x}]
    sub   r2, r5, r6, lsl #{TAB_SHIFT}
    cmp   r2, #{ROWS_PER_TAB}
    movgt r2, #{ROWS_PER_TAB}
    sub   r8, r7, r6, lsl #{TAB_SHIFT}
    tst   r1, #{KEY_UP:#x}
    bne   tk_up
    tst   r1, #{KEY_DOWN:#x}
    bne   tk_down
    tst   r1, #{KEY_LEFT:#x}
    bne   tk_left
    tst   r1, #{KEY_RIGHT:#x}
    bne   tk_right
    mvn   r0, #0
    pop   {{r4-r8, pc}}
tk_up:
    cmn   r7, #1
    subeq r0, r2, #1
    beq   tk_row
    subs  r0, r8, #1
    addlt r0, r0, r2
    b     tk_row
tk_down:
    cmn   r7, #1
    moveq r0, #0
    beq   tk_row
    add   r0, r8, #1
    cmp   r0, r2
    movge r0, #0
tk_row:
    add   r3, r0, r6, lsl #{TAB_SHIFT}
    cmp   r3, r7
    mvneq r0, #0
    addne r0, r0, #{FIRST_ROW_SPRITE}
    pop   {{r4-r8, pc}}
tk_left:
    add   r3, r5, #{ROWS_PER_TAB - 1}
    mov   r3, r3, lsr #{TAB_SHIFT}
    cmp   r3, #1
    mvnle r0, #0
    pople {{r4-r8, pc}}
    subs  r6, r6, #1
    addlt r6, r6, r3
    b     tk_tab
tk_right:
    add   r3, r5, #{ROWS_PER_TAB - 1}
    mov   r3, r3, lsr #{TAB_SHIFT}
    cmp   r3, #1
    mvnle r0, #0
    pople {{r4-r8, pc}}
    add   r6, r6, #1
    cmp   r6, r3
    movge r6, #0
tk_tab:
    cmn   r7, #1
    moveq r8, #0
    sub   r2, r5, r6, lsl #{TAB_SHIFT}
    cmp   r2, #{ROWS_PER_TAB}
    movgt r2, #{ROWS_PER_TAB}
    cmp   r8, r2
    subge r8, r2, #1
    strh  r6, [r4, #{MENU_TAB:#x}]
    add   r0, r8, #{FIRST_ROW_SPRITE}
    pop   {{r4-r8, pc}}
tk_pad:
    .word {PAD_NEW:#x}
tk_menu:
    .word {MENU:#x}
"""

# Replaces `ands r0, r0, #0xF0`: the flags it leaves decide the free cursor. Towns: no D-pad.
TOWN_CURSOR_ASM = f"""
    push  {{r0, lr}}
    bl    {IS_OVERWORLD:#x}
    cmp   r0, #0
    pop   {{r0, lr}}
    andsne r0, r0, #{DPAD:#x}
    movseq r0, #0
    bx    lr
"""

TOWN_MENU_PATCHES = (
    CaveCode("cave_town_keys", TOWN_KEYS_ASM, "town menu: D-pad picks rows and tabs"),
    CaveCode(
        "cave_town_cursor", TOWN_CURSOR_ASM, "town menu: D-pad leaves the map icon"
    ),
    AsmPatch(
        TOUCH_HIT_CALL,
        TOUCH_HIT_CALL + 4,
        TOUCH_HIT_CALL_WORD,
        TOUCH_HIT_CALL_WORD,
        "bl ${cave_town_keys}",
        "town menu: D-pad picks rows and tabs",
    ),
    AsmPatch(
        FREE_CURSOR_TEST,
        FREE_CURSOR_TEST + 4,
        FREE_CURSOR_TEST_WORD,
        FREE_CURSOR_TEST_WORD,
        "bl ${cave_town_cursor}",
        "town menu: D-pad leaves the map icon",
    ),
)
