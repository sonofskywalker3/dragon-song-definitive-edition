"""Run from battle with the Select button instead of blowing into the microphone.

The battle command input (func_0203a34c) is the only caller of the mic-blow detector func_0206bafc
(docs/re-field-battle.md section 1): a blow makes the whole party run, and it is the game's only
way to flee. Background noise, a sneeze or a bus set it off by accident, the most common gameplay
complaint after the ones the design doc already covers (docs/research-community-feedback.md 1B).

The call is replaced by "Select newly pressed", so running needs a deliberate press on the command
screen and the mic is never consulted. Everything after it is the game's own run path: escape works
in normal battles when rand % 10 >= the number of living enemies, never in boss battles.
"""

from dsde.patching import AsmPatch, CaveCode, Feature
from dsde.targeting_consts import PAD, PAD_PRESSED

MIC_BLOW_CALL = 0x0203A880  # bl func_0206bafc in func_0203a34c
MIC_BLOW_CALL_WORD = 0xEB00C49D
KEY_SELECT = 0x04

# Replaces `bl func_0206bafc`: r0 = 1 when Select was just pressed, else 0 (keeps r4..r11)
RUN_BUTTON_ASM = f"""
    push  {{r4, lr}}
    ldr   r0, run_pad
    bl    {PAD_PRESSED:#x}
    tst   r0, #{KEY_SELECT:#x}
    movne r0, #1
    moveq r0, #0
    pop   {{r4, pc}}
run_pad:
    .word {PAD:#x}
"""

SELECT_TO_RUN = Feature(
    "select-to-run",
    (
        CaveCode("cave_run_button", RUN_BUTTON_ASM, "Select runs from battle"),
        AsmPatch(
            MIC_BLOW_CALL,
            MIC_BLOW_CALL + 4,
            MIC_BLOW_CALL_WORD,
            MIC_BLOW_CALL_WORD,
            "bl ${cave_run_button}",
            "Select runs from battle, not the microphone",
        ),
    ),
)
