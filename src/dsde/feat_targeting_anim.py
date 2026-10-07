"""Manual targeting: the attacker's animation follows a redirected attack.

A party Attack runs as an action script on battler 12 (the attacker's scratch copy): +0xC8 points
at 16-byte steps, +0xCC is the current step. Step flag 0x200000 aims the move at target slot 0
(+0x8C) through STEP_SETUP; a later step with a move type (0x7000) runs there and step flag 0x10
keeps the move going. Jian's attack aims at step 0, leaps at step 1 and then swings three hits
(flag 0x40) in place, so when the hit hook moves a later hit to the next enemy, the damage lands
there while Jian keeps swinging at the first one.

After each step of the attacker's script (the STEP_SETUP call that follows the step's hit), if
the target is dead or doomed by this action's queued damage and the script still has hits to
come, the target slots move to the next enemy the attacker reaches, the move target is re-aimed
from home as step 0 would have done, and an attacker already away from home hops over to the new
enemy before the next swing. A step that has a move of its own is just re-aimed. The hit hook
stays as the fallback for anything this misses.

With nobody left in reach but a living back-row enemy behind a dead front slot (a melee attacker
whose combo cleared the front row; a ranged one reaches the back row anyway), that enemy drops into
the front row at once: the game's own refill, started now instead of after the action and run
REFILL_STEPS_PER_FRAME steps a frame from the sprite render hook, and the swings aim at the slot it
drops into (Jeff, 2026-10-07). If a swing comes before the drop ends, the hit hook ends it first, so
the swing lands. Without a dead front slot to fill, the remaining swings whiff as in vanilla.
"""

from dsde.patching import AsmPatch, CaveCode
from dsde.targeting_consts import (
    ACTION,
    ACTION_ATTACK,
    BATTLE_WORK_PTR,
    BATTLER_SIZE,
    BATTLERS_PTR,
    COVER_MODE,
    FIRST_ENEMY,
    FLAGS_ENEMY,
    LAST_ENEMY,
    TARGETS,
)

STEP_SETUP = 0x0202FDF0  # (battler index): set up the current action step's move
MOVE_SETUP = 0x020303E8  # (battler, step word): start a move from the current position
STEP_SETUP_START_CALLS = (  # battle state 6: an action starts (attack; spell or item)
    (0x0202D848, 0xEB000968),
    (0x0202D87C, 0xEB00095B),
)
STEP_SETUP_NEXT_CALL = (0x0202D944, 0xEB000929)  # battle state 7: after each step
MOVE_FLAG_TEST = (0x0202DA14, 0xE2100010)  # ands r0, r0, #0x10: step keeps moving

SCRATCH = 12  # the attacker's scratch battler
SCRATCH_OFFSET = SCRATCH * BATTLER_SIZE
POS_X = 0x14
POS_Y = 0x18
POS_Z = 0x24
HOME_X = 0x50  # set from the position when a step aims (step 0)
HOME_Y = 0x54
HOME_Z = 0x58
SCRIPT = 0xC8
STEP = 0xCC
STEP_SIZE_SHIFT = 4
MOVE_FRAMES = 0xB0
MOVE_COUNT = 0xB4
TARGET_SLOTS = 8

STEP_AIM = 0x200000
STEP_MOVING = 0x10
STEP_HIT = 0x40
STEP_END = 0x80000000
STEP_STOPS = 0xA0  # 0x20 and 0x80 also end or divert the script
STEP_MOVE_TYPE = 0x7000
MOVE_HOP = 0x1000
MAX_STEPS = 32
HOP_FRAMES = 8

ANIM_STATE_ASM = """
    .word 0
"""
ANIM_HOPPING = 0  # byte: 1 while our hop to a new target may still be running
ANIM_REFILL = 1  # byte: 1 while a back-row enemy drops into the front row mid-attack

