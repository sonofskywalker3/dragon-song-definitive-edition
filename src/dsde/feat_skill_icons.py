"""Icons in the battle Special list: each skill's box shows a 16 x 16 picture.

The list's boxes draw a picture per spell from its own file, sysmenupack entry 0x35 (loaded by func_02028100
to *0x020B86E4): a 256-color BGR555 palette, then 256 images of 0x100 bytes (8bpp, four 8 x 8 tiles), image
spell - 1. The game fills only images 0 to 14 (a sigil for each healer spell, a grey one for the Dragon Magic,
a burst for Gale Cut and Thunder Sword); every later spell id is blank, a plain box. func_02035784 copies each
listed entry's image into the box (func_020280e8: 0x200 + (id - 1) * 0x100); for a spell list it reads this
file, for an item list the item icons (entry 0x36, *0x020B86E8; docs/plan-targeting.md).

The entry is rebuilt on the item icons' palette, so a box can also show a game item's icon unchanged: every
image is mapped to that palette (nearest color). Drawn icons are PNG files in art/icons/ (listed in
ART-SOURCES.md); Escape and the four Dragon Magic spells show the game's own item icons (the boots and the
rings); Quick, Grand Weapon, and Grand Shell keep the game's sigil. The card entry (spell 63) shows the icon of
the card its member wears: the copy takes that card's image from the item icon file instead.
"""

import struct
from pathlib import Path

from PIL import Image

from dsde.archive import decompress, read_archive
from dsde.feat_skills_table import CARD_SLOT_OFFSET, EQUIPMENT
from dsde.feat_targeting_names import (
    ICON_COLORS,
    ICON_SIDE,
    ICON_SIZE,
    ICON_TILE,
    ICONS_ENTRY,
    ICONS_START,
    VANILLA_SYSMENU,
    _nearest,
)
from dsde.patching import CaveCode, DataPatch
from dsde.skills_cards import CARD_SPELL
from dsde.skills_common import (
    BATTLER_RECORD,
    BATTLER_SIZE,
    BATTLERS_PTR,
    CHARACTER_RECORD_SIZE,
    RECORD_SIZE,
    RECORDS_PTR,
    hook,
)

ART_DIR = Path(__file__).resolve().parents[2] / "art" / "icons"

SPELL_IMAGES_ENTRY = 0x35
SPELL_IMAGE_SLOTS = 256
SPELL_FILE_PTR = 0x020B86E4  # the loaded spell image file
ICON_FILE_PTR = 0x020B86E8  # the loaded item icon file
# func_02035784: `bl func_020280e8` (r0 = the file, r1 = the entry's id, r2 = 0), the image it copies; r7 = menu
COPY_SITE = 0x020357F4
COPY_WORD = 0xEBFFCA3B
IMAGE_AT = 0x020280E8  # func_020280e8
MENU_MEMBER = 0x34  # the battler whose list it is
RECORD_CHARACTER = 4

TRANSPARENT = 0
OPAQUE = 128  # PNG alpha below this is transparent

# The game's own icons used as they are (item ids)
GAME_ICONS = {
    6: 5,
    10: 203,
    11: 204,
    12: 205,
    13: 206,
}  # Escape: boots; Dragon Magic: the four rings

# Spell id -> icon file name (art/icons/<name>.png)
DRAWN: dict[int, str] = {
    1: "healing_water",
    2: "tender_rain",
    3: "cure_water",
    4: "divine_rain",
    5: "miracle_tears",
    14: "gale_cut",
    15: "thunder_sword",
    38: "weapon_break",
    39: "armor_break",
    40: "focus",
    41: "knockout_kick",
    42: "war_breaker",
    43: "wall_breaker",
    44: "venom_claw",
    45: "blinding_swipe",
    46: "feral_rage",
    47: "howl",
    48: "venom_rain",
    49: "blinding_gale",
    50: "dread_roar",
    51: "rally",
    52: "stand_fast",
    53: "quick_march",
    54: "stratagem",
    55: "battle_cry",
    56: "shield_wall",
    57: "forced_march",
    58: "war_council",
    59: "water_bind",
    60: "binding_rain",
    61: "stone_throw",
    62: "double_strike",
}


def _entries() -> list[bytes]:
    return read_archive(VANILLA_SYSMENU.read_bytes())


