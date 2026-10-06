"""Every design change as a named Feature. See docs/design.md for the why."""

from pathlib import Path

from dsde.boss_exp import boss_exp, check_tables
from dsde.enemies import ENEMY_ROW_SIZE, ENEMY_TABLE, read_enemies
from dsde.feat_battle_end import BATTLE_END_RULES
from dsde.feat_results import RESULT_SCREENS
from dsde.feat_targeting import MANUAL_TARGETING
from dsde.patching import ARM_NOP, AsmPatch, CaveCode, DataPatch, Feature, Patch

# Field running, see docs/re-field-battle.md section 1. The run state lives in the player's
# 8-bit counter at +0x40 bits 5..12 (the old HP drain counter): 0 = ready, 1..RUN_TICKS =
# running, then cooldown until RUN_TICKS + COOLDOWN_TICKS. One tick = 2 frames at 60 fps.
# As in Lunar 1 and 2, holding B runs once: after the cooldown the state waits at its end until B is
# released, so running again needs a fresh press.
FRAMES_PER_TICK = 2
RUN_TICKS = 90  # 3 seconds
COOLDOWN_TICKS = 90  # 3 seconds
FRAME_COUNTER = 0x020B05BC
TIMED_RUN_BODY_ADDR = 0x020251AC
TIMED_RUN_EXIT = 0x02024C58
DPAD_MASK = 0xF0
# Bits 5..12 (0x1FE0) is not an ARM immediate, so it is cleared in two parts
COUNTER_MASK_HIGH = 0x1FC0
COUNTER_MASK_LOW = 0x20

# Part 1 sits in the freed too-tired check block: load the run state, then jump to part 2.
TIMED_RUN_ASM_ENTRY = f"""
    ldr   r1, [r2]
    mov   r3, r1, lsl #19
    mov   r3, r3, lsr #24
    ldr   r0, [sp, #8]
    ldr   r12, frame_counter
    ldrh  r12, [r12]
    b     {TIMED_RUN_BODY_ADDR:#x}
frame_counter:
    .word {FRAME_COUNTER:#x}
"""

# Part 2 sits in the freed HP drain block. In: r0 = B held, r1 = player flags, r2 = &flags,
# r3 = run state, r5 = held keys, r12 = frame counter.
TIMED_RUN_ASM_BODY = f"""
    cmp   r3, #0
    bne   active
    cmp   r0, #0
    tstne r5, #{DPAD_MASK:#x}
    movne r3, #1
    b     store
active:
    cmp   r3, #{RUN_TICKS}
    bhi   tick
    cmp   r0, #0
    moveq r3, #{RUN_TICKS + 1}
    beq   store
tick:
    tst   r12, #{FRAMES_PER_TICK - 1}
    addeq r3, r3, #1
    cmp   r3, #{RUN_TICKS + COOLDOWN_TICKS}
    bls   store
    cmp   r0, #0
    movne r3, #{RUN_TICKS + COOLDOWN_TICKS}
    moveq r3, #0
store:
    bic   r1, r1, #{COUNTER_MASK_HIGH:#x}
    bic   r1, r1, #{COUNTER_MASK_LOW:#x}
    orr   r1, r1, r3, lsl #5
    str   r1, [r2]
    sub   r0, r3, #1
    cmp   r0, #{RUN_TICKS}
    movlo r0, #1
    movhs r0, #0
    str   r0, [sp, #8]
    b     {TIMED_RUN_EXIT:#x}
"""

# Branch encodings: 0xEA000000 | ((target - (addr + 8)) >> 2).
NO_RUN_HP_COST = Feature(
    "no-run-hp-cost",
    (
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        Patch(
            0x02024BF8,
            0x0A000016,
            0xEA000016,
            "beq -> b: skip the HP <= 1/3 too-tired check",
        ),
    ),
)