# The front-row refill (vanilla runs it in round state 0x11, after the action): battle work +0xD2 is the
# mask of columns to refill, +0xD4 the frame counter; REFILL_STEP lowers the back-row enemies of those
# columns one frame and, at REFILL_FRAMES, copies each into the front slot of its column and returns 0.
REFILL_COLUMNS = (
    0x02053ED4  # () -> mask: columns whose back enemy lives and front enemy is dead
)
REFILL_STEP = 0x02053918
REFILL_MASK = 0xD2
REFILL_TIMER = 0xD4
REFILL_LAST_FRAME = 0x3F  # the next step is the last: it copies
REFILL_STEPS_PER_FRAME = 3  # 64 frames -> about 21, between two swings of a combo
FIRST_FRONT_SLOT = 8  # front slot of column c is battler 8 + c

# A step that only aims (STEP_AIM, nothing else), for re-aiming through STEP_SETUP
AIM_STEP_ASM = f"""
    .word {STEP_AIM:#x}
    .word 0
    .word 0
    .word 0
"""

# Replaces `bl STEP_SETUP` when an action starts: forget any earlier hop
BEGIN_ASM = f"""
    ldr   r1, begin_anim
    mov   r2, #0
    strb  r2, [r1, #{ANIM_HOPPING}]
    b     {STEP_SETUP:#x}
begin_anim:
    .word ${{cave_tgt_anim_state}}
"""

