"""Enemy stat, action and drop tables in the ARM9 binary, and the game's level scaling rules.

See docs/re-enemies.md for how each field was identified.

Enemy record (ENEMY_TABLE, ENEMY_ROW_SIZE bytes per row, indexed by enemy row id):
    +0x00 u32  flags (bit 31 boss, bit 30 stagger gauge, bits 0-1 AI aggression class)
    +0x04 s16 x8  stats at level 0: max HP, max MP, attack, defense, agility, intelligence,
                  dexterity, luck (same order as the character record at 0x020B4664 + 0x14)
    +0x14 u32  Althena Conduct (EXP) at level 0
    +0x18 s16 x8  the same stats at level 98
    +0x28 u32  EXP at level 98
    +0x2C s16 x4  cumulative action chances out of 100
    +0x34 4 x {u32 action flags, u16 extra, s16 skill id}   bit 27 = steal, bit 26 = break gear

Drop record (DROP_TABLE, DROP_ROW_SIZE bytes per row, same row id):
    +0x00 u16 x3  chances out of 1000 for slots 0..2 (cumulative for normal enemies, independent for bosses)
    +0x06 u16  unused
    +0x08 u16  item for slot 0
    +0x0A u16  item for slot 1
    slot 2 is always the enemy's card.

Usage:
    uv run python -m dsde.enemies                 # markdown table, stats as level 0 - level 98
    uv run python -m dsde.enemies --level 20      # stats an enemy has at enemy level 20
"""

import argparse
import logging
import struct
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

ARM9_BASE = 0x02000000
DEFAULT_BIN = Path("extract/arm9/arm9.bin")

ENEMY_TABLE = 0x02097CE4
ENEMY_ROW_SIZE = 0x54
ENEMY_ROWS = 157
DROP_TABLE = 0x02097588
DROP_ROW_SIZE = 0x0C
NAME_BLOCK = 0x020A7C2E
NAME_COUNT = 417
TERMINATOR = 0xFF

STAT_NAMES = ("HP", "MP", "ATK", "DEF", "AGI", "INT", "DEX", "LUCK")
STAT_COUNT = len(STAT_NAMES)
ACTION_COUNT = 4
MAX_SCALE_LEVEL = 98

FIRST_BOSS_ROW = 0x88
NORMAL_ROWS_PER_SPECIES = 4
LAST_NORMAL_SPECIES = 0x21
BOSS_SPECIES_OFFSET = 0x66
CARD_ITEM_BASE = 0xD8
BOSS_CARD_OFFSET = 0x72
ORB_GUARDIAN_ROW = 0x8D
DROP_ROLL_RANGE = 1000
DROP_SLOTS = 3
CARD_SLOT = 2

FLAG_BOSS = 0x80000000
FLAG_STAGGER = 0x40000000
ACTION_STEAL = 0x08000000
ACTION_BREAK = 0x04000000

AREA_LEVEL_SPAN_LOW = 20
AREA_LEVEL_LOW_LIMIT = 20
AREA_LEVEL_SPAN_HIGH = 35
AREA_LEVEL_CAP = 80
PARTY_SPREAD_SHIFT = 3

CHAR_SPACE = 0x00
CHAR_UPPER_FIRST = 0x02
CHAR_UPPER_LAST = 0x1B
CHAR_LOWER_FIRST = 0x3A
CHAR_LOWER_LAST = 0x53
CHAR_DIGIT_FIRST = 0x30
CHAR_DIGIT_LAST = 0x39
CHAR_APOSTROPHE = 0x54


@dataclass(frozen=True)
class Action:
    flags: int
    extra: int
    skill: int
    chance: int

    @property
    def steals(self) -> bool:
        return bool(self.flags & ACTION_STEAL)

    @property
    def breaks(self) -> bool:
        return bool(self.flags & ACTION_BREAK)


@dataclass(frozen=True)
class Drop:
    item: int
    chance: int


