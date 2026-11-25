"""Who a worn card is used on: basic or upgraded by wearer, and the refusal of a use that would change nothing
(docs/plan-cards.md 3).

A card paired with a kit skill (cards_data.PAIRS) works on one picked target for a wearer who has not learned
that skill, and on all targets (the card's own flags) for one who has; every other card keeps its own flags.
`cave_card_targets` answers for a character, and both ends ask it:

- the Special list's OK handler reads the card spell's target bits from it (0x02036CE0) instead of the spell
  table, so a basic use opens the enemy grid or the ally picker as a one-target skill does;
- the turn resolver's item branch, where a card's targets are filled in (0x02051F58), takes the same bits, and a
  one-enemy card uses the enemy picked on the grid (0x02051F84) instead of a random one, Dagon included.

"Learned" is the level test the Special list uses: the learner's level index has reached the skill's learn level
(its row of the skills table, or the healers' spell-levels schedule).

A use that would change nothing is refused before the turn with "No effect!" and no points taken, as the skills
are: a stat card when every stat it moves is already a stage past 0 that way, a status card when the target
already has a status (or is a boss immune to it), a battle-wide card when its flag is already set. For an
all-target use the list tests every living target; for a one-target use the card's effect is written into the
card spell's effect record, so the grid and the ally picker refuse a wasted pick through the skills' own test.
"""

import struct

from dsde import targeting_consts as T
from dsde.cards_common import (
    CHAR_RECORD_SIZE,
    FIRST_BOSS_CARD,
    FIRST_CARD,
    ITEM_SIZE,
    ITEM_TABLE,
)
from dsde.cards_data import GAME_SPELLS, PAIRS, CardPair
from dsde.feat_spell_levels import SCHEDULE
from dsde.patching import CaveCode
from dsde.skills_cards import CARD_SPELL
from dsde.skills_common import (
    ALL_TARGETS,
    FX_ARG,
    FX_DELTA,
    FX_KIND,
    FX_SIZE_SHIFT,
    LEVEL_INDEX,
    RECORD_SIZE,
    RECORD_STAGES,
    RECORDS_PTR,
    STRING_NO_EFFECT,
    TARGET_BITS,
    VANILLA_ARM9,
    hook,
)
from dsde.skills_data import BY_SPELL
from dsde.skills_types import LUCIA, Kind, Target

ARM9_BASE = 0x02000000
CARD_EFFECTS = 0x0209D124  # 12 bytes per effect id from 0x100: u32 flags, u32 amount, u16 mask, u16 row
CARD_EFFECT_SIZE = 12
FIRST_EFFECT = 0x100
ITEM_EFFECT = 2
CARD_RAISE = 0x1000000
CARD_LOWER = 0x2000000
CARD_STATUS = 0x4000000
# a battle-wide card's effect flag -> its bit of the battle flags word (docs/re-cards.md 4)
CARD_BATTLE_BITS = {
    0x8000: 0x01,
    0x10000: 0x02,
    0x20000: 0x04,
    0x2000: 0x08,
    0x4000: 0x20,
    0x40000: 0x40,
    0x80000: 0x80,
}
MONSTER_CARDS = FIRST_BOSS_CARD - FIRST_CARD
NO_LEARNER = 0xFF
LEARNERS = 2  # learner slots per card
LEARNER_SHIFT = 2  # 2 bytes per learner, 4 per card
CARD_FLAGS = 0x0206AA68  # (item) -> the item's card effect flags
NO_BASIC, BASIC_ENEMY, BASIC_ALLY, BASIC_REGEN = 0, 1, 2, 3
BASIC_FLAG = (
    0x100  # with a card index: the wearer gets the basic version (cave_card_idle)
)
NAMIA_REGEN = 0x0206A790  # func_0206a744: `orr r3, r3, #8`, Namia's 10% regen bit
NAMIA_REGEN_WORD = 0xE3833008
NAMIA_BIT = 0x08
DIVINE_RAIN_BIT = 0x10  # Divine Rain's 5% regen
BATTLE_ACTOR = 0x32  # battle work: the acting battler

