"""Select shortcuts in and out of the field menu (Jeff, 2026-10-08), jumping straight there, no keys pressed.

- Select in the field opens the menu straight at the save screen. The menu loads as for X; its first screen
  change, from loading to the top menu (state 0x4F towards 3), is sent to the System setup (0x33) instead, as
  picking System would; once that has set up the screen (state 0x34, before the System list shows), the next
  screen change goes to the save screen's setup (0x3B) with what picking Save sets: the save flag 0x02139EF4, the
  cursor back on the first entry, and the header tab tucked away for the next label. The menu stays
  black over those few setup frames and fades in on the save screen, as it fades in on the top menu for X. The top menu and the System list never run, and no selection sounds play. B on the save
  screen goes to the System list as usual. Where saving is not allowed (func_02056f0c is 0) the menu opens as
  for X.
- Select anywhere in the menu goes straight to its exit (state 0x5C: a short fade, then the field). The exit
  only frees the menu's own buffer (0x0213B27C + 0x60C); each sub-screen (Magic, Items, the grey-box entry)
  frees its own buffers on its way back, so the menu's heap allocations are tracked (HEAP_LOG, filled by hooks on
  func_02005298 and func_02005224 while the game is in the menu) and whatever an open screen still holds is
  freed before the jump. Not while a save is being written (states 0x40, 0x41).

Research: docs/re-field-menu.md.
"""

from dsde.patching import AsmPatch, CaveCode

FIELD_X_TEST = 0x0201F0AC  # ands r1, r7, #0x400 (X opens the menu), followed by beq
FIELD_X_TEST_WORD = 0xE2171B01
MENU_PAD_CALL = (
    0x02059F98  # bl func_0201a3b8 at the menu's entry, result unused; r0 = pad
)
MENU_PAD_CALL_WORD = 0xEBFF0106
HEAP_ALLOC = 0x02005298  # func_02005298(arena, -1, size): push {r4-r7, lr} first
HEAP_FREE = 0x02005224  # func_02005224(arena, -1, block): push {r4-r7, lr} first
HEAP_ENTRY_WORD = 0xE92D40F0
SAVE_ALLOWED = 0x02056F0C  # func_02056f0c: 0 where saving is locked
GAME_MODE = 0x020B000C
MENU_MODE = 5
MODE_STATES = 0x020AFF84  # + MODE_STATE_OFFSET = 0x020B0010, the current mode's state
MODE_STATE_OFFSET = 0x8C
MENU_WORK = 0x02139FD4  # +1: the state a screen change (0x4F) goes to
MENU_BASE_BUFFER = (
    0x0213B27C + 0x60C
)  # pointer to the menu's own buffer, freed by the exit
SAVE_FLAG = 0x02139EF4  # set when System, Save opens the save screen
MENU_CURSOR = 0x02139F40
FIRST_ENTRY = (
    0  # picking System, then Save, each leave the cursor here (diag_save_path)
)
PAD_NEW = 6
KEY_SELECT = 0x4
KEY_X = 0x400
STATE_LOAD = 0  # the menu's first state: loads it and allocates its buffer
STATE_TOP = 3
STATE_CHANGE = 0x4F
STATE_SYSTEM_SETUP = 0x33  # sets up the System screen (sprites, title, list window)
STATE_SYSTEM_READY = 0x34  # next: the screen change to the System list
STATE_SAVE_SETUP = 0x3B
STATE_SAVE = 0x3D
STATE_WRITING = (0x40, 0x41)  # writing the save
STATE_EXIT = 0x5C
HEAP_LOG_SIZE = 16
FADE = (
    0x02018CBC  # func_02018cbc(screens, level, frames): 0 frames sets the level at once
)
BOTH_SCREENS = 3
LEVEL_BLACK = 0
LEVEL_NORMAL = 0x80
FADE_IN_FRAMES = 10  # the menu's own fade-in (feat_field_menu.py)
HEADER_TAB = 0x02059BCC  # func_02059bcc(0, 0) tucks the header tab away; the next screen shows its label
TAB_HIDE = 0
SHORTCUT_LIMIT = 120  # frames before a shortcut that never arrives gives up
# Flags word: byte 1 the open-at-save stage (1 waiting for the first screen change, 2 arriving), byte 2 frames
OPEN_START = 0x100
STAGE_WAITING = 1  # menu loading: its first screen change goes to the System setup instead of the top menu
STAGE_SYSTEM = 2  # System set up: switch to the save screen as picking Save does, before the list shows
STAGE_ARRIVING = 3

