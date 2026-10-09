"""ARM code of the party chat feature (feat_party_chat): entry pick, script start, icon bounce.

Addresses are from docs/re-party-chat.md and docs/re-field-hud.md section 2.
"""

START_SCRIPT = 0x02041988  # func_02041988: script pc = start of the loaded file
HINT_START_FIELD = 0x02020188  # field state 0x20 (Y or the figures): bl func_02041988
HINT_START_FIELD_WORD = 0xEB0085FE
HINT_START_MENU = 0x0205F368  # System menu: bl func_02041988
HINT_START_MENU_WORD = 0xEBFF8986
PULSE_CALL = 0x02022108  # every field frame: bl func_0206f7c4 (HUD pulse)
PULSE_CALL_WORD = 0xEB0135AD
PULSE = 0x0206F7C4
SET_AFFINE = 0x0201ACE4  # func_0201ace4(oam, matrix, scale, rotation, flag)
SUB_OAM = 0x020AFF50  # pointer to the bottom screen's OAM manager
SINE_TABLE = 0x02089158  # s16 sin, s16 cos per 1/4096 turn
MAIN_CONTEXT = (
    0x020B4640  # pointer to the main script context (story flags at its start)
)
FIELD_MAP = 0x020B6BE4  # s16 current map id
FIGURES = 0x020B7F28 + 0xC + 6 * 0x30  # HUD button 6: +0 type, +2 OAM flags, +0xE cell
FIGURES_TYPE = 2
FIGURES_CELL = 14
STILL_FLAGS = 0x8000  # as func_0206f3a4 gives buttons without a matrix
BOUNCE_FLAGS = 0xA026  # 0xA025 is vanilla's (affine, matrix 5); matrix 6 is ours
BOUNCE_MATRIX = 6
PHASE_STEP = 0x800  # vanilla's pulse speed

SELECT_ASM = """
    push  {r4-r11, lr}
    mov   r4, r0
    mov   r5, r1
    ldr   r6, chat_table
    mov   r7, #0
    mov   r8, #0
entry_loop:
    ldrh  r0, [r6]
    cmp   r0, #0
    beq   select_done
    add   r9, r6, r0, lsl #1
    ldrh  r1, [r6, #2]
    cmp   r5, r1
    blo   entry_next
    ldrh  r1, [r6, #4]
    cmp   r5, r1
    bhi   entry_next
    ldrh  r1, [r6, #10]
    mov   r10, #0
    cmp   r1, #0
    movne r10, #1
    movne r10, r10, lsl r1
    tst   r8, r10
    bne   entry_next
    add   r3, r6, #12
clause_loop:
    cmp   r3, r9
    bhs   entry_match
    ldrh  r0, [r3], #2
    mov   r11, r0, lsr #12
    and   r1, r0, #0xFF
    mov   r2, #0
    mov   lr, r1
flag_loop:
    ldrh  r0, [r3], #2
    mov   ip, r0, lsr #5
    ldr   ip, [r4, ip, lsl #2]
    and   r0, r0, #31
    mov   ip, ip, lsr r0
    tst   ip, #1
    addne r2, r2, #1
    subs  lr, lr, #1
    bne   flag_loop
    cmp   r11, #1
    beq   kind_on
    cmp   r11, #2
    beq   kind_off
    cmp   r11, #3
    beq   kind_any
    cmp   r2, r1
    blo   clause_loop
    b     entry_next
kind_on:
    cmp   r2, r1
    beq   clause_loop
    b     entry_next
kind_off:
    cmp   r2, #0
    beq   clause_loop
    b     entry_next
kind_any:
    cmp   r2, #0
    bne   clause_loop
    b     entry_next
entry_match:
    orr   r8, r8, r10
    ldrh  r0, [r6, #6]
    mov   ip, r0, lsr #5
    ldr   ip, [r4, ip, lsl #2]
    and   r0, r0, #31
    mov   ip, ip, lsr r0
    tst   ip, #1
    moveq r0, r6
    beq   select_ret
    cmp   r7, #0
    moveq r7, r6
entry_next:
    mov   r6, r9
    b     entry_loop
select_done:
    mov   r0, r7
select_ret:
    pop   {r4-r11, pc}
chat_table:
    .word ${cave_chat_table}
"""

