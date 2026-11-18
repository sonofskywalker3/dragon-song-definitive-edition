"""The stone of Stone Throw: a battle sprite file made from Jian's unused throw (btldata 15).

In the throw he tosses a small stone above his head (cells 3 to 5); the stone is a piece of its own there,
one 16 x 16 piece of 4bpp tiles at tile unit 49, drawn in his palette. Flora's arrow (btldata 10) is the
same shape of file: one animation of one frame, one cell of one 16 x 16 piece. So the stone's file is the
arrow's file with the stone's tiles and Jian's palette in place of the arrow's, and it flies along the
arrow's path. It goes in btldata 17 (Lucia standing, a file no table loads; docs/re-skills.md 3).
"""

import struct
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.mce import (
    CELLS,
    PALETTE,
    PALETTE_COLORS,
    PIECE_FORMAT,
    PIECES,
    SECTION_COUNT,
    SECTIONS_AT,
    TILES,
    TILE_UNIT,
)
from dsde.patching import DataPatch
from dsde.skills_types import SPRITE_STONE

VANILLA_BTLDATA = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "btldata.dat"
)
ARCHIVE = "btldata"
ARROW_FILE = 10
THROW_FILE = 15
STONE_PIECE = 4  # in the throw: the stone above his head in cell 3 (cells 4 and 5 reuse its tiles)
PIECE_16 = 0x40  # piece size code: 16 x 16
PIECE_BYTES = 16 * 16 // 2  # 4bpp


def _sections(data: bytes) -> tuple[int, ...]:
    return struct.unpack_from(f"<{SECTION_COUNT}I", data, SECTIONS_AT)


def _piece(data: bytes, index: int) -> tuple[int, ...]:
    return struct.unpack_from(
        PIECE_FORMAT,
        data,
        _sections(data)[PIECES] + index * struct.calcsize(PIECE_FORMAT),
    )


def stone_file(arrow: bytes, throw: bytes) -> bytes:
    """The arrow's file with the stone's tiles and the throw's palette."""
    if (_sections(arrow)[CELLS + 1] - _sections(arrow)[CELLS]) // 4 != 1 or _piece(
        arrow, 0
    )[2] != PIECE_16:
        raise ValueError("btldata 10 is not one 16 x 16 cell")
    stone = _piece(throw, STONE_PIECE)
    if stone[2] != PIECE_16:
        raise ValueError("the throw's stone is not a 16 x 16 piece")
    first = _sections(throw)[TILES] + stone[4] * TILE_UNIT
    tiles = throw[first : first + PIECE_BYTES]
    palette = throw[_sections(throw)[PALETTE] :][: PALETTE_COLORS * 2]
    out = bytearray(arrow)
    at = _sections(arrow)[TILES] + _piece(arrow, 0)[4] * TILE_UNIT
    out[at : at + PIECE_BYTES] = tiles
    at = _sections(arrow)[PALETTE]
    out[at : at + len(palette)] = palette
    return bytes(out)


def stone_patch() -> DataPatch:
    entries = read_archive(VANILLA_BTLDATA.read_bytes())
    old = decompress(entries[SPRITE_STONE])
    new = stone_file(decompress(entries[ARROW_FILE]), decompress(entries[THROW_FILE]))
    return DataPatch(
        ARCHIVE,
        SPRITE_STONE,
        0,
        old,
        new,
        "Stone Throw: the stone Jian tosses, as a sprite of its own",
        whole=True,
    )