TIMED_RUN = Feature(
    "timed-run",
    (
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        AsmPatch(
            0x02024BF8,
            0x02024C58,
            0x0A000016,
            0xBAFFFFEA,
            TIMED_RUN_ASM_ENTRY,
            "load run state",
        ),
        AsmPatch(
            TIMED_RUN_BODY_ADDR,
            0x02025228,
            0xE5902000,
            0xEB013188,
            TIMED_RUN_ASM_BODY,
            "3 s run, 3 s cooldown",
        ),
    ),
)

# One battle mode, see docs/re-field-battle.md section 2.9. Mode flag 0x020B4848: 1 = Virtue (EXP).
ONE_BATTLE_MODE = Feature(
    "one-battle-mode",
    (
        Patch(
            0x0201F128,
            0x0A00004C,
            0xEA00004C,
            "beq -> b: R and the touch button no longer toggle the mode",
        ),
        Patch(
            0x020298E0,
            0xE5D00298,
            0xE3A00001,
            "ldrb flag -> mov r0, #1: battles use Virtue rules",
        ),
        Patch(
            0x02029984,
            0xE5D00298,
            0xE3A00001,
            "ldrb flag -> mov r0, #1: battles use Virtue rules",
        ),
        Patch(
            0x02053680,
            0xEA000013,
            0xEA000011,
            "EXP kills also fall into the item drop roll",
        ),
    ),
)

NO_VIRTUE_CLOCK = Feature(
    "no-virtue-clock",
    (
        Patch(
            0x02021F80,
            0x0A000015,
            0xEA000015,
            "beq -> b: the clock never revives a defeated enemy",
        ),
    ),
)

RESTOCK_ON_ENTRY = Feature(
    "restock-on-entry",
    (
        Patch(
            0x0201E0F4,
            0x1A000008,
            ARM_NOP,
            "every fresh map entry rerolls enemies and zeroes kills",
        ),
    ),
)

NO_CLEAR_REFILL = Feature(
    "no-clear-refill",
    (
        Patch(
            0x0202096C,
            0x05C01C64,
            ARM_NOP,
            "never set the area-cleared flag, so no 30% HP/MP refill",
        ),
    ),
)

# US save glitch, see docs/re-field-battle.md section 5. Flora's Underground Tunnel line in script 010
# marks itself as said with story flag 0xCF, which is the endgame save lock, and nothing clears it.
SAVE_LOCK_FLAG = 0xCF
FLORA_LINE_FLAG = 0x5E  # unused by every script and by engine code
FIX_SAVE_GLITCH = Feature(
    "fix-save-glitch",
    (
        DataPatch(
            "script",
            10,
            0x3F34,
            SAVE_LOCK_FLAG.to_bytes(4, "little"),
            FLORA_LINE_FLAG.to_bytes(4, "little"),
            "Flora's tunnel line checks its own flag, not the save lock",
        ),
        DataPatch(
            "script",
            10,
            0x3F52,
            SAVE_LOCK_FLAG.to_bytes(2, "little"),
            FLORA_LINE_FLAG.to_bytes(2, "little"),
            "Flora's tunnel line sets its own flag, not the save lock",
        ),
    ),
)

# Silver from battles (design 3). At the EXP step func_02052fb8 fetches the battle's EXP pool
# (before the game doubles it); the hook adds the same amount of silver. Tune SILVER_PER_EXP later.
# The amount is also kept in cave_silver_gained for the Silver line on the result-screens EXP page.
SILVER = 0x020B4824
SILVER_CAP = 999_999
GET_EXP_POOL = 0x0202AF34
SILVER_HOOK = 0x02052FE0
SILVER_DROPS = Feature(
    "silver-drops",
    (
        CaveCode(
            "cave_silver",
            f"""
    push  {{r4, lr}}
    bl    {GET_EXP_POOL:#x}
    mov   r4, r0
    ldr   r1, silver_gained
    str   r4, [r1]
    ldr   r1, silver
    ldr   r2, [r1]
    add   r2, r2, r4
    ldr   r3, silver_cap
    cmp   r2, r3
    movhi r2, r3
    str   r2, [r1]
    mov   r0, r4
    pop   {{r4, pc}}
silver:
    .word {SILVER:#x}
silver_cap:
    .word {SILVER_CAP:#x}
silver_gained:
    .word ${{cave_silver_gained}}
""",
            "battle EXP pool -> silver",
        ),
        CaveCode("cave_silver_gained", "    .word 0", "silver gained this battle"),
        AsmPatch(
            SILVER_HOOK,
            SILVER_HOOK + 4,
            0xEBFF5FD3,
            0xEBFF5FD3,
            "bl ${cave_silver}",
            "EXP step also pays silver",
        ),
    ),
)

