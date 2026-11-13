"""What a learned skill does when it is cast, and the "No effect!" line.

The effect hook sits in func_020500dc, which runs once per target of a spell. By the skill's kind
(skills_data.Kind):

- STAGE: the stat moves one stage with the game's own routine and the target's stats are recomputed,
  choosing the recompute by the target's side as the debuff cards do;
- STATUS: a success roll against the skill's chance (none, and no random number drawn, for a skill that
  always lands), then the status is queued the way the game's own
  status skills queue it (func_0202d1d4), so the flash, the mark over the battler, and the turn handling are
  the game's; a failed roll shows the game's MISS popup over the target with its sound;
- FLAG: the battle-wide flag is set, with the result word the card of that flag leaves.

A target the skill would do nothing to (feat_skills_idle.py) is left alone. For a spell on one target the
message line then says "No effect!" (the menu refuses such a pick, but the target can change after it); a
spell on everyone just passes over that target.

The cast's look is in feat_skills_look.py.
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLER_ENEMY,
    BATTLER_POSITION,
    BATTLER_RECORD,
    BATTLER_SIZE,
    BATTLERS_PTR,
    DRAW_TEXT,
    FX_ARG,
    FX_CHANCE,
    FX_DELTA,
    FX_KIND,
    FX_SIZE_SHIFT,
    MESSAGE_FRAMES,
    MESSAGE_NO_EFFECT,
    MESSAGE_WINDOW,
    OPEN_WINDOW,
    RECORD_SIZE,
    RECORDS_PTR,
    STRING_BASE,
    STRING_NO_EFFECT,
    STRING_OFFSETS,
    WORK_MESSAGE,
    hook,
)
from dsde.skills_data import SPELL_COUNT, SURE, Kind

FX_SITE = 0x020503A0  # func_020500dc: `ands r0, r5, #0x1000000`, the first buff test
FX_WORD = 0xE2150401
ADD_STAGE = 0x02054DEC  # (record, stat, delta)
RECOMPUTE_ENEMY = 0x02069AD8  # (record, 1)
RECOMPUTE_PARTY = 0x02054EBC
RESULT_WORDS = 0x0213B8F8
RESULT_FLAG = 8  # word 2: -1 as a debuff card leaves it (the target darkens), 1 as a buff spell does
RESULT_FLASH = 12  # word 3: -2 as the game's status skills leave it
STATUS_QUEUED = -2
RESULT_SURE_HIT = 4  # word 2 as the cards with a battle-wide flag leave it
RANDOM = 0x02011424  # () -> the game's random number
DIVMOD = 0x02015F80  # (n, d) -> r0 = n / d, r1 = n % d
PERCENT = 100
QUEUE_STATUS = (
    0x0202D1D4  # (battler index, status): applied by the round after the action
)
POPUP = 0x0202BF9C  # (x, y, z, kind): a floating popup; the hit resolver's miss is kind 2, 0x20 above
POPUP_MISS = 2
POPUP_RISE = 0x20
SOUND_MISS = 0x16

# The message line (window 0xD: "Lost Abadon card!", "Escape failed!"): func_02044990 picks its text from
# battle work +0xDA (bit 0, bit 1), +0xDC, +0xDE, +0xE0; the window clears them when it closes.
MESSAGE_SITE = (
    0x020449C0  # `ands r1, r2, #1` (r2 = +0xDA, r5 = text handle, r7 = x, r6 = y)
)
MESSAGE_SITE_WORD = 0xE2121001
MESSAGE_NEXT = 0x020449C4
MESSAGE_DONE = 0x020449EC  # the function's epilogue

# Replaces `ands r0, r5, #0x1000000` in func_020500dc (bl). r6 = spell, r7 = target battler, r5 = the
# spell's flags. Leaves the flags of the replaced instruction.
FX_ASM = f"""
    push  {{r4, r8, sb, lr}}
    cmp   r6, #{SPELL_COUNT}
    bhs   fx_out
    ldr   sb, fx_table
    add   sb, sb, r6, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [sb, #{FX_KIND}]
    cmp   r0, #{Kind.NONE}
    beq   fx_out
    mov   r0, r7
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   fx_none
    ldr   r0, fx_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r4, r7, r1, r0
    ldrb  r0, [sb, #{FX_KIND}]
    cmp   r0, #{Kind.STATUS}
    beq   fx_status
    cmp   r0, #{Kind.FLAG}
    beq   fx_flag
    ldr   r0, [r4, #{BATTLER_RECORD:#x}]
    ldr   r1, fx_records
    ldr   r1, [r1]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r8, r0, r2, r1
    mov   r0, r8
    ldrb  r1, [sb, #{FX_ARG}]
    ldrsb r2, [sb, #{FX_DELTA}]
    bl    {ADD_STAGE:#x}
    mov   r0, r8
    mov   r1, #1
    ldr   r2, [r4]
    tst   r2, #{BATTLER_ENEMY}
    beq   fx_party
    bl    {RECOMPUTE_ENEMY:#x}
    b     fx_result
fx_party:
    bl    {RECOMPUTE_PARTY:#x}
fx_result:
    ldr   r0, fx_results
    ldrsb r1, [sb, #{FX_DELTA}]
    str   r1, [r0, #{RESULT_FLAG}]
    b     fx_out
fx_status:
    ldrb  r8, [sb, #{FX_CHANCE}]
    cmp   r8, #{SURE}
    bhs   fx_lands
    bl    {RANDOM:#x}
    bic   r0, r0, #0x80000000
    mov   r1, #{PERCENT}
    bl    {DIVMOD:#x}
    cmp   r1, r8
    bhs   fx_miss
fx_lands:
    mov   r0, r7
    ldrb  r1, [sb, #{FX_ARG}]
    bl    {QUEUE_STATUS:#x}
    ldr   r0, fx_results
    mvn   r1, #{-STATUS_QUEUED - 1}
    str   r1, [r0, #{RESULT_FLASH}]
    b     fx_out
fx_miss:
    ldr   r0, [r4, #{BATTLER_POSITION:#x}]
    ldr   r1, [r4, #{BATTLER_POSITION + 4:#x}]
    ldr   r2, [r4, #{BATTLER_POSITION + 8:#x}]
    add   r2, r2, #{POPUP_RISE:#x}
    mov   r3, #{POPUP_MISS}
    bl    {POPUP:#x}
    mov   r0, #{SOUND_MISS:#x}
    bl    {T.PLAY_SOUND:#x}
    b     fx_out
fx_flag:
    ldr   r0, fx_work
    ldr   r0, [r0]
    ldr   r1, [r0]
    ldrb  r2, [sb, #{FX_ARG}]
    orr   r1, r1, r2
    str   r1, [r0]
    ldr   r0, fx_results
    mov   r1, #{RESULT_SURE_HIT}
    str   r1, [r0, #{RESULT_FLAG}]
    b     fx_out
fx_none:
    tst   r5, #{ALL_TARGETS:#x}
    bne   fx_out
    ldr   r0, fx_work
    ldr   r0, [r0]
    mov   r1, #{MESSAGE_NO_EFFECT}
    strh  r1, [r0, #{WORK_MESSAGE:#x}]
    mov   r0, #{MESSAGE_WINDOW:#x}
    mov   r1, #1
    mov   r2, #{MESSAGE_FRAMES:#x}
    bl    {OPEN_WINDOW:#x}
fx_out:
    ands  r0, r5, #0x1000000
    pop   {{r4, r8, sb, pc}}
fx_table:
    .word ${{cave_skill_fx}}
fx_battlers:
    .word {BATTLERS_PTR:#x}
fx_records:
    .word {RECORDS_PTR:#x}
fx_results:
    .word {RESULT_WORDS:#x}
fx_work:
    .word {BATTLE_WORK_PTR:#x}
"""

# Replaces `ands r1, r2, #1` in func_02044990 (b). A third message bit draws "No effect!" the way the
# first draws "Escape failed!".
MESSAGE_ASM = f"""
    tst   r2, #{MESSAGE_NO_EFFECT}
    beq   message_vanilla
    mov   r2, #0
    str   r2, [sp]
    ldr   r1, message_offsets
    ldrh  r3, [r1, #{2 * STRING_NO_EFFECT}]
    ldr   r4, message_base
    add   r3, r4, r3
    mov   r0, r5
    mov   r1, r7
    add   r2, r6, #1
    bl    {DRAW_TEXT:#x}
    b     {MESSAGE_DONE:#x}
message_vanilla:
    ands  r1, r2, #1
    b     {MESSAGE_NEXT:#x}
message_offsets:
    .word {STRING_OFFSETS:#x}
message_base:
    .word {STRING_BASE:#x}
"""

FX_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_effect", FX_ASM, "what a skill does to its target"),
    hook(
        FX_SITE,
        FX_WORD,
        "bl ${cave_skill_effect}",
        "what a skill does to its target",
    ),
    CaveCode("cave_skill_msg", MESSAGE_ASM, "the message line can say No effect!"),
    hook(
        MESSAGE_SITE,
        MESSAGE_SITE_WORD,
        "b ${cave_skill_msg}",
        "the message line can say No effect!",
    ),
)