def png_icon(path: Path, palette: tuple[int, ...]) -> bytes:
    """A 16 x 16 PNG as an icon: 8bpp, four 8 x 8 tiles, each color the nearest of the palette."""
    image = Image.open(path).convert("RGBA")
    if image.size != (ICON_SIDE, ICON_SIDE):
        raise ValueError(
            f"{path.name} is {image.size}, icons are {ICON_SIDE}x{ICON_SIDE}"
        )
    out = bytearray(ICON_SIZE)
    cache: dict[tuple[int, int, int], int] = {}
    for y in range(ICON_SIDE):
        for x in range(ICON_SIDE):
            r, g, b, a = image.getpixel((x, y))
            if a < OPAQUE:
                continue
            key = (r, g, b)
            if key not in cache:
                cache[key] = _nearest(
                    (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10, palette
                )
            tile = (y // ICON_TILE) * (ICON_SIDE // ICON_TILE) + x // ICON_TILE
            out[
                tile * ICON_TILE * ICON_TILE
                + (y % ICON_TILE) * ICON_TILE
                + x % ICON_TILE
            ] = cache[key]
    return bytes(out)


def _remap(image: bytes, old: tuple[int, ...], new: tuple[int, ...]) -> bytes:
    """An image moved from one palette to another, each color to the nearest."""
    table = {v: _nearest(old[v], new) for v in set(image) if v != TRANSPARENT}
    return bytes(table.get(v, TRANSPARENT) for v in image)


def spell_file() -> bytes:
    """Entry 0x35 rebuilt: the item icons' palette, and an image for every listed spell."""
    entries = _entries()
    spells = decompress(entries[SPELL_IMAGES_ENTRY])
    icons = decompress(entries[ICONS_ENTRY])
    if len(spells) != ICONS_START + SPELL_IMAGE_SLOTS * ICON_SIZE:
        raise ValueError(f"spell image file is {len(spells)} bytes")
    old = struct.unpack_from(f"<{ICON_COLORS}H", spells)
    palette = struct.unpack_from(f"<{ICON_COLORS}H", icons)

    def image(data: bytes, spell: int) -> bytes:
        at = ICONS_START + (spell - 1) * ICON_SIZE
        return data[at : at + ICON_SIZE]

    out = bytearray(spells)
    out[:ICONS_START] = icons[:ICONS_START]
    for spell in range(1, SPELL_IMAGE_SLOTS + 1):
        if spell in DRAWN:
            new = png_icon(ART_DIR / f"{DRAWN[spell]}.png", palette)
        elif spell in GAME_ICONS:
            new = image(icons, GAME_ICONS[spell])
        else:
            new = _remap(image(spells, spell), old, palette)
        at = ICONS_START + (spell - 1) * ICON_SIZE
        out[at : at + ICON_SIZE] = new
    return bytes(out)


# Replaces `bl func_020280e8` in func_02035784 (r0 = the file, r1 = the entry's id, r7 = menu): the card entry
# of a spell list takes the worn card's image from the item icon file.
COPY_ASM = f"""
    push  {{r2, r3, lr}}
    cmp   r1, #{CARD_SPELL}
    bne   si_copy
    ldr   r3, si_spell_file
    ldr   r3, [r3]
    cmp   r0, r3
    bne   si_copy
    ldrh  r0, [r7, #{MENU_MEMBER:#x}]
    ldr   r1, si_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r1, r0, r2, r1
    ldr   r1, [r1, #{BATTLER_RECORD:#x}]
    ldr   r0, si_records
    ldr   r0, [r0]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r0, r1, r2, r0
    ldr   r0, [r0, #{RECORD_CHARACTER}]
    ldr   r1, si_slots
    mov   r2, #{CHARACTER_RECORD_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r1, [r1, #{CARD_SLOT_OFFSET:#x}]
    ldr   r0, si_icon_file
    ldr   r0, [r0]
si_copy:
    mov   r2, #0
    bl    {IMAGE_AT:#x}
    pop   {{r2, r3, pc}}
si_spell_file:
    .word {SPELL_FILE_PTR:#x}
si_icon_file:
    .word {ICON_FILE_PTR:#x}
si_battlers:
    .word {BATTLERS_PTR:#x}
si_records:
    .word {RECORDS_PTR:#x}
si_slots:
    .word {EQUIPMENT:#x}
"""


def icon_patches() -> tuple:
    vanilla = decompress(_entries()[SPELL_IMAGES_ENTRY])
    return (
        DataPatch(
            "sysmenupack",
            SPELL_IMAGES_ENTRY,
            0,
            vanilla,
            spell_file(),
            "skill images on the item icons' palette, one for every listed spell",
            whole=True,
        ),
        CaveCode(
            "cave_skill_icon", COPY_ASM, "the card entry's image is its card's icon"
        ),
        hook(
            COPY_SITE,
            COPY_WORD,
            "bl ${cave_skill_icon}",
            "the card entry's image is its card's icon",
        ),
    )
