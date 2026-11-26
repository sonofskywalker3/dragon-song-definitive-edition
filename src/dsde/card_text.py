"""What each card says on the Cards equip page (docs/plan-cards.md 7.7), approved by Jeff 2026-11-26.

Item descriptions are sysmenupack entry 58 ("CMTX"): a header, a u16 table, then one fixed 61-byte record per item
id from 0x346 (60 characters, the end byte, spaces after it). The equip page shows a record as two lines of 30
characters, so a line is padded to 30 to start the next. The menu font has no %, +, or parentheses.

A card's own record says what it does for anyone who wears it. A card that powers up a skill (cards_data.BOOSTS)
has a second line: for a member who has that skill in their kit, it names the highest of the card's skills the
member has learned by now (War Breaker once Jian has it, Weapon Break before) and what the card does to it; for
anyone else, "Powers up" and the card's first skill. Those
two-line texts are extra records after the game's 417 (the game loads the whole file, so they cost no cave
space), and the equip page's two description draws (states 0x18 and 0x19, `bl func_02066c44` with the item id in
r1) ask cave_card_text, which swaps in the record for the shown member and goes on to func_02066c44.
"""

from functools import cache
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.cards_common import (
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    CHARACTERS,
    FIRST_CARD,
    LAST_CARD,
)
from dsde.cards_data import BOOSTS, GAME_SPELLS
from dsde.feat_spell_levels import SCHEDULE
from dsde.patching import CaveCode, DataPatch
from dsde.skills_common import encode, hook
from dsde.skills_data import BY_SPELL
from dsde.skills_types import FLORA, LUCIA

VANILLA_SYSMENUPACK = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "sysmenupack.dat"
)
ARCHIVE = "sysmenupack"
DESCRIPTIONS = 58
FIRST_RECORD = 0x346
RECORD = 61
GAME_RECORDS = 417  # item ids 0 to 416
LINE = 30
SPACE = 0x00
HEALERS = (LUCIA, FLORA)  # the game spells' learners (feat_spell_levels.SCHEDULE)

# card item id order: 216 Blob .. 249 Druid, 250 Sasquatch .. 269 Ignatius
LINES: dict[str, tuple[str, ...]] = {
    "Blob": ("Symbols move slower",),
    "Onlooker": ("Lowers all enemies' AGI",),
    "Shreeker": ("Poisons one enemy",),
    "Namia": ("Party regains HP each turn",),
    "Treant": ("Recovers HP on the map",),
    "Ice Mongrel": ("Always escapes from battle",),
    "Mad Fang": ("Draws symbols toward you",),
    "Yeti": ("Steals an item from an enemy",),
    "Termite": ("One ally's gear won't break",),
    "Abadon": ("Lowers one enemy's DEF",),
    "Tick": ("Paralyzes one enemy",),
    "Bealzebub": ("One ally's attacks never miss",),
    "Insector": ("Party deals more damage", "for 2 to 4 rounds"),
    "Gloomwing": ("Recovers MP on the map",),
    "Kuntukapu": ("Party regains MP each turn", "for 2 to 4 rounds"),
    "Ikontabipu": ("Puts one enemy to sleep",),
    "Dagon": ("Turns one enemy to stone",),
    "Hellbird": ("Fully restores one ally's MP",),
    "Sturge": ("Raises the party's LUK",),
    "Vitra": ("Fully restores one ally's HP",),
    "Quetzalcoatl": ("Lowers one enemy's ATK",),
    "Comet": ("Raises one ally's INT",),
    "Ohainkaru": ("Stops symbols for a while",),
    "Shaitan": ("Revives one ally at full HP",),
    "Phantom": ("Silences all enemies",),
    "Ochu": ("Party takes less damage", "for 2 to 4 rounds"),
    "Evil Earth": ("Raises the party's DEX",),
    "Chupacabra": ("Lowers all enemies' DEX",),
    "Enigma": ("Lowers all enemies' INT",),
    "Ghoula": ("Symbols flee for a while",),
    "Thanatos": ("Lowers all enemies' LUK",),
    "Asmodee": ("Blinds one enemy",),
    "Duager": ("Lowers all enemies' stats",),
    "Druid": ("Confuses all enemies",),
    "Sasquatch": ("Raises ATK 4, DEF 8",),
    "Armored Boar": ("Raises DEF 8", "Hits may deal double"),
    "Raft": ("Raises AGI 12, DEX 5",),
    "Sharif": ("Raises LUK 10", "Prevents blindness"),
    "Moran": ("Hits may lower DEF",),
    "Deuce": ("Raises DEF 12, LUK 8",),
    "Gronk": ("Raises INT 12", "Lessens wind damage"),
    "Zethos": ("Raises ATK 12, LUK 10",),
    "Caucus": ("Raises INT 10", "Regains HP each turn"),
    "Orcus": ("Hits may lower ATK",),
    "Morus": ("Gives the Steal command",),
    "Red Dragon": ("Raises ATK 12", "Halves fire damage"),
    "White Dragon": ("Raises AGI 15", "Halves wind damage"),
    "Black Dragon": ("Raises DEF 15", "Halves earth damage"),
    "Blue Dragon": ("Raises INT 15", "Halves water damage"),
    "Dark Jian": ("Raises every stat 5",),
    "Gideon": ("Raises ATK 15, DEX 10",),
    "Gideon 2": ("A collection card", "It cannot be used"),
    "Gideon 3": ("A collection card", "It cannot be used"),
    "Ignatius": ("A collection card", "It cannot be used"),
}

