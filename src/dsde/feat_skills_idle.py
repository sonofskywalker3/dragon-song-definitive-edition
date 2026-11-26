"""Would a skill do nothing? One test for every hook, and the menu's refusal.

Jeff's rule: a cast that would change nothing is refused before it is made, with "No effect!" on the name
bar and no MP taken. What "nothing" means depends on the skill's kind (skills_data.Kind):

- STAGE: the stat is already a stage past 0 in the skill's direction (2 stages for a cast a worn card
  enhances: the boost state's limit, feat_skills_boost.py);
- STATUS: the target already has a status (a battler has one at a time), or it is a boss row and the
  status is one a boss never takes (the game's rule in func_020500dc: row flags bit 31 with status 1, 3, 4,
  5, or 7);
- FLAG: the battle-wide flag is already set.

`cave_skill_idle` answers for one battler; the enemy grid calls it as its veto, the one-enemy path, the
ally picker, and the effect hooks call it directly. `cave_skill_idle_all` answers for a spell with no
picker: an all-enemy spell is idle when every living enemy is, an all-ally spell when every living ally
is, anything else when the caster is. `cave_skill_refuse` is the shared
refusal the Special list's handlers end in.
"""

from dsde import targeting_consts as T
from dsde.feat_skills_boost import STATE_LIMIT
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLER_ENEMY,
    BATTLER_RECORD,
    BATTLER_ROW,
    BATTLER_SIZE,
    BATTLERS_PTR,
    FX_ARG,
    FX_DELTA,
    FX_KIND,
    FX_SIZE_SHIFT,
    OPEN_WINDOW,
    RECORD_SIZE,
    RECORD_STAGES,
    RECORD_STATUS,
    RECORDS_PTR,
    SPELL_ENTRY_SIZE,
    SPELL_TABLE,
    STATUS_MASK,
    STRING_NO_EFFECT,
    TARGET_BITS,
    hook,
)
from dsde.skills_data import BOSS_IMMUNE, SPELL_COUNT, Kind

ENEMY_ROWS = 0x02097CE4  # enemy table, 0x54 per row; the first word is the row's flags
ENEMY_ROW_SIZE = 0x54
ROW_BOSS = 0x80000000  # row flag: a boss (rows 136 to 156)
PARTY_SLOTS = 3  # party battlers are 0..2
IMMUNE_MASK = sum(1 << status for status in BOSS_IMMUNE)  # bit n: status n

# The Special list's OK handler, where a spell with no picker (all enemies, all allies) ends the member's
# command: `ldr r2, [pc, #0x97c]` (the menu), reached for target bits 0x40000000 and 0xC0000000
LIST_OK_GROUP = 0x02036D20
LIST_OK_GROUP_WORD = 0xE59F297C
LIST_OK_GROUP_NEXT = 0x02036D24

# r0 = battler index, r1 = spell -> r0 = 0 if the spell would change something on that battler, else the
# battle string to show ("No effect!"). Clobbers r1 to r3 and ip only (the grid calls it as its veto).
IDLE_ASM = f"""
    cmp   r1, #{SPELL_COUNT}
    bhs   idle_fine
    ldr   r2, idle_fx
    add   r2, r2, r1, lsl #{FX_SIZE_SHIFT}
    ldrb  r3, [r2, #{FX_KIND}]
    cmp   r3, #{Kind.NONE}
    beq   idle_fine
    cmp   r3, #{Kind.HIT}
    beq   idle_fine
    cmp   r3, #{Kind.FLAG}
    beq   idle_flag
    ldr   ip, idle_battlers
    ldr   ip, [ip]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r0, r1, r0, ip
    cmp   r3, #{Kind.STATUS}
    beq   idle_status
    ldr   r0, [r0, #{BATTLER_RECORD:#x}]
    ldr   r3, idle_records
    ldr   r3, [r3]
    mov   ip, #{RECORD_SIZE:#x}
    mla   r0, ip, r0, r3
    ldrb  r3, [r2, #{FX_ARG}]
    add   r0, r0, r3, lsl #1
    ldrsh r0, [r0, #{RECORD_STAGES:#x}]
    ldrsb r3, [r2, #{FX_DELTA}]
    cmp   r3, #0
    rsblt r0, r0, #0
    ldr   ip, idle_state
    ldrb  ip, [ip, #{STATE_LIMIT}]
    cmp   r0, ip
    bge   idle_none
idle_fine:
    mov   r0, #0
    bx    lr
idle_status:
    ldr   r3, [r0, #{BATTLER_RECORD:#x}]
    ldr   r1, idle_records
    ldr   r1, [r1]
    mov   ip, #{RECORD_SIZE:#x}
    mla   r3, ip, r3, r1
    ldr   r3, [r3, #{RECORD_STATUS:#x}]
    tst   r3, #{STATUS_MASK:#x}
    bne   idle_none
    ldr   r1, [r0]
    tst   r1, #{BATTLER_ENEMY}
    beq   idle_fine
    ldr   r1, [r0, #{BATTLER_ROW:#x}]
    ldr   r3, idle_rows
    mov   ip, #{ENEMY_ROW_SIZE:#x}
    mla   r1, ip, r1, r3
    ldr   r1, [r1]
    tst   r1, #{ROW_BOSS:#x}
    beq   idle_fine
    ldrb  r1, [r2, #{FX_ARG}]
    mov   r3, #1
    lsl   r3, r3, r1
    tst   r3, #{IMMUNE_MASK:#x}
    beq   idle_fine
idle_none:
    mov   r0, #{STRING_NO_EFFECT}
    bx    lr
idle_flag:
    ldr   r0, idle_work
    ldr   r0, [r0]
    ldr   r0, [r0]
    ldrb  r3, [r2, #{FX_ARG}]
    tst   r0, r3
    bne   idle_none
    b     idle_fine
idle_fx:
    .word ${{cave_skill_fx}}
idle_battlers:
    .word {BATTLERS_PTR:#x}
idle_records:
    .word {RECORDS_PTR:#x}
idle_rows:
    .word {ENEMY_ROWS:#x}
idle_work:
    .word {BATTLE_WORK_PTR:#x}
idle_state:
    .word ${{cave_skill_boost}}
"""

