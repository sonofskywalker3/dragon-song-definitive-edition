"""Manual targeting: the D-pad handler of the enemy grid (see feat_targeting_picker.py)."""

from dsde.targeting_consts import (
    BUTTON_SIZE,
    BUTTONS_PTR,
    CLEAR_GROUP_HIGHLIGHT,
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    DOTS_BUILD,
    DOTS_UPDATE,
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
    MENU,
    MENU_CONFIRM,
    MENU_COUNT,
    MENU_CURSOR,
    MENU_FIRST_SHOWN,
    MENU_KEYS,
    MENU_PAGE,
    MOVE_CURSOR_CORNERS,
    PAD,
    PAD_DIRECTION,
    PAD_PRESSED,
    PAD_REPEATED,
    PAGE_LIST,
    PLAY_SOUND,
    SLIDE_BUTTON,
    SOUND_CURSOR,
    STATE_MAP,
    STATE_MODE,
)


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
