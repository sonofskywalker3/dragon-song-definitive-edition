"""The card slot and the dragon ring slot (docs/plan-cards.md 7.1 and 7.2).

Every member's equipment grows from five slots to seven: slot 5 holds a card and slot 6 a dragon ring, the
record shorts at +0x4A and +0x4C, which the game only ever zeroes. Cards already carry slot number 5 in their
item type, so the equip routine's "slot = type" puts a card in slot 5 by itself; a dragon ring keeps its
accessory type (so the Item page keeps it on its accessory page) and is sent to slot 6.

- Item data: every slottable card and every dragon ring may be equipped by anyone (the "who" bits), and each
  boss card with a passive gets its stat bonuses and gear effect (cards_data.BOSS_PASSIVES).
- func_0206b930 (may this member equip it) accepts slot number 5.
- func_0206b46c (equip) sends a dragon ring to slot 6.
- func_0206b880 (how many members wear an item) looks in slot 6 for a ring; its loop over the five members
  stays as it is.
- func_0206b8ec (does a member wear it), func_0206b4d8 (stat totals), func_0206aabc (MP cost gear), and
  func_0206ab6c (gear effects) cover the two new slots. A monster card's effect id (0x117 and up) is past the
  gear effect switch's last case (0x2D), so a slotted monster card adds no gear effect.
- func_020555e8 (the reset that keeps the records, EXP, and cards) no longer zeroes the two new slots.

func_02055760 (the new game's default gear), func_0206b144 (break's replacement item), and func_0206b1d0
(the break picker) keep the game's five slots.
"""

import struct

from dsde.cards_common import (
    CHAR_RECORDS,
    EQUIP_OFFSET,
    ITEM_SIZE,
    ITEM_TABLE,
    ITEM_TYPE_SLOT,
    RING_ITEMS,
    RING_SLOT,
    WHO_BITS,
)
from dsde.cards_data import BOSS_PASSIVES, SLOTTABLE
from dsde.patching import AsmPatch, CaveCode, Patch, byte_patches
from dsde.skills_common import VANILLA_ARM9, hook

ARM9_BASE = 0x02000000
ITEM_EFFECT = 2  # u16 effect id
ITEM_STATS = 4  # six s16: ATK, DEF, AGI, INT, DEX, LUCK
FIRST_RING = RING_ITEMS[0]
RING_SPAN = len(RING_ITEMS) - 1
SLOT_COUNT = 7
NOP = 0xE1A00000

CAN_EQUIP_LIMIT = 0x0206B950  # func_0206b930: `cmp r2, #5` then `bxhs lr` (false for slot numbers 5 and up)
EQUIP_SLOT_OF = (
    0x0206B4B4  # func_0206b46c: `and r1, r3, #0xf`, the slot from the item's type
)
WEARERS = 0x0206B880  # func_0206b880, whole: how many members wear item r0
WEARERS_END = 0x0206B8EC
WEARS_LIMIT = 0x0206B91C  # func_0206b8ec: `cmp ip, #5`, the slot loop
TOTALS_LIMIT = 0x0206B650  # func_0206b4d8: `cmp lr, #5`, the slot loop
MP_GEAR_LIMIT = 0x0206AB38  # func_0206aabc: `cmp r7, #4` / `ble`, the slot loop
EFFECTS_LIMIT = 0x0206AECC  # func_0206ab6c: `cmp sb, #4` / `ble`, the slot loop
RESET_SLOT5 = 0x0205567C  # func_020555e8: `strh r5, [r1, #0xf2]`, record + 0x4A
RESET_SLOT6 = 0x02055680  # `strh r5, [r1, #0xf4]`, record + 0x4C


def _vanilla() -> bytes:
    return VANILLA_ARM9.read_bytes()


