"""Manual Attack targeting (design section 4).

Plan, register notes and evidence: docs/plan-targeting.md. When the player picks Fight for a party
member, the battle menu's list page (page 4, normally the item list) is reused as an enemy list:
a mode byte in ITCM tells our button hook that page 4 is the enemy picker. The list holds only the
enemies the member can reach with the game's own rule (character 3, or anyone wearing equipment
effect 0x0D, reaches every enemy; everyone else reaches the front row, battlers 8..11). With one
reachable enemy there is no list. The chosen battler index (4..11) goes in the member's first
target slot (+0x8C), which the game clears every round and never sets to an enemy for a party
member itself.

At execution the auto rule's target pick is replaced when a manual target is present. A dead
target moves on to the next living reachable enemy in list order (front row first, then left to
right on screen), wrapping to the top. The same redirect replaces the "target dead, the hit whiffs"
test for every party Attack hit, so later hits of a multi-hit attack move on as well.
"""

from dsde.feat_targeting_picker import PICKER_PATCHES
from dsde.patching import AsmPatch, CaveCode, Feature
from dsde.targeting_consts import (
    ACTION,
    ACTION_ATTACK,
    AUTO_TARGET,
    AUTO_TARGET_CALL,
    BATTLE_WORK_PTR,
    BATTLER_ALIVE,
    BATTLER_SIZE,
    BATTLERS_PTR,
    CHAR_ID,
    CHAR_REACHES_ALL,
    COVER_MODE,
    EQUIP_REACHES_ALL,
    FIRST_ENEMY,
    FIRST_FRONT,
    FLAGS_ENEMY,
    HAS_EQUIP_EFFECT,
    HIT_ALIVE_CALL,
    LAST_ENEMY,
    POSITION_X,
    ROWS_ANY,
    ROWS_BACK,
    ROWS_FRONT,
    STATE_MANUAL,
    TARGETS,
)

STATE_ASM = """
    .word 0
    .word 0
    .word 0
"""

# r0 = battler -> r0 = rows it reaches (ROWS_ANY or ROWS_FRONT). Same rule as 0x02051BD8.
ROWS_ASM = f"""
    push  {{r4, lr}}
    ldr   r1, [r0, #{CHAR_ID:#x}]
    cmp   r1, #{CHAR_REACHES_ALL}
    moveq r0, #{ROWS_ANY}
    popeq {{r4, pc}}
    mov   r0, #{EQUIP_REACHES_ALL:#x}
    bl    {HAS_EQUIP_EFFECT:#x}
    cmp   r0, #1
    moveq r0, #{ROWS_ANY}
    movne r0, #{ROWS_FRONT}
    pop   {{r4, pc}}
"""

# r0 = battler index, r1 = rows -> r0 = 1 if that enemy is alive and in reach
OK_ASM = f"""
    push  {{r4, lr}}
    cmp   r1, #{ROWS_FRONT}
    bne   ok_not_front
    cmp   r0, #{FIRST_FRONT}
    blt   ok_no
ok_not_front:
    cmp   r1, #{ROWS_BACK}
    bne   ok_alive
    cmp   r0, #{FIRST_FRONT}
    bge   ok_no
ok_alive:
    ldr   r2, ok_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r0, r3, r0, r2
    bl    {BATTLER_ALIVE:#x}
    cmp   r0, #0
    movgt r0, #1
    popgt {{r4, pc}}
ok_no:
    mov   r0, #0
    pop   {{r4, pc}}
ok_battlers:
    .word {BATTLERS_PTR:#x}
"""

