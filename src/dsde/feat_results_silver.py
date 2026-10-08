"""EXP page layout: the party member lines at the top, an empty row, then a "Silver <amount>" line.

The EXP page is built from message windows: 6 is the Althena Conduct pool (a title banner over a
box), 7..9 are one line per party member (a name box and the EXP gained). Window state lives in a
table of 14 entries (0x30 bytes each) at WINDOW_TABLE, filled with each window's fixed geometry by
func_02045ccc. func_02045a64 animates open windows every frame: it clears the old rectangle,
copies the frame tiles from a source tilemap (func_0204537c, source row picked per window id) and
calls the window's text routine (func_02045940).

The pool window is not shown any more (Althena Conduct is the game's name for EXP, and each member
line already shows its amount; the pool still counts down and is awarded as before). Window 6
becomes the Silver line instead: it takes a member line's geometry, at the left x of the first
member line, and draws the member line frame and "Silver" with the amount, both in black like the
vanilla "Althena Conduct" label so it does not read as a party member. The member lines move up
into the pool window's rows (keeping their staggered x), and the Silver line sits GAP_ROWS below
the last present member. With three members the lines end on row 16 and the Silver line fills
rows 20..23, the last row of the top screen.

Every EXP page starts by resetting windows 6..9 to their fixed geometry, so nothing carries over
between battles. All four windows open, slide, and close together as in the original. The amount
comes from the silver-drops feature (cave_silver_gained), which sets it in func_02052fb8 right
after the windows are opened and before their first draw.

Like the member lines, which show each character's total EXP counting up, the Silver line shows the
silver carried, counting up from what the party had before the battle (Jeff, 2026-10-08: a gain
counting up from 0 next to totals looked wrong). silver-drops has already added the battle's silver
to the purse when the windows open. The battle round context keeps the EXP still to pay out at
+0x148, set to twice the battle's pool (members get the doubled pool) at the same moment as the
silver, and counted down as the EXP pours; the line shows the purse minus half of what is left
(at most the silver gained), so it reaches the purse when the pour ends (or at once when A skips
it). The text routine runs every frame for an open window, so no extra hook."""

from dsde.patching import AsmPatch, CaveCode

WINDOW_TABLE = 0x020B88B4
WINDOW_SIZE = 0x30
WINDOW_ID = 0xC
WINDOW_X_FINAL = 0x10
WINDOW_Y_FINAL = 0x18
WINDOW_Y_START = 0x1C
WINDOW_WIDTH = 0x20
WINDOW_HEIGHT = 0x24
WINDOW_Y_NOW = 0x2C
SILVER_WINDOW = 6  # the vanilla Althena Conduct pool window
FIRST_MEMBER_WINDOW = 7
END_MEMBER_WINDOW = 10  # windows 7..9
FIRST_EXP_WINDOW = SILVER_WINDOW
END_EXP_WINDOW = END_MEMBER_WINDOW
LINE_ROWS = 4
POOL_ROWS = 7  # rows of the pool window (banner and box), freed for the member lines
GAP_ROWS = 3  # empty rows between the last member line and the Silver line
MEMBER_FRAME_ROW = 0x1A  # source tilemap row of the member line frame (func_0204537c)
PARTY_SLOTS = 3
BATTLERS = 0x020B8640  # pointer to the battler objects, 300 bytes each
BATTLER_SIZE = 300

