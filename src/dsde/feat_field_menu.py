"""Field menu speed and shortcuts (Jeff, 2026-10-07 and 2026-10-08 playtests; research in docs/re-field-menu.md).

- Select in the field opens the save screen, and Select anywhere in the menu goes straight back to the map
  (feat_menu_shortcuts.py).
- The menu is quicker: screen changes wait 6 frames instead of 19 (none while Select opens the save screen) and
  no longer wait for the icon and tab animations, the fades into and out of the menu take 10 frames instead of
  30, and a held key repeats after 12 frames, then every 4 (was 30, then every frame).
"""

from dsde.feat_menu_shortcuts import SHORTCUT_PATCHES
from dsde.patching import AsmPatch, CaveCode, Feature, Patch

CHANGE_FLOOR_TEST = (
    0x02061CAC  # state 0x4F (screen change): cmp r0, #0x13 (frames waited)
)
BACK_FLOOR_TEST = 0x02061E2C  # state 0x5B (going back): cmp r0, #0x13
FLOOR_TEST_WORD = 0xE3500013
FLOOR = 6  # frames a screen change waits (vanilla 19); 0 while a shortcut runs

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
        *SHORTCUT_PATCHES,
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
