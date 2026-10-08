"""Healing statues answer A from any side (Jeff, 2026-10-08: "You can't activate a statue from the sides or back").

The field's A-button object search (func_0201e6a0, 0x0201F2A4) runs two checks before a statue (talk object,
kind 1, id 0x37D) heals:

1. The shared reach check func_020260f4 for every talk object and chest: the point 8 pixels ahead of Jian must
   be within 15 pixels of the object on both axes, and Jian must face it (the octant of the direction to it
   within one of his facing). A statue's footprint is bigger than a person's: beside it or behind it Jian
   stops 18 to 26 pixels from its centre, out of reach.
2. A statue-only facing rule (0x0201F300..0x0201F348): unless the statue's +0x15 byte is 0xFF, Jian's facing
   must be within one step of up-right (up, up-right or right), or of up-left when the statue's own facing
   (+0x17 low bits) is 2. The statues in Thieves' Woods, Delrich Temple, map 19, and Roland Forest have 0 or
   0x10 there (only Fountain Square's has 0xFF). With both checks, vanilla heals only from below the statue
   facing up or from its lower corner facing up-right (statue facing 6) or up-left (facing 2).

Statues now skip both: the reach check call goes through a cave that, for a statue only, accepts Jian within
30 pixels of its centre when his facing points at it (within 67.5 degrees of the direction to it, using the
game's own facing vectors, where the diagonals are the 2:1 field diagonals). Every other object still takes
the shared check unchanged. The statue facing rule's branch is gone. Research: docs/re-field-battle.md 2.11.
"""

from dsde.patching import ARM_NOP, AsmPatch, CaveCode, Feature, Patch

# bl func_020260f4 (r0 = Jian, r1 = the object) in the A-button object search
OBJECT_REACH_CALL = 0x0201F2C0
OBJECT_REACH_CALL_WORD = 0xEB001B8B
# The shared reach and facing check: returns 1 when the object answers A
OBJECT_REACH_CHECK = 0x020260F4
# bgt: Jian's facing more than one step from the side the statue allows
STATUE_FACING_BRANCH = 0x0201F348
STATUE_FACING_BRANCH_WORD = 0xCA00006A
TALK_KIND = 1  # object +0x14
STATUE_ID = 0x37D  # object +0x12
STATUE_ID_HIGH = 0x300  # STATUE_ID split into two ARM immediates
STATUE_ID_LOW = STATUE_ID - STATUE_ID_HIGH
STATUE_REACH = 30  # pixels from Jian to the statue's centre
# Facing accepted when cos^2 >= 1 / (2^3 - 1) = 1/7, within about 67.5 degrees of the direction to the statue:
# dot^2 * 7 >= distance^2 * 256^2, with dot = (statue - Jian) . facing vector.
COS_SQUARED_SHIFT = 3
UNIT_SQUARED_SHIFT = 16  # facing vectors below are 8.8 fixed point
FACING_MASK = 7  # Jian +0x17 low bits
# The game's facing vectors (0x020A7878 / 0x020A7874 by the index table at 0x0208D9B4), Q12 >> 4:
# up, up-right, right, down-right, down, down-left, left, up-left; y grows downwards.
FACING_VECTORS = (
    (0, -256),
    (229, -114),
    (256, 0),
    (229, 114),
    (0, 256),
    (-229, 114),
    (-256, 0),
    (-229, -114),
)
FIXED_SHIFT = 12  # positions are 20.12

_VECTOR_WORDS = "\n".join(f"    .short {x}, {y}" for x, y in FACING_VECTORS)

STATUE_ANY_SIDE = Feature(
    "statue-any-side",
    (
        CaveCode(
            "cave_statue_reach",
            f"""
    ldrb  r2, [r1, #0x14]
    cmp   r2, #{TALK_KIND}
    bne   {OBJECT_REACH_CHECK:#x}
    ldrsh r2, [r1, #0x12]
    mov   r3, #{STATUE_ID_HIGH:#x}
    add   r3, r3, #{STATUE_ID_LOW:#x}
    cmp   r2, r3
    bne   {OBJECT_REACH_CHECK:#x}
    push  {{r4, r5, lr}}
    ldr   r2, [r1, #4]
    ldr   r3, [r0, #4]
    sub   r2, r2, r3
    mov   r2, r2, asr #{FIXED_SHIFT}
    ldr   r3, [r1, #8]
    ldr   r12, [r0, #8]
    sub   r3, r3, r12
    mov   r3, r3, asr #{FIXED_SHIFT}
    mul   r4, r2, r2
    mla   r4, r3, r3, r4
    cmp   r4, #{STATUE_REACH * STATUE_REACH}
    bhi   statue_no
    ldrb  r12, [r0, #0x17]
    and   r12, r12, #{FACING_MASK}
    adr   r5, statue_vectors
    add   r5, r5, r12, lsl #2
    ldrsh r12, [r5]
    ldrsh r5, [r5, #2]
    mul   r12, r2, r12
    mla   r12, r3, r5, r12
    cmp   r12, #0
    ble   statue_no
    mul   r5, r12, r12
    rsb   r5, r5, r5, lsl #{COS_SQUARED_SHIFT}
    mov   r4, r4, lsl #{UNIT_SQUARED_SHIFT}
    cmp   r5, r4
    movhs r0, #1
    movlo r0, #0
    pop   {{r4, r5, pc}}
statue_no:
    mov   r0, #0
    pop   {{r4, r5, pc}}
statue_vectors:
{_VECTOR_WORDS}
""",
            "statue reach: any side Jian faces it from",
        ),
        AsmPatch(
            OBJECT_REACH_CALL,
            OBJECT_REACH_CALL + 4,
            OBJECT_REACH_CALL_WORD,
            OBJECT_REACH_CALL_WORD,
            "bl ${cave_statue_reach}",
            "A-button object search: statues use their own reach",
        ),
        Patch(
            STATUE_FACING_BRANCH,
            STATUE_FACING_BRANCH_WORD,
            ARM_NOP,
            "statue heals whichever way Jian faces it",
        ),
    ),
)