# The card record, 8 bytes per monster card
REC_SHIFT = 3
REC_BASIC = 0  # NO_BASIC, BASIC_ENEMY, or BASIC_ALLY
REC_KIND = (
    1  # Kind.NONE, STAGE, STATUS, or FLAG: what "would change nothing" means for it
)
REC_ARG = (
    2  # STAGE: the lowest stat it moves; STATUS: the status; FLAG: the battle flag bit
)
REC_DELTA = 3  # s8, STAGE: +1 or -1
REC_MASK = 4  # u16, STAGE: bit n = stat n
REC_BASIC_ARG = 6  # FLAG: the battle flag bit of the basic version

MENU_FLAGS_CALL = 0x02036CE0  # Special list OK: `bl func_02050094` (the spell's flags), r0 = the spell
MENU_FLAGS_WORD = 0xEB0064EB
SPELL_FLAGS = 0x02050094
RESOLVE_FLAGS_CALL = (
    0x02051F58  # func_020514ec, item branch: `bl func_0206aa68`, r4 = the battler
)
RESOLVE_FLAGS_WORD = 0xEB0062C2
RESOLVE_PICK_CALL = (
    0x02051F84  # the item branch's one enemy: `bl func_02050f78` with (3, 0)
)
RESOLVE_PICK_WORD = 0xEBFFFBFB
BATTLER_CHARACTER = 4
BATTLER_RECORD = 0x10
PARTY_SLOTS = 3


def _effect(arm9: bytes, card: int) -> tuple[int, int]:
    """A card's effect flags and mask, as the game keeps them."""
    effect = struct.unpack_from(
        "<H", arm9, ITEM_TABLE + card * ITEM_SIZE + ITEM_EFFECT - ARM9_BASE
    )[0]
    flags, _amount, mask = struct.unpack_from(
        "<IIH",
        arm9,
        CARD_EFFECTS + (effect - FIRST_EFFECT) * CARD_EFFECT_SIZE - ARM9_BASE,
    )
    return flags, mask


def _lowest_bit(mask: int) -> int:
    return (mask & -mask).bit_length() - 1


def card_record(arm9: bytes, card: int, pair: CardPair | None) -> bytes:
    """The 8-byte record of a monster card: its basic version and its "would change nothing" test."""
    flags, mask = _effect(arm9, card)
    kind, arg, delta, stat_mask = Kind.NONE, 0, 0, 0
    if flags & (CARD_RAISE | CARD_LOWER):
        kind, stat_mask = Kind.STAGE, mask
        arg, delta = _lowest_bit(mask), 1 if flags & CARD_RAISE else -1
    elif flags & CARD_STATUS:
        kind, arg = Kind.STATUS, _lowest_bit(mask)
    else:
        bits = [bit for flag, bit in CARD_BATTLE_BITS.items() if flags & flag]
        if bits:
            kind, arg = Kind.FLAG, bits[0]
    basic, basic_arg = NO_BASIC, arg
    if pair is not None and pair.basic_target == Target.ENEMY_ONE:
        basic = BASIC_ENEMY
    elif pair is not None and pair.basic_target == Target.ALLY_ONE:
        basic = BASIC_ALLY
    elif pair is not None and arg == NAMIA_BIT:
        basic, basic_arg = BASIC_REGEN, DIVINE_RAIN_BIT
    return struct.pack("<BBBbHBx", basic, kind, arg, delta, stat_mask, basic_arg)


def learn_index(owner: int, spell: int) -> int:
    """The level index at which `owner` has learned `spell`: a healer's game spell by the spell-levels
    schedule, a skill by its own level."""
    if spell in GAME_SPELLS:
        _name, lucia, flora, _vanilla = SCHEDULE[spell]
        level = lucia if owner == LUCIA else flora
        if level is None:
            raise ValueError(f"spell {spell} is never learned by member {owner}")
        return level - 1
    return BY_SPELL[spell].level - 1


def learners(pair: CardPair | None) -> bytes:
    """A card's learners: (character, learn level index) twice, 0xFF for none."""
    rows = [] if pair is None else list(pair.learners)
    out = bytearray()
    for slot in range(LEARNERS):
        if slot < len(rows):
            owner, spell = rows[slot]
            out += bytes((owner, learn_index(owner, spell)))
        else:
            out += bytes((NO_LEARNER, NO_LEARNER))
    return bytes(out)


def _bytes_asm(data: bytes) -> str:
    return f"    .byte {', '.join(str(b) for b in data)}\n    .align 2\n"