# Replaces `ands r1, r7, #0x400` (r7 = new keys) every field frame: sets the flags for this frame's key (none:
# cleared, so a menu opened by touch never inherits a shortcut) and leaves Z clear when X or Select opens the menu.
FIELD_ASM = f"""
    push  {{r0}}
    ldr   r1, fs_flags
    mov   r0, #0
    tst   r7, #{KEY_SELECT:#x}
    movne r0, #{OPEN_START:#x}
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

# Replaces `bl func_0201a3b8` at the menu's entry, every menu frame. r0 = pad.
MENU_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r5, r0
    ldr   r6, mk_flags
    ldr   r1, mk_mode
    ldr   r4, [r1, #{MODE_STATE_OFFSET:#x}]
    cmp   r4, #{STATE_LOAD}
    bne   mk_keys
    ldr   r1, mk_log
    mov   r2, #0
    mov   r3, #0
mk_clear:
    str   r3, [r1, r2, lsl #2]
    add   r2, r2, #1
    cmp   r2, #{HEAP_LOG_SIZE}
    blt   mk_clear
mk_keys:
    ldrh  r3, [r5, #{PAD_NEW}]
    tst   r3, #{KEY_SELECT:#x}
    beq   mk_open
    cmp   r4, #{STATE_TOP}
    blo   mk_open
    cmp   r4, #{STATE_WRITING[0]:#x}
    cmpne r4, #{STATE_WRITING[1]:#x}
    beq   mk_open
    cmp   r4, #{STATE_EXIT:#x}
    bhs   mk_open
    bl    ${{cave_menu_release}}
    ldr   r1, mk_mode
    mov   r2, #{STATE_EXIT:#x}
    str   r2, [r1, #{MODE_STATE_OFFSET:#x}]
    mov   r1, #0
    str   r1, [r6]
    pop   {{r4-r6, pc}}
mk_open:
    ldr   r1, [r6]
    cmp   r1, #0
    popeq {{r4-r6, pc}}
    ldrb  r1, [r6, #2]
    add   r1, r1, #1
    strb  r1, [r6, #2]
    cmp   r1, #{SHORTCUT_LIMIT}
    movhs r1, #0
    strhs r1, [r6]
    pophs {{r4-r6, pc}}
    ldrb  r1, [r6, #1]
    cmp   r1, #{STAGE_WAITING}
    bne   mk_system
    cmp   r4, #{STATE_CHANGE:#x}
    popne {{r4-r6, pc}}
    ldr   r2, mk_work
    ldrb  r3, [r2, #1]
    cmp   r3, #{STATE_TOP}
    popne {{r4-r6, pc}}
    bl    {SAVE_ALLOWED:#x}
    cmp   r0, #0
    moveq r1, #0
    streq r1, [r6]
    popeq {{r4-r6, pc}}
    mov   r0, #{BOTH_SCREENS}
    mov   r1, #{LEVEL_BLACK}
    mov   r2, #0
    bl    {FADE:#x}
    mov   r0, #{TAB_HIDE}
    mov   r1, #0
    bl    {HEADER_TAB:#x}
    ldr   r2, mk_work
    mov   r3, #{STATE_SYSTEM_SETUP:#x}
    strb  r3, [r2, #1]
    ldr   r2, mk_cursor
    mov   r3, #{FIRST_ENTRY}
    strb  r3, [r2]
    mov   r1, #{STAGE_SYSTEM}
    strb  r1, [r6, #1]
    pop   {{r4-r6, pc}}
mk_system:
    cmp   r1, #{STAGE_SYSTEM}
    bne   mk_arrive
    cmp   r4, #{STATE_SYSTEM_READY:#x}
    popne {{r4-r6, pc}}
    mov   r0, #{TAB_HIDE}
    mov   r1, #0
    bl    {HEADER_TAB:#x}
    ldr   r2, mk_work
    mov   r3, #{STATE_SAVE_SETUP:#x}
    strb  r3, [r2, #1]
    ldr   r1, mk_mode
    mov   r3, #{STATE_CHANGE:#x}
    str   r3, [r1, #{MODE_STATE_OFFSET:#x}]
    ldr   r2, mk_save_flag
    mov   r3, #1
    strb  r3, [r2]
    ldr   r2, mk_cursor
    mov   r3, #{FIRST_ENTRY}
    strb  r3, [r2]
    mov   r1, #{STAGE_ARRIVING}
    strb  r1, [r6, #1]
    pop   {{r4-r6, pc}}
mk_arrive:
    cmp   r4, #{STATE_SAVE:#x}
    popne {{r4-r6, pc}}
    mov   r1, #0
    str   r1, [r6]
    mov   r0, #{BOTH_SCREENS}
    mov   r1, #{LEVEL_NORMAL}
    mov   r2, #{FADE_IN_FRAMES}
    bl    {FADE:#x}
    pop   {{r4-r6, pc}}
mk_mode:
    .word {MODE_STATES:#x}
mk_flags:
    .word ${{cave_menu_flags}}
mk_log:
    .word ${{cave_heap_log}}
mk_work:
    .word {MENU_WORK:#x}
mk_save_flag:
    .word {SAVE_FLAG:#x}
mk_cursor:
    .word {MENU_CURSOR:#x}
"""