WINDOW_INIT = 0x02045CCC  # (window) fixed geometry, closed
SET_WINDOW = 0x0204582C  # (window, open, timer)
MEMBER_PRESENT = 0x02031B70  # (battler) -> -1 when the slot is empty
TEXT_TARGET = 0x020455DC  # (0, 0, 0) -> tilemap the window text goes to
# (target, x, y, string, [sp] palette); the text uses BG palette 11 + palette
DRAW_STRING = 0x02045114
DRAW_NUMBER = 0x02045208  # (target, right x, y, value, [sp] palette)
ROUND_CTX_PTR = 0x020B8550  # pointer to the battle round context
POOL_LEFT = 0x148  # round context: EXP still to pay out (twice the pool)
PURSE = 0x020B4824  # u32 silver carried (features.SILVER)
BLACK_PALETTE = 0  # the vanilla "Althena Conduct" label and every EXP amount
NAME_X = 1
NUMBER_X = 0x10
TEXT_ROW = 1
# "Silver" in the game's text encoding (A-Z 0x02.., a-z 0x3A.., 0xFF ends)
SILVER_TEXT = bytes((0x14, 0x42, 0x45, 0x4F, 0x3E, 0x4B, 0xFF))

OPEN_POOL_HOOK = 0x0203B3C4  # func_0203b03c: bl func_0204582c (6, 1, -1)
OPEN_POOL_OLD = 0xEB002918
FRAME_ROW_HOOK = (
    0x0204556C  # func_0204537c: add r1, r5, sb (source row of frame row sb)
)
FRAME_ROW_OLD = 0xE0851009
POOL_TEXT_HOOK = 0x02045A1C  # func_02045940: bl func_02044390 (pool text)
POOL_TEXT_OLD = 0xEBFFFA5B

# Runs where the game opens window 6 for the EXP page (r0..r2 = 6, 1, -1, passed through).
LAYOUT_ASM = f"""
    push  {{r0, r1, r2, r4, r5, r6, r7, lr}}
    mov   r4, #{FIRST_EXP_WINDOW}
reset:
    mov   r0, r4
    bl    {WINDOW_INIT:#x}
    add   r4, r4, #1
    cmp   r4, #{END_EXP_WINDOW}
    blt   reset
    mvn   r5, #0
    mov   r6, #0
find_last:
    ldr   r0, battlers
    ldr   r0, [r0]
    mov   r1, #{BATTLER_SIZE}
    mla   r0, r6, r1, r0
    bl    {MEMBER_PRESENT:#x}
    cmp   r0, #0
    movge r5, r6
    add   r6, r6, #1
    cmp   r6, #{PARTY_SLOTS}
    blt   find_last
    ldr   r4, table
    mov   r6, #{FIRST_MEMBER_WINDOW}
move_up:
    mov   r1, #{WINDOW_SIZE}
    mla   r0, r1, r6, r4
    ldr   r1, [r0, #{WINDOW_Y_FINAL:#x}]
    sub   r1, r1, #{POOL_ROWS}
    str   r1, [r0, #{WINDOW_Y_FINAL:#x}]
    ldr   r1, [r0, #{WINDOW_Y_START:#x}]
    sub   r1, r1, #{POOL_ROWS}
    str   r1, [r0, #{WINDOW_Y_START:#x}]
    ldr   r1, [r0, #{WINDOW_Y_NOW:#x}]
    sub   r1, r1, #{POOL_ROWS}
    str   r1, [r0, #{WINDOW_Y_NOW:#x}]
    add   r6, r6, #1
    cmp   r6, #{END_MEMBER_WINDOW}
    blt   move_up
    add   r0, r4, #{FIRST_MEMBER_WINDOW * WINDOW_SIZE:#x}
    add   r1, r4, #{SILVER_WINDOW * WINDOW_SIZE:#x}
    ldr   r2, [r0, #{WINDOW_X_FINAL:#x}]
    str   r2, [r1, #{WINDOW_X_FINAL:#x}]
    ldr   r2, [r0, #{WINDOW_WIDTH:#x}]
    str   r2, [r1, #{WINDOW_WIDTH:#x}]
    ldr   r2, [r0, #{WINDOW_HEIGHT:#x}]
    str   r2, [r1, #{WINDOW_HEIGHT:#x}]
    ldr   r2, [r0, #{WINDOW_Y_FINAL:#x}]
    add   r5, r5, #1
    mov   r3, #{LINE_ROWS}
    mla   r2, r5, r3, r2
    add   r2, r2, #{GAP_ROWS}
    str   r2, [r1, #{WINDOW_Y_FINAL:#x}]
    str   r2, [r1, #{WINDOW_Y_START:#x}]
    str   r2, [r1, #{WINDOW_Y_NOW:#x}]
    pop   {{r0, r1, r2, r4, r5, r6, r7, lr}}
    b     {SET_WINDOW:#x}
battlers:
    .word {BATTLERS:#x}
table:
    .word {WINDOW_TABLE:#x}
"""

