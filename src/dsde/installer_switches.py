"""The custom installer's switches (docs/plan-installer.md section 3, approved by Jeff on 2026-11-26).

Each switch names the features it builds (features.py), the switches it needs, and whether it is on by default.
The defaults equal the full release: every switch on except Retold party chat. ALWAYS is built whatever the
switches say. A switch whose need is off is greyed out with the reason, and switching a need off switches its
dependents off (`resolve_switches`).
"""

from dataclasses import dataclass
from types import MappingProxyType

EXPLORING = "Exploring"
MENUS = "Menus and text"
BATTLES = "Battles"
SPELLS = "Spells and skills"
CARDS = "Cards"
EXTRAS = "Fixes and extras"
STORY = "Story"
GROUPS = (EXPLORING, MENUS, BATTLES, SPELLS, CARDS, EXTRAS, STORY)

# Built in every patch: the title seal says which build this is, and the save glitch fix (Jeff, 2026-11-26).
ALWAYS: tuple[str, ...] = ("title-seal", "fix-save-glitch")

RETOLD_DETAILS = (
    "I'm rewriting the game's dialogue to be truer to Lunar: The Silver Star and Lunar 2: Eternal Blue, the "
    "canon this story leads into. The rewrite rests on research into every earlier script of both games and the "
    "original Japanese of each, Dragon Song's included. It has only just begun: so far, a new opening narration "
    "retranslated from the Japanese and a new wake-up scene. More arrives with each release.\n"
    "Off: the original English dialogue, word for word."
)


@dataclass(frozen=True)
class Switch:
    number: int
    group: str
    label: str
    tooltip: str
    features: tuple[str, ...]
    needs: tuple[int, ...] = ()
    default: bool = True
    details: str = ""