@dataclass(frozen=True)
class Enemy:
    row: int
    name: str
    flags: int
    stats_min: tuple[int, ...]
    stats_max: tuple[int, ...]
    exp_min: int
    exp_max: int
    actions: tuple[Action, ...]
    drops: tuple[Drop, ...]

    @property
    def boss(self) -> bool:
        return bool(self.flags & FLAG_BOSS)

    def stats_at(self, level: int) -> dict[str, int]:
        """Stats and EXP at an enemy level, as func_02069ad8 computes them."""
        stats = {
            name: scale_stat(lo, hi, level)
            for name, lo, hi in zip(
                STAT_NAMES, self.stats_min, self.stats_max, strict=True
            )
        }
        stats["EXP"] = scale_exp(self.exp_min, self.exp_max, level)
        return stats


def decode_text(raw: bytes) -> str:
    """Decode the game's single-byte text encoding (letters, digits, space, apostrophe)."""
    out = []
    for byte in raw:
        if byte == CHAR_SPACE:
            out.append(" ")
        elif CHAR_UPPER_FIRST <= byte <= CHAR_UPPER_LAST:
            out.append(chr(ord("A") + byte - CHAR_UPPER_FIRST))
        elif CHAR_LOWER_FIRST <= byte <= CHAR_LOWER_LAST:
            out.append(chr(ord("a") + byte - CHAR_LOWER_FIRST))
        elif CHAR_DIGIT_FIRST <= byte <= CHAR_DIGIT_LAST:
            out.append(chr(byte))
        elif byte == CHAR_APOSTROPHE:
            out.append("'")
        else:
            out.append(f"{{{byte:02x}}}")
    return "".join(out)


def read_names(data: bytes) -> list[str]:
    """Item, card and character names in ID order (item 216 + species is that enemy's card)."""
    start = NAME_BLOCK - ARM9_BASE
    names = []
    pos = start
    for _ in range(NAME_COUNT):
        end = data.index(TERMINATOR, pos)
        names.append(decode_text(data[pos:end]).strip())
        pos = end + 1
    return names


