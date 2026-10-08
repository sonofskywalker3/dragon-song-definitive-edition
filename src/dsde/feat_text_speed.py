"""Dialogue types faster while A or B is held; holding B also turns the pages (Jeff, 2026-10-07).

The message op (handler func_02040910) calls MSG_UPDATE(window) once a frame. While the page types, each call
counts the window's delay (+0x38 against +0x36) and draws the next character when it is due; at the end of a
page (byte FE) PAGE_WAIT (+0x2E) turns nonzero and the page waits for a new press of A (pad +6 bit 0) or a
touch, with the arrow blinking on BLINK (+0x2F, counting the waiting frames).

Here, in the message op only (shops and the hub menus call MSG_UPDATE themselves and are untouched):
- With A or B held the update runs up to FAST times a frame, so the text types (and scrolls) three times as
  fast. It stops early once the page waits, so the A check still runs once a frame: holding A never turns a
  page, A has to be let go and pressed again, as in vanilla.
- With B held, once a page has waited B_HOLD frames, its update runs with A added to this frame's new keys, so
  the page turns exactly as a press of A would turn it.
The opening's asides check (feat_opening_asides.py) runs first, as before.
"""

from dsde.patching import AsmPatch, CaveCode, Feature
from dsde.targeting_consts import PAD

MSG_UPDATE_CALL = 0x02040B54  # bl func_0203b81c in the message op's wait state
MSG_UPDATE_CALL_WORD = 0xEB_FFEB30
MSG_UPDATE = 0x0203B81C
PAD_NEW = 0x06  # u16 in the pad struct: keys newly pressed this frame
PAD_HELD = 0x0C  # u16 in the pad struct: keys held down this frame
KEY_A = 0x1
KEY_B = 0x2
FAST = 3  # window updates a frame while A or B is held
PAGE_WAIT = 0x2E  # byte in the window: nonzero at the end of a page
BLINK = 0x2F  # byte in the window: frames the page has waited (the arrow's blink, 0 at the page end)
B_HOLD = 8  # frames a finished page stays up before held B turns it

TEXT_SPEED_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r4, r0
    bl    ${{cave_aside_autoclose}}
    ldr   r6, ts_pad
    ldrh  r1, [r6, #{PAD_HELD:#x}]
    mov   r5, #1
    tst   r1, #{KEY_A | KEY_B:#x}
    movne r5, #{FAST}
    tst   r1, #{KEY_B:#x}
    beq   ts_loop
    ldrb  r2, [r4, #{PAGE_WAIT:#x}]
    cmp   r2, #0
    beq   ts_loop
    ldrb  r2, [r4, #{BLINK:#x}]
    cmp   r2, #{B_HOLD}
    blt   ts_loop
    ldrh  r5, [r6, #{PAD_NEW:#x}]
    orr   r1, r5, #{KEY_A:#x}
    strh  r1, [r6, #{PAD_NEW:#x}]
    mov   r0, r4
    bl    {MSG_UPDATE:#x}
    strh  r5, [r6, #{PAD_NEW:#x}]
    pop   {{r4-r6, pc}}
ts_loop:
    mov   r0, r4
    bl    {MSG_UPDATE:#x}
    subs  r5, r5, #1
    popeq {{r4-r6, pc}}
    cmp   r0, #0
    popeq {{r4-r6, pc}}
    ldrb  r1, [r4, #{PAGE_WAIT:#x}]
    cmp   r1, #0
    popne {{r4-r6, pc}}
    b     ts_loop
ts_pad:
    .word {PAD:#x}
"""

TEXT_SPEED = Feature(
    "text-speed",
    (
        CaveCode(
            "cave_text_speed", TEXT_SPEED_ASM, "held A/B types fast, held B turns pages"
        ),
        AsmPatch(
            MSG_UPDATE_CALL,
            MSG_UPDATE_CALL + 4,
            MSG_UPDATE_CALL_WORD,
            MSG_UPDATE_CALL_WORD,
            "bl ${cave_text_speed}",
            "dialogue: held A/B types fast, held B turns pages",
        ),
    ),
)