# Bosses give EXP (design 2). Vanilla boss and scripted battles run with battle mode -1, and four
# checks require mode == 1 for EXP; they become mode != 0. Boss EXP fields are 1 to 10 placeholders,
# so each boss gets BOSS_EXP_FACTOR times the average EXP of its area's regular enemies (dsde.boss_exp).
VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"
EXP_MIN_OFFSET = 0x14
EXP_MAX_OFFSET = 0x28


def _boss_exp_patches() -> tuple[Patch, ...]:
    data = VANILLA_ARM9.read_bytes()
    check_tables(data)
    enemies = read_enemies(data)
    patches = []
    for row, (exp_min, exp_max) in boss_exp(enemies).items():
        enemy = enemies[row]
        address = ENEMY_TABLE + row * ENEMY_ROW_SIZE
        note = f"{enemy.name} EXP"
        patches.append(
            Patch(
                address + EXP_MIN_OFFSET, enemy.exp_min, exp_min, note + " at level 0"
            )
        )
        patches.append(
            Patch(
                address + EXP_MAX_OFFSET, enemy.exp_max, exp_max, note + " at level 98"
            )
        )
    return tuple(patches)


CMP_MODE_1 = 0xE3500001
CMP_MODE_0 = 0xE3500000
BOSS_EXP = Feature(
    "boss-exp",
    (
        Patch(0x0205361C, CMP_MODE_1, CMP_MODE_0, "enemy death: EXP when mode != 0"),
        Patch(0x02053620, 0x1A000017, 0x0A000017, "enemy death: EXP when mode != 0"),
        Patch(
            0x0202A8E4,
            CMP_MODE_1,
            CMP_MODE_0,
            "result routing: EXP screen when mode != 0",
        ),
        Patch(
            0x0202A8E8,
            0x1A000003,
            0x0A000003,
            "result routing: EXP screen when mode != 0",
        ),
        Patch(
            0x0202A9F8,
            CMP_MODE_1,
            CMP_MODE_0,
            "result routing: EXP screen when mode != 0",
        ),
        Patch(
            0x0202A9FC,
            0x1A000003,
            0x0A000003,
            "result routing: EXP screen when mode != 0",
        ),
        Patch(
            0x0203B0E0,
            CMP_MODE_1,
            CMP_MODE_0,
            "result setup: EXP windows whenever EXP is shown",
        ),
        Patch(
            0x0203B0E4,
            0x0A0000B3,
            0x1A0000B3,
            "result setup: EXP windows whenever EXP is shown",
        ),
        *_boss_exp_patches(),
    ),
)

FEATURES: tuple[Feature, ...] = (
    NO_RUN_HP_COST,
    TIMED_RUN,
    ONE_BATTLE_MODE,
    RESULT_SCREENS,
    NO_VIRTUE_CLOCK,
    RESTOCK_ON_ENTRY,
    NO_CLEAR_REFILL,
    FIX_SAVE_GLITCH,
    SILVER_DROPS,
    BOSS_EXP,
    BATTLE_END_RULES,
    MANUAL_TARGETING,
)
DEFAULT_FEATURES: tuple[str, ...] = (
    TIMED_RUN.name,
    ONE_BATTLE_MODE.name,
    NO_VIRTUE_CLOCK.name,
    RESTOCK_ON_ENTRY.name,
    NO_CLEAR_REFILL.name,
    FIX_SAVE_GLITCH.name,
    SILVER_DROPS.name,
    BOSS_EXP.name,
    RESULT_SCREENS.name,
    BATTLE_END_RULES.name,
    MANUAL_TARGETING.name,
)
