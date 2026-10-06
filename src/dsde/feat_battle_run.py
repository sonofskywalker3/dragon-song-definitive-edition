"""Run from battle by holding L and R instead of blowing into the microphone.

The battle command input (func_0203a34c) is the only caller of the mic-blow detector func_0206bafc
(docs/re-field-battle.md section 1): a blow makes the whole party run, and it is the game's only
way to flee. Background noise, a sneeze or a bus set it off by accident, the most common gameplay
complaint after the ones the design doc already covers (docs/research-community-feedback.md 1B).

The call is replaced by "L and R both held for HOLD_FRAMES frames in a row" (Jeff: no single button
press), so running is always deliberate and the mic is never consulted. Everything after it is the
game's own run path: escape works in normal battles when rand % 10 >= the number of living enemies,
never in boss battles.

L and R are for running only (Jeff), so the game's hold-to-fast-forward (func_020297d4 sets the battle
speed level at 0x020B8540 every frame: L = 1, R = 2, L+R = 3; docs/re-curse-battle-speed.md 2.1) is
switched off: the two conditional stores become no-ops and the level stays 0. Battle pacing is to be
fixed by default instead (docs/re-battle-pacing.md).
"""

from dsde.patching import ARM_NOP, AsmPatch, CaveCode, Feature, Patch
from dsde.targeting_consts import PAD

MIC_BLOW_CALL = 0x0203A880  # bl func_0206bafc in func_0203a34c
MIC_BLOW_CALL_WORD = 0xEB00C49D
PAD_HELD = 0x0C  # u16 in the pad struct: keys held down this frame
KEYS_RUN = 0x300  # L (0x200) and R (0x100)
HOLD_FRAMES = 30  # half a second
FAST_FORWARD_STORES = (  # func_020297d4: strne of the speed level for L, then R
    (0x0202980C, 0x15810000),
    (0x02029820, 0x15801000),
)

HOLD_STATE_ASM = """
    .word 0
"""

# Replaces `bl func_0206bafc`: r0 = 1 once L and R have been held together for HOLD_FRAMES frames
# in a row (the count restarts whenever either is let go), else 0. Keeps r4..r11.
RUN_BUTTON_ASM = f"""
    ldr   r1, run_pad
    ldrh  r1, [r1, #{PAD_HELD:#x}]
    ldr   r2, run_count
    and   r1, r1, #{KEYS_RUN:#x}
    cmp   r1, #{KEYS_RUN:#x}
    ldreq r0, [r2]
    addeq r0, r0, #1
    movne r0, #0
    str   r0, [r2]
    cmp   r0, #{HOLD_FRAMES}
    movge r0, #0
    strge r0, [r2]
    movge r0, #1
    movlt r0, #0
    bx    lr
run_pad:
    .word {PAD:#x}
run_count:
    .word ${{cave_run_hold}}
"""

HOLD_LR_TO_RUN = Feature(
    "hold-lr-to-run",
    (
        CaveCode("cave_run_hold", HOLD_STATE_ASM, "frames L and R have been held"),
        CaveCode("cave_run_button", RUN_BUTTON_ASM, "holding L and R runs from battle"),
        AsmPatch(
            MIC_BLOW_CALL,
            MIC_BLOW_CALL + 4,
            MIC_BLOW_CALL_WORD,
            MIC_BLOW_CALL_WORD,
            "bl ${cave_run_button}",
            "holding L and R runs from battle, not the microphone",
        ),
        *(
            Patch(addr, old, ARM_NOP, "L and R no longer fast-forward battles")
            for addr, old in FAST_FORWARD_STORES
        ),
    ),
)
