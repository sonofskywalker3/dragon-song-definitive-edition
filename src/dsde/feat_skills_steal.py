"""Stealing from a monster (docs/plan-cards.md 5 and 8, approved build list points 4 and 5).

One routine for the Steal skill (the Morus card) and the Yeti card. A steal rolls its chance; on a success it takes
one item from the target's drop row (func_02069dd0(row, slot): slot 1, the rarer item, with the rare chance, else
slot 0, and the other slot when the first holds nothing that can be stolen), puts it in the bag, and the message
line says "Stole <item>!"; on a miss the MISS popup shows over the target. Each monster can be robbed once a battle:
its bit (0x10000 << (battler - 4)) of the battle flags word is set on the attempt, hit or miss, and the word is
zeroed each battle. What can be stolen: any item but a card, a dragon ring, or an item from id 387 up (key items,
orbs, the Package).

`cave_skill_stealable` is the refusal test of a steal (feat_skills_idle.py, kind STEAL): "No effect!" for a
monster already robbed or with nothing to steal.
"""

from dsde import targeting_consts as T
from dsde.feat_skills_table import ITEM_NAME_OFFSETS, ITEM_NAMES
from dsde.patching import CaveCode
from dsde.skills_common import (
    BATTLE_WORK_PTR,
    BATTLER_POSITION,
    BATTLER_ROW,
    BATTLER_SIZE,
    BATTLERS_PTR,
    MESSAGE_FRAMES,
    MESSAGE_WINDOW,
    OPEN_WINDOW,
    STRING_NO_EFFECT,
    WORK_MESSAGE,
    encode,
)

FIRST_ENEMY = 4
LAST_ENEMY = 11
ROBBED = 0x10000  # battle flags: ROBBED << (battler - FIRST_ENEMY)
DROP_ITEM = 0x02069DD0  # (enemy row, slot 0 or 1) -> item id, 0 for none
ADD_ITEM = 0x0206B98C  # (bag, item, count)
BAG = 0x0213B930
FIRST_CARD, LAST_CARD = 216, 269
FIRST_RING, LAST_RING = 0xCB, 0xCE
FIRST_UNSTEALABLE = 387
HIGH_BASE = 256
RANDOM = 0x02011424
DIVMOD = 0x02015F80
PERCENT = 100
POPUP = 0x0202BF9C
POPUP_MISS = 2
POPUP_RISE = 0x20
SOUND_MISS = 0x16
MESSAGE_STOLE = 8  # our bit of the message line: "Stole <item>!"
TEXT_WIDTH = 0x020450F8  # (string) -> its width in pixels
DRAW_TEXT = 0x02045114
STYLE_PLAIN, STYLE_NAME = 0, 1

# r0 = an item id -> r0 = the item if it can be stolen, else 0. Keeps r1 to r3 (ids past 255 are compared from
# HIGH_BASE, since the larger constants do not fit an ARM immediate).
OK_ASM = f"""
    sub   ip, r0, #{FIRST_CARD}
    cmp   ip, #{LAST_CARD - FIRST_CARD}
    bls   ok_no
    sub   ip, r0, #{FIRST_RING}
    cmp   ip, #{LAST_RING - FIRST_RING}
    bls   ok_no
    cmp   r0, #{HIGH_BASE}
    bxlo  lr
    sub   ip, r0, #{HIGH_BASE}
    cmp   ip, #{FIRST_UNSTEALABLE - 1 - HIGH_BASE}
    bxls  lr
ok_no:
    mov   r0, #0
    bx    lr
"""

# r0 = an enemy battler index -> r0 = 0 if a steal could take something from it, else "No effect!" (already robbed,
# or no item it can lose). Clobbers r1 to r3 and ip only.
STEALABLE_ASM = f"""
    push  {{r4, lr}}
    sub   r4, r0, #{FIRST_ENEMY}
    cmp   r4, #{LAST_ENEMY - FIRST_ENEMY}
    bhi   sb_none
    ldr   r1, sb_work
    ldr   r1, [r1]
    ldr   r1, [r1]
    mov   r2, #{ROBBED:#x}
    tst   r1, r2, lsl r4
    bne   sb_none
    ldr   r1, sb_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r4, [r0, #{BATTLER_ROW:#x}]
    mov   r0, r4
    mov   r1, #0
    bl    {DROP_ITEM:#x}
    bl    ${{cave_skill_steal_ok}}
    cmp   r0, #0
    bne   sb_fine
    mov   r0, r4
    mov   r1, #1
    bl    {DROP_ITEM:#x}
    bl    ${{cave_skill_steal_ok}}
    cmp   r0, #0
    beq   sb_none
sb_fine:
    mov   r0, #0
    pop   {{r4, pc}}
sb_none:
    mov   r0, #{STRING_NO_EFFECT}
    pop   {{r4, pc}}
sb_work:
    .word {BATTLE_WORK_PTR:#x}
sb_battlers:
    .word {BATTLERS_PTR:#x}
"""

