"""MP economy (design 8): cheaper spells, flat MP items, Mental Gum
in shops, and healing statues that also cure status. Research: docs/re-mp-jobs-rings.md section 1.

New costs change only what casting takes (func_0206aabc, which also applies the Holy Umbrella and Magic Booster
reductions): spells are learned by level (feat_spell_levels.py), not when max MP reaches the cost.
"""

from dsde.patching import ARM_NOP, AsmPatch, CaveCode, Feature, Patch


SPELL_COST_TABLE = 0x0209497C  # u32 cost at +4 of each 0x0C-byte spell entry
SPELL_ENTRY_SIZE = 0x0C
NEW_SPELL_COSTS = {  # spell index: (name, vanilla cost, new cost), about 40%
    1: ("Healing Water", 10, 4),
    2: ("Tender Rain", 30, 12),
    3: ("Cure Squall", 8, 4),
    4: ("Divine Rain", 40, 16),
    5: ("Miracle Tears", 50, 20),
    6: ("Escape", 5, 2),
    7: ("Quick", 20, 8),
    8: ("Grand Weapon", 24, 10),
    9: ("Grand Shell", 28, 10),
}
# Medicine: func_0206a8b8 adds maxMP * value / 100 for effect flag 0x20. The single-target MP items
# (Mental Gum 20, Mental Drop 50, flags 0x80000023) now add the value itself; the all-allies card
# (flags 0xC0000023) keeps its percentage. The temp target at 0x0213B91C holds MP at +0xC, max at +0x10.
MP_ITEM_BLOCK = 0x0206A988
MP_ITEM_BLOCK_END = 0x0206A9C4
MP_ITEM_FIRST_WORD = 0xE59F20A8
MP_ITEM_LAST_WORD = 0xC58CE00C
MEDICINE_MP_POOL = 0x0206AA38  # literal 0x0209D12A (MP value of effect 0)
TARGET_POOL = 0x0206AA2C  # literal 0x0213B91C
DIV100_POOL = 0x0206AA34  # literal 0x51EB851F
FLAG_ALL_TARGETS = 0x40000000
ARM_PC_AHEAD = 8


def _pool(word_addr: int, pool_addr: int) -> str:
    return f"[pc, #{pool_addr - (word_addr + ARM_PC_AHEAD):#x}]"


def _mp_item_asm() -> str:
    a = MP_ITEM_BLOCK
    word = 4
    return f"""
    ldr   r2, {_pool(a, MEDICINE_MP_POOL)}
    ldr   ip, {_pool(a + word, TARGET_POOL)}
    ldrh  r2, [r2, r1]
    ldr   lr, [ip, #0x10]
    ldr   r3, {_pool(a + 4 * word, DIV100_POOL)}
    tst   r0, #{FLAG_ALL_TARGETS:#x}
    moveq r5, r2
    mulne r4, lr, r2
    smullne r2, r5, r3, r4
    asrne r5, r5, #5
    ldr   r3, [ip, #0xc]
    add   r2, r3, r5
    str   r2, [ip, #0xc]
    cmp   r2, lr
    strgt lr, [ip, #0xc]
"""


# Mental Gum (item 0x116) costs 1000 and is sold in the item shop (slot 3) of the 3rd town onwards, after
# Healing Drop. Each list is 30 u16 item ids; entries 2..5 shift from 118 119 11B 0 to 116 118 119 11B.
ITEM_TABLE = 0x0209B068
ITEM_ENTRY_SIZE = 0x14
ITEM_PRICE = 0x10
MENTAL_GUM = 0x116
MENTAL_GUM_PRICE_OLD = 30
MENTAL_GUM_PRICE = 1000
SHOP_LIST_SIZE = 0x3C
ITEM_SHOP_SLOT = 3
ITEM_SHOPS = {  # town script: shop list base (slot 1)
    "005": 0x0209D6F8,
    "007": 0x0209DAB8,
    "010": 0x0209D9C8,
    "011": 0x0209D7AC,
    "012": 0x0209D860,
}
SHOP_WORDS = (  # (offset in the list, vanilla word, new word)
    (4, 0x0119_0118, 0x0118_0116),
    (8, 0x0000_011B, 0x011B_0119),
)


def _shop_patches() -> tuple[Patch, ...]:
    patches = []
    for town, base in ITEM_SHOPS.items():
        items = base + (ITEM_SHOP_SLOT - 1) * SHOP_LIST_SIZE
        for offset, old, new in SHOP_WORDS:
            patches.append(
                Patch(items + offset, old, new, f"town {town} item shop: Mental Gum")
            )
    return tuple(patches)


# Healing statues (map object 0x37D, field loop func_0201e6a0) refill HP and MP of the three party
# members; the copy now also clears the status (character record +0x08, low 4 bits, as Cure items do).
STATUE_COPY = 0x0201F370
STATUE_COPY_END = 0x0201F380
STATUE_FIRST_WORD = 0xE5910014
STATUE_LAST_WORD = 0xE5810018
STATUS_MASK = 0xF
# Using a statue pans the camera to centre it (field state 0x3C), waits for the pan, sparkles, then pans
# back to Jian (0x0201FDF0) and waits again: about two seconds of camera for a statue Jian is already
# standing at (Jeff, 2026-10-07). Both calls of the camera move (func_0201d878, 60 frames) go, so the
# waits after them pass at once; the code is shared, so every statue in the game is affected.
STATUE_CAMERA_CALLS = (
    (0x0201FA98, 0xEBFFF776),  # bl func_0201d878: centre the statue
    (0x0201FDF0, 0xEBFFF6A0),  # bl func_0201d878: back to Jian
)

MP_ECONOMY = Feature(
    "mp-economy",
    (
        *(
            Patch(
                SPELL_COST_TABLE + index * SPELL_ENTRY_SIZE,
                old,
                new,
                f"{name} costs {new} MP",
            )
            for index, (name, old, new) in NEW_SPELL_COSTS.items()
        ),
        AsmPatch(
            MP_ITEM_BLOCK,
            MP_ITEM_BLOCK_END,
            MP_ITEM_FIRST_WORD,
            MP_ITEM_LAST_WORD,
            _mp_item_asm(),
            "single-target MP items restore a flat amount",
        ),
        Patch(
            ITEM_TABLE + MENTAL_GUM * ITEM_ENTRY_SIZE + ITEM_PRICE,
            MENTAL_GUM_PRICE_OLD,
            MENTAL_GUM_PRICE,
            "Mental Gum costs 1000",
        ),
        *_shop_patches(),
        CaveCode(
            "cave_statue",
            f"""
    ldr   r0, [r1, #0x14]
    str   r0, [r1, #0x10]
    ldr   r0, [r1, #0x1c]
    str   r0, [r1, #0x18]
    ldr   r0, [r1, #8]
    bic   r0, r0, #{STATUS_MASK:#x}
    str   r0, [r1, #8]
    bx    lr
""",
            "statue refill also cures status",
        ),
        AsmPatch(
            STATUE_COPY,
            STATUE_COPY_END,
            STATUE_FIRST_WORD,
            STATUE_LAST_WORD,
            f"""
    bl    ${{cave_statue}}
    .word {ARM_NOP:#x}
    .word {ARM_NOP:#x}
    .word {ARM_NOP:#x}
""",
            "healing statue also cures status",
        ),
        *(
            Patch(addr, word, ARM_NOP, "healing statue: no camera pan")
            for addr, word in STATUE_CAMERA_CALLS
        ),
    ),
)
