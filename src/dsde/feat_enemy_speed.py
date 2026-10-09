"""Enemy actions animate faster on Fast (docs/plan-enemy-attacks.md, lever 2).

Fast is the pacing package with no game acceleration (feat_battle_speed SPEED_LEVELS), so an enemy's
animation-driven steps (wait for the sprite animation) run at 1x and dominate every enemy turn. Party actors
already get Faster's sprite level on Fast (feat_battle_flow ACTOR_BONUS); these hooks give the acting enemy
the same treatment, on Fast only (Faster already runs everything at level 2, Normal stays vanilla).

- enemy-sprite-speed: the sprite accumulator in func_02031e08 (`mla r2, r1, r4, r2` at 0x02031FF4, r1 = level
  after feat_battle_flow's hook at 0x02031FF0, r4 = step, r5 = battler index, r6 = battler) uses at least
  ENEMY_LEVEL for battlers 12 and 13 (the acting copies) whose flags mark an enemy (bit 3). Idle enemies,
  party sprites, their hurt reactions and every effect battler keep their speed. The animation advances at
  most one cel per sprite update, so cels already one frame long do not get shorter.
- enemy-spell-speed: while an enemy (battler 4..11) is the actor on Fast. A spell's visible part runs as one
  effect script per target (battle work +0x78 + 4 * i, busy flag +0x98 + 2 * i, func_02031238 /
  func_02031408) on effect battler 14 + i, and the caster's last step waits for them (flag 0x2000000,
  func_020314d8). Those effect battlers' sprites get two more sprite steps (level 2, 3x: hook on the 1x add at
  0x02031FE4), their fixed steps last half as long (frame count read at 0x020314A0), and the global effect
  script timer of func_0207d1b8 (0x0207D1EC) reads at least level 2 (2x).
"""

from dsde.patching import AsmPatch, CaveCode, Feature

SPRITE_MLA = 0x02031FF4  # func_02031e08: mla r2, r1, r4, r2
SPRITE_MLA_WORD = 0xE0222491
EFFECT_LEVEL_LOAD = 0x0207D1EC  # func_0207d1b8: ldr r2, [r2] (speed level)
EFFECT_LEVEL_LOAD_WORD = 0xE5922000
EFFECT_SPRITE_ADD = 0x02031FE4  # func_02031e08: add r2, r2, r4 (1x sprite step)
EFFECT_SPRITE_ADD_WORD = 0xE0822004
EFFECT_COUNT_ADD = (
    0x020314A0  # func_02031408: ldrsh ip, [r4, #0xc] (effect step frames)
)
EFFECT_COUNT_ADD_WORD = 0xE1D4C0FC
FIRST_EFFECT = (
    0xE  # effect battlers 14..21: one per target (work +0x78 script, +0x98 busy)
)
EFFECT_END = 0x16
EFFECT_SPRITE_SHIFT = 1  # + 2 steps: level 2 (3x)
FAST = 1
ACTING_COPY = 12
FOLLOW_UP_COPY = 13
ENEMY_FLAG = 8
ENEMY_LEVEL = 2  # Faster's sprite level: 3x, the same as party actors on Fast
EFFECT_LEVEL = 2  # 1 + 2 / 2 = effect timer at 2x
BATTLE_WORK = 0x020B8550
ACTOR = 0x32
FIRST_ENEMY = 4
ENEMY_END = 12

SPRITE_ASM = f"""
    push  {{r0, lr}}
    cmp   r5, #{ACTING_COPY}
    cmpne r5, #{FOLLOW_UP_COPY}
    bne   es_plain
    ldr   r0, [r6]
    tst   r0, #{ENEMY_FLAG}
    beq   es_plain
    ldr   r0, es_state
    ldrb  r0, [r0]
    cmp   r0, #{FAST}
    bne   es_plain
    cmp   r1, #{ENEMY_LEVEL}
    movlt r1, #{ENEMY_LEVEL}
es_plain:
    mla   r2, r1, r4, r2
    pop   {{r0, pc}}
es_state:
    .word ${{cave_speed_state}}
"""

