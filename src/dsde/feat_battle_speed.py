"""Battle speed setting: tap R to cycle Normal, Fast and Fastest (design 7).

Like the 2025 Lunar remasters, a three-step battle speed the player changes at any time in battle, but
on the R trigger alone: L+R held is the run chord (hold-lr-to-run), so R cycles the speed when it is
released after a press during which L was never held. Pressing L and R together for a run never
changes the speed.

The game already scales battle animation by a speed level at 0x020B8540 (sprites run at 1 + level,
spell effects at 1 + level / 2; docs/re-curse-battle-speed.md 2.1), which func_020297d4 zeroes every
frame before its (now disabled) L/R hold fast-forward. That store becomes a call that writes the level
for the current setting instead: Normal is the original game, Fast is the pacing package of
feat_battle_pace.py with no acceleration, Fastest is the package plus the game's old R speed (sprites 3x,
spell effects 2x). The setting lives in ITCM, starts at Fast and lasts until power-off.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

SPEED_LEVEL_STORE = (
    0x02029804  # func_020297d4: str r2, [r1] (r1 = 0x020B8540, r2 = 0, r4 = keys held)
)
SPEED_LEVEL_STORE_WORD = 0xE5812000
SPEED_LEVEL = 0x020B8540
PLAY_SOUND = 0x020284D8
SOUND_MENU = 1
KEY_R = 0x100
KEY_L = 0x200
SPEED_LEVELS = (
    0,
    0,
    2,
)  # game acceleration for Normal, Fast (battle-pace only), Fastest
DEFAULT_SETTING = 1  # Fast

# Bytes: +0 setting (index into SPEED_LEVELS), +1 armed (R pressed without L), +2 R held last frame
STATE_SETTING = 0
STATE_ARMED = 1
STATE_R_BEFORE = 2
STATE_ASM = f"""
    .byte {DEFAULT_SETTING}, 0, 0, 0
"""
LEVELS_ASM = "    .byte " + ", ".join(str(level) for level in SPEED_LEVELS) + ", 0"

# Replaces `str r2, [r1]` (the per-frame speed level reset). In: r4 = keys held. Keeps r4..r11.
SPEED_ASM = f"""
    push  {{r4, lr}}
    ldr   r2, spd_state
    tst   r4, #{KEY_R:#x}
    beq   spd_r_up
    tst   r4, #{KEY_L:#x}
    movne r3, #0
    strbne r3, [r2, #{STATE_ARMED}]
    bne   spd_apply
    ldrb  r3, [r2, #{STATE_R_BEFORE}]
    cmp   r3, #0
    moveq r3, #1
    strbeq r3, [r2, #{STATE_ARMED}]
    b     spd_apply
spd_r_up:
    ldrb  r3, [r2, #{STATE_R_BEFORE}]
    cmp   r3, #0
    beq   spd_apply
    ldrb  r3, [r2, #{STATE_ARMED}]
    cmp   r3, #0
    beq   spd_apply
    mov   r3, #0
    strb  r3, [r2, #{STATE_ARMED}]
    ldrb  r3, [r2, #{STATE_SETTING}]
    add   r3, r3, #1
    cmp   r3, #{len(SPEED_LEVELS)}
    movge r3, #0
    strb  r3, [r2, #{STATE_SETTING}]
    mov   r0, #{SOUND_MENU}
    bl    {PLAY_SOUND:#x}
spd_apply:
    ldr   r2, spd_state
    tst   r4, #{KEY_R:#x}
    movne r3, #1
    moveq r3, #0
    strb  r3, [r2, #{STATE_R_BEFORE}]
    ldrb  r3, [r2, #{STATE_SETTING}]
    ldr   r2, spd_levels
    ldrb  r3, [r2, r3]
    ldr   r1, spd_level
    str   r3, [r1]
    pop   {{r4, pc}}
spd_state:
    .word ${{cave_speed_state}}
spd_levels:
    .word ${{cave_speed_levels}}
spd_level:
    .word {SPEED_LEVEL:#x}
"""

BATTLE_SPEED = Feature(
    "battle-speed",
    (
        CaveCode("cave_speed_state", STATE_ASM, "battle speed setting"),
        CaveCode("cave_speed_levels", LEVELS_ASM, "speed level per setting"),
        CaveCode("cave_speed", SPEED_ASM, "R cycles the battle speed"),
        AsmPatch(
            SPEED_LEVEL_STORE,
            SPEED_LEVEL_STORE + 4,
            SPEED_LEVEL_STORE_WORD,
            SPEED_LEVEL_STORE_WORD,
            "bl ${cave_speed}",
            "speed level from the battle speed setting",
        ),
    ),
)
