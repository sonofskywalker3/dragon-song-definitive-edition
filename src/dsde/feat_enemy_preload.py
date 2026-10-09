"""Load an enemy's sound bank before its action starts (docs/re-battle-pacing.md section 7, P9).

The 2-frame hitches during enemy actions are sound bank loads, not sprite loads (confirmed, section 7).
func_02028234 plays a battle sound; ids 0x1F..0x5C need one of the sound effect banks 2, 3, or 4, and only
one of them fits in the 512 KB sound heap next to the system bank and the battle music. When a sound needs
a bank other than the loaded one (s16 0x020B8564), it stops a flagged looping sound (func_02028434), pops the
heap to level 3 (func_02043eb0), and loads the new bank and its wave archive (func_02043f5c, 129 to 165 KB)
from the card synchronously: the battle main misses two frames.

This hook runs where round state 6 starts the action (func_0202d22c calls func_020316e0(12) for step 0,
right after copying the actor into battler 12): the camera turn has ended and the enemy has not moved yet,
and the animation slots that state 5 queued are loaded (state 6 waits for func_0201a530). For an enemy actor
(battler 4..11) it predicts the first sound of the action that needs a bank, in the order the game plays
them: for each step, the step's sound (kind at step +6, func_02067448(12, kind, 0) as in func_020316e0), then
the sounds of the step's animation cels (slot data at battle work +0x5C + 4 * slot: animation table at
+8, cel table at +0xC; a cel's kind at +4, func_02067448(12, kind, 1) as in func_02031e08). For a skill whose
own steps have none, it walks the first target's effect script (battle work +0x78) with the kinds that do
not depend on the effect battler. If that bank is not the loaded one, it switches banks exactly as
func_02028234 does, so the load (and its two lag frames) falls on a still frame and the first sound finds
its bank loaded. Then it runs func_020316e0(12) as before.

It cannot remove a switch inside one action: an action whose sounds need two banks (the generic lunge
0x02095334 plays 0x52 from bank 4, 0x28 from bank 2, then 0x52 again) still loads between its steps,
because two banks never fit at once (section 7).
"""

from dsde.patching import AsmPatch, CaveCode, Feature

# func_0202d22c round state 6: the two `bl func_020316e0` (r0 = 12) that start step 0
STEP0_CALLS = (0x0202D840, 0x0202D874)
STEP0_CALL_WORDS = (0xEB000FA6, 0xEB000F99)
START_STEP = 0x020316E0
BATTLE_WORK = 0x020B8550
BATTLERS = 0x020B8640
SOUND_BANK = 0x020B8564  # s16: the sound effect bank in the heap's level 4, -1 none
BATTLER_SIZE = 300
ACTING_COPY = 12
ACTOR = 0x32  # battle work: acting battler
SLOT_DATA = 0x5C  # battle work: animation slot buffers (u32 each)
EFFECT_SCRIPTS = 0x78  # battle work: effect script per target slot (u32 each)
SCRIPT = 0xC8  # battler: action script
AI_COMMAND = 0x84  # battler: 1 physical, 2 or 4 skill
TARGETS = 0x8C  # battler: 8 target slots (s16, -1 empty)
PARTY_SLOTS_FLAG = (
    0x100000  # battler flags: slots per battler (func_020316e0), not an enemy layout
)
TARGET_SLOTS = 8
PHYSICAL = 1
FIRST_ENEMY = 4
ENEMY_END = 12
FIRST_EFFECT = 0xE
STEP_SIZE = 0x10
STEP_SOUND_KIND = 6  # u16
STEP_SLOT = 8  # s16
STEP_ANIM = 0xA  # u16
LAST_STEP = 0x80000000
MAX_STEPS = 64
SLOT_ANIM_COUNT = 4  # slot data: u16 number of animations (func_02032acc)
SLOT_ANIM_TABLE = 8  # u32 offset of the animation table (0xC per animation)
SLOT_CEL_TABLE = 0xC  # u32 offset of the cel table (0x18 per cel)
ANIM_SIZE = 0xC
ANIM_FIRST_CEL = 0  # u16
ANIM_CEL_COUNT = 8  # u16 (func_02032aac)
CEL_SIZE = 0x18
CEL_SOUND_KIND = 4  # s32, played when the cel starts if > 0 (func_02032a0c)
MAX_CELS = 64
# kinds whose sound comes from the battler's species (func_02067448 cases 1 and 3)
SPECIES_KIND_ATTACK = 1
SPECIES_KIND_MOVE = 3
# where a script or slot buffer may be: ITCM caves (cut scripts) up to main RAM's end
POINTER_LO = 0x01FF8000
POINTER_HI = 0x02400000
# func_02028234: ids 0x1F..0x5C pick a bank (0x20, 0x21, 0x24 pick none)
BANK_IDS_FIRST = 0x1F
BANK_IDS_SPAN = 0x3D
BANK4_FIRST = 0x4B  # 0x4B..0x5C
BANK3_FIRST = 0x3A  # 0x3A..0x4A and 0x22
BANK3_SINGLE = 0x22
BANK2_FIRST = 0x25  # 0x25..0x39, 0x1F and 0x23
BANK2_SINGLE_A = 0x1F
BANK2_SINGLE_B = 0x23
SOUND_FOR_KIND = 0x02067448
STOP_FLAGGED_SOUND = 0x02028434
POP_SOUND_BANK = 0x02043EB0
LOAD_SOUND_BANK = 0x02043F5C

