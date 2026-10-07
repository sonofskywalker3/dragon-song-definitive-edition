"""Back-row enemies drop into an empty front slot during an action, not only after it.

Vanilla refills the front row in round state 0x11, after the action: REFILL_COLUMNS (func_02053ed4) gives
the mask of columns to refill by the battle's own rule (a column whose back enemy lives and front enemy is
dead; in the Caucus fight, battle 7, only once the whole front row is dead), battle work +0xD2 holds it and
+0xD4 counts the frames, and REFILL_STEP (func_02053918) lowers the back enemies one frame at a time and
at the end copies each into the front slot of its column (battler and stat record, turn order fixed up).

Jeff (2026-10-07): with kill-on-hit (Fast and Fastest) a front enemy dies mid-action, and the enemy behind
it should drop in as soon as the slot is empty, as the battle calls for. Every frame of an action (round
state 7) the tick asks REFILL_COLUMNS, leaves out the columns that were already due when the action started
(a front slot empty from the start of the battle or from an earlier action: vanilla refills those after
the action, round state 0x10 / 0x11, and so do we) and columns whose front enemy is still fading out (dying
but not yet gone), and starts the refill on the rest; it then runs REFILL_STEPS_PER_FRAME steps a frame. The
lunge follow-up (feat_targeting_anim.py) also starts one at once, fading or not, when a melee attacker has
nobody left in reach, and the hit hook ends a running drop before a hit on a dead target, so a swing at the
slot lands on the enemy that dropped in. A drop still running when the round reaches vanilla's own refill
(states 0x10, 0x11) ends at once, so vanilla finds nothing left to do. On Normal deaths resolve after the
action and vanilla's refill does everything.

The tick is called from the sprite render hook (feat_targeting_brackets.py), which runs every battle frame.
"""

from dsde.feat_battle_kill import BATTLER_SIZE, DYING, GONE
from dsde.patching import CaveCode
from dsde.targeting_consts import BATTLE_WORK_PTR, BATTLERS_PTR

REFILL_COLUMNS = (
    0x02053ED4  # () -> mask of columns to refill now, by the battle's own rule
)
REFILL_STEP = (
    0x02053918  # () -> 0 once the refill has copied (then the mask must be cleared)
)
REFILL_MASK = 0xD2
REFILL_TIMER = 0xD4
REFILL_LAST_FRAME = 0x3F  # the next step is the last: it copies
REFILL_STEPS_PER_FRAME = 3  # 64 frames -> about 21, between two swings of a combo
FIRST_FRONT_SLOT = 8  # front slot of column c is battler 8 + c
COLUMNS = 4
ROUND_STATE = 0x2E  # s16 in battle work
ROUND_ACTION = 7  # the steps of an action run
ROUND_REFILL_CHECK = 0x10  # vanilla decides its refill
ROUND_REFILL = 0x11  # vanilla runs it

DROP_STATE_ASM = """
    .word 0
"""
DROPPING = 0  # byte: 1 while our refill runs
LAST_ROUND = 1  # byte: round state seen last frame
START_MASK = (
    2  # byte: REFILL_COLUMNS when the action started (those wait for vanilla's refill)
)

