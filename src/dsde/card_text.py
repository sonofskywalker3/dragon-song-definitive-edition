"""What each card says on the Cards equip page (docs/plan-cards.md 7.7): DRAFT for Jeff's approval.

Item descriptions are sysmenupack entry 58 ("CMTX"): a header, a u16 table, then one fixed 61-byte record per item
id from 0x346 (60 characters, the end byte, spaces after it). The equip page shows a record as two lines of 30
characters, so a line is padded to 30 to start the next. The menu font has no %, +, or parentheses.

The first line says what the card does for anyone who wears it. A card that matches a skill gets a second line
for a wearer who knows that skill: the card then powers up the skill (cards_data.BOOSTS) instead of being used
itself. A boss card says what it gives while worn.
"""

from functools import cache
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.cards_common import FIRST_CARD, LAST_CARD
from dsde.patching import DataPatch
from dsde.skills_common import encode

VANILLA_SYSMENUPACK = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "sysmenupack.dat"
)
ARCHIVE = "sysmenupack"
DESCRIPTIONS = 58
FIRST_RECORD = 0x346
RECORD = 61
LINE = 30
SPACE = 0x00

# card item id order: 216 Blob .. 249 Druid, 250 Sasquatch .. 269 Ignatius
LINES: dict[str, tuple[str, ...]] = {
    "Blob": ("Symbols move slower",),
    "Onlooker": ("Lowers all enemies' AGI",),
    "Shreeker": ("Poisons one enemy", "Venom Claw poison hits harder"),
    "Namia": ("Party regains HP each turn", "Divine Rain heals double"),
    "Treant": ("Recovers HP on the map", "for a while"),
    "Ice Mongrel": ("Always escapes from battle",),
    "Mad Fang": ("Draws symbols toward you",),
    "Yeti": ("Steals an item from an enemy",),
    "Termite": ("Keeps one ally's gear from", "breaking this battle"),
    "Abadon": ("Lowers one enemy's DEF", "Armor Break lowers DEF twice"),
    "Tick": ("Paralyzes one enemy", "Water Bind and Howl always hit"),
    "Bealzebub": ("One ally's attacks never miss", "Focus covers the whole party"),
    "Insector": ("Party deals more damage", "for 2 to 4 rounds"),
    "Gloomwing": ("Recovers MP on the map", "for a while"),
    "Kuntukapu": ("Party regains MP each turn", "for 2 to 4 rounds"),
    "Ikontabipu": ("Puts one enemy to sleep", "Knockout Kick always lands"),
    "Dagon": ("Turns one enemy to stone",),
    "Hellbird": ("Fully restores one ally's MP",),
    "Sturge": ("Raises the party's LUK",),
    "Vitra": ("Fully restores one ally's HP", "Tender Rain heals to full"),
    "Quetzalcoatl": ("Lowers one enemy's ATK", "Weapon Break lowers ATK twice"),
    "Comet": ("Raises one ally's INT", "Stratagem raises INT twice"),
    "Ohainkaru": ("Stops symbols for a while",),
    "Shaitan": ("Revives one ally at full HP", "Miracle Tears revives at full"),
    "Phantom": ("Silences all enemies",),
    "Ochu": ("Party takes less damage", "for 2 to 4 rounds"),
    "Evil Earth": ("Raises the party's DEX",),
    "Chupacabra": ("Lowers all enemies' DEX",),
    "Enigma": ("Lowers all enemies' INT",),
    "Ghoula": ("Symbols flee for a while",),
    "Thanatos": ("Lowers all enemies' LUK",),
    "Asmodee": ("Blinds one enemy", "Blinding Swipe lasts longer"),
    "Duager": ("Lowers all enemies' stats",),
    "Druid": ("Confuses all enemies",),
    "Sasquatch": ("Worn: raises ATK 4, DEF 8",),
    "Armored Boar": ("Worn: raises DEF 8", "Hits sometimes deal double"),
    "Raft": ("Worn: raises AGI 12, DEX 5",),
    "Sharif": ("Worn: raises LUK 10", "Wearer cannot be blinded"),
    "Moran": ("Worn: hits may lower an", "enemy's DEF"),
    "Deuce": ("Worn: raises DEF 12, LUK 8",),
    "Gronk": ("Worn: raises INT 12", "Takes less wind damage"),
    "Zethos": ("Worn: raises ATK 12, LUK 10",),
    "Caucus": ("Worn: raises INT 10", "Regains some HP each turn"),
    "Orcus": ("Worn: hits may lower an", "enemy's ATK"),
    "Morus": ("Worn: gives the Steal command",),
    "Red Dragon": ("Worn: raises ATK 12", "Takes half damage from fire"),
    "White Dragon": ("Worn: raises AGI 15", "Takes half damage from wind"),
    "Black Dragon": ("Worn: raises DEF 15", "Takes half damage from earth"),
    "Blue Dragon": ("Worn: raises INT 15", "Takes half damage from water"),
    "Dark Jian": ("Worn: raises every stat 5",),
    "Gideon": ("Worn: raises ATK 15, DEX 10",),
    "Gideon 2": ("A collection card", "It cannot be used"),
    "Gideon 3": ("A collection card", "It cannot be used"),
    "Ignatius": ("A collection card", "It cannot be used"),
}


def record(lines: tuple[str, ...]) -> bytes:
    """A description record: each line padded to the box's width, the end byte, spaces to 61 bytes."""
    if any(len(line) > LINE for line in lines) or len(lines) > 2:
        raise ValueError(f"card text too long for two lines of {LINE}: {lines}")
    text = "".join(line.ljust(LINE) for line in lines[:-1]) + lines[-1]
    data = encode(text)
    return data + bytes([SPACE]) * (RECORD - len(data))


@cache
def _vanilla() -> bytes:
    return decompress(read_archive(VANILLA_SYSMENUPACK.read_bytes())[DESCRIPTIONS])


def card_text_patches() -> tuple[DataPatch, ...]:
    if len(LINES) != LAST_CARD - FIRST_CARD + 1:
        raise ValueError("card text needs one entry per card")
    data = _vanilla()
    start = FIRST_RECORD + FIRST_CARD * RECORD
    end = start + len(LINES) * RECORD
    new = b"".join(record(lines) for lines in LINES.values())
    return (
        DataPatch(
            ARCHIVE,
            DESCRIPTIONS,
            start,
            data[start:end],
            new,
            "what each card does, on the Cards equip page",
        ),
    )
