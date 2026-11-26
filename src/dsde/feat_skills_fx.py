"""What a learned skill does when it is cast, and the "No effect!" line.

The effect hook sits in func_020500dc, which runs once per target of a spell. By the skill's kind
(skills_data.Kind):

- STAGE: the stat moves one stage with the game's own routine and the target's stats are recomputed,
  choosing the recompute by the target's side as the debuff cards do;
- STATUS: on a boss, a roll of 80% (the statuses a boss is not immune to: poison and blind); otherwise a success
  roll against the skill's chance (none, and no random number drawn, for a skill that
  always lands), then the status is queued the way the game's own
  status skills queue it (func_0202d1d4), so the flash, the mark over the battler, and the turn handling are
  the game's; a failed roll shows the game's MISS popup over the target with its sound;
- STEAL: a steal (feat_skills_steal.py);
- FLAG: the battle-wide flag is set, with the result word the card of that flag leaves. The sure-hit flag cast on
  one ally (Focus) sets that member's own bit instead, unless a worn card enhances the cast (Bealzebub: the
  party's flag); the hit roll (0x020526FC) reads the attacker's own bit as the party's.

A cast a worn card enhances (feat_skills_boost.py) moves a stat 2 stages, and its status always lands and is
marked as the strong kind.

A target the skill would do nothing to (feat_skills_idle.py) is left alone. For a spell on one target the
message line then says "No effect!" (the menu refuses such a pick, but the target can change after it); a
spell on everyone just passes over that target.

The cast's look is in feat_skills_look.py.
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.feat_skills_boost import BOOST_LIMIT, STATE_PENDING
from dsde.feat_skills_steal import MESSAGE_STOLE
from dsde.skills_common import (
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLER_ENEMY,
    BATTLER_POSITION,
    BATTLER_ROW,
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
    RECORD_STAGES,
    RECORDS_PTR,
    STRING_BASE,
    STRING_NO_EFFECT,
    STRING_OFFSETS,
    WORK_MESSAGE,
    hook,
)
from dsde.skills_data import SPELL_COUNT, SURE, Kind
from dsde.feat_skills_idle import ENEMY_ROW_SIZE, ENEMY_ROWS, ROW_BOSS
from dsde.skills_types import BOSS_CHANCE, FLAG_SURE_HIT, PERSONAL_SURE_HIT

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
    push  {{r4, r8, sb, sl, lr}}
    cmp   r6, #{SPELL_COUNT}
    bhs   fx_out
    ldr   sb, fx_table
    add   sb, sb, r6, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [sb, #{FX_KIND}]
    cmp   r0, #{Kind.NONE}
    beq   fx_out
    cmp   r0, #{Kind.HIT}
    beq   fx_out
    mov   r0, r7
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   fx_none
    bl    ${{cave_skill_boosted}}
    mov   sl, r0
    ldr   r0, fx_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r4, r7, r1, r0
    ldrb  r0, [sb, #{FX_KIND}]
    cmp   r0, #{Kind.STATUS}
    beq   fx_status
    cmp   r0, #{Kind.FLAG}
    beq   fx_flag
    cmp   r0, #{Kind.STEAL}
    beq   fx_steal
    ldr   r0, [r4, #{BATTLER_RECORD:#x}]
    ldr   r1, fx_records
    ldr   r1, [r1]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r8, r0, r2, r1
    mov   r0, r8
    ldrb  r1, [sb, #{FX_ARG}]
    ldrsb r2, [sb, #{FX_DELTA}]
    bl    {ADD_STAGE:#x}
    cmp   sl, #0
    beq   fx_recompute
    ldrb  r1, [sb, #{FX_ARG}]
    add   r0, r8, r1, lsl #1
    ldrsh r0, [r0, #{RECORD_STAGES:#x}]
    ldrsb r2, [sb, #{FX_DELTA}]
    cmp   r2, #0
    rsblt r0, r0, #0
    cmp   r0, #{BOOST_LIMIT}
    bge   fx_recompute
    mov   r0, r8
    ldrb  r1, [sb, #{FX_ARG}]
    bl    {ADD_STAGE:#x}
fx_recompute:
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
    ldr   r0, [r4]
    tst   r0, #{BATTLER_ENEMY}
    beq   fx_regular
    ldr   r0, [r4, #{BATTLER_ROW:#x}]
    ldr   r1, fx_rows
    mov   r2, #{ENEMY_ROW_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0]
    tst   r0, #{ROW_BOSS:#x}
    movne r8, #{BOSS_CHANCE}
    bne   fx_roll
fx_regular:
    cmp   sl, #0
    bne   fx_lands
fx_roll:
    cmp   r8, #{SURE}
    bhs   fx_lands
    bl    {RANDOM:#x}
    bic   r0, r0, #0x80000000
    mov   r1, #{PERCENT}
    bl    {DIVMOD:#x}
    cmp   r1, r8
    bhs   fx_miss
fx_lands:
    cmp   sl, #0
    beq   fx_queue
    mov   r0, r7
    bl    ${{cave_skill_record_of}}
    ldr   r1, fx_state
    add   r1, r1, r0
    mov   r0, #1
    strb  r0, [r1, #{STATE_PENDING}]
fx_queue:
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
    cmp   r2, #{FLAG_SURE_HIT}
    bne   fx_flag_set
    tst   r5, #{ALL_TARGETS:#x}
    bne   fx_flag_set
    cmp   sl, #0
    moveq r2, #{PERSONAL_SURE_HIT:#x}
    lsleq r2, r2, r7
fx_flag_set:
    orr   r1, r1, r2
    str   r1, [r0]
    ldr   r0, fx_results
    mov   r1, #{RESULT_SURE_HIT}
    str   r1, [r0, #{RESULT_FLAG}]
    b     fx_out
fx_steal:
    mov   r0, r7
    ldrb  r1, [sb, #{FX_CHANCE}]
    ldrb  r2, [sb, #{FX_ARG}]
    bl    ${{cave_skill_steal}}
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
    pop   {{r4, r8, sb, sl, pc}}
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
fx_state:
    .word ${{cave_skill_boost}}
fx_rows:
    .word {ENEMY_ROWS:#x}
"""

