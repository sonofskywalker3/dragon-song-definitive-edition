"""A "Definitive Edition" seal on the title screen, under DRAGON SONG.

The title's top screen is two 8bpp BG layers from titlepack: the art (entry 10) and, above it, the
LUNAR / DRAGON SONG logo (entry 12). Both are NTC8 files: u16 tile count at +4, 256-colour palette at
0x10, 8 x 8 tiles of one byte per pixel from 0x210. The art's map gives screen cell n tile n (every
title map is the identity under the seal, no tile shared), so the seal is painted straight into the
art's tiles at its place below SONG.

No titlepack file may change size: growing the logo by 3 KB to hold the seal on its own layer broke
the game later (warp6 no longer reached the temple battle, 2026-10-07), most likely a fixed-size load
buffer. The art keeps its size and tile count; only pixels and palette entries change.

The art's palette uses all 256 colours. Seal colours with no close match free a slot by merging the
two closest colours of the art (the pixels of one move to the other, a change of a 5-bit step or so
that cannot be seen), then take that slot.

The seal is drawn at build time: an oval starburst whose straight-edged points have whole-pixel
corners, with three lines of cream pixel capitals: DEFINITIVE / EDITION / the edition
(docs/plan-two-editions.md), so a screenshot or bug report says which build it is. `title-seal` (Classic
edition) is a red seal saying CLASSIC; `title-seal-retold` (Retold edition, after title-seal) repaints the
palette and tiles as a blue seal saying RETOLD.
"""

import math
import struct
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.patching import DataPatch, Feature

VANILLA_TITLEPACK = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "titlepack.dat"
)
ARCHIVE = "titlepack"
ART = 10

PALETTE_AT = 0x10
TILES_AT = 0x210
COLOURS = 256
TILE = 8
TILE_BYTES = TILE * TILE
MAP_WIDTH = 32

# Seal size and place (screen pixels, top screen)
SEAL_WIDTH, SEAL_HEIGHT = 84, 50
SEAL_X, SEAL_Y = 166, 80
POINTS = 20  # star points around the rim, evenly spaced along it
POINT_DEPTH = 5  # pixels from the tips to the notches between them
ARC_SAMPLES = 3600  # steps used to measure the rim's length

RIM_BLUE = (48, 96, 208)
RIM_DARK = (16, 32, 96)
RIM_RED = (200, 40, 40)
RIM_DARK_RED = (96, 16, 16)
CREAM = (255, 244, 206)  # the lettering
CLOSE_ENOUGH = (
    3 * 8 * 8
)  # squared RGB distance: within about one 5-bit step per channel

