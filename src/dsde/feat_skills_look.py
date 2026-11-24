"""How a learned skill's cast plays (the party action setup, func_02068308).

- A skill with the ATTACK look plays its owner's attack with the hit flags taken out and starts the effect
  row's sprite on the last blow (Jeff: a regular attack, then the effect). Jian's scripts are copies of his
  combo; the other fighters' are copies of the single attack the game gives everyone else. If the skill
  would do nothing to the target (the menu refuses a pick like that, but the target can change after the
  pick) the cast has no effect step, so no banner, and the message line says "No effect!" as the cast
  starts.
- A skill with the ROW look plays its effect row's own cast, which is written for the pose a character
  takes to use an item or a card; a spell gets the character's Special file instead, so the pose file is put
  back in its place.
- A skill with the SPELL look is left as the game set it up: the effect row's cast in the caster's
  Special pose, which is how a healer's own spells play.
- A skill can name a sprite of its own: it goes in the effect sprite slot in place of the row's, and the
  row's effect script plays it (Flora's water ribbon on the status row, whose script plays animation 0).
- A skill with the THROW look (Stone Throw) is Jian's unused throw (btldata 15) played where he stands: he
  tosses the stone, then bats it as he swings, and the swing starts the stone (the skill's sprite) flying at
  the target on the effect script of Flora's arrows, in the game's projectile mode, whose hit step deals his
  ordinary attack's damage.
- A skill with the CLAW look (Savage Rush) is Gabryel's unused double claw (btldata 33): she runs in (or
  leaps up to a back-row enemy) as for her attack, winds up, and swipes twice, each swipe an ordinary hit,
  so it deals two of her Fight's blows.
- A skill on all enemies or all allies plays its effect row's own cast, as a card does. Before the setup,
  the targets it would do nothing to are taken out of the caster's target list, so no banner shows on them
  and the effect never runs for them; if that leaves nobody, the list stays as it is and the line says
  "No effect!".
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    ACTION_SPECIAL,
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLER_COMMAND,
    BATTLER_ROW,
    BATTLER_SCRIPT,
    CHARACTER_FILES,
    CHARACTER_FILES_SIZE,
    FILE_ATTACK,
    FILE_ITEM_POSE,
    FIRST_ENEMY,
    FIRST_FRONT_ENEMY,
    FX_KIND,
    FX_LOOK,
    FX_SIZE_SHIFT,
    FX_SPRITE,
    MESSAGE_FRAMES,
    MESSAGE_NO_EFFECT,
    MESSAGE_WINDOW,
    OPEN_WINDOW,
    SPELL_ENTRY_SIZE,
    SPELL_TABLE,
    WORK_EFFECT_MODE,
    WORK_EFFECT_SCRIPTS,
    WORK_EFFECT_SPRITE,
    WORK_MESSAGE,
    WORK_SLOT0,
    hook,
)
from dsde.skills_data import JIAN, SPELL_COUNT, Kind, Look

PARTY_SETUP_CALL = (
    0x020688B4  # func_02068890: `bl func_02068308` (party action setup), r0 = the actor
)
PARTY_SETUP_CALL_WORD = 0xEBFFFE93
PARTY_SETUP = 0x02068308  # (actor, mode)
SETUP_COUNTER = (
    1  # mode bit: the actor's counterattack, set up in slots 3 to 5 with its own script
)
TARGET_SLOTS = 8  # s16 battler indices at battler + TARGETS, -1 = empty
THROW_FILE = (
    15  # Jian's unused throw: animation 0 tosses the stone up, animation 1 swings at it
)
CLAW_FILE = 33  # Gabryel's unused double claw: animation 0 the wind-up, 1 a swipe with white arcs
EFFECT_NONE = 0  # effect mode: no effect helpers this action, as for Fight
EFFECT_PROJECTILE = 1  # effect mode: each effect starts on a helper at the caster and flies (Flora's arrows)
ARROW_FLIGHT = (
    0x02094EE4  # effect script of Flora's arrows: 16 frames to the target, then the hit
)

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


# The other fighters' attack: the single blow of 0x020958C0 (front row) and 0x020954F0 (the leap at a
# back-row enemy), its hit (0xC0) gone and the blow starting and waiting for the effects
FIGHTER_CAST: Steps = (
    (0x00200001, 0x00000000, 1, 0, 0),
    (0x00001016, 0x00030000, 1, 1, 6),
    (0x00000012, 0x00000000, 1, 2, 6),
    (0x00000001, 0x00000000, 1, 3, 0),
    (0x00000001, 0x00000000, 0, 0, 0),
    (0x00000001, 0x00010000, 0, 1, 0),
    (0x00000001 | STEP_WAIT_EFFECTS, STEP_START_EFFECTS, 0, 2, 0),
    (0x00000001, 0x00000000, 1, 0, 0),
    (0x04009016, 0x00030000, 1, 2, 8),
    (0x04000012, 0x00000000, 1, 1, 8),
    (0x80000001, 0x00000000, 1, 3, 0),
)
FIGHTER_CAST_BACK: Steps = (
    (0x00300001, 0x00000000, 1, 0, 0),
    (0x00001012, 0x00030000, 1, 1, 10),
    (0x00000001, 0x00000000, 0, 0, 0),
    (0x00000001, 0x00010000, 0, 1, 0),
    (0x00000001 | STEP_WAIT_EFFECTS, STEP_START_EFFECTS, 0, 2, 0),
    (0x04009012, 0x00000000, 1, 2, 10),
    (0x80000001, 0x00000000, 1, 3, 0),
)
# Jian's throw: the toss, then the swing, which starts the stone and waits for it to land
JIAN_THROW: Steps = (
    (0x00000001, 0x00000000, 0, 0, 0),
    (0x80000001 | STEP_WAIT_EFFECTS, 0x00010000 | STEP_START_EFFECTS, 0, 1, 0),
)
# Gabryel's double claw: her attack's run in and back (0x020958C0, 0x020954F0 at a back-row enemy), with the
# blow the wind-up and two swipes, each with the hit flag (0x40) and its own sound. The last keeps the 0x80
# of the game's single hit (hand over to a follow-up actor).
STEP_HIT = 0x00000041
STEP_LAST_HIT = 0x000000C1
CLAW_BLOWS: Steps = (
    (0x00000001, 0x00000000, 0, 0, 0),
    (STEP_HIT, 0x00010000, 0, 1, 0),
    (STEP_LAST_HIT, 0x00010000, 0, 1, 0),
)
CLAW_CAST: Steps = (
    *FIGHTER_CAST[:4],
    *CLAW_BLOWS,
    *FIGHTER_CAST[7:],
)
CLAW_CAST_BACK: Steps = (
    *FIGHTER_CAST_BACK[:2],
    *CLAW_BLOWS,
    *FIGHTER_CAST_BACK[5:],
)
# Index into anim_scripts: these bits added up
SCRIPT_PLAIN = 1  # no effect step
SCRIPT_BACK = 2  # the target is in the back row
SCRIPT_FIGHTER = 4  # not Jian


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
# command and spell) is set up untouched. Before the game's setup an all-target skill's target list is
# pruned (anim_prune). After it, a skill's own effect sprite replaces the row's, a skill with the SPELL
# look is otherwise left alone, a skill with the ROW look gets its caster's item pose file in slot 0, and
# a skill with the ATTACK look its caster's attack file and its own script: run in (or leap up to a
# back-row enemy), the attack without hits, the effect on the target, back, or the same with no effect step
# when the skill would do nothing.
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
    tst   r0, #{ALL_TARGETS:#x}
    beq   anim_setup
    bl    anim_prune
anim_setup:
    mov   r0, r4
    mov   r1, r5
    bl    {PARTY_SETUP:#x}
    cmn   r6, #1
    popeq {{r4-r8, pc}}
    ldr   r8, [r4, #{BATTLER_ROW:#x}]
    ldr   r0, anim_files
    mov   r1, #{CHARACTER_FILES_SIZE:#x}
    mla   r2, r1, r8, r0
    ldr   r3, anim_work
    ldr   r3, [r3]
    ldrh  r0, [r7, #{FX_SPRITE}]
    cmp   r0, #0
    strhne r0, [r3, #{WORK_EFFECT_SPRITE:#x}]
    ldrb  r0, [r7, #{FX_LOOK}]
    cmp   r0, #{Look.SPELL}
    popeq {{r4-r8, pc}}
    cmp   r0, #{Look.THROW}
    beq   anim_throw_setup
    cmp   r0, #{Look.CLAW}
    beq   anim_claw_setup
    cmp   r0, #{Look.ATTACK}
    ldrhne r0, [r2, #{FILE_ITEM_POSE:#x}]
    strhne r0, [r3, #{WORK_SLOT0:#x}]
    popne {{r4-r8, pc}}
    ldrh  r0, [r2, #{FILE_ATTACK:#x}]
    strh  r0, [r3, #{WORK_SLOT0:#x}]
    cmp   r8, #{JIAN}
    moveq r8, #0
    movne r8, #{SCRIPT_FIGHTER}
    ldrsh r1, [r4, #{T.TARGETS:#x}]
    cmp   r1, #{FIRST_FRONT_ENEMY}
    addlt r8, r8, #{SCRIPT_BACK}
    adr   r0, anim_scripts
    ldr   r0, [r0, r8, lsl #2]
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    cmp   r1, #{FIRST_ENEMY}
    poplt {{r4-r8, pc}}
    mov   r0, r1
    mov   r1, r6
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    popeq {{r4-r8, pc}}
    add   r8, r8, #{SCRIPT_PLAIN}
    adr   r0, anim_scripts
    ldr   r0, [r0, r8, lsl #2]
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    ldr   r1, anim_work
    ldr   r1, [r1]
    mov   r0, #0
    strh  r0, [r1, #{WORK_EFFECT_MODE:#x}]
{_NO_EFFECT_LINE}
    pop   {{r4-r8, pc}}

anim_throw_setup:
    mov   r0, #{THROW_FILE}
    strh  r0, [r3, #{WORK_SLOT0:#x}]
    mov   r0, #{EFFECT_PROJECTILE}
    strh  r0, [r3, #{WORK_EFFECT_MODE:#x}]
    ldr   r0, anim_throw_at
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
    ldr   r1, anim_flight
    mov   r2, #0
throw_loop:
    add   r0, r4, r2, lsl #1
    ldrsh r0, [r0, #{T.TARGETS:#x}]
    cmn   r0, #1
    addne r0, r3, r2, lsl #2
    strne r1, [r0, #{WORK_EFFECT_SCRIPTS:#x}]
    add   r2, r2, #1
    cmp   r2, #{TARGET_SLOTS}
    blt   throw_loop
    pop   {{r4-r8, pc}}

anim_claw_setup:
    mov   r0, #{CLAW_FILE}
    strh  r0, [r3, #{WORK_SLOT0:#x}]
    mov   r0, #{EFFECT_NONE}
    strh  r0, [r3, #{WORK_EFFECT_MODE:#x}]
    ldrsh r1, [r4, #{T.TARGETS:#x}]
    cmp   r1, #{FIRST_FRONT_ENEMY}
    ldrge r0, anim_claw_at
    ldrlt r0, anim_claw_back_at
    str   r0, [r4, #{BATTLER_SCRIPT:#x}]
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
anim_files:
    .word {CHARACTER_FILES:#x}
anim_work:
    .word {BATTLE_WORK_PTR:#x}
anim_throw_at:
    .word anim_throw
anim_flight:
    .word {ARROW_FLIGHT:#x}
anim_claw_at:
    .word anim_claw
anim_claw_back_at:
    .word anim_claw_back
anim_scripts:
    .word anim_jian, anim_jian_plain, anim_jian_back, anim_jian_back_plain
    .word anim_fighter, anim_fighter_plain, anim_fighter_back, anim_fighter_back_plain
anim_jian:
{_script(JIAN_CAST)}
anim_jian_plain:
{_script(_plain(JIAN_CAST))}
anim_jian_back:
{_script(JIAN_CAST_BACK)}
anim_jian_back_plain:
{_script(_plain(JIAN_CAST_BACK))}
anim_fighter:
{_script(FIGHTER_CAST)}
anim_fighter_plain:
{_script(_plain(FIGHTER_CAST))}
anim_fighter_back:
{_script(FIGHTER_CAST_BACK)}
anim_fighter_back_plain:
{_script(_plain(FIGHTER_CAST_BACK))}
anim_throw:
{_script(JIAN_THROW)}
anim_claw:
{_script(CLAW_CAST)}
anim_claw_back:
{_script(CLAW_CAST_BACK)}
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