def _records_asm(arm9: bytes) -> str:
    by_card = {pair.card: pair for pair in PAIRS}
    records = b"".join(
        card_record(arm9, card, by_card.get(card))
        for card in range(FIRST_CARD, FIRST_BOSS_CARD)
    )
    return _bytes_asm(records)


def _learners_asm() -> str:
    by_card = {pair.card: pair for pair in PAIRS}
    rows = b"".join(
        learners(by_card.get(card)) for card in range(FIRST_CARD, FIRST_BOSS_CARD)
    )
    return _bytes_asm(rows)


# r0 = character id -> r0 = the basic version the wearer gets of their worn card (BASIC_*; NO_BASIC for a card
# with one version or a wearer who has learned its skill), r1 = card - FIRST_CARD, or -1 with no battle card
# worn. Keeps r2 to r11.
BASIC_ASM = f"""
    push  {{r2-r5, lr}}
    mov   r4, r0
    mov   r1, #0
    bl    ${{cave_card_worn_battle}}
    subs  r5, r0, #{FIRST_CARD:#x}
    movmi r0, #{NO_BASIC}
    mvnmi r1, #0
    popmi {{r2-r5, pc}}
    ldr   r2, cb_records
    add   r2, r2, r5, lsl #{REC_SHIFT}
    ldrb  r0, [r2, #{REC_BASIC}]
    cmp   r0, #{NO_BASIC}
    beq   cb_done
    ldr   ip, cb_level
    mov   r3, #{CHAR_RECORD_SIZE:#x}
    mla   ip, r4, r3, ip
    ldr   ip, [ip]
    ldr   r2, cb_learners
    add   r2, r2, r5, lsl #{LEARNER_SHIFT}
    mov   r3, #0
cb_learner:
    ldrb  r1, [r2], #1
    ldrb  lr, [r2], #1
    cmp   r1, r4
    bne   cb_next
    cmp   ip, lr
    movhs r0, #{NO_BASIC}
    bhs   cb_done
cb_next:
    add   r3, r3, #1
    cmp   r3, #{LEARNERS}
    blt   cb_learner
cb_done:
    mov   r1, r5
    pop   {{r2-r5, pc}}
cb_records:
    .word ${{cave_card_records}}
cb_learners:
    .word ${{cave_card_learners}}
cb_level:
    .word {LEVEL_INDEX:#x}
"""

# r0 = character id -> r0 = the target bits of a use of their worn card (Target), r1 = card - FIRST_CARD, r2 = the
# basic version they get (BASIC_*), or r0 = ENEMY_ALL and r1 = -1 with no battle card worn. Keeps r3 to r11.
TARGETS_ASM = f"""
    push  {{r3-r5, lr}}
    bl    ${{cave_card_basic}}
    movs  r5, r1
    movmi r0, #{Target.ENEMY_ALL:#x}
    popmi {{r3-r5, pc}}
    mov   r4, r0
    add   r0, r5, #{FIRST_CARD:#x}
    bl    {CARD_FLAGS:#x}
    and   r0, r0, #{TARGET_BITS:#x}
    cmp   r4, #{BASIC_ENEMY}
    moveq r0, #{Target.ENEMY_ONE:#x}
    cmp   r4, #{BASIC_ALLY}
    moveq r0, #{Target.ALLY_ONE:#x}
    mov   r1, r5
    mov   r2, r4
    pop   {{r3-r5, pc}}
"""

# In place of `orr r3, r3, #8` in func_0206a744, where Namia's effect sets its regen bit (ip = the battle work, its
# +0x32 the acting battler): a wearer who has not learned Divine Rain gets Divine Rain's 5% bit instead of 10%.
NAMIA_ASM = f"""
    push  {{r0-r2, ip, lr}}
    ldrsh r0, [ip, #{BATTLE_ACTOR:#x}]
    ldr   r1, cn_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_basic}}
    cmp   r0, #{BASIC_REGEN}
    pop   {{r0-r2, ip, lr}}
    orrne r3, r3, #{NAMIA_BIT:#x}
    orreq r3, r3, #{DIVINE_RAIN_BIT:#x}
    bx    lr
cn_battlers:
    .word {T.BATTLERS_PTR:#x}
"""