def species_of(row: int) -> int:
    """Species index of an enemy row (func_0206892c): four rows per normal species, one per boss."""
    if row < FIRST_BOSS_ROW:
        return min(row // NORMAL_ROWS_PER_SPECIES, LAST_NORMAL_SPECIES)
    return row - BOSS_SPECIES_OFFSET


def card_item(row: int) -> int:
    """Card item id dropped by slot 2 (func_02069dd0 for normal rows, func_02069f34 for bosses)."""
    if row < FIRST_BOSS_ROW:
        return row // NORMAL_ROWS_PER_SPECIES + CARD_ITEM_BASE
    return row + BOSS_CARD_OFFSET


def scale_stat(lo: int, hi: int, level: int) -> int:
    """func_02069d7c: lo + (hi - lo) * level / 98 in float, truncated; level <= 0 gives lo."""
    if level <= 0:
        return lo
    return lo + int((hi - lo) * level / MAX_SCALE_LEVEL)


def scale_exp(lo: int, hi: int, level: int) -> int:
    """func_02069d54: integer form of the same interpolation."""
    return lo + int((hi - lo) * level / MAX_SCALE_LEVEL)


def area_level_max(area_min: int) -> int:
    """Upper clamp for enemy level that func_0204f8b0 derives from the area's minimum."""
    if area_min < AREA_LEVEL_LOW_LIMIT:
        top = area_min + AREA_LEVEL_SPAN_LOW
    else:
        top = min(area_min * 2, area_min + AREA_LEVEL_SPAN_HIGH)
    top = min(top, AREA_LEVEL_CAP)
    return max(top, area_min)


def enemy_level_range(party_max_level: int, area_min: int) -> tuple[int, int]:
    """Lowest and highest enemy level func_02054494 can roll for a party and area."""
    spread = max(1, party_max_level >> PARTY_SPREAD_SHIFT)
    lo = party_max_level - spread if spread <= party_max_level else party_max_level
    hi = party_max_level
    top = area_level_max(area_min)
    return (min(max(lo, area_min), top), min(max(hi, area_min), top))


def read_enemies(data: bytes) -> list[Enemy]:
    names = read_names(data)
    enemies = []
    for row in range(ENEMY_ROWS):
        base = ENEMY_TABLE - ARM9_BASE + row * ENEMY_ROW_SIZE
        flags = struct.unpack_from("<I", data, base)[0]
        stats_min = struct.unpack_from(f"<{STAT_COUNT}h", data, base + 0x04)
        exp_min = struct.unpack_from("<I", data, base + 0x14)[0]
        stats_max = struct.unpack_from(f"<{STAT_COUNT}h", data, base + 0x18)
        exp_max = struct.unpack_from("<I", data, base + 0x28)[0]
        cumulative = struct.unpack_from(f"<{ACTION_COUNT}h", data, base + 0x2C)
        actions = []
        previous = 0
        for index in range(ACTION_COUNT):
            action_flags, extra, skill = struct.unpack_from(
                "<IHh", data, base + 0x34 + index * 8
            )
            chance = cumulative[index] - previous
            previous = cumulative[index]
            if action_flags:
                actions.append(Action(action_flags, extra, skill, chance))
        enemies.append(
            Enemy(
                row=row,
                name=names[CARD_ITEM_BASE + species_of(row)],
                flags=flags,
                stats_min=stats_min,
                stats_max=stats_max,
                exp_min=exp_min,
                exp_max=exp_max,
                actions=tuple(actions),
                drops=_read_drops(data, row),
            )
        )
    return enemies


def _read_drops(data: bytes, row: int) -> tuple[Drop, ...]:
    """Per-slot item and chance out of 1000, following func_02069e00 / func_02069f34."""
    base = DROP_TABLE - ARM9_BASE + row * DROP_ROW_SIZE
    chances = struct.unpack_from(f"<{DROP_SLOTS}H", data, base)
    items = struct.unpack_from("<2H", data, base + 0x08)
    slot_items = (*items, card_item(row))
    drops = []
    previous = 0
    for slot in range(DROP_SLOTS):
        if row < FIRST_BOSS_ROW:
            chance = max(chances[slot] - previous, 0)
            previous = max(previous, chances[slot])
        else:
            chance = chances[slot]
        drops.append(Drop(slot_items[slot], chance))
    return tuple(drops)


def _action_text(action: Action, names: list[str]) -> str:
    tags = []
    if action.steals:
        tags.append("STEAL")
    if action.breaks:
        tags.append("BREAK")
    tag = f" {'/'.join(tags)}" if tags else ""
    return f"{action.chance}% {action.flags:#x}/{action.extra}/{action.skill}{tag}"


def markdown_table(enemies: list[Enemy], names: list[str], level: int | None) -> str:
    header = ["row", "name", "flags", "stats"]
    header += ["EXP", "actions", "drops (per 1000)"]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for enemy in enemies:
        if level is None:
            stats = " ".join(
                f"{n} {lo}-{hi}"
                for n, lo, hi in zip(
                    STAT_NAMES, enemy.stats_min, enemy.stats_max, strict=True
                )
            )
            exp = f"{enemy.exp_min}-{enemy.exp_max}"
        else:
            scaled = enemy.stats_at(level)
            exp = str(scaled.pop("EXP"))
            stats = " ".join(f"{n} {v}" for n, v in scaled.items())
        actions = "; ".join(_action_text(a, names) for a in enemy.actions)
        drops = "; ".join(
            f"{names[d.item]} {d.chance}" for d in enemy.drops if d.chance
        )
        cells = [
            str(enemy.row),
            enemy.name,
            f"{enemy.flags:#010x}",
            stats,
            exp,
            actions,
            drops,
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.enemies")
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    parser.add_argument("--level", type=int, help="show stats at this enemy level")
    parser.add_argument(
        "--out", type=Path, help="write the table here instead of logging it"
    )
    args = parser.parse_args()
    data = args.bin.read_bytes()
    names = read_names(data)
    table = markdown_table(read_enemies(data), names, args.level)
    if args.out:
        args.out.write_text(table + "\n", encoding="utf-8")
        log.info("wrote %s", args.out)
    else:
        log.info("%s", table)


if __name__ == "__main__":
    main()
