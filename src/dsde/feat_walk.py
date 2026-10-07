"""Faster field movement (playtest feedback 6): walking 1.5 times and running 3 times vanilla walking.

func_02024b34 moves the player by the unit direction vector (0x1000 = 1 pixel, 20.12) once per frame, and a
second time in the same frame while running (the run flag at [sp, #8], set by `timed-run`). Each step loads the
vector at two places: the normal step, and the slide along a wall when the normal step is blocked. Both loads
now go through a cave that scales the vector by 1.5, walking or running, so a running frame's two steps
make 3 (Jeff, 2026-10-07: walking 1.25 made running feel little better). Scripted walks use the route path
(func_02024b34 state 1) and are unchanged.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

WALK_STEP_LOAD = 0x02024F80  # ldrsh r1, [r0, r1]: y of the step (x already in r3)
WALK_STEP_LOAD_WORD = 0xE19010F1
WALK_SLIDE_LOAD = 0x02025070  # ldrsh r2, [r0, r2]: y of the slide step (x in r3)
WALK_SLIDE_LOAD_WORD = 0xE19020F2
STEP_SHIFT = 1  # step += step >> 1: 1.5 times as fast

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
    ),
)
