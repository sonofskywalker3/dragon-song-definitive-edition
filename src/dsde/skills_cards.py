"""The skill entry behind a member's card slot (docs/plan-cards.md 2.4).

A card worn in the card slot is used from the Special list through one spell id. It is learned by nobody by level
(its learn level is past the last one), so the skills framework never lists it; the card feature lists it for a
member who wears a battle card, and when the action runs it becomes the game's own card command with that card,
so the card's effect, animation, and points are the game's.
"""

from dsde.skills_types import JIAN, ROW_UNUSED, Kind, Look, Skill, Target

CARD_SPELL = 63
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
)
