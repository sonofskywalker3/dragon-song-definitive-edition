"""Where the learned skills live: spell table entries, names, descriptions, and the per-spell cave tables.

Spell entries. The spell table (0x02094978) has one blank row after the game's 38 entries, and the stat
growth table starts right behind it (0x02094B4C, six blocks of 0x60 bytes, read only as base + character *
0x60 through two pool words). The growth table moves into the cave and its old bytes become spell entries 39
and up, so the spell table itself, and the features that edit it in place (mp-economy, spell-levels), stay
where they are. The four loops over the table run to the new count.

Names. The battle string list has room for one more name (entry 91, Weapon Break) and for "No effect!"
(entry 99); skills from id 39 take their name from a pointer table in the cave, through the one place a
spell name is drawn in battle (the name bar, func_02044c00). The field Magic page reads the list too, but
the fighters' skills are not listed there.

Descriptions. One 61-byte record per spell id in sysmenupack entry 61, appended after the game's 16.

Cave tables, indexed by spell id: `cave_skill_levels` (one row of learn level indices per fighter, 255 = not
his or hers) and `cave_skill_fx` (kind, stat, delta, look; see skills_data.py).
"""

import struct

from dsde import targeting_consts as T
from dsde.jp_hint_pairs import END
from dsde.patching import AsmPatch, CaveCode, DataPatch, Patch, byte_patches
from dsde.skills_common import (
    FLAG_BATTLE,
    NEVER,
    SPELL_ENTRY_SIZE,
    SPELL_NAME_FIRST,
    SPELL_TABLE,
    STRING_BASE,
    STRING_NO_EFFECT,
    STRING_OFFSETS,
    VANILLA_ARM9,
    VANILLA_SPELL_COUNT,
    byte_list,
    encode,
    hook,
)
from dsde.patching import ARM9_BASE
from dsde.skills_data import (
    BY_SPELL,
    FIRST_SKILL,
    GABRYEL,
    JIAN,
    RUFUS,
    SKILLS,
    SPELL_COUNT,
    Skill,
)

# Loops over the spell table: `cmp rN, #0x26`
BOUND_SITES = (
    (0x02035F64, 0xE3560026, "battle Special list"),
    (0x02050EB0, 0xE3540026, "first castable spell"),
    (0x02050F04, 0xE3540026, "has any spell"),
    (0x02065068, 0xE3580026, "field Magic list"),
)

# Stat growth: six 0x60-byte blocks (the five characters and one more), read by func_020553xx and
# func_020554f4 as base + character * 0x60 + field; nothing else points into it
GROWTH_TABLE = 0x02094B4C
GROWTH_SIZE = 0x240
GROWTH_POOL_WORDS = (0x020554F0, 0x020555E4)
SPELL_ROOM = (
    GROWTH_TABLE + GROWTH_SIZE - SPELL_TABLE
) // SPELL_ENTRY_SIZE  # ids below this fit

# String list edits (entry 91 points at its two-byte blank, entry 99 at the first blank after the name)
BLANK_OFFSET = 0x0307
NAME_OFFSET = 0x0309
NAME_SLOTS_USED = range(92, 99)  # their blanks hold Weapon Break's name
NO_EFFECT_OFFSET = 0x0317
NO_EFFECT_SLOTS_USED = range(100, 105)  # their blanks hold "No effect!"
NO_EFFECT_TEXT = "No effect!"
FIRST_CAVE_NAME = (
    FIRST_SKILL + 1
)  # names from this spell id on come from the cave table

# The name bar's spell name (func_02044c00 case 3): `add r3, ip, r3` (ip = text base, r3 = the list
# offset of entry spell + 0x35), then `bl func_02045114`
NAME_SITE = 0x02044E7C
NAME_SITE_WORD = 0xE08C3003
MENU_BAR_ID = 0x94  # menu field: the id the name bar shows (here the spell)

# Spell descriptions: sysmenupack entry 61, 61-byte records from file + 0x24, one per spell id
DESCRIPTIONS_ARCHIVE = "sysmenupack"
DESCRIPTIONS_ENTRY = 61
DESCRIPTION_SIZE = 0x3D
DESCRIPTIONS_END = 0x3F4  # 16 records in the vanilla file
DESCRIPTIONS_TAIL = bytes(
    4
)  # the file's last bytes (record 15's padding), checked first
VANILLA_DESCRIPTIONS = 16

LEVEL_ROWS = (JIAN, GABRYEL, RUFUS)  # row order of cave_skill_levels

if SPELL_COUNT > SPELL_ROOM:
    raise ValueError(f"{SPELL_COUNT} spells do not fit: room for {SPELL_ROOM}")


def _word(arm9: bytes, addr: int) -> int:
    return struct.unpack_from("<I", arm9, addr - ARM9_BASE)[0]


def _entry_patches(arm9: bytes) -> tuple[Patch, ...]:
    """Each skill's spell table entry: flags, MP cost, and no healer levels with the effect row."""
    patches = []
    for skill in SKILLS:
        addr = SPELL_TABLE + skill.spell * SPELL_ENTRY_SIZE
        words = (
            FLAG_BATTLE | skill.target,
            skill.cost,
            skill.row << 16 | NEVER << 8 | NEVER,
        )
        for index, new in enumerate(words):
            at = addr + 4 * index
            patches.append(
                Patch(
                    at, _word(arm9, at), new, f"{skill.name}: spell entry word {index}"
                )
            )
    return tuple(patches)