# Replaces `ands r1, r2, #1` in func_02044990 (b). A third message bit draws "No effect!" the way the
# first draws "Escape failed!".
MESSAGE_ASM = f"""
    tst   r2, #{MESSAGE_STOLE}
    bne   ${{cave_skill_steal_msg}}
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

# func_0205265c (the hit roll; r4 = the attacker's stat record, r6 is reused by then): `ldr r0, [r0]`, the battle
# flags word it tests for the party's sure hit
SURE_HIT_SITE = 0x020526FC
SURE_HIT_WORD = 0xE5900000
PARTY_SLOTS = 3

# In place of `ldr r0, [r0]`: the flags word, with the party's sure-hit bit added when the attacker is the party
# member in slot n (their battler's stat record is r4) and bit PERSONAL_SURE_HIT << n is set. Keeps r1 to r3.
SURE_HIT_ASM = f"""
    ldr   r0, [r0]
    push  {{r1-r3, lr}}
    ldr   r1, sh_records
    ldr   r1, [r1]
    sub   r2, r4, r1
    mov   r1, #0
sh_index:
    cmp   r2, #{RECORD_SIZE:#x}
    subhs r2, r2, #{RECORD_SIZE:#x}
    addhs r1, r1, #1
    bhs   sh_index
    ldr   r2, sh_battlers
    ldr   r2, [r2]
    mov   r3, #0
sh_slot:
    ldr   lr, [r2, #{BATTLER_RECORD:#x}]
    cmp   lr, r1
    beq   sh_found
    add   r2, r2, #{BATTLER_SIZE:#x}
    add   r3, r3, #1
    cmp   r3, #{PARTY_SLOTS}
    blt   sh_slot
    pop   {{r1-r3, pc}}
sh_found:
    mov   r1, #{PERSONAL_SURE_HIT:#x}
    tst   r0, r1, lsl r3
    orrne r0, r0, #{FLAG_SURE_HIT}
    pop   {{r1-r3, pc}}
sh_records:
    .word {RECORDS_PTR:#x}
sh_battlers:
    .word {BATTLERS_PTR:#x}
"""

FX_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_sure_hit", SURE_HIT_ASM, "a member's own sure hit"),
    hook(
        SURE_HIT_SITE,
        SURE_HIT_WORD,
        "bl ${cave_skill_sure_hit}",
        "a member's own sure hit",
    ),
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
