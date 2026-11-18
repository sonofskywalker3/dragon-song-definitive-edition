"""Spell lists in learn order (Jeff, 2026-11-18).

The game builds a member's spell list by scanning spell ids upward, so a skill shows where its id falls,
and the ids run in the order the skills were made, not the order they are learned. Both lists that are
built that way are sorted after they are built, by the level the member learns each spell at, keeping id
order among spells learned at the same level (a stable sort). An upgrade (Skill.replaces: War Breaker for
Weapon Break, and so on) takes its base spell's key, and the base then leaves the list, so the upgrade sits
where the base was (Jeff, 2026-11-18). So a newly learned spell comes after everything learned before it,
an upgrade takes its base's place, and no learned spell already in the list moves. (Jian's Dragon Magic,
which comes with a ring and not a level, stays after his learned skills, so it moves down one place when
he learns another.)

- The battle Special list (func_02035e00 case 2: halfword spell ids at menu + 0x44, count in r7).
- The field Magic page (func_02064ff0: 8-byte entries on its stack, count in r7, party slot in sb).

Learn level: a healer's is her byte of the spell's table entry (the spell-levels schedule, and her own
skills' bytes); a fighter's is his or her row of the learned skills. Spells that are not learned by level
go first when the member has them from the start (Gabryel's Gale Cut, Rufus's Thunder Sword) and last
when they come with equipment (Jian's Dragon Magic, from the rings).
"""

from dsde.feat_skills_table import LEVEL_ROWS
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    BATTLER_ROW,
    BATTLER_SIZE,
    BATTLERS_PTR,
    NEVER,
    SPELL_ENTRY_SIZE,
    SPELL_TABLE,
    byte_list,
    hook,
)
from dsde.skills_data import FLORA, GABRYEL, LUCIA, RUFUS, SKILLS, SPELL_COUNT

GALE_CUT = 14  # Gabryel's own spell, hers from when she joins
THUNDER_SWORD = 15  # Rufus's, his from when he joins
FROM_THE_START = {GABRYEL: GALE_CUT, RUFUS: THUNDER_SWORD}
WITH_EQUIPMENT = NEVER - 1  # sorts after every learned spell (a ring's Dragon Magic)
LUCIA_LEVEL = 8  # byte of a spell table entry: Lucia's learn level index
FLORA_LEVEL = 9

MENU = 0x020B8800  # the battle menu: +0x34 the member's battler index, +0x44 the list, +0x82 1 for spells
MENU_MEMBER = 0x34
MENU_LIST = 0x44
MENU_SPELLS = 0x82
BATTLE_LIST_DONE = (
    0x02035F6C  # func_02035e00's exit, all cases: `ldr r0, [pc, #0x18]` (the menu)
)
BATTLE_LIST_DONE_WORD = 0xE59F0018
BATTLE_STRIDE = 2
FIELD_LIST_DONE = 0x02065070  # func_02064ff0 after its loop: `ldr r0, [pc, #0x24]`
FIELD_LIST_DONE_WORD = 0xE59F0024
FIELD_LIST_OUT = 0x0213A008  # what that load gives
FIELD_STRIDE = 8
KEY_ID_BITS = 6  # the sort key's low bits hold the spell id, for ties in learn level
PARTY = 0x020B464C  # s16 character id per party slot, 4 bytes apart (func_02050c50's field branch)
PARTY_SLOT_SHIFT = 2


def _order_rows() -> str:
    """Sort key per spell id, one row per fighter in LEVEL_ROWS order."""
    lines = []
    for owner in LEVEL_ROWS:
        row = [WITH_EQUIPMENT] * SPELL_COUNT
        if owner in FROM_THE_START:
            row[FROM_THE_START[owner]] = 0
        for skill in SKILLS:
            if skill.owner == owner:
                row[skill.spell] = skill.level - 1
        lines.append(f"    .byte {byte_list(bytes(row))}")
    return "\n".join(lines) + "\n    .align 2\n"


