"""The skill entry behind a member's card slot (docs/plan-cards.md 2.4).

A card worn in the card slot is used from the Special list through one spell id. It is learned by nobody by level
(its learn level is past the last one), so the skills framework never lists it; the card feature lists it for a
member who wears a battle card, and when the action runs it becomes the game's own card command with that card,
so the card's effect, animation, and points are the game's.
"""

from dsde.skills_types import JIAN, ROW_STATUS, ROW_UNUSED, Kind, Look, Skill, Target

CARD_SPELL = 63
STEAL_SPELL = 64  # listed for a member wearing the Morus card (docs/plan-cards.md 5)
STEAL_CHANCE = 50  # percent (Jeff, 2026-11-25)
STEAL_RARE_CHANCE = 35  # percent for the rarer drop slot: the game's 25 and a 10 bonus
NEVER_BY_LEVEL = 256  # its learn level index is 255: never learned, and sorted after every other spell

CARD_SKILLS: tuple[Skill, ...] = (
    Skill(
        CARD_SPELL,
        "Card",
        "Use the card in your slot",
        0,
        JIAN,
        NEVER_BY_LEVEL,
        Target.ENEMY_ALL,
        Kind.NONE,
        0,
        0,
        ROW_UNUSED,
        Look.ROW,
    ),
    Skill(
        STEAL_SPELL,
        "Steal",
        "Take an item from one monster",
        0,
        JIAN,
        NEVER_BY_LEVEL,
        Target.ENEMY_ONE,
        Kind.STEAL,
        STEAL_RARE_CHANCE,
        0,
        ROW_STATUS,
        Look.ATTACK,
        chance=STEAL_CHANCE,
    ),
)
