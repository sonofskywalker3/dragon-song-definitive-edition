"""Lucia and Flora learn their spells by level (Jeff, 2026-10-08: six spells at level 5 was too many, too soon).

Vanilla shows a spell (func_02050c50) when the character's level reaches the spell's minimum level byte (entry
+0x08 for Lucia, +0x09 for Flora; all 0) and her max MP reaches the spell's cost. With costs that small the MP
test decided everything: Lucia had six spells at level 5. Here the level bytes carry a schedule that finishes by
level 12, because Lucia leaves the party for good at Sungrid Bridge (after Zethos, fight level 10, before Elda
Canyon, 16). Flora (joins at level 1) uses the same levels, and keeps her 255 on Miracle Tears, which she never
learns. The MP test always passes, so the cost only says what a cast takes. Known spells are not saved; they are
worked out from the level each time, so old saves follow the new schedule.
"""

from dsde.patching import AsmPatch, Feature, Patch

SPELL_TABLE = 0x02094978  # 0x0C bytes per spell: flags, MP cost, Lucia level, Flora level, u16 effect
SPELL_ENTRY_SIZE = 0x0C
SPELL_LEVELS = 0x08  # u32 at the entry: Lucia level byte, Flora level byte, u16 effect
LEVEL_MASK = 0xFFFF  # both level bytes
FLORA_SHIFT = 8
FLORA_NEVER = 0xFF
UNLOCK_COST_CALL = (
    0x02050DE8  # func_02050c50: bl func_020500c4 (spell cost) before the max MP test
)
UNLOCK_COST_CALL_WORD = 0xEBFFFCB5
SCHEDULE = {  # spell index: (name, level learned (1-based), vanilla word at +0x08)
    1: ("Healing Water", 1, 0x00000000),
    3: ("Cure Squall", 2, 0x002E0000),
    6: ("Escape", 3, 0x00000000),
    7: ("Quick", 4, 0x00170000),
    2: ("Tender Rain", 6, 0x000E0000),
    8: ("Grand Weapon", 7, 0x00150000),
    9: ("Grand Shell", 8, 0x00160000),
    4: ("Divine Rain", 10, 0x000F0000),
    5: ("Miracle Tears", 12, 0x0026FF00),
}


def _levels_word(level: int, vanilla: int) -> int:
    """The entry's level word with both characters at `level` (stored 0-based), Flora's 'never' kept."""
    flora = (vanilla >> FLORA_SHIFT) & 0xFF
    flora = FLORA_NEVER if flora == FLORA_NEVER else level - 1
    return (vanilla & ~LEVEL_MASK) | (flora << FLORA_SHIFT) | (level - 1)


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
                _levels_word(level, vanilla),
                f"{name} at level {level}",
            )
            for index, (name, level, vanilla) in SCHEDULE.items()
        ),
    ),
)