# Replaces `bl STEP_SETUP` after each step of the attacker's script (r0 = SCRATCH)
FOLLOW_ASM = f"""
    push  {{r4-r9, lr}}
    bl    {STEP_SETUP:#x}
    ldr   r4, fol_battlers
    ldr   r4, [r4]
    add   r4, r4, #{SCRATCH_OFFSET:#x}
    ldr   r0, [r4, #{SCRIPT:#x}]
    ldrsh r1, [r4, #{STEP:#x}]
    add   r0, r0, r1, lsl #{STEP_SIZE_SHIFT}
    ldr   r0, [r0]
    tst   r0, #{STEP_MOVE_TYPE:#x}
    ldrne r1, fol_anim
    movne r2, #0
    strbne r2, [r1, #{ANIM_HOPPING}]
    ldr   r0, fol_work
    ldr   r0, [r0]
    ldrsh r0, [r0, #{COVER_MODE:#x}]
    cmp   r0, #0
    bne   fol_done
    ldr   r0, [r4]
    tst   r0, #{FLAGS_ENEMY}
    bne   fol_done
    ldrsh r0, [r4, #{ACTION:#x}]
    cmp   r0, #{ACTION_ATTACK}
    bne   fol_done
    ldrsh r5, [r4, #{TARGETS:#x}]
    cmp   r5, #{FIRST_ENEMY}
    blt   fol_done
    cmp   r5, #{LAST_ENEMY}
    bgt   fol_done
    ldr   r0, [r4, #{SCRIPT:#x}]
    ldrsh r1, [r4, #{STEP:#x}]
    add   r0, r0, r1, lsl #{STEP_SIZE_SHIFT}
    mov   r2, #{MAX_STEPS}
fol_scan:
    add   r0, r0, #{1 << STEP_SIZE_SHIFT}
    ldr   r1, [r0]
    tst   r1, #{STEP_HIT:#x}
    bne   fol_more
    tst   r1, #{STEP_END:#x}
    bne   fol_done
    tst   r1, #{STEP_STOPS:#x}
    bne   fol_done
    subs  r2, r2, #1
    bne   fol_scan
    b     fol_done
fol_more:
    ldr   r0, fol_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r0, r5, r1, r0
    bl    ${{cave_tgt_live}}
    cmp   r0, #0
    bgt   fol_done
    mov   r0, r4
    bl    ${{cave_tgt_rows}}
    mov   r1, r0
    mov   r0, r5
    bl    ${{cave_tgt_reach}}
    cmp   r0, #0
    bge   fol_found
    bl    {REFILL_COLUMNS:#x}
    cmp   r0, #0
    beq   fol_done
    ldr   r1, fol_work
    ldr   r1, [r1]
    strh  r0, [r1, #{REFILL_MASK:#x}]
    mov   r2, #0
    strh  r2, [r1, #{REFILL_TIMER:#x}]
    ldr   r2, fol_anim
    mov   r3, #1
    strb  r3, [r2, #{ANIM_REFILL}]
    subs  r2, r5, #{FIRST_FRONT_SLOT}
    blt   fol_column
    mov   r3, #1
    tst   r0, r3, lsl r2
    movne r0, r5
    bne   fol_found
fol_column:
    mov   r1, #{FIRST_FRONT_SLOT}
fol_bit:
    tst   r0, #1
    movne r0, r1
    bne   fol_found
    mov   r0, r0, lsr #1
    add   r1, r1, #1
    b     fol_bit
fol_found:
    cmp   r0, r5
    beq   fol_done
    mov   r6, r0
    mov   r0, #0
fol_slot:
    add   r1, r4, r0, lsl #1
    ldrsh r2, [r1, #{TARGETS:#x}]
    cmp   r2, r5
    strheq r6, [r1, #{TARGETS:#x}]
    add   r0, r0, #1
    cmp   r0, #{TARGET_SLOTS}
    blt   fol_slot
    ldr   r7, [r4, #{POS_X:#x}]
    ldr   r8, [r4, #{POS_Y:#x}]
    ldr   r9, [r4, #{POS_Z:#x}]
    ldr   r0, [r4, #{HOME_X:#x}]
    str   r0, [r4, #{POS_X:#x}]
    ldr   r0, [r4, #{HOME_Y:#x}]
    str   r0, [r4, #{POS_Y:#x}]
    ldr   r0, [r4, #{HOME_Z:#x}]
    str   r0, [r4, #{POS_Z:#x}]
    ldr   r0, [r4]
    push  {{r0}}
    ldr   r0, [r4, #{SCRIPT:#x}]
    push  {{r0}}
    ldrh  r0, [r4, #{STEP:#x}]
    push  {{r0}}
    ldr   r0, fol_aim
    str   r0, [r4, #{SCRIPT:#x}]
    mov   r0, #0
    strh  r0, [r4, #{STEP:#x}]
    mov   r0, #{SCRATCH}
    bl    {STEP_SETUP:#x}
    pop   {{r0}}
    strh  r0, [r4, #{STEP:#x}]
    pop   {{r0}}
    str   r0, [r4, #{SCRIPT:#x}]
    pop   {{r0}}
    str   r0, [r4]
    str   r7, [r4, #{POS_X:#x}]
    str   r8, [r4, #{POS_Y:#x}]
    str   r9, [r4, #{POS_Z:#x}]
    ldr   r0, [r4, #{SCRIPT:#x}]
    ldrsh r1, [r4, #{STEP:#x}]
    add   r0, r0, r1, lsl #{STEP_SIZE_SHIFT}
    ldr   r6, [r0]
    tst   r6, #{STEP_MOVE_TYPE:#x}
    beq   fol_hop
    mov   r0, r4
    mov   r1, r6
    bl    {MOVE_SETUP:#x}
    b     fol_done
fol_hop:
    ldr   r0, [r4, #{HOME_X:#x}]
    cmp   r0, r7
    bne   fol_away
    ldr   r0, [r4, #{HOME_Y:#x}]
    cmp   r0, r8
    beq   fol_done
fol_away:
    mov   r0, r4
    mov   r1, #{MOVE_HOP:#x}
    bl    {MOVE_SETUP:#x}
    mov   r0, #{HOP_FRAMES}
    str   r0, [r4, #{MOVE_FRAMES:#x}]
    ldr   r1, fol_anim
    mov   r0, #1
    strb  r0, [r1, #{ANIM_HOPPING}]
fol_done:
    pop   {{r4-r9, pc}}
fol_battlers:
    .word {BATTLERS_PTR:#x}
fol_work:
    .word {BATTLE_WORK_PTR:#x}
fol_anim:
    .word ${{cave_tgt_anim_state}}
fol_aim:
    .word ${{cave_tgt_aim_step}}
"""

# Every battle frame (called from the sprite render hook): run a mid-attack refill, several steps a frame
REFILL_TICK_ASM = f"""
    push  {{r4, r5, lr}}
    ldr   r4, tick_anim
    ldrb  r0, [r4, #{ANIM_REFILL}]
    cmp   r0, #0
    popeq {{r4, r5, pc}}
    mov   r5, #{REFILL_STEPS_PER_FRAME}
tick_step:
    ldr   r0, tick_work
    ldr   r0, [r0]
    ldrsh r0, [r0, #{REFILL_MASK:#x}]
    cmp   r0, #0
    beq   tick_done
    bl    {REFILL_STEP:#x}
    cmp   r0, #0
    beq   tick_done
    subs  r5, r5, #1
    bne   tick_step
    pop   {{r4, r5, pc}}
tick_done:
    ldr   r0, tick_work
    ldr   r0, [r0]
    mov   r1, #0
    strh  r1, [r0, #{REFILL_MASK:#x}]
    strb  r1, [r4, #{ANIM_REFILL}]
    pop   {{r4, r5, pc}}
tick_anim:
    .word ${{cave_tgt_anim_state}}
tick_work:
    .word {BATTLE_WORK_PTR:#x}
"""

