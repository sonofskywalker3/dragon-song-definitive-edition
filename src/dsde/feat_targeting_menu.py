"""The battle menu side of manual targeting: Fight opens the enemy picker, its buttons confirm or cancel.

Fight on the command page fills the picker grid (see feat_targeting_picker) and switches the menu to
the list page (page 4) with the ITCM mode byte set. With one reachable enemy it is chosen at once.
On the list page OK / A, or a second tap on the same cell, stores the enemy in the member's first
target slot and ends the member's command like vanilla Fight; back / B returns to the command page.
"""

from dsde.targeting_consts import (
    ATTACK_BLOCK,
    BACK_BUTTON,
    BATTLER_SIZE,
    BATTLERS_PTR,
    BUTTON_BACK,
    BUTTON_EPILOGUE,
    BUTTON_ID_BITS,
    BUTTON_OK,
    BUTTON_ROW,
    BUTTON_SIZE,
    BUTTONS_PTR,
    CLEAR_GROUP_HIGHLIGHT,
    COMMAND_ATTACK,
    FIRST_DOT_BUTTON,
    FIRST_ROW_BUTTON,
    GROUP_LIST,
    HIDE_CURSOR_CORNERS,
    HIGHLIGHTED_ROW,
    LIST_DOTS_AND_LABELS,
    LIST_ROWS,
    MENU,
    MENU_BUTTON,
    MENU_COMMAND,
    MENU_DESCRIPTION,
    MENU_FIRST_SHOWN,
    MENU_HIGHLIGHT,
    MENU_MEMBER,
    MENU_NEXT_PAGE,
    MENU_PAGE,
    MENU_REBUILD,
    MENU_ROW_STYLE,
    NO_DESCRIPTION,
    OK_BACK_SLIDE,
    PAGE_COMMANDS,
    PAGE_LIST,
    PLAY_SOUND,
    RESULT_MEMBER_DONE,
    RESULT_STAY,
    SLIDE_ALL_OUT,
    SLIDE_BUTTON,
    SOUND_BACK,
    SOUND_MENU,
    SOUND_REFUSE,
    STATE_FIRST,
    STATE_LAST_TAP,
    STATE_MAP,
    STATE_MODE,
    TARGETS,
)


def _slide(button: int, direction: int) -> str:
    """Asm that slides one menu button in (1) or out (0); clobbers r0..r3, ip."""
    return f"""
    ldr   r0, open_buttons
    ldr   r0, [r0]
    mov   r1, #{button}
    mov   r2, #{BUTTON_SIZE}
    mla   r0, r1, r2, r0
    mov   r1, #{direction}
    mov   r2, #0
    bl    {SLIDE_BUTTON:#x}"""


# Entered by `b` from the page 1 jump table for Fight. r5 and r7 go to the epilogue: r5 = 1 hides
# the cursor corners, r7 is the result (0 stay on this member).
OPEN_ASM = f"""
    ldr   r4, open_menu
    ldrh  r0, [r4, #{MENU_MEMBER:#x}]
    ldr   r1, open_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r8, r0, r2, r1
    mvn   r0, #0
    strh  r0, [r8, #{TARGETS:#x}]
    mov   r0, r8
    bl    ${{cave_tgt_rows}}
    bl    ${{cave_tgt_fill}}
    cmp   r0, #1
    bgt   open_list
    bne   open_vanilla
    ldr   r1, open_state
    ldrb  r0, [r1, #{STATE_FIRST}]
    add   r1, r1, #{STATE_MAP}
    ldrb  r0, [r1, r0]
    strh  r0, [r8, #{TARGETS:#x}]
open_vanilla:
    ldr   r4, open_buttons
    mov   r5, #1
    mov   r6, #{COMMAND_ATTACK}
    mov   r7, #0
    b     {ATTACK_BLOCK:#x}
open_list:
    mov   r0, #0
    str   r0, [r4, #{MENU_FIRST_SHOWN:#x}]
    strh  r0, [r4, #{MENU_ROW_STYLE:#x}]
    ldr   r1, open_state
    ldrb  r0, [r1, #{STATE_FIRST}]
    str   r0, [r4, #{MENU_HIGHLIGHT:#x}]
    mov   r0, #{NO_DESCRIPTION}
    str   r0, [r4, #{MENU_DESCRIPTION:#x}]
    mov   r0, #0
    bl    {LIST_DOTS_AND_LABELS:#x}
{_slide(FIRST_ROW_BUTTON, 0)}
{_slide(FIRST_ROW_BUTTON + 1, 0)}
{_slide(FIRST_ROW_BUTTON + 2, 0)}
{_slide(BACK_BUTTON, 0)}
    ldr   r4, open_menu
    mov   r0, #{PAGE_LIST}
    strh  r0, [r4, #{MENU_NEXT_PAGE:#x}]
    ldr   r0, [r4]
    orr   r0, r0, #{MENU_REBUILD}
    str   r0, [r4]
    mvn   r0, #0
    mov   r1, #{GROUP_LIST:#x}
    bl    {CLEAR_GROUP_HIGHLIGHT:#x}
    ldr   r1, open_state
    mov   r0, #1
    strb  r0, [r1, #{STATE_MODE}]
    mvn   r0, #0
    strb  r0, [r1, #{STATE_LAST_TAP}]
    mov   r0, #{SOUND_MENU}
    bl    {PLAY_SOUND:#x}
    ldr   r4, open_buttons
    mov   r5, #1
    mov   r7, #{RESULT_STAY}
    b     {BUTTON_EPILOGUE:#x}
open_menu:
    .word {MENU:#x}
open_battlers:
    .word {BATTLERS_PTR:#x}
open_buttons:
    .word {BUTTONS_PTR:#x}
open_state:
    .word ${{cave_tgt_state}}
"""