# Clobbers r0 only: r0 = 1 on Fast while an enemy (battler 4..11) is the actor, else 0.
ENEMY_TURN_ASM = f"""
    ldr   r0, et_state
    ldrb  r0, [r0]
    cmp   r0, #{FAST}
    movne r0, #0
    bxne  lr
    ldr   r0, et_work
    ldr   r0, [r0]
    cmp   r0, #0
    bxeq  lr
    ldrsh r0, [r0, #{ACTOR:#x}]
    cmp   r0, #{FIRST_ENEMY}
    movlt r0, #0
    bxlt  lr
    cmp   r0, #{ENEMY_END}
    movge r0, #0
    movlt r0, #1
    bx    lr
et_state:
    .word ${{cave_speed_state}}
et_work:
    .word {BATTLE_WORK:#x}
"""

# Replaces `ldr r2, [r2]` (speed level for the effect script timer).
EFFECT_TIMER_ASM = f"""
    push  {{r0, lr}}
    ldr   r2, [r2]
    bl    ${{cave_enemy_turn}}
    cmp   r0, #0
    beq   ef_out
    cmp   r2, #{EFFECT_LEVEL}
    movlt r2, #{EFFECT_LEVEL}
ef_out:
    pop   {{r0, pc}}
"""

# Replaces `add r2, r2, r4` (the 1x sprite step; r5 = battler index, r0 must survive).
EFFECT_SPRITE_ASM = f"""
    push  {{r0, lr}}
    add   r2, r2, r4
    cmp   r5, #{FIRST_EFFECT}
    blt   es_out
    cmp   r5, #{EFFECT_END}
    bge   es_out
    bl    ${{cave_enemy_turn}}
    cmp   r0, #0
    addne r2, r2, r4, lsl #{EFFECT_SPRITE_SHIFT}
es_out:
    pop   {{r0, pc}}
"""

# Replaces `ldrsh ip, [r4, #0xc]` (an effect step's frame count, compared with the +0xB8 counter): half,
# rounded up. Not the counter's add: lr holds work +0xB8 there, and a bl would lose it.
EFFECT_COUNT_ASM = """
    push  {r0, lr}
    ldrsh ip, [r4, #0xc]
    bl    ${cave_enemy_turn}
    cmp   r0, #0
    addne ip, ip, #1
    asrne ip, ip, #1
    pop   {r0, pc}
"""

ENEMY_SPRITE_SPEED = Feature(
    "enemy-sprite-speed",
    (
        CaveCode(
            "cave_enemy_sprite", SPRITE_ASM, "acting enemy animates at 3x on Fast"
        ),
        AsmPatch(
            SPRITE_MLA,
            SPRITE_MLA + 4,
            SPRITE_MLA_WORD,
            SPRITE_MLA_WORD,
            "bl ${cave_enemy_sprite}",
            "acting enemy animates faster on Fast",
        ),
    ),
)

ENEMY_SPELL_SPEED = Feature(
    "enemy-spell-speed",
    (
        CaveCode("cave_enemy_turn", ENEMY_TURN_ASM, "enemy acting on Fast?"),
        CaveCode("cave_enemy_fx_timer", EFFECT_TIMER_ASM, "effect timer 2x"),
        CaveCode("cave_enemy_fx_sprite", EFFECT_SPRITE_ASM, "effect sprites 3x"),
        CaveCode("cave_enemy_fx_count", EFFECT_COUNT_ASM, "effect steps 2x"),
        AsmPatch(
            EFFECT_LEVEL_LOAD,
            EFFECT_LEVEL_LOAD + 4,
            EFFECT_LEVEL_LOAD_WORD,
            EFFECT_LEVEL_LOAD_WORD,
            "bl ${cave_enemy_fx_timer}",
            "enemy spell effect timer faster on Fast",
        ),
        AsmPatch(
            EFFECT_SPRITE_ADD,
            EFFECT_SPRITE_ADD + 4,
            EFFECT_SPRITE_ADD_WORD,
            EFFECT_SPRITE_ADD_WORD,
            "bl ${cave_enemy_fx_sprite}",
            "enemy spell effect sprites faster on Fast",
        ),
        AsmPatch(
            EFFECT_COUNT_ADD,
            EFFECT_COUNT_ADD + 4,
            EFFECT_COUNT_ADD_WORD,
            EFFECT_COUNT_ADD_WORD,
            "bl ${cave_enemy_fx_count}",
            "enemy spell effect steps faster on Fast",
        ),
    ),
)
