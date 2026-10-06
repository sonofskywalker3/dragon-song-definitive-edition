"""A character who leaves the party leaves their equipment behind.

Story scripts remove characters with op 0x1C (party_leave, handler func_02040238), which only takes
them out of the party slots: whatever they wear stays on them, often for good (Lucia in script 016,
Flora in 019) or until gear found meanwhile has outclassed it (Gabryel in 009 and 019, Rufus in
021). Jeff: every leave should leave the gear, since it may still be useful in the short term.

The inventory count already includes equipped items (docs/re-enemies.md section 5), and field
character records hold level stats only (gear bonuses are added when the battle copy is built,
func_0206b030), so dropping gear is just emptying the five slots (weapon, body, arm, head, accessory
at record + 0x3C; 0 is empty). The op table entry for 0x1C points at a wrapper that does this for a
character who is in the party, then runs the game's handler. It skips the intro's setup leaves
(script 026 removes Lucia, Gabryel, Flora and Rufus before the game starts) by acting only once story
flag 0x1 is set, which Jian's wake-up scene sets right after the intro.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

OP_TABLE = 0x020A3EE8  # script op handlers, {handler, yield} per op
OP_PARTY_LEAVE = 0x1C
PARTY_LEAVE = 0x02040238
LEAVE_ENTRY = OP_TABLE + OP_PARTY_LEAVE * 8

SCRIPT_PC = 0xE0  # script context: address of the current op
OP_ARG = 2  # party_leave: s16 character id
STORY_FLAGS = 0x00  # script context: flag bit array
FLAG_AFTER_INTRO = 1  # set by the wake-up scene (script 001)
PARTY_SLOTS = 0x020B464C  # 3 x {s16 character, s16}, -1 empty
PARTY_SLOT_COUNT = 3
PARTY_SLOT_SIZE = 4
CHARACTERS = 0x020B465C  # character records, CHARACTER_SIZE each, in id order
CHARACTER_SIZE = 0x5C
EQUIPMENT = 0x3C  # five u16 slots
EQUIPMENT_SLOTS = 5
LAST_CHARACTER = 4

# Op 0x1C handler: r0 = script context. Empties the leaving character's equipment when they are in
# the party and the intro is over, then tail-calls the game's handler with r0 intact.
LEAVE_ASM = f"""
    push  {{r0, r4, r5, lr}}
    ldr   r1, [r0, #{STORY_FLAGS:#x}]
    tst   r1, #{1 << FLAG_AFTER_INTRO:#x}
    beq   leave_done
    ldr   r1, [r0, #{SCRIPT_PC:#x}]
    ldrsh r4, [r1, #{OP_ARG}]
    cmp   r4, #0
    blt   leave_done
    cmp   r4, #{LAST_CHARACTER}
    bgt   leave_done
    ldr   r1, leave_party
    mov   r2, #{PARTY_SLOT_COUNT}
leave_find:
    ldrsh r3, [r1], #{PARTY_SLOT_SIZE}
    cmp   r3, r4
    beq   leave_drop
    subs  r2, r2, #1
    bne   leave_find
    b     leave_done
leave_drop:
    ldr   r1, leave_records
    mov   r2, #{CHARACTER_SIZE:#x}
    mla   r1, r4, r2, r1
    add   r1, r1, #{EQUIPMENT:#x}
    mov   r2, #0
    mov   r3, #{EQUIPMENT_SLOTS}
leave_clear:
    strh  r2, [r1], #2
    subs  r3, r3, #1
    bne   leave_clear
leave_done:
    pop   {{r0, r4, r5, lr}}
    b     {PARTY_LEAVE:#x}
leave_party:
    .word {PARTY_SLOTS:#x}
leave_records:
    .word {CHARACTERS:#x}
"""

LEAVE_DROPS_GEAR = Feature(
    "leave-drops-gear",
    (
        CaveCode("cave_leave_gear", LEAVE_ASM, "a leaving character leaves their gear"),
        AsmPatch(
            LEAVE_ENTRY,
            LEAVE_ENTRY + 4,
            PARTY_LEAVE,
            PARTY_LEAVE,
            ".word ${cave_leave_gear}",
            "party_leave goes through the gear wrapper",
        ),
    ),
)
