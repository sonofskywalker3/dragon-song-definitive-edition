"""The battle screen's wooden sign says "L+R" instead of "MIC" (design 7).

During command input the top screen shows a wooden sign with a running man and "MIC": blowing into
the microphone used to run from battle. Running is now holding L and R (feat_battle_run.py), so the
sign's lettering is redrawn.

The sign is 6 x 5 tiles (48 x 40 pixels, 4bpp) of the battle UI tile set, btldata entry 3 (an "MNCG"
file: header, palettes from 0x10, tiles from 0x130). The game copies the tiles to engine B (top
screen) BG0 character base 0xC000 and draws the sign with tiles 0xE2..0xFF, palette bank 8 (the
file's palette 7), at tile column 26, row 19. No other tile set holds these tiles.

The lettering keeps the original's style: 1-pixel strokes 6 rows high, shaded white, white, cream,
tan, blue, blue from top to bottom, with a black outline around every stroke on the plank's wood.
The new tiles are made at build time from the vanilla tiles: only the lettering band is redrawn.
"""

from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.patching import DataPatch, Feature

VANILLA_BTLDATA = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "btldata.dat"
)
ARCHIVE = "btldata"
ENTRY = 3  # battle UI tile set
TILES_START = 0x130  # first tile in the entry
TILE_BYTES = 32  # 4bpp 8 x 8
TILE_SIZE = 8
SIGN_FIRST_TILE = 0xE2
SIGN_COLUMNS = 6
SIGN_ROWS = 5
SIGN_OFFSET = TILES_START + SIGN_FIRST_TILE * TILE_BYTES
SIGN_BYTES = SIGN_COLUMNS * SIGN_ROWS * TILE_BYTES
LOW_NIBBLE = 0x0F
NIBBLE_BITS = 4

# Palette indexes of bank 8
OUTLINE = 0x1
# Lettering band of the plank (sign pixels): rows 26..33, columns 15..36. Row 26 and row 33 are the
# plank's dark top and bottom edges; the letters fill rows 27..32.
BAND_LEFT = 15
BAND_RIGHT = 36
LETTER_TOP = 27
# Wood color of each band row away from the letters (the plank's middle shades), rows 26..33
WOOD_BY_ROW = (0x2, 0xC, 0xB, 0xB, 0x8, 0x8, 0x5, 0x4)
BAND_TOP = LETTER_TOP - 1
# Letter color of each glyph row, as in the original "MIC": white, white, cream, tan, blue, blue
INK_BY_ROW = (0xF, 0xF, 0xE, 0xD, 0x9, 0x9)

GLYPHS = {  # 6 rows each, "#" = stroke
    "L": (
        "#...",
        "#...",
        "#...",
        "#...",
        "#...",
        "####",
    ),
    "+": (
        ".....",
        "..#..",
        "..#..",
        "#####",
        "..#..",
        "..#..",
    ),
    "R": (
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#..#.",
        "#...#",
    ),
}
TEXT = "L+R"
LETTER_GAP = 2  # columns between letters (the outline between them stays black)
STROKE = "#"


def _decode(data: bytes) -> list[list[int]]:
    """Sign tiles to rows of palette indexes (48 x 40)."""
    width = SIGN_COLUMNS * TILE_SIZE
    pixels = [[0] * width for _ in range(SIGN_ROWS * TILE_SIZE)]
    for index in range(SIGN_COLUMNS * SIGN_ROWS):
        left = index % SIGN_COLUMNS * TILE_SIZE
        top = index // SIGN_COLUMNS * TILE_SIZE
        for i, byte in enumerate(data[index * TILE_BYTES : (index + 1) * TILE_BYTES]):
            y, x = top + i // (TILE_SIZE // 2), left + i % (TILE_SIZE // 2) * 2
            pixels[y][x] = byte & LOW_NIBBLE
            pixels[y][x + 1] = byte >> NIBBLE_BITS
    return pixels


def _encode(pixels: list[list[int]]) -> bytes:
    out = bytearray()
    for index in range(SIGN_COLUMNS * SIGN_ROWS):
        left = index % SIGN_COLUMNS * TILE_SIZE
        top = index // SIGN_COLUMNS * TILE_SIZE
        for y in range(top, top + TILE_SIZE):
            for x in range(left, left + TILE_SIZE, 2):
                out.append(pixels[y][x] | pixels[y][x + 1] << NIBBLE_BITS)
    return bytes(out)


def _strokes() -> set[tuple[int, int]]:
    """Sign pixels (x, y) of the lettering, centered in the band."""
    width = sum(len(GLYPHS[c][0]) for c in TEXT) + LETTER_GAP * (len(TEXT) - 1)
    x = (BAND_LEFT + BAND_RIGHT + 1 - width) // 2
    strokes = set()
    for char in TEXT:
        glyph = GLYPHS[char]
        for row, line in enumerate(glyph):
            strokes.update(
                (x + col, LETTER_TOP + row) for col, c in enumerate(line) if c == STROKE
            )
        x += len(glyph[0]) + LETTER_GAP
    return strokes


def sign_pixels(vanilla: bytes) -> list[list[int]]:
    """The sign's pixels with the lettering band redrawn as "L+R"."""
    pixels = _decode(vanilla)
    strokes = _strokes()
    for row, wood in enumerate(WOOD_BY_ROW):
        y = BAND_TOP + row
        for x in range(BAND_LEFT, BAND_RIGHT + 1):
            if (x, y) in strokes:
                pixels[y][x] = INK_BY_ROW[y - LETTER_TOP]
            elif any(
                (x + dx, y + dy) in strokes for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            ):
                pixels[y][x] = OUTLINE
            else:
                pixels[y][x] = wood
    return pixels


def vanilla_sign() -> bytes:
    entries = read_archive(VANILLA_BTLDATA.read_bytes())
    data = decompress(entries[ENTRY])
    return data[SIGN_OFFSET : SIGN_OFFSET + SIGN_BYTES]


def _sign_patch() -> DataPatch:
    old = vanilla_sign()
    return DataPatch(
        ARCHIVE,
        ENTRY,
        SIGN_OFFSET,
        old,
        _encode(sign_pixels(old)),
        'battle sign: "L+R" instead of "MIC"',
    )


MIC_SIGN = Feature("mic-sign", (_sign_patch(),))
