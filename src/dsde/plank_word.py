"""A new word for the System list's planks, made from the planks' own letters (feat_bestiary.py).

The System list's planks are sprites of sysmenupack: cells CLT 36 over tiles NTC 48 (palette 0). Each plank is a
blank plank (frame 0, or 1 selected) and a word in its own frames: two 32 x 16 pieces, light shaded letters inside
a dark brown outline (index 11; MID and LOW use 10, the same brown). Frames 2 and 3 are Save (normal and selected,
the same tiles), 6 and 7 Quit Game, 10 and 11 MID, 16 and 17 Music Hall.

"Bestiary" is put together from those words' letters, pixel for pixel: e, a from Save; t, i from Quit Game (one
row lower, to share Save's baseline; the i's darker pixel under its dot taken out so it does not read as an l);
s from Music Hall (its few near-black pixels lightened to the letters' mid brown). The game has no B, r, or y in
this lettering; they are made in its own colours: B follows MID's D (its stem, bars, and shading row) with a
middle bar and the right side narrowed into two bowls (B_ROWS); r is Quit's u turned over (an n), its stem and the start of
the arch; y is Save's v with its right arm carried below the line and hooked left. The outline is then laid
around the letters as the game's words have it: every empty pixel within two of a letter (dx^2 + dy^2 <= 5).

The word's 16 tiles are added after NTC 48's 362, and two frames (normal and selected, placed as Save's are)
after CLT 36's 27.
"""

import struct
from functools import cache
from pathlib import Path

from dsde.archive import decompress, read_archive

VANILLA_SYSMENUPACK = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "sysmenupack.dat"
)
ARCHIVE = "sysmenupack"
CELLS = 36  # CLT8: u16 frames at +4, u16 pieces at +6, frames {u16 first piece, u16 pieces}, 12-byte pieces
TILES = 48  # NTC8: u16 tiles at +4, u16 palettes at +6, palettes (0x200 each) from 0x10, then 8x8 tiles
NTC_HEADER = 0x10
PALETTE_BYTES = 0x200
TILE_BYTES = 64
CLT_HEADER = 8
FRAME_BYTES = 4
PIECE_BYTES = 12
PIECE = "<HhhHBBBB"  # tile, x, y, 0, 0, flags, shape (6: 32 x 16), palette slot
TILE_SIDE = 8
PIECE_W = 32
WORD_W = 64
WORD_H = 16
OUTLINE = 11
OUTLINE_LOW = 10  # MID and LOW
EMPTY = 0
MID_BROWN = 55  # a letter's shading brown (Save's)
NEAR_BLACK = 12  # Music Hall's s has a few pixels darker than this
OUTLINE_REACH = 5  # dx^2 + dy^2
QUIT_DROP = 1  # Quit Game's letters sit a row higher than Save's
SAVE_FRAMES = (
    2,
    3,
)  # the word frames whose placement the new word copies (normal, selected)
SAVE_TILE = 80
EXPECTED_FRAMES = 27
EXPECTED_TILES = 362

# word name -> (first tile, pieces)
SOURCES = {
    "Save": (80, 2),
    "QuitGame": (112, 2),
    "MID": (136, 1),
    "MusicHall": (236, 2),
}

Glyph = dict[tuple[int, int], int]


@cache
def _vanilla(entry: int) -> bytes:
    return decompress(read_archive(VANILLA_SYSMENUPACK.read_bytes())[entry])