SWITCHES: tuple[Switch, ...] = (
    Switch(
        1,
        EXPLORING,
        "No HP drain while running",
        "Running no longer costs HP, and you can still run at low HP.",
        ("no-run-hp-cost",),
    ),
    Switch(
        2,
        EXPLORING,
        "Timed dash with cooldown",
        "Where enemies are about, B starts a dash of about 3 seconds, then a 3-second cooldown. Where there are "
        "none left, you run for as long as you hold B.",
        ("timed-run",),
        needs=(1,),
    ),
    Switch(
        3,
        EXPLORING,
        "Run gauge in the pocketwatch",
        "The pocketwatch is open while an area has enemies, and its hand shows the dash and the cooldown. It "
        "closes once every enemy in the area is beaten.",
        ("pocketwatch",),
        needs=(2,),
    ),
    Switch(
        4,
        EXPLORING,
        "Walking and running 50% faster",
        "Jian walks and runs 1.5 times as fast as in the original. Scripted walks keep their speed.",
        ("walk-speed",),
    ),
    Switch(
        5,
        EXPLORING,
        "No slowdown on ramps and stairs",
        "Slopes no longer cut your speed to less than half.",
        ("no-ramp-slowdown",),
    ),
    Switch(
        6,
        EXPLORING,
        "Enemies return when you enter an area, not on a timer",
        "Beaten enemies stay gone until you leave the area and come back. The Virtue clock no longer brings them "
        "back.",
        ("restock-on-entry", "no-virtue-clock"),
    ),
    Switch(
        7,
        EXPLORING,
        "Clearing an area no longer refills HP and MP",
        "Beating every enemy in an area no longer gives back 30% of HP and MP.",
        ("no-clear-refill",),
    ),
    Switch(
        8,
        EXPLORING,
        "Healing statues work from any side, heal faster, and cure status",
        "Press A at a statue from any side. The camera no longer pans to it and back, and it cures poison and "
        "other statuses too.",
        ("statue-any-side",),
    ),
    Switch(
        9,
        EXPLORING,
        "D-pad in town and world map menus",
        'In a "Select place to go" menu, Up and Down pick a place, Left and Right change the tab, and A goes.',
        ("town-menu-dpad",),
    ),
    Switch(
        10,
        EXPLORING,
        "B in a town menu selects Leave town",
        'B selects "Leave town", ready for A, instead of the place you just left.',
        ("town-menu-leave",),
    ),
    Switch(
        11,
        EXPLORING,
        "The HUD stops pulsing",
        "The Menu note, the leader's portrait, and the party chat figures on the field screen hold still.",
        ("still-hud",),
    ),
    Switch(
        12,
        MENUS,
        "Select opens Save",
        "Select in the field opens the save screen directly.",
        ("menu-select-save",),
        needs=(14,),
    ),
    Switch(
        13,
        MENUS,
        "Select leaves the menu from any screen",
        "Select anywhere in the menu goes straight back to the map.",
        ("menu-select-exit",),
    ),
    Switch(
        14,
        MENUS,
        "Faster menus (shorter waits, fades, and key repeat)",
        "Menu screens open in about a quarter of the time, fades take a third, and a held key repeats.",
        ("menu-speed",),
    ),
    Switch(
        15,
        MENUS,
        "Hold A for fast text",
        "Holding A types text three times as fast. Press A again to turn the page.",
        ("text-hold-a",),
    ),
    Switch(
        16,
        MENUS,
        "Hold B for fast text and auto-advance",
        "Holding B types text three times as fast and turns the pages by itself.",
        ("text-hold-b",),
    ),
    Switch(
        17,
        MENUS,
        "The guidebook explains this version's rules",
        "The Adventure Guidebook (Start) describes the rules you switched on, in the book's own lettering.",
        ("guidebook",),
    ),
    Switch(
        18,
        MENUS,
        '"Experience" in place of "Althena Conduct"',
        "The status screen and the victory screen say Experience.",
        ("experience-name",),
    ),
    Switch(
        19,
        MENUS,
        "Name and typo fixes in the job menu and messages",
        "Name tags match the names in the job menu, as in the Japanese release.",
        ("text-fixes",),
    ),
    Switch(
        20,
        BATTLES,
        "Experience and items from every battle (one battle mode)",
        "The Combat and Virtue modes are gone: every battle gives experience and items.",
        ("one-battle-mode",),
    ),
    Switch(
        21,
        BATTLES,
        "Silver from battles",
        "A battle gives as much silver as experience.",
        ("silver-drops",),
    ),
    Switch(
        22,
        BATTLES,
        "Bosses give experience",
        "Each boss gives about ten regular enemies' worth of experience from its area.",
        ("boss-exp",),
    ),
    Switch(
        23,
        BATTLES,
        "The reworked result screens",
        "The victory screen counts experience (and silver, with Silver from battles) up from your totals, and a "
        "second page lists the items received.",
        ("result-screens",),
    ),
    Switch(
        24,
        BATTLES,
        "Pick your own targets",
        "Pick an enemy on the touch screen or with the D-pad, on a grid laid out like the battlefield. An attack "
        "whose target dies moves to the next enemy.",
        ("manual-targeting",),
    ),
    Switch(
        25,
        BATTLES,
        "Battle speeds with R (and their sign)",
        "Tap R in battle to cycle Fast, Faster, and Normal (the original timing), shown on a plank under the "
        "status bar. Off: battles stay on Fast.",
        ("battle-speed",),
    ),
    Switch(
        26,
        BATTLES,
        "Faster party actions",
        "On Fast and Faster: quicker moves, shorter kill flashes and victory screens, faster attacks for Lucia, "
        "Gabryel, and Rufus, and no wait for a beaten enemy's sparkles.",
        ("battle-pace", "battle-flow"),
    ),
    Switch(
        27,
        BATTLES,
        "Enemies die on their killing hit",
        "On Fast and Faster, each enemy dies on the hit that kills it, not all together after the combo.",
        ("kill-on-hit",),
    ),
    Switch(
        28,
        BATTLES,
        "Faster enemy animations",
        "On Fast, the acting enemy animates as fast as the party.",
        ("enemy-sprite-speed",),
    ),
    Switch(
        29,
        BATTLES,
        "Faster enemy spells",
        "On Fast, enemy spell effects play faster.",
        ("enemy-spell-speed",),
    ),
    Switch(
        30,
        BATTLES,
        "Shorter enemy steps",
        "On Fast, enemies hop once instead of four times, glide less, and crouch and land quicker. Every swing "
        "and hit is kept whole.",
        ("enemy-quick-steps",),
    ),
    Switch(
        31,
        BATTLES,
        "Hold L and R to run instead of the microphone (the sign follows)",
        "Hold L and R together for half a second to run from a battle; the battle sign says L+R. The "
        "microphone is ignored.",
        ("hold-lr-to-run", "mic-sign"),
    ),
    Switch(
        32,
        BATTLES,
        "Broken and stolen gear returned after a win",
        "Gear broken in battle comes back afterwards, and an item a thief stole is returned if you win.",
        ("gear-return",),
    ),
    Switch(
        33,
        BATTLES,
        "Benched members gain experience",
        "Characters out of the party earn the same experience as the party, so nobody falls behind.",
        ("benched-exp",),
    ),
    Switch(
        34,
        BATTLES,
        "A leaving member drops their gear",
        "A character who leaves the party leaves their gear in your inventory.",
        ("leave-drops-gear",),
    ),
    Switch(
        35,
        BATTLES,
        "No curse penalty",
        "Jian keeps his 3-hit combo while cursed.",
        ("no-curse-penalty",),
    ),
    Switch(
        36,
        BATTLES,
        "Curse restricts healing",
        "While Jian is cursed, items don't heal him and healing magic heals him less. Statues and revives still "
        "work.",
        ("curse-no-healing",),
    ),
    Switch(
        37,
        SPELLS,
        "Spells cost about 40% of their MP",
        "Healing Water 4, Cure Water 4, Escape 2, Tender Rain 12, Divine Rain 16, and Miracle Tears 20 MP.",
        ("spell-costs",),
    ),
    Switch(
        38,
        SPELLS,
        "MP items restore a flat amount",
        "Mental Gum and Mental Drop restore a set amount of MP, not a share of max MP. Mental Gum costs 1000 "
        "and is sold in item shops from the third town on.",
        ("mp-items",),
    ),
    Switch(
        39,
        SPELLS,
        "Healers learn spells by level",
        "Lucia and Flora learn their spells one level at a time, in learn order.",
        ("spell-levels",),
    ),
    Switch(
        40,
        SPELLS,
        "Level-learned skills for Jian, Gabryel, Rufus, and Flora",
        "Skills learned by level and cast from Special for MP.",
        ("skills",),
        needs=(24,),
    ),
    Switch(
        41,
        SPELLS,
        "Special list icons for every spell and skill",
        "Each box in the Special list shows a picture. Off: the blank boxes.",
        ("skill-icons",),
    ),
    Switch(
        42,
        SPELLS,
        "Poison wears off after 2 to 4 turns",
        "Poison ends after 2 to 4 turns, on monsters and the party, instead of lasting the battle.",
        ("poison-turns",),
    ),
    Switch(
        43,
        CARDS,
        "Dragon ring slot: a ring slot for every member, and a ring's Dragon Magic for whoever wears it",
        "Every member gets a ring slot, and whoever wears a dragon ring can cast its Dragon Magic.",
        ("ring-slot",),
    ),
    Switch(
        44,
        CARDS,
        "Card system overhaul",
        "Equip monster cards to use them in battle or power up skills; they recharge as you fight.",
        ("cards",),
        needs=(40,),
    ),
    Switch(
        45,
        CARDS,
        "The bestiary",
        "The System list's Bestiary plank shows the cards you have found.",
        ("bestiary",),
        needs=(44,),
    ),
    Switch(
        46,
        EXTRAS,
        "Gad's Express jobs grow with the journey",
        "Delivery offices offer jobs whose items you can find by then, and one future job that pays more.",
        ("gad-express",),
    ),
    Switch(
        47,
        EXTRAS,
        "Retold party chat on Y",
        "Y opens Retold's party chat, with hints for where you are, in place of the original think-aloud.",
        ("party-chat",),
        default=False,
    ),
    Switch(
        48,
        STORY,
        "Retold story",
        "The rewritten dialogue, the intro that sends Jian straight to Lucia, the walk-out opening, and the blue "
        "title seal.",
        (
            "text-edits",
            "opening-flags",
            "opening-run",
            "opening-text",
            "title-seal-retold",
        ),
        details=RETOLD_DETAILS,
    ),
)
BY_NUMBER = MappingProxyType({switch.number: switch for switch in SWITCHES})


