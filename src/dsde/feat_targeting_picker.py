"""The enemy picker for manual targeting: the battle menu's list page laid out like the battle.

Page 4 (the item list) shows six cells per page in three columns of two: cell 2c is column c's top
row, cell 2c + 1 its bottom row. Back-row enemies (battlers 4..7, high on the screen) fill the top
row and front-row enemies (battlers 8..11) the bottom row, each left to right as on screen, so a
column holds the n-th enemy of each row. Cells with no enemy are holes: their button is removed
after the game builds the rows, and our own D-pad handler steps over them.
"""

from dsde.feat_targeting_menu import DISPATCH_ASM, OPEN_ASM
from dsde.patching import AsmPatch, CaveCode
from dsde.targeting_consts import (
    BATTLER_SIZE,
    BATTLERS_PTR,
    BUILD_ROWS,
    BUILD_ROWS_CALLS,
    BUTTON_SIZE,
    BUTTONS_PTR,
    CARD_ITEM_BASE,
    CHAR_ID,
    CLEAR_GROUP_HIGHLIGHT,
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    DOTS_BUILD,
    DOTS_UPDATE,
    FIGHT_JUMP_ENTRY,
    FIRST_ROW_BUTTON,
    GRID_BOTTOM,
    GRID_TOP,
    GROUP_ROWS,
    HIGHLIGHT_BUTTON,
    HOLE,
    INFO_WINDOW,
    KEY_A,
    LIST_ROWS,
    LOAD_LABELS,
    MAX_ENTRIES,
    MENU,
    MENU_BUTTON_CALL,
    MENU_CONFIRM,
    MENU_COUNT,
    MENU_CURSOR,
    MENU_FIRST_SHOWN,
    MENU_IDS,
    MENU_KEYS,
    MENU_KEYS_CALL,
    MENU_PAGE,
    MOVE_CURSOR_CORNERS,
    PAD,
    PAD_DIRECTION,
    PAD_PRESSED,
    PAD_REPEATED,
    PAGE_LIST,
    PLAY_SOUND,
    ROWS_ANY,
    ROWS_BACK,
    ROWS_FRONT,
    SLIDE_BUTTON,
    SOUND_CURSOR,
    SPECIES_OF,
    STATE_FIRST,
    STATE_MAP,
    STATE_MODE,
)

# r0 = rows filter (ROWS_BACK or ROWS_FRONT), r1 = grid row (0 top, 1 bottom) -> r0 = enemies
# placed. Puts each reachable living enemy of that row, in list order, in the next column.
ROW_ASM = f"""
    push  {{r4-r8, lr}}
    mov   r5, r0
    mov   r6, r1
    mvn   r4, #0
    mov   r7, #0
row_loop:
    mov   r0, r4
    mov   r1, r5
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    blt   row_done
    mov   r4, r0
    add   r8, r6, r7, lsl #1
    ldr   r1, row_state
    add   r1, r1, #{STATE_MAP}
    strb  r0, [r1, r8]
    ldr   r1, row_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0, #{CHAR_ID:#x}]
    bl    {SPECIES_OF:#x}
    add   r0, r0, #{CARD_ITEM_BASE:#x}
    ldr   r1, row_menu
    add   r1, r1, #{MENU_IDS:#x}
    mov   r2, r8, lsl #1
    strh  r0, [r1, r2]
    add   r7, r7, #1
    b     row_loop
row_done:
    mov   r0, r7
    pop   {{r4-r8, pc}}
row_state:
    .word ${{cave_tgt_state}}
row_battlers:
    .word {BATTLERS_PTR:#x}
row_menu:
    .word {MENU:#x}
"""