def _item_edits(arm9: bytes) -> dict[int, int]:
    """Byte edits to the item table: the "who" bits, and each boss passive's stats and gear effect."""
    edits: dict[int, int] = {}

    def put(addr: int, fmt: str, value: int) -> None:
        for i, byte in enumerate(struct.pack(fmt, value)):
            edits[addr + i] = byte

    for item in sorted(SLOTTABLE | frozenset(RING_ITEMS)):
        entry = ITEM_TABLE + item * ITEM_SIZE
        kind = struct.unpack_from("<H", arm9, entry - ARM9_BASE)[0]
        put(entry, "<H", kind | WHO_BITS)
    for passive in BOSS_PASSIVES:
        entry = ITEM_TABLE + passive.card * ITEM_SIZE
        put(entry + ITEM_EFFECT, "<H", passive.gear_effect)
        for i, value in enumerate(passive.stats):
            put(entry + ITEM_STATS + 2 * i, "<h", value)
    return edits


# Called in place of `and r1, r3, #0xf` in func_0206b46c (r3 = the item's type, r4 = the item): r1 = the
# slot. Touches only r1 and the flags.
EQUIP_SLOT_ASM = f"""
    and   r1, r3, #{ITEM_TYPE_SLOT:#x}
    sub   r4, r4, #{FIRST_RING:#x}
    cmp   r4, #{RING_SPAN}
    movls r1, #{RING_SLOT}
    add   r4, r4, #{FIRST_RING:#x}
    bx    lr
"""

# func_0206b880 rewritten: r0 = item -> r0 = how many of the five members wear it, in the slot it goes in.
WEARERS_ASM = f"""
    ldr   r1, wearers_items
    mov   r2, #{ITEM_SIZE:#x}
    mla   r1, r0, r2, r1
    ldrh  r1, [r1]
    and   r2, r1, #{ITEM_TYPE_SLOT:#x}
    sub   r1, r0, #{FIRST_RING:#x}
    cmp   r1, #{RING_SPAN}
    movls r2, #{RING_SLOT}
    mov   r3, #0
    cmp   r2, #{SLOT_COUNT}
    bhs   wearers_done
    ldr   r1, wearers_slots
    add   r2, r1, r2, lsl #1
    mov   ip, #5
wearers_loop:
    ldrh  r1, [r2]
    cmp   r0, r1
    addeq r3, r3, #1
    add   r2, r2, #0x5c
    subs  ip, ip, #1
    bne   wearers_loop
wearers_done:
    mov   r0, r3
    bx    lr
wearers_items:
    .word {ITEM_TABLE:#x}
wearers_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
"""


def slot_patches() -> tuple[Patch | AsmPatch | CaveCode, ...]:
    arm9 = _vanilla()
    return (
        *byte_patches(
            arm9,
            _item_edits(arm9),
            "cards and dragon rings for anyone; boss card passives",
        ),
        Patch(
            CAN_EQUIP_LIMIT,
            0xE3520005,
            0xE3520006,
            "a card (slot number 5) can be equipped",
        ),
        CaveCode(
            "cave_card_equip_slot",
            EQUIP_SLOT_ASM,
            "a dragon ring goes to the ring slot",
        ),
        hook(
            EQUIP_SLOT_OF,
            0xE203100F,
            "bl ${cave_card_equip_slot}",
            "equip: the ring slot for a dragon ring",
        ),
        AsmPatch(
            WEARERS,
            WEARERS_END,
            0xE3A01014,
            0x020B05B0,
            WEARERS_ASM,
            "worn count: the card and ring slots",
        ),
        Patch(WEARS_LIMIT, 0xE35C0005, 0xE35C0007, "is it worn: seven slots"),
        Patch(TOTALS_LIMIT, 0xE35E0005, 0xE35E0007, "stat totals: seven slots"),
        Patch(MP_GEAR_LIMIT, 0xE3570004, 0xE3570006, "MP cost gear: seven slots"),
        Patch(EFFECTS_LIMIT, 0xE3590004, 0xE3590006, "gear effects: seven slots"),
        Patch(RESET_SLOT5, 0xE1C15FB2, NOP, "the keep-EXP reset keeps the card slot"),
        Patch(RESET_SLOT6, 0xE1C15FB4, NOP, "the keep-EXP reset keeps the ring slot"),
    )
