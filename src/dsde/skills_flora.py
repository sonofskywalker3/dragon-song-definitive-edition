"""Flora's skills: the water spells that bind enemies. Her healing spells are the game's own (spell-levels)."""

from dsde.skills_types import (
    FLORA,
    Kind,
    Look,
    ROW_STATUS,
    SPRITE_WATER_RIBBON,
    STATUS_CHANCE,
    STATUS_PARALYSIS,
    Skill,
    Target,
)

FLORA_SKILLS: tuple[Skill, ...] = (
    # Flora's own spells (Lucia never learns them). The status is the game's paralysis; the sprite is the
    # ribbon of water in place of the status row's green rings, and the cast is a healer's own
    Skill(
        59,
        "Water Bind",
        "Bind one monster in water",
        9,
        FLORA,
        16,
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_PARALYSIS,
        0,
        ROW_STATUS,
        Look.SPELL,
        STATUS_CHANCE,
        sprite=SPRITE_WATER_RIBBON,
    ),
    Skill(
        60,
        "Binding Rain",
        "Bind all monsters in water",
        13,
        FLORA,
        28,
        Target.ENEMY_ALL,
        Kind.STATUS,
        STATUS_PARALYSIS,
        0,
        ROW_STATUS,
        Look.SPELL,
        STATUS_CHANCE,
        sprite=SPRITE_WATER_RIBBON,
        replaces=59,
    ),
)
