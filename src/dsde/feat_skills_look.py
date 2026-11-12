"""How a learned skill's cast plays (the party action setup, func_02068308).

- A skill with the ATTACK look plays its owner's attack with the hit flags taken out and starts the effect
  row's sprite on the last blow (Jeff: a regular attack, then the effect). Only Jian has such skills so far;
  the scripts are copies of his combo. If the skill would do nothing to the target (the menu refuses a pick
  like that, but the target can change after the pick) the cast has no effect step, so no banner, and the
  message line says "No effect!" as the cast starts.
- A skill on all enemies plays its effect row's own cast, as a card does. Before the setup, the enemies it
  would do nothing to are taken out of the caster's target list, so no banner shows on them and the effect
  never runs for them; if that leaves nobody, the list stays as it is and the line says "No effect!".
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    ACTION_SPECIAL,
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLER_COMMAND,
    BATTLER_SCRIPT,
    FIRST_ENEMY,
    FIRST_FRONT_ENEMY,
    FX_KIND,
    FX_LOOK,
    FX_SIZE_SHIFT,
    MESSAGE_FRAMES,
    MESSAGE_NO_EFFECT,
    MESSAGE_WINDOW,
    OPEN_WINDOW,
    SPELL_ENTRY_SIZE,
    SPELL_TABLE,
    TARGET_BITS,
    WORK_EFFECT_MODE,
    WORK_MESSAGE,
    WORK_SLOT0,
    hook,
)
from dsde.skills_data import SPELL_COUNT, Kind, Look

PARTY_SETUP_CALL = (
    0x020688B4  # func_02068890: `bl func_02068308` (party action setup), r0 = the actor
)
PARTY_SETUP_CALL_WORD = 0xEBFFFE93
PARTY_SETUP = 0x02068308  # (actor, mode)
SETUP_COUNTER = (
    1  # mode bit: the actor's counterattack, set up in slots 3 to 5 with its own script
)
JIAN_ATTACK_FILE = 0x020953D4 + 4  # character table, Jian: the 3-hit combo's file
TARGET_SLOTS = 8  # s16 battler indices at battler + TARGETS, -1 = empty

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


# Asm that says "No effect!" on the message line; clobbers r0 to r3, ip, lr. The round waits for the line
# to close before the script's next step, as it does for the game's own lines.
_NO_EFFECT_LINE = f"""
    ldr   r1, anim_work
    ldr   r1, [r1]
    mov   r0, #{MESSAGE_NO_EFFECT}
    strh  r0, [r1, #{WORK_MESSAGE:#x}]
    mov   r0, #{MESSAGE_WINDOW:#x}
    mov   r1, #1
    mov   r2, #{MESSAGE_FRAMES:#x}
    bl    {OPEN_WINDOW:#x}"""

# Replaces `bl func_02068308`. r0 = the acting party battler, r1 = mode. A counter (which keeps the queued
# command and spell) is set up untouched. Before the game's setup an all-enemy skill's target list is
# pruned (anim_prune); after it, a skill with the ATTACK look gets Jian's attack file in slot 0 and its own
# script: run in (or leap up to a back-row enemy), the combo without hits, the effect on the target, back,
# or the same with no effect step when the skill would do nothing.
ANIM_ASM = f"""
    push  {{r4-r8, lr}}
    mov   r4, r0
    mov   r5, r1
    mvn   r6, #0
    tst   r5, #{SETUP_COUNTER}
    bne   anim_setup
    ldrh  r0, [r4, #{BATTLER_COMMAND:#x}]
    cmp   r0, #{ACTION_SPECIAL}
    bne   anim_setup
    ldrh  r0, [r4, #{T.BATTLER_SPELL:#x}]
    cmp   r0, #{SPELL_COUNT}
    bhs   anim_setup
    mov   r6, r0
    ldr   r7, anim_table
    add   r7, r7, r6, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [r7, #{FX_KIND}]
    cmp   r0, #{Kind.NONE}
    mvneq r6, #0
    beq   anim_setup
    ldr   r0, anim_spells
    mov   r1, #{SPELL_ENTRY_SIZE:#x}
    mul   r2, r6, r1
    ldr   r0, [r0, r2]
    and   r0, r0, #{TARGET_BITS:#x}
    cmp   r0, #{ALL_TARGETS:#x}
    bne   anim_setup
    bl    anim_prune
anim_setup:
    mov   r0, r4
    mov   r1, r5
    bl    {PARTY_SETUP:#x}
    cmn   r6, #1
    popeq {{r4-r8, pc}}
    ldrb  r0, [r7, #{FX_LOOK}]
    cmp   r0, #{Look.ATTACK}
    popne {{r4-r8, pc}}
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
    poplt {{r4-r8, pc}}
    mov   r0, r1
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    popeq {{r4-r8, pc}}
    adr   r0, anim_plain
    ldrsh r1, [r4, #{T.TARGETS:#x}]
    cmp   r1, #{FIRST_FRONT_ENEMY}
    adrlt r0, anim_plain_back
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    ldr   r1, anim_work
    ldr   r1, [r1]
    mov   r0, #0
    strh  r0, [r1, #{WORK_EFFECT_MODE:#x}]
{_NO_EFFECT_LINE}
    pop   {{r4-r8, pc}}

anim_prune:
    push  {{sb, lr}}
    mov   r2, #0
    mov   r8, #0
prune_loop:
    add   r0, r4, r8, lsl #1
    ldrsh sb, [r0, #{T.TARGETS:#x}]
    cmn   sb, #1
    beq   prune_next
    push  {{r2, r3}}
    mov   r0, sb
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    pop   {{r2, r3}}
    cmp   r0, #0
    bne   prune_next
    add   r0, r4, r2, lsl #1
    strh  sb, [r0, #{T.TARGETS:#x}]
    add   r2, r2, #1
prune_next:
    add   r8, r8, #1
    cmp   r8, #{TARGET_SLOTS}
    blt   prune_loop
    cmp   r2, #0
    beq   prune_nobody
    mvn   r1, #0
prune_fill:
    cmp   r2, #{TARGET_SLOTS}
    popge {{sb, pc}}
    add   r0, r4, r2, lsl #1
    strh  r1, [r0, #{T.TARGETS:#x}]
    add   r2, r2, #1
    b     prune_fill
prune_nobody:
{_NO_EFFECT_LINE}
    pop   {{sb, pc}}

anim_table:
    .word ${{cave_skill_fx}}
anim_spells:
    .word {SPELL_TABLE:#x}
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

LOOK_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_anim", ANIM_ASM, "how a skill's cast plays"),
    hook(
        PARTY_SETUP_CALL,
        PARTY_SETUP_CALL_WORD,
        "bl ${cave_skill_anim}",
        "how a skill's cast plays",
    ),
)
