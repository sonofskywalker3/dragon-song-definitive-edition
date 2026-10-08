"""Faster field movement (playtest feedback 6): walking 1.5 times and running 3 times vanilla walking.

func_02024b34 moves the player by the unit direction vector (0x1000 = 1 pixel, 20.12) once per frame, and a
second time in the same frame while running (the run flag at [sp, #8], set by `timed-run`). Each step loads the
vector at two places: the normal step, and the slide along a wall when the normal step is blocked. Both loads
now go through a cave that scales the vector by 1.5, walking or running, so a running frame's two steps
make 3 (Jeff, 2026-10-07: walking 1.25 made running feel little better). Scripted walks use the route path
(func_02024b34 state 1) and are unchanged.

No slowdown on ramps (Jeff, 2026-10-08). Standing in a slope region of the map (type 1 in the region list at
*0x020B6C24, found by func_0201d438) set the step's speed index to 1, which scales the step by 0.65 from the
table at 0x0209E034 on a separate path that also missed the x1.5 above: walking dropped from 1.5 to 0.65 pixels a
frame. The index now stays 0 on slopes, so ramps move like flat ground; diagonal input is still turned along the
slope. Type-3 regions and the special tile on maps 0x35..0x39 (both 0.6) and scripted routes keep their speeds.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

WALK_STEP_LOAD = 0x02024F80  # ldrsh r1, [r0, r1]: y of the step (x already in r3)
WALK_STEP_LOAD_WORD = 0xE19010F1
WALK_SLIDE_LOAD = 0x02025070  # ldrsh r2, [r0, r2]: y of the slide step (x in r3)
WALK_SLIDE_LOAD_WORD = 0xE19020F2
STEP_SHIFT = 1  # step += step >> 1: 1.5 times as fast
SLOPE_SPEED_INDEX = 0x02024D88  # mov r6, r5 (r5 = 1): slope regions use speed table entry 1 (0.65)
SLOPE_SPEED_INDEX_WORD = 0xE1A06005

WALK_SPEED = Feature(
    "walk-speed",
    (
        CaveCode(
            "cave_walk_step",
            f"""
    ldrsh r1, [r0, r1]
    add   r1, r1, r1, asr #{STEP_SHIFT}
    add   r3, r3, r3, asr #{STEP_SHIFT}
    bx    lr
""",
            "field step x1.5",
        ),
        CaveCode(
            "cave_walk_slide",
            f"""
    ldrsh r2, [r0, r2]
    add   r2, r2, r2, asr #{STEP_SHIFT}
    add   r3, r3, r3, asr #{STEP_SHIFT}
    bx    lr
""",
            "field slide step x1.5",
        ),
        AsmPatch(
            WALK_STEP_LOAD,
            WALK_STEP_LOAD + 4,
            WALK_STEP_LOAD_WORD,
            WALK_STEP_LOAD_WORD,
            "bl ${cave_walk_step}",
            "field step x1.5",
        ),
        AsmPatch(
            WALK_SLIDE_LOAD,
            WALK_SLIDE_LOAD + 4,
            WALK_SLIDE_LOAD_WORD,
            WALK_SLIDE_LOAD_WORD,
            "bl ${cave_walk_slide}",
            "field slide step x1.5",
        ),
        AsmPatch(
            SLOPE_SPEED_INDEX,
            SLOPE_SPEED_INDEX + 4,
            SLOPE_SPEED_INDEX_WORD,
            SLOPE_SPEED_INDEX_WORD,
            "mov r6, #0",
            "no slowdown on ramps",
        ),
    ),
)