def _growth_asm(arm9: bytes) -> str:
    start = GROWTH_TABLE - ARM9_BASE
    words = struct.unpack_from(f"<{GROWTH_SIZE // 4}I", arm9, start)
    return "\n".join(f"    .word {word:#x}" for word in words)


def _string_patches(arm9: bytes) -> tuple[Patch, ...]:
    """Weapon Break's name (entry 91) and "No effect!" (entry 99) in the battle string list."""
    first = BY_SPELL[FIRST_SKILL]
    edits = dict(enumerate(encode(first.name), STRING_BASE + NAME_OFFSET))
    offsets = {SPELL_NAME_FIRST + first.spell: NAME_OFFSET}
    offsets |= dict.fromkeys(NAME_SLOTS_USED, BLANK_OFFSET)
    edits |= dict(enumerate(encode(NO_EFFECT_TEXT), STRING_BASE + NO_EFFECT_OFFSET))
    offsets |= {STRING_NO_EFFECT: NO_EFFECT_OFFSET}
    offsets |= dict.fromkeys(NO_EFFECT_SLOTS_USED, BLANK_OFFSET)
    for entry, offset in offsets.items():
        addr = STRING_OFFSETS + 2 * entry
        edits |= dict(enumerate(struct.pack("<H", offset), addr))
    return byte_patches(arm9, edits, "skill strings")


def _cave_names() -> tuple[Skill, ...]:
    return tuple(skill for skill in SKILLS if skill.spell >= FIRST_CAVE_NAME)


def _name_asm() -> str:
    """The name bar's string for a spell: the list's as computed, or the cave table's from id 39."""
    pointers = "\n".join(f"    .word name_{skill.spell}" for skill in _cave_names())
    strings = "\n".join(
        f"name_{skill.spell}:\n    .byte {byte_list(encode(skill.name))}"
        for skill in _cave_names()
    )
    return f"""
    add   r3, ip, r3
    ldr   ip, name_menu
    ldr   ip, [ip, #{MENU_BAR_ID:#x}]
    cmp   ip, #{SPELL_COUNT}
    bxhs  lr
    subs  ip, ip, #{FIRST_CAVE_NAME}
    bxlo  lr
    adr   r3, name_table
    ldr   r3, [r3, ip, lsl #2]
    bx    lr
name_menu:
    .word {T.MENU:#x}
name_table:
{pointers}
{strings}
    .align 2
"""


def _descriptions() -> bytes:
    """Records 16 to the last skill: blanks for the enemy skills, then each skill's line."""
    blank = bytes([END]).ljust(DESCRIPTION_SIZE, b"\0")
    records = [blank] * (FIRST_SKILL - VANILLA_DESCRIPTIONS)
    records += [encode(skill.text).ljust(DESCRIPTION_SIZE, b"\0") for skill in SKILLS]
    return b"".join(records)


def _levels_asm() -> str:
    """Learn level index per spell id, one row per fighter in LEVEL_ROWS order."""
    lines = []
    for owner in LEVEL_ROWS:
        row = [NEVER] * SPELL_COUNT
        for skill in SKILLS:
            if skill.owner == owner:
                row[skill.spell] = skill.level - 1
        lines.append(f"    .byte {byte_list(bytes(row))}")
    return "\n".join(lines) + "\n    .align 2\n"


def _fx_asm() -> str:
    """Effect record per spell id: kind, stat, delta (s8), look; zeros for the game's own spells."""
    lines = []
    for spell in range(SPELL_COUNT):
        skill = BY_SPELL.get(spell)
        record = (
            (skill.kind, skill.stat, skill.delta & 0xFF, skill.look)
            if skill
            else (0, 0, 0, 0)
        )
        lines.append(f"    .byte {byte_list(bytes(record))}")
    return "\n".join(lines) + "\n"


def level_row_offset(owner: int) -> int:
    """Byte offset of a fighter's row in cave_skill_levels."""
    return LEVEL_ROWS.index(owner) * SPELL_COUNT


def table_patches() -> tuple[Patch | AsmPatch | CaveCode | DataPatch, ...]:
    arm9 = VANILLA_ARM9.read_bytes()
    return (
        CaveCode(
            "cave_skill_growth", _growth_asm(arm9), "the stat growth table, moved"
        ),
        *(
            AsmPatch(
                addr,
                addr + 4,
                GROWTH_TABLE,
                GROWTH_TABLE,
                ".word ${cave_skill_growth}",
                "stat growth is read from the cave",
            )
            for addr in GROWTH_POOL_WORDS
        ),
        *_entry_patches(arm9),
        *(
            Patch(
                addr,
                old,
                old + SPELL_COUNT - VANILLA_SPELL_COUNT,
                f"{note}: up to spell {SPELL_COUNT - 1}",
            )
            for addr, old, note in BOUND_SITES
        ),
        *_string_patches(arm9),
        CaveCode("cave_skill_name", _name_asm(), "skill names from the cave"),
        hook(
            NAME_SITE,
            NAME_SITE_WORD,
            "bl ${cave_skill_name}",
            "skill names from the cave",
        ),
        DataPatch(
            DESCRIPTIONS_ARCHIVE,
            DESCRIPTIONS_ENTRY,
            DESCRIPTIONS_END - len(DESCRIPTIONS_TAIL),
            DESCRIPTIONS_TAIL,
            DESCRIPTIONS_TAIL + _descriptions(),
            "spell descriptions up to the last skill",
        ),
        CaveCode("cave_skill_levels", _levels_asm(), "skill learn levels"),
        CaveCode("cave_skill_fx", _fx_asm(), "skill effect records"),
    )
