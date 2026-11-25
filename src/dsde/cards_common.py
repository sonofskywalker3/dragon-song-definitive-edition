"""Addresses and record layouts shared by the card feature modules (feat_card_*.py, feat_ring_slot.py).

Every member gets two equipment slots after the game's five (docs/plan-cards.md 7.1): slot 5 holds a card and
slot 6 a dragon ring. The game indexes a member's equipment as record + 0x40 + 2 * slot, so the new slots are
the shorts at +0x4A and +0x4C, which the game only ever zeroes.
"""

CHAR_RECORDS = 0x020B4658  # one record per character id, 0x5C bytes each
CHAR_RECORD_SIZE = 0x5C
EQUIP_OFFSET = (
    0x40  # u16 item id per slot: 0 weapon, 1 body, 2 arm, 3 head, 4 accessory
)
EQUIP_SLOT_SIZE = 2
GAME_SLOTS = 5
CARD_SLOT = 5
RING_SLOT = 6
CHARACTERS = 5  # Jian, Lucia, Gabryel, Flora, Rufus

ITEM_TABLE = 0x0209B068  # 0x14 per item: +0 type, +2 effect id, +4 six stat shorts (ATK DEF AGI INT DEX LUCK)
ITEM_SIZE = 0x14
ITEM_TYPE_SLOT = 0xF  # low nibble of the type: the slot it goes in (cards: 5)
WHO_BITS = 0x1F0  # type bits 0x10 Jian, 0x20 Lucia, 0x40 Gabryel, 0x80 Flora, 0x100 Rufus may equip it

BAG = 0x0213B930  # the bag func_0206ba54 counts in
FIRST_CARD = 0xD8  # 216, the Blob card; a species' card is FIRST_CARD + species
FIRST_BOSS_CARD = 250
LAST_CARD = 269
CARD_POINTS = 0x020B4884  # s16 points per card, index card - FIRST_CARD
CARD_POINTS_SIZE = 2
CARD_FULL = 0x0209EA14  # a card's full points: 8 bytes per card, the value first
CARD_FULL_SIZE = 8
POINTS_PER_USE = 100

RING_ITEMS = (0xCB, 0xCC, 0xCD, 0xCE)  # Blazing, Tidal, Gale, Earth


def slot_address(char_id: int, slot: int) -> int:
    """Where character `char_id`'s equipment slot `slot` (0..6) is kept."""
    return (
        CHAR_RECORDS
        + char_id * CHAR_RECORD_SIZE
        + EQUIP_OFFSET
        + slot * EQUIP_SLOT_SIZE
    )


def card_points_address(card: int) -> int:
    """The s16 holding card item `card`'s points."""
    return CARD_POINTS + (card - FIRST_CARD) * CARD_POINTS_SIZE


def card_full_address(card: int) -> int:
    """Where card item `card`'s full points are kept."""
    return CARD_FULL + (card - FIRST_CARD) * CARD_FULL_SIZE
