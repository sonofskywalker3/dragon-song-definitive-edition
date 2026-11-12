"""Skills the fighters learn by level (docs/plan-skills.md); first one: Jian's Weapon Break.

Weapon Break (docs/plan-weapon-break.md): Jian, level 9, 8 MP, one enemy, ATK down one stage and never
below stage -1. It lives in spell table entry 38, an unused blank row inside the table's own footprint, so
nothing moves: the four loops over the table go one entry further, the name takes a spare slot of the battle
string list, and the description file gets records up to 38. Jian's branches of the "listed" and "castable"
tests take a level row from the cave in place of a ring, and the spell effect gains a stat-stage step. MP is
charged by the game's own Special path. The cast is Jian's attack with the hits taken out, then the ATK DOWN
banner on the target (effect row 27, the Quetzalcoatl card's).
"""

import struct
from pathlib import Path

from dsde import targeting_consts as T

from dsde.jp_hint_pairs import END, USA_TABLE
from dsde.patching import (
    AsmPatch,
    CaveCode,
    DataPatch,
    Feature,
    Patch,
    byte_patches,
)

VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"

SPELL_TABLE = 0x02094978  # 0x0C per spell: u32 flags, u32 MP cost, u8 Lucia level, u8 Flora level, u16 row
SPELL_ENTRY_SIZE = 0x0C
VANILLA_SPELL_COUNT = 0x26
FLAG_BATTLE = 0x2  # usable in battle; top two bits 0 = one enemy
RING_FLAGS = 0x00F00000  # Dragon Magic: one bit per ring
NEVER = 0xFF  # level byte: never learned

WEAPON_BREAK = 38
WEAPON_BREAK_COST = 8
WEAPON_BREAK_LEVEL = 9
WEAPON_BREAK_ROW = (
    27  # effect row: ATK DOWN banner (sprite 304), caster script 0x02095294
)
SPELL_COUNT = WEAPON_BREAK + 1

# Loops over the spell table: `cmp rN, #0x26`
BOUND_SITES = (
    (0x02035F64, 0xE3560026, "battle Special list"),
    (0x02050EB0, 0xE3540026, "first castable spell"),
    (0x02050F04, 0xE3540026, "has any spell"),
    (0x02065068, 0xE3580026, "field Magic list"),
)

# Battle string list: u16 offsets from the text base; a spell's name is entry spell + 0x35
STRING_OFFSETS = 0x020A41DC
STRING_BASE = 0x020A42E4
SPELL_NAME_FIRST = 0x35
BLANK_OFFSET = (
    0x0307  # entry 91's two-byte blank; the blanks of 92 to 98 hold the new name
)
NAME_OFFSET = 0x0309
NAME_SLOTS_USED = range(92, 99)
WEAPON_BREAK_NAME = "Weapon Break"

# Spell descriptions: sysmenupack entry 61, 61-byte records from file + 0x24, one per spell id
DESCRIPTIONS_ARCHIVE = "sysmenupack"
DESCRIPTIONS_ENTRY = 61
DESCRIPTION_SIZE = 0x3D
DESCRIPTIONS_END = 0x3F4  # 16 records in the vanilla file
DESCRIPTIONS_TAIL = bytes(
    4
)  # the file's last bytes (record 15's padding), checked before appending
VANILLA_DESCRIPTIONS = 16
WEAPON_BREAK_TEXT = "Lower one monster's attack"

JIAN_LEVEL = 0x020B4664  # u32 level index (0 = level 1) in Jian's field record
LIST_JIAN = 0x02050D24  # func_02050c50, Jian branch: `mov r0, #0xc`
LIST_RING_TESTS = 0x02050D28
LIST_TAIL = 0x02050DDC  # `cmp r6, #1`: listed, then the max MP test
CAST_JIAN = 0x02050AF8  # func_02050a74, Jian branch: `mov r0, #0xc`
CAST_RING_TESTS = 0x02050B08  # with r4 = flags
CAST_MP_TEST = 0x02050B88  # `cmp r7, #1`
MOV_R0_12 = 0xE3A0000C

# Special on the command page: only Lucia and Flora (ids 1, 3) get the spell list; anyone else gets a
# one-spell panel, and is refused with two spells or more. Everyone gets the list now, unless it would be
# empty (Jian with a ring he owns but does not wear passes the "has a spell" test and lists nothing).
LIST_GATE = 0x020369F4  # `bne 0x02036AB0` after `cmp r0, #3`
LIST_GATE_WORD = 0x1A00002D
BUILD_SPELL_LIST = 0x02035E00  # (2) -> entries
LIST_PAGE_BUILT = (
    0x02036A00  # the healers' path, after its own call of BUILD_SPELL_LIST
)
SPECIAL_REFUSED = 0x02036B18  # "Cannot use!"
GATE_ASM = f"""
    mov   r0, #2
    bl    {BUILD_SPELL_LIST:#x}
    cmp   r0, #0
    beq   {SPECIAL_REFUSED:#x}
    b     {LIST_PAGE_BUILT:#x}
"""

