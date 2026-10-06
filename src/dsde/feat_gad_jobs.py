"""Gad's Express job offers by towns visited (design 9). Research: docs/re-mp-jobs-rings.md section 2.

Vanilla: an office's rank rises every 5 deliveries made from it, and func_0206cf28 picks 4 random templates from
the first rank * 10 of the office's 40. Now:

- Rank (func_02071fa8) = towns visited - 1, from 1 to 4 (a new game already has 2: Port Searis and Perit). Towns visited = set bytes among the 7 destination
  unlocks at 0x020B486A (set when a town's main map is first entered, func_02041d38).
- The pick (a cave replacing the 6 calls of func_0206cf28 in func_0206cfc0) offers up to 3 templates whose items
  can all be had by now (earliest town count from dsde.gad_jobs, at or below towns visited), from the rank range,
  or from the rest of the pool if the rank range has fewer than 3, then fills the remaining slots with "future"
  templates (obtainable later). The first future slot pays 1.5 times its fee (fee store in func_0206cc2c).
  Templates whose items have no shop or regular enemy source are never offered.
"""

import struct
from pathlib import Path

from dsde.gad_jobs import template_town_counts
from dsde.patching import ARM9_BASE, AsmPatch, CaveCode, Patch

VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"
ARM_PC_AHEAD = 8

PLACE_UNLOCKS = 0x020B486A
PLACE_COUNT = 7
MAX_RANK = 4
MIN_RANK = 1
START_TOWNS = 2  # destinations unlocked when play starts; rank 1 there, +1 per new town
MAP_ID = 0x020B6BE4
OFFICES = (  # Gad's office map: template pool (40 u16 template indices)
    (0x9A, 0x0209DEB4),
    (0xA9, 0x0209DF04),
    (0xBD, 0x0209DF54),
    (0xCA, 0x0209DDC4),
    (0xEC, 0x0209DE14),
    (0xFC, 0x0209DE64),
)
POOL_SIZE = 40
NOW_SLOTS = 3
JOB_SLOTS = 4
NEVER = 0xFF  # no shop or regular enemy source: never offered
PICK_STACK = 2 * POOL_SIZE  # two byte lists: obtainable now, future
RAND = 0x02011424
DIVMOD = 0x02015F80  # r1 = r0 % r1
VANILLA_PICK = 0x0206CF28
PICK_CALLS = {  # func_0206cfc0: bl func_0206cf28, one per office
    0x0206D080: 0xEBFFFFA8,
    0x0206D0C4: 0xEBFFFF97,
    0x0206D108: 0xEBFFFF86,
    0x0206D14C: 0xEBFFFF75,
    0x0206D190: 0xEBFFFF64,
    0x0206D1D4: 0xEBFFFF53,
}
FEE_STORE = 0x0206CEE8  # func_0206cc2c: str r3, [r0, #0x1c] (r8 = slot)
FEE_STORE_WORD = 0xE580301C
RANK_FUNC = 0x02071FA8
RANK_FUNC_END = 0x02071FF4
RANK_FIRST_WORD = 0xE92D4000
RANK_LAST_WORD = 0xE12FFF1E
RANK_POOL = (
    0x02071FF4  # literal 0x020B4864 (delivery counters; the unlocks follow at +6)
)
UNLOCKS_AFTER_COUNTERS = 6


def availability_rows() -> bytes:
    """Earliest town count per office pool entry, 40 bytes per office in OFFICES order."""
    data = VANILLA_ARM9.read_bytes()
    counts = template_town_counts(data)
    rows = bytearray()
    for _, pool in OFFICES:
        for template in struct.unpack_from(f"<{POOL_SIZE}H", data, pool - ARM9_BASE):
            count = counts.get(template)
            rows.append(NEVER if count is None else count)
    return bytes(rows)


def _bytes_asm(data: bytes) -> str:
    return "\n".join(f"    .byte {b}" for b in data)


def _rank_asm() -> str:
    return f"""
    ldr   r1, [pc, #{RANK_POOL - (RANK_FUNC + ARM_PC_AHEAD):#x}]
    add   r1, r1, #{UNLOCKS_AFTER_COUNTERS}
    mov   r0, #0
    mov   r2, #0
count:
    ldrb  r3, [r1, r2]
    cmp   r3, #0
    addne r0, r0, #1
    add   r2, r2, #1
    cmp   r2, #{PLACE_COUNT}
    blt   count
    sub   r0, r0, #{START_TOWNS - MIN_RANK}
    cmp   r0, #{MIN_RANK}
    movlt r0, #{MIN_RANK}
    cmp   r0, #{MAX_RANK}
    movgt r0, #{MAX_RANK}
    bx    lr
"""


