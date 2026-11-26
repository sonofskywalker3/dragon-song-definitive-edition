"""Changed cards (docs/plan-cards.md 8, approved build list point 4; Kuntukapu from point 3).

- **Insector, Ochu, and Kuntukapu last 2 to 4 rounds**, not the rest of the battle. Their battle flag bits (0x40,
  0x80, 0x20) get a round count when a round starts (where the command input hands over to the round): the
  first round start that finds a bit set gives it 3 to 5, each round start takes one, and the bit is cleared
  at 0, so the card works for the rest of the round it was used in and 2 to 4 more. The count is forgotten
  whenever its bit is clear (each battle zeroes the flags), so the next use starts afresh.
- **Hellbird fills one picked ally's MP** instead of everyone's: its effect's target bits are one ally, so the
  Special list opens the ally picker for it as for a basic card.
- **Termite guards one picked ally**: breaks and steals aimed at that member miss for the rest of the battle (the
  game's Termite made every enemy's break miss). Its effect's target bits are one ally; where the card sets the
  party's bit 0x02 (func_0206a744, 0x0206A808) it sets the picked ally's own guard bit instead (0x800 << party
  slot, bits the game leaves unused), and the enemy attack's steal and break tests (func_02030b44, 0x02030C50 and
  0x02030C6C) also read the target's own bit.
- **Yeti steals** (point 4): its effect's target bits are one enemy, and where it set the party's steal guard
  (0x0206A7E0) the user steals from the picked monster: 25%, the rarer slot 25% (feat_skills_steal.py). Its
  refusal test is the steal's: a monster already robbed or with nothing to steal.
"""

import struct

from dsde.feat_skills_boost import RANDOM
from dsde.patching import CaveCode, Patch
from dsde.skills_common import BATTLE_WORK_PTR, VANILLA_ARM9, hook
from dsde.cards_data import HELLBIRD, TERMITE, YETI
from dsde.skills_types import FLAG_GUARD as GUARD_BIT
from dsde.skills_types import PERSONAL_GUARD

ARM9_BASE = 0x02000000
ITEM_TABLE = 0x0209B068
ITEM_SIZE = 0x14
ITEM_EFFECT = 2
CARD_EFFECTS = 0x0209D124
CARD_EFFECT_SIZE = 12
FIRST_EFFECT = 0x100
TARGET_BITS = 0xC0000000
ALLY_ONE = 0x80000000
ENEMY_ONE = 0x00000000
YETI_SITE = 0x0206A7E0  # func_0206a744: `orr r3, r3, #1`
YETI_WORD = 0xE3833001
YETI_CHANCE = 25
YETI_RARE_CHANCE = 25

TIMED_BITS = (
    0x20,
    0x40,
    0x80,
)  # Kuntukapu's MP regen, Insector's damage up, Ochu's damage down
TIMED_ROUNDS = 3  # plus two coin flips: 3 to 5 at the first round start, so 2 to 4 rounds after the one it was used in
# func_020297d4 case 7 hands over to the round (battle state 8) in two places: `streq r1, [r0, #0x8c]` (the
# usual one, followed by `beq`) and `str r1, [r0, #0x8c]` after a message's countdown
ROUND_START = 0x0202A3F8
ROUND_START_WORD = 0x0580108C
ROUND_START_LATE = 0x0202A4E0
ROUND_START_LATE_WORD = 0xE580108C

PARTY_SLOTS = 3
TERMITE_SITE = 0x0206A808  # func_0206a744: `orr r3, r3, #2`
TERMITE_WORD = 0xE3833002
BATTLE_ACTOR = 0x32
BATTLER_TARGET = 0x8C  # the ally picker's party slot
BATTLERS_PTR = 0x020B8640
BATTLER_SIZE = 0x12C
STEAL_TEST = (
    0x02030C50  # func_02030b44 (r4 = the target's battler index): `ands r0, r0, #1`
)
STEAL_TEST_WORD = 0xE2100001
BREAK_TEST = 0x02030C6C  # `ands r0, r0, #2`
BREAK_TEST_WORD = 0xE2100002
STEAL_BIT = 0x01


def _effect_flags_addr(card: int) -> int:
    arm9 = VANILLA_ARM9.read_bytes()
    effect = struct.unpack_from(
        "<H", arm9, ITEM_TABLE + card * ITEM_SIZE + ITEM_EFFECT - ARM9_BASE
    )[0]
    return CARD_EFFECTS + (effect - FIRST_EFFECT) * CARD_EFFECT_SIZE


def _one_target(card: int, target: int, note: str) -> Patch:
    """The card's effect flags with other target bits."""
    addr = _effect_flags_addr(card)
    old = struct.unpack_from("<I", VANILLA_ARM9.read_bytes(), addr - ARM9_BASE)[0]
    return Patch(addr, old, (old & ~TARGET_BITS) | target, note)


# In place of `orr r3, r3, #1` in func_0206a744 (ip = the battle work), where the Yeti card set the party's
# steal guard: the user steals from the monster they picked (the actor's first target), 25%, the rarer slot 25%.
# r3 comes back as the flags word reloaded, since the game stores r3 next and the steal sets the robbed bit.
YETI_ASM = f"""
    push  {{r0-r2, ip, lr}}
    ldrsh r0, [ip, #{BATTLE_ACTOR:#x}]
    ldr   r1, ye_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldrsh r0, [r0, #{BATTLER_TARGET:#x}]
    mov   r1, #{YETI_CHANCE}
    mov   r2, #{YETI_RARE_CHANCE}
    bl    ${{cave_skill_steal}}
    ldr   ip, [sp, #12]
    ldr   r3, [ip]
    pop   {{r0-r2, ip, pc}}
ye_battlers:
    .word {BATTLERS_PTR:#x}
"""


