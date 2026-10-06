"""EXP page silver line: "Silver <amount>" styled like a party member line, below the last one.

The EXP page is built from message windows: 6 is the Althena Conduct pool (a title banner over a
box), 7..9 are one line per party member (a name box and the EXP gained). Window state lives in a
table of 14 entries (0x30 bytes each) at WINDOW_TABLE, filled with each window's fixed geometry by
func_02045ccc. func_02045a64 animates open windows every frame: it clears the old rectangle,
copies the frame tiles from a source tilemap (func_0204537c, source row picked per window id) and
calls the window's text routine (func_02045940, func_0204429c for 7..9).

The silver line rides on the last member's window: its height grows from 4 to 8 rows, the frame
copy repeats the member frame for rows 4..7, and the text routine draws "Silver" and the amount
four rows below the member. Clearing, sliding and closing then cover the extra line for free.

The top screen is full with three members (HUD 0..4, pool 5..11, members 12..23), so with the
third slot filled the pool window drops its title banner (the box below it also reads Althena
Conduct) and the member lines move up three rows. The silver line then starts on row 21 and its
last frame row (the box's 3 pixel bottom edge) falls off the screen; the game's frame copy skips
rows past the bottom, and the text rows stay on screen.

Every EXP page starts by resetting windows 6..9 to their fixed geometry, so nothing carries over
between battles. The amount comes from the silver-drops feature (cave_silver_gained), which sets
it in func_02052fb8 right after the windows are opened and before their first draw."""

from dsde.patching import AsmPatch, CaveCode

WINDOW_TABLE = 0x020B88B4
WINDOW_SIZE = 0x30
WINDOW_ID = 0xC
WINDOW_Y_FINAL = 0x18
WINDOW_Y_START = 0x1C
WINDOW_HEIGHT = 0x24
WINDOW_Y_NOW = 0x2C
POOL_WINDOW = 6
FIRST_MEMBER_WINDOW = 7
END_MEMBER_WINDOW = 10  # windows 7..9
FIRST_EXP_WINDOW = POOL_WINDOW
END_EXP_WINDOW = END_MEMBER_WINDOW
LINE_ROWS = 4
RIDER_HEIGHT = 2 * LINE_ROWS  # member line plus the silver line
LINE_ROW_MASK = LINE_ROWS - 1
BANNER_ROWS = 3  # pool window rows 0..2 are the title banner, 3..6 the box
POOL_BOX_ROWS = 4
PARTY_SLOTS = 3
LAST_SLOT = PARTY_SLOTS - 1  # with this slot filled the lines move up BANNER_ROWS
BATTLERS = 0x020B8640  # pointer to the battler objects, 300 bytes each
BATTLER_SIZE = 300

