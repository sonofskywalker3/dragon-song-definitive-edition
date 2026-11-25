"""Where the learned skills live: spell table entries, names, descriptions, and the per-spell cave tables.

Spell entries. The spell table (0x02094978) has one blank row after the game's 38 entries, and the stat
growth table starts right behind it (0x02094B4C, six blocks of 0x60 bytes, read only as base + character *
0x60 through two pool words). The growth table moves into the cave and its old bytes become spell entries 39
and up, so the spell table itself, and the features that edit it in place (mp-economy, spell-levels), stay
where they are. The loops over the table run to the new count, except the field Magic page's.

Names. The battle string list has room for one more name (entry 91, Weapon Break) and for "No effect!"
(entry 99); skills from id 39 take their name from a pointer table in the cave, through the one place a
spell name is drawn in battle (the name bar, func_02044c00). The field Magic page reads the list too, but
no skill is listed there.

Descriptions. One 61-byte record per spell id in sysmenupack entry 61, appended after the game's 16.

Cave tables, indexed by spell id: `cave_skill_levels` (one row of learn level indices per fighter, 255 = not
his or hers; a healer's skill is learned by the level bytes of its table entry) and `cave_skill_fx`
(kind, argument, delta, look, chance, self, sprite; see skills_common.FX_*).
"""

import struct

from dsde import targeting_consts as T
from dsde.jp_hint_pairs import END
from dsde.patching import AsmPatch, CaveCode, DataPatch, Patch, byte_patches
from dsde.skills_cards import CARD_SPELL
from dsde.skills_common import (
    BATTLER_RECORD,
    BATTLER_SIZE,
    BATTLERS_PTR,
    CHARACTER_RECORD_SIZE,
    FLAG_BATTLE,
    RECORD_SIZE,
    RECORDS_PTR,
    FX_SIZE,
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
    FLORA,
    GABRYEL,
    JIAN,
    LUCIA,
    RUFUS,
    SKILLS,
    SPELL_COUNT,
    Skill,
)

