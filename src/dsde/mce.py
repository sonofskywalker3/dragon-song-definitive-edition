"""Reads MCE0 files, the battle sprite animations in btldata.dat (one per enemy species).

Layout (little endian), worked out from the Blue Dragon's bubbles (btldata entry 0xDD):

    +0x00 "MCE0", +0x04 u16 animation count, +0x06 u16 ?
    +0x08 u32 x6  section offsets: animations, frames, cells, pieces, tiles, palette
    cells    {u16 first piece, u16 piece count}
    pieces   12 bytes: s16 x, s16 y (from the sprite's origin), u16 size code, u16 tile count,
             u16 first tile in 64-byte units, u16 ?
    tiles    4bpp 8x8 tiles, 32 bytes each, a piece's tiles in rows
    palette  16 BGR555 colors, color 0 transparent
"""

import struct
from dataclasses import dataclass

MAGIC = b"MCE0"
SECTIONS_AT = 0x08
SECTION_COUNT = 6
CELLS, PIECES, TILES, PALETTE = 2, 3, 4, 5
CELL_FORMAT = "<HH"
PIECE_FORMAT = "<hhHHHH"
PALETTE_COLORS = 16
TILE = 8
TILE_BYTES = 32
TILE_UNIT = 64  # piece tile starts count 64-byte units
TRANSPARENT = 0
NIBBLE = 4
LOW_NIBBLE = 0xF
# Piece size code -> width, height in pixels
PIECE_SIZES = {0x00: (8, 8), 0x10: (16, 8), 0x20: (8, 16), 0x40: (16, 16)}


@dataclass(frozen=True)
class Sprite:
    """One cell of an MCE0 file: pixels as palette indexes, 0 transparent."""

    pixels: dict[tuple[int, int], int]
    palette: tuple[int, ...]  # BGR555

    def bounds(self) -> tuple[int, int, int, int]:
        """Left, top, right, bottom (inclusive) of the opaque pixels."""
        xs = [x for x, _ in self.pixels]
        ys = [y for _, y in self.pixels]
        return min(xs), min(ys), max(xs), max(ys)


def read_cell(data: bytes, cell: int) -> Sprite:
    """Assemble one cell of an MCE0 file from its pieces."""
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError("not an MCE0 file")
    sections = struct.unpack_from(f"<{SECTION_COUNT}I", data, SECTIONS_AT)
    first, count = struct.unpack_from(
        CELL_FORMAT, data, sections[CELLS] + cell * struct.calcsize(CELL_FORMAT)
    )
    piece_size = struct.calcsize(PIECE_FORMAT)
    tiles = data[sections[TILES] : sections[PALETTE]]
    palette = struct.unpack_from(f"<{PALETTE_COLORS}H", data, sections[PALETTE])
    pixels: dict[tuple[int, int], int] = {}
    for index in range(first, first + count):
        x, y, size, _, unit, _ = struct.unpack_from(
            PIECE_FORMAT, data, sections[PIECES] + index * piece_size
        )
        width, height = PIECE_SIZES[size]
        tile = unit * TILE_UNIT // TILE_BYTES
        for ty in range(0, height, TILE):
            for tx in range(0, width, TILE):
                _put_tile(pixels, tiles, tile, x + tx, y + ty)
                tile += 1
    return Sprite(pixels, palette)


def _put_tile(
    pixels: dict[tuple[int, int], int], tiles: bytes, tile: int, x: int, y: int
) -> None:
    for p in range(TILE * TILE):
        byte = tiles[tile * TILE_BYTES + p // 2]
        value = byte >> NIBBLE if p % 2 else byte & LOW_NIBBLE
        if value != TRANSPARENT:
            pixels[(x + p % TILE, y + p // TILE)] = value