# Replaces "add r1, r5, sb" in the frame copy (r5 source row of the window, sb frame row,
# r8 window entry). Only r1 (result) and ip (rewritten right after) may change.
FRAME_ROW_ASM = f"""
    ldr   ip, [r8, #{WINDOW_ID:#x}]
    cmp   ip, #{SILVER_WINDOW}
    addne r1, r5, sb
    moveq r1, #{MEMBER_FRAME_ROW}
    addeq r1, r1, sb
    bx    lr
"""

# Window 6 text (r0 x, r1 y): "Silver" and the amount, in black.
SILVER_TEXT_ASM = f"""
    push  {{r4, r5, r6, lr}}
    sub   sp, sp, #8
    mov   r4, r0
    mov   r5, r1
    mov   r0, #0
    mov   r1, #0
    mov   r2, #0
    bl    {TEXT_TARGET:#x}
    mov   r6, r0
    mov   r3, #{BLACK_PALETTE}
    str   r3, [sp]
    ldr   r3, silver_name
    add   r1, r4, #{NAME_X}
    add   r2, r5, #{TEXT_ROW}
    bl    {DRAW_STRING:#x}
    mov   r0, #{BLACK_PALETTE}
    str   r0, [sp]
    ldr   r1, round_ctx
    ldr   r1, [r1]
    ldr   r1, [r1, #{POOL_LEFT:#x}]
    add   r1, r1, #1
    mov   r1, r1, lsr #1
    ldr   r3, silver_gained
    ldr   r3, [r3]
    cmp   r1, r3
    movhi r1, r3
    ldr   r3, purse
    ldr   r3, [r3]
    subs  r3, r3, r1
    movlt r3, #0
    mov   r0, r6
    add   r1, r4, #{NUMBER_X}
    add   r2, r5, #{TEXT_ROW}
    bl    {DRAW_NUMBER:#x}
    add   sp, sp, #8
    pop   {{r4, r5, r6, pc}}
silver_gained:
    .word ${{cave_silver_gained}}
purse:
    .word {PURSE:#x}
round_ctx:
    .word {ROUND_CTX_PTR:#x}
silver_name:
    .word ${{cave_result_silver_text}}
"""


def _hook(addr: int, old: int, cave: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, f"bl ${{{cave}}}", note)


SILVER_LINE_PATCHES: tuple[AsmPatch | CaveCode, ...] = (
    CaveCode("cave_silver_layout", LAYOUT_ASM, "EXP page layout with the silver line"),
    CaveCode(
        "cave_silver_frame_row", FRAME_ROW_ASM, "member frame for the silver line"
    ),
    CaveCode("cave_silver_text", SILVER_TEXT_ASM, "silver line text"),
    CaveCode(
        "cave_result_silver_text",
        "    .byte " + ", ".join(f"{b:#x}" for b in SILVER_TEXT),
        "Silver label",
    ),
    _hook(OPEN_POOL_HOOK, OPEN_POOL_OLD, "cave_silver_layout", "EXP page layout"),
    _hook(FRAME_ROW_HOOK, FRAME_ROW_OLD, "cave_silver_frame_row", "window frame rows"),
    _hook(POOL_TEXT_HOOK, POOL_TEXT_OLD, "cave_silver_text", "silver line text"),
)