# Every battle frame: run a refill of ours, or start one during an action
DROP_TICK_ASM = f"""
    push  {{r4-r7, lr}}
    ldr   r4, tick_state
    ldr   r6, tick_work
    ldr   r6, [r6]
    ldrsh r7, [r6, #{ROUND_STATE:#x}]
    ldrb  r0, [r4, #{LAST_ROUND}]
    strb  r7, [r4, #{LAST_ROUND}]
    cmp   r7, #{ROUND_ACTION}
    bne   tick_check
    cmp   r0, #{ROUND_ACTION}
    beq   tick_check
    bl    {REFILL_COLUMNS:#x}
    strb  r0, [r4, #{START_MASK}]
tick_check:
    ldrb  r0, [r4, #{DROPPING}]
    cmp   r0, #0
    beq   tick_poll
    cmp   r7, #{ROUND_REFILL_CHECK:#x}
    cmpne r7, #{ROUND_REFILL:#x}
    bne   tick_run
    bl    ${{cave_tgt_drop_finish}}
    pop   {{r4-r7, pc}}
tick_run:
    mov   r5, #{REFILL_STEPS_PER_FRAME}
tick_step:
    ldrsh r0, [r6, #{REFILL_MASK:#x}]
    cmp   r0, #0
    beq   tick_done
    bl    {REFILL_STEP:#x}
    cmp   r0, #0
    beq   tick_done
    subs  r5, r5, #1
    bne   tick_step
    pop   {{r4-r7, pc}}
tick_done:
    mov   r0, #0
    strh  r0, [r6, #{REFILL_MASK:#x}]
    strb  r0, [r4, #{DROPPING}]
    pop   {{r4-r7, pc}}
tick_poll:
    cmp   r7, #{ROUND_ACTION}
    popne {{r4-r7, pc}}
    bl    {REFILL_COLUMNS:#x}
    ldrb  r1, [r4, #{START_MASK}]
    bics  r5, r0, r1
    popeq {{r4-r7, pc}}
    ldr   r1, tick_battlers
    ldr   r1, [r1]
    add   r1, r1, #{FIRST_FRONT_SLOT * BATTLER_SIZE:#x}
    mov   r2, #0
tick_column:
    mov   r3, #1
    tst   r5, r3, lsl r2
    beq   tick_next
    ldr   r0, [r1]
    tst   r0, #{DYING:#x}
    beq   tick_next
    tst   r0, #{GONE:#x}
    biceq r5, r5, r3, lsl r2
tick_next:
    add   r1, r1, #{BATTLER_SIZE:#x}
    add   r2, r2, #1
    cmp   r2, #{COLUMNS}
    blt   tick_column
    cmp   r5, #0
    popeq {{r4-r7, pc}}
    strh  r5, [r6, #{REFILL_MASK:#x}]
    mov   r0, #0
    strh  r0, [r6, #{REFILL_TIMER:#x}]
    mov   r0, #1
    strb  r0, [r4, #{DROPPING}]
    pop   {{r4-r7, pc}}
tick_state:
    .word ${{cave_tgt_drop_state}}
tick_work:
    .word {BATTLE_WORK_PTR:#x}
tick_battlers:
    .word {BATTLERS_PTR:#x}
"""

# End a running refill of ours now (it copies at once). Keeps r4-r11.
DROP_FINISH_ASM = f"""
    push  {{r4, lr}}
    ldr   r4, fin_state
    ldrb  r0, [r4, #{DROPPING}]
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
    strb  r1, [r4, #{DROPPING}]
    pop   {{r4, pc}}
fin_state:
    .word ${{cave_tgt_drop_state}}
fin_work:
    .word {BATTLE_WORK_PTR:#x}
"""

# Start a refill of ours now on the columns REFILL_COLUMNS gives (r0 = that mask, not 0). Keeps r4-r11.
DROP_START_ASM = f"""
    ldr   r1, start_work
    ldr   r1, [r1]
    strh  r0, [r1, #{REFILL_MASK:#x}]
    mov   r2, #0
    strh  r2, [r1, #{REFILL_TIMER:#x}]
    ldr   r1, start_state
    mov   r2, #1
    strb  r2, [r1, #{DROPPING}]
    bx    lr
start_state:
    .word ${{cave_tgt_drop_state}}
start_work:
    .word {BATTLE_WORK_PTR:#x}
"""

DROP_PATCHES = (
    CaveCode("cave_tgt_drop_state", DROP_STATE_ASM, "back row dropping mid-action"),
    CaveCode("cave_tgt_drop_finish", DROP_FINISH_ASM, "drop ends now"),
    CaveCode("cave_tgt_drop_start", DROP_START_ASM, "drop starts now"),
    CaveCode("cave_tgt_drop_tick", DROP_TICK_ASM, "back row drops as slots empty"),
)
