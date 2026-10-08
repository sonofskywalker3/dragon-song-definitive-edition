"""Enemies die on the hit that kills them (playtest feedback 8), on Fast and Faster.

Vanilla defers damage: each hit adds to the target's pending damage (stat record +0x60) and HP only drops
when the action ends. Then round state 0xC applies it to every battler (func_020532ac -> func_02053384) and
spawns the death sparkles (func_0202cdfc), and state 0xD holds and fades all the dead enemies together (a
screen blend; dying battlers get flag 0x1000000, semi-transparent, then 0x2000000, gone). So a combo that
kills three enemies shows them all dying together after the last hit.

Here, on Fast and Faster:
- The hit function (func_02030b44) applies an enemy target's pending damage right after the hit
  (func_02053384: HP drops; on a kill the dying flag, death animation, sound and item roll), and on a kill
  spawns that enemy's sparkles at once and starts its own death timer.
- A tick before the round machine (func_0202d22c, called every frame of a round) counts each timer down:
  KILL_HOLD frames with the halo, then KILL_FADE frames of the same blend fade state 0xD uses, then the
  enemy is gone (0x2000000). Timers of battlers that are not dying are cleared, so nothing carries over.
- State 0xC's sparkle pass (a copy of func_0202cdfc) skips enemies whose death is already running.
Party targets keep the deferred damage, and so do hits on the acting scratch copies (battlers 12 and 13: an enemy
countered during its own attack is hit as battler 12; kill-on-hit on it wrote its death timer past the 12-entry
table into this routine and crashed the 3DS, Jeff 2026-10-07). Normal stays vanilla: no timer ever starts, and the sparkle pass
behaves like the original.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

HIT_REACTION_CALL = 0x020310A0  # func_02030b44: bl func_020322a8 (hit animation); r4 = target, r5 = battler
HIT_REACTION_CALL_WORD = 0xEB000480
ROUND_CALL = (
    0x0202A67C  # func_020297d4 state 8: bl func_0202d22c (the round, every frame)
)
ROUND_CALL_WORD = 0xEB000AEA
SPARKLE_PASS_CALL = 0x0202DDF8  # round state 0xC: bl func_0202cdfc
SPARKLE_PASS_CALL_WORD = 0xEBFFFBFF
SET_ANIMATION = 0x020322A8
APPLY_DAMAGE = 0x02053384
ROUND = 0x0202D22C
SPAWN_SPARKLES = 0x0202CB9C  # func_0202cb9c(battler, kind): halo and rising sparkles
SPARKLE_KIND = 0xF
BATTLERS = 0x020B8640  # pointer to the battlers, BATTLER_SIZE bytes each, flags at +0
BATTLER_SIZE = 300
FIRST_ENEMY = 4
BATTLER_SLOTS = 12
ENEMY_FLAG = 8
DIED = -1  # func_02053384 result when the battler died
DEFEATED = 0x4000000  # dying enemy in a battle that gives EXP (func_0202cdfc spawns its sparkles)
DYING = 0xC000000  # either dying flag
SEMI_TRANSPARENT = 0x1000000
GONE = 0x2000000
KILL_HOLD = 20  # frames, as the Fast kill flash hold
KILL_FADE = 16  # frames, as the Fast kill fade
BLEND_MAIN = 0x04000050  # BLDCNT and BLDALPHA in one word (func_02002958)
BLEND_SUB_OFFSET = 0x1000
BLEND_CONTROL = 0x0A40  # alpha blend, second target BG1 and BG3 (as state 0xD)
BLEND_EVB = 0x1000  # second target weight 16
BLEND_FULL = (
    16  # first target weight once the fade is over (state 0xD ends with 0x1010)
)

KILL_ON_HIT_ASM = f"""
    push  {{r4, lr}}
    bl    {SET_ANIMATION:#x}
    ldr   r0, kill_state
    ldrb  r0, [r0]
    cmp   r0, #0
    beq   done
    ldr   r0, [r5]
    tst   r0, #{ENEMY_FLAG}
    beq   done
    cmp   r4, #{BATTLER_SLOTS}
    bge   done
    mov   r0, r4
    bl    {APPLY_DAMAGE:#x}
    cmp   r0, #{DIED}
    bne   done
    mov   r0, r4
    mov   r1, #{SPARKLE_KIND}
    bl    {SPAWN_SPARKLES:#x}
    ldr   r0, kill_timers
    mov   r1, #{KILL_HOLD + KILL_FADE}
    strb  r1, [r0, r4]
done:
    pop   {{r4, pc}}
kill_state:
    .word ${{cave_speed_state}}
kill_timers:
    .word ${{cave_kill_timers}}
"""

TICK_ASM = f"""
    push  {{r4-r7, lr}}
    ldr   r4, tick_timers
    ldr   r5, tick_battlers
    ldr   r5, [r5]
    mov   r6, #{FIRST_ENEMY}
tick:
    ldrb  r0, [r4, r6]
    cmp   r0, #0
    beq   next
    mov   r1, #{BATTLER_SIZE}
    mla   r7, r6, r1, r5
    ldr   r1, [r7]
    tst   r1, #{DYING}
    moveq r0, #0
    strbeq r0, [r4, r6]
    beq   next
    sub   r0, r0, #1
    strb  r0, [r4, r6]
    cmp   r0, #{KILL_FADE}
    orreq r1, r1, #{SEMI_TRANSPARENT}
    cmp   r0, #0
    orreq r1, r1, #{GONE}
    str   r1, [r7]
    cmp   r0, #{KILL_FADE}
    bgt   next
    cmp   r0, #0
    moveq r0, #{BLEND_FULL}
    orr   r0, r0, #{BLEND_EVB}
    ldr   r2, blend_control
    orr   r2, r2, r0, lsl #16
    ldr   r3, blend_main
    str   r2, [r3]
    add   r3, r3, #{BLEND_SUB_OFFSET}
    str   r2, [r3]
next:
    add   r6, r6, #1
    cmp   r6, #{BATTLER_SLOTS}
    blt   tick
    pop   {{r4-r7, lr}}
    b     {ROUND:#x}
tick_timers:
    .word ${{cave_kill_timers}}
tick_battlers:
    .word {BATTLERS:#x}
blend_control:
    .word {BLEND_CONTROL:#x}
blend_main:
    .word {BLEND_MAIN:#x}
"""

# func_0202cdfc: for each enemy that is dying (0x4000000) and not gone, spawn its sparkles; here also not
# when its own death is already running.
SPARKLE_PASS_ASM = f"""
    push  {{r4-r6, lr}}
    ldr   r4, pass_timers
    ldr   r5, pass_battlers
    ldr   r5, [r5]
    mov   r6, #{FIRST_ENEMY}
pass:
    mov   r1, #{BATTLER_SIZE}
    mla   r0, r6, r1, r5
    ldr   r0, [r0]
    tst   r0, #{GONE}
    bne   skip
    tst   r0, #{DEFEATED}
    beq   skip
    ldrb  r1, [r4, r6]
    cmp   r1, #0
    bne   skip
    mov   r0, r6
    mov   r1, #{SPARKLE_KIND}
    bl    {SPAWN_SPARKLES:#x}
skip:
    add   r6, r6, #1
    cmp   r6, #{BATTLER_SLOTS}
    blt   pass
    pop   {{r4-r6, pc}}
pass_timers:
    .word ${{cave_kill_timers}}
pass_battlers:
    .word {BATTLERS:#x}
"""


def _call(addr: int, word: int, cave: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, word, word, f"bl ${{{cave}}}", note)


KILL_ON_HIT = Feature(
    "kill-on-hit",
    (
        CaveCode(
            "cave_kill_timers",
            "\n".join(["    .byte 0"] * BATTLER_SLOTS),
            "death timer per battler",
        ),
        CaveCode(
            "cave_kill_on_hit", KILL_ON_HIT_ASM, "enemies die on their killing hit"
        ),
        CaveCode("cave_kill_tick", TICK_ASM, "each death holds, then fades"),
        CaveCode(
            "cave_kill_sparkles", SPARKLE_PASS_ASM, "no second sparkles after the hit"
        ),
        _call(
            HIT_REACTION_CALL,
            HIT_REACTION_CALL_WORD,
            "cave_kill_on_hit",
            "apply an enemy's damage on the hit",
        ),
        _call(ROUND_CALL, ROUND_CALL_WORD, "cave_kill_tick", "death timers tick"),
        _call(
            SPARKLE_PASS_CALL,
            SPARKLE_PASS_CALL_WORD,
            "cave_kill_sparkles",
            "end-of-action sparkles skip running deaths",
        ),
    ),
)
