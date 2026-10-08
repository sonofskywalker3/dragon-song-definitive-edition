"""Field bottom screen (HUD): the Menu note, the leader portrait, and the party chat figures hold still.

The "bounce" is a scale pulse on affine matrix 5 shared by those three buttons: func_0206f7c4, called
every field frame, adds 0x800 to the phase at F+0xC4 and scales the matrix by 1 + sin(phase) / 8
(docs/re-field-hud.md section 2). Keeping the phase at 0 keeps the scale at 1, so all three stand
still; their touch areas are separate and keep working (Jeff, 2026-10-08: no icon should keep drawing
the eye; the party chat figures may later bounce only for a new message).
"""

from dsde.patching import AsmPatch, Feature

PULSE_STEP = 0x0206F7E0  # func_0206f7c4: add ip, ip, #0x800 (phase step)
PULSE_STEP_WORD = 0xE28CCB02

STILL_HUD = Feature(
    "still-hud",
    (
        AsmPatch(
            PULSE_STEP,
            PULSE_STEP + 4,
            PULSE_STEP_WORD,
            PULSE_STEP_WORD,
            "mov ip, #0",
            "HUD pulse phase stays 0",
        ),
    ),
)
