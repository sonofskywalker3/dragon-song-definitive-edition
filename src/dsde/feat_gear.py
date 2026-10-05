"""Broken gear comes back after battle; stolen items come back when the thief dies.

Design section 6. Plan, register notes and evidence: docs/plan-break-steal.md. Three hooks, each a
`bl` swap that calls an ITCM routine which then runs the displaced call.

Thieves are not tracked individually: enemies move between battler slots when the front row dies
(a back-row enemy is copied into the dead one's slot and renumbered, seen in the emulator), so no
field identifies the thief for the whole battle. Enemies never flee and a battle is only won when
every enemy is dead, so "the thief died" is the same as "the battle was won". A win (battle result
0 or 1 at ctx+0xC) returns every stolen item; fleeing or losing keeps them gone.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

STEAL_SLOTS = 16
SNAPSHOT_CHARACTERS = 5
SNAPSHOT_BYTES_PER_CHARACTER = 8
DATA_WORDS = STEAL_SLOTS + SNAPSHOT_CHARACTERS * SNAPSHOT_BYTES_PER_CHARACTER // 4

# Steal table (16 x u8 thief, u8 pad, u16 item), then gear snapshot (5 chars x 4 halfwords)
DATA_ASM = "\n".join(["    .word 0"] * DATA_WORDS)

START_ASM = """
    ldr   r0, bs_data
    mov   r1, #0
    mov   r2, #16
clear_loop:
    str   r1, [r0], #4
    subs  r2, r2, #1
    bne   clear_loop
    ldr   r1, char_equip
    mov   r2, #5
snap_loop:
    ldr   r3, [r1]
    ldr   r12, [r1, #4]
    str   r3, [r0], #4
    str   r12, [r0], #4
    add   r1, r1, #0x5c
    subs  r2, r2, #1
    bne   snap_loop
    b     0x02054494
bs_data:
    .word ${cave_bs_data}
char_equip:
    .word 0x020B4698
"""

STEAL_ASM = """
    push  {r0-r3, lr}
    mov   r3, #0
    ldr   r0, bs_data
    mov   r2, #16
find:
    ldrh  r12, [r0, #2]
    cmp   r12, #0
    beq   found
    add   r0, r0, #4
    subs  r2, r2, #1
    bne   find
    b     done
found:
    strb  r3, [r0]
    strh  r1, [r0, #2]
done:
    pop   {r0-r3, lr}
    b     0x0206B98C
bs_data:
    .word ${cave_bs_data}
"""

END_ASM = """
    push  {r4-r10, lr}
    bl    0x02052888
    ldr   r4, char_equip
    ldr   r5, bs_snap
    mov   r6, #0
char_loop:
    mov   r7, #0
slot_loop:
    mov   r10, r7, lsl #1
    ldrh  r8, [r4, r10]
    ldrh  r9, [r5, r10]
    cmp   r8, r9
    beq   slot_next
    add   r2, r7, r7, lsl #2
    add   r2, r2, r6
    mov   r2, r2, lsl #1
    ldr   r3, break_table
    ldrh  r2, [r3, r2]
    cmp   r8, r2
    bne   slot_next
    strh  r9, [r4, r10]
    ldr   r0, inventory
    mov   r1, r8
    mvn   r2, #0
    bl    0x0206B98C
    cmp   r9, #0
    beq   slot_next
    ldr   r0, inventory
    mov   r1, r9
    mov   r2, #1
    bl    0x0206B98C
slot_next:
    add   r7, r7, #1
    cmp   r7, #4
    blt   slot_loop
    add   r4, r4, #0x5c
    add   r5, r5, #8
    add   r6, r6, #1
    cmp   r6, #5
    blt   char_loop
    ldr   r0, result
    ldrsh r0, [r0]
    cmp   r0, #1
    bhi   forget
    ldr   r4, bs_data
    mov   r5, #16
give_back:
    ldrh  r1, [r4, #2]
    cmp   r1, #0
    beq   give_next
    ldr   r0, inventory
    mov   r2, #1
    bl    0x0206B98C
give_next:
    add   r4, r4, #4
    subs  r5, r5, #1
    bne   give_back
forget:
    ldr   r0, bs_data
    mov   r1, #0
    mov   r2, #16
clear_loop:
    str   r1, [r0], #4
    subs  r2, r2, #1
    bne   clear_loop
    pop   {r4-r10, pc}
char_equip:
    .word 0x020B4698
bs_snap:
    .word ${cave_bs_data} + 0x40
break_table:
    .word 0x0209D0FC
inventory:
    .word 0x0213B930
bs_data:
    .word ${cave_bs_data}
result:
    .word 0x020B85C4
"""

BATTLE_START_HOOK = 0x02029BF0  # bl 0x02054494, battler setup
STEAL_HOOK = 0x02030F28  # bl 0x0206B98C, inventory -1 for the stolen item
BATTLE_END_HOOK = 0x0202AC54  # bl 0x02052888, every battle outcome

GEAR_AND_THEFT_RETURN = Feature(
    "gear-and-theft-return",
    (
        CaveCode("cave_bs_data", DATA_ASM, "steal table and gear snapshot"),
        CaveCode(
            "cave_bs_start", START_ASM, "battle start: clear thefts, snapshot gear"
        ),
        CaveCode("cave_bs_steal", STEAL_ASM, "record stolen item"),
        CaveCode(
            "cave_bs_end",
            END_ASM,
            "battle end: undo breaks; a win returns stolen items",
        ),
        AsmPatch(
            BATTLE_START_HOOK,
            BATTLE_START_HOOK + 4,
            0xEB00AA27,
            0xEB00AA27,
            "bl ${cave_bs_start}",
            "battle start hook",
        ),
        AsmPatch(
            STEAL_HOOK,
            STEAL_HOOK + 4,
            0xEB00EA97,
            0xEB00EA97,
            "bl ${cave_bs_steal}",
            "steal hook",
        ),
        AsmPatch(
            BATTLE_END_HOOK,
            BATTLE_END_HOOK + 4,
            0xEB009F0B,
            0xEB009F0B,
            "bl ${cave_bs_end}",
            "battle end hook",
        ),
    ),
)
