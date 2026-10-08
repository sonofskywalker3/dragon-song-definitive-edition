"""Field menu shortcuts and speed (Jeff, 2026-10-07 playtest; research in docs/re-field-menu.md).

- Select in the field opens the menu straight at Save: it opens the menu as X does, then presses A for the
  player on System (top menu) and on Save (System list), so the game's own save path runs (and its lock still
  refuses where saving is not allowed).
- Select anywhere in the menu goes back to the map: it presses B for the player every frame until the menu
  starts its exit fade, so each screen frees its own buffers on its own way out.
- The menu is quicker: screen changes wait 6 frames instead of 19 and no longer wait for the icon and tab
  animations, the fades into and out of the menu take 10 frames instead of 30, and a held key repeats after
  12 frames, then every 4 (was 30, then every frame).

The field (mode 1, state 0x14) reads new keys into r7: X opens the menu (state 0xA6), Start the guidebook,
nothing reads Select. The menu (mode 5, func_02059f84) keeps its state in MODE_STATE, the cursor in MENU_CURSOR
and a key mode flag after it (0 on a screen's first frame, when the cursor is forced to 0).
"""

from dsde.patching import AsmPatch, CaveCode, Feature, Patch

FIELD_X_TEST = 0x0201F0AC  # ands r1, r7, #0x400 (X opens the menu), followed by beq
FIELD_X_TEST_WORD = 0xE2171B01
MENU_PAD_CALL = (
    0x02059F98  # bl func_0201a3b8 at the menu's entry, result unused; r0 = pad
)
MENU_PAD_CALL_WORD = 0xEBFF0106
MODE_STATES = 0x020AFF84  # + MODE_STATE_OFFSET = 0x020B0010, the current mode's state
MODE_STATE_OFFSET = 0x8C
MENU_CURSOR = 0x02139F40  # byte; the key mode flag is the word at +4
KEY_MODE = 4
PAD_NEW = 6
KEY_A = 0x1
KEY_B = 0x2
KEY_SELECT = 0x4
KEY_X = 0x400
STATE_TOP = 3  # top menu
STATE_SYSTEM = 0x35  # System list
STATE_EXIT = 0x5C  # exit fade, then back to the field
CURSOR_SYSTEM = 8  # top menu entry
CURSOR_SAVE = 2  # System list entry
# Flags: byte 0 unwinding (Select in the menu), byte 1 save shortcut stage (1 top menu, 2 System list)
SAVE_STAGE_START = 0x100  # halfword: stage 1, not unwinding
STAGE_TOP = 1
STAGE_SYSTEM = 2

FIELD_ASM = f"""
    ands  r1, r7, #{KEY_X:#x}
    movne r0, #0
    bne   fs_store
    ands  r1, r7, #{KEY_SELECT:#x}
    bxeq  lr
    mov   r0, #{SAVE_STAGE_START:#x}
fs_store:
    ldr   r1, fs_flags
    strh  r0, [r1]
    movs  r1, #1
    bx    lr
fs_flags:
    .word ${{cave_menu_flags}}
"""

MENU_ASM = f"""
    ldr   r1, mk_mode
    ldr   r2, [r1, #{MODE_STATE_OFFSET:#x}]
    ldrh  r3, [r0, #{PAD_NEW}]
    ldr   r12, mk_flags
    tst   r3, #{KEY_SELECT:#x}
    beq   mk_unwind
    cmp   r2, #{STATE_EXIT:#x}
    movlo r1, #1
    strhlo r1, [r12]
mk_unwind:
    ldrb  r1, [r12]
    cmp   r1, #0
    beq   mk_save
    cmp   r2, #{STATE_EXIT:#x}
    movhs r1, #0
    strbhs r1, [r12]
    orrlo r3, r3, #{KEY_B:#x}
    strhlo r3, [r0, #{PAD_NEW}]
    bx    lr
mk_save:
    ldrb  r1, [r12, #1]
    cmp   r1, #{STAGE_TOP}
    bne   mk_save2
    cmp   r2, #{STATE_TOP}
    bxne  lr
    ldr   r1, mk_cursor
    ldr   r2, [r1, #{KEY_MODE}]
    cmp   r2, #0
    bxeq  lr
    mov   r2, #{CURSOR_SYSTEM}
    strb  r2, [r1]
    orr   r3, r3, #{KEY_A:#x}
    strh  r3, [r0, #{PAD_NEW}]
    mov   r1, #{STAGE_SYSTEM}
    strb  r1, [r12, #1]
    bx    lr
mk_save2:
    cmp   r1, #{STAGE_SYSTEM}
    bxne  lr
    cmp   r2, #{STATE_SYSTEM:#x}
    bxne  lr
    ldr   r1, mk_cursor
    ldr   r2, [r1, #{KEY_MODE}]
    cmp   r2, #0
    bxeq  lr
    mov   r2, #{CURSOR_SAVE}
    strb  r2, [r1]
    orr   r3, r3, #{KEY_A:#x}
    strh  r3, [r0, #{PAD_NEW}]
    mov   r1, #0
    strb  r1, [r12, #1]
    bx    lr
mk_mode:
    .word {MODE_STATES:#x}
mk_cursor:
    .word {MENU_CURSOR:#x}
mk_flags:
    .word ${{cave_menu_flags}}
"""

# (address, old word, new word, note): measured in docs/re-field-menu.md
MENU_SPEED = (
    (
        0x02061CAC,
        0xE3500013,
        0xE3500006,
        "screen change (state 0x4F) waits 6 frames, not 19",
    ),
    (
        0x02061E2C,
        0xE3500013,
        0xE3500006,
        "going back (state 0x5B) waits 6 frames, not 19",
    ),
    (
        0x02061C84,
        0x1A0000C2,
        0xE1A00000,
        "screen change does not wait for the icon animation",
    ),
    (
        0x02061CA0,
        0x1A0000BB,
        0xE1A00000,
        "screen change does not wait for the tab animation",
    ),
    (0x02061E20, 0x1A00005B, 0xE1A00000, "going back does not wait for the animations"),
    (0x02021468, 0xE3A0201E, 0xE3A0200A, "field fade into the menu: 10 frames, not 30"),
    (0x0205A23C, 0xE3A0201E, 0xE3A0200A, "menu fade-in: 10 frames, not 30"),
    (0x02061E54, 0xE3A0201E, 0xE3A0200A, "menu exit fade: 10 frames, not 30"),
    (0x020595B0, 0xE350001E, 0xE350000C, "a held key repeats after 12 frames"),
    (0x020595BC, 0xE3A0201E, 0xE3A02008, "then every 4 frames"),
)

FIELD_MENU = Feature(
    "field-menu",
    (
        CaveCode("cave_menu_flags", "    .word 0", "menu shortcut flags"),
        CaveCode(
            "cave_field_select", FIELD_ASM, "field: Select opens the menu at Save"
        ),
        CaveCode("cave_menu_keys", MENU_ASM, "menu: Select closes it; save shortcut"),
        AsmPatch(
            FIELD_X_TEST,
            FIELD_X_TEST + 4,
            FIELD_X_TEST_WORD,
            FIELD_X_TEST_WORD,
            "bl ${cave_field_select}",
            "field: X or Select opens the menu",
        ),
        AsmPatch(
            MENU_PAD_CALL,
            MENU_PAD_CALL + 4,
            MENU_PAD_CALL_WORD,
            MENU_PAD_CALL_WORD,
            "bl ${cave_menu_keys}",
            "menu: Select closes it; save shortcut",
        ),
        *(Patch(addr, old, new, note) for addr, old, new, note in MENU_SPEED),
    ),
)
