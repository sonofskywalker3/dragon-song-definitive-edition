"""Lucia and Flora learn their spells by level (Jeff, 2026-10-08: six spells at level 5 was too many, too soon).

Vanilla shows a spell (func_02050c50) when the character's level reaches the spell's minimum level byte (entry
+0x08 for Lucia, +0x09 for Flora; all 0, and 255 for Flora's Miracle Tears) and her max MP reaches the spell's
cost. With costs that small the MP test decided everything: Lucia had six spells at level 5. Here the level
bytes carry a schedule for each of them (Jeff, 2026-11-12):

- Quick, Grand Weapon, and Grand Shell are learned by neither: the stat buffs are Rufus's orders now
  (skills_rufus.py), and a healer's buff would stack a second stage on top of his.
- Lucia's six spells run to level 13, more spread out than before now that the buffs are gone; she leaves the
  party for good at Sungrid Bridge, around level 11 to 14.
- Flora joins near level 13 (at Jian's EXP) knowing the first four, and her list runs to the end of the game:
  Divine Rain at 20 and Miracle Tears at 32, which vanilla never gave her and without which the last party
  has no revive spell. Her own two water spells are skills (skills_flora.py, levels 16 and 28).

The MP test always passes, so the cost only says what a cast takes. Known spells are not saved; they are worked
out from the level each time, so old saves follow the new schedule.
"""

from dsde.patching import AsmPatch, Feature, Patch

SPELL_TABLE = 0x02094978  # 0x0C bytes per spell: flags, MP cost, Lucia level, Flora level, u16 effect
SPELL_ENTRY_SIZE = 0x0C
SPELL_LEVELS = 0x08  # u32 at the entry: Lucia level byte, Flora level byte, u16 effect
LEVEL_MASK = 0xFFFF  # both level bytes
FLORA_SHIFT = 8
UNLOCK_COST_CALL = (
    0x02050DE8  # func_02050c50: bl func_020500c4 (spell cost) before the max MP test
)
UNLOCK_COST_CALL_WORD = 0xEBFFFCB5
NEVER = 0xFF  # level byte: never learned
# spell index: (name, Lucia's level, Flora's level (1-based, None = never), vanilla word at +0x08)
SCHEDULE: dict[int, tuple[str, int | None, int | None, int]] = {
    1: ("Healing Water", 1, 1, 0x00000000),
    3: ("Cure Squall", 4, 4, 0x002E0000),
    6: ("Escape", 6, 6, 0x00000000),
    2: ("Tender Rain", 8, 8, 0x000E0000),
    4: ("Divine Rain", 11, 20, 0x000F0000),
    5: ("Miracle Tears", 13, 32, 0x0026FF00),
    7: ("Quick", None, None, 0x00170000),
    8: ("Grand Weapon", None, None, 0x00150000),
    9: ("Grand Shell", None, None, 0x00160000),
}


def _level_byte(level: int | None) -> int:
    """A learn level as the table stores it: 0-based, or the 'never' byte."""
    return NEVER if level is None else level - 1


def _levels_word(lucia: int | None, flora: int | None, vanilla: int) -> int:
    """The entry's level word with each healer's own level; the effect row in the high half is kept."""
    return (
        (vanilla & ~LEVEL_MASK)
        | (_level_byte(flora) << FLORA_SHIFT)
        | _level_byte(lucia)
    )


def _note(name: str, lucia: int | None, flora: int | None) -> str:
    if lucia is None and flora is None:
        return f"{name}: learned by neither healer"
    return f"{name}: Lucia at level {lucia}, Flora at level {flora}"


SPELL_LEVELS_FEATURE = Feature(
    "spell-levels",
    (
        AsmPatch(
            UNLOCK_COST_CALL,
            UNLOCK_COST_CALL + 4,
            UNLOCK_COST_CALL_WORD,
            UNLOCK_COST_CALL_WORD,
            "mov r0, #0",
            "spells no longer wait for max MP",
        ),
        *(
            Patch(
                SPELL_TABLE + index * SPELL_ENTRY_SIZE + SPELL_LEVELS,
                vanilla,
                _levels_word(lucia, flora, vanilla),
                _note(name, lucia, flora),
            )
            for index, (name, lucia, flora, vanilla) in SCHEDULE.items()
        ),
    ),
)
