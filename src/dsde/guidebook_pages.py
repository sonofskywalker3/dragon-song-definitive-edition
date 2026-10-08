"""Layout and original text of the Adventure Guidebook pages (feat_guidebook.py, guidebook_font.py).

Each page is a 256x192 picture in pack.dat with two panels of ruled lines; the right panel is the left one moved
PANEL_SHIFT columns right. Research: docs/re-field-menu.md.
"""

from dataclasses import dataclass

PANEL_SHIFT = 128  # the right panel is the left one moved right
LINE_HEIGHT = 12  # rows of a text line, from its top to the row above its rule


@dataclass(frozen=True)
class Page:
    """One guidebook screen: its picture and palette entries in pack.dat and its panel layout."""

    picture: int
    palette: int
    first_rule: int  # row of the first text line's rule
    slots: int  # text lines per panel
    indented: int  # leading lines beside the picture
    heading_top: int  # rows of the heading pill
    heading_bottom: int


TOP = {
    "first_rule": 62,
    "slots": 9,
    "indented": 2,
    "heading_top": 33,
    "heading_bottom": 46,
}
BOTTOM = {
    "first_rule": 30,
    "slots": 11,
    "indented": 2,
    "heading_top": 1,
    "heading_bottom": 14,
}
TOWNS_TOP = Page(0xAB, 0xAA, **TOP)
TOWNS_BOTTOM = Page(0xAC, 0xAA, **BOTTOM)
FIELDS_TOP = Page(0xAE, 0xAD, **TOP)
FIELDS_BOTTOM = Page(0xAF, 0xAD, **BOTTOM)
RULE_PITCH = 16
INDENT_X = 50  # left panel: indented lines' rule start
FULL_X = 8  # left panel: full lines' rule start
PANEL_END = 119  # left panel: last column of a rule

# Vanilla body text, line by line, for each (page, panel). None: the line holds an icon too, not cut.
ORIGINAL_LINES: dict[tuple[Page, int], tuple[str | None, ...]] = {
    (TOWNS_TOP, 0): (
        "Hold the",
        "B Button",
        "when moving to",
        "run. Running",
        "consumes HP, and",
        "at 1/3 HP you can",
        "no longer run.",
    ),
    (TOWNS_TOP, 1): (
        "Althena",
        "Statues",
        "can be seen in",
        "many places.",
        "Press the",
        "A Button in front",
        "of one to fully",
        "heal.",
    ),
    (TOWNS_BOTTOM, 0): (
        "Save the",
        "game to",
        "continue play",
        None,
        "from the menu",
        "screen, and then",
        "save.",
        "You can save up",
        "to 3 games.",
    ),
    (TOWNS_BOTTOM, 1): (
        "Select",
        None,
        "the menu screen",
        "and select the",
        "item to change.",
        "Use A Button or",
        "touch to select.",
        "and L Button or",
        "R Button to",
        "Change members.",
    ),
    (FIELDS_TOP, 0): (
        "Defeat",
        "monsters",
        "to get items.",
        "Althena Conducts",
        "cannot be earned.",
        "Use AC to power",
        "up characters.",
        "Monsters will",
        "revive later.",
    ),
    (FIELDS_TOP, 1): (
        "Defeat",
        "monsters",
        "and get Althena",
        "Conducts, but",
        "not items.",
        "A check will be",
        "awarded per win.",
        None,
        "revive here.",
    ),
    (FIELDS_BOTTOM, 0): (
        "After",
        "each win",
        "the clock fills",
        "to MAX, then",
        "gradually",
        "decreases. After",
        "each revolution,",
        "a check is gone",
        "and a monster",
        "will revive.",
    ),
    (FIELDS_BOTTOM, 1): (
        "Clear map",
        "of all",
        "monsters in",
        "Virtue mode and",
        "all check boxes",
        "are checked, then",
        "the blue boxes",
        "will open, and",
        "30% HP and MP",
        "will be regained.",
    ),
}


def heading_rows(page: Page) -> range:
    return range(page.heading_top, page.heading_bottom + 1)


# Letters the vanilla text never shows cleanly, drawn in the same style: capitals on rows 2..9 with a
# half-strength last row, stems at full strength. Digits are coverage tenths ("9" full), "." none.
HANDMADE: dict[str, tuple[str, ...]] = {
    "E": (
        "......",
        "......",
        "999997",
        "9.....",
        "9.....",
        "977774",
        "9.....",
        "9.....",
        "977777",
        "444444",
    ),
    "F": (
        "......",
        "......",
        "999997",
        "9.....",
        "9.....",
        "977774",
        "9.....",
        "9.....",
        "9.....",
        "4.....",
    ),
    "H": (
        ".......",
        ".......",
        "9.....9",
        "9.....9",
        "9.....9",
        "9777779",
        "9.....9",
        "9.....9",
        "9.....9",
        "4.....4",
    ),
    "N": (
        ".......",
        ".......",
        "94....9",
        "979...9",
        "9.79..9",
        "9..79.9",
        "9...799",
        "9....99",
        "9.....9",
        "4.....4",
    ),
    "O": (
        ".......",
        "..441..",
        ".69996.",
        "48...84",
        "9.....9",
        "9.....9",
        "9.....9",
        "66...66",
        ".87778.",
        "..444..",
    ),
    "T": (
        ".......",
        ".......",
        "9999999",
        "...9...",
        "...9...",
        "...9...",
        "...9...",
        "...9...",
        "...9...",
        "...4...",
    ),
    "3": (
        "......",
        "......",
        ".7997.",
        "6...79",
        "....9.",
        "..997.",
        "....79",
        "9....9",
        "69..96",
        ".4774.",
    ),
    "j": ("...", "..2", "..9", "..4", "..7", "..7", "..7", "..7", "..7", "..7", "64."),
    ",": ("..", "..", "..", "..", "..", "..", "..", "..", "95", ".9", "5."),
    "(": ("...", "..6", ".7.", "7..", "9..", "9..", "9..", "9..", "7..", ".7.", "..6"),
    ")": ("...", "6..", ".7.", "..7", "..9", "..9", "..9", "..9", "..7", ".7.", "6.."),
    "+": (
        ".....",
        ".....",
        ".....",
        ".....",
        "..9..",
        "..9..",
        "99999",
        "..9..",
        "..9..",
        ".....",
    ),
}
FULL_TENTHS = 9