# Frees every block the menu's screens still hold (the heap log, less the menu's own buffer).
RELEASE_ASM = f"""
    push  {{r4-r6, lr}}
    ldr   r4, rl_log
    ldr   r5, rl_base
    ldr   r5, [r5]
    mov   r6, #0
rl_loop:
    ldr   r2, [r4, r6, lsl #2]
    cmp   r2, #0
    beq   rl_next
    cmp   r2, r5
    beq   rl_next
    mov   r0, #0
    mvn   r1, #0
    bl    {HEAP_FREE:#x}
rl_next:
    add   r6, r6, #1
    cmp   r6, #{HEAP_LOG_SIZE}
    blt   rl_loop
    pop   {{r4-r6, pc}}
rl_log:
    .word ${{cave_heap_log}}
rl_base:
    .word {MENU_BASE_BUFFER:#x}
"""

# Entered from `b` at func_02005298's first instruction; runs the function, then logs the block in the menu.
ALLOC_ASM = f"""
    push  {{r4, lr}}
    bl    ha_original
    ldr   r1, ha_mode
    ldr   r1, [r1]
    cmp   r1, #{MENU_MODE}
    cmpeq r0, #0
    popeq {{r4, pc}}
    cmp   r1, #{MENU_MODE}
    popne {{r4, pc}}
    ldr   r1, ha_log
    mov   r2, #0
ha_find:
    ldr   r3, [r1, r2, lsl #2]
    cmp   r3, #0
    streq r0, [r1, r2, lsl #2]
    popeq {{r4, pc}}
    add   r2, r2, #1
    cmp   r2, #{HEAP_LOG_SIZE}
    blt   ha_find
    pop   {{r4, pc}}
ha_original:
    push  {{r4-r7, lr}}
    b     {HEAP_ALLOC + 4:#x}
ha_mode:
    .word {GAME_MODE:#x}
ha_log:
    .word ${{cave_heap_log}}
"""

# Entered from `b` at func_02005224's first instruction (r2 = block): drops the block from the log, then frees.
FREE_ASM = f"""
    push  {{r4}}
    ldr   r12, hf_log
    mov   r3, #0
hf_find:
    ldr   r4, [r12, r3, lsl #2]
    cmp   r4, r2
    moveq r4, #0
    streq r4, [r12, r3, lsl #2]
    add   r3, r3, #1
    cmp   r3, #{HEAP_LOG_SIZE}
    blt   hf_find
    pop   {{r4}}
    push  {{r4-r7, lr}}
    b     {HEAP_FREE + 4:#x}
hf_log:
    .word ${{cave_heap_log}}
"""


def _replace(addr: int, word: int, asm: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, word, word, asm, note)


SHORTCUT_PATCHES = (
    CaveCode("cave_menu_flags", "    .word 0", "menu shortcut flags"),
    CaveCode(
        "cave_heap_log",
        "\n".join(["    .word 0"] * HEAP_LOG_SIZE),
        "blocks the menu holds",
    ),
    CaveCode("cave_field_select", FIELD_ASM, "field: Select opens the menu at Save"),
    CaveCode("cave_menu_keys", MENU_ASM, "menu: Select exits; open at the save screen"),
    CaveCode("cave_menu_release", RELEASE_ASM, "menu: free what open screens hold"),
    CaveCode("cave_heap_alloc", ALLOC_ASM, "log the menu's heap blocks"),
    CaveCode("cave_heap_free", FREE_ASM, "unlog freed heap blocks"),
    _replace(
        FIELD_X_TEST,
        FIELD_X_TEST_WORD,
        "bl ${cave_field_select}",
        "field: X or Select opens the menu",
    ),
    _replace(
        MENU_PAD_CALL,
        MENU_PAD_CALL_WORD,
        "bl ${cave_menu_keys}",
        "menu: Select shortcuts",
    ),
    _replace(
        HEAP_ALLOC,
        HEAP_ENTRY_WORD,
        "b ${cave_heap_alloc}",
        "log the menu's heap blocks",
    ),
    _replace(
        HEAP_FREE, HEAP_ENTRY_WORD, "b ${cave_heap_free}", "unlog freed heap blocks"
    ),
)