# r0 = battler index, r1 = card - FIRST_CARD (| BASIC_FLAG for the basic version) -> r0 = 0 if a use would change something on that battler, else
# "No effect!". A stat card: every stat it moves already a stage past 0 that way; a status or battle-wide card:
# the skills' own test (cave_skill_idle), its kind and argument written into the card spell's effect record.
IDLE_ASM = f"""
    push  {{r4-r6, lr}}
    and   r4, r1, #{BASIC_FLAG:#x}
    bic   r1, r1, #{BASIC_FLAG:#x}
    ldr   r2, ci_records
    add   r2, r2, r1, lsl #{REC_SHIFT}
    ldrb  r3, [r2, #{REC_KIND}]
    cmp   r3, #{Kind.STAGE}
    bne   ci_other
    ldr   ip, ci_battlers
    ldr   ip, [ip]
    mov   r1, #{T.BATTLER_SIZE:#x}
    mla   r0, r1, r0, ip
    ldr   r0, [r0, #{BATTLER_RECORD:#x}]
    ldr   r3, ci_stat_records
    ldr   r3, [r3]
    mov   ip, #{RECORD_SIZE:#x}
    mla   r0, ip, r0, r3
    add   r0, r0, #{RECORD_STAGES:#x}
    ldrh  r4, [r2, #{REC_MASK}]
    ldrsb r5, [r2, #{REC_DELTA}]
    mov   r6, #0
ci_stat:
    movs  r4, r4, lsr #1
    bcc   ci_skip
    add   r3, r0, r6, lsl #1
    ldrsh r3, [r3]
    cmp   r5, #0
    rsblt r3, r3, #0
    cmp   r3, #0
    ble   ci_fine
ci_skip:
    add   r6, r6, #1
    cmp   r4, #0
    bne   ci_stat
    mov   r0, #{STRING_NO_EFFECT}
    pop   {{r4-r6, pc}}
ci_other:
    cmp   r3, #{Kind.NONE}
    beq   ci_fine
    ldr   ip, ci_fx
    strb  r3, [ip, #{FX_KIND}]
    cmp   r4, #0
    ldrbeq r3, [r2, #{REC_ARG}]
    ldrbne r3, [r2, #{REC_BASIC_ARG}]
    strb  r3, [ip, #{FX_ARG}]
    mov   r1, #{CARD_SPELL}
    bl    ${{cave_skill_idle}}
    pop   {{r4-r6, pc}}
ci_fine:
    mov   r0, #0
    pop   {{r4-r6, pc}}
ci_records:
    .word ${{cave_card_records}}
ci_battlers:
    .word {T.BATTLERS_PTR:#x}
ci_stat_records:
    .word {RECORDS_PTR:#x}
ci_fx:
    .word ${{cave_skill_fx}} + {CARD_SPELL << FX_SIZE_SHIFT}
"""

