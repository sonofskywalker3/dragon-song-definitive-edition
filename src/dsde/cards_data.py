"""The cards as data (docs/plan-cards.md 3 and 4).

A monster card in a member's card slot is an ability used from the Special list (or, for a field card, the
field Magic page) for 100 points. A card whose effect overlaps a kit skill (PAIRS) works on one picked target
for a member who has not learned that skill and on all targets for one who has (spec 3); the others have one
version. A boss card in the slot is a passive: six stat bonuses and one gear effect as item data, or a hook.
"""

from dataclasses import dataclass

from dsde.cards_common import FIRST_BOSS_CARD, FIRST_CARD, LAST_CARD
from dsde.skills_data import BY_SPELL
from dsde.skills_types import (
    FLORA,
    GABRYEL,
    JIAN,
    LUCIA,
    RUFUS,
    STAT_ATK,
    STAT_DEF,
    STAT_INT,
    STATUS_BLIND,
    STATUS_CHANCE,
    STATUS_PARALYSIS,
    STATUS_POISON,
    STATUS_SLEEP,
    SURE,
    Kind,
    Target,
)

# Monster cards (item ids; the species' card is FIRST_CARD + species)
BLOB, ONLOOKER, SHREEKER, NAMIA, TREANT, ICE_MONGREL, MAD_FANG, YETI = range(216, 224)
TERMITE, ABADON, TICK, BEALZEBUB, INSECTOR, GLOOMWING, KUNTUKAPU, IKONTABIPU = range(
    224, 232
)
DAGON, HELLBIRD, STURGE, VITRA, QUETZALCOATL, COMET, OHAINKARU, SHAITAN = range(
    232, 240
)
PHANTOM, OCHU, EVIL_EARTH, CHUPACABRA, ENIGMA, GHOULA, THANATOS, ASMODEE = range(
    240, 248
)
DUAGER, DRUID = 248, 249

# Boss cards
SASQUATCH, ARMORED_BOAR, RAFT, SHARIF, MORAN, DEUCE, GRONK, ZETHOS = range(250, 258)
CAUCUS, ORCUS, MORUS, RED_DRAGON, WHITE_DRAGON, BLACK_DRAGON, BLUE_DRAGON = range(
    258, 265
)
DARK_JIAN, GIDEON, GIDEON_2, GIDEON_3, IGNATIUS = range(265, 270)
DEFERRED_BOSS_CARDS = frozenset(
    {GIDEON_2, GIDEON_3, IGNATIUS}
)  # collectibles for now (spec 8, decision 2)

# Spells a pair's learners are tested on: the game's own ids, and the skills' (skills_*.py)
TENDER_RAIN, DIVINE_RAIN, MIRACLE_TEARS = 2, 4, 5
WEAPON_BREAK, ARMOR_BREAK, KNOCKOUT_KICK, WAR_BREAKER, WALL_BREAKER = 38, 39, 41, 42, 43
FOCUS = 40
VENOM_CLAW, BLINDING_SWIPE, HOWL, VENOM_RAIN, BLINDING_GALE, DREAD_ROAR = (
    44,
    45,
    47,
    48,
    49,
    50,
)
STRATAGEM, WAR_COUNCIL, WATER_BIND, BINDING_RAIN = 54, 58, 59, 60
GAME_SPELLS = frozenset({TENDER_RAIN, DIVINE_RAIN, MIRACLE_TEARS})

# Gear effect ids (item +2; the switch in func_0206ab6c)
GEAR_BLIND_PROOF = 0x10
GEAR_HP_REGEN_2 = 0x1D
GEAR_WATER_GUARD = 0x1F
GEAR_EARTH_GUARD = 0x20
GEAR_WIND_GUARD = 0x21
GEAR_FIRE_GUARD = 0x22
GEAR_DOUBLE_CHANCE = 0x27
# New gear effect ids past the game's last (0x2D), for the boss cards alone (feat_card_bosses.py): the dragons take
# half damage from their element (the game's guards above take a quarter off), and Caucus regains 3% a turn
(
    GEAR_STRONG_WATER,
    GEAR_STRONG_EARTH,
    GEAR_STRONG_WIND,
    GEAR_STRONG_FIRE,
    GEAR_HP_REGEN_3,
) = range(0x2E, 0x33)
NO_GEAR_EFFECT = 0


