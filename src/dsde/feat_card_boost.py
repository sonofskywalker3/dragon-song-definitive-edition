"""A worn card enhances the matching skill (docs/plan-cards.md 8, approved build list point 2).

A member who knows a skill or spell their worn card enhances (cards_data.BOOSTS) casts it enhanced while the card
has the points: the cast costs its MP and 100 points (a one-target cast) or 200 (an all-target one), and at too
few points it casts as normal. What an enhanced cast does is the skills feature's (feat_skills_boost.py); this
module decides when:

- the resolver's MP charge (func_020514ec, 0x02051A98) takes the card's points too and names the caster in the
  boost state, or names nobody for a plain cast;
- the Special list's OK sets the stage limit the refusal test uses, 2 for a cast that will be enhanced, so a
  target already one stage down can still be picked;
- the name bar shows the font's up arrow after the name of a skill that will be enhanced (the font has no "+");
- the card entry is not listed for a member who knows the card's skill (feat_card_use.py asks
  cave_card_basic, which answers BASIC_LEARNER).
"""

import struct

from dsde import targeting_consts as T
from dsde.cards_common import (
    CARD_POINTS,
    CARD_SLOT,
    CHAR_RECORD_SIZE,
    CHAR_RECORDS,
    EQUIP_OFFSET,
    FIRST_CARD,
    POINTS_PER_USE,
)
from dsde.cards_data import GAME_SPELLS, active_boosts
from dsde.feat_skills_boost import (
    BOOST_LIMIT,
    NO_ACTOR,
    PLAIN_LIMIT,
    STATE_ACTOR,
    STATE_LIMIT,
)
from dsde.jp_hint_pairs import END
from dsde.patching import CaveCode
from dsde.skills_common import (
    ALL_TARGETS,
    BATTLE_WORK_PTR,
    BATTLERS_PTR,
    BATTLER_SIZE,
    DRAW_TEXT,
    SPELL_ENTRY_SIZE,
    SPELL_TABLE,
    VANILLA_ARM9,
    byte_list,
    hook,
)
from dsde.skills_cards import STEAL_SPELL
from dsde.skills_data import BY_SPELL, SPELL_COUNT

ARM9_BASE = 0x02000000
NO_CARD = 0xFF
ONE_TARGET_USES, ALL_TARGET_USES = 1, 2
BATTLER_CHARACTER = 4
BATTLER_ACTION_ID = 0x86
WORK_ACTOR = 0x32
GLYPH_UP = 0x57  # the battle font's up arrow
NAME_BUFFER = 40

CHARGE_SITE = 0x02051A98  # func_020514ec, the Special branch: `sub r1, r1, r0` (MP - cost; r4 = the battler)
CHARGE_WORD = 0xE0411000
NAME_DRAW = 0x02044E80  # the name bar's spell case: `bl func_02045114` (r3 = the name)
NAME_DRAW_WORD = 0xEB0000A3
MENU_BAR_ID = 0x94  # menu field: the spell on the name bar
MENU_BAR_MEMBER = 0x9C  # menu field: the battler whose list it is


def _all_targets(spell: int) -> bool:
    if spell in GAME_SPELLS:
        arm9 = VANILLA_ARM9.read_bytes()
        flags = struct.unpack_from(
            "<I", arm9, SPELL_TABLE + spell * SPELL_ENTRY_SIZE - ARM9_BASE
        )[0]
        return bool(flags & ALL_TARGETS)
    return bool(BY_SPELL[spell].target & ALL_TARGETS)


def boost_table(poison_turns: bool = True) -> bytes:
    """Two bytes per spell id: the card that enhances it (card - FIRST_CARD, 0xFF for none) and the uses an
    enhanced cast takes."""
    rows = [(NO_CARD, 0)] * SPELL_COUNT
    for card, spells in active_boosts(poison_turns).items():
        for spell in spells:
            uses = ALL_TARGET_USES if _all_targets(spell) else ONE_TARGET_USES
            rows[spell] = (card - FIRST_CARD, uses)
    return bytes(byte for row in rows for byte in row)


# r0 = character id, r1 = spell -> r0 = the points an enhanced cast takes, or 0 if the cast is plain (the worn
# card does not enhance it, or has too few points); r1 = the worn card's points. Keeps r2, r3.
COST_ASM = f"""
    push  {{r2, r3, lr}}
    cmp   r1, #{SPELL_COUNT}
    bhs   bc_none
    ldr   r2, bc_table
    add   r2, r2, r1, lsl #1
    ldrb  r3, [r2]
    cmp   r3, #{NO_CARD}
    beq   bc_none
    ldrb  lr, [r2, #1]
    ldr   r2, bc_slots
    mov   r1, #{CHAR_RECORD_SIZE:#x}
    mla   r2, r0, r1, r2
    ldrh  r0, [r2, #{CARD_SLOT * 2}]
    sub   r0, r0, #{FIRST_CARD:#x}
    cmp   r0, r3
    bne   bc_none
    ldr   r1, bc_points
    add   r1, r1, r0, lsl #1
    ldrsh r2, [r1]
    mov   r0, #{POINTS_PER_USE}
    mul   r0, lr, r0
    cmp   r2, r0
    blt   bc_none
    pop   {{r2, r3, pc}}
bc_none:
    mov   r0, #0
    pop   {{r2, r3, pc}}
bc_table:
    .word ${{cave_card_boosts}}
bc_slots:
    .word {CHAR_RECORDS + EQUIP_OFFSET:#x}
bc_points:
    .word {CARD_POINTS:#x}
"""

