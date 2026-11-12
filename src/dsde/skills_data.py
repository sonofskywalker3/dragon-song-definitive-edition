"""The skills the party learns by level, as data (docs/plan-skills.md).

Each skill is one spell table entry from id 38 up. The feature modules (feat_skills_*.py) turn this list
into the table entries, the names and descriptions, the per-spell cave tables the hooks read, and the
learn levels, so adding a skill of an existing kind is one more `Skill` here.
"""

from dataclasses import dataclass
from enum import IntEnum

# Character ids
JIAN, LUCIA, GABRYEL, FLORA, RUFUS = range(5)

# Stat ids as func_02054dec takes them; the stage of stat n is the s16 at stat record + 0x38 + 2 * n
STAT_ATK, STAT_DEF, STAT_AGI, STAT_INT, STAT_DEX, STAT_LUK = range(4, 10)

FIRST_SKILL = 38  # the blank row after the game's own 38 spell entries


class Target(IntEnum):
    """Who a spell is cast on: the top two bits of its flags."""

    ENEMY_ONE = 0x00000000
    ENEMY_ALL = 0x40000000
    ALLY_ONE = 0x80000000
    ALLY_ALL = 0xC0000000


class Kind(IntEnum):
    """What a skill does to its target (byte 0 of its effect record)."""

    NONE = 0  # the game's own spells
    STAGE = 1  # moves one stat one stage, and never past one stage from 0


class Look(IntEnum):
    """How the cast plays (byte 3 of the effect record)."""

    ROW = 0  # the effect row's own caster script, as a card or a healer's spell
    ATTACK = 1  # the owner's attack with the hits taken out, then the row's effect on the target


@dataclass(frozen=True)
class Skill:
    """One learned skill. `row` is the effect table row that supplies the sprite and its script."""

    spell: int
    name: str
    text: str  # the description line of the Special list, at most 30 characters
    cost: int  # MP
    owner: int  # character id
    level: int  # learned at this level (1-based)
    target: Target
    kind: Kind
    stat: int
    delta: int  # stages: -1 lowers, +1 raises
    row: int
    look: Look


ROW_ATK_DOWN = 27  # "ATK DOWN" banner (sprite 304), the Quetzalcoatl card's row
ROW_DEF_DOWN = 28  # "DEF DOWN" banner (sprite 305), the Abadon card's row

SKILLS: tuple[Skill, ...] = (
    Skill(
        38,
        "Weapon Break",
        "Lower one monster's attack",
        8,
        JIAN,
        9,
        Target.ENEMY_ONE,
        Kind.STAGE,
        STAT_ATK,
        -1,
        ROW_ATK_DOWN,
        Look.ATTACK,
    ),
    Skill(
        39,
        "Armor Break",
        "Lower one monster's defense",
        6,
        JIAN,
        14,
        Target.ENEMY_ONE,
        Kind.STAGE,
        STAT_DEF,
        -1,
        ROW_DEF_DOWN,
        Look.ATTACK,
    ),
)

DESCRIPTION_MAX = 30
if [skill.spell for skill in SKILLS] != list(
    range(FIRST_SKILL, FIRST_SKILL + len(SKILLS))
):
    raise ValueError("skill spell ids must run from FIRST_SKILL with no gaps")
if any(len(skill.text) > DESCRIPTION_MAX for skill in SKILLS):
    raise ValueError(f"a skill description is longer than {DESCRIPTION_MAX} characters")

SPELL_COUNT = FIRST_SKILL + len(SKILLS)  # spell ids 0 .. SPELL_COUNT - 1 exist
BY_SPELL = {skill.spell: skill for skill in SKILLS}