# In place of `bl func_02050094` in the Special list's OK handler (r0 = the spell). Any other spell: its flags.
# The card spell: the target bits of the member's card use. An all-target use that would change nothing on any
# living target is refused there (the handler's r4, r5, and r7 kept, r6 = the menu, as cave_skill_refuse wants);
# a one-target use writes the card's test into the card spell's effect record for the grid and the picker.
MENU_ASM = f"""
    cmp   r0, #{CARD_SPELL}
    bne   {SPELL_FLAGS:#x}
    push  {{r4-r7, lr}}
    ldr   r6, cm_menu
    ldrh  r0, [r6, #{T.MENU_MEMBER:#x}]
    ldr   r1, cm_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_targets}}
    mov   r5, r0
    movs  r6, r1
    bmi   cm_none
    cmp   r2, #{BASIC_REGEN}
    ldr   r2, cm_records
    add   r2, r2, r6, lsl #{REC_SHIFT}
    orreq r6, r6, #{BASIC_FLAG:#x}
    ldr   r3, cm_fx
    tst   r5, #{ALL_TARGETS:#x}
    bne   cm_all
    ldrb  r0, [r2, #{REC_KIND}]
    strb  r0, [r3, #{FX_KIND}]
    ldrb  r0, [r2, #{REC_ARG}]
    strb  r0, [r3, #{FX_ARG}]
    ldrb  r0, [r2, #{REC_DELTA}]
    strb  r0, [r3, #{FX_DELTA}]
    b     cm_done
cm_all:
    cmp   r5, #{Target.ALLY_ALL:#x}
    beq   cm_allies
    mvn   r4, #0
cm_enemy:
    mov   r0, r4
    mov   r1, #{T.ROWS_ANY}
    bl    ${{cave_tgt_after}}
    cmp   r0, #0
    blt   cm_enemies_done
    mov   r4, r0
    mov   r1, r6
    bl    ${{cave_card_idle}}
    cmp   r0, #0
    bne   cm_enemy
    b     cm_fine
cm_enemies_done:
    cmn   r4, #1
    bne   cm_refuse
    b     cm_fine
cm_allies:
    mov   r4, #0
    mov   r7, #0
cm_ally:
    ldr   r0, cm_battlers
    ldr   r0, [r0]
    mov   r1, #{T.BATTLER_SIZE:#x}
    mla   r0, r1, r4, r0
    bl    {T.BATTLER_ALIVE:#x}
    cmp   r0, #0
    ble   cm_ally_next
    add   r7, r7, #1
    mov   r0, r4
    mov   r1, r6
    bl    ${{cave_card_idle}}
    cmp   r0, #0
    beq   cm_fine
cm_ally_next:
    add   r4, r4, #1
    cmp   r4, #{PARTY_SLOTS}
    blt   cm_ally
    cmp   r7, #0
    bne   cm_refuse
cm_fine:
cm_none:
    ldr   r3, cm_fx
    mov   r0, #{Kind.NONE}
    strb  r0, [r3, #{FX_KIND}]
cm_done:
    mov   r0, r5
    pop   {{r4-r7, pc}}
cm_refuse:
    ldr   r3, cm_fx
    mov   r0, #{Kind.NONE}
    strb  r0, [r3, #{FX_KIND}]
    pop   {{r4-r7, lr}}
    ldr   r6, cm_menu
    mov   r0, #{STRING_NO_EFFECT}
    b     ${{cave_skill_refuse}}
cm_menu:
    .word {T.MENU:#x}
cm_battlers:
    .word {T.BATTLERS_PTR:#x}
cm_records:
    .word ${{cave_card_records}}
cm_fx:
    .word ${{cave_skill_fx}} + {CARD_SPELL << FX_SIZE_SHIFT}
"""

# In place of `bl func_0206aa68` in the resolver's item branch (r0 = the item, r4 = the battler): a monster card's
# flags with the target bits of its wearer's use.
RESOLVE_ASM = f"""
    sub   r1, r0, #{FIRST_CARD:#x}
    cmp   r1, #{MONSTER_CARDS}
    bhs   {CARD_FLAGS:#x}
    push  {{r4, r5, lr}}
    bl    {CARD_FLAGS:#x}
    bic   r5, r0, #{TARGET_BITS:#x}
    ldr   r0, [r4, #{BATTLER_CHARACTER}]
    bl    ${{cave_card_targets}}
    orr   r0, r0, r5
    pop   {{r4, r5, pc}}
"""


def target_patches() -> tuple:
    arm9 = VANILLA_ARM9.read_bytes()
    return (
        CaveCode(
            "cave_card_records", _records_asm(arm9), "each card's targets and test"
        ),
        CaveCode("cave_card_learners", _learners_asm(), "who upgrades each card"),
        CaveCode("cave_card_basic", BASIC_ASM, "a card's basic version by wearer"),
        CaveCode("cave_card_targets", TARGETS_ASM, "a card's targets by wearer"),
        CaveCode("cave_card_namia", NAMIA_ASM, "Namia's basic version: 5% regen"),
        hook(
            NAMIA_REGEN,
            NAMIA_REGEN_WORD,
            "bl ${cave_card_namia}",
            "Namia's basic version: 5% regen",
        ),
        CaveCode("cave_card_idle", IDLE_ASM, "would a card change nothing"),
        CaveCode("cave_card_menu", MENU_ASM, "the card spell's targets in the list"),
        hook(
            MENU_FLAGS_CALL,
            MENU_FLAGS_WORD,
            "bl ${cave_card_menu}",
            "the card spell's targets in the list",
        ),
        CaveCode(
            "cave_card_resolve_targets", RESOLVE_ASM, "a card's targets by wearer"
        ),
        hook(
            RESOLVE_FLAGS_CALL,
            RESOLVE_FLAGS_WORD,
            "bl ${cave_card_resolve_targets}",
            "a card's targets by wearer",
        ),
        hook(
            RESOLVE_PICK_CALL,
            RESOLVE_PICK_WORD,
            "bl ${cave_skill_pick}",
            "a one-enemy card uses the picked enemy",
        ),
    )