def _base_bytes() -> str:
    """Per spell id: the spell it upgrades (Skill.replaces), 0 for none."""
    row = [0] * SPELL_COUNT
    for skill in SKILLS:
        row[skill.spell] = skill.replaces
    return f"    .byte {byte_list(bytes(row))}\n    .align 2\n"


def _row_of() -> str:
    """Row of the order table per character id; 255 for the healers, who use their table bytes."""
    rows = [NEVER] * (max(LEVEL_ROWS) + 1)
    for row, owner in enumerate(LEVEL_ROWS):
        rows[owner] = row
    return ", ".join(str(row) for row in rows)


# r0 = list base, r1 = count, r2 = stride in bytes, r3 = character id -> r0 = the new count. Insertion sort of the halfword spell
# ids at base + i * stride (the field list's entries are words whose high half is 0, and their flag byte is
# 0 for every entry, so moving the low halfword is enough), by the key below, stable; then a spell whose
# upgrade is listed is dropped, so the upgrade has its place.
SORT_ASM = f"""
    push  {{r4-r11, lr}}
    mov   r4, r0
    mov   r5, r1
    mov   r6, r2
    mov   r7, r3
    mov   r8, #1
sort_outer:
    cmp   r8, r5
    bge   sort_compact
    mla   r0, r8, r6, r4
    ldrh  sb, [r0]
    mov   r0, r7
    mov   r1, sb
    bl    sort_key
    mov   sl, r0
    sub   fp, r8, #1
sort_inner:
    cmp   fp, #0
    blt   sort_place
    mla   r0, fp, r6, r4
    ldrh  r1, [r0]
    mov   r0, r7
    bl    sort_key
    cmp   r0, sl
    ble   sort_place
    mla   r0, fp, r6, r4
    ldrh  r1, [r0]
    strh  r1, [r0, r6]
    sub   fp, fp, #1
    b     sort_inner
sort_place:
    add   r0, fp, #1
    mla   r0, r6, r0, r4
    strh  sb, [r0]
    add   r8, r8, #1
    b     sort_outer

@ Drop each spell whose upgrade is also listed (the upgrade sorted into its place), keeping the order; the
@ freed entries at the end get spell 0. r8 reads, sl writes.
sort_compact:
    mov   r8, #0
    mov   sl, #0
compact_loop:
    cmp   r8, r5
    bge   compact_tail
    mla   r0, r6, r8, r4
    ldrh  sb, [r0]
    mov   fp, #0
compact_scan:
    cmp   fp, r5
    bge   compact_keep
    mla   r0, r6, fp, r4
    ldrh  r1, [r0]
    cmp   r1, #{SPELL_COUNT}
    bhs   compact_next
    ldr   r2, key_base
    ldrb  r2, [r2, r1]
    cmp   r2, sb
    beq   compact_drop
compact_next:
    add   fp, fp, #1
    b     compact_scan
compact_keep:
    mla   r0, r6, sl, r4
    strh  sb, [r0]
    add   sl, sl, #1
compact_drop:
    add   r8, r8, #1
    b     compact_loop
compact_tail:
    mov   r1, #0
    mov   r8, sl
tail_loop:
    cmp   r8, r5
    bge   sort_done
    mla   r0, r6, r8, r4
    strh  r1, [r0]
    add   r8, r8, #1
    b     tail_loop
sort_done:
    mov   r0, sl
    pop   {{r4-r11, pc}}

@ r0 = character id, r1 = spell -> r0 = its sort key, learn level << KEY_ID_BITS | spell id, where an upgrade
@ counts as its base (level and id), so it takes exactly the base's place; clobbers r1 to r3
sort_key:
    push  {{r4, lr}}
    cmp   r1, #{SPELL_COUNT}
    bhs   key_own
    ldr   r2, key_base
    ldrb  r2, [r2, r1]
    cmp   r2, #0
    movne r1, r2
key_own:
    mov   r4, r1
    bl    key_level
    orr   r0, r4, r0, lsl #{KEY_ID_BITS}
    pop   {{r4, pc}}

@ r0 = character id, r1 = spell -> r0 = the level the character learns it at; clobbers r1 to r3
key_level:
    cmp   r0, #{LUCIA}
    moveq r2, #{LUCIA_LEVEL}
    cmp   r0, #{FLORA}
    moveq r2, #{FLORA_LEVEL}
    cmpne r0, #{LUCIA}
    bne   key_fighter
    ldr   r3, key_spells
    mov   r0, #{SPELL_ENTRY_SIZE}
    mla   r3, r0, r1, r3
    ldrb  r0, [r3, r2]
    bx    lr
key_fighter:
    adr   r2, key_rows
    ldrb  r2, [r2, r0]
    mov   r0, #{WITH_EQUIPMENT}
    cmp   r2, #{NEVER}
    bxeq  lr
    cmp   r1, #{SPELL_COUNT}
    bxhs  lr
    mov   r0, #{SPELL_COUNT}
    mul   r2, r0, r2
    ldr   r0, key_order
    add   r0, r0, r2
    ldrb  r0, [r0, r1]
    bx    lr
key_spells:
    .word {SPELL_TABLE:#x}
key_order:
    .word ${{cave_skill_order}}
key_base:
    .word ${{cave_skill_base}}
key_rows:
    .byte {_row_of()}
    .align 2
"""