# In: r0 = u16 out[4] (pool indices), r1 = rank * 10. Lists on the stack: now at sp, future at sp + 40.
# r4 out, r5 limit, r6 towns, r7 office row / count wanted now, r8 availability row, r9 now count,
# r10 future count, r11 loop index.
PICK_ASM = f"""
    push  {{r4-r11, lr}}
    sub   sp, sp, #{PICK_STACK}
    mov   r4, r0
    mov   r5, r1
    ldr   r0, unlocks
    mov   r6, #0
    mov   r1, #0
towns:
    ldrb  r2, [r0, r1]
    cmp   r2, #0
    addne r6, r6, #1
    add   r1, r1, #1
    cmp   r1, #{PLACE_COUNT}
    blt   towns
    ldr   r0, map_id
    ldrsh r0, [r0]
    adr   r1, office_maps
    mov   r7, #0
office:
    add   r2, r1, r7, lsl #1
    ldrh  r2, [r2]
    cmp   r2, r0
    beq   found
    add   r7, r7, #1
    cmp   r7, #{len(OFFICES)}
    blt   office
    add   sp, sp, #{PICK_STACK}
    mov   r0, r4
    mov   r1, r5
    pop   {{r4-r11, lr}}
    b     {VANILLA_PICK:#x}
found:
    adr   r8, availability
    mov   r0, #{POOL_SIZE}
    mla   r8, r7, r0, r8
    mov   r9, #0
    mov   r10, #0
    mov   r11, #0
split:
    ldrb  r0, [r8, r11]
    cmp   r0, #{NEVER}
    beq   next
    cmp   r0, r6
    bgt   future
    cmp   r11, r5
    strblt r11, [sp, r9]
    addlt r9, r9, #1
    b     next
future:
    add   r1, sp, #{POOL_SIZE}
    strb  r11, [r1, r10]
    add   r10, r10, #1
next:
    add   r11, r11, #1
    cmp   r11, #{POOL_SIZE}
    blt   split
    mov   r11, r5
extra:
    cmp   r9, #{NOW_SLOTS}
    bge   choose
    cmp   r11, #{POOL_SIZE}
    bge   choose
    ldrb  r0, [r8, r11]
    cmp   r0, r6
    strble r11, [sp, r9]
    addle r9, r9, #1
    add   r11, r11, #1
    b     extra
choose:
    cmp   r10, #0
    movne r7, #{NOW_SLOTS}
    moveq r7, #{JOB_SLOTS}
    cmp   r9, r7
    movlt r7, r9
    mov   r11, #0
pick_now:
    cmp   r11, r7
    bge   pick_future
    bl    {RAND:#x}
    sub   r1, r9, r11
    bl    {DIVMOD:#x}
    add   r1, r1, r11
    ldrb  r0, [sp, r11]
    ldrb  r2, [sp, r1]
    strb  r0, [sp, r1]
    strb  r2, [sp, r11]
    mov   r0, r11, lsl #1
    strh  r2, [r4, r0]
    add   r11, r11, #1
    b     pick_now
pick_future:
    ldr   r0, future_slot
    mvn   r1, #0
    str   r1, [r0]
    add   r9, sp, #{POOL_SIZE}
    mov   r6, #0
future_loop:
    cmp   r11, #{JOB_SLOTS}
    bge   done
    cmp   r6, r10
    bge   done
    bl    {RAND:#x}
    sub   r1, r10, r6
    bl    {DIVMOD:#x}
    add   r1, r1, r6
    ldrb  r0, [r9, r6]
    ldrb  r2, [r9, r1]
    strb  r0, [r9, r1]
    strb  r2, [r9, r6]
    mov   r0, r11, lsl #1
    strh  r2, [r4, r0]
    cmp   r6, #0
    ldreq r0, future_slot
    streq r11, [r0]
    add   r6, r6, #1
    add   r11, r11, #1
    b     future_loop
done:
    add   sp, sp, #{PICK_STACK}
    pop   {{r4-r11, pc}}
unlocks:
    .word {PLACE_UNLOCKS:#x}
map_id:
    .word {MAP_ID:#x}
future_slot:
    .word ${{cave_gad_future_slot}}
office_maps:
{chr(10).join(f"    .hword {office:#x}" for office, _ in OFFICES)}
availability:
"""

