"""Opening run: Jian's asides close by themselves when his walk ends (see feat_opening.py)."""

from dsde.patching import CaveCode

# Jian's asides close by themselves when his walk ends (Jeff, 2026-10-07: the walks are timed to the text).
# The message op (handler func_02040910) waits each frame on MSG_UPDATE(window) until it returns 0; at the end
# of a page the window's +0x2E is 1 (arrow shown) until A clears it, then the message's end closes the box.
# While the run flag is set and the player's route is done, a waiting page is cleared as A would, so the box
# closes. Text still typing finishes first; every other message is untouched. The check runs first in the
# message op's window update (feat_text_speed.py owns that call); it only touches r1.
MSG_PAGE_WAIT = (
    0x2E  # byte in the message window: 1 at the end of a page, waiting for A
)
PAGE_WAITING = 1
SCRIPT_CONTEXT_PTR = 0x020B4640  # flag bits at the start of the main script context
RUN_FLAG = 0x1DF  # feat_opening.RUN_FLAG: set while the scripted run is on
RUN_FLAG_WORD = (RUN_FLAG >> 5) * 4
RUN_FLAG_BIT = 1 << (RUN_FLAG & 31)
PLAYER_ROUTE = 0x020B6CEC  # the player's route pointer, 0 once the route is done

AUTO_CLOSE_ASM = f"""
    ldr   r1, ac_context
    ldr   r1, [r1]
    ldr   r1, [r1, #{RUN_FLAG_WORD:#x}]
    tst   r1, #{RUN_FLAG_BIT:#x}
    bxeq  lr
    ldr   r1, ac_route
    ldr   r1, [r1]
    cmp   r1, #0
    bxne  lr
    ldrb  r1, [r0, #{MSG_PAGE_WAIT:#x}]
    cmp   r1, #{PAGE_WAITING}
    moveq r1, #0
    strbeq r1, [r0, #{MSG_PAGE_WAIT:#x}]
    bx    lr
ac_context:
    .word {SCRIPT_CONTEXT_PTR:#x}
ac_route:
    .word {PLAYER_ROUTE:#x}
"""

ASIDE_AUTOCLOSE = (
    CaveCode("cave_aside_autoclose", AUTO_CLOSE_ASM, "asides close as the walk ends"),
)