TITLE_LINES = (("DEFINITIVE", 11), ("EDITION", 21))  # text and top row inside the seal
EDITION_TOP = 32  # top row of the edition's name, under them
CLASSIC = "CLASSIC"
RETOLD = "RETOLD"
RIMS = {CLASSIC: (RIM_RED, RIM_DARK_RED), RETOLD: (RIM_BLUE, RIM_DARK)}  # fill, edge
FONT = {  # 7 rows each, "1" = ink
    "D": ("1110", "1001", "1001", "1001", "1001", "1001", "1110"),
    "E": ("1111", "1000", "1000", "1110", "1000", "1000", "1111"),
    "F": ("1111", "1000", "1000", "1110", "1000", "1000", "1000"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "N": ("1001", "1101", "1101", "1011", "1011", "1001", "1001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "V": ("10001", "10001", "10001", "10001", "01010", "01010", "00100"),
    "O": ("0110", "1001", "1001", "1001", "1001", "1001", "0110"),
    "G": ("0111", "1000", "1000", "1011", "1001", "1001", "0111"),
    "S": ("0111", "1000", "1000", "0110", "0001", "0001", "1110"),
    "R": ("1110", "1001", "1001", "1110", "1010", "1001", "1001"),
    "C": ("0111", "1000", "1000", "1000", "1000", "1000", "0111"),
    "L": ("1000", "1000", "1000", "1000", "1000", "1000", "1111"),
    "A": ("0110", "1001", "1001", "1111", "1001", "1001", "1001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
}

Rgb = tuple[int, int, int]
Pixel = tuple[int, int]


def _star(cx: float, cy: float, rx: float, ry: float) -> list[Pixel]:
    """Star polygon on whole pixels: tips on the oval, notches POINT_DEPTH in, spaced by arc length."""
    steps = [i * math.tau / ARC_SAMPLES for i in range(ARC_SAMPLES + 1)]
    length = [0.0]
    for a, b in zip(steps, steps[1:], strict=False):
        length.append(
            length[-1]
            + math.hypot(
                rx * (math.cos(b) - math.cos(a)), ry * (math.sin(b) - math.sin(a))
            )
        )
    corners = []
    for k in range(2 * POINTS):
        target = length[-1] * k / (2 * POINTS)
        t = steps[next(i for i, s in enumerate(length) if s >= target)]
        inset = 0 if k % 2 == 0 else POINT_DEPTH
        corners.append(
            (
                round(cx + (rx - inset) * math.cos(t)),
                round(cy + (ry - inset) * math.sin(t)),
            )
        )
    return corners


def _line(a: Pixel, b: Pixel) -> list[Pixel]:
    """Bresenham line from a to b, both ends included."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _inside(polygon: list[Pixel], x: float, y: float) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def seal_pixels(edition: str) -> dict[Pixel, Rgb]:
    """The seal as {(x, y): colour}, in seal coordinates; missing pixels are transparent."""
    cx, cy = (SEAL_WIDTH - 1) / 2, (SEAL_HEIGHT - 1) / 2
    rx, ry = (SEAL_WIDTH - 1) / 2, (SEAL_HEIGHT - 1) / 2
    star = _star(cx, cy, rx, ry)
    edge = {
        p for a, b in zip(star, star[1:] + star[:1], strict=True) for p in _line(a, b)
    }
    shape = edge | {
        (x, y)
        for y in range(SEAL_HEIGHT)
        for x in range(SEAL_WIDTH)
        if _inside(star, x, y)
    }
    fill, rim = RIMS[edition]
    out: dict[Pixel, Rgb] = dict.fromkeys(shape, fill)
    out.update(dict.fromkeys(edge, rim))
    for text, top in (*TITLE_LINES, (edition, EDITION_TOP)):
        width = sum(len(FONT[c][0]) + 1 for c in text) - 1
        x = round(cx - width / 2)
        for c in text:
            for gy, row in enumerate(FONT[c]):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        out[x + gx, top + gy] = CREAM
            x += len(FONT[c][0]) + 1
    return out


def _rgb(c: int) -> Rgb:
    return ((c & 0x1F) << 3, ((c >> 5) & 0x1F) << 3, ((c >> 10) & 0x1F) << 3)


def _bgr555(rgb: Rgb) -> int:
    r, g, b = (v >> 3 for v in rgb)
    return r | g << 5 | b << 10


def _distance(a: Rgb, b: Rgb) -> int:
    return sum((x - y) ** 2 for x, y in zip(a, b, strict=True))


def _closest_pair(palette: list[Rgb], taken: set[int]) -> tuple[int, int]:
    """The two closest colours, colours already taken excluded: (kept, freed)."""
    free = [i for i in range(COLOURS) if i not in taken]
    _, kept, freed = min(
        (_distance(palette[i], palette[j]), i, j)
        for n, i in enumerate(free)
        for j in free[n + 1 :]
    )
    return kept, freed


def _seal_palette(
    art: bytes, edition: str
) -> tuple[list[Rgb], bytearray, dict[Rgb, int]]:
    """The art's palette and tiles with slots freed for the seal, and each seal colour's index."""
    palette = [
        _rgb(struct.unpack_from("<H", art, PALETTE_AT + i * 2)[0])
        for i in range(COLOURS)
    ]
    tiles = bytearray(art[TILES_AT:])
    index_of: dict[Rgb, int] = {}
    for colour in (*RIMS[edition], CREAM):
        near = min(range(COLOURS), key=lambda i: _distance(palette[i], colour))
        if _distance(palette[near], colour) <= CLOSE_ENOUGH:
            index_of[colour] = near
            continue
        kept, freed = _closest_pair(palette, set(index_of.values()))
        tiles = bytearray(kept if b == freed else b for b in tiles)
        palette[freed] = colour
        index_of[colour] = freed
    return palette, tiles, index_of


def _painted(edition: str) -> tuple[bytes, bytes, list[Rgb], bytearray]:
    """The art, and its palette and tiles with the seal for edition painted in."""
    art = decompress(read_archive(VANILLA_TITLEPACK.read_bytes())[ART])
    palette, tiles, index_of = _seal_palette(art, edition)
    for (sx, sy), colour in seal_pixels(edition).items():
        x, y = SEAL_X + sx, SEAL_Y + sy
        tile = (y // TILE) * MAP_WIDTH + x // TILE
        tiles[tile * TILE_BYTES + (y % TILE) * TILE + x % TILE] = index_of[colour]
    return art, art[PALETTE_AT:TILES_AT], palette, tiles


def _palette_bytes(palette: list[Rgb]) -> bytes:
    return b"".join(struct.pack("<H", _bgr555(c)) for c in palette)


def seal_patches() -> tuple[DataPatch, ...]:
    art, old_palette, palette, tiles = _painted(CLASSIC)
    return (
        DataPatch(
            ARCHIVE,
            ART,
            PALETTE_AT,
            old_palette,
            _palette_bytes(palette),
            "title seal: seal colours in freed palette slots",
        ),
        DataPatch(
            ARCHIVE,
            ART,
            TILES_AT,
            art[TILES_AT:],
            bytes(tiles),
            "title seal: painted under SONG (art colours merged to free slots)",
        ),
    )


def retold_seal_patches() -> tuple[DataPatch, ...]:
    """Over title-seal's palette and tiles: the blue seal saying RETOLD."""
    *_, classic_palette, classic_tiles = _painted(CLASSIC)
    *_, retold_palette, retold_tiles = _painted(RETOLD)
    return (
        DataPatch(
            ARCHIVE,
            ART,
            PALETTE_AT,
            _palette_bytes(classic_palette),
            _palette_bytes(retold_palette),
            "title seal: blue instead of red",
        ),
        DataPatch(
            ARCHIVE,
            ART,
            TILES_AT,
            bytes(classic_tiles),
            bytes(retold_tiles),
            "title seal: RETOLD instead of CLASSIC",
        ),
    )


TITLE_SEAL = Feature("title-seal", seal_patches())
TITLE_SEAL_RETOLD = Feature("title-seal-retold", retold_seal_patches())
