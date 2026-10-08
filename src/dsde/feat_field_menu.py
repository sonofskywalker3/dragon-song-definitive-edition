"""Field menu shortcuts and speed (Jeff, 2026-10-07 and 2026-10-08 playtests; research in docs/re-field-menu.md).

- Select in the field opens the save screen. Behind a black screen it opens the menu as X does and presses A
  for the player on System (top menu) and on Save (System list), with every screen change instant, then shows
  the save screen. The game's own path runs, so each screen sets itself up, B on the save screen goes back to
  the System list as usual, and the save lock still refuses where saving is not allowed.
- Select anywhere in the menu goes straight back to the map: behind a black screen it presses B for the player
  every frame, with every screen change instant, until the menu starts its exit, so each screen frees its own
  buffers on its own way out (jumping to the exit states would skip that; docs/re-field-menu.md). The screen
  stays black through the menu's exit until the field fades in; the field clears the flags.
- A shortcut gives up after SHORTCUT_LIMIT frames and shows the screen again, so a refused save cannot leave it
  black.
- The menu is quicker: screen changes wait 6 frames instead of 19 (none during a shortcut) and no longer wait
  for the icon and tab animations, the fades into and out of the menu take 10 frames instead of 30, and a held
  key repeats after 12 frames, then every 4 (was 30, then every frame).

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
CHANGE_FLOOR_TEST = (
    0x02061CAC  # state 0x4F (screen change): cmp r0, #0x13 (frames waited)
)
BACK_FLOOR_TEST = 0x02061E2C  # state 0x5B (going back): cmp r0, #0x13
FLOOR_TEST_WORD = 0xE3500013
FLOOR = 6  # frames a screen change waits (vanilla 19); 0 during a shortcut
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
STATE_SLOTS = 0x3D  # save screen (album slots)
STATE_EXIT = 0x5C  # exit fade, then back to the field
CURSOR_SYSTEM = 8  # top menu entry
CURSOR_SAVE = 2  # System list entry
BRIGHTNESS = (
    0x0400006C  # master brightness, main screen; the sub screen's is SUB_SCREEN further
)
SUB_SCREEN = 0x1000
BLACK = 0x8010  # brightness down, full
NORMAL_BRIGHTNESS = 0
SHORTCUT_LIMIT = 120  # frames
# Flags word: byte 0 unwinding (Select in the menu), byte 1 save shortcut stage, byte 2 frames it has run
UNWIND = 1
SAVE_STAGE_START = 0x100  # stage 1, not unwinding, no frames
STAGE_TOP = 1
STAGE_SYSTEM = 2
STAGE_SLOTS = 3

# Replaces `ands r1, r7, #0x400` (r7 = new keys) every field frame: sets the flags for this frame's key (none:
# cleared, so a menu opened by touch never inherits a shortcut) and leaves Z clear when X or Select opens the menu.
FIELD_ASM = f"""
    push  {{r0}}
    ldr   r1, fs_flags
    mov   r0, #0
    tst   r7, #{KEY_SELECT:#x}
    movne r0, #{SAVE_STAGE_START:#x}
    tst   r7, #{KEY_X:#x}
    movne r0, #0
    str   r0, [r1]
    pop   {{r0}}
    ands  r1, r7, #{KEY_X:#x}
    bxne  lr
    ands  r1, r7, #{KEY_SELECT:#x}
    bx    lr
fs_flags:
    .word ${{cave_menu_flags}}
"""

MENU_ASM = f"""
    push  {{r4, lr}}
    ldr   r1, mk_mode
    ldr   r2, [r1, #{MODE_STATE_OFFSET:#x}]
    ldrh  r3, [r0, #{PAD_NEW}]
    ldr   r12, mk_flags
    tst   r3, #{KEY_SELECT:#x}
    beq   mk_running
    cmp   r2, #{STATE_EXIT:#x}
    movlo r1, #{UNWIND}
    strlo r1, [r12]
mk_running:
    ldr   r1, [r12]
    cmp   r1, #0
    popeq {{r4, pc}}
    ldrb  r1, [r12, #2]
    add   r1, r1, #1
    strb  r1, [r12, #2]
    cmp   r1, #{SHORTCUT_LIMIT}
    bhs   mk_done
    ldr   r1, mk_bright
    ldr   r4, mk_black
    strh  r4, [r1]
    add   r1, r1, #{SUB_SCREEN:#x}
    strh  r4, [r1]
    ldrb  r1, [r12]
    cmp   r1, #0
    beq   mk_save
    cmp   r2, #{STATE_EXIT:#x}
    orrlo r3, r3, #{KEY_B:#x}
    strhlo r3, [r0, #{PAD_NEW}]
    pop   {{r4, pc}}
mk_save:
    ldrb  r1, [r12, #1]
    cmp   r1, #{STAGE_TOP}
    beq   mk_top
    cmp   r1, #{STAGE_SYSTEM}
    beq   mk_system
    cmp   r2, #{STATE_SLOTS:#x}
    popne {{r4, pc}}
    b     mk_done
mk_top:
    cmp   r2, #{STATE_TOP}
    popne {{r4, pc}}
    mov   r4, #{CURSOR_SYSTEM}
    mov   r1, #{STAGE_SYSTEM}
    b     mk_pick
mk_system:
    cmp   r2, #{STATE_SYSTEM:#x}
    popne {{r4, pc}}
    mov   r4, #{CURSOR_SAVE}
    mov   r1, #{STAGE_SLOTS}
mk_pick:
    ldr   r2, mk_cursor
    ldr   lr, [r2, #{KEY_MODE}]
    cmp   lr, #0
    popeq {{r4, pc}}
    strb  r4, [r2]
    orr   r3, r3, #{KEY_A:#x}
    strh  r3, [r0, #{PAD_NEW}]
    strb  r1, [r12, #1]
    pop   {{r4, pc}}
mk_done:
    mov   r1, #0
    str   r1, [r12]
    ldr   r1, mk_bright
    mov   r4, #{NORMAL_BRIGHTNESS}
    strh  r4, [r1]
    add   r1, r1, #{SUB_SCREEN:#x}
    strh  r4, [r1]
    pop   {{r4, pc}}
mk_mode:
    .word {MODE_STATES:#x}
mk_cursor:
    .word {MENU_CURSOR:#x}
mk_flags:
    .word ${{cave_menu_flags}}
mk_bright:
    .word {BRIGHTNESS:#x}
mk_black:
    .word {BLACK:#x}
"""

# Replaces `cmp r0, #0x13` in both screen change states (r0 = frames waited); r2 is free there.
FLOOR_ASM = f"""
    ldr   r2, fl_flags
    ldr   r2, [r2]
    cmp   r2, #0
    moveq r2, #{FLOOR}
    movne r2, #0
    cmp   r0, r2
    bx    lr
fl_flags:
    .word ${{cave_menu_flags}}
"""

# (address, old word, new word, note): measured in docs/re-field-menu.md
MENU_SPEED = (
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
        CaveCode(
            "cave_menu_floor",
            FLOOR_ASM,
            "menu: screen changes wait 6 frames, none in a shortcut",
        ),
        *(
            AsmPatch(
                addr,
                addr + 4,
                FLOOR_TEST_WORD,
                FLOOR_TEST_WORD,
                "bl ${cave_menu_floor}",
                "menu: screen changes wait 6 frames, none in a shortcut",
            )
            for addr in (CHANGE_FLOOR_TEST, BACK_FLOOR_TEST)
        ),
        *(Patch(addr, old, new, note) for addr, old, new, note in MENU_SPEED),
    ),
)
