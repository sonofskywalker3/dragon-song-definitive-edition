"""What a learned skill does when it is cast: the effect, the cast's look, and the "No effect!" line.

- Effect (func_020500dc, which runs once per target): a stage skill moves its stat one stage with the
  game's own routine and recomputes the target's stats, choosing the recompute by the target's side as the
  debuff cards do. A stat already a stage past 0 in that direction is left alone.
- Look (the party action setup, func_02068308): a skill with the ATTACK look plays its owner's attack with
  the hit flags taken out and starts the effect row's banner on the last blow. Only Jian has such skills so
  far; the scripts are copies of his combo.
- A cast that will do nothing (the menu refuses a pick like that, but the target can change after the pick)
  has no effect step, so no banner, and the message line says "No effect!" as the cast starts.
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    ACTION_SPECIAL,
    BATTLE_WORK_PTR,
    BATTLER_COMMAND,
    BATTLER_ENEMY,
    BATTLER_RECORD,
    BATTLER_SCRIPT,
    BATTLER_SIZE,
    BATTLERS_PTR,
    DRAW_TEXT,
    FIRST_ENEMY,
    FIRST_FRONT_ENEMY,
    FX_DELTA,
    FX_KIND,
    FX_LOOK,
    FX_SIZE_SHIFT,
    FX_STAT,
    MESSAGE_FRAMES,
    MESSAGE_NO_EFFECT,
    MESSAGE_WINDOW,
    OPEN_WINDOW,
    RECORD_SIZE,
    RECORDS_PTR,
    STRING_BASE,
    STRING_NO_EFFECT,
    STRING_OFFSETS,
    WORK_EFFECT_MODE,
    WORK_MESSAGE,
    WORK_SLOT0,
    hook,
)
from dsde.skills_data import SPELL_COUNT, Kind, Look

FX_SITE = 0x020503A0  # func_020500dc: `ands r0, r5, #0x1000000`, the first buff test
FX_WORD = 0xE2150401
ADD_STAGE = 0x02054DEC  # (record, stat, delta)
RECOMPUTE_ENEMY = 0x02069AD8  # (record, 1)
RECOMPUTE_PARTY = 0x02054EBC
RESULT_WORDS = 0x0213B8F8
RESULT_FLAG = 8  # word 2: -1 as a debuff card leaves it (the target darkens), 1 as a buff spell does

PARTY_SETUP_CALL = (
    0x020688B4  # func_02068890: `bl func_02068308` (party action setup), r0 = the actor
)
PARTY_SETUP_CALL_WORD = 0xEBFFFE93
PARTY_SETUP = 0x02068308  # (actor, mode)
SETUP_COUNTER = (
    1  # mode bit: the actor's counterattack, set up in slots 3 to 5 with its own script
)
JIAN_ATTACK_FILE = 0x020953D4 + 4  # character table, Jian: the 3-hit combo's file

# Action script steps: flags, sound << 16 | effects started << 8, slot, animation, frames. Flags as in
# Jian's combo 0x02095AF0, with the three hit flags (0x40) gone and the last kick starting the target's
# effect script (bits 8..15 of the second word) and waiting for it (0x02000000).
Steps = tuple[tuple[int, int, int, int, int], ...]
STEP_START_EFFECTS = 0xFF00
STEP_WAIT_EFFECTS = 0x02000000
JIAN_CAST: Steps = (
    (0x00200001, 0x00000000, 1, 0, 0),
    (0x00001016, 0x00030000, 1, 1, 6),
    (0x00000012, 0x00000000, 1, 2, 6),
    (0x00000001, 0x00000000, 1, 3, 0),
    (0x00000001, 0x00010000, 0, 0, 0),
    (0x00000001, 0x00010000, 0, 1, 0),
    (0x00000001, 0x00010000, 0, 2, 0),
    (0x00000001 | STEP_WAIT_EFFECTS, STEP_START_EFFECTS, 0, 3, 0),
    (0x00000001, 0x00000000, 1, 0, 0),
    (0x04009016, 0x00030000, 1, 2, 8),
    (0x04000012, 0x00000000, 1, 1, 8),
    (0x80000001, 0x00000000, 1, 3, 0),
)
# The same against a back-row enemy, from Jian's leaping combo 0x02095560
JIAN_CAST_BACK: Steps = (
    (0x00300001, 0x00000000, 1, 0, 0),
    (0x00001012, 0x00030000, 1, 1, 20),
    (0x00000001, 0x00010000, 0, 0, 0),
    (0x00000001, 0x00010000, 0, 1, 0),
    (0x00000001, 0x00010000, 0, 2, 0),
    (0x00000001 | STEP_WAIT_EFFECTS, STEP_START_EFFECTS, 0, 3, 0),
    (0x04009012, 0x00000000, 1, 2, 16),
    (0x80000001, 0x00000000, 1, 3, 0),
)

# The message line (window 0xD: "Lost Abadon card!", "Escape failed!"): func_02044990 picks its text from
# battle work +0xDA (bit 0, bit 1), +0xDC, +0xDE, +0xE0; the window clears them when it closes.
MESSAGE_SITE = (
    0x020449C0  # `ands r1, r2, #1` (r2 = +0xDA, r5 = text handle, r7 = x, r6 = y)
)
MESSAGE_SITE_WORD = 0xE2121001
MESSAGE_NEXT = 0x020449C4
MESSAGE_DONE = 0x020449EC  # the function's epilogue

# Replaces `ands r0, r5, #0x1000000` in func_020500dc (bl). r6 = spell, r7 = target battler, r5 = flags.
# A stage skill moves the target's stat one stage; if that would do nothing, nothing changes and the
# message line says "No effect!". Leaves the flags of the replaced instruction.
FX_ASM = f"""
    push  {{r4, r8, sb, lr}}
    cmp   r6, #{SPELL_COUNT}
    bhs   fx_out
    ldr   sb, fx_table
    add   sb, sb, r6, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [sb, #{FX_KIND}]
    cmp   r0, #{Kind.STAGE}
    bne   fx_out
    mov   r0, r7
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   fx_none
    ldr   r0, fx_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r4, r7, r1, r0
    ldr   r0, [r4, #{BATTLER_RECORD:#x}]
    ldr   r1, fx_records
    ldr   r1, [r1]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r8, r0, r2, r1
    mov   r0, r8
    ldrb  r1, [sb, #{FX_STAT}]
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
fx_none:
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


def _plain(steps: Steps) -> Steps:
    """The cast with no effect: the last blow is an ordinary step (as the blows before it)."""
    return tuple(
        (flags & ~STEP_WAIT_EFFECTS, steps[index - 1][1], slot, anim, frames)
        if word == STEP_START_EFFECTS
        else (flags, word, slot, anim, frames)
        for index, (flags, word, slot, anim, frames) in enumerate(steps)
    )


def _script(steps: Steps) -> str:
    """Action script steps as asm data: two words, then slot, animation, frames, and a pad halfword."""
    return "\n".join(
        f"    .word {flags:#x}, {word:#x}\n    .hword {slot}, {anim}, {frames}, 0"
        for flags, word, slot, anim, frames in steps
    )


# Replaces `bl func_02068308`. r0 = the acting party battler, r1 = mode. After the game's own setup of an
# action (not of a counter, which keeps the queued command and spell), a skill with the ATTACK look gets
# Jian's attack file in slot 0 and its own script: run in (or leap up to a back-row enemy), the combo
# without hits, the effect on the target, back. If the skill would do nothing to the target the cast has no
# effect step at all (no effect helpers are set up, so no banner) and the message line says "No effect!" as
# the cast starts (the round waits for the line to close before the next step, as it does for the game's
# own lines).
ANIM_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
    mov   r5, r1
    bl    {PARTY_SETUP:#x}
    tst   r5, #{SETUP_COUNTER}
    popne {{r4-r6, pc}}
    ldrh  r0, [r4, #{BATTLER_COMMAND:#x}]
    cmp   r0, #{ACTION_SPECIAL}
    popne {{r4-r6, pc}}
    ldrh  r6, [r4, #{T.BATTLER_SPELL:#x}]
    cmp   r6, #{SPELL_COUNT}
    pophs {{r4-r6, pc}}
    ldr   r0, anim_table
    add   r0, r0, r6, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [r0, #{FX_LOOK}]
    cmp   r0, #{Look.ATTACK}
    popne {{r4-r6, pc}}
    ldr   r0, anim_file
    ldrh  r0, [r0]
    ldr   r1, anim_work
    ldr   r1, [r1]
    strh  r0, [r1, #{WORK_SLOT0:#x}]
    adr   r0, anim_script
    ldrsh r1, [r4, #{T.TARGETS:#x}]
    cmp   r1, #{FIRST_FRONT_ENEMY}
    adrlt r0, anim_script_back
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    cmp   r1, #{FIRST_ENEMY}
    poplt {{r4-r6, pc}}
    mov   r0, r1
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    popeq {{r4-r6, pc}}
    adr   r0, anim_plain
    ldrsh r1, [r4, #{T.TARGETS:#x}]
    cmp   r1, #{FIRST_FRONT_ENEMY}
    adrlt r0, anim_plain_back
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    ldr   r1, anim_work
    ldr   r1, [r1]
    mov   r0, #0
    strh  r0, [r1, #{WORK_EFFECT_MODE:#x}]
    mov   r0, #{MESSAGE_NO_EFFECT}
    strh  r0, [r1, #{WORK_MESSAGE:#x}]
    mov   r0, #{MESSAGE_WINDOW:#x}
    mov   r1, #1
    mov   r2, #{MESSAGE_FRAMES:#x}
    bl    {OPEN_WINDOW:#x}
    pop   {{r4-r6, pc}}
anim_table:
    .word ${{cave_skill_fx}}
anim_file:
    .word {JIAN_ATTACK_FILE:#x}
anim_work:
    .word {BATTLE_WORK_PTR:#x}
anim_script:
{_script(JIAN_CAST)}
anim_script_back:
{_script(JIAN_CAST_BACK)}
anim_plain:
{_script(_plain(JIAN_CAST))}
anim_plain_back:
{_script(_plain(JIAN_CAST_BACK))}
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
    CaveCode("cave_skill_effect", FX_ASM, "a stage skill moves the target's stat"),
    hook(
        FX_SITE,
        FX_WORD,
        "bl ${cave_skill_effect}",
        "a stage skill moves the target's stat",
    ),
    CaveCode("cave_skill_msg", MESSAGE_ASM, "the message line can say No effect!"),
    hook(
        MESSAGE_SITE,
        MESSAGE_SITE_WORD,
        "b ${cave_skill_msg}",
        "the message line can say No effect!",
    ),
    CaveCode(
        "cave_skill_anim", ANIM_ASM, "an attack-style skill plays its owner's attack"
    ),
    hook(
        PARTY_SETUP_CALL,
        PARTY_SETUP_CALL_WORD,
        "bl ${cave_skill_anim}",
        "an attack-style skill plays its owner's attack",
    ),
)