@dataclass(frozen=True)
class CardPair:
    """A card whose effect overlaps a kit skill: basic on one target, upgraded on all for a learner."""

    card: int
    learners: tuple[
        tuple[int, int], ...
    ]  # (character id, spell id): having learned it gives the upgrade
    basic_target: Target  # ENEMY_ONE or ALLY_ONE
    kind: Kind  # STAGE or STATUS follow the skills' rules (spec 3.3); NONE keeps the card's own effect
    arg: int = 0  # the stat (STAGE) or the status (STATUS)
    delta: int = 0
    chance: int = SURE


@dataclass(frozen=True)
class BossPassive:
    """A boss card's passive while worn: item data, plus a hook for the three that need code."""

    card: int
    stats: tuple[int, int, int, int, int, int]  # ATK, DEF, AGI, INT, DEX, LUCK bonuses
    gear_effect: int = NO_GEAR_EFFECT
    hook: str = ""  # "moran", "orcus", or "steal"


PAIRS: tuple[CardPair, ...] = (
    CardPair(
        QUETZALCOATL,
        ((JIAN, WEAPON_BREAK),),
        Target.ENEMY_ONE,
        Kind.STAGE,
        STAT_ATK,
        -1,
    ),
    CardPair(
        ABADON, ((JIAN, ARMOR_BREAK),), Target.ENEMY_ONE, Kind.STAGE, STAT_DEF, -1
    ),
    CardPair(
        IKONTABIPU,
        ((JIAN, KNOCKOUT_KICK),),
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_SLEEP,
        0,
        STATUS_CHANCE,
    ),
    CardPair(
        SHREEKER, ((GABRYEL, VENOM_CLAW),), Target.ENEMY_ONE, Kind.STATUS, STATUS_POISON
    ),
    CardPair(
        ASMODEE,
        ((GABRYEL, BLINDING_SWIPE),),
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_BLIND,
    ),
    CardPair(
        TICK,
        ((GABRYEL, HOWL),),  # Howl only (Jeff, 2026-11-26): Flora's Water Bind is not paired
        Target.ENEMY_ONE,
        Kind.STATUS,
        STATUS_PARALYSIS,
        0,
        STATUS_CHANCE,
    ),
    CardPair(COMET, ((RUFUS, STRATAGEM),), Target.ALLY_ONE, Kind.STAGE, STAT_INT, 1),
    CardPair(
        NAMIA, ((LUCIA, DIVINE_RAIN), (FLORA, DIVINE_RAIN)), Target.ALLY_ALL, Kind.NONE
    ),
    CardPair(
        SHAITAN,
        ((LUCIA, MIRACLE_TEARS), (FLORA, MIRACLE_TEARS)),
        Target.ALLY_ONE,
        Kind.NONE,
    ),
    CardPair(
        VITRA, ((LUCIA, TENDER_RAIN), (FLORA, TENDER_RAIN)), Target.ALLY_ONE, Kind.NONE
    ),
    CardPair(BEALZEBUB, ((JIAN, FOCUS),), Target.ALLY_ONE, Kind.NONE),
)
# The skills and spells a worn card enhances (docs/plan-cards.md 8): a wearer who knows one of them casts it
# enhanced for the MP and 100 points (one target) or 200 (all targets), and is not offered the card itself.
BOOSTS: dict[int, tuple[int, ...]] = {
    QUETZALCOATL: (WEAPON_BREAK, WAR_BREAKER),
    ABADON: (ARMOR_BREAK, WALL_BREAKER),
    IKONTABIPU: (KNOCKOUT_KICK,),
    SHREEKER: (VENOM_CLAW, VENOM_RAIN),
    ASMODEE: (BLINDING_SWIPE, BLINDING_GALE),
    TICK: (HOWL, DREAD_ROAR),
    COMET: (STRATAGEM, WAR_COUNCIL),
    NAMIA: (DIVINE_RAIN,),
    SHAITAN: (MIRACLE_TEARS,),
    VITRA: (TENDER_RAIN,),
    BEALZEBUB: (FOCUS,),
}
NAMIA_BASIC_REGEN = (
    5  # percent of max HP a turn: Divine Rain's, for a wearer who has not learned it
)

ONE_VERSION = frozenset(
    {
        ONLOOKER,
        CHUPACABRA,
        ENIGMA,
        THANATOS,
        DUAGER,
        STURGE,
        EVIL_EARTH,
        DAGON,
        PHANTOM,
        DRUID,
        INSECTOR,
        OCHU,
        KUNTUKAPU,
        HELLBIRD,
        YETI,
        TERMITE,
        ICE_MONGREL,
    }
)
FIELD_CARDS = frozenset({BLOB, OHAINKARU, MAD_FANG, GHOULA, TREANT, GLOOMWING})

