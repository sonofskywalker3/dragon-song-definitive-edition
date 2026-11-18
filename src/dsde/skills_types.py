"""What a learned skill is: the types and constants the skill lists (skills_*.py) are written in.

docs/plan-skills.md has the design. The feature modules (feat_skills_*.py) turn the lists into spell table
entries, names, descriptions, and the per-spell cave tables the hooks read.
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

    ROW = 0  # the effect row's own caster script in the item pose, as a card is played
    ATTACK = 1  # the owner's attack with the hits taken out, then the row's effect on the target
    SPELL = 2  # the effect row's own caster script in the caster's Special pose, as a healer's spell


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
    sprite: int = (
        0  # btldata entry shown in place of the effect row's sprite; 0 = the row's own
    )


ROW_ATK_UP = (
    21  # "ATK UP" banner (sprite 298); 22 to 24 are the same for the next stats
)
ROW_DEF_UP = 22  # "DEF UP" (sprite 299)
ROW_AGI_UP = 23  # "AGI UP" (sprite 300)
ROW_INT_UP = 24  # "INT UP" (sprite 301)
ROW_ATK_DOWN = 27  # "ATK DOWN" banner (sprite 304), the Quetzalcoatl card's row
ROW_DEF_DOWN = 28  # "DEF DOWN" banner (sprite 305), the Abadon card's row
ROW_STATUS = 34  # green rings on the target (sprite 314), the status cards' row
ROW_SURE_HIT = 37  # "HIT" banner on each ally (sprite 319), the Bealzebub card's row

SPRITE_WATER_RIBBON = 313  # a ribbon of water coiling round the target; in the game's files, used by nothing
