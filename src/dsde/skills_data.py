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

# Statuses (the low nibble of stat record + 0x08; docs/re-cards.md)
STATUS_SLEEP = 1
STATUS_BLIND = 2
STATUS_PARALYSIS = 4  # no action; Gabryel's Howl calls it fear
STATUS_POISON = 6
# Statuses a boss row (enemy row flags bit 31) never takes; blind (2) and poison (6) land on bosses too
BOSS_IMMUNE = frozenset({1, 3, 4, 5, 7})
STATUS_CHANCE = 70  # percent: the success roll of the statuses that stop a turn (the cards never miss)
SURE = 100  # percent: no roll at all, so no random number is drawn

# Battle-wide flags in the first word of the battle work area, set by the cards and cleared with it at the
# start of each battle
FLAG_SURE_HIT = 4  # the party's physical attacks always hit (the Bealzebub card)

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
    STAGE = 1  # moves stat `arg` one stage (`delta`), and never past one stage from 0
    STATUS = 2  # gives status `arg` (a roll if `chance` is under 100); never over another status
    FLAG = 3  # sets battle-wide flag `arg` for the rest of the battle


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
    arg: int  # a stat id (STAGE), a status (STATUS), or a battle flag mask (FLAG)
    delta: int  # STAGE: -1 lowers, +1 raises; 0 for the other kinds
    row: int
    look: Look
    chance: int = SURE  # STATUS: percent chance to land
    self_only: bool = False  # an ALLY_ONE skill cast on its caster, with no ally picker


ROW_ATK_UP = 21  # "ATK UP" banner (sprite 298)
ROW_ATK_DOWN = 27  # "ATK DOWN" banner (sprite 304), the Quetzalcoatl card's row
ROW_DEF_DOWN = 28  # "DEF DOWN" banner (sprite 305), the Abadon card's row
ROW_STATUS = 34  # green rings on the target (sprite 314), the status cards' row
ROW_SURE_HIT = 37  # "HIT" banner on each ally (sprite 319), the Bealzebub card's row

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
    # The engine's flag covers the whole party, so the skill is cast on all allies: the banner shows on each
    Skill(
        40,
        "Focus",
        "Attacks will not miss",
        6,
        JIAN,
        19,
        Target.ALLY_ALL,
        Kind.FLAG,
        FLAG_SURE_HIT,
        0,
        ROW_SURE_HIT,
        Look.ROW,
    ),
    Skill(
        41,
        "Knockout Kick",
        "Put one monster to sleep",
        9,
        JIAN,
        25,
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_SLEEP,
        0,
        ROW_STATUS,
        Look.ATTACK,
        STATUS_CHANCE,
    ),
    # Jian cannot run to every enemy: the all-enemy versions play the row's own cast, as the cards do
    Skill(
        42,
        "War Breaker",
        "Lower all monsters' attack",
        12,
        JIAN,
        30,
        Target.ENEMY_ALL,
        Kind.STAGE,
        STAT_ATK,
        -1,
        ROW_ATK_DOWN,
        Look.ROW,
    ),
    Skill(
        43,
        "Wall Breaker",
        "Lower all monsters' defense",
        9,
        JIAN,
        36,
        Target.ENEMY_ALL,
        Kind.STAGE,
        STAT_DEF,
        -1,
        ROW_DEF_DOWN,
        Look.ROW,
    ),
    # Gabryel. Poison and blind always land, on bosses too; fear is the game's paralysis and rolls
    Skill(
        44,
        "Venom Claw",
        "Poison one monster",
        8,
        GABRYEL,
        13,
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_POISON,
        0,
        ROW_STATUS,
        Look.ATTACK,
    ),
    Skill(
        45,
        "Blinding Swipe",
        "Blind one monster",
        7,
        GABRYEL,
        17,
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_BLIND,
        0,
        ROW_STATUS,
        Look.ATTACK,
    ),
    Skill(
        46,
        "Feral",
        "Raise your own attack",
        8,
        GABRYEL,
        21,
        Target.ALLY_ONE,
        Kind.STAGE,
        STAT_ATK,
        1,
        ROW_ATK_UP,
        Look.ROW,
        self_only=True,
    ),
    Skill(
        47,
        "Howl",
        "Scare one monster stiff",
        9,
        GABRYEL,
        26,
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_PARALYSIS,
        0,
        ROW_STATUS,
        Look.ATTACK,
        STATUS_CHANCE,
    ),
    Skill(
        48,
        "Venom Storm",
        "Poison all monsters",
        12,
        GABRYEL,
        31,
        Target.ENEMY_ALL,
        Kind.STATUS,
        STATUS_POISON,
        0,
        ROW_STATUS,
        Look.ROW,
    ),
    Skill(
        49,
        "Blinding Gale",
        "Blind all monsters",
        10,
        GABRYEL,
        35,
        Target.ENEMY_ALL,
        Kind.STATUS,
        STATUS_BLIND,
        0,
        ROW_STATUS,
        Look.ROW,
    ),
    Skill(
        50,
        "Dread Roar",
        "Scare all monsters stiff",
        13,
        GABRYEL,
        39,
        Target.ENEMY_ALL,
        Kind.STATUS,
        STATUS_PARALYSIS,
        0,
        ROW_STATUS,
        Look.ROW,
        STATUS_CHANCE,
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
