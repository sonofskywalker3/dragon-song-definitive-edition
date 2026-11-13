"""The battle menu side of the learned skills: listing, casting, and picking the one enemy.

- Special opens the spell list for every character (in the original only Lucia and Flora get it; the others
  get a one-spell panel and are refused with two spells or more), unless the list would be empty.
- The fighters' branches of "is this spell listed" (func_02050c50) take a learn level from
  cave_skill_levels: Jian's in place of a ring, Gabryel's beside her Gale Cut. Jian's branch of "can it be
  cast" (func_02050a74) lets a spell with no ring bit through; the others' already cast whatever is listed.
  MP is charged by the game's own Special path.
- A skill cast on its caster alone (skills_data.Skill.self_only) skips the ally picker.
- A spell on one enemy opens the Fight grid (feat_targeting_*.py) in spell mode and is cast on the enemy
  picked there; the original lets the game pick at random. A pick that would do nothing is refused with "No
  effect!" on the name bar: the grid asks the veto routine this module leaves in the picker's state
  (feat_skills_idle.py), so the targeting feature knows nothing about spells.

The name bar's ailment tags for the grid are in feat_skills_tags.py.
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.feat_skills_table import LEVEL_ROWS
from dsde.skills_common import (
    CHARACTER_RECORD_SIZE,
    FIRST_ENEMY,
    FX_SELF,
    FX_SIZE_SHIFT,
    LAST_ENEMY,
    LEVEL_INDEX,
    NEVER,
    RING_FLAGS,
    SPELL_TABLE,
    hook,
)
from dsde.skills_data import GABRYEL, JIAN, SPELL_COUNT

# func_02050c50's branches by character (r5): each starts with `mov r0, #0xc` and goes on to its own test
# (Jian's rings, Gabryel's flag 0x200 for Gale Cut)
LIST_JIAN = 0x02050D24
LIST_GABRYEL = 0x02050DA8
LIST_BRANCHES = {JIAN: LIST_JIAN, GABRYEL: LIST_GABRYEL}
LIST_TAIL = 0x02050DDC  # `cmp r6, #1`: listed, then the max MP test
CAST_JIAN = 0x02050AF8  # func_02050a74, Jian branch: `mov r0, #0xc`
CAST_RING_TESTS = 0x02050B08  # with r4 = flags
CAST_MP_TEST = 0x02050B88  # `cmp r7, #1`
MOV_R0_12 = 0xE3A0000C

LIST_GATE = 0x020369F4  # `bne 0x02036AB0` after `cmp r0, #3` (the character id)
LIST_GATE_WORD = 0x1A00002D
BUILD_SPELL_LIST = 0x02035E00  # (2) -> 1 if the list has entries
LIST_PAGE_BUILT = 0x02036A00  # the healers' path, after its own BUILD_SPELL_LIST call
SPECIAL_REFUSED = 0x02036B18  # "Cannot use!"

LIST_OK_ENEMY = (
    0x02036CFC  # Special list OK, target bits 0: `beq 0x02036D20` (end the command)
)
LIST_OK_ENEMY_WORD = 0x0A000007
LIST_OK_DONE = 0x02036E18  # plays the menu sound, then the button epilogue (r5, r7 as the handler left them)
LIST_OK_ALLY = 0x02036D10  # Special list OK, target bits 0x80000000: `beq 0x02036D88` (the ally picker)
LIST_OK_ALLY_WORD = 0x0A00001C
ALLY_PICKER = 0x02036D88
MEMBER_DONE = 0x020377F0  # slides the page out when a member's command ends
CLOSE_DESCRIPTION = 0x02039570  # (0)
SPELL_BUTTON = 4  # the Special list's own button, slid out when leaving the page
RESOLVE_ENEMY = 0x02051D34  # func_020514ec, party Special on one enemy: `bl func_02050f78` with (3, 0)
RESOLVE_ENEMY_WORD = 0xEBFFFC8F
AUTO_TARGET = 0x02050F78
AUTO_ANY_ENEMY = 3

# Everyone's Special goes to the list page, unless the list would be empty (Jian with a ring he owns but
# does not wear passes the "has a spell" test and lists nothing).
GATE_ASM = f"""
    mov   r0, #2
    bl    {BUILD_SPELL_LIST:#x}
    cmp   r0, #0
    beq   {SPECIAL_REFUSED:#x}
    b     {LIST_PAGE_BUILT:#x}
"""


def _row_bytes() -> str:
    """Row of cave_skill_levels per character id, 255 for a character with no row."""
    rows = [NEVER] * (max(LEVEL_ROWS) + 1)
    for row, owner in enumerate(LEVEL_ROWS):
        rows[owner] = row
    return ", ".join(str(row) for row in rows)


def _back(owner: int) -> str:
    """Asm that returns to a character's own branch, past the instruction the hook replaced."""
    return f"""
    cmp   r5, #{owner}
    beq   {LIST_BRANCHES[owner] + 4:#x}"""


# Replaces `mov r0, #0xc` at the top of a fighter's branch of func_02050c50. r5 = character, r8 = spell,
# r7 = 0 in the field, r6 = listed so far (0). A spell with a level in the fighter's row is listed in battle
# from that level; any other spell goes on to the branch's own test.
LIST_ASM = f"""
    cmp   r7, #0
    beq   list_vanilla
    adr   r0, list_rows
    ldrb  r0, [r0, r5]
    mov   r1, #{SPELL_COUNT}
    mul   r0, r1, r0
    ldr   r1, list_levels
    add   r0, r0, r1
    ldrb  r0, [r0, r8]
    cmp   r0, #{NEVER}
    beq   list_vanilla
    ldr   r1, list_level
    mov   r2, #{CHARACTER_RECORD_SIZE:#x}
    mul   r3, r5, r2
    ldr   r1, [r1, r3]
    cmp   r1, r0
    movhs r6, #1
    b     {LIST_TAIL:#x}
list_vanilla:
    mov   r0, #0xc{"".join(_back(owner) for owner in LIST_BRANCHES)}
    b     {LIST_TAIL:#x}
list_level:
    .word {LEVEL_INDEX:#x}
list_levels:
    .word ${{cave_skill_levels}}
list_rows:
    .byte {_row_bytes()}
    .align 2
"""

# Replaces `mov r0, #0xc` at the top of Jian's branch of func_02050a74. sb = spell, r7 = -1. A listed
# spell with no ring bit needs no ring; the MP test follows as for any spell.
CAST_ASM = f"""
    mov   r0, #0xc
    mul   r1, sb, r0
    ldr   r0, cast_table
    ldr   r4, [r0, r1]
    tst   r4, #{RING_FLAGS:#x}
    bne   {CAST_RING_TESTS:#x}
    mov   r7, #1
    b     {CAST_MP_TEST:#x}
cast_table:
    .word {SPELL_TABLE:#x}
"""


def _slide_out(button: str) -> str:
    """Asm that slides the menu button whose index is in the register `button` out; clobbers r0..r3, ip."""
    return f"""
    ldr   r0, open_buttons
    ldr   r0, [r0]
    mov   r2, #{T.BUTTON_SIZE}
    mla   r0, {button}, r2, r0
    mov   r1, #0
    mov   r2, #0
    bl    {T.SLIDE_BUTTON:#x}"""


# Entered by `beq` from the Special list's OK handler for a spell that targets one enemy. The handler's
# r4, r5, and r7 go on to its epilogue; r6, r8, sb, and sl are free (its one-ally branch uses them).
# One enemy alive: it is the target and the command ends as in vanilla, or, if the spell would do nothing
# to it, it is refused (cave_skill_refuse) and the list stays up. The menu's list is left alone in that case: filling the grid here left the description
# window open and empty. Several enemies: the Special list's rows slide out as they do for the ally picker
# and the enemy grid opens in spell mode, with our veto routine in the picker's state.
OPEN_ASM = f"""
    ldr   r6, open_menu
    ldrh  r0, [r6, #{T.MENU_MEMBER:#x}]
    ldr   r1, open_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r8, r0, r2, r1
    mvn   r0, #0
    strh  r0, [r8, #{T.TARGETS:#x}]
    mov   r1, #{T.ROWS_ANY}
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    blt   open_end
    mov   sb, r0
    mov   r1, #{T.ROWS_ANY}
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    bge   open_grid
    mov   r0, sb
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   ${{cave_skill_refuse}}
    strh  sb, [r8, #{T.TARGETS:#x}]
open_end:
    b     ${{cave_skill_done}}
open_grid:
    mov   r0, #0
    bl    {CLOSE_DESCRIPTION:#x}
    mov   r0, #{T.ROWS_ANY}
    bl    ${{cave_tgt_fill}}
    mov   sb, #{SPELL_BUTTON}
{_slide_out("sb")}
    mov   r0, #0
    bl    {T.OK_BACK_SLIDE:#x}
    mov   sl, #0
open_rows:
    add   sb, sl, #{T.FIRST_DOT_BUTTON}
{_slide_out("sb")}
    add   sb, sl, #{T.FIRST_ROW_BUTTON}
{_slide_out("sb")}
    add   sl, sl, #1
    cmp   sl, #{T.LIST_ROWS}
    blt   open_rows
    mov   r0, #0
    str   r0, [r6, #{T.MENU_FIRST_SHOWN:#x}]
    strh  r0, [r6, #{T.MENU_ROW_STYLE:#x}]
    ldr   r1, open_state
    ldrb  r0, [r1, #{T.STATE_FIRST}]
    str   r0, [r6, #{T.MENU_HIGHLIGHT:#x}]
    mov   r0, #{T.NO_DESCRIPTION}
    str   r0, [r6, #{T.MENU_DESCRIPTION:#x}]
    mov   r0, #0
    bl    {T.LIST_DOTS_AND_LABELS:#x}
    mov   r0, #{T.PAGE_LIST}
    strh  r0, [r6, #{T.MENU_NEXT_PAGE:#x}]
    ldr   r0, [r6]
    orr   r0, r0, #{T.MENU_REBUILD}
    str   r0, [r6]
    mvn   r0, #0
    mov   r1, #{T.GROUP_LIST:#x}
    bl    {T.CLEAR_GROUP_HIGHLIGHT:#x}
    ldr   r1, open_state
    mov   r0, #{T.MODE_SPELL}
    strb  r0, [r1, #{T.STATE_MODE}]
    mvn   r0, #0
    strb  r0, [r1, #{T.STATE_LAST_TAP}]
    ldr   r0, open_idle
    str   r0, [r1, #{T.STATE_VETO}]
    b     {LIST_OK_DONE:#x}
open_menu:
    .word {T.MENU:#x}
open_battlers:
    .word {T.BATTLERS_PTR:#x}
open_buttons:
    .word {T.BUTTONS_PTR:#x}
open_state:
    .word ${{cave_tgt_state}}
open_idle:
    .word ${{cave_skill_idle}}
"""

# Entered by `b` with r6 = the menu and r8 = the member's battler, its first target slot already set: ends
# the member's command as a Special with the list's spell, the way the list's own handler does (0x02036D20),
# but leaving the target alone.
DONE_ASM = f"""
    ldrh  r0, [r6, #{T.MENU_SPELL:#x}]
    strh  r0, [r8, #{T.BATTLER_SPELL:#x}]
    mov   r0, #{T.COMMAND_SPECIAL}
    str   r0, [r6, #{T.MENU_COMMAND:#x}]
    mov   r7, #{T.RESULT_MEMBER_DONE}
    bl    {MEMBER_DONE:#x}
    ldr   r0, [r6]
    orr   r0, r0, #{T.MENU_REBUILD}
    str   r0, [r6]
    mov   r0, #{T.PAGE_COMMANDS}
    strh  r0, [r6, #{T.MENU_NEXT_PAGE:#x}]
    mov   r0, #0
    bl    {CLOSE_DESCRIPTION:#x}
    b     {LIST_OK_DONE:#x}
"""

# Entered by `beq` from the Special list's OK handler for a spell on one ally (the handler's r4, r5, and r7
# go on; r6, r8, and sb are free). A skill cast on its caster alone needs no picker: the member is the
# target and the command ends, or the cast is refused if it would do nothing. Any other one-ally spell goes
# to the ally picker as before.
SELF_ASM = f"""
    ldr   r6, self_menu
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    cmp   r1, #{SPELL_COUNT}
    bhs   {ALLY_PICKER:#x}
    ldr   r0, self_fx
    add   r0, r0, r1, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [r0, #{FX_SELF}]
    cmp   r0, #0
    beq   {ALLY_PICKER:#x}
    ldrh  sb, [r6, #{T.MENU_MEMBER:#x}]
    mov   r0, sb
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   ${{cave_skill_refuse}}
    ldr   r1, self_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r8, r2, sb, r1
    strh  sb, [r8, #{T.TARGETS:#x}]
    b     ${{cave_skill_done}}
self_menu:
    .word {T.MENU:#x}
self_fx:
    .word ${{cave_skill_fx}}
self_battlers:
    .word {T.BATTLERS_PTR:#x}
"""

# Replaces `bl func_02050f78` (r0 = 3, r1 = 0) where a party Special picks its one enemy. r4 = actor.
# An enemy chosen on the grid (4..11 in the first target slot) is used, or the next living one;
# without a choice, or with nobody left, the game's random pick runs as before.
PICK_ASM = f"""
    push  {{r5, lr}}
    ldrsh r0, [r4, #{T.TARGETS:#x}]
    cmp   r0, #{FIRST_ENEMY}
    blt   pick_auto
    cmp   r0, #{LAST_ENEMY}
    bgt   pick_auto
    mov   r1, #{T.ROWS_ANY}
    bl    ${{cave_tgt_next}}
    cmp   r0, #0
    popge {{r5, pc}}
pick_auto:
    mov   r0, #{AUTO_ANY_ENEMY}
    mov   r1, #0
    bl    {AUTO_TARGET:#x}
    pop   {{r5, pc}}
"""


MENU_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_gate", GATE_ASM, "Special opens the spell list for everyone"),
    hook(
        LIST_GATE,
        LIST_GATE_WORD,
        "bne ${cave_skill_gate}",
        "Special opens the spell list for everyone",
    ),
    CaveCode("cave_skill_list", LIST_ASM, "the fighters' skills listed by level"),
    *(
        hook(
            addr,
            MOV_R0_12,
            "b ${cave_skill_list}",
            "the fighters' skills listed by level",
        )
        for addr in LIST_BRANCHES.values()
    ),
    CaveCode(
        "cave_skill_done", DONE_ASM, "a skill's command ends with its target kept"
    ),
    CaveCode("cave_skill_self", SELF_ASM, "a skill on its caster needs no ally picker"),
    hook(
        LIST_OK_ALLY,
        LIST_OK_ALLY_WORD,
        "beq ${cave_skill_self}",
        "a skill on its caster needs no ally picker",
    ),
    CaveCode("cave_skill_cast", CAST_ASM, "level skills need no ring"),
    hook(CAST_JIAN, MOV_R0_12, "b ${cave_skill_cast}", "level skills need no ring"),
    CaveCode("cave_skill_open", OPEN_ASM, "a single-enemy spell opens the enemy grid"),
    hook(
        LIST_OK_ENEMY,
        LIST_OK_ENEMY_WORD,
        "beq ${cave_skill_open}",
        "a single-enemy spell opens the enemy grid",
    ),
    CaveCode("cave_skill_pick", PICK_ASM, "a single-enemy spell uses the chosen enemy"),
    hook(
        RESOLVE_ENEMY,
        RESOLVE_ENEMY_WORD,
        "bl ${cave_skill_pick}",
        "a single-enemy spell uses the chosen enemy",
    ),
)
