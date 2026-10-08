"""Faster party attacks and no wait for the death sparkles, on Fast and Fastest (Jeff, 2026-10-08).

Jeff: Lucia's attack is slow, and there is too long a wait between one character's attack and the next.
Measured on Fast in the first temple battle (docs/re-battle-pacing.md section "Actor flow"): Lucia's one-hit
Fight took 204 frames, as long as Jian's three-hit combo, nearly all of it waiting on 6-frame animation cels
played at 1x; and after a kill the round sat in state 0xD until the death sparkles had finished rising (about
151 frames after the hit), so Jian landing home to Lucia leaving took 150 frames.

- Sprites advance by 0x100 * (1 + level) a sprite update (func_02031e08, level from 0x020B8540). For the
  acting copy (battlers 12 and 13) of a party member other than Jian, the level gets ACTOR_BONUS more (Fastest's
  sprite speed, the original game's R fast-forward); Jian already felt right and keeps his speed. The death
  sparkles (effect battlers 0x16..0x1D) get FX_BONUS more.
- State 0xD runs vanilla's hold and fade of deferred deaths first, then waited (func_0202cb44) for every
  sparkle to finish. Now it waits only while a kill-on-hit death (cave_kill_timers) is still running, so the
  sparkles finish over the next actor's camera turn. With no enemy left alive it keeps the full wait, so the
  end of a battle is unchanged.
Normal is untouched: both hooks check cave_speed_state first.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

SPRITE_LEVEL_LOAD = (
    0x02031FF0  # func_02031e08: ldr r1, [r1] (speed level); r6 = the battler
)
SPRITE_LEVEL_LOAD_WORD = 0xE5911000
SPARKLE_WAIT_CALL = (
    0x0202DF74  # round state 0xD: bl func_0202cb44 (effect battlers still busy?)
)
SPARKLE_WAIT_CALL_WORD = 0xEBFFFAF2
SPARKLE_WAIT = 0x0202CB44
BATTLERS = 0x020B8640  # pointer to the battlers, BATTLER_SIZE bytes each, flags at +0, character at +4
BATTLER_SIZE = 0x12C
ACTING_FIRST = 12 * BATTLER_SIZE  # battlers 12 and 13: the acting copies
FX_FIRST = 0x16 * BATTLER_SIZE  # effect battlers 0x16..0x1D (death sparkles)
FX_SPAN = 8 * BATTLER_SIZE
FIRST_ENEMY = 4
ENEMY_SLOTS_END = 12
ENEMY_FLAG = 8
PRESENT = 1
DYING_OR_GONE = 0x0E000000
JIAN = 0
NORMAL = 0
ACTOR_BONUS = 2
FX_BONUS = 1

ANIM_ASM = f"""
    push  {{r0, r2, lr}}
    ldr   r1, [r1]
    ldr   r0, fl_state
    ldrb  r0, [r0]
    cmp   r0, #{NORMAL}
    popeq {{r0, r2, pc}}
    ldr   r0, fl_battlers
    ldr   r0, [r0]
    add   r2, r0, #{ACTING_FIRST:#x}
    cmp   r6, r2
    addne r2, r2, #{BATTLER_SIZE:#x}
    cmpne r6, r2
    bne   fl_fx
    ldr   r2, [r6]
    tst   r2, #{ENEMY_FLAG}
    popne {{r0, r2, pc}}
    ldr   r2, [r6, #4]
    cmp   r2, #{JIAN}
    addne r1, r1, #{ACTOR_BONUS}
    pop   {{r0, r2, pc}}
fl_fx:
    add   r2, r0, #{FX_FIRST & 0xFF00:#x}
    add   r2, r2, #{FX_FIRST & 0xFF:#x}
    cmp   r6, r2
    blo   fl_out
    add   r2, r2, #{FX_SPAN:#x}
    cmp   r6, r2
    addlo r1, r1, #{FX_BONUS}
fl_out:
    pop   {{r0, r2, pc}}
fl_state:
    .word ${{cave_speed_state}}
fl_battlers:
    .word {BATTLERS:#x}
"""

WAIT_ASM = f"""
    ldr   r0, sw_state
    ldrb  r0, [r0]
    cmp   r0, #{NORMAL}
    beq   {SPARKLE_WAIT:#x}
    ldr   r0, sw_timers
    mov   r1, #{FIRST_ENEMY}
sw_timer:
    ldrb  r2, [r0, r1]
    cmp   r2, #0
    movne r0, #1
    bxne  lr
    add   r1, r1, #1
    cmp   r1, #{ENEMY_SLOTS_END}
    blt   sw_timer
    ldr   r0, sw_battlers
    ldr   r0, [r0]
    add   r0, r0, #{FIRST_ENEMY * BATTLER_SIZE:#x}
    mov   r1, #{FIRST_ENEMY}
sw_live:
    ldr   r2, [r0]
    tst   r2, #{PRESENT}
    beq   sw_next
    tst   r2, #{DYING_OR_GONE:#x}
    moveq r0, #0
    bxeq  lr
sw_next:
    add   r0, r0, #{BATTLER_SIZE:#x}
    add   r1, r1, #1
    cmp   r1, #{ENEMY_SLOTS_END}
    blt   sw_live
    b     {SPARKLE_WAIT:#x}
sw_state:
    .word ${{cave_speed_state}}
sw_timers:
    .word ${{cave_kill_timers}}
sw_battlers:
    .word {BATTLERS:#x}
"""

BATTLE_FLOW = Feature(
    "battle-flow",
    (
        CaveCode(
            "cave_flow_anim", ANIM_ASM, "party attacks and sparkles animate faster"
        ),
        AsmPatch(
            SPRITE_LEVEL_LOAD,
            SPRITE_LEVEL_LOAD + 4,
            SPRITE_LEVEL_LOAD_WORD,
            SPRITE_LEVEL_LOAD_WORD,
            "bl ${cave_flow_anim}",
            "party attacks and sparkles animate faster",
        ),
        CaveCode("cave_flow_wait", WAIT_ASM, "no wait for the death sparkles"),
        AsmPatch(
            SPARKLE_WAIT_CALL,
            SPARKLE_WAIT_CALL + 4,
            SPARKLE_WAIT_CALL_WORD,
            SPARKLE_WAIT_CALL_WORD,
            "bl ${cave_flow_wait}",
            "no wait for the death sparkles",
        ),
    ),
)
