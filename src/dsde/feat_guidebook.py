"""The Adventure Guidebook (Start in the field) describes this hack, not the original (Jeff, 2026-10-08).

Start shows script 027: one of two pages of pictures in pack.dat (docs/re-field-menu.md), Towns on town maps and
Fields elsewhere, each a top and a bottom screen with two panels. The original text described HP-costly running
and the Combat/Virtue modes, the Virtue clock and the area-clear refill, all gone here. The changed panels are
redrawn at build time with the guidebook's own letters (guidebook_font.py): the old lines are wiped back to the
ruled paper and the new text is wrapped over the same lines; a changed heading gets a new black pill sized to
its text. Pictures, icons, and unchanged panels stay as they are.
"""

from dataclasses import dataclass

from dsde.guidebook_font import WIDTH, Glyph, Picture, font, line_top
from dsde.guidebook_pages import (
    FIELDS_BOTTOM,
    FIELDS_TOP,
    FULL_X,
    INDENT_X,
    LINE_HEIGHT,
    PANEL_END,
    PANEL_SHIFT,
    TOWNS_BOTTOM,
    TOWNS_TOP,
    Page,
    heading_rows,
)
from dsde.patching import DataPatch, Feature

ARCHIVE = "pack"
LETTER_GAP = 1  # columns between letters (the vanilla text's most common gap)
SPACE = 4  # extra columns for a space, on top of the letter gap
INDENT_START = 6  # an indented line's text starts this far right of its rule
TEXT_RIGHT = PANEL_END - 2  # last column of text, as far as the vanilla text goes
WIPE_MARGIN = 1  # vanilla letters' soft edges reach one column left of the rule
FULL_START = 1
HEADING_LETTER_ROW = 2  # glyph row that lands on the pill's first letter row
PILL_LETTER_TOP = 4  # first letter row of the pill, from the heading band's top
INK: tuple[int, int, int] = (0, 0, 0)
WHITE: tuple[int, int, int] = (248, 248, 248)


@dataclass(frozen=True)
class PanelText:
    """New text for one panel: its heading (None: keep) and its body from line `first` on."""

    page: Page
    panel: int
    body: str
    first: int = 0
    heading: str | None = None


# Oxford comma, lowercase "experience" (docs/style-rules.md). Blue Chest panel: Jeff's wording, 2026-10-08.
PANELS = (
    PanelText(
        TOWNS_TOP,
        0,
        "Press the B Button to dash for about 3 seconds, then catch your breath. Running costs no HP. "
        "Once the pocketwatch closes, run freely.",
    ),
    PanelText(
        TOWNS_TOP,
        1,
        "Althena Statues can be seen in many places. Press the A Button beside one to fully heal and cure.",
    ),
    PanelText(
        TOWNS_BOTTOM,
        0,
        "save. Or press Select to jump straight to saving. You can save up to 3 games.",
        first=6,
    ),
    PanelText(
        FIELDS_TOP,
        0,
        "Every battle gives experience, items, and silver.",
        heading="Battles",
    ),
    PanelText(
        FIELDS_TOP,
        1,
        "Tap R in battle to cycle Fast (the default), Faster, and Normal. Hold L+R to run away. "
        "The mic is ignored.",
        heading="Speed",
    ),
    PanelText(
        FIELDS_BOTTOM,
        0,
        "Beaten enemies stay gone until you leave the area and come back.",
        heading="Enemies",
    ),
    PanelText(
        FIELDS_BOTTOM,
        1,
        "Blue chests remain locked until every monster in the area is killed. Monster count is tracked "
        "below the pocketwatch.",
        heading="Blue Chest",
    ),
)


def text_width(glyphs: dict[str, Glyph], text: str) -> int:
    width = 0
    for letter in text:
        width += SPACE if letter == " " else glyphs[letter].width
        width += LETTER_GAP
    return max(0, width - LETTER_GAP)


def _slot_start(page: Page, panel: int, slot: int) -> int:
    if slot < page.indented:
        return INDENT_X + INDENT_START + panel * PANEL_SHIFT
    return FULL_X + FULL_START + panel * PANEL_SHIFT


def wrap(glyphs: dict[str, Glyph], text: PanelText) -> list[str]:
    """The body's words over the panel's lines from `first` on; fails if they do not fit."""
    lines: list[str] = []
    slot = text.first
    current = ""
    for word in text.body.split():
        trial = f"{current} {word}" if current else word
        right = _slot_start(text.page, text.panel, slot) + text_width(glyphs, trial) - 1
        if right <= TEXT_RIGHT + text.panel * PANEL_SHIFT:
            current = trial
            continue
        lines.append(current)
        slot += 1
        current = word
    lines.append(current)
    if text.first + len(lines) > text.page.slots:
        raise ValueError(
            f"{text.body!r} needs {len(lines)} lines from line {text.first}"
        )
    return lines