# Loops over the spell table: `cmp rN, #0x26`. The field Magic list's loop (0x02065068) keeps its 0x26:
# every skill is for battle only, the field page would list a healer's skill greyed with a name read from
# the string list (which has none from id 39), and its buffer is sized for the original count.
BOUND_SITES = (
    (0x02035F64, 0xE3560026, "battle Special list"),
    (0x02050EB0, 0xE3540026, "first castable spell"),
    (0x02050F04, 0xE3540026, "has any spell"),
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
# Renamed game spells (Jeff, 2026-11-25). The battle string list's spell names are also the field Magic page's.
# A name that fits is written over the old one; a longer one comes from the cave, in battle only (Dragon Magic
# is never on the field Magic page).
IN_PLACE_NAMES = {3: "Cure Water"}  # Cure Squall
CAVE_RENAMES = {11: "Crashing Wave"}  # Loud Call
FIRST_CAVE_NAME = (
    FIRST_SKILL + 1
)  # names from this spell id on come from the cave table

# The name bar's spell name (func_02044c00 case 3): `add r3, ip, r3` (ip = text base, r3 = the list
# offset of entry spell + 0x35), then `bl func_02045114`
NAME_SITE = 0x02044E7C
NAME_SITE_WORD = 0xE08C3003
MENU_BAR_ID = 0x94  # menu field: the id the name bar shows (here the spell)
MENU_BAR_MEMBER = 0x9C  # menu field: the battler whose list it is
RECORD_CHARACTER = 4  # battle stat record: the character id
EQUIPMENT = 0x020B4698  # a character's equipment slots, CHARACTER_RECORD_SIZE apart
CARD_SLOT_OFFSET = (
    10  # slot 5, the card slot of the card feature (docs/plan-cards.md 7.1)
)
ITEM_NAME_OFFSETS = 0x020A78EC  # u16 per item id: its name's offset from ITEM_NAMES
ITEM_NAMES = 0x020A7C30

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
    """Each skill's spell table entry: flags, MP cost, the healers' level bytes, and the effect row.

    The game lists a spell for Lucia or Flora when her level index reaches her byte of the entry
    (func_02050c50), so a healer's skill is learned through that byte and the fighters' rows of
    `cave_skill_levels` do not know it; everyone else's skills have "never" in both bytes.
    """
    patches = []
    for skill in SKILLS:
        addr = SPELL_TABLE + skill.spell * SPELL_ENTRY_SIZE
        lucia = skill.level - 1 if skill.owner == LUCIA else NEVER
        flora = skill.level - 1 if skill.owner == FLORA else NEVER
        words = (
            FLAG_BATTLE | skill.target,
            skill.cost,
            skill.row << 16 | flora << 8 | lucia,
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
    """Weapon Break's name (entry 91), "No effect!" (entry 99), and Cure Squall renamed in the string list."""
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
    for spell, name in IN_PLACE_NAMES.items():
        at = STRING_BASE + _string_offset(arm9, SPELL_NAME_FIRST + spell)
        old_end = arm9.index(END, at - ARM9_BASE) + ARM9_BASE
        new = encode(name)
        if at + len(new) > old_end + 1:
            raise ValueError(f"{name} is longer than the name it replaces")
        edits |= dict(enumerate(new, at))
    return byte_patches(arm9, edits, "skill strings")


def _string_offset(arm9: bytes, entry: int) -> int:
    return struct.unpack_from("<H", arm9, STRING_OFFSETS + 2 * entry - ARM9_BASE)[0]


def _cave_names() -> tuple[Skill, ...]:
    return tuple(skill for skill in SKILLS if skill.spell >= FIRST_CAVE_NAME)


def _name_asm() -> str:
    """The name bar's string for a spell: the list's as computed, or the cave table's from id 39."""
    pointers = "\n".join(f"    .word name_{skill.spell}" for skill in _cave_names())
    strings = "\n".join(
        f"name_{skill.spell}:\n    .byte {byte_list(encode(skill.name))}"
        for skill in _cave_names()
    )
    renames = "\n".join(
        f"""    cmp   ip, #{spell}
    ldreq r3, rename_ptr_{spell}
    bxeq  lr"""
        for spell in CAVE_RENAMES
    )
    rename_ptrs = "\n".join(
        f"rename_ptr_{spell}:\n    .word rename_{spell}" for spell in CAVE_RENAMES
    )
    renamed = "\n".join(
        f"rename_{spell}:\n    .byte {byte_list(encode(name))}"
        for spell, name in CAVE_RENAMES.items()
    )
    return f"""
    add   r3, ip, r3
    ldr   ip, name_menu
    ldr   ip, [ip, #{MENU_BAR_ID:#x}]
{renames}
    cmp   ip, #{CARD_SPELL}
    beq   name_card
    cmp   ip, #{SPELL_COUNT}
    bxhs  lr
    subs  ip, ip, #{FIRST_CAVE_NAME}
    bxlo  lr
    adr   r3, name_table
    ldr   r3, [r3, ip, lsl #2]
    bx    lr
@ the card spell: the name of the card the member (menu + 0x9C, a battler) wears in the card slot
name_card:
    push  {{r0-r2}}
    ldr   r0, name_menu
    ldr   r0, [r0, #{MENU_BAR_MEMBER:#x}]
    ldr   r1, name_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r1, r0, r2, r1
    ldr   r1, [r1, #{BATTLER_RECORD:#x}]
    ldr   r0, name_records
    ldr   r0, [r0]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r0, r1, r2, r0
    ldr   r0, [r0, #{RECORD_CHARACTER}]
    ldr   r1, name_slots
    mov   r2, #{CHARACTER_RECORD_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r0, [r1, #{CARD_SLOT_OFFSET:#x}]
    ldr   r1, name_offsets
    add   r1, r1, r0, lsl #1
    ldrh  r1, [r1]
    ldr   r3, name_items
    add   r3, r3, r1
    pop   {{r0-r2}}
    bx    lr
name_battlers:
    .word {BATTLERS_PTR:#x}
name_records:
    .word {RECORDS_PTR:#x}
name_slots:
    .word {EQUIPMENT:#x}
name_offsets:
    .word {ITEM_NAME_OFFSETS:#x}
name_items:
    .word {ITEM_NAMES:#x}
name_menu:
    .word {T.MENU:#x}
{rename_ptrs}
name_table:
{pointers}
{strings}
{renamed}
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
    """Effect record per spell id (skills_common.FX_*); zeros for the game's own spells."""
    lines = []
    for spell in range(SPELL_COUNT):
        skill = BY_SPELL.get(spell)
        record = (
            (
                skill.kind,
                skill.arg,
                skill.delta & 0xFF,
                skill.look,
                skill.chance,
                int(skill.self_only),
                *struct.pack("<H", skill.sprite),
            )
            if skill
            else ()
        )
        lines.append(f"    .byte {byte_list(bytes(record).ljust(FX_SIZE, bytes(1)))}")
    return "\n".join(lines) + "\n"


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