# r0 = a, r1 = b (battler indexes) -> r0 = 1 if a comes before b in the list.
# Front row first, then screen position, then index. Uses r0..r3, ip only.
LESS_ASM = f"""
    cmp   r0, #{FIRST_FRONT}
    movge r2, #0
    movlt r2, #1
    cmp   r1, #{FIRST_FRONT}
    movge r3, #0
    movlt r3, #1
    cmp   r2, r3
    movlt r0, #1
    movgt r0, #0
    bxne  lr
    ldr   ip, less_battlers
    ldr   ip, [ip]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r3, r0, r2, ip
    mla   r2, r1, r2, ip
    ldr   r3, [r3, #{POSITION_X:#x}]
    ldr   r2, [r2, #{POSITION_X:#x}]
    cmp   r3, r2
    movlt r0, #1
    movgt r0, #0
    bxne  lr
    cmp   r0, r1
    movlt r0, #1
    movge r0, #0
    bx    lr
less_battlers:
    .word {BATTLERS_PTR:#x}
"""

# r0 = prev (-1 none), r1 = rows -> r0 = first reachable living enemy after prev in list order, -1
AFTER_ASM = f"""
    push  {{r4-r8, lr}}
    mov   r4, r0
    mov   r5, r1
    mvn   r6, #0
    mov   r7, #{FIRST_ENEMY}
after_loop:
    mov   r0, r7
    mov   r1, r5
    bl    ${{cave_tgt_ok}}
    cmp   r0, #0
    beq   after_next
    cmp   r4, #0
    blt   after_best
    mov   r0, r4
    mov   r1, r7
    bl    ${{cave_tgt_less}}
    cmp   r0, #0
    beq   after_next
after_best:
    cmp   r6, #0
    blt   after_take
    mov   r0, r7
    mov   r1, r6
    bl    ${{cave_tgt_less}}
    cmp   r0, #0
    beq   after_next
after_take:
    mov   r6, r7
after_next:
    add   r7, r7, #1
    cmp   r7, #{LAST_ENEMY}
    ble   after_loop
    mov   r0, r6
    pop   {{r4-r8, pc}}
"""

# r0 = start battler, r1 = rows -> r0 = start if it is alive and in reach, else the next one in
# list order (wrapping to the top), else -1. Falls back to every row when nobody is in reach.
NEXT_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
    mov   r5, r1
next_retry:
    mov   r0, r4
    mov   r1, r5
    bl    ${{cave_tgt_ok}}
    cmp   r0, #0
    movne r0, r4
    popne {{r4-r6, pc}}
    mov   r0, r4
    mov   r1, r5
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    popge {{r4-r6, pc}}
    mvn   r0, #0
    mov   r1, r5
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    popge {{r4-r6, pc}}
    cmp   r5, #{ROWS_ANY}
    movne r5, #{ROWS_ANY}
    bne   next_retry
    mvn   r0, #0
    pop   {{r4-r6, pc}}
"""

# Replaces `bl AUTO_TARGET` in the party Attack loop. In: r0 = mode, r1 = rows, r4 = actor,
# r7 = hit index. Out: r0 = target. Hit 0 with a manual target (4..11 in +0x8C) uses it; later hits
# of that attack reuse hit 0's resolved target. Everything else takes the game's auto rule.
PICK_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r5, r0
    mov   r6, r1
    ldr   r2, pick_state
    ldr   r3, [r4]
    tst   r3, #{FLAGS_ENEMY}
    bne   pick_auto
    cmp   r7, #0
    bne   pick_later
    mov   r3, #0
    strb  r3, [r2, #{STATE_MANUAL}]
    ldrsh r0, [r4, #{TARGETS:#x}]
    cmp   r0, #{FIRST_ENEMY}
    blt   pick_auto
    cmp   r0, #{LAST_ENEMY}
    bgt   pick_auto
    mov   r3, #1
    strb  r3, [r2, #{STATE_MANUAL}]
    b     pick_resolve
pick_later:
    ldrb  r3, [r2, #{STATE_MANUAL}]
    cmp   r3, #0
    beq   pick_auto
    ldrsh r0, [r4, #{TARGETS:#x}]
pick_resolve:
    mov   r1, r6
    bl    ${{cave_tgt_next}}
    cmp   r0, #0
    popge {{r4-r6, pc}}
pick_auto:
    mov   r0, r5
    mov   r1, r6
    bl    {AUTO_TARGET:#x}
    pop   {{r4-r6, pc}}
pick_state:
    .word ${{cave_tgt_state}}
"""