FX_SITE = 0x020503A0  # func_020500dc: `ands r0, r5, #0x1000000`, the first buff test
FX_WORD = 0xE2150401
BATTLERS_PTR = 0x020B8640
BATTLER_SIZE = 0x12C
BATTLER_RECORD = 0x10  # stat record index
BATTLER_ENEMY = 8  # flag bit in battler + 0
RECORDS_PTR = 0x020B8620
RECORD_SIZE = 0x6C
RECORD_ATK_STAGE = 0x40  # s16 stage of stat 4
STAT_ATK = 4
ADD_STAGE = 0x02054DEC  # (record, stat, delta)
RECOMPUTE_ENEMY = 0x02069AD8  # (record, 1)
RECOMPUTE_PARTY = 0x02054EBC
RESULT_WORDS = 0x0213B8F8
RESULT_FLAG = 8  # word 2: -1 as a debuff card leaves it

# Target pick for a single-enemy spell (needs manual-targeting: the Fight grid, feat_targeting_*.py)
LIST_OK_ENEMY = (
    0x02036CFC  # Special list OK, target bits 0: `beq 0x02036D20` (end the command)
)
LIST_OK_ENEMY_WORD = 0x0A000007
LIST_OK_DONE = 0x02036E18  # plays the menu sound, then the button epilogue (r5, r7 as the handler left them)
MEMBER_DONE = 0x020377F0  # slides the page out when a member's command ends
CLOSE_DESCRIPTION = 0x02039570  # (0)
SPELL_BUTTON = 4  # the Special list's own button, slid out when leaving the page
RESOLVE_ENEMY = 0x02051D34  # func_020514ec, party Special on one enemy: `bl func_02050f78` with (3, 0)
RESOLVE_ENEMY_WORD = 0xEBFFFC8F
AUTO_TARGET = 0x02050F78
AUTO_ANY_ENEMY = 3
FIRST_ENEMY = 4  # enemy battlers are 4..11
LAST_ENEMY = 11

