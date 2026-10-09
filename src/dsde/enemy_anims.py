"""Enemy attack animations: which action script each enemy action runs, and the emulator plans that
force one enemy into a battle and record its turns (docs/re-enemy-attacks.md).

Static part (this file): every enemy row's four actions (enemy record +0x2C chances, +0x34 actions,
docs/re-enemies.md), grouped per species into distinct actions (same flags, extra value and skill id =
same script and sprite, so area variants that share them are measured once), the action script each one
runs (func_02068034) and that script's step list (16-byte steps, func_02031514).

Plans: a battle is forced from the field of Delrich Temple (map 6) by the field's own battle start (the
three writes boss_gronk.plan uses), and for a regular battle the formation that func_0202b948 /
func_0202b3f0 chose is overwritten with `execpoke` at the entry of func_0202bc28 (called right after
func_0202b948 in func_020297d4 states 0 and 1). The enemy row gets 30000 HP, AI class 3 (always acts while
above half HP, func_02069848) and the chance table rewritten so the chosen action is always picked
(func_02069a38). Runner and analysis: dsde.enemy_anims_run.

    uv run python -m dsde.enemy_anims            # list every distinct action with its script
"""

import argparse
import logging
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from dsde.enemies import (
    ACTION_BREAK,
    ACTION_COUNT,
    ACTION_STEAL,
    ARM9_BASE,
    ENEMY_ROW_SIZE,
    ENEMY_TABLE,
    FIRST_BOSS_ROW,
    read_names,
    species_of,
    CARD_ITEM_BASE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARM9_BIN = PROJECT_ROOT / "extract" / "arm9" / "arm9.bin"
PLANS = PROJECT_ROOT / "emu" / "plans"
LAST_BOSS_ROW = 155  # 156 is the Blue Dragon's bubble, measured with the Blue Dragon

# func_02068034, AI command 1 (physical): script by the action's extra value, else by flags & 0xFF
PHYSICAL_SCRIPTS = 0x020A784C
SPECIAL_SCRIPT_MASK = 0xF0
SPECIAL_SCRIPTS = {0x10: 0x02095DF0, 0x20: 0x02095BB0, 0x30: 0x02095820}
DARK_JIAN_ROW = 0x97
DARK_JIAN_FIRST_SCRIPT = 0x02095C70  # Dark Jian's action 0
# AI command 2/4 (skill): spell table entry u16 [0x02094982 + skill * 0xC], script at 0x02096188 + i * 0x10
SKILL_INDEX = 0x02094982
SKILL_INDEX_SIZE = 0xC
SKILL_SCRIPTS = 0x02096188
SKILL_ENTRY_SIZE = 0x10
ACTION_USES_SKILL = 0x600  # action flags bits 9-10
SCRIPT_TABLE_SIZE = 12

STEP_SIZE = 0x10
STEP_END = 0x80000000
STEP_KIND_MASK = 3
STEP_KINDS = {0: "instant", 1: "anim", 2: "fixed", 3: "never"}
MAX_STEPS = 64

# Battle setup (docs/re-field-battle.md 2.3, docs/re-enemies.md)
BATTLE_CTX = 0x020B85B8
LEAD_ROW = BATTLE_CTX + 0x32
FORMATION_SLOTS = BATTLE_CTX + 0x34  # 8 x s16 rows, -1 empty; slot i is battler 4 + i
SLOT_COUNT = 8
AFTER_FORMATION = 0x0202BC28  # func_0202bc28 entry, right after func_0202b948
SPECIES_TABLE = (
    0x02096EDC  # 0x1C per species; flags & 4 = placed in slots 0..3 (back row)
)
SPECIES_SIZE = 0x1C
SPECIES_BACK_ROW = 4
FRONT_LEAD_SLOT = 5
BACK_LEAD_SLOT = 1
FIELD_EVENT_FLAG = 0x020B7838  # field + 0x54: 1 = event battle, 0 = regular
FIELD_BATTLE_ID = 0x020B783A  # field + 0x56: event battle id, or formation index
MAIN_STATE = 0x020B0010
MAIN_STATE_START_BATTLE = 0x73
MAIN_STATE_COMMAND = 7
STAT_RECORDS = 0x020B8620
STAT_HP = 0x14
FORCED_HP = 30000
JIAN_HP = 999
AI_CLASS_MASK = 3
AI_ALWAYS = 3
NEVER = 0xFFFF  # s16 -1: rand % 100 is never <= -1
ALWAYS = 100
STEAL_ITEMS = range(
    287, 297
)  # materials the thief can take (docs/re-enemies.md section 4)
INVENTORY = 0x0213B930
STEAL_STOCK = 5

# Bosses whose action is not the chance roll: func_020695c0 overrides it by battle type and round
# (Gronk every 20th round action 3, Zethos action 1 or 3, Red and White Dragon every 5th round action 2,
# Black Dragon every 4th action 1, Blue Dragon every 4th round below half HP action 2) and Dark Jian copies
# Jian's command (func_0202efdc). For these the action is also written into the actor when its action
# starts: func_02068890 -> func_02068034(battler) in round state 5, battler +0xC0 action index, +0x84 AI
# command (1 physical, 2 skill), +0x86 skill id.
ACTION_SETUP = 0x02068034
SETUP_FORCED_ROWS = frozenset({142, 143, 147, 148, 149, 150, 151})
# Natural actions of those rows that stall or lose turns when forced this way (measured with the chance
# table alone: the summary picks the turn that ran the action's own script)
SETUP_FORCE_SKIP = frozenset({(149, 0), (150, 1)})
AI_PHYSICAL = 1
AI_SKILL = 2
# Dark Jian copies Jian's command of the same round (func_0202efdc returns the first living party battler with
# character id 0's AI command +0x84): Fight (1) -> action 0, Special (2) -> action 1 (skill 13, script
# 0x02095EC0), command 4 -> action 2. Action 1 is recorded by having Jian cast Inferno every round: the Blazing
# Ring (item 0xCB) owned and worn in the accessory slot (Jian's gear, 5 x u16 at 0x020B4698, slot 4), and the
# battle MP (stat record + 0x18) kept at 99. Menu: Manual, then Special (Right, A), Inferno (A), OK (A, A).
DARK_JIAN_SPELL = (151, 1)
BLAZING_RING = 0xCB
JIAN_ACCESSORY = 0x020B46A0
STAT_MP = 0x18
JIAN_MP = 99
CAST_SPECIAL = ("press A 3", "wait 40", "press Right 3", "wait 30", "press A 3", "wait 40",
                "press A 3", "wait 40", "press A 3", "wait 40", "press A 3", "wait 40")  # fmt: skip

# Boss row -> event battle id (func_0202b948; docs/re-enemies.md)
BOSS_BATTLES = {
    136: 1, 137: 2, 138: 3, 139: 0x0F, 140: 0x10, 141: 4, 142: 5, 143: 6, 144: 7, 145: 7,
    146: 7, 147: 8, 148: 9, 149: 10, 150: 0x0B, 151: 0x19, 152: 0x0C, 153: 0x0D, 154: 0x0E,
    155: 0x11,
}  # fmt: skip


@dataclass(frozen=True)
class Step:
    index: int
    flags: int
    anim_slot: int
    sound: int
    frames: int

    @property
    def kind(self) -> str:
        return STEP_KINDS[self.flags & STEP_KIND_MASK]


@dataclass(frozen=True)
class EnemyAction:
    row: int  # the row measured (first row of the species with this action)
    rows: tuple[int, ...]  # every row with the same action
    name: str
    index: int  # action slot 0..3 in the row measured
    flags: int
    extra: int
    skill: int
    chance: int  # in the row measured, out of 100
    script: int  # static guess (func_02068034); the emulator log has the real one

    @property
    def boss(self) -> bool:
        return self.row >= FIRST_BOSS_ROW

    @property
    def label(self) -> str:
        if self.flags & ACTION_STEAL:
            kind = "steal"
        elif self.flags & ACTION_BREAK:
            kind = "break"
        elif self.flags & ACTION_USES_SKILL:
            kind = f"skill{self.skill}"
        else:
            kind = "attack"
        extra = f"_x{self.extra:x}" if self.extra else ""
        return f"a{self.index}_{kind}{extra}"

    @property
    def key(self) -> str:
        """Folder name under build/enemy_anims/."""
        name = re.sub(r"[^A-Za-z0-9]+", "_", self.name).strip("_")
        return f"{self.row:03d}_{name}_{self.label}"


def u16(data: bytes, addr: int) -> int:
    return struct.unpack_from("<H", data, addr - ARM9_BASE)[0]


def u32(data: bytes, addr: int) -> int:
    return struct.unpack_from("<I", data, addr - ARM9_BASE)[0]


def row_addr(row: int) -> int:
    return ENEMY_TABLE + row * ENEMY_ROW_SIZE


def read_steps(data: bytes, script: int) -> list[Step]:
    steps = []
    for i in range(MAX_STEPS):
        flags, _, anim, sound, frames = struct.unpack_from(
            "<IIhhh", data, script - ARM9_BASE + i * STEP_SIZE
        )
        steps.append(Step(i, flags, anim, sound, frames))
        if flags & STEP_END:
            break
    return steps


def static_script(data: bytes, row: int, flags: int, extra: int, skill: int) -> int:
    """The script func_02068034 gives this action (0 when it cannot tell statically)."""
    if flags & ACTION_USES_SKILL:
        index = u16(data, SKILL_INDEX + skill * SKILL_INDEX_SIZE)
        return u32(data, SKILL_SCRIPTS + index * SKILL_ENTRY_SIZE)
    if row == DARK_JIAN_ROW:
        return 0  # action 0 uses 0x02095C70 on its first use only
    special = SPECIAL_SCRIPTS.get(extra & SPECIAL_SCRIPT_MASK)
    if special:
        return special
    index = flags & 0xFF
    if index >= SCRIPT_TABLE_SIZE:
        return 0
    return u32(data, PHYSICAL_SCRIPTS + index * 4)


def read_actions(data: bytes) -> list[EnemyAction]:
    """Distinct actions per species (normal rows) and per boss row."""
    names = read_names(data)
    found: dict[tuple, dict] = {}
    for row in range(LAST_BOSS_ROW + 1):
        base = row_addr(row)
        chances = struct.unpack_from(f"<{ACTION_COUNT}h", data, base + 0x2C - ARM9_BASE)
        previous = 0  # same convention as dsde.enemies (cumulative differences)
        for index in range(ACTION_COUNT):
            flags, extra, skill = struct.unpack_from(
                "<IHh", data, base + 0x34 + index * 8 - ARM9_BASE
            )
            chance = max(0, chances[index] - previous)
            previous = max(previous, chances[index])
            if not flags:
                continue
            group = species_of(row) if row < FIRST_BOSS_ROW else row
            key = (group, flags, extra, skill)
            if key in found:
                found[key]["rows"].append(row)
                continue
            found[key] = dict(
                row=row,
                rows=[row],
                name=names[CARD_ITEM_BASE + species_of(row)],
                index=index,
                flags=flags,
                extra=extra,
                skill=skill,
                chance=min(chance, ALWAYS),
                script=static_script(data, row, flags, extra, skill),
            )
    return [EnemyAction(**{**v, "rows": tuple(v["rows"])}) for v in found.values()]


def read_plan(name: str) -> str:
    """A plan's text with its includes inlined (generated plans live outside emu/plans)."""
    lines = []
    for line in (PLANS / f"{name}.plan").read_text().splitlines():
        words = line.split("#")[0].split()
        if words[:1] == ["include"]:
            lines.append(read_plan(words[1]))
        else:
            lines.append(line)
    return "\n".join(lines)


def force_row_lines(data: bytes, row: int, action_index: int | None) -> list[str]:
    """Pokes that give a row 30000 HP, AI class 3 and (optionally) one action always picked."""
    base = row_addr(row)
    flags = u32(data, base)
    lines = [
        f"poke u16 {base + 0x04:#010x} {FORCED_HP}",
        f"poke u16 {base + 0x18:#010x} {FORCED_HP}",
        f"poke u32 {base:#010x} {(flags & ~AI_CLASS_MASK) | AI_ALWAYS:#x}",
    ]
    if action_index is not None:
        for i in range(ACTION_COUNT):
            value = NEVER if i < action_index else ALWAYS
            lines.append(f"poke u16 {base + 0x2C + 2 * i:#010x} {value:#x}")
    return lines


def battle_rows(action: EnemyAction) -> list[int]:
    """Rows to strengthen in the battle: the boss fights with helpers have several bosses."""
    if action.row in (144, 145, 146):
        return [144, 145, 146]
    if action.row == 150:
        return [150, 156]
    return [action.row]


def lead_slot(data: bytes, row: int) -> int:
    species_flags = u32(data, SPECIES_TABLE + species_of(row) * SPECIES_SIZE)
    return BACK_LEAD_SLOT if species_flags & SPECIES_BACK_ROW else FRONT_LEAD_SLOT


def battle_lines(data: bytes, action: EnemyAction) -> list[str]:
    """Start the battle: the boss's own event battle, or a regular battle with only this row."""
    if action.boss:
        return [
            f"poke u16 {FIELD_EVENT_FLAG:#010x} 1",
            f"poke u16 {FIELD_BATTLE_ID:#010x} {BOSS_BATTLES[action.row]}",
            f"poke u32 {MAIN_STATE:#010x} {MAIN_STATE_START_BATTLE:#x}",
        ]
    slot = lead_slot(data, action.row)
    lines = [f"execpoke {AFTER_FORMATION:#010x} u16 {LEAD_ROW:#010x} {action.row}"]
    for i in range(SLOT_COUNT):
        value = action.row if i == slot else NEVER
        lines.append(
            f"execpoke {AFTER_FORMATION:#010x} u16 {FORMATION_SLOTS + 2 * i:#010x} {value:#x}"
        )
    lines += [
        f"poke u16 {FIELD_EVENT_FLAG:#010x} 0",
        f"poke u16 {FIELD_BATTLE_ID:#010x} 0",
        f"poke u32 {MAIN_STATE:#010x} {MAIN_STATE_START_BATTLE:#x}",
    ]
    return lines


def make_plan(
    data: bytes,
    action: EnemyAction,
    name: str,
    speed_pin: str | None,
    turns: int,
    shot_turns: int,
) -> str:
    """One run: boot, stand in Delrich Temple, force the battle, Auto, record `turns` enemy turns."""
    lines = [
        f"# generated by dsde.enemy_anims: {action.key} ({name})",
        read_plan("boot_from_save"),
        read_plan("cheats_strong"),
        "# Delrich Temple (map 6), standing off the enemy spawn points (as boss_gronk.plan)",
        "pin u16 0x020B77EC 6",
        "press Right 40",
        "press Down,Right 40",
        "press Right 40",
        "press Down 80",
        "wait 200",
        "unpin",
        read_plan("cheats_strong"),
        f"pinptr u32 {STAT_RECORDS:#010x} {STAT_HP:#x} {JIAN_HP}",
    ]
    if speed_pin:
        lines.append(speed_pin)
    for row in battle_rows(action):
        lines += force_row_lines(data, row, action.index if row == action.row else None)
    if (
        action.row in SETUP_FORCED_ROWS
        and (action.row, action.index) not in SETUP_FORCE_SKIP
        and (action.row, action.index) != DARK_JIAN_SPELL
    ):
        skill = bool(action.flags & ACTION_USES_SKILL)
        lines += [
            f"execpokereg {ACTION_SETUP:#010x} 0 0xC0 u32 {action.index}",
            f"execpokereg {ACTION_SETUP:#010x} 0 0x84 u16 {AI_SKILL if skill else AI_PHYSICAL}",
        ]
        if skill:
            lines.append(f"execpokereg {ACTION_SETUP:#010x} 0 0x86 u16 {action.skill}")
    if action.flags & ACTION_STEAL:
        lines += [
            f"poke u8 {INVENTORY + item - 1:#010x} {STEAL_STOCK}"
            for item in STEAL_ITEMS
        ]
    if (action.row, action.index) == DARK_JIAN_SPELL:
        lines += [
            f"poke u8 {INVENTORY + BLAZING_RING - 1:#010x} 1",
            f"poke u16 {JIAN_ACCESSORY:#010x} {BLAZING_RING:#x}",
            f"pinptr u32 {STAT_RECORDS:#010x} {STAT_MP:#x} {JIAN_MP}",
        ]
    lines += battle_lines(data, action)
    wait_command = [
        f"waituntil u32 {MAIN_STATE:#010x} {MAIN_STATE_COMMAND} 3000",
        "wait 110",  # the Manual/Auto window slides in after state 7 starts
    ]
    lines += [
        f"rec {name} 2 {turns} {shot_turns} {action.row}",
        *wait_command,
        "shot cmd",
    ]
    if (action.row, action.index) == DARK_JIAN_SPELL:
        lines.append(
            "# Manual: Jian casts Inferno each round, Dark Jian copies the Special"
        )
        for round_index in range(turns + 1):
            lines += [*(wait_command if round_index else []), *CAST_SPECIAL]
    else:
        lines += [
            "# Auto battle: Right, A, then A on the confirmation",
            "press Right 3",
            "wait 10",
            "press A 3",
            "wait 20",
            "press A 3",
        ]
    lines += [
        "waitrec 9000",
        "shot end",
        "battlers",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.enemy_anims")
    parser.parse_args()
    data = ARM9_BIN.read_bytes()
    for action in read_actions(data):
        steps = read_steps(data, action.script) if action.script else []
        fixed = sum(s.frames for s in steps if s.kind == "fixed")
        print(
            f"{action.key:40s} rows {','.join(map(str, action.rows)):16s} "
            f"{action.flags:#010x} x{action.extra:#x} sk{action.skill:3d} {action.chance:3d}% "
            f"script {action.script:#010x} steps {len(steps):2d} fixed {fixed}"
        )


if __name__ == "__main__":
    main()
