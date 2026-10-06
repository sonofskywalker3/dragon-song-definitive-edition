"""Boss EXP (design 2): each boss is worth BOSS_EXP_FACTOR regular enemies of the place it is fought in.

A boss's EXP fields (level 0 at +0x14, level 98 at +0x28) become BOSS_EXP_FACTOR times the average of the
same fields over the regular enemy rows of the boss's area, so the boss stays linear in level and pays
about ten of that area's regulars at whatever level the fight rolls. See docs/boss-exp.md.

Where the rows come from (all read from the vanilla ARM9, see docs/boss-exp.md):
    - Boss battles are started by script op 0x10 type 3 (`10 00 03 00 <id>`); the map table at 0x02091D18
      (byte +2) says which maps run each script, and the dungeon group table at 0x02091C78 gives the
      area group of those maps (battle context +0x00).
    - A regular battle in area group g draws its enemies from two lists of 8 rows at
      [FORMATION_POOLS + 4 * g] (func_0202b3f0) plus the touched symbol's lead row, a pair of s16 at
      LEAD_ROWS + 4 * g (func_0202b948). AREA_REGULAR_ROWS below is that union, written out.

Usage:
    uv run python -m dsde.boss_exp     # check the tables against the ROM, print the per-boss table
"""

import argparse
import logging
import struct
from dataclasses import dataclass
from pathlib import Path

from dsde.enemies import (
    ARM9_BASE,
    DEFAULT_BIN,
    FIRST_BOSS_ROW,
    Enemy,
    read_enemies,
    scale_exp,
)

log = logging.getLogger(__name__)

BOSS_EXP_FACTOR = 10
FORMATION_POOLS_PTR = 0x0202B6A8  # literal pool word of func_0202b3f0
LEAD_ROWS_PTR = 0x0202BBAC  # literal pool word of func_0202b948
POOL_SLOTS = 16  # two lists (front, back) of 8 s16 rows, -1 = empty
LEAD_SLOTS = 2
EMPTY_ROW = -1
MAX_LEVEL = 98

# Regular enemy rows per area group (union of the group's formation pools and lead rows).
# Only the groups a boss uses are listed; `check_tables` compares them with the ROM.
AREA_REGULAR_ROWS: dict[int, tuple[int, ...]] = {
    1: (1, 9, 40, 45, 72, 88, 120),  # Delrich Temple, maps 5 to 19
    3: (
        10,
        12,
        16,
        24,
        46,
        49,
        53,
        69,
    ),  # maps 31 to 34 (script 014, Armored Boar's dungeon)
    8: (78, 90, 97, 118, 122, 126, 130),  # Elda Canyon area 2, maps 58 to 60
    9: (
        86,
        97,
        114,
        118,
        122,
        126,
        130,
        134,
    ),  # Vile Castle, maps 61 to 84, first visit
    12: (27, 31, 35, 38, 81, 86, 92),  # Red Dragon Cave, maps 94 to 99
    13: (
        11,
        14,
        18,
        23,
        42,
        59,
        63,
        82,
        93,
        102,
        111,
    ),  # White Dragon Cave, maps 100 to 105
    14: (15, 19, 39, 43, 47, 83, 91, 94),  # Black Dragon Cave, maps 106 to 111
    15: (7, 58, 62, 66, 87, 95, 101, 107),  # Blue Dragon Cave, maps 112 to 120
    18: (84, 96, 112, 116, 121, 124, 128, 132),  # Cathedral of Althena, maps 140 to 150
    19: (
        85,
        98,
        115,
        119,
        123,
        127,
        131,
        135,
    ),  # Vile Castle after story flag 0xC9 (the return)
}


@dataclass(frozen=True)
class BossArea:
    group: int
    place: str
    fight_level: (
        int  # lowest enemy level of the fight (area minimum or the boss override)
    )