# The cast's look: Jian's own attack, then the banner on the target
PARTY_SETUP_CALL = (
    0x020688B4  # func_02068890: `bl func_02068308` (party action setup), r0 = the actor
)
PARTY_SETUP_CALL_WORD = 0xEBFFFE93
PARTY_SETUP = 0x02068308  # (actor, mode)
SETUP_COUNTER = (
    1  # mode bit: the actor's counterattack, set up in slots 3 to 5 with its own script
)
BATTLER_COMMAND = 0x84
ACTION_SPECIAL = 2  # battler command (the menu's command number for it is 4)
BATTLER_SCRIPT = 0xC8
BATTLE_WORK_PTR = 0x020B8550
WORK_SLOT0 = 0x50  # btldata entry of animation slot 0 (slot 1 is the move file, slot 2 the effect sprite)
JIAN_ATTACK_FILE = 0x020953D4 + 4  # character table, Jian: the 3-hit combo's file
# Action script steps: flags, sound << 16 | effects started << 8, slot, animation, frames. Flags as in
# Jian's combo 0x02095AF0, with the three hit flags (0x40) gone and the last kick starting the target's
# effect script (bits 8..15 of the second word) and waiting for it (0x02000000).
STEP_START_EFFECTS = 0xFF00
STEP_WAIT_EFFECTS = 0x02000000
WEAPON_BREAK_SCRIPT = (
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
WEAPON_BREAK_SCRIPT_BACK = (
    (0x00300001, 0x00000000, 1, 0, 0),
    (0x00001012, 0x00030000, 1, 1, 20),
    (0x00000001, 0x00010000, 0, 0, 0),
    (0x00000001, 0x00010000, 0, 1, 0),
    (0x00000001, 0x00010000, 0, 2, 0),
    (0x00000001 | STEP_WAIT_EFFECTS, STEP_START_EFFECTS, 0, 3, 0),
    (0x04009012, 0x00000000, 1, 2, 16),
    (0x80000001, 0x00000000, 1, 3, 0),
)
FIRST_FRONT_ENEMY = 8  # battlers 4..7 are the back row

_CODES = {char: code for code, char in USA_TABLE.items()}


def _encode(text: str) -> bytes:
    return bytes(_CODES[char] for char in text) + bytes([END])


def _levels() -> str:
    """Jian's learn level index per spell id as `.byte` lines, 255 = not learned by level."""
    levels = [NEVER] * SPELL_COUNT
    levels[WEAPON_BREAK] = WEAPON_BREAK_LEVEL - 1
    return "\n".join(f"    .byte {level}" for level in levels)


def _name_patches() -> tuple[Patch, ...]:
    arm9 = VANILLA_ARM9.read_bytes()
    edits = dict(enumerate(_encode(WEAPON_BREAK_NAME), STRING_BASE + NAME_OFFSET))
    offsets = {SPELL_NAME_FIRST + WEAPON_BREAK: NAME_OFFSET}
    offsets |= dict.fromkeys(NAME_SLOTS_USED, BLANK_OFFSET)
    for entry, offset in offsets.items():
        addr = STRING_OFFSETS + 2 * entry
        edits |= dict(enumerate(struct.pack("<H", offset), addr))
    return byte_patches(arm9, edits, f"spell name {WEAPON_BREAK_NAME}")


def _descriptions() -> bytes:
    """Records 16 to 38: blanks for the enemy skills, then Weapon Break's line."""
    blank = bytes([END]).ljust(DESCRIPTION_SIZE, b"\0")
    text = _encode(WEAPON_BREAK_TEXT).ljust(DESCRIPTION_SIZE, b"\0")
    return blank * (WEAPON_BREAK - VANILLA_DESCRIPTIONS) + text


# Replaces `mov r0, #0xc` at the top of Jian's branch of func_02050c50. r8 = spell, r7 = 0 in the field,
# r6 = listed so far (0). A spell with a level in the cave row is listed in battle from that level.
LIST_ASM = f"""
    cmp   r7, #0
    beq   list_rings
    adr   r0, list_levels
    ldrb  r0, [r0, r8]
    cmp   r0, #{NEVER}
    beq   list_rings
    ldr   r1, list_jian_level
    ldr   r1, [r1]
    cmp   r1, r0
    movhs r6, #1
    b     {LIST_TAIL:#x}
list_rings:
    mov   r0, #0xc
    b     {LIST_RING_TESTS:#x}
list_jian_level:
    .word {JIAN_LEVEL:#x}
list_levels:
{_levels()}
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

# Replaces `ands r0, r5, #0x1000000` in func_020500dc (bl). r6 = spell, r7 = target battler, r5 = flags.
# Weapon Break lowers the target's ATK one stage unless it is already below 0. Leaves the flags of the
# replaced instruction.
FX_ASM = f"""
    push  {{r4, r8, lr}}
    cmp   r6, #{WEAPON_BREAK}
    bne   fx_out
    ldr   r0, fx_battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE:#x}
    mla   r4, r7, r1, r0
    ldr   r0, [r4, #{BATTLER_RECORD:#x}]
    ldr   r1, fx_records
    ldr   r1, [r1]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r8, r0, r2, r1
    ldrsh r1, [r8, #{RECORD_ATK_STAGE:#x}]
    cmp   r1, #0
    blt   fx_out
    mov   r0, r8
    mov   r1, #{STAT_ATK}
    mvn   r2, #0
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
    mvn   r1, #0
    str   r1, [r0, #{RESULT_FLAG}]
fx_out:
    ands  r0, r5, #0x1000000
    pop   {{r4, r8, pc}}
fx_battlers:
    .word {BATTLERS_PTR:#x}
fx_records:
    .word {RECORDS_PTR:#x}
fx_results:
    .word {RESULT_WORDS:#x}
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
# One enemy alive: it is the target and the command ends as in vanilla. Several: the Special list's
# rows slide out as they do for the ally picker and the enemy grid opens in spell mode.
OPEN_ASM = f"""
    ldr   r6, open_menu
    ldrh  r0, [r6, #{T.MENU_MEMBER:#x}]
    ldr   r1, open_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r8, r0, r2, r1
    mov   r0, #0
    bl    {CLOSE_DESCRIPTION:#x}
    mvn   r0, #0
    strh  r0, [r8, #{T.TARGETS:#x}]
    mov   r0, #{T.ROWS_ANY}
    bl    ${{cave_tgt_fill}}
    cmp   r0, #1
    bgt   open_grid
    bne   open_end
    ldr   r1, open_state
    ldrb  r0, [r1, #{T.STATE_FIRST}]
    add   r1, r1, #{T.STATE_MAP}
    ldrb  r0, [r1, r0]
    strh  r0, [r8, #{T.TARGETS:#x}]
open_end:
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
    b     {LIST_OK_DONE:#x}
open_grid:
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
    b     {LIST_OK_DONE:#x}
open_menu:
    .word {T.MENU:#x}
open_battlers:
    .word {T.BATTLERS_PTR:#x}
open_buttons:
    .word {T.BUTTONS_PTR:#x}
open_state:
    .word ${{cave_tgt_state}}
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


def _script(steps: tuple[tuple[int, int, int, int, int], ...]) -> str:
    """Action script steps as asm data: two words, then slot, animation, frames, and a pad halfword."""
    return "\n".join(
        f"    .word {flags:#x}, {word:#x}\n    .hword {slot}, {anim}, {frames}, 0"
        for flags, word, slot, anim, frames in steps
    )


# Replaces `bl func_02068308`. r0 = the acting party battler, r1 = mode. After the game's own setup of an
# action (not of a counter, which keeps the queued command and spell), a Weapon Break cast gets Jian's attack file in slot 0 and its own script: run in (or leap up to a
# back-row enemy), the combo without hits, the banner on the target, back.
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
    ldrh  r0, [r4, #{T.BATTLER_SPELL:#x}]
    cmp   r0, #{WEAPON_BREAK}
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
    pop   {{r4-r6, pc}}
anim_file:
    .word {JIAN_ATTACK_FILE:#x}
anim_work:
    .word {BATTLE_WORK_PTR:#x}
anim_script:
{_script(WEAPON_BREAK_SCRIPT)}
anim_script_back:
{_script(WEAPON_BREAK_SCRIPT_BACK)}
"""


def _hook(addr: int, old: int, asm: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, asm, note)


_ENTRY = SPELL_TABLE + WEAPON_BREAK * SPELL_ENTRY_SIZE

SKILLS_FEATURE = Feature(
    "skills",
    (
        Patch(_ENTRY, 0, FLAG_BATTLE, "Weapon Break: battle only, one enemy"),
        Patch(_ENTRY + 4, 0, WEAPON_BREAK_COST, "Weapon Break MP cost"),
        Patch(
            _ENTRY + 8,
            0x0000FFFF,
            WEAPON_BREAK_ROW << 16 | 0xFFFF,
            "Weapon Break: not a healer spell, ATK DOWN banner row",
        ),
        *(
            Patch(
                addr,
                old,
                old + SPELL_COUNT - VANILLA_SPELL_COUNT,
                f"{note}: one more spell",
            )
            for addr, old, note in BOUND_SITES
        ),
        *_name_patches(),
        DataPatch(
            DESCRIPTIONS_ARCHIVE,
            DESCRIPTIONS_ENTRY,
            DESCRIPTIONS_END - len(DESCRIPTIONS_TAIL),
            DESCRIPTIONS_TAIL,
            DESCRIPTIONS_TAIL + _descriptions(),
            "spell descriptions up to Weapon Break",
        ),
        CaveCode(
            "cave_skill_gate", GATE_ASM, "Special opens the spell list for everyone"
        ),
        _hook(
            LIST_GATE,
            LIST_GATE_WORD,
            "bne ${cave_skill_gate}",
            "Special opens the spell list for everyone",
        ),
        CaveCode("cave_skill_list", LIST_ASM, "Jian's skills listed by level"),
        CaveCode("cave_skill_cast", CAST_ASM, "level skills need no ring"),
        CaveCode("cave_skill_fx", FX_ASM, "Weapon Break lowers ATK one stage"),
        _hook(
            LIST_JIAN,
            MOV_R0_12,
            "b ${cave_skill_list}",
            "Jian's skills listed by level",
        ),
        _hook(
            CAST_JIAN, MOV_R0_12, "b ${cave_skill_cast}", "level skills need no ring"
        ),
        _hook(
            FX_SITE, FX_WORD, "bl ${cave_skill_fx}", "Weapon Break lowers ATK one stage"
        ),
        CaveCode(
            "cave_skill_open", OPEN_ASM, "a single-enemy spell opens the enemy grid"
        ),
        CaveCode("cave_skill_anim", ANIM_ASM, "Weapon Break plays Jian's attack"),
        _hook(
            PARTY_SETUP_CALL,
            PARTY_SETUP_CALL_WORD,
            "bl ${cave_skill_anim}",
            "Weapon Break plays Jian's attack",
        ),
        CaveCode(
            "cave_skill_pick", PICK_ASM, "a single-enemy spell uses the chosen enemy"
        ),
        _hook(
            LIST_OK_ENEMY,
            LIST_OK_ENEMY_WORD,
            "beq ${cave_skill_open}",
            "a single-enemy spell opens the enemy grid",
        ),
        _hook(
            RESOLVE_ENEMY,
            RESOLVE_ENEMY_WORD,
            "bl ${cave_skill_pick}",
            "a single-enemy spell uses the chosen enemy",
        ),
    ),
)