FEE_ASM = """
    ldr   r1, future_slot
    ldr   r1, [r1]
    cmp   r1, r8
    addeq r3, r3, r3, lsr #1
    str   r3, [r0, #0x1c]
    bx    lr
future_slot:
    .word ${cave_gad_future_slot}
"""


# The job list (func_0204ccd4, main engine BG) draws each title with palette bank 10; the future job's title
# uses bank 9 (unused on this screen) holding a red copy of bank 10. Its text colors 1 (lightest) to 7 (the
# glyph core) are blended from white down to dark red.
TITLE_PALETTE_STORE = (
    0x0204D8A8  # str r4, [sp, #8]: palette bank argument (r4 = 10, r7 = slot)
)
TITLE_PALETTE_STORE_WORD = 0xE58D4008
RED_BANK = 9
BG_PALETTE_MAIN = 0x05000000
PALETTE_BANK_BYTES = 0x20
JOB_TITLE_PALETTE = (
    0x0000,
    0x7FDE,
    0x6739,
    0x56B5,
    0x4631,
    0x2529,
    0x1084,
    0x0421,
    *(0x7FFF,) * 7,
    0x0000,
)
TEXT_COLORS = range(1, 8)
DARK_RED = (24, 2, 2)  # 5-bit RGB of the glyph core
WHITE_LEVEL = 31
CHANNEL_BITS = 5
CHANNEL_MASK = 0x1F


def red_title_palette() -> tuple[int, ...]:
    colors = list(JOB_TITLE_PALETTE)
    for i in TEXT_COLORS:
        level = colors[i] & CHANNEL_MASK
        t = (level - 1) / (WHITE_LEVEL - 1)
        r, g, b = (round(c + t * (WHITE_LEVEL - c)) for c in DARK_RED)
        colors[i] = r | g << CHANNEL_BITS | b << 2 * CHANNEL_BITS
    return tuple(colors)


TITLE_ASM = f"""
    ldr   r0, future_slot
    ldr   r0, [r0]
    cmp   r0, r7
    movne r0, r4
    moveq r0, #{RED_BANK}
    str   r0, [sp, #8]
    bxne  lr
    adr   r1, red
    ldr   r2, bank
    mov   r3, #0
copy:
    ldrh  r12, [r1, r3]
    strh  r12, [r2, r3]
    add   r3, r3, #2
    cmp   r3, #{PALETTE_BANK_BYTES}
    blt   copy
    bx    lr
future_slot:
    .word ${{cave_gad_future_slot}}
bank:
    .word {BG_PALETTE_MAIN + RED_BANK * PALETTE_BANK_BYTES:#x}
red:
{chr(10).join(f"    .short {c:#x}" for c in red_title_palette())}
"""


def job_patches() -> tuple[CaveCode | AsmPatch | Patch, ...]:
    return (
        CaveCode("cave_gad_future_slot", "    .word 0xffffffff", "future job slot"),
        CaveCode(
            "cave_gad_pick",
            PICK_ASM + _bytes_asm(availability_rows()),
            "job offers: obtainable now plus one future job",
        ),
        CaveCode("cave_gad_fee", FEE_ASM, "future job pays 1.5 times"),
        *(
            AsmPatch(
                addr, addr + 4, word, word, "bl ${cave_gad_pick}", "pick job offers"
            )
            for addr, word in PICK_CALLS.items()
        ),
        AsmPatch(
            FEE_STORE,
            FEE_STORE + 4,
            FEE_STORE_WORD,
            FEE_STORE_WORD,
            "bl ${cave_gad_fee}",
            "future job fee x1.5",
        ),
        AsmPatch(
            RANK_FUNC,
            RANK_FUNC_END,
            RANK_FIRST_WORD,
            RANK_LAST_WORD,
            _rank_asm(),
            "office rank = towns visited, 1 to 4",
        ),
        CaveCode("cave_gad_title", TITLE_ASM, "future job title in red"),
        AsmPatch(
            TITLE_PALETTE_STORE,
            TITLE_PALETTE_STORE + 4,
            TITLE_PALETTE_STORE_WORD,
            TITLE_PALETTE_STORE_WORD,
            "bl ${cave_gad_title}",
            "future job title in red",
        ),
    )