# In place of `sub r1, r1, r0` where a Special's MP is taken (r4 = the battler, its +0x86 the spell): an enhanced
# cast takes the card's points too and names its caster in the boost state; a plain one names nobody. Steal takes
# no MP (its castable answer is 1 only so that the menu takes it).
CHARGE_ASM = f"""
    push  {{r0, r2, r3, ip, lr}}
    push  {{r1}}
    ldr   r0, [r4, #{BATTLER_CHARACTER}]
    ldrh  r1, [r4, #{BATTLER_ACTION_ID:#x}]
    bl    ${{cave_card_boost_cost}}
    ldr   r3, ch_state
    cmp   r0, #0
    beq   ch_plain
    ldrsh r2, [r1]
    sub   r2, r2, r0
    strh  r2, [r1]
    ldr   r0, ch_work
    ldr   r0, [r0]
    ldrsh r0, [r0, #{WORK_ACTOR:#x}]
    strb  r0, [r3, #{STATE_ACTOR}]
    mov   r0, #{BOOST_LIMIT}
    strb  r0, [r3, #{STATE_LIMIT}]
    b     ch_done
ch_plain:
    mov   r0, #{NO_ACTOR}
    strb  r0, [r3, #{STATE_ACTOR}]
    mov   r0, #{PLAIN_LIMIT}
    strb  r0, [r3, #{STATE_LIMIT}]
ch_done:
    pop   {{r1}}
    pop   {{r0, r2, r3, ip, lr}}
    push  {{r2}}
    ldrh  r2, [r4, #{BATTLER_ACTION_ID:#x}]
    cmp   r2, #{STEAL_SPELL}
    moveq r0, #0
    pop   {{r2}}
    sub   r1, r1, r0
    bx    lr
ch_state:
    .word ${{cave_skill_boost}}
ch_work:
    .word {BATTLE_WORK_PTR:#x}
"""

# r0 = the spell picked on the Special list -> the stage limit the refusal test uses while the member aims it:
# 2 if the member's cast of it will be enhanced, else 1. Keeps every register.
MENU_ASM = f"""
    push  {{r0-r3, ip, lr}}
    mov   r1, r0
    ldr   r0, bm_menu
    ldrh  r0, [r0, #{T.MENU_MEMBER:#x}]
    ldr   r2, bm_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r0, r3, r0, r2
    ldr   r0, [r0, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_boost_cost}}
    cmp   r0, #0
    movne r0, #{BOOST_LIMIT}
    moveq r0, #{PLAIN_LIMIT}
    ldr   r1, bm_state
    strb  r0, [r1, #{STATE_LIMIT}]
    pop   {{r0-r3, ip, lr}}
    bx    lr
bm_menu:
    .word {T.MENU:#x}
bm_battlers:
    .word {BATTLERS_PTR:#x}
bm_state:
    .word ${{cave_skill_boost}}
"""

# In place of `bl func_02045114` where the name bar draws a spell's name (r3): a name the member's worn card will
# enhance is copied with the up arrow after it.
NAME_ASM = f"""
    push  {{r0-r3, ip, lr}}
    ldr   r0, bn_menu
    ldr   r1, [r0, #{MENU_BAR_ID:#x}]
    ldr   r0, [r0, #{MENU_BAR_MEMBER:#x}]
    ldr   r2, bn_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r0, r3, r0, r2
    ldr   r0, [r0, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_boost_cost}}
    cmp   r0, #0
    beq   bn_plain
    ldr   r3, [sp, #12]
    ldr   r2, bn_buffer
    mov   r1, r2
bn_copy:
    ldrb  r0, [r3], #1
    cmp   r0, #{END:#x}
    strbne r0, [r2], #1
    bne   bn_copy
    mov   r0, #{GLYPH_UP:#x}
    strb  r0, [r2], #1
    mov   r0, #{END:#x}
    strb  r0, [r2]
    str   r1, [sp, #12]
bn_plain:
    pop   {{r0-r3, ip, lr}}
    b     {DRAW_TEXT:#x}
bn_menu:
    .word {T.MENU:#x}
bn_battlers:
    .word {BATTLERS_PTR:#x}
bn_buffer:
    .word ${{cave_card_boost_name_buffer}}
"""


def boost_table_patch(poison_turns: bool) -> CaveCode:
    """The enhancing cards' table, which depends on poison-turns (cards_data.active_boosts): glue."""
    return CaveCode(
        "cave_card_boosts",
        f"    .byte {byte_list(boost_table(poison_turns))}\n    .align 2\n",
        "the skills each card enhances",
    )


def boost_patches() -> tuple:
    return (
        CaveCode("cave_card_boost_cost", COST_ASM, "an enhanced cast's points"),
        CaveCode("cave_card_boost_charge", CHARGE_ASM, "an enhanced cast takes points"),
        hook(
            CHARGE_SITE,
            CHARGE_WORD,
            "bl ${cave_card_boost_charge}",
            "an enhanced cast takes points",
        ),
        CaveCode("cave_card_boost_menu", MENU_ASM, "an enhanced cast's stage limit"),
        CaveCode(
            "cave_card_boost_name_buffer",
            f"    .space {NAME_BUFFER}\n    .align 2\n",
            "an enhanced cast's name",
        ),
        CaveCode("cave_card_boost_name", NAME_ASM, "an enhanced cast's name"),
        hook(
            NAME_DRAW,
            NAME_DRAW_WORD,
            "bl ${cave_card_boost_name}",
            "an enhanced cast's name",
        ),
    )
