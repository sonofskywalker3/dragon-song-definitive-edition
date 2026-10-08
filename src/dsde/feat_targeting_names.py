"""Manual targeting: a picker label for the Blue Dragon's summons.

The picker shows an enemy as its card item (CARD_ITEM_BASE + species): the item's icon in the grid
cell and its name in the bottom bar. Enemy row 156, the four bubbles the Blue Dragon summons, maps
to species 54, one past the last enemy species, which is the Jian character card (0x10E), so they
showed Jian's portrait and the name "Jian". The game never names them on screen; walkthroughs call
them bubbles, and they are drawn as white and purple bubbles.

Row 156 is shown as item 0x19C instead, an unused placeholder named "K26". Its name becomes
"Bubble" and its icon is drawn from the bubbles' own battle sprite: the smallest frame of their
wobble animation (15 x 14 pixels, so no scaling) from their MCE0 file in btldata, each of its colors
replaced by the nearest one in the icon palette. "Bubble" does not fit in K26's 4-byte
string, so it runs on into K27's, and K27, also unused, points at K28's string. The info window
prints a count after an item name except for cards (0xD8..0x113); one hook treats 0x19C as a card.
Ids from 0x1A0 up print no name at all, which is why K30 is not used. Jian's card and every other
item keep their names.
"""

import struct
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.mce import TRANSPARENT, Sprite, read_cell
from dsde.patching import ARM9_BASE, AsmPatch, CaveCode, DataPatch, Patch, byte_patches

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VANILLA_ARM9 = PROJECT_ROOT / "extract" / "arm9" / "arm9.bin"
VANILLA_SYSMENU = PROJECT_ROOT / "extract" / "files" / "sysmenupack.dat"
VANILLA_BTLDATA = PROJECT_ROOT / "extract" / "files" / "btldata.dat"

SUMMON_ROW = 156  # enemy row of the Blue Dragon's summons
SUMMON_CARD = 0x19C  # placeholder item "K26", shown for SUMMON_ROW
SPARE_CARD = 0x19D  # placeholder item "K27": its string space goes to SUMMON_CARD
DONOR_CARD = 0x19E  # placeholder item "K28": SPARE_CARD shows this string
SUMMON_SPECIES = 54
SUMMON_CELL = (
    3  # frame of the bubbles' sprite used for the icon (the only one that fits)
)

NAME_OFFSETS = 0x020A78EC  # u16 per item id: offset of its name from NAME_STRINGS
NAME_STRINGS = 0x020A7C30
NAME_END = 0xFF
# Item name encoding: A = 0x02, a = 0x3A
UPPER_BASE = 0x02
LOWER_BASE = 0x3A
SUMMON_NAME = "Bubble"

INFO_CARD_TEST = (0x02044CE4, 0xE35000D8)  # cmp r0, #0xD8: cards print no count
FIRST_CARD = 0xD8

ICONS_ENTRY = 0x36  # sysmenupack entry: one icon per item id from 1
ICONS_START = 0x200
ICON_SIZE = 0x100
ICON_SIDE = 16  # 8bpp, four 8x8 tiles: top left, top right, bottom left, bottom right
ICON_TILE = 8
ICON_COLORS = (
    256  # shared BGR555 palette at the start of the icon file, color 0 transparent
)
SPECIES_ANIMS = (
    0x02096EDC  # per species, 0x1C bytes; +0x10 = btldata entry of its sprite
)
SPECIES_RECORD = 0x1C
SPECIES_SPRITE = 0x10
CHANNEL_BITS = 5
CHANNEL_MASK = 0x1F


def encode_name(text: str) -> bytes:
    """Encode letters in the item name table's encoding, with the end byte."""
    out = bytearray()
    for char in text:
        base = UPPER_BASE if char.isupper() else LOWER_BASE
        out.append(base + ord(char.lower()) - ord("a"))
    out.append(NAME_END)
    return bytes(out)


def _word(arm9: bytes, addr: int) -> int:
    return struct.unpack_from("<I", arm9, addr - ARM9_BASE)[0]


def _offset_addr(item: int) -> int:
    return NAME_OFFSETS + 2 * item