BOSS_PASSIVES: tuple[BossPassive, ...] = (
    BossPassive(SASQUATCH, (4, 8, 0, 0, 0, 0)),
    BossPassive(ARMORED_BOAR, (0, 8, 0, 0, 0, 0), GEAR_DOUBLE_CHANCE),
    BossPassive(RAFT, (0, 0, 12, 0, 5, 0)),
    BossPassive(SHARIF, (0, 0, 0, 0, 0, 10), GEAR_BLIND_PROOF),
    BossPassive(MORAN, (0, 0, 0, 0, 0, 0), hook="moran"),
    BossPassive(DEUCE, (0, 12, 0, 0, 0, 8)),
    BossPassive(GRONK, (0, 0, 0, 12, 0, 0), GEAR_WIND_GUARD),
    BossPassive(ZETHOS, (12, 0, 0, 0, 0, 10)),
    BossPassive(CAUCUS, (0, 0, 0, 10, 0, 0), GEAR_HP_REGEN_3),
    BossPassive(ORCUS, (0, 0, 0, 0, 0, 0), hook="orcus"),
    BossPassive(MORUS, (0, 0, 0, 0, 0, 0), hook="steal"),
    BossPassive(RED_DRAGON, (12, 0, 0, 0, 0, 0), GEAR_STRONG_FIRE),
    BossPassive(WHITE_DRAGON, (0, 0, 15, 0, 0, 0), GEAR_STRONG_WIND),
    BossPassive(BLACK_DRAGON, (0, 15, 0, 0, 0, 0), GEAR_STRONG_EARTH),
    BossPassive(BLUE_DRAGON, (0, 0, 0, 15, 0, 0), GEAR_STRONG_WATER),
    BossPassive(DARK_JIAN, (5, 5, 5, 5, 5, 5)),
    BossPassive(GIDEON, (15, 0, 0, 0, 10, 0)),
)
BOSS_HOOKS = frozenset({"moran", "orcus", "steal"})

MONSTER_CARDS = frozenset(range(FIRST_CARD, FIRST_BOSS_CARD))
PAIRED = frozenset(pair.card for pair in PAIRS)
SLOTTABLE = MONSTER_CARDS | frozenset(passive.card for passive in BOSS_PASSIVES)


def _check() -> None:
    """The tables cover each card exactly once and name only spells that exist."""
    groups = (PAIRED, ONE_VERSION, FIELD_CARDS)
    if (
        sum(len(group) for group in groups) != len(MONSTER_CARDS)
        or frozenset().union(*groups) != MONSTER_CARDS
    ):
        raise ValueError(
            "pairs, one-version cards, and field cards must split the 34 monster cards"
        )
    if len(PAIRED) != len(PAIRS):
        raise ValueError("a card is paired twice")
    bosses = [passive.card for passive in BOSS_PASSIVES]
    if len(set(bosses)) != len(bosses) or set(bosses) & DEFERRED_BOSS_CARDS:
        raise ValueError("boss passives: a card twice, or a deferred card")
    if not all(FIRST_BOSS_CARD <= card <= LAST_CARD for card in bosses):
        raise ValueError("a boss passive names a card that is not a boss card")
    if len(bosses) + len(DEFERRED_BOSS_CARDS) != LAST_CARD - FIRST_BOSS_CARD + 1:
        raise ValueError("every boss card is either given a passive or deferred")
    for passive in BOSS_PASSIVES:
        if passive.hook and passive.hook not in BOSS_HOOKS:
            raise ValueError(f"unknown boss hook {passive.hook!r}")
    for pair in PAIRS:
        for owner, spell in pair.learners:
            if spell not in GAME_SPELLS and (
                spell not in BY_SPELL or BY_SPELL[spell].owner != owner
            ):
                raise ValueError(
                    f"card {pair.card}: spell {spell} is not member {owner}'s"
                )
    for card, spells in BOOSTS.items():
        pair = next((pair for pair in PAIRS if pair.card == card), None)
        if pair is None or any(spell not in spells for _owner, spell in pair.learners):
            raise ValueError(
                f"card {card}: an enhancing card must be paired, and enhance its pair's skills"
            )
    boosted = [spell for spells in BOOSTS.values() for spell in spells]
    if len(set(boosted)) != len(boosted):
        raise ValueError("a spell is enhanced by two cards")


_check()