# Replaces the load at func_02035e00's exit; r7 = the count. Only the spell list (menu + 0x82 = 1) is
# sorted; the item and card lists keep the game's order.
BATTLE_ASM = f"""
    push  {{lr}}
    ldr   r0, battle_menu
    ldrh  r1, [r0, #{MENU_SPELLS:#x}]
    cmp   r1, #1
    bne   battle_out
    ldrh  r1, [r0, #{MENU_MEMBER:#x}]
    ldr   r2, battle_battlers
    ldr   r2, [r2]
    mov   r3, #{BATTLER_SIZE:#x}
    mla   r1, r3, r1, r2
    ldr   r3, [r1, #{BATTLER_ROW:#x}]
    add   r0, r0, #{MENU_LIST:#x}
    mov   r1, r7
    mov   r2, #{BATTLE_STRIDE}
    bl    ${{cave_skill_sort}}
    mov   r7, r0
battle_out:
    ldr   r0, battle_menu
    pop   {{pc}}
battle_menu:
    .word {MENU:#x}
battle_battlers:
    .word {BATTLERS_PTR:#x}
"""

# Replaces the load after func_02064ff0's loop: r5 = its list (its sp), r7 = the count, sb = the party slot
FIELD_ASM = f"""
    push  {{lr}}
    mov   r0, r5
    mov   r1, r7
    mov   r2, #{FIELD_STRIDE}
    ldr   r3, field_party
    add   r3, r3, sb, lsl #{PARTY_SLOT_SHIFT}
    ldrsh r3, [r3]
    bl    ${{cave_skill_sort}}
    mov   r7, r0
    ldr   r0, field_out
    pop   {{pc}}
field_party:
    .word {PARTY:#x}
field_out:
    .word {FIELD_LIST_OUT:#x}
"""

if SPELL_COUNT > 1 << KEY_ID_BITS:
    raise ValueError(f"spell ids up to {SPELL_COUNT - 1} do not fit the sort key's {KEY_ID_BITS} bits")

ORDER_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_order", _order_rows(), "the fighters' spells in learn order"),
    CaveCode("cave_skill_base", _base_bytes(), "which spell each upgrade replaces"),
    CaveCode("cave_skill_sort", SORT_ASM, "spell lists sorted by learn level"),
    CaveCode("cave_skill_order_battle", BATTLE_ASM, "the Special list in learn order"),
    CaveCode("cave_skill_order_field", FIELD_ASM, "the Magic page in learn order"),
    hook(
        BATTLE_LIST_DONE,
        BATTLE_LIST_DONE_WORD,
        "bl ${cave_skill_order_battle}",
        "the Special list in learn order",
    ),
    hook(
        FIELD_LIST_DONE,
        FIELD_LIST_DONE_WORD,
        "bl ${cave_skill_order_field}",
        "the Magic page in learn order",
    ),
)