# r0 = an enemy battler index, r1 = the chance (percent), r2 = the chance of the rarer slot -> r0 = the item stolen,
# or 0. A monster already robbed or with nothing to steal is left alone (a Steal and a Yeti aimed at it in the same
# round: the second finds it robbed). Otherwise marks it robbed, puts the item in the bag and opens the message
# line, or shows MISS.
STEAL_ASM = f"""
    push  {{r4-r8, lr}}
    mov   r4, r0
    mov   r5, r1
    mov   r6, r2
    bl    ${{cave_skill_stealable}}
    cmp   r0, #0
    bne   st_done
    ldr   r0, st_work
    ldr   r0, [r0]
    ldr   r1, [r0]
    sub   r2, r4, #{FIRST_ENEMY}
    mov   r3, #{ROBBED:#x}
    orr   r1, r1, r3, lsl r2
    str   r1, [r0]
    ldr   r0, st_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r8, r4, r1, r0
    bl    {RANDOM:#x}
    bic   r0, r0, #0x80000000
    mov   r1, #{PERCENT}
    bl    {DIVMOD:#x}
    cmp   r1, r5
    bhs   st_miss
    bl    {RANDOM:#x}
    bic   r0, r0, #0x80000000
    mov   r1, #{PERCENT}
    bl    {DIVMOD:#x}
    cmp   r1, r6
    movlo r5, #1
    movhs r5, #0
    ldr   r7, [r8, #{BATTLER_ROW:#x}]
    mov   r0, r7
    mov   r1, r5
    bl    {DROP_ITEM:#x}
    bl    ${{cave_skill_steal_ok}}
    cmp   r0, #0
    bne   st_take
    mov   r0, r7
    eor   r1, r5, #1
    bl    {DROP_ITEM:#x}
    bl    ${{cave_skill_steal_ok}}
    cmp   r0, #0
    beq   st_done
st_take:
    mov   r5, r0
    ldr   r0, st_bag
    mov   r1, r5
    mov   r2, #1
    bl    {ADD_ITEM:#x}
    ldr   r0, st_item
    strh  r5, [r0]
    ldr   r0, st_work
    ldr   r0, [r0]
    ldrh  r1, [r0, #{WORK_MESSAGE:#x}]
    orr   r1, r1, #{MESSAGE_STOLE}
    strh  r1, [r0, #{WORK_MESSAGE:#x}]
    mov   r0, #{MESSAGE_WINDOW:#x}
    mov   r1, #1
    mov   r2, #{MESSAGE_FRAMES:#x}
    bl    {OPEN_WINDOW:#x}
    mov   r0, r5
    pop   {{r4-r8, pc}}
st_miss:
    ldr   r0, [r8, #{BATTLER_POSITION:#x}]
    ldr   r1, [r8, #{BATTLER_POSITION + 4:#x}]
    ldr   r2, [r8, #{BATTLER_POSITION + 8:#x}]
    add   r2, r2, #{POPUP_RISE:#x}
    mov   r3, #{POPUP_MISS}
    bl    {POPUP:#x}
    mov   r0, #{SOUND_MISS:#x}
    bl    {T.PLAY_SOUND:#x}
st_done:
    mov   r0, #0
    pop   {{r4-r8, pc}}
st_work:
    .word {BATTLE_WORK_PTR:#x}
st_battlers:
    .word {BATTLERS_PTR:#x}
st_bag:
    .word {BAG:#x}
st_item:
    .word ${{cave_skill_stolen}}
"""


# Entered from the message line hook for our bit MESSAGE_STOLE (r5 = the text handle, r7 = x, r6 = y, [sp] the
# style word): "Stole " in plain text, the item's name highlighted as the game's "<item> was stolen" shows it,
# then "!". Ends at the drawer's epilogue.
def message_asm(done: int) -> str:
    return f"""
    mov   r0, #{STYLE_PLAIN}
    str   r0, [sp]
    mov   r0, r5
    mov   r1, r7
    add   r2, r6, #1
    adr   r3, sm_stole
    bl    {DRAW_TEXT:#x}
    adr   r0, sm_stole
    bl    {TEXT_WIDTH:#x}
    add   r7, r7, r0
    ldr   r0, sm_item
    ldrh  r0, [r0]
    ldr   r1, sm_offsets
    add   r1, r1, r0, lsl #1
    ldrh  r1, [r1]
    ldr   r8, sm_names
    add   r8, r8, r1
    mov   r0, #{STYLE_NAME}
    str   r0, [sp]
    mov   r0, r5
    mov   r1, r7
    add   r2, r6, #1
    mov   r3, r8
    bl    {DRAW_TEXT:#x}
    mov   r0, r8
    bl    {TEXT_WIDTH:#x}
    add   r7, r7, r0
    mov   r0, #{STYLE_PLAIN}
    str   r0, [sp]
    mov   r0, r5
    mov   r1, r7
    add   r2, r6, #1
    adr   r3, sm_bang
    bl    {DRAW_TEXT:#x}
    b     {done:#x}
sm_item:
    .word ${{cave_skill_stolen}}
sm_offsets:
    .word {ITEM_NAME_OFFSETS:#x}
sm_names:
    .word {ITEM_NAMES:#x}
sm_stole:
    .byte {", ".join(str(b) for b in encode("Stole "))}
sm_bang:
    .byte {", ".join(str(b) for b in encode("!"))}
    .align 2
"""


MESSAGE_DONE = 0x020449EC  # func_02044990's epilogue

STEAL_PATCHES: tuple[CaveCode, ...] = (
    CaveCode(
        "cave_skill_steal_msg",
        message_asm(MESSAGE_DONE),
        "the message line can say Stole <item>!",
    ),
    CaveCode(
        "cave_skill_stolen",
        "    .hword 0\n    .align 2\n",
        "the item stolen, for the message",
    ),
    CaveCode("cave_skill_steal_ok", OK_ASM, "an item that can be stolen"),
    CaveCode(
        "cave_skill_stealable", STEALABLE_ASM, "a monster with something to steal"
    ),
    CaveCode("cave_skill_steal", STEAL_ASM, "a steal"),
)
