"""Field bottom screen pocketwatch: open = enemies about (timed run), closed = safe (unlimited run).

The watch was the Virtue clock, which the hack removed. Now it shows danger and the run gauge
(docs/re-field-hud.md section 4):
- open while the map has enemy spawn points (vanilla's test, func_02071c4c) and its area still has
  enemies left; closed in towns, rooms with no spawn points, and areas whose enemies are all beaten
- the hand sweeps one turn over the dash and winds back over the cooldown (timed-run state)
- the watch closes right after the battle that beats the last enemy; restock-on-entry rerolls the
  area on the next entry, so it opens again there

cave_watch_open is the one "watch open" test; the run code (feat_run.py) uses it too, so running
has no timer wherever the watch is closed. func_02071c4c itself stays as it is: the mode toggle and
enemy graphics loading also call it.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

ENEMY_MAP_TEST = 0x02071C4C  # func_02071c4c(-1): spawn points, map 0..0x96, not map 4
ENEMY_AREA_ENTRY = 0x0206EC54  # func_0206ec54(): this area's enemy entry or 0
AREA_KILLS = 4  # entry +4 u8 enemies beaten
AREA_TOTAL = 5  # entry +5 u8 enemies in the area

# cave_watch_open: r0 = 1 open, 0 closed; keeps r1..r3 and r12 (both callees only use r0..r2).
WATCH_OPEN_ASM = f"""
    push  {{r1, r2, r3, lr}}
    mvn   r0, #0
    bl    {ENEMY_MAP_TEST:#x}
    cmp   r0, #0
    beq   done
    bl    {ENEMY_AREA_ENTRY:#x}
    cmp   r0, #0
    moveq r0, #1
    beq   done
    ldrb  r1, [r0, #{AREA_KILLS}]
    ldrb  r2, [r0, #{AREA_TOTAL}]
    cmp   r1, r2
    movhs r0, #0
    movlo r0, #1
done:
    pop   {{r1, r2, r3, pc}}
"""
WATCH_OPEN_CAVE = CaveCode("cave_watch_open", WATCH_OPEN_ASM, "pocketwatch open test")

# HUD build (func_0206f3a4): open or closed body, hand and crystal shown or hidden
HUD_WATCH_TEST = 0x0206F4F4
HUD_WATCH_TEST_WORD = 0xEB0009D4  # bl func_02071c4c

# Hand rotation, field state 0x14 (0x02021F78..0x0202200C): vanilla turned the hand by the Virtue
# clock (entry +0 / entry +2). The block from 0x02021F78 to the division is replaced by the run
# gauge. The angle joins vanilla at 0x02021FF0, past its `rsb r0, r0, #0x10000` (which turned the hand
# counterclockwise), so the hand sweeps clockwise while running and winds back during the cooldown.
HAND_BLOCK = 0x02021F78
HAND_BLOCK_END = 0x02021FDC
HAND_BLOCK_FIRST = 0xE5D41004  # ldrb r1, [r4, #4]
HAND_BLOCK_LAST = 0xEB013E7F  # bl func_020719dc
HAND_ROTATE = 0x02021FF0  # lsl r2, r0, #16, then the affine matrix 0 call
FULL_TURN = 0x10000

# After a battle (field state 0x7B), every result path ends at 0x020209A8 with the HP/MP panel and
# kill boxes (func_0207184c). The whole HUD build (func_0206f3a4) does that and also picks the watch
# again, after the kill is counted, so the battle that beats the last enemy closes the watch.
AFTER_BATTLE_PANEL = 0x020209A8
AFTER_BATTLE_PANEL_WORD = 0xEB0143A7  # bl func_0207184c
HUD_BUILD = 0x0206F3A4


def hand_asm(run_state: int, run_ticks: int, cooldown_ticks: int) -> str:
    """Hand angle from the run state: one turn over the dash, wound back over the cooldown."""
    return f"""
    ldr   r0, run_state
    ldr   r0, [r0]
    mov   r0, r0, lsl #19
    mov   r0, r0, lsr #24
    cmp   r0, #{run_ticks}
    ldrls r1, run_step
    rsbhi r0, r0, #{run_ticks + cooldown_ticks}
    ldrhi r1, cooldown_step
    mul   r0, r1, r0
    b     {HAND_ROTATE:#x}
run_state:
    .word {run_state:#x}
run_step:
    .word {FULL_TURN // run_ticks:#x}
cooldown_step:
    .word {FULL_TURN // cooldown_ticks:#x}
"""


def pocketwatch(run_state: int, run_ticks: int, cooldown_ticks: int) -> Feature:
    """The pocketwatch feature for the timed run's state address and lengths (needs timed-run)."""
    return Feature(
        "pocketwatch",
        (
            AsmPatch(
                HUD_WATCH_TEST,
                HUD_WATCH_TEST + 4,
                HUD_WATCH_TEST_WORD,
                HUD_WATCH_TEST_WORD,
                "bl ${cave_watch_open}",
                "HUD: watch closed once the area is cleared",
            ),
            AsmPatch(
                HAND_BLOCK,
                HAND_BLOCK_END,
                HAND_BLOCK_FIRST,
                HAND_BLOCK_LAST,
                hand_asm(run_state, run_ticks, cooldown_ticks),
                "watch hand = run gauge",
            ),
            AsmPatch(
                AFTER_BATTLE_PANEL,
                AFTER_BATTLE_PANEL + 4,
                AFTER_BATTLE_PANEL_WORD,
                AFTER_BATTLE_PANEL_WORD,
                f"bl {HUD_BUILD:#x}",
                "rebuild the HUD after a battle: the clearing win closes the watch",
            ),
        ),
    )