class Canvas:
    """A guidebook screen being redrawn, colours matched to its own palette."""

    def __init__(self, picture: Picture) -> None:
        self.picture = picture
        self.cache: dict[tuple[int, int, int], int] = {}

    def index(self, color: tuple[int, int, int]) -> int:
        if color not in self.cache:
            self.cache[color] = self.picture.nearest(color)
        return self.cache[color]

    def put(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        self.picture.pixels[y * WIDTH + x] = self.index(color)

    def draw(
        self,
        glyphs: dict[str, Glyph],
        text: str,
        x: int,
        top: int,
        ink: tuple[int, int, int],
        bold: bool = False,
    ) -> None:
        for letter in text:
            if letter == " ":
                x += SPACE + LETTER_GAP
                continue
            glyph = glyphs[letter]
            columns = list(glyph.columns)
            if bold:
                columns = [
                    tuple(
                        max(a, b)
                        for a, b in zip(columns[i], columns[i - 1] if i else columns[i])
                    )
                    for i in range(len(columns))
                ] + [columns[-1]]
            for dx, column in enumerate(columns):
                for dy, coverage in enumerate(column):
                    if coverage <= 0:
                        continue
                    under = self.picture.rgb(x + dx, top + dy)
                    mixed = tuple(
                        round(u + (i - u) * coverage) for u, i in zip(under, ink)
                    )
                    self.put(x + dx, top + dy, mixed)
            x += len(columns) + LETTER_GAP


def _wipe_line(canvas: Canvas, page: Page, panel: int, slot: int) -> None:
    """Back to bare paper: each row takes the colour at the panel's right end."""
    top = line_top(page, slot)
    right = PANEL_END + panel * PANEL_SHIFT
    left = (
        (INDENT_X if slot < page.indented else FULL_X)
        + panel * PANEL_SHIFT
        - WIPE_MARGIN
    )
    for y in range(top, top + LINE_HEIGHT):
        paper = canvas.picture.rgb(right, y)
        for x in range(left, right + 1):
            canvas.put(x, y, paper)


def _outlined(
    glyphs: dict[str, Glyph], text: str
) -> tuple[list[list[float]], list[list[float]]]:
    """White coverage of the heading's letters and the black outline around them, column by column."""
    fill: list[list[float]] = []
    for n, letter in enumerate(text):
        if n:
            fill.extend([[0.0] * LINE_HEIGHT for _ in range(HEADING_GAP)])
        if letter == " ":
            fill.extend([[0.0] * LINE_HEIGHT for _ in range(SPACE)])
            continue
        fill.extend([list(column) for column in glyphs[letter].columns])
    pad = OUTLINE
    fill = [[0.0] * LINE_HEIGHT] * pad + fill + [[0.0] * LINE_HEIGHT] * pad
    fill = [[0.0] * pad + column + [0.0] * pad for column in fill]
    outline = [
        [
            max(
                (
                    fill[x + dx][y + dy]
                    for dx in range(-pad, pad + 1)
                    for dy in range(-pad, pad + 1)
                    if dx * dx + dy * dy <= OUTLINE_REACH
                    and 0 <= x + dx < len(fill)
                    and 0 <= y + dy < len(fill[0])
                ),
                default=0.0,
            )
            for y in range(len(fill[0]))
        ]
        for x in range(len(fill))
    ]
    return fill, outline


def _redraw_heading(
    canvas: Canvas, background: Picture, glyphs: dict[str, Glyph], text: PanelText
) -> None:
    """Wipe the old heading to the plain paper, then white letters with a black outline, as vanilla."""
    assert text.heading is not None
    page = text.page
    left = INDENT_X + text.panel * PANEL_SHIFT
    right = PANEL_END + text.panel * PANEL_SHIFT
    for y in heading_rows(page):
        paper = background.rgb(right, y)
        for x in range(left, right + 1):
            canvas.put(x, y, paper)
    fill, outline = _outlined(glyphs, text.heading)
    x0 = left + HEADING_START - OUTLINE
    y0 = page.heading_top + PILL_LETTER_TOP - HEADING_LETTER_ROW - OUTLINE
    if x0 + len(fill) - 1 > right:
        raise ValueError(f"heading {text.heading!r} is too wide")
    for dx, (fill_column, outline_column) in enumerate(zip(fill, outline)):
        for dy, (white, black) in enumerate(zip(fill_column, outline_column)):
            if black <= 0:
                continue
            x, y = x0 + dx, y0 + dy
            if y not in heading_rows(page):
                continue
            under = canvas.picture.rgb(x, y)
            dark = tuple(round(u * (1 - black)) for u in under)
            mixed = tuple(round(d + (w - d) * white) for d, w in zip(dark, WHITE))
            canvas.put(x, y, mixed)


HEADING_GAP = 1  # columns between heading letters (their outlines merge, as in vanilla)
HEADING_START = 7  # first letter column from the indented rule's start
OUTLINE = 2  # outline thickness
OUTLINE_REACH = 5  # squared distance the outline reaches: a rounded 2-pixel ring


def redraw(page: Page, background_page: Page) -> bytes:
    """A page with its PANELS redrawn; background_page has the same frame with short headings."""
    glyphs = font()
    canvas = Canvas(Picture(page))
    background = Picture(background_page)
    for text in PANELS:
        if text.page != page:
            continue
        lines = wrap(glyphs, text)
        for slot in range(text.first, page.slots):
            _wipe_line(canvas, page, text.panel, slot)
        for offset, line in enumerate(lines):
            slot = text.first + offset
            canvas.draw(
                glyphs,
                line,
                _slot_start(page, text.panel, slot),
                line_top(page, slot),
                INK,
            )
        if text.heading is not None:
            _redraw_heading(canvas, background, glyphs, text)
    return bytes(canvas.picture.pixels)


BACKGROUNDS = {  # page -> a page with the same frame whose headings are short
    TOWNS_TOP: TOWNS_TOP,
    TOWNS_BOTTOM: TOWNS_BOTTOM,
    FIELDS_TOP: TOWNS_TOP,
    FIELDS_BOTTOM: TOWNS_BOTTOM,
}


def guidebook_patches() -> tuple[DataPatch, ...]:
    patches = []
    for page in (TOWNS_TOP, TOWNS_BOTTOM, FIELDS_TOP, FIELDS_BOTTOM):
        old = bytes(Picture(page).pixels)
        patches.append(
            DataPatch(
                ARCHIVE,
                page.picture,
                0,
                old,
                redraw(page, BACKGROUNDS[page]),
                "guidebook page",
            )
        )
    return tuple(patches)


GUIDEBOOK = Feature("guidebook", guidebook_patches())