# Boss row -> the area group whose regular rows set its EXP.
BOSS_AREAS: dict[int, BossArea] = {
    136: BossArea(
        1, "Sasquatch: Delrich Temple (script 013, event battles 1, 0x13..0x15)", 7
    ),
    137: BossArea(3, "Armored Boar: script 014 dungeon, maps 31 to 34", 10),
    # San Coliseum (script 005, a town): no encounters; nearest dungeon before it is group 3
    138: BossArea(3, "Raft: San Coliseum, uses the script 014 dungeon", 10),
    139: BossArea(3, "Sharif: San Coliseum, uses the script 014 dungeon", 10),
    140: BossArea(3, "Moran: San Coliseum, uses the script 014 dungeon", 10),
    141: BossArea(18, "Deuce: Cathedral of Althena (script 015)", 10),
    142: BossArea(18, "Gronk: Cathedral of Althena (script 015)", 10),
    # Zethos Castle in Leephon (script 009, a town): nearest dungeon before it is the Cathedral
    143: BossArea(18, "Zethos: Leephon, uses the Cathedral of Althena", 10),
    144: BossArea(8, "Caucus: Elda Canyon (script 020)", 16),
    145: BossArea(8, "Orcus: Elda Canyon, joins the Caucus fight", 16),
    146: BossArea(8, "Morus: Elda Canyon, joins the Caucus fight", 16),
    147: BossArea(12, "Red Dragon: Red Dragon Cave (script 017)", 23),
    148: BossArea(13, "White Dragon: White Dragon Cave (script 006)", 24),
    149: BossArea(14, "Black Dragon: Black Dragon Cave (script 022)", 28),
    150: BossArea(15, "Blue Dragon: Blue Dragon Cave (script 023)", 36),
    # func_020297d4 chains event battle 10 (Black Dragon) straight into 0x19 (Dark Jian)
    151: BossArea(14, "Dark Jian: Black Dragon Cave, follows the Black Dragon", 28),
    152: BossArea(19, "Gideon: Vile Castle return (script 021, after flag 0xC9)", 40),
    153: BossArea(19, "Gideon 2: Vile Castle return", 42),
    154: BossArea(19, "Gideon 3: Vile Castle return", 42),
    155: BossArea(9, "Ignatius: Vile Castle Grand Hall, first visit (script 021)", 97),
}


def _word(data: bytes, address: int) -> int:
    return struct.unpack_from("<I", data, address - ARM9_BASE)[0]


def rom_area_rows(data: bytes, group: int) -> tuple[int, ...]:
    """The regular rows a battle in area group `group` can contain, read from the formation tables."""
    pool = _word(data, _word(data, FORMATION_POOLS_PTR) + 4 * group)
    rows = struct.unpack_from(f"<{POOL_SLOTS}h", data, pool - ARM9_BASE)
    leads = struct.unpack_from(
        f"<{LEAD_SLOTS}h", data, _word(data, LEAD_ROWS_PTR) + 4 * group - ARM9_BASE
    )
    return tuple(sorted({row for row in (*rows, *leads) if row != EMPTY_ROW}))


def check_tables(data: bytes) -> None:
    """Raise ValueError if a written-out row list differs from the ROM or holds a boss row."""
    for group, rows in AREA_REGULAR_ROWS.items():
        actual = rom_area_rows(data, group)
        if actual != rows:
            raise ValueError(f"area group {group}: table {rows}, ROM {actual}")
        if any(row >= FIRST_BOSS_ROW for row in rows):
            raise ValueError(f"area group {group} lists a boss row")
    for row, area in BOSS_AREAS.items():
        if area.group not in AREA_REGULAR_ROWS:
            raise ValueError(f"boss row {row}: no regular rows for group {area.group}")


def boss_exp(enemies: list[Enemy]) -> dict[int, tuple[int, int]]:
    """Boss row -> (EXP at level 0, EXP at level 98): BOSS_EXP_FACTOR x its area's regular average."""
    values = {}
    for row, area in BOSS_AREAS.items():
        regular = [enemies[r] for r in AREA_REGULAR_ROWS[area.group]]
        exp_min = round(
            BOSS_EXP_FACTOR * sum(e.exp_min for e in regular) / len(regular)
        )
        exp_max = round(
            BOSS_EXP_FACTOR * sum(e.exp_max for e in regular) / len(regular)
        )
        values[row] = (exp_min, exp_max)
    return values


def markdown_table(enemies: list[Enemy]) -> str:
    lines = [
        "| Row | Boss and place | Area group | EXP level 0 | EXP level 98 | Fight level | EXP there |",
        "|---|---|---|---|---|---|---|",
    ]
    for row, (exp_min, exp_max) in boss_exp(enemies).items():
        area = BOSS_AREAS[row]
        at_fight = scale_exp(exp_min, exp_max, min(area.fight_level, MAX_LEVEL))
        lines.append(
            f"| {row} | {area.place} | {area.group} | {exp_min} | {exp_max} "
            f"| {area.fight_level} | {at_fight} |"
        )
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.boss_exp")
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    args = parser.parse_args()
    data = args.bin.read_bytes()
    check_tables(data)
    log.info("area tables match the ROM")
    log.info("%s", markdown_table(read_enemies(data)))


if __name__ == "__main__":
    main()
