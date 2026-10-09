"""Enemy attack animations: which action script each enemy action runs (docs/re-enemy-attacks.md).

Every enemy row's four actions (enemy record +0x2C chances, +0x34 actions, docs/re-enemies.md), grouped per
species into distinct actions (same flags, extra value and skill id = same script and sprite, so area
variants that share them are measured once), the action script each one runs (func_02068034) and that
script's step list (16-byte steps, func_02031514). The emulator plans that record them are built in
dsde.enemy_anims_plans; runner and analysis: dsde.enemy_anims_run.

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
    CARD_ITEM_BASE,
    ENEMY_ROW_SIZE,
    ENEMY_TABLE,
    FIRST_BOSS_ROW,
    read_names,
    species_of,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARM9_BIN = PROJECT_ROOT / "extract" / "arm9" / "arm9.bin"
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
ALWAYS = 100  # chances are out of 100

STEP_SIZE = 0x10
STEP_END = 0x80000000
STEP_KIND_MASK = 3
STEP_KINDS = {0: "instant", 1: "anim", 2: "fixed", 3: "never"}
MAX_STEPS = 64


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