def _name_patches() -> tuple[Patch, ...]:
    arm9 = VANILLA_ARM9.read_bytes()

    def offset(item: int) -> int:
        return struct.unpack_from("<H", arm9, _offset_addr(item) - ARM9_BASE)[0]

    summon, spare, donor = offset(SUMMON_CARD), offset(SPARE_CARD), offset(DONOR_CARD)
    spare_end = arm9.index(NAME_END, NAME_STRINGS + spare - ARM9_BASE)
    room = spare_end + 1 - (NAME_STRINGS + summon - ARM9_BASE)
    name = encode_name(SUMMON_NAME)
    if len(name) > room:
        raise ValueError(f"{SUMMON_NAME!r} needs {len(name)} bytes, {room} free")
    edits = {NAME_STRINGS + summon + i: b for i, b in enumerate(name)}
    for i, b in enumerate(donor.to_bytes(2, "little")):
        edits[_offset_addr(SPARE_CARD) + i] = b
    return byte_patches(arm9, edits, f"item {SUMMON_CARD:#x} named {SUMMON_NAME}")


def _rgb(color: int) -> tuple[int, int, int]:
    return tuple((color >> (CHANNEL_BITS * i)) & CHANNEL_MASK for i in range(3))


def _nearest(color: int, palette: tuple[int, ...]) -> int:
    """Index of the opaque palette color closest to a BGR555 color."""
    want = _rgb(color)

    def distance(index: int) -> int:
        return sum(
            (a - b) ** 2 for a, b in zip(want, _rgb(palette[index]), strict=True)
        )

    return min(range(TRANSPARENT + 1, len(palette)), key=distance)


def icon_from_sprite(sprite: Sprite, palette: tuple[int, ...]) -> bytes:
    """A 16x16 item icon of a sprite (centred, not scaled), in the icon palette."""
    left, top, right, bottom = sprite.bounds()
    width, height = right - left + 1, bottom - top + 1
    if width > ICON_SIDE or height > ICON_SIDE:
        raise ValueError(
            f"sprite is {width}x{height}, icons are {ICON_SIDE}x{ICON_SIDE}"
        )
    dx = (ICON_SIDE - width) // 2 - left
    dy = (ICON_SIDE - height) // 2 - top
    colors = {i: _nearest(c, palette) for i, c in enumerate(sprite.palette)}
    icon = bytearray(ICON_SIZE)
    for (x, y), value in sprite.pixels.items():
        ix, iy = x + dx, y + dy
        tile = (iy // ICON_TILE) * (ICON_SIDE // ICON_TILE) + ix // ICON_TILE
        pixel = (iy % ICON_TILE) * ICON_TILE + ix % ICON_TILE
        icon[tile * ICON_TILE * ICON_TILE + pixel] = colors[value]
    return bytes(icon)


def _summon_icon(icon_palette: tuple[int, ...]) -> bytes:
    arm9 = VANILLA_ARM9.read_bytes()
    record = SPECIES_ANIMS + SUMMON_SPECIES * SPECIES_RECORD + SPECIES_SPRITE
    entry = struct.unpack_from("<H", arm9, record - ARM9_BASE)[0]
    mce = decompress(read_archive(VANILLA_BTLDATA.read_bytes())[entry])
    return icon_from_sprite(read_cell(mce, SUMMON_CELL), icon_palette)


def _icon_patch() -> DataPatch:
    icons = decompress(read_archive(VANILLA_SYSMENU.read_bytes())[ICONS_ENTRY])
    palette = struct.unpack_from(f"<{ICON_COLORS}H", icons)
    at = ICONS_START + (SUMMON_CARD - 1) * ICON_SIZE
    return DataPatch(
        "sysmenupack",
        ICONS_ENTRY,
        at,
        icons[at : at + ICON_SIZE],
        _summon_icon(palette),
        f"item {SUMMON_CARD:#x} gets the bubbles' sprite as its icon",
    )


# Replaces `cmp r0, #0xD8` in the info window (r0 = item id, flags read by the next blt): the
# summon label counts as a card, so no count is printed after its name
CARD_TEST_ASM = f"""
    cmp   r0, #{SUMMON_CARD:#x}
    moveq r0, #{FIRST_CARD:#x}
    cmp   r0, #{FIRST_CARD:#x}
    bx    lr
"""

NAME_PATCHES: tuple[Patch | DataPatch | CaveCode | AsmPatch, ...] = (
    *_name_patches(),
    _icon_patch(),
    CaveCode("cave_tgt_card_test", CARD_TEST_ASM, "summon label prints no count"),
    AsmPatch(
        INFO_CARD_TEST[0],
        INFO_CARD_TEST[0] + 4,
        INFO_CARD_TEST[1],
        INFO_CARD_TEST[1],
        "bl ${cave_tgt_card_test}",
        "summon label prints no count",
    ),
)