# The second line for a member who has the skill: what the card does to it (cards_data.BOOSTS; feat_skills_boost).
POWER_UP: dict[int, str] = {
    38: "Doubles Weapon Break",
    42: "Doubles War Breaker",
    39: "Doubles Armor Break",
    43: "Doubles Wall Breaker",
    41: "Knockout Kick always lands",
    44: "Venom Claw poison: 2x damage",
    48: "Venom Rain poison: 2x damage",
    45: "Blinding Swipe lasts longer",
    49: "Blinding Gale lasts longer",
    47: "Howl always lands",
    50: "Dread Roar always lands",
    54: "Doubles Stratagem",
    58: "Doubles War Council",
    4: "Doubles Divine Rain",
    5: "Miracle Tears revives at full",
    2: "Tender Rain heals to full",
    40: "Focus covers the whole party",
}

# cave_card_text: the shown member's party slot, their character id, and their level index
MENU_WORK = 0x0213B27C  # +0x644: the party slot shown
MENU_WORK_MEMBER = 0x644
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart
LEVEL_OFFSET = 0xC  # the level index in a character record
TEXT_DRAW = (
    0x02066C44  # (handle, item, column, row, [sp] width, ..., [sp + 0xC] record size)
)
TEXT_DRAWS = ((0x0205D600, 0xEB00258F), (0x0205D918, 0xEB0024C9))
TABLE_END = 0xFF
ENTRY = 4  # card - FIRST_CARD, character, level index from which it shows, extra record


def record(lines: tuple[str, ...]) -> bytes:
    """A description record: each line padded to the box's width, the end byte, spaces to 61 bytes."""
    if any(len(line) > LINE for line in lines) or len(lines) > 2:
        raise ValueError(f"card text too long for two lines of {LINE}: {lines}")
    text = "".join(line.ljust(LINE) for line in lines[:-1]) + lines[-1]
    data = encode(text)
    return data + bytes([SPACE]) * (RECORD - len(data))


def _learns(member: int, spell: int) -> int | None:
    """The level index at which `member` has `spell`, or None if it is not in their kit."""
    if spell in GAME_SPELLS:
        if member not in HEALERS:
            return None
        level = SCHEDULE[spell][1 if member == LUCIA else 2]
        return None if level is None else level - 1
    skill = BY_SPELL[spell]
    return skill.level - 1 if skill.owner == member else None


@cache
def _power_ups() -> tuple[list[tuple[int, int, int, int]], list[bytes]]:
    """(table entries, extra records): per card and member, the card's skills in their kit, highest first; the
    lowest shows from level index 0, so a member who will learn the skill sees it named before they do. A member
    without any of them sees "Powers up" and the card's first skill (Jeff, 2026-11-26: no member names)."""
    names = list(LINES)
    entries: list[tuple[int, int, int, int]] = []
    extra: list[bytes] = []
    for card, spells in BOOSTS.items():
        first_line = LINES[names[card - FIRST_CARD]][0]
        for member in range(CHARACTERS):
            kit = sorted(
                (
                    (level, spell)
                    for spell in spells
                    if (level := _learns(member, spell)) is not None
                ),
                reverse=True,
            )
            if not kit:
                entries.append((card - FIRST_CARD, member, 0, len(extra)))
                extra.append(
                    record((first_line, f"Powers up {_spell_name(spells[0])}"))
                )
                continue
            for k, (level, spell) in enumerate(kit):
                shown_from = 0 if k == len(kit) - 1 else level
                entries.append((card - FIRST_CARD, member, shown_from, len(extra)))
                extra.append(record((first_line, POWER_UP[spell])))
    return entries, extra


