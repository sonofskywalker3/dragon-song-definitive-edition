"""Result screens: the EXP page shows the silver won, and a second page lists the dropped items.

Design sections 2 and 3. All battles now use the EXP (Virtue) result flow, whose screen shows only
Althena Conduct: windows 6 (the pool) and 7..9 (one per party member). feat_results_silver adds a
"Silver" line below the last member. The vanilla item list (window 5 plus item icons) is built by
the same setup routine, func_0203b03c, only when the battle mode at ctx+8 is not an EXP mode, and
the two layouts share the top of the top screen.

Victory flow (func_020297d4 case 10, substate at ctx+0x10): 0 builds the screen, 1 waits for the
victory poses, 2 and 3 pour EXP and show level-ups, 0x28 (or 0x32) moves to 99, and 99 calls
func_0203a34c every frame until the player presses A, which ends the battle.

The hook replaces that call in the 99 handler. When A ends the EXP page and items dropped, it
closes windows 6..9 and waits in substate CLOSING_PAGE until their close animation ends (opening
the item window earlier lets the closing windows erase parts of it). Then it reruns func_0203b03c
with the mode briefly set to 0 so it builds the item page instead, and moves to substate
ITEM_PAGE, which the game handles exactly like 99 (wait for A, then leave). With no items, A leaves
the battle as in the original game. Boss battles (mode -1) take the same path, since boss-exp
gives them the EXP page.

The silver amount comes from the silver-drops feature (cave_silver_gained), so result-screens
needs silver-drops."""

from dsde.feat_results_silver import (
    END_EXP_WINDOW,
    FIRST_EXP_WINDOW,
    SET_WINDOW,
    SILVER_LINE_PATCHES,
)
from dsde.patching import AsmPatch, CaveCode, Feature

BATTLE_CTX = 0x020B85B8
MODE_OFFSET = 0x8
SUBSTATE_OFFSET = 0x10
DROPS_OFFSET = 0x48  # 4 slots of (s16 item, s16 count)
DROP_SLOTS = 4
DROP_SLOT_SHIFT = 2  # 4 bytes per slot
EXP_PAGE = 99  # vanilla "wait for A, then leave"
# Values above 0x28 other than 0x32 take the same default branch as 99
CLOSING_PAGE = 97  # EXP windows closing; the item page opens once they are gone
ITEM_PAGE = 98
ITEM_MODE = 0  # a non-EXP battle mode: func_0203b03c builds the item list
WINDOW_CLOSE = 0
WINDOW_NO_TIMER = -1
WINDOW_CLOSING = 0  # func_020457cc result while the close animation runs

RESULT_INPUT = 0x0203A34C  # result screen input; nonzero when A leaves the screen
RESULT_SETUP = 0x0203B03C
RESULT_PROMPT = 0x0203B018  # called by the game when it enters substate 99
WINDOW_STATE = 0x020457CC  # (window) -> 1 opening, 0 closing, 2 open, -1 closed
INPUT_HOOK = 0x0202AB44
INPUT_HOOK_OLD = 0xEB003E00  # bl func_0203a34c

INPUT_ASM = f"""
    push  {{r4, r5, r6, lr}}
    bl    {RESULT_INPUT:#x}
    ldr   r4, ctx
    ldrsh r1, [r4, #{SUBSTATE_OFFSET:#x}]
    cmp   r1, #{CLOSING_PAGE}
    beq   closing
    cmp   r0, #0
    beq   done
    cmp   r1, #{EXP_PAGE}
    bne   done
    mov   r2, #0
check:
    add   r3, r4, r2, lsl #{DROP_SLOT_SHIFT}
    ldrsh r3, [r3, #{DROPS_OFFSET:#x}]
    cmp   r3, #0
    bgt   show
    add   r2, r2, #1
    cmp   r2, #{DROP_SLOTS}
    blt   check
    b     done
show:
    mov   r0, #{CLOSING_PAGE}
    strh  r0, [r4, #{SUBSTATE_OFFSET:#x}]
    mov   r5, #{FIRST_EXP_WINDOW}
close:
    mov   r0, r5
    mov   r1, #{WINDOW_CLOSE}
    mvn   r2, #{~WINDOW_NO_TIMER}
    bl    {SET_WINDOW:#x}
    add   r5, r5, #1
    cmp   r5, #{END_EXP_WINDOW}
    blt   close
    mov   r0, #0
    b     done
closing:
    mov   r5, #{FIRST_EXP_WINDOW}
wait_closed:
    mov   r0, r5
    bl    {WINDOW_STATE:#x}
    cmp   r0, #{WINDOW_CLOSING}
    moveq r0, #0
    beq   done
    add   r5, r5, #1
    cmp   r5, #{END_EXP_WINDOW}
    blt   wait_closed
    mov   r0, #{ITEM_PAGE}
    strh  r0, [r4, #{SUBSTATE_OFFSET:#x}]
    ldrh  r6, [r4, #{MODE_OFFSET:#x}]
    mov   r0, #{ITEM_MODE}
    strh  r0, [r4, #{MODE_OFFSET:#x}]
    bl    {RESULT_SETUP:#x}
    strh  r6, [r4, #{MODE_OFFSET:#x}]
    bl    {RESULT_PROMPT:#x}
    mov   r0, #0
done:
    pop   {{r4, r5, r6, pc}}
ctx:
    .word {BATTLE_CTX:#x}
"""

RESULT_SCREENS = Feature(
    "result-screens",
    (
        CaveCode(
            "cave_result_input",
            INPUT_ASM,
            "EXP page, then the item page if items dropped",
        ),
        AsmPatch(
            INPUT_HOOK,
            INPUT_HOOK + 4,
            INPUT_HOOK_OLD,
            INPUT_HOOK_OLD,
            "bl ${cave_result_input}",
            "A on the EXP page opens the item page",
        ),
        *SILVER_LINE_PATCHES,
    ),
)