TIMERS_ASM = f"""
    .byte {", ".join("0" for _ in TIMED_BITS)}
    .align 2
"""

# In place of the store where the round starts (reached on equal at the first site): count each timed bit's rounds
# down. Returns with Z set, for the `beq` after the first site.
ROUND_ASM = f"""
    str   r1, [r0, #0x8c]
    push  {{r0-r7, lr}}
    ldr   r6, rd_work
    ldr   r6, [r6]
    ldr   r7, [r6]
    ldr   r2, rd_timers
    mov   r3, #0
rd_loop:
    adr   r4, rd_bits
    ldrb  r4, [r4, r3]
    tst   r7, r4
    moveq r5, #0
    beq   rd_store
    ldrb  r5, [r2, r3]
    cmp   r5, #0
    bne   rd_count
    push  {{r2, r3}}
    bl    {RANDOM:#x}
    and   r5, r0, #1
    bl    {RANDOM:#x}
    and   r0, r0, #1
    add   r5, r5, r0
    add   r5, r5, #{TIMED_ROUNDS}
    pop   {{r2, r3}}
rd_count:
    subs  r5, r5, #1
    biceq r7, r7, r4
rd_store:
    strb  r5, [r2, r3]
    add   r3, r3, #1
    cmp   r3, #{len(TIMED_BITS)}
    blt   rd_loop
    str   r7, [r6]
    pop   {{r0-r7, lr}}
    cmp   r0, r0
    bx    lr
rd_work:
    .word {BATTLE_WORK_PTR:#x}
rd_timers:
    .word ${{cave_card_timers}}
rd_bits:
    .byte {", ".join(f"{bit:#x}" for bit in TIMED_BITS)}
    .align 2
"""

# In place of `orr r3, r3, #2` in func_0206a744 (ip = the battle work): the picked ally's own guard bit.
TERMITE_ASM = f"""
    push  {{r0-r2, lr}}
    ldrsh r0, [ip, #{BATTLE_ACTOR:#x}]
    ldr   r1, tm_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldrsh r0, [r0, #{BATTLER_TARGET:#x}]
    mov   r1, #{PERSONAL_GUARD:#x}
    orr   r3, r3, r1, lsl r0
    pop   {{r0-r2, pc}}
tm_battlers:
    .word {BATTLERS_PTR:#x}
"""

# r0 = the battle flags, r1 = the party's bit for this attack (steal 0x01, break 0x02), r4 = the target's battler
# index -> r0 = 1 if the attack is guarded against (the party's bit, or the target's own guard bit), else 0, with
# the flags of `movs r0, r0`. Keeps r1 to r3.
GUARDED_ASM = f"""
    push  {{r2, lr}}
    tst   r0, r1
    bne   gd_yes
    cmp   r4, #{PARTY_SLOTS}
    bhs   gd_no
    mov   r2, #{PERSONAL_GUARD:#x}
    tst   r0, r2, lsl r4
    bne   gd_yes
gd_no:
    movs  r0, #0
    pop   {{r2, pc}}
gd_yes:
    movs  r0, #1
    pop   {{r2, pc}}
"""


def _test_asm(bit: int) -> str:
    return f"""
    push  {{r1, lr}}
    mov   r1, #{bit:#x}
    bl    ${{cave_card_guarded}}
    pop   {{r1, pc}}
"""


def change_patches() -> tuple:
    return (
        CaveCode("cave_card_timers", TIMERS_ASM, "the timed cards' rounds"),
        CaveCode(
            "cave_card_rounds",
            ROUND_ASM,
            "Insector, Ochu, and Kuntukapu last 2 to 4 rounds",
        ),
        hook(
            ROUND_START,
            ROUND_START_WORD,
            "bleq ${cave_card_rounds}",
            "Insector, Ochu, and Kuntukapu last 2 to 4 rounds",
        ),
        hook(
            ROUND_START_LATE,
            ROUND_START_LATE_WORD,
            "bl ${cave_card_rounds}",
            "Insector, Ochu, and Kuntukapu last 2 to 4 rounds",
        ),
        _one_target(HELLBIRD, ALLY_ONE, "Hellbird fills one ally's MP"),
        _one_target(TERMITE, ALLY_ONE, "Termite guards one ally"),
        _one_target(YETI, ENEMY_ONE, "Yeti steals from one monster"),
        CaveCode("cave_card_yeti", YETI_ASM, "Yeti steals from one monster"),
        hook(
            YETI_SITE, YETI_WORD, "bl ${cave_card_yeti}", "Yeti steals from one monster"
        ),
        CaveCode("cave_card_termite", TERMITE_ASM, "Termite guards one ally"),
        hook(
            TERMITE_SITE,
            TERMITE_WORD,
            "bl ${cave_card_termite}",
            "Termite guards one ally",
        ),
        CaveCode("cave_card_guarded", GUARDED_ASM, "a guarded member"),
        CaveCode(
            "cave_card_guard_steal",
            _test_asm(STEAL_BIT),
            "a guarded member's steal misses",
        ),
        hook(
            STEAL_TEST,
            STEAL_TEST_WORD,
            "bl ${cave_card_guard_steal}",
            "a guarded member's steal misses",
        ),
        CaveCode(
            "cave_card_guard_break",
            _test_asm(GUARD_BIT),
            "a guarded member's break misses",
        ),
        hook(
            BREAK_TEST,
            BREAK_TEST_WORD,
            "bl ${cave_card_guard_break}",
            "a guarded member's break misses",
        ),
    )