def defaults() -> frozenset[int]:
    return frozenset(switch.number for switch in SWITCHES if switch.default)


def dependents(number: int) -> frozenset[int]:
    """Every switch that needs `number`, directly or through another switch."""
    found: set[int] = set()
    todo = [number]
    while todo:
        need = todo.pop()
        for switch in SWITCHES:
            if need in switch.needs and switch.number not in found:
                found.add(switch.number)
                todo.append(switch.number)
    return frozenset(found)


def missing_needs(number: int, on: frozenset[int]) -> tuple[int, ...]:
    """The needs of a switch that are off: the reason it is greyed out."""
    return tuple(need for need in BY_NUMBER[number].needs if need not in on)


def resolve_switches(on: frozenset[int]) -> frozenset[int]:
    """The switches that are really on: a switch whose need is off is off too."""
    result = set(on)
    changed = True
    while changed:
        changed = False
        for number in sorted(result):
            if missing_needs(number, frozenset(result)):
                result.discard(number)
                changed = True
    return frozenset(result)


def feature_names(on: frozenset[int], order: tuple[str, ...]) -> list[str]:
    """The features to build for the switches on, plus ALWAYS, in the build order `order` (features.FEATURES)."""
    wanted = set(ALWAYS)
    for number in resolve_switches(on):
        wanted.update(BY_NUMBER[number].features)
    return [name for name in order if name in wanted]