START_ASM = f"""
    push  {{r4, lr}}
    mov   r4, r0
    bl    {START_SCRIPT:#x}
    ldr   r1, start_map
    ldrh  r1, [r1]
    add   r0, r4, #0x200
    strh  r1, [r0, #6]
    mov   r0, r4
    bl    ${{cave_chat_select}}
    cmp   r0, #0
    popeq {{r4, pc}}
    ldrh  r1, [r0, #8]
    ldr   r2, [r4, #0xDC]
    add   r2, r2, r1, lsl #2
    str   r2, [r4, #0xE0]
    ldrh  r1, [r0, #6]
    mov   r2, r1, lsr #5
    and   r1, r1, #31
    mov   r3, #1
    mov   r3, r3, lsl r1
    ldr   r1, [r4, r2, lsl #2]
    orr   r1, r1, r3
    str   r1, [r4, r2, lsl #2]
    ldr   r0, start_main
    ldr   r0, [r0]
    cmp   r0, #0
    ldrne r1, [r0, r2, lsl #2]
    orrne r1, r1, r3
    strne r1, [r0, r2, lsl #2]
    pop   {{r4, pc}}
start_map:
    .word {FIELD_MAP:#x}
start_main:
    .word {MAIN_CONTEXT:#x}
"""

FRAME_ASM = f"""
    push  {{r4, lr}}
    bl    {PULSE:#x}
    ldr   r4, frame_figures
    ldrb  r0, [r4]
    cmp   r0, #{FIGURES_TYPE}
    popne {{r4, pc}}
    ldrb  r0, [r4, #0xE]
    cmp   r0, #{FIGURES_CELL}
    popne {{r4, pc}}
    ldr   r0, frame_main
    ldr   r0, [r0]
    cmp   r0, #0
    beq   frame_still
    ldr   r1, frame_map
    ldrh  r1, [r1]
    bl    ${{cave_chat_select}}
    cmp   r0, #0
    beq   frame_still
    ldrh  r1, [r0, #6]
    ldr   r0, frame_main
    ldr   r0, [r0]
    mov   r2, r1, lsr #5
    ldr   r2, [r0, r2, lsl #2]
    and   r1, r1, #31
    mov   r2, r2, lsr r1
    tst   r2, #1
    bne   frame_still
    ldr   r2, frame_phase
    ldrh  r0, [r2]
    add   r0, r0, #{PHASE_STEP:#x}
    strh  r0, [r2]
    mov   r0, r0, lsl #16
    mov   r0, r0, lsr #20
    ldr   r1, frame_sine
    add   r1, r1, r0, lsl #2
    ldrsh r1, [r1]
    mov   r2, r1, asr #3
    add   r2, r2, #0x1000
    mov   r2, r2, lsl #16
    mov   r2, r2, lsr #16
    ldr   r0, frame_oam
    ldr   r0, [r0]
    mov   r1, #{BOUNCE_MATRIX}
    mov   r3, #0
    sub   sp, sp, #8
    str   r3, [sp]
    bl    {SET_AFFINE:#x}
    add   sp, sp, #8
    ldr   r0, frame_bounce
    strh  r0, [r4, #2]
    pop   {{r4, pc}}
frame_still:
    mov   r0, #{STILL_FLAGS:#x}
    strh  r0, [r4, #2]
    ldr   r2, frame_phase
    mov   r0, #0
    strh  r0, [r2]
    pop   {{r4, pc}}
frame_figures:
    .word {FIGURES:#x}
frame_main:
    .word {MAIN_CONTEXT:#x}
frame_map:
    .word {FIELD_MAP:#x}
frame_sine:
    .word {SINE_TABLE:#x}
frame_oam:
    .word {SUB_OAM:#x}
frame_bounce:
    .word {BOUNCE_FLAGS:#x}
frame_phase:
    .word ${{cave_chat_phase}}
"""