# Replaces `bl func_020316e0` (r0 = 12). Registers: r4 work, r5 battler index for func_02067448, r6 battler,
# r7 step, r8 1 when the species kinds and the cels count, r9 / r10 scratch.
#   ep_walk: walks the script at r7; r0 = bank of the first sound that needs one, or -1.
#   ep_kind: r1 = kind, r2 = func_02067448's third argument; r0 = bank or -1.
#   ep_cels: r0 = step; r0 = bank of the first cel sound of its animation, or -1.
PRELOAD_ASM = f"""
    push  {{r0-r11, lr}}
    ldr   r4, ep_work
    ldr   r4, [r4]
    cmp   r4, #0
    beq   ep_out
    ldrsh r0, [r4, #{ACTOR:#x}]
    cmp   r0, #{FIRST_ENEMY}
    blt   ep_out
    cmp   r0, #{ENEMY_END}
    bge   ep_out
    ldr   r6, ep_battlers
    ldr   r6, [r6]
    mov   r0, #{BATTLER_SIZE}
    mov   r5, #{ACTING_COPY}
    mla   r6, r5, r0, r6
    ldr   r7, [r6, #{SCRIPT:#x}]
    ldr   r0, [r6]
    tst   r0, #{PARTY_SLOTS_FLAG:#x}
    moveq r8, #1
    movne r8, #0
    bl    ep_walk
    cmp   r0, #0
    bge   ep_have
    ldrh  r0, [r6, #{AI_COMMAND:#x}]
    cmp   r0, #{PHYSICAL}
    beq   ep_out
    mov   r9, #0
ep_find:
    add   r0, r6, r9, lsl #1
    ldrsh r0, [r0, #{TARGETS:#x}]
    cmn   r0, #1
    bne   ep_found
    add   r9, r9, #1
    cmp   r9, #{TARGET_SLOTS}
    blt   ep_find
    b     ep_out
ep_found:
    add   r0, r4, r9, lsl #2
    ldr   r7, [r0, #{EFFECT_SCRIPTS:#x}]
    add   r5, r9, #{FIRST_EFFECT:#x}
    mov   r8, #0
    bl    ep_walk
    cmp   r0, #0
    blt   ep_out
ep_have:
    ldr   r9, ep_bank
    ldrsh r1, [r9]
    cmp   r1, r0
    beq   ep_out
    mov   r10, r0
    bl    {STOP_FLAGGED_SOUND:#x}
    bl    {POP_SOUND_BANK:#x}
    mov   r0, #0
    mov   r1, r10
    bl    {LOAD_SOUND_BANK:#x}
    strh  r10, [r9]
ep_out:
    pop   {{r0-r11, lr}}
    b     {START_STEP:#x}

ep_walk:
    push  {{r7, r11, lr}}
    mov   r0, r7
    bl    ep_valid
    bne   ep_none
    mov   r11, #0
ep_step:
    ldrh  r1, [r7, #{STEP_SOUND_KIND}]
    mov   r2, #0
    bl    ep_kind
    cmp   r0, #0
    bge   ep_ret
    cmp   r8, #0
    beq   ep_next
    mov   r0, r7
    bl    ep_cels
    cmp   r0, #0
    bge   ep_ret
ep_next:
    ldr   r0, [r7]
    tst   r0, #{LAST_STEP:#x}
    bne   ep_none
    add   r7, r7, #{STEP_SIZE:#x}
    add   r11, r11, #1
    cmp   r11, #{MAX_STEPS}
    blt   ep_step
ep_none:
    mvn   r0, #0
ep_ret:
    pop   {{r7, r11, pc}}

ep_cels:
    push  {{r7, r9, r10, r11, lr}}
    ldrsh r1, [r0, #{STEP_SLOT}]
    ldrh  r7, [r0, #{STEP_ANIM}]
    cmp   r1, #0
    blt   ep_cnone
    add   r1, r4, r1, lsl #2
    ldr   r9, [r1, #{SLOT_DATA:#x}]
    mov   r0, r9
    bl    ep_valid
    bne   ep_cnone
    ldrh  r1, [r9, #{SLOT_ANIM_COUNT}]
    cmp   r7, r1
    movhs r7, #0
    ldr   r1, [r9, #{SLOT_ANIM_TABLE}]
    add   r1, r9, r1
    mov   r0, #{ANIM_SIZE}
    mla   r1, r7, r0, r1
    ldrh  r10, [r1, #{ANIM_FIRST_CEL}]
    ldrh  r11, [r1, #{ANIM_CEL_COUNT}]
    cmp   r11, #{MAX_CELS}
    movhi r11, #{MAX_CELS}
    ldr   r1, [r9, #{SLOT_CEL_TABLE}]
    add   r9, r9, r1
    mov   r0, #{CEL_SIZE}
    mla   r9, r10, r0, r9
ep_cel:
    subs  r11, r11, #1
    blt   ep_cnone
    ldr   r1, [r9, #{CEL_SOUND_KIND}]
    add   r9, r9, #{CEL_SIZE:#x}
    cmp   r1, #0
    ble   ep_cel
    mov   r2, #1
    bl    ep_kind
    cmp   r0, #0
    blt   ep_cel
    pop   {{r7, r9, r10, r11, pc}}
ep_cnone:
    mvn   r0, #0
    pop   {{r7, r9, r10, r11, pc}}

ep_valid:
    ldr   r1, ep_lo
    cmp   r0, r1
    blo   ep_invalid
    ldr   r1, ep_hi
    cmp   r0, r1
    bhs   ep_invalid
    cmp   r0, r0
    bx    lr
ep_invalid:
    cmp   r0, #0
    cmpeq r0, #1
    bx    lr

ep_kind:
    cmp   r1, #0
    beq   ep_knone
    cmp   r8, #0
    bne   ep_ksound
    cmp   r1, #{SPECIES_KIND_ATTACK}
    cmpne r1, #{SPECIES_KIND_MOVE}
    beq   ep_knone
ep_ksound:
    push  {{lr}}
    mov   r0, r5
    bl    {SOUND_FOR_KIND:#x}
    pop   {{lr}}
    sub   r1, r0, #{BANK_IDS_FIRST:#x}
    cmp   r1, #{BANK_IDS_SPAN:#x}
    bhi   ep_knone
    cmp   r0, #{BANK4_FIRST:#x}
    movge r0, #4
    bxge  lr
    cmp   r0, #{BANK3_FIRST:#x}
    movge r0, #3
    bxge  lr
    cmp   r0, #{BANK2_FIRST:#x}
    movge r0, #2
    bxge  lr
    cmp   r0, #{BANK3_SINGLE:#x}
    moveq r0, #3
    bxeq  lr
    cmp   r0, #{BANK2_SINGLE_A:#x}
    cmpne r0, #{BANK2_SINGLE_B:#x}
    moveq r0, #2
    bxeq  lr
ep_knone:
    mvn   r0, #0
    bx    lr

ep_work:
    .word {BATTLE_WORK:#x}
ep_battlers:
    .word {BATTLERS:#x}
ep_bank:
    .word {SOUND_BANK:#x}
ep_lo:
    .word {POINTER_LO:#x}
ep_hi:
    .word {POINTER_HI:#x}
"""

ENEMY_PRELOAD = Feature(
    "enemy-preload",
    (
        CaveCode(
            "cave_enemy_preload",
            PRELOAD_ASM,
            "load the acting enemy's sound bank before its first step",
        ),
        *(
            AsmPatch(
                addr,
                addr + 4,
                word,
                word,
                "bl ${cave_enemy_preload}",
                "round state 6: switch the sound bank before the enemy moves",
            )
            for addr, word in zip(STEP0_CALLS, STEP0_CALL_WORDS)
        ),
    ),
)