# r0 = the caster's battler index, r1 = spell -> r0 as cave_skill_idle, for a spell cast with no picker.
# An all-enemy spell is idle when every living enemy is, an all-ally spell when every living ally is
# (with nobody alive it is let through); any other spell is judged on the caster.
IDLE_ALL_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
    mov   r5, r1
    cmp   r5, #{SPELL_COUNT}
    bhs   all_fine
    ldr   r0, all_spells
    mov   r1, #{SPELL_ENTRY_SIZE:#x}
    mul   r2, r5, r1
    ldr   r0, [r0, r2]
    and   r0, r0, #{TARGET_BITS:#x}
    cmp   r0, #{ALL_TARGETS:#x}
    beq   all_enemies
    cmp   r0, #{TARGET_BITS:#x}
    beq   all_allies
    mov   r0, r4
    mov   r1, r5
    bl    ${{cave_skill_idle}}
    pop   {{r4-r6, pc}}
all_enemies:
    mvn   r6, #0
all_loop:
    mov   r0, r6
    mov   r1, #{T.ROWS_ANY}
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    blt   all_done
    mov   r6, r0
    mov   r1, r5
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   all_loop
all_fine:
    mov   r0, #0
    pop   {{r4-r6, pc}}
all_done:
    cmn   r6, #1
    moveq r0, #0
    movne r0, #{STRING_NO_EFFECT}
    pop   {{r4-r6, pc}}
all_allies:
    mov   r6, #0
    mov   r4, #0
allies_loop:
    ldr   r0, all_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r0, r1, r6, r0
    bl    {T.BATTLER_ALIVE:#x}
    cmp   r0, #0
    ble   allies_next
    add   r4, r4, #1
    mov   r0, r6
    mov   r1, r5
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    beq   all_fine
allies_next:
    add   r6, r6, #1
    cmp   r6, #{PARTY_SLOTS}
    blt   allies_loop
    cmp   r4, #0
    moveq r0, #0
    movne r0, #{STRING_NO_EFFECT}
    pop   {{r4-r6, pc}}
all_spells:
    .word {SPELL_TABLE:#x}
all_battlers:
    .word {BATTLERS_PTR:#x}
"""

# Entered by `b` from a Special list handler with r0 = the battle string to show and r6 = the menu. The
# name bar shows it for a second, as the game's own "Cannot use!" (func_02035128), the refuse sound plays,
# and the list stays up: r5 = 0 keeps the cursor corners, as the game's refusal at 0x02036B18 does.
REFUSE_ASM = f"""
    str   r0, [r6, #{T.MENU_BAR_STRING:#x}]
    mov   r0, #{T.BAR_FRAMES:#x}
    str   r0, [r6, #{T.MENU_BAR_FRAMES:#x}]
    mov   r0, #0
    str   r0, [r6, #{T.MENU_BAR_TIMER_RESET:#x}]
    mov   r1, #1
    mvn   r2, #0
    bl    {OPEN_WINDOW:#x}
    mov   r0, #{T.SOUND_REFUSE}
    bl    {T.PLAY_SOUND:#x}
    mov   r5, #0
    b     {T.BUTTON_EPILOGUE:#x}
"""

# Replaces `ldr r2, [pc, #0x97c]` (b) where the Special list ends the command for a spell with no picker.
# The handler's r4, r5, and r7 go on; r6 is free (the block sets it). A spell that would do nothing is
# refused; otherwise the replaced load and on.
GROUP_ASM = f"""
    ldr   r6, group_menu
    ldrh  r0, [r6, #{T.MENU_MEMBER:#x}]
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    bl    ${{cave_skill_idle_all}}
    cmp   r0, #0
    bne   ${{cave_skill_refuse}}
    ldr   r2, group_menu
    b     {LIST_OK_GROUP_NEXT:#x}
group_menu:
    .word {T.MENU:#x}
"""

IDLE_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode(
        "cave_skill_idle", IDLE_ASM, "would this spell do nothing to this battler"
    ),
    CaveCode(
        "cave_skill_idle_all", IDLE_ALL_ASM, "would this spell do nothing to anyone"
    ),
    CaveCode("cave_skill_refuse", REFUSE_ASM, "the Special list refuses a wasted cast"),
    CaveCode("cave_skill_group", GROUP_ASM, "a wasted all-target spell is refused"),
    hook(
        LIST_OK_GROUP,
        LIST_OK_GROUP_WORD,
        "b ${cave_skill_group}",
        "a wasted all-target spell is refused",
    ),
)
