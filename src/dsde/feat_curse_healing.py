"""While Jian is cursed, items do not heal him and Lucia's magic heals him at a reduced rate (Jeff, 2026-10-09).

The Curse of Lost Equilibrium runs from the end of the San Coliseum (story flag 0x33) to the Zethos fight
(0x79 set after it). In battle the game keeps it as one halfword, battle ctx 0x020B85B8 + 0x5C, set at battle
start from those two flags and cleared mid-fight by Zethos's skill 21 on round 3 (docs/re-curse-battle-speed.md
part 1). In the field nothing tracks it, so the field hooks test the story flags (0x33 set, 0x79 clear) in the
flag words behind 0x020B4640. The battle hooks read the battle flag, so healing works again from the moment
Zethos lifts the curse, before 0x79 is set.

What the curse does, and what the player sees (docs/plan-curse.md has the measured behavior). Statues still
heal him fully; healing magic (Althena's power, dampened) heals him at CURSE_HEAL_PERCENT; items do nothing:

- Field menu, Healing Gum and Healing Drop on Jian: the game's own "HP is already full" refusal
  (func_020635cc returns 0 before the item is used), so the item is not used up and the menu answers as it
  does for a full-HP target.
- Field menu, an all-allies HP item (the card 0xEB): heals the others, not Jian (used up as usual).
- Battle, any item that restores HP on Jian (func_0206a2f8): his HP stays; no number shows, as when a heal
  meets a full-HP ally. A single-target item goes back into the bag, because the battle takes it out of
  the bag when the turn starts (func_020514ec).
- Healing Water and Tender Rain, field and battle (func_02050850, the spell heal amount, shared by both):
  amount * CURSE_HEAL_PERCENT / 100 for Jian, rounded down, at least 1. They target him and cost MP as usual.
  Items never reach func_02050850 (they use func_0206a8b8), and neither do revives (Miracle Tears sets 10% in
  func_020500dc; Angel's Tears is an item) or Divine Rain (no heal flag).

Not blocked: reviving (Angel's Tears, Miracle Tears, the 10% revive) brings a fallen Jian back, so a knock-out
never strands him until the next statue; MP items still restore his MP (the curse is about healing; his MP
only feeds the Dragon Magic rings); status cures still cure. Healing statues set HP to max directly in the
field loop and are untouched.

This composes with no-curse-penalty (which keeps Jian's 3-hit combo): the two touch different code, and both
are meant to be on together. Nothing here changes any text; the vanilla "The Curse of Lost Equilibrium has
been broken!" line stays.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

FLAGS_CTX_PTR = 0x020B4640  # pointer to the story flag words (bit n of word n >> 5)
CURSE_FLAG_WORD = 0x33 >> 5  # story flag 0x33: set at the end of the San Coliseum
CURSE_FLAG_BIT = 1 << (0x33 & 0x1F)
LIFTED_FLAG_WORD = 0x79 >> 5  # story flag 0x79: set after the Zethos fight
LIFTED_FLAG_BIT = 1 << (0x79 & 0x1F)
WORD_BYTES = 4
BATTLE_CURSE = 0x020B85B8 + 0x5C  # battle ctx halfword: 1 while cursed this battle
JIAN = 0  # character id / party record index
PARTY_BATTLERS = 4  # battlers 0..3 are the party
BATTLE_CHARS = 0x020B8620  # pointer to the battle character records
BATTLE_CHAR_SIZE = 0x6C
BATTLE_CHAR_ID = 4
BATTLER_CHAR = 0x10  # battler +0x10: index of its battle character record
STAGING = 0x0213B91C  # item target staging: status, HP, max HP, MP, max MP
STAGING_HP = 4
INVENTORY = 0x0213B930
APPLY_MEDICINE = 0x0206A8B8  # func_0206a8b8: apply an item's medicine effect to STAGING
ITEM_ALL_TARGETS = 0x0206B674  # func_0206b674: 1 for items that act on every ally
ADD_ITEM = 0x0206B98C  # func_0206b98c(inventory, item, count)

# func_02050850 (spell heal amount; r4 = 1 in battle, r6 = target battler there): ldr r0, [sp, #0x14]
SPELL_AMOUNT_LOAD = 0x020509D0
SPELL_AMOUNT_LOAD_WORD = 0xE59D0014
SPELL_TARGET_SP = 4 + 4  # [sp, #4] of the frame, past the cave's pushed lr
SPELL_AMOUNT_SP = 0x14 + 4
# func_020635cc (field item use), Healing Gum / Drop: cmp r2 (HP), r0 (max HP); r3 = record index
FIELD_ITEM_FULL_CMP = 0x020636F4
FIELD_ITEM_FULL_CMP_WORD = 0xE1520000
# func_020635cc, an all-allies item: bl func_0206a8b8 per member; r9 -> the member's s16 record index
FIELD_ITEM_ALL_APPLY = 0x020638F8
FIELD_ITEM_ALL_APPLY_WORD = 0xEB001BEE
# func_0206a2f8 (battle item effect, r8 = target battler, [sp, #4] = its index): bl func_0206a8b8
BATTLE_ITEM_APPLY = 0x0206A630
BATTLE_ITEM_APPLY_WORD = 0xEB0000A0
BATTLE_ITEM_TARGET_SP = 4 * 4 + 4  # past the cave's four pushed registers
# Spell heals on cursed Jian: amount * CURSE_HEAL_PERCENT / 100, rounded down, at least 1 (Jeff, 2026-10-09:
# 25 to 50; it is Althena's power, dampened). Items do nothing.
CURSE_HEAL_PERCENT = 50
DIV100_MAGIC = (
    0x51EB851F  # x / 100 = (x * DIV100_MAGIC) >> (32 + DIV100_SHIFT), as the game does
)
DIV100_SHIFT = 5


def curse_no_healing(percent: int = CURSE_HEAL_PERCENT) -> Feature:
    """The feature with spell heals on cursed Jian scaled to `percent` (tests build 25 and 50)."""
    return Feature(
        "curse-no-healing",
        (
            CaveCode(
                "cave_curse_field",
                f"""
    ldr   r0, curse_flags
    ldr   r0, [r0]
    ldr   r1, [r0, #{LIFTED_FLAG_WORD * WORD_BYTES}]
    tst   r1, #{LIFTED_FLAG_BIT:#x}
    movne r0, #0
    bxne  lr
    ldr   r1, [r0, #{CURSE_FLAG_WORD * WORD_BYTES}]
    tst   r1, #{CURSE_FLAG_BIT:#x}
    moveq r0, #0
    movne r0, #1
    bx    lr
curse_flags:
    .word {FLAGS_CTX_PTR:#x}
""",
                "r0 = 1 while story flag 0x33 is set and 0x79 is not (field)",
            ),
            CaveCode(
                "cave_curse_field_jian",
                f"""
    cmp   r0, #{JIAN}
    movne r0, #0
    bxne  lr
    b     ${{cave_curse_field}}
""",
                "r0 = 1 when party record r0 is Jian and the story curse holds",
            ),
            CaveCode(
                "cave_curse_battle",
                f"""
    ldr   r0, curse_battle
    ldrh  r0, [r0]
    bx    lr
curse_battle:
    .word {BATTLE_CURSE:#x}
""",
                "r0 = the battle's curse flag",
            ),
            CaveCode(
                "cave_curse_spell_amount",
                f"""
    push  {{lr}}
    ldr   r0, [sp, #{SPELL_TARGET_SP}]
    cmp   r0, #{JIAN}
    bne   spell_keep
    cmp   r4, #0
    beq   spell_field
    cmp   r6, #{PARTY_BATTLERS}
    bhs   spell_keep
    bl    ${{cave_curse_battle}}
    b     spell_check
spell_field:
    bl    ${{cave_curse_field}}
spell_check:
    cmp   r0, #0
    ldr   r0, [sp, #{SPELL_AMOUNT_SP}]
    popeq {{pc}}
    cmp   r0, #0
    pople {{pc}}
    mov   r1, #{percent}
    mul   r2, r0, r1
    ldr   r1, div100
    smull r3, r0, r1, r2
    mov   r0, r0, asr #{DIV100_SHIFT}
    cmp   r0, #0
    moveq r0, #1
    str   r0, [sp, #{SPELL_AMOUNT_SP}]
    pop   {{pc}}
spell_keep:
    ldr   r0, [sp, #{SPELL_AMOUNT_SP}]
    pop   {{pc}}
div100:
    .word {DIV100_MAGIC:#x}
""",
                f"spell heals on cursed Jian at {percent}%",
            ),
            CaveCode(
                "cave_curse_field_item_full",
                """
    push  {r0-r3, lr}
    mov   r0, r3
    bl    ${cave_curse_field_jian}
    cmp   r0, #0
    pop   {r0-r3, lr}
    bne   curse_full
    cmp   r2, r0
    bx    lr
curse_full:
    cmp   r0, r0
    bx    lr
""",
                "field Healing Gum / Drop: cursed Jian counts as full HP",
            ),
            CaveCode(
                "cave_curse_field_item_all",
                f"""
    push  {{r4, r5, lr}}
    ldr   r5, staging
    ldr   r4, [r5, #{STAGING_HP}]
    bl    {APPLY_MEDICINE:#x}
    cmp   r4, #0
    ble   item_all_done
    ldrsh r0, [r9]
    bl    ${{cave_curse_field_jian}}
    cmp   r0, #0
    strne r4, [r5, #{STAGING_HP}]
item_all_done:
    pop   {{r4, r5, pc}}
staging:
    .word {STAGING:#x}
""",
                "field all-allies item: cursed Jian keeps his HP",
            ),
            CaveCode(
                "cave_curse_battle_item",
                f"""
    push  {{r4, r5, r6, lr}}
    mov   r5, r0
    ldr   r6, staging
    ldr   r4, [r6, #{STAGING_HP}]
    bl    {APPLY_MEDICINE:#x}
    ldr   r0, [sp, #{BATTLE_ITEM_TARGET_SP}]
    cmp   r0, #{PARTY_BATTLERS}
    bhs   item_done
    cmp   r4, #0
    ble   item_done
    ldr   r0, [r6, #{STAGING_HP}]
    cmp   r0, r4
    ble   item_done
    ldr   r0, [r8, #{BATTLER_CHAR}]
    ldr   r1, battle_chars
    ldr   r1, [r1]
    mov   r2, #{BATTLE_CHAR_SIZE}
    mla   r3, r0, r2, r1
    ldr   r0, [r3, #{BATTLE_CHAR_ID}]
    cmp   r0, #{JIAN}
    bne   item_done
    bl    ${{cave_curse_battle}}
    cmp   r0, #0
    beq   item_done
    str   r4, [r6, #{STAGING_HP}]
    mov   r0, r5
    bl    {ITEM_ALL_TARGETS:#x}
    cmp   r0, #0
    bne   item_done
    ldr   r0, inventory
    mov   r1, r5
    mov   r2, #1
    bl    {ADD_ITEM:#x}
item_done:
    pop   {{r4, r5, r6, pc}}
staging:
    .word {STAGING:#x}
battle_chars:
    .word {BATTLE_CHARS:#x}
inventory:
    .word {INVENTORY:#x}
""",
                "battle item: cursed Jian keeps his HP, a single-target item goes back in the bag",
            ),
            AsmPatch(
                SPELL_AMOUNT_LOAD,
                SPELL_AMOUNT_LOAD + 4,
                SPELL_AMOUNT_LOAD_WORD,
                SPELL_AMOUNT_LOAD_WORD,
                "bl ${cave_curse_spell_amount}",
                "healing spells: reduced on cursed Jian",
            ),
            AsmPatch(
                FIELD_ITEM_FULL_CMP,
                FIELD_ITEM_FULL_CMP + 4,
                FIELD_ITEM_FULL_CMP_WORD,
                FIELD_ITEM_FULL_CMP_WORD,
                "bl ${cave_curse_field_item_full}",
                "field HP items: refused on cursed Jian, not used up",
            ),
            AsmPatch(
                FIELD_ITEM_ALL_APPLY,
                FIELD_ITEM_ALL_APPLY + 4,
                FIELD_ITEM_ALL_APPLY_WORD,
                FIELD_ITEM_ALL_APPLY_WORD,
                "bl ${cave_curse_field_item_all}",
                "field all-allies items: no HP for cursed Jian",
            ),
            AsmPatch(
                BATTLE_ITEM_APPLY,
                BATTLE_ITEM_APPLY + 4,
                BATTLE_ITEM_APPLY_WORD,
                BATTLE_ITEM_APPLY_WORD,
                "bl ${cave_curse_battle_item}",
                "battle HP items: no HP for cursed Jian, item returned",
            ),
        ),
    )


CURSE_NO_HEALING = curse_no_healing()