def _spell_name(spell: int) -> str:
    return SCHEDULE[spell][0] if spell in GAME_SPELLS else BY_SPELL[spell].name


@cache
def _vanilla() -> bytes:
    return decompress(read_archive(VANILLA_SYSMENUPACK.read_bytes())[DESCRIPTIONS])


def _descriptions() -> bytes:
    if len(LINES) != LAST_CARD - FIRST_CARD + 1:
        raise ValueError("card text needs one entry per card")
    data = _vanilla()
    start = FIRST_RECORD + FIRST_CARD * RECORD
    end_cards = start + len(LINES) * RECORD
    end_records = FIRST_RECORD + GAME_RECORDS * RECORD
    cards = b"".join(record(lines) for lines in LINES.values())
    _, extra = _power_ups()
    return (
        data[:start]
        + cards
        + data[end_cards:end_records]
        + b"".join(extra)
        + data[end_records:]
    )


def _table_asm() -> str:
    entries, _ = _power_ups()
    rows = [f"    .byte {c}, {m}, {lv}, {k}" for c, m, lv, k in entries]
    return "\n".join(rows) + f"\n    .byte {TABLE_END}, 0, 0, 0"


# In place of `bl func_02066c44` (r1 = the item): a boosted card's two-line record for the shown member, if they
# have one of its skills by their level; otherwise the item's own record. Every other register is kept.
TEXT_ASM = f"""
    push  {{r0, r2-r6, lr}}
    subs  r4, r1, #{FIRST_CARD:#x}
    bmi   ct_done
    cmp   r4, #{len(LINES)}
    bhs   ct_done
    ldr   r5, ct_work
    ldr   r5, [r5, #{MENU_WORK_MEMBER:#x}]
    ldr   r6, ct_party
    add   r6, r6, r5, lsl #2
    ldrsh r5, [r6]
    cmp   r5, #{CHARACTERS}
    bhs   ct_done
    ldr   r6, ct_records
    mov   r2, #{CHAR_RECORD_SIZE:#x}
    mla   r6, r5, r2, r6
    ldr   r6, [r6, #{LEVEL_OFFSET:#x}]
    ldr   r2, ct_table
ct_entry:
    ldrb  r3, [r2]
    cmp   r3, #{TABLE_END:#x}
    beq   ct_done
    cmp   r3, r4
    bne   ct_next
    ldrb  r3, [r2, #1]
    cmp   r3, r5
    bne   ct_next
    ldrb  r3, [r2, #2]
    cmp   r3, r6
    bhi   ct_next
    ldrb  r3, [r2, #3]
    ldr   r1, ct_first_extra
    add   r1, r1, r3
    b     ct_done
ct_next:
    add   r2, r2, #{ENTRY}
    b     ct_entry
ct_done:
    pop   {{r0, r2-r6, lr}}
    b     {TEXT_DRAW:#x}
ct_work:
    .word {MENU_WORK:#x}
ct_party:
    .word {PARTY:#x}
ct_records:
    .word {CHAR_RECORDS:#x}
ct_table:
    .word ${{cave_card_text_table}}
ct_first_extra:
    .word {GAME_RECORDS}
"""


def card_text_patches() -> tuple[CaveCode | DataPatch, ...]:
    entries, _ = _power_ups()
    if len(entries) > TABLE_END:
        raise ValueError("too many power-up texts for the byte-sized table")
    return (
        DataPatch(
            ARCHIVE,
            DESCRIPTIONS,
            0,
            _vanilla(),
            _descriptions(),
            "what each card does, and the skill it powers up for the member shown",
            whole=True,
        ),
        CaveCode(
            "cave_card_text_table",
            _table_asm(),
            "card text: which power-up line for which member",
        ),
        CaveCode(
            "cave_card_text",
            TEXT_ASM,
            "card text: the power-up line for the member shown",
        ),
        *(
            hook(
                addr,
                word,
                "bl ${cave_card_text}",
                "card text: the power-up line for the member shown",
            )
            for addr, word in TEXT_DRAWS
        ),
    )