WINDOW_INIT = 0x02045CCC  # (window) fixed geometry, closed
SET_WINDOW = 0x0204582C  # (window, open, timer)
MEMBER_PRESENT = 0x02031B70  # (battler) -> -1 when the slot is empty
DRAW_MEMBER = 0x0204429C  # (x, y, slot) name and EXP gained
DRAW_POOL = 0x02044390  # (x, y) "Althena Conduct" and the pool, 4 rows below y
TEXT_TARGET = 0x020455DC  # (0, 0, 0) -> tilemap the window text goes to
DRAW_STRING = 0x02045114  # (target, x, y, string, [sp] palette)
DRAW_NUMBER = 0x02045208  # (target, right x, y, value, [sp] 0)
NAME_PALETTE = 4  # living party member names
NUMBER_PALETTE = 0
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
POOL_TEXT_HOOK = 0x02045A1C  # func_02045940: bl func_02044390
POOL_TEXT_OLD = 0xEBFFFA5B
MEMBER_TEXT_HOOK = 0x02045A38  # func_02045940: bl func_0204429c
MEMBER_TEXT_OLD = 0xEBFFFA17

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
    cmp   r5, #0
    blt   open
    ldr   r4, table
    mov   r1, #{WINDOW_SIZE}
    add   r0, r5, #{FIRST_MEMBER_WINDOW}
    mla   r0, r1, r0, r4
    mov   r1, #{RIDER_HEIGHT}
    str   r1, [r0, #{WINDOW_HEIGHT:#x}]
    cmp   r5, #{LAST_SLOT}
    bne   open
    add   r0, r4, #{POOL_WINDOW * WINDOW_SIZE:#x}
    mov   r1, #{POOL_BOX_ROWS}
    str   r1, [r0, #{WINDOW_HEIGHT:#x}]
    mov   r6, #{FIRST_MEMBER_WINDOW}
move_up:
    mov   r1, #{WINDOW_SIZE}
    mla   r0, r1, r6, r4
    ldr   r1, [r0, #{WINDOW_Y_FINAL:#x}]
    sub   r1, r1, #{BANNER_ROWS}
    str   r1, [r0, #{WINDOW_Y_FINAL:#x}]
    ldr   r1, [r0, #{WINDOW_Y_START:#x}]
    sub   r1, r1, #{BANNER_ROWS}
    str   r1, [r0, #{WINDOW_Y_START:#x}]
    ldr   r1, [r0, #{WINDOW_Y_NOW:#x}]
    sub   r1, r1, #{BANNER_ROWS}
    str   r1, [r0, #{WINDOW_Y_NOW:#x}]
    add   r6, r6, #1
    cmp   r6, #{END_MEMBER_WINDOW}
    blt   move_up
open:
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
    cmp   ip, #{FIRST_MEMBER_WINDOW}
    blt   pool
    cmp   ip, #{END_MEMBER_WINDOW}
    bge   plain
    and   ip, sb, #{LINE_ROW_MASK}
    add   r1, r5, ip
    bx    lr
pool:
    cmp   ip, #{POOL_WINDOW}
    bne   plain
    ldr   ip, [r8, #{WINDOW_HEIGHT:#x}]
    cmp   ip, #{POOL_BOX_ROWS}
    bne   plain
    add   r1, r5, sb
    add   r1, r1, #{BANNER_ROWS}
    bx    lr
plain:
    add   r1, r5, sb
    bx    lr
"""

# Pool text: without the banner the box starts BANNER_ROWS higher in the window.
POOL_TEXT_ASM = f"""
    ldr   ip, pool_height
    ldr   ip, [ip]
    cmp   ip, #{POOL_BOX_ROWS}
    subeq r1, r1, #{BANNER_ROWS}
    b     {DRAW_POOL:#x}
pool_height:
    .word {WINDOW_TABLE + POOL_WINDOW * WINDOW_SIZE + WINDOW_HEIGHT:#x}
"""

# Member text (r0 x, r1 y, r2 slot); the window carrying the silver line also draws it.
MEMBER_TEXT_ASM = f"""
    push  {{r4, r5, r6, r7, lr}}
    sub   sp, sp, #4
    mov   r4, r0
    mov   r5, r1
    mov   r6, r2
    bl    {DRAW_MEMBER:#x}
    ldr   r0, table
    add   r1, r6, #{FIRST_MEMBER_WINDOW}
    mov   r2, #{WINDOW_SIZE}
    mla   r0, r1, r2, r0
    ldr   r0, [r0, #{WINDOW_HEIGHT:#x}]
    cmp   r0, #{RIDER_HEIGHT}
    bne   out
    mov   r0, #0
    mov   r1, #0
    mov   r2, #0
    bl    {TEXT_TARGET:#x}
    mov   r7, r0
    mov   r3, #{NAME_PALETTE}
    str   r3, [sp]
    ldr   r3, silver_name
    add   r1, r4, #{NAME_X}
    add   r2, r5, #{LINE_ROWS + TEXT_ROW}
    bl    {DRAW_STRING:#x}
    mov   r0, #{NUMBER_PALETTE}
    str   r0, [sp]
    ldr   r3, silver_gained
    ldr   r3, [r3]
    mov   r0, r7
    add   r1, r4, #{NUMBER_X}
    add   r2, r5, #{LINE_ROWS + TEXT_ROW}
    bl    {DRAW_NUMBER:#x}
out:
    add   sp, sp, #4
    pop   {{r4, r5, r6, r7, pc}}
table:
    .word {WINDOW_TABLE:#x}
silver_gained:
    .word ${{cave_silver_gained}}
silver_name:
    .word ${{cave_result_silver_text}}
"""


def _hook(addr: int, old: int, cave: str, note: str) -> AsmPatch:
    return AsmPatch(addr, addr + 4, old, old, f"bl ${{{cave}}}", note)


SILVER_LINE_PATCHES: tuple[AsmPatch | CaveCode, ...] = (
    CaveCode("cave_silver_layout", LAYOUT_ASM, "EXP page layout with the silver line"),
    CaveCode("cave_silver_frame_row", FRAME_ROW_ASM, "frame rows for the silver line"),
    CaveCode("cave_silver_pool_text", POOL_TEXT_ASM, "pool text without the banner"),
    CaveCode("cave_silver_member_text", MEMBER_TEXT_ASM, "silver line text"),
    CaveCode(
        "cave_result_silver_text",
        "    .byte " + ", ".join(f"{b:#x}" for b in SILVER_TEXT),
        "Silver label",
    ),
    _hook(OPEN_POOL_HOOK, OPEN_POOL_OLD, "cave_silver_layout", "EXP page layout"),
    _hook(FRAME_ROW_HOOK, FRAME_ROW_OLD, "cave_silver_frame_row", "window frame rows"),
    _hook(POOL_TEXT_HOOK, POOL_TEXT_OLD, "cave_silver_pool_text", "pool text row"),
    _hook(MEMBER_TEXT_HOOK, MEMBER_TEXT_OLD, "cave_silver_member_text", "silver line"),
)