def _source(name: str) -> list[list[int]]:
    ntc = _vanilla(TILES)
    palettes = struct.unpack_from("<H", ntc, 6)[0]
    base = NTC_HEADER + palettes * PALETTE_BYTES
    first, pieces = SOURCES[name]
    rows: list[list[int]] = [[] for _ in range(WORD_H)]
    tile = first
    for _ in range(pieces):
        piece = [[EMPTY] * PIECE_W for _ in range(WORD_H)]
        for ty in range(WORD_H // TILE_SIDE):
            for tx in range(PIECE_W // TILE_SIDE):
                at = base + tile * TILE_BYTES
                tile += 1
                for py in range(TILE_SIDE):
                    for px in range(TILE_SIDE):
                        piece[ty * TILE_SIDE + py][tx * TILE_SIDE + px] = ntc[
                            at + py * TILE_SIDE + px
                        ]
        for y in range(WORD_H):
            rows[y] += piece[y]
    return rows


def _cut(name: str, x0: int, x1: int, dy: int = 0) -> Glyph:
    rows = _source(name)
    return {
        (x - x0, y + dy): rows[y][x]
        for y in range(WORD_H)
        for x in range(x0, x1 + 1)
        if rows[y][x] not in (EMPTY, OUTLINE, OUTLINE_LOW)
    }


def _width(g: Glyph) -> int:
    return max(x for x, _ in g) + 1


# B, laid out in MID's D's own colours: its stem (194 / 135), top and bottom bars, the shading row under it, and
# a middle bar, the right side narrowed into two bowls. Rows from the cap line (row 4); 0 is empty.
B_ROWS = (
    (164, 251, 251, 251, 219, 55, 0),
    (194, 135, 0, 0, 135, 251, 0),
    (194, 135, 0, 0, 0, 251, 0),
    (194, 135, 0, 0, 55, 219, 0),
    (194, 219, 194, 194, 251, 135, 0),
    (194, 135, 0, 0, 0, 135, 251),
    (194, 135, 0, 0, 0, 0, 251),
    (194, 219, 194, 194, 219, 251, 164),
    (18, 135, 135, 135, 135, 18, 0),
)
CAP_LINE = 4


def _b_from_d(d: Glyph) -> Glyph:
    """B in the D's colours (B_ROWS); checks that the D still has those colours."""
    colours = set(d.values())
    needed = {c for row in B_ROWS for c in row if c}
    if not needed <= colours:
        raise ValueError(
            f"MID's D lacks the colours B is drawn in: {sorted(needed - colours)}"
        )
    return {
        (x, CAP_LINE + y): c
        for y, row in enumerate(B_ROWS)
        for x, c in enumerate(row)
        if c
    }


def _letters() -> dict[str, Glyph]:
    a = _cut("Save", 24, 30)
    v = _cut("Save", 32, 38)
    e = _cut("Save", 40, 45)
    u = _cut("QuitGame", 11, 15, QUIT_DROP)
    i_raw = _cut("QuitGame", 19, 19, QUIT_DROP)
    i_top = min(y for _, y in i_raw)
    i = {(x, y): c for (x, y), c in i_raw.items() if y != i_top + 1}
    t = _cut("QuitGame", 23, 27, QUIT_DROP)
    s = {
        k: (MID_BROWN if c < NEAR_BLACK else c)
        for k, c in _cut("MusicHall", 17, 23).items()
    }
    d = _cut("MID", 21, 28)

    b = _b_from_d(d)
    stem_w = 2

    u_top = min(y for _, y in u)
    u_bottom = max(y for _, y in u)
    n = {(x, u_top + u_bottom - y): c for (x, y), c in u.items()}
    arch_end = 4
    r = {
        (x, y): c
        for (x, y), c in n.items()
        if x < stem_w or (x <= arch_end and y <= u_top + 1)
    }

    v_bottom = max(y for _, y in v)
    right = max(x for x, _ in v)
    arm = sorted(((y, x), c) for (x, y), c in v.items() if x == right - 2)
    tail = arm[-1][1] if arm else max(v.values())
    y_glyph = dict(v)
    for x, y in (
        (right - 3, v_bottom + 1),
        (right - 4, v_bottom + 2),
        (right - 5, v_bottom + 2),
    ):
        y_glyph[(x, y)] = tail
    return {"B": b, "e": e, "s": s, "t": t, "i": i, "a": a, "r": r, "y": y_glyph}


def compose(text: str) -> list[list[int]]:
    """`text` in the planks' lettering as a 64 x 16 grid of palette indices, centred."""
    glyphs = _letters()
    gap = 1
    total = sum(_width(glyphs[ch]) for ch in text) + gap * (len(text) - 1)
    if total > WORD_W - 4:
        raise ValueError(f"{text!r} is too wide for a plank word ({total} pixels)")
    x = (WORD_W - total) // 2
    grid = [[EMPTY] * WORD_W for _ in range(WORD_H)]
    for ch in text:
        for (gx, gy), c in glyphs[ch].items():
            grid[gy][x + gx] = c
        x += _width(glyphs[ch]) + gap
    reach = [
        (dx, dy)
        for dx in range(-2, 3)
        for dy in range(-2, 3)
        if dx * dx + dy * dy <= OUTLINE_REACH
    ]
    out = [row[:] for row in grid]
    for y in range(WORD_H):
        for xx in range(WORD_W):
            if grid[y][xx] == EMPTY and any(
                0 <= y + dy < WORD_H
                and 0 <= xx + dx < WORD_W
                and grid[y + dy][xx + dx] != EMPTY
                for dx, dy in reach
            ):
                out[y][xx] = OUTLINE
    return out


def _tiles(grid: list[list[int]]) -> bytes:
    """Two 32 x 16 pieces, each four tiles across and two down, in 1D order."""
    out = bytearray()
    for px0 in (0, PIECE_W):
        for ty in range(WORD_H // TILE_SIDE):
            for tx in range(PIECE_W // TILE_SIDE):
                for py in range(TILE_SIDE):
                    for p in range(TILE_SIDE):
                        out.append(grid[ty * TILE_SIDE + py][px0 + tx * TILE_SIDE + p])
    return bytes(out)


@cache
def plank_word_patch(text: str) -> tuple[bytes, bytes, bytes, bytes, int]:
    """(tiles old, tiles new, cells old, cells new, first new frame) for `text` added as a plank word."""
    ntc = _vanilla(TILES)
    tile_count = struct.unpack_from("<H", ntc, 4)[0]
    clt = _vanilla(CELLS)
    frames, pieces = struct.unpack_from("<HH", clt, 4)
    if frames != EXPECTED_FRAMES or tile_count != EXPECTED_TILES:
        raise ValueError(
            "the System planks' sprites are not the vanilla 27 frames over 362 tiles"
        )
    new_ntc = bytearray(ntc + _tiles(compose(text)))
    struct.pack_into(
        "<H",
        new_ntc,
        4,
        tile_count + 2 * (PIECE_W // TILE_SIDE) * (WORD_H // TILE_SIDE),
    )

    frame_table = clt[CLT_HEADER : CLT_HEADER + frames * FRAME_BYTES]
    pieces_at = CLT_HEADER + frames * FRAME_BYTES
    piece_table = clt[pieces_at : pieces_at + pieces * PIECE_BYTES]
    tail = clt[pieces_at + pieces * PIECE_BYTES :]
    new_frames = bytearray(frame_table)
    new_pieces = bytearray(piece_table)
    added = 0
    for source in SAVE_FRAMES:
        first, count = struct.unpack_from("<HH", clt, CLT_HEADER + source * FRAME_BYTES)
        new_frames += struct.pack("<HH", pieces + added, count)
        for k in range(count):
            fields = list(
                struct.unpack_from(PIECE, piece_table, (first + k) * PIECE_BYTES)
            )
            fields[0] = fields[0] - SAVE_TILE + tile_count
            new_pieces += struct.pack(PIECE, *fields)
        added += count
    header = clt[:4] + struct.pack("<HH", frames + len(SAVE_FRAMES), pieces + added)
    new_clt = header + bytes(new_frames) + bytes(new_pieces) + tail
    return ntc, bytes(new_ntc), clt, new_clt, frames