# Replaces `bl BATTLER_ALIVE` before a hit in func_02030b44. In: r0 = r5 = target battler,
# r4 = target index, r6 = attacker (scratch copy), fp = hit flags; the caller keeps the target in
# r4, r5, [sp + 4] and [sp + 0x1C] (here + 8 for our push). A party Attack hit on a dead enemy moves
# to the next living enemy in list order instead of whiffing.
CALLER_TARGET_INDEX = 0x04 + 8
CALLER_TARGET_OFFSET = 0x1C + 8
HIT_SLOT_SHIFT = 12
HIT_SLOT_MASK = 7
HIT_ASM = f"""
    push  {{r1, lr}}
    bl    {BATTLER_ALIVE:#x}
    cmp   r0, #0
    bgt   hit_done
    ldr   r1, hit_work
    ldr   r1, [r1]
    ldrsh r1, [r1, #{COVER_MODE:#x}]
    cmp   r1, #0
    bne   hit_done
    ldr   r1, [r6]
    tst   r1, #{FLAGS_ENEMY}
    bne   hit_done
    ldrsh r1, [r6, #{ACTION:#x}]
    cmp   r1, #{ACTION_ATTACK}
    bne   hit_done
    cmp   r4, #{FIRST_ENEMY}
    blt   hit_done
    cmp   r4, #{LAST_ENEMY}
    bgt   hit_done
    str   r0, [sp]
    mov   r0, r6
    bl    ${{cave_tgt_rows}}
    mov   r1, r0
    mov   r0, r4
    bl    ${{cave_tgt_next}}
    cmp   r0, #0
    ldrlt r0, [sp]
    blt   hit_done
    mov   r4, r0
    ldr   r1, hit_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mul   r3, r0, r2
    add   r5, r1, r3
    str   r4, [sp, #{CALLER_TARGET_INDEX:#x}]
    str   r3, [sp, #{CALLER_TARGET_OFFSET:#x}]
    mov   r1, fp, lsr #{HIT_SLOT_SHIFT}
    and   r1, r1, #{HIT_SLOT_MASK}
    add   r1, r6, r1, lsl #1
    strh  r4, [r1, #{TARGETS:#x}]
    mov   r0, #1
hit_done:
    pop   {{r1, pc}}
hit_work:
    .word {BATTLE_WORK_PTR:#x}
hit_battlers:
    .word {BATTLERS_PTR:#x}
"""


def _hook(addr: int, old: int, asm: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, asm, note)


MANUAL_TARGETING = Feature(
    "manual-targeting",
    (
        CaveCode("cave_tgt_state", STATE_ASM, "enemy list mode and entry map"),
        CaveCode("cave_tgt_rows", ROWS_ASM, "rows a party member reaches"),
        CaveCode("cave_tgt_ok", OK_ASM, "enemy alive and in reach"),
        CaveCode("cave_tgt_less", LESS_ASM, "enemy list order"),
        CaveCode("cave_tgt_after", AFTER_ASM, "next enemy in list order"),
        CaveCode("cave_tgt_next", NEXT_ASM, "living target or the next one"),
        CaveCode("cave_tgt_pick", PICK_ASM, "Attack uses the chosen enemy"),
        CaveCode("cave_tgt_hit", HIT_ASM, "hit on a dead enemy moves on"),
        *PICKER_PATCHES,
        _hook(
            AUTO_TARGET_CALL,
            0xEBFFFCCB,
            "bl ${cave_tgt_pick}",
            "Attack uses the chosen enemy",
        ),
        _hook(
            HIT_ALIVE_CALL,
            0xEB0003E9,
            "bl ${cave_tgt_hit}",
            "hit on a dead enemy moves on",
        ),
    ),
)
