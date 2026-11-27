"""Town and world map menus work with the D-pad (Jeff, 2026-10-07).

A "Select place to go" menu (game mode 2, func_02042c08, the same code for every hub map 0x104..0x126: the
world map hubs 0x104..0x11C and the towns from 0x11D) lists the places as pages of four rows behind tabs on the
touch screen; only touch could switch tabs, and the D-pad dragged the Jian icon around the map instead. Now, in
towns and on the world map alike (Jeff found the switch between the two jarring): Up/Down move through the rows
of the tab, Left/Right switch tabs, A goes (vanilla), and touch works as before.

Menu state at S = 0x020B8C2C: +0x30 selected entry (index into the visible list, -1 none), +0x32 tab (page of
four), +0x38 number of visible entries. Research and tests: docs/re-field-battle.md "Town map menu".

- Each frame the menu asks TOUCH_HIT which bottom-screen sprite was touched (rows are ids 4..7). The hook
  returns that when something was touched; otherwise a new D-pad press becomes a touch of a row (setting the
  tab first for Left/Right), so the vanilla touch path plays the sound, switches the page, highlights the row,
  moves the Jian icon to the place and shows YES/NO, ready for A.
- The free-cursor test (`ands r0, held, #0xF0`) sees no D-pad, so a held key does not drag the icon.

B (and the NO button) picks the way out in a town (Jeff, 2026-11-22; its own feature, town-menu-leave). In the original it went back to the
entry for the place you had just left, which you seldom want again; now it selects "Leave town" (the first
listed entry that leads to a world map hub, 0x104..0x11C), ready for A. A town part with no such entry
(Zethos Castle) gets its entry to the neighboring part instead. On the world map, and in a town whose
Leave entry is still hidden, B does what it did. The three places that looked up the entry of the previous
map (func_020426c0) call the cave instead, and B no longer skips the lookup when the previous place is
already selected.
"""

from dsde.patching import AsmPatch, CaveCode

TOUCH_HIT_CALL = (
    0x020434D0  # bl func_020273b0: touched bottom-screen sprite id, -1 none
)
TOUCH_HIT_CALL_WORD = 0xEBFF8FB6
TOUCH_HIT = 0x020273B0
FREE_CURSOR_TEST = 0x0204364C  # ands r0, r0, #0xF0 (held D-pad keys)
FREE_CURSOR_TEST_WORD = 0xE21000F0
NO_KEYS = 0  # the free-cursor test sees no D-pad
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

TOWN_KEYS_ASM = f"""
    push  {{r4-r8, lr}}
    bl    {TOUCH_HIT:#x}
    cmn   r0, #1
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

BACK_ENTRY = (
    0x020426C0  # (map) -> visible index of the entry that leads to map, -1 none
)
BACK_ENTRY_CALLS = {  # bl func_020426c0 with r0 = the previous map
    0x020435BC: 0xEBFFFC3F,  # the NO button
    0x02043990: 0xEBFFFB4A,  # B with an entry selected
    0x020439B0: 0xEBFFFB42,  # B with nothing selected
}
BACK_SAME_SKIP = (
    0x0204398C  # beq: B does nothing when the previous place is already selected
)
BACK_SAME_SKIP_WORD = 0x0A000009
CURRENT_MAP = 0x020B6BE4  # s16
MENU_EXITS = 0x34  # pointer to the hub table entry, whose first word is the exit list
MENU_VISIBLE = 0x3C  # u8[]: visible entry -> exit list index
EXIT_SHIFT = (
    2  # an exit is 12 bytes (index * 3 << 2); its first s16 is the map it leads to
)
FIRST_HUB = 0x104  # world map hubs 0x104..0x11C
FIRST_TOWN_HUB = 0x11D  # town hubs from here on

# Replaces `bl func_020426c0` (r0 = the previous map): the entry B goes to.
TOWN_BACK_ASM = f"""
    push  {{r4-r7, lr}}
    mov   r7, r0
    ldr   r4, tb_menu
    ldr   r0, tb_map
    ldrsh r0, [r0]
    ldr   r1, tb_town
    cmp   r0, r1
    blt   tb_previous
    ldr   r5, [r4, #{MENU_COUNT:#x}]
    ldr   r6, [r4, #{MENU_EXITS:#x}]
    ldr   r6, [r6]
    mov   r2, #0
    mvn   r3, #0
tb_next:
    cmp   r2, r5
    bge   tb_listed
    add   r0, r4, r2
    ldrb  r0, [r0, #{MENU_VISIBLE:#x}]
    add   r0, r0, r0, lsl #1
    add   r0, r6, r0, lsl #{EXIT_SHIFT}
    ldrsh r0, [r0]
    cmp   r0, #{FIRST_HUB:#x}
    blt   tb_step
    cmp   r0, r1
    movlt r0, r2
    poplt {{r4-r7, pc}}
    cmn   r3, #1
    moveq r3, r2
tb_step:
    add   r2, r2, #1
    b     tb_next
tb_listed:
    cmn   r3, #1
    movne r0, r3
    popne {{r4-r7, pc}}
tb_previous:
    mov   r0, r7
    bl    {BACK_ENTRY:#x}
    pop   {{r4-r7, pc}}
tb_menu:
    .word {MENU:#x}
tb_map:
    .word {CURRENT_MAP:#x}
tb_town:
    .word {FIRST_TOWN_HUB:#x}
"""

TOWN_BACK_PATCHES = (
    CaveCode("cave_town_back", TOWN_BACK_ASM, "town menus: B picks the way out"),
    *(
        AsmPatch(
            addr,
            addr + 4,
            word,
            word,
            "bl ${cave_town_back}",
            "town menus: B picks the way out",
        )
        for addr, word in BACK_ENTRY_CALLS.items()
    ),
    AsmPatch(
        BACK_SAME_SKIP,
        BACK_SAME_SKIP + 4,
        BACK_SAME_SKIP_WORD,
        BACK_SAME_SKIP_WORD,
        "nop",
        "town menus: B picks the way out even from the previous place",
    ),
)

TOWN_MENU_PATCHES = (
    CaveCode("cave_town_keys", TOWN_KEYS_ASM, "map menus: D-pad picks rows and tabs"),
    AsmPatch(
        TOUCH_HIT_CALL,
        TOUCH_HIT_CALL + 4,
        TOUCH_HIT_CALL_WORD,
        TOUCH_HIT_CALL_WORD,
        "bl ${cave_town_keys}",
        "map menus: D-pad picks rows and tabs",
    ),
    AsmPatch(
        FREE_CURSOR_TEST,
        FREE_CURSOR_TEST + 4,
        FREE_CURSOR_TEST_WORD,
        FREE_CURSOR_TEST_WORD,
        f"ands r0, r0, #{NO_KEYS}",
        "map menus: the D-pad no longer drags the map icon",
    ),
)
