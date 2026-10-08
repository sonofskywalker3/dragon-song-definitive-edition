"""Letters of the Adventure Guidebook pages, cut from the vanilla pictures (feat_guidebook.py).

The guidebook's body text is drawn into its pictures in black, anti-aliased over the cream paper. Every line's
wording is known (ORIGINAL_LINES), so each line is cut at its blank columns and each piece is matched to its
character; a line whose pieces do not match its characters one to one (touching letters) is skipped. Lines sit
at whole-row offsets from each other, found from each line's ink profile. A letter is kept as coverage values
0..1 (ink over paper), so it can be drawn again over any background. Letters the pages never show cleanly are
drawn by hand (HANDMADE). The headings (white letters merged into a black outline) are drawn from the same
letters by feat_guidebook.py.
"""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.guidebook_pages import (
    FULL_TENTHS,
    FULL_X,
    HANDMADE,
    INDENT_X,
    LINE_HEIGHT,
    ORIGINAL_LINES,
    PANEL_END,
    PANEL_SHIFT,
    RULE_PITCH,
    Page,
)

VANILLA_PACK = Path(__file__).resolve().parents[2] / "extract" / "files" / "pack.dat"
WIDTH = 256
HEIGHT = 192
INK_EDGE = 0.08  # coverage below this is background when cutting letters
# Share of a usual line's ink in each row (measured over the vanilla lines; descenders in the last rows)
REFERENCE_PROFILE = (
    0.0,
    0.01,
    0.03,
    0.14,
    0.17,
    0.14,
    0.14,
    0.11,
    0.17,
    0.07,
    0.0,
    0.0,
)
MAX_SHIFT = 2

Rgb = tuple[int, int, int]


@dataclass(frozen=True)
class Glyph:
    """A letter's coverage, column by column: columns[x][y] in 0..1 for LINE_HEIGHT rows."""

    columns: tuple[tuple[float, ...], ...]

    @property
    def width(self) -> int:
        return len(self.columns)


@cache
def _vanilla_entry(entry: int) -> bytes:
    return decompress(read_archive(VANILLA_PACK.read_bytes())[entry])


class Picture:
    """A guidebook screen: 8bpp pixels and their 256-colour palette."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.pixels = bytearray(_vanilla_entry(page.picture))
        raw = _vanilla_entry(page.palette)
        self.palette: list[Rgb] = []
        for i in range(len(raw) // 2):
            value = raw[2 * i] | raw[2 * i + 1] << 8
            self.palette.append(
                ((value & 31) * 8, ((value >> 5) & 31) * 8, ((value >> 10) & 31) * 8)
            )

    def rgb(self, x: int, y: int) -> Rgb:
        return self.palette[self.pixels[y * WIDTH + x]]

    def nearest(self, color: Rgb) -> int:
        return min(
            range(len(self.palette)),
            key=lambda i: sum((a - b) ** 2 for a, b in zip(self.palette[i], color)),
        )


def luminance(color: Rgb) -> float:
    r, g, b = color
    return 0.3 * r + 0.59 * g + 0.11 * b


def line_top(page: Page, slot: int) -> int:
    return page.first_rule + slot * RULE_PITCH - LINE_HEIGHT


def line_left(page: Page, panel: int, slot: int) -> int:
    rule = INDENT_X if slot < page.indented else FULL_X
    return rule + panel * PANEL_SHIFT


def _cut(coverage: list[list[float]]) -> list[tuple[int, int]]:
    """Runs of columns holding ink: (first, last)."""
    runs = []
    start = None
    for x, column in enumerate(coverage):
        inked = max(column) >= INK_EDGE
        if inked and start is None:
            start = x
        elif not inked and start is not None:
            runs.append((start, x - 1))
            start = None
    if start is not None:
        runs.append((start, len(coverage) - 1))
    return runs


def _body_coverage(picture: Picture, x0: int, x1: int, top: int) -> list[list[float]]:
    paper = luminance(picture.rgb(x1, top))
    return [
        [
            max(0.0, min(1.0, 1 - luminance(picture.rgb(x, y)) / paper))
            for y in range(top, top + LINE_HEIGHT)
        ]
        for x in range(x0, x1 + 1)
    ]


def _learn(
    found: dict[str, list[Glyph]], coverage: list[list[float]], text: str
) -> None:
    letters = [c for c in text if c != " "]
    runs = _cut(coverage)
    if len(runs) != len(letters):
        return
    shift = -line_shift(coverage)
    for letter, (a, b) in zip(letters, runs):
        found.setdefault(letter, []).append(
            Glyph(tuple(_shifted(coverage[x], shift) for x in range(a, b + 1)))
        )


def _profile(coverage: list[list[float]]) -> list[float]:
    rows = [sum(column[y] for column in coverage) for y in range(LINE_HEIGHT)]
    total = sum(rows) or 1.0
    return [r / total for r in rows]


def line_shift(coverage: list[list[float]]) -> int:
    """Whole rows the line sits below the usual line (REFERENCE_PROFILE), from its ink profile."""
    profile = _profile(coverage)

    def mismatch(shift: int) -> float:
        return sum(
            (
                profile[y]
                - (
                    REFERENCE_PROFILE[y - shift]
                    if 0 <= y - shift < LINE_HEIGHT
                    else 0.0
                )
            )
            ** 2
            for y in range(LINE_HEIGHT)
        )

    return min(range(-MAX_SHIFT, MAX_SHIFT + 1), key=mismatch)


def _shifted(column: list[float], shift: int) -> tuple[float, ...]:
    return tuple(
        column[y - shift] if 0 <= y - shift < len(column) else 0.0
        for y in range(len(column))
    )


def _typical(found: dict[str, list[Glyph]]) -> dict[str, Glyph]:
    """Per letter, a cut of the most common width: a bad split shows up as an odd width."""
    typical = {}
    for letter, cuts in found.items():
        widths = [g.width for g in cuts]
        common = max(set(widths), key=widths.count)
        typical[letter] = next(g for g in cuts if g.width == common)
    return typical


def body_glyphs() -> dict[str, Glyph]:
    found: dict[str, list[Glyph]] = {}
    for (page, panel), lines in ORIGINAL_LINES.items():
        picture = Picture(page)
        for slot, text in enumerate(lines):
            if text is None:
                continue
            x0 = line_left(page, panel, slot)
            x1 = PANEL_END + panel * PANEL_SHIFT
            _learn(found, _body_coverage(picture, x0, x1, line_top(page, slot)), text)
    return _typical(found)


def _handmade(rows: tuple[str, ...]) -> Glyph:
    rows = rows + ("." * len(rows[0]),) * (LINE_HEIGHT - len(rows))
    return Glyph(
        tuple(
            tuple(0.0 if row[x] == "." else int(row[x]) / FULL_TENTHS for row in rows)
            for x in range(len(rows[0]))
        )
    )


def font() -> dict[str, Glyph]:
    """Every body letter: cut from the vanilla pages, plus the handmade ones."""
    glyphs = body_glyphs()
    for letter, rows in HANDMADE.items():
        glyphs.setdefault(letter, _handmade(rows))
    return glyphs