# Replaces `bl MENU_BUTTON`. In: r0 = button index. Out: r0 = result. While the enemy list is up,
# OK / A and a second tap on the same row confirm, back / B cancels to the command page.
DISPATCH_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
    ldr   r5, disp_state
    ldr   r6, disp_menu
    ldrb  r0, [r5, #{STATE_MODE}]
    cmp   r0, #0
    beq   disp_vanilla
    ldrsh r0, [r6, #{MENU_PAGE:#x}]
    cmp   r0, #{PAGE_LIST}
    movne r0, #0
    strbne r0, [r5, #{STATE_MODE}]
    bne   disp_vanilla
    ldr   r0, disp_buttons
    ldr   r0, [r0]
    mov   r1, #{BUTTON_SIZE}
    mla   r0, r4, r1, r0
    ldr   r0, [r0]
    mov   r0, r0, lsl #{BUTTON_ID_BITS}
    mov   r0, r0, lsr #{BUTTON_ID_BITS}
    cmp   r0, #{BUTTON_OK}
    beq   disp_confirm
    cmp   r0, #{BUTTON_BACK}
    beq   disp_cancel
    cmp   r0, #{BUTTON_ROW}
    bne   disp_vanilla
    ldr   r1, [r6, #{MENU_FIRST_SHOWN:#x}]
    add   r1, r1, r4
    ldrsb r2, [r5, #{STATE_LAST_TAP}]
    cmp   r1, r2
    beq   disp_confirm
    strb  r1, [r5, #{STATE_LAST_TAP}]
disp_vanilla:
    mov   r0, r4
    bl    {MENU_BUTTON:#x}
    pop   {{r4-r6, pc}}

disp_confirm:
    bl    {HIGHLIGHTED_ROW:#x}
    cmp   r0, #0
    blt   disp_refuse
    ldr   r1, [r6, #{MENU_FIRST_SHOWN:#x}]
    add   r0, r0, r1
    add   r1, r5, #{STATE_MAP}
    ldrb  r0, [r1, r0]
    ldrh  r1, [r6, #{MENU_MEMBER:#x}]
    ldr   r2, disp_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r1, r3, r1, r2
    strh  r0, [r1, #{TARGETS:#x}]
    mov   r0, #{COMMAND_ATTACK}
    str   r0, [r6, #{MENU_COMMAND:#x}]
    bl    {SLIDE_ALL_OUT:#x}
    mov   r0, #{PAGE_COMMANDS}
    strh  r0, [r6, #{MENU_NEXT_PAGE:#x}]
    ldr   r0, [r6]
    orr   r0, r0, #{MENU_REBUILD}
    str   r0, [r6]
    mov   r0, #0
    strb  r0, [r5, #{STATE_MODE}]
    mov   r0, #{SOUND_MENU}
    bl    {PLAY_SOUND:#x}
    bl    {HIDE_CURSOR_CORNERS:#x}
    mov   r0, #{RESULT_MEMBER_DONE}
    pop   {{r4-r6, pc}}

disp_cancel:
    mov   r0, #0
    bl    {OK_BACK_SLIDE:#x}
    mov   r4, #0
disp_cancel_loop:
    ldr   r0, disp_buttons
    ldr   r0, [r0]
    add   r1, r4, #{FIRST_DOT_BUTTON}
    mov   r2, #{BUTTON_SIZE}
    mla   r0, r1, r2, r0
    mov   r1, #0
    mov   r2, #0
    bl    {SLIDE_BUTTON:#x}
    ldr   r0, disp_buttons
    ldr   r0, [r0]
    add   r1, r4, #{FIRST_ROW_BUTTON}
    mov   r2, #{BUTTON_SIZE}
    mla   r0, r1, r2, r0
    mov   r1, #0
    mov   r2, #0
    bl    {SLIDE_BUTTON:#x}
    add   r4, r4, #1
    cmp   r4, #{LIST_ROWS}
    blt   disp_cancel_loop
    mov   r0, #{PAGE_COMMANDS}
    strh  r0, [r6, #{MENU_NEXT_PAGE:#x}]
    ldr   r0, [r6]
    orr   r0, r0, #{MENU_REBUILD}
    str   r0, [r6]
    mvn   r0, #0
    mov   r1, #{GROUP_LIST:#x}
    bl    {CLEAR_GROUP_HIGHLIGHT:#x}
    mov   r0, #0
    strb  r0, [r5, #{STATE_MODE}]
    mov   r0, #{SOUND_BACK}
    bl    {PLAY_SOUND:#x}
    bl    {HIDE_CURSOR_CORNERS:#x}
    mov   r0, #{RESULT_STAY}
    pop   {{r4-r6, pc}}

disp_refuse:
    mov   r0, #{SOUND_REFUSE}
    bl    {PLAY_SOUND:#x}
    mov   r0, #{RESULT_STAY}
    pop   {{r4-r6, pc}}
disp_state:
    .word ${{cave_tgt_state}}
disp_menu:
    .word {MENU:#x}
disp_buttons:
    .word {BUTTONS_PTR:#x}
disp_battlers:
    .word {BATTLERS_PTR:#x}
"""