# r0 = rows the member reaches -> r0 = enemies listed. Fills the grid (ids, count, map, first
# real entry). If nobody is in reach, lists every living enemy.
FILL_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
fill_retry:
    ldr   r1, fill_state
    mvn   r0, #0
    str   r0, [r1, #{STATE_MAP}]
    str   r0, [r1, #{STATE_MAP + 4}]
    ldr   r1, fill_menu
    add   r1, r1, #{MENU_IDS:#x}
    mov   r2, #{CARD_ITEM_BASE:#x}
    orr   r2, r2, r2, lsl #16
    mov   r3, #{MAX_ENTRIES // 2}
fill_clear:
    str   r2, [r1], #4
    subs  r3, r3, #1
    bne   fill_clear
    mov   r5, #0
    cmp   r4, #{ROWS_ANY}
    bne   fill_front
    mov   r0, #{ROWS_BACK}
    mov   r1, #{GRID_TOP}
    bl    ${{cave_tgt_row}}
    mov   r5, r0
fill_front:
    mov   r0, #{ROWS_FRONT}
    mov   r1, #{GRID_BOTTOM}
    bl    ${{cave_tgt_row}}
    mov   r6, r0
    adds  r0, r5, r6
    bne   fill_out
    cmp   r4, #{ROWS_ANY}
    movne r4, #{ROWS_ANY}
    bne   fill_retry
fill_out:
    cmp   r5, r6
    movge r1, r5
    movlt r1, r6
    mov   r1, r1, lsl #1
    ldr   r2, fill_menu
    str   r1, [r2, #{MENU_COUNT:#x}]
    ldr   r2, fill_state
    cmp   r5, #0
    moveq r1, #{GRID_BOTTOM}
    movne r1, #{GRID_TOP}
    strb  r1, [r2, #{STATE_FIRST}]
    pop   {{r4-r6, pc}}
fill_state:
    .word ${{cave_tgt_state}}
fill_menu:
    .word {MENU:#x}
"""

# Replaces the three calls of BUILD_ROWS: builds the rows, then removes the hole cells' buttons
# while the enemy picker is up.
BUILT_ASM = f"""
    push  {{r4-r6, lr}}
    bl    {BUILD_ROWS:#x}
    ldr   r4, built_state
    ldrb  r0, [r4, #{STATE_MODE}]
    cmp   r0, #0
    popeq {{r4-r6, pc}}
    ldr   r5, built_menu
    ldrsh r0, [r5, #{MENU_PAGE:#x}]
    cmp   r0, #{PAGE_LIST}
    popne {{r4-r6, pc}}
    mov   r6, #0
built_loop:
    ldr   r0, [r5, #{MENU_FIRST_SHOWN:#x}]
    add   r0, r0, r6
    ldr   r1, [r5, #{MENU_COUNT:#x}]
    cmp   r0, r1
    bge   built_next
    add   r1, r4, #{STATE_MAP}
    ldrb  r0, [r1, r0]
    cmp   r0, #{HOLE:#x}
    bne   built_next
    ldr   r0, built_buttons
    ldr   r0, [r0]
    add   r1, r6, #{FIRST_ROW_BUTTON}
    mov   r2, #{BUTTON_SIZE}
    mla   r0, r1, r2, r0
    mov   r1, #0
    str   r1, [r0]
built_next:
    add   r6, r6, #1
    cmp   r6, #{LIST_ROWS}
    blt   built_loop
    pop   {{r4-r6, pc}}
built_state:
    .word ${{cave_tgt_state}}
built_menu:
    .word {MENU:#x}
built_buttons:
    .word {BUTTONS_PTR:#x}
"""


def _if_real(skip: str) -> str:
    """Asm: branch to keys_move if grid entry r0 holds an enemy, else fall through to skip."""
    return f"""
    cmp   r0, r9
    bge   {skip}
    add   r1, r4, #{STATE_MAP}
    ldrb  r1, [r1, r0]
    cmp   r1, #{HOLE:#x}
    bne   keys_move
{skip}:"""


# Replaces the menu's key handler call. While the enemy picker is up: A confirms (as vanilla, by
# flagging the cursored button), Left/Right move along the grid row skipping holes (or to the
# other row of the next column), Up/Down change row to the nearest column with an enemy.
# r4 state, r5 menu, r7 current entry, r8 columns, r9 entry count.
KEYS_ASM = f"""
    push  {{r4-r10, lr}}
    ldr   r4, keys_state
    ldr   r5, keys_menu
    ldrb  r0, [r4, #{STATE_MODE}]
    cmp   r0, #0
    beq   keys_vanilla
    ldrsh r0, [r5, #{MENU_PAGE:#x}]
    cmp   r0, #{PAGE_LIST}
    bne   keys_vanilla
    ldr   r0, [r5, #{MENU_CURSOR:#x}]
    cmn   r0, #1
    beq   keys_out
    ldr   r0, keys_pad
    bl    {PAD_PRESSED:#x}
    tst   r0, #{KEY_A}
    movne r1, #1
    strne r1, [r5, #{MENU_CONFIRM:#x}]
    ldr   r0, keys_pad
    bl    {PAD_REPEATED:#x}
    bl    {PAD_DIRECTION:#x}
    mov   r6, r0
    ldr   r7, [r5, #{MENU_FIRST_SHOWN:#x}]
    ldr   r0, [r5, #{MENU_CURSOR:#x}]
    add   r7, r7, r0
    ldr   r9, [r5, #{MENU_COUNT:#x}]
    mov   r8, r9, lsr #1
    tst   r6, #{DIR_RIGHT:#x}
    movne r1, #1
    bne   keys_horizontal
    tst   r6, #{DIR_LEFT:#x}
    mvnne r1, #0
    bne   keys_horizontal
    tst   r6, #{DIR_UP:#x}
    movne r1, #{GRID_TOP}
    bne   keys_vertical
    tst   r6, #{DIR_DOWN:#x}
    movne r1, #{GRID_BOTTOM}
    bne   keys_vertical
keys_out:
    pop   {{r4-r10, pc}}
keys_vanilla:
    bl    {MENU_KEYS:#x}
    pop   {{r4-r10, pc}}

keys_horizontal:
    mov   r6, r1
    mov   r10, r7, lsr #1
kh_loop:
    add   r10, r10, r6
    cmp   r10, #0
    blt   kh_other
    cmp   r10, r8
    bge   kh_other
    and   r0, r7, #1
    add   r0, r0, r10, lsl #1
{_if_real("kh_skip")}
    b     kh_loop
kh_other:
    mov   r10, r7, lsr #1
    add   r10, r10, r6
    cmp   r10, #0
    blt   keys_out
    cmp   r10, r8
    bge   keys_out
    and   r0, r7, #1
    eor   r0, r0, #1
    add   r0, r0, r10, lsl #1
{_if_real("kh_other_skip")}
    b     keys_out

keys_vertical:
    and   r0, r7, #1
    cmp   r0, r1
    beq   keys_out
    mov   r6, r1
    mov   r10, r7, lsr #1
kv_left:
    add   r0, r6, r10, lsl #1
{_if_real("kv_left_skip")}
    subs  r10, r10, #1
    bge   kv_left
    mov   r10, r7, lsr #1
kv_right:
    add   r10, r10, #1
    cmp   r10, r8
    bge   keys_out
    add   r0, r6, r10, lsl #1
{_if_real("kv_right_skip")}
    b     kv_right

keys_move:
    mov   r7, r0
    mov   r8, #0
    cmp   r7, #{LIST_ROWS}
    movlt r6, #0
    movge r6, #{LIST_ROWS}
    ldr   r0, [r5, #{MENU_FIRST_SHOWN:#x}]
    cmp   r0, r6
    beq   keys_same_page
    str   r6, [r5, #{MENU_FIRST_SHOWN:#x}]
    mov   r8, #1
    bl    {DOTS_UPDATE:#x}
    mov   r0, #0
    bl    {LOAD_LABELS:#x}
    bl    {DOTS_BUILD:#x}
    bl    ${{cave_tgt_built}}
    mov   r10, #{FIRST_ROW_BUTTON}
keys_slide_in:
    ldr   r0, keys_buttons
    ldr   r0, [r0]
    mov   r1, #{BUTTON_SIZE}
    mla   r0, r10, r1, r0
    mov   r1, #1
    mov   r2, #0
    bl    {SLIDE_BUTTON:#x}
    add   r10, r10, #1
    cmp   r10, #{FIRST_ROW_BUTTON + LIST_ROWS}
    blt   keys_slide_in
keys_same_page:
    sub   r0, r7, r6
    str   r0, [r5, #{MENU_CURSOR:#x}]
    mvn   r0, #0
    mov   r1, #{GROUP_ROWS:#x}
    bl    {CLEAR_GROUP_HIGHLIGHT:#x}
    ldr   r0, [r5, #{MENU_CURSOR:#x}]
    add   r0, r0, #{FIRST_ROW_BUTTON}
    bl    {HIGHLIGHT_BUTTON:#x}
    mov   r0, #1
    bl    {INFO_WINDOW:#x}
    mov   r0, #{SOUND_CURSOR}
    bl    {PLAY_SOUND:#x}
    ldr   r0, [r5, #{MENU_CURSOR:#x}]
    add   r0, r0, #{FIRST_ROW_BUTTON}
    ldr   r1, keys_buttons
    ldr   r1, [r1]
    mov   r2, #{BUTTON_SIZE}
    mla   r0, r2, r0, r1
    mov   r1, r8
    bl    {MOVE_CURSOR_CORNERS:#x}
    pop   {{r4-r10, pc}}
keys_state:
    .word ${{cave_tgt_state}}
keys_menu:
    .word {MENU:#x}
keys_pad:
    .word {PAD:#x}
keys_buttons:
    .word {BUTTONS_PTR:#x}
"""


def _hook(addr: int, old: int, asm: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, asm, note)


PICKER_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_tgt_open", OPEN_ASM, "Fight opens the enemy list"),
    CaveCode("cave_tgt_dispatch", DISPATCH_ASM, "enemy list buttons"),
    _hook(
        FIGHT_JUMP_ENTRY, 0xEA00003A, "b ${cave_tgt_open}", "Fight opens the enemy list"
    ),
    _hook(
        MENU_BUTTON_CALL, 0xEBFFEFEB, "bl ${cave_tgt_dispatch}", "enemy list buttons"
    ),
    CaveCode("cave_tgt_row", ROW_ASM, "one grid row of the enemy list"),
    CaveCode("cave_tgt_fill", FILL_ASM, "fill the enemy list"),
    CaveCode("cave_tgt_built", BUILT_ASM, "remove empty grid cells"),
    CaveCode("cave_tgt_keys", KEYS_ASM, "D-pad on the enemy grid"),
    _hook(MENU_KEYS_CALL, 0xEBFFE917, "bl ${cave_tgt_keys}", "D-pad on the enemy grid"),
    *(
        _hook(addr, old, "bl ${cave_tgt_built}", "remove empty grid cells")
        for addr, old in BUILD_ROWS_CALLS
    ),
)