# Before a hit on a dead target (the hit hook): a mid-attack refill still running ends at once, so the
# enemy that is dropping is in its front slot for this hit
REFILL_FINISH_ASM = f"""
    push  {{r4, lr}}
    ldr   r4, fin_anim
    ldrb  r0, [r4, #{ANIM_REFILL}]
    cmp   r0, #0
    popeq {{r4, pc}}
    ldr   r0, fin_work
    ldr   r0, [r0]
    ldrsh r1, [r0, #{REFILL_MASK:#x}]
    cmp   r1, #0
    beq   fin_done
    mov   r1, #{REFILL_LAST_FRAME:#x}
    strh  r1, [r0, #{REFILL_TIMER:#x}]
    bl    {REFILL_STEP:#x}
fin_done:
    ldr   r0, fin_work
    ldr   r0, [r0]
    mov   r1, #0
    strh  r1, [r0, #{REFILL_MASK:#x}]
    strb  r1, [r4, #{ANIM_REFILL}]
    pop   {{r4, pc}}
fin_anim:
    .word ${{cave_tgt_anim_state}}
fin_work:
    .word {BATTLE_WORK_PTR:#x}
"""

# Replaces `ands r0, r0, #0x10` (r0 = current step word, flags read by the next beq): the
# attacker keeps moving while the step says so, or while our hop has frames left
MOVING_ASM = f"""
    ands  r0, r0, #{STEP_MOVING:#x}
    bxne  lr
    ldr   r1, mov_anim
    ldrb  r1, [r1, #{ANIM_HOPPING}]
    cmp   r1, #0
    beq   mov_done
    ldr   r1, mov_battlers
    ldr   r1, [r1]
    add   r1, r1, #{SCRATCH_OFFSET:#x}
    ldr   r2, [r1, #{MOVE_FRAMES:#x}]
    ldr   r3, [r1, #{MOVE_COUNT:#x}]
    cmp   r3, r2
    movlt r0, #{STEP_MOVING:#x}
mov_done:
    ands  r0, r0, #{STEP_MOVING:#x}
    bx    lr
mov_anim:
    .word ${{cave_tgt_anim_state}}
mov_battlers:
    .word {BATTLERS_PTR:#x}
"""


def _hook(site: tuple[int, int], asm: str, note: str) -> AsmPatch:
    addr, old = site
    return AsmPatch(addr, addr + 4, old, old, asm, note)


ANIM_PATCHES = (
    CaveCode("cave_tgt_anim_state", ANIM_STATE_ASM, "hop to a new target running"),
    CaveCode("cave_tgt_aim_step", AIM_STEP_ASM, "action step that only aims"),
    CaveCode("cave_tgt_begin", BEGIN_ASM, "action starts: no hop"),
    CaveCode("cave_tgt_follow", FOLLOW_ASM, "animation follows a redirect"),
    CaveCode("cave_tgt_moving", MOVING_ASM, "attacker moves during a hop"),
    CaveCode("cave_tgt_refill_tick", REFILL_TICK_ASM, "back row drops mid-attack"),
    CaveCode("cave_tgt_refill_finish", REFILL_FINISH_ASM, "drop ends before the hit"),
    *(
        _hook(site, "bl ${cave_tgt_begin}", "action starts: no hop")
        for site in STEP_SETUP_START_CALLS
    ),
    _hook(
        STEP_SETUP_NEXT_CALL, "bl ${cave_tgt_follow}", "animation follows a redirect"
    ),
    _hook(MOVE_FLAG_TEST, "bl ${cave_tgt_moving}", "attacker moves during a hop"),
)
