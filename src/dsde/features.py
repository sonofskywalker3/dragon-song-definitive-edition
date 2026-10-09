"""Every design change as a named Feature. See docs/design.md for the why."""

from pathlib import Path

from dsde.boss_exp import boss_exp, check_tables
from dsde.enemies import ENEMY_ROW_SIZE, ENEMY_TABLE, read_enemies
from dsde.feat_battle_end import BATTLE_END_RULES
from dsde.feat_battle_flow import BATTLE_FLOW
from dsde.feat_battle_kill import KILL_ON_HIT
from dsde.feat_battle_pace import BATTLE_PACE
from dsde.feat_battle_run import HOLD_LR_TO_RUN
from dsde.feat_battle_speed import BATTLE_SPEED
from dsde.feat_curse import NO_CURSE_PENALTY
from dsde.feat_enemy_moves import ENEMY_QUICK_STEPS, ENEMY_SHORT_MOVES
from dsde.feat_enemy_preload import ENEMY_PRELOAD
from dsde.feat_enemy_speed import ENEMY_SPELL_SPEED, ENEMY_SPRITE_SPEED
from dsde.feat_experience_name import EXPERIENCE_NAME
from dsde.feat_field_menu import FIELD_MENU
from dsde.feat_gad import GAD_EXPRESS
from dsde.feat_guidebook import GUIDEBOOK
from dsde.feat_hud import STILL_HUD
from dsde.feat_mic_sign import MIC_SIGN
from dsde.feat_mp import MP_ECONOMY
from dsde.feat_opening import OPENING
from dsde.feat_party import LEAVE_DROPS_GEAR
from dsde.feat_party_chat import PARTY_CHAT
from dsde.feat_results import RESULT_SCREENS
from dsde.feat_run import NO_RUN_HP_COST, POCKETWATCH, TIMED_RUN
from dsde.feat_spell_levels import SPELL_LEVELS_FEATURE
from dsde.feat_statue import STATUE_ANY_SIDE
from dsde.feat_targeting import MANUAL_TARGETING
from dsde.feat_text import TEXT_FIXES
from dsde.feat_text_speed import TEXT_SPEED
from dsde.feat_title_seal import TITLE_SEAL
from dsde.feat_town_brackets import TOWN_BRACKET_PATCHES
from dsde.feat_town_menu import TOWN_MENU_PATCHES
from dsde.feat_walk import WALK_SPEED
from dsde.patching import ARM_NOP, AsmPatch, CaveCode, DataPatch, Feature, Patch

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

TOWN_MENU = Feature("town-menu-dpad", TOWN_MENU_PATCHES + TOWN_BRACKET_PATCHES)

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
    TEXT_FIXES,
    HOLD_LR_TO_RUN,
    LEAVE_DROPS_GEAR,
    BATTLE_SPEED,
    NO_CURSE_PENALTY,
    BATTLE_PACE,
    KILL_ON_HIT,
    BATTLE_FLOW,
    MP_ECONOMY,
    SPELL_LEVELS_FEATURE,
    WALK_SPEED,
    GAD_EXPRESS,
    MIC_SIGN,
    OPENING,
    TEXT_SPEED,
    EXPERIENCE_NAME,
    TITLE_SEAL,
    TOWN_MENU,
    FIELD_MENU,
    GUIDEBOOK,
    STILL_HUD,
    STATUE_ANY_SIDE,
    POCKETWATCH,
    # Enemy action cuts (docs/plan-enemy-attacks.md, v0.1.5). The two script features share a
    # hook, so build at most one of enemy-short-moves and enemy-quick-steps.
    ENEMY_SPRITE_SPEED,
    ENEMY_SPELL_SPEED,
    ENEMY_SHORT_MOVES,
    ENEMY_QUICK_STEPS,
    # Sound bank switch moved before the enemy moves (docs/re-battle-pacing.md 7, P9). Off by default.
    ENEMY_PRELOAD,
    # Place-aware party chat on Y (docs/re-party-chat.md). Off by default while Jeff writes the lines.
    PARTY_CHAT,
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
    TEXT_FIXES.name,
    HOLD_LR_TO_RUN.name,
    LEAVE_DROPS_GEAR.name,
    BATTLE_SPEED.name,
    NO_CURSE_PENALTY.name,
    BATTLE_PACE.name,
    KILL_ON_HIT.name,
    BATTLE_FLOW.name,
    MP_ECONOMY.name,
    SPELL_LEVELS_FEATURE.name,
    WALK_SPEED.name,
    GAD_EXPRESS.name,
    MIC_SIGN.name,
    OPENING.name,
    TEXT_SPEED.name,
    EXPERIENCE_NAME.name,
    TITLE_SEAL.name,
    TOWN_MENU.name,
    FIELD_MENU.name,
    GUIDEBOOK.name,
    STILL_HUD.name,
    STATUE_ANY_SIDE.name,
    POCKETWATCH.name,
    ENEMY_SPRITE_SPEED.name,
    ENEMY_SPELL_SPEED.name,
    ENEMY_QUICK_STEPS.name,
)
