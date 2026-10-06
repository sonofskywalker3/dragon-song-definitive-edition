"""Gad's Express (design 9): the earliest "town count" at which each job template can be completed.

Town count = number of set destination unlock bytes at 0x020B486A, the value that drives an office's rank
(min(4, town count)). A template is obtainable at town count n when every item it asks for is sold in a
town counted by then, or dropped by a regular enemy of an area group the player can fight in by then.
"Package supplied" jobs need no items and are obtainable from count 1. Bosses and chests are ignored.

How the tables below were derived (all from the vanilla ARM9, see docs/re-mp-jobs-rings.md 2.5):
    - Town order. func_02041d38 sets unlock byte i when the player enters a town hub map 0x11D + k. The hub
      exit lists (0x020A3B20 + (map - 0x104) * 0xC: u32 list, s16 count; 0xC-byte exits whose last u16 is
      a place-name label) name each hub. TOWNS is the story order (docs/story-party-timeline.md).
    - Area groups. The dungeon group table at 0x02091C78 gives each map's group (battle context +0x00);
      the overworld exit lists name each group's maps. AREA_TOWN_COUNT is the count at which the player
      first fights there.
    - Regular enemy rows of a group: boss_exp.rom_area_rows (formation pools + lead rows).

Usage:
    uv run python -m dsde.gad_jobs                  # per-office summary
    uv run python -m dsde.gad_jobs --frontier-open  # count the Frontier as open after Ignatius
"""

import argparse
import logging
import struct
from dataclasses import dataclass
from pathlib import Path

from dsde.boss_exp import rom_area_rows
from dsde.enemies import ARM9_BASE, DEFAULT_BIN, read_enemies, read_names

log = logging.getLogger(__name__)

TEMPLATE_TABLE = 0x020A8E3C
TEMPLATE_SIZE = 0x1A
TEMPLATE_COUNT = 241  # entry 0 is empty
TEMPLATE_ITEMS = 5
TEMPLATE_COUNTS_OFFSET = 0x0A
TEMPLATE_PACKAGE_OFFSET = 0x14
TEMPLATE_RANK_OFFSET = 0x16
PACKAGE_SUPPLIED = 1
COUNT_RAW_SHIFT = 2  # count = raw / 4 + 1

SHOP_LIST_ENTRIES = 30
SHOP_LIST_SIZE = 0x3C
POOL_ENTRIES = 40
NO_ITEM = 0

MAX_RANK = 4
FIRST_TOWN_COUNT = 1
LAST_TOWN_COUNT = 7
MIN_OBTAINABLE_JOBS = 3  # design 9: up to 3 obtainable jobs plus one future job
# The airship (after the Blue Dragon) reopens the Frontier; that is after the 7th town (Rebric).
FRONTIER_REOPEN_COUNT = LAST_TOWN_COUNT
NEVER = LAST_TOWN_COUNT + 1  # sorts after every real town count


@dataclass(frozen=True)
class Town:
    name: str
    hub_maps: tuple[int, ...]  # maps 0x11D + k whose entry sets the unlock byte
    scripts: tuple[int, ...]
    count: int  # town count right after its first entry


# Destination towns in the order their hubs are first entered. Lind Village (hub 0x124, script 010) sets no
# unlock byte and does not count.
TOWNS: tuple[Town, ...] = (
    Town("Port Searis", (0x11D,), (1,), 1),  # game start
    Town("Perit Village", (0x120,), (3,), 2),  # through Thieves' Woods
    Town(
        "Healriz", (0x11E, 0x11F), (4, 5), 3
    ),  # after Delrich Temple; 0x11F is San Coliseum's side
    Town("Port Olbeage", (0x121,), (7,), 4),  # ferry after the Coliseum
    Town(
        "Leephon City", (0x122, 0x123), (8, 9), 5
    ),  # through the Cathedral; 0x123 is Zethos Castle
    Town(
        "Noapeace", (0x125,), (11,), 6
    ),  # dragon trials, through Meryod Submarine Cave
    Town("Rebric Village", (0x126,), (12,), 7),  # through Moto Rainforest
)

LIND_COUNT = 5  # Lind Village (Frontier) is entered between Leephon and Noapeace


@dataclass(frozen=True)
class Shop:
    town: str
    list_base: int
    slots: int
    count: int
    frontier: bool = False


# docs/re-mp-jobs-rings.md 1.4: every slot of each town's lists (1 weapons, 2 armor, 3 items, 4-6 sundries).
SHOPS: tuple[Shop, ...] = (
    Shop("Port Searis", 0x0209D914, 3, 1),
    Shop("Perit Village", 0x0209D644, 3, 2),
    Shop("Healriz", 0x0209D6F8, 3, 3),
    Shop("Port Olbeage", 0x0209DAB8, 6, 4),
    Shop("Leephon City (accessories, map 0xE0)", 0x0209D608, 1, 5),
    Shop("Lind Village", 0x0209D9C8, 4, LIND_COUNT, frontier=True),
    Shop("Noapeace", 0x0209D7AC, 3, 6),
    Shop("Rebric Village", 0x0209D860, 3, 7),
)


@dataclass(frozen=True)
class Area:
    name: str
    count: int
    frontier: bool = False  # closed from the Ignatius fight until the airship


# Area group -> where it is and the town count at which it is first fought in. Enemy minimum levels
# (docs/re-enemies.md) rise with the count: 0-8, 4-6, 10, 10, then 11 to 25, 25 to 29, 32 to 37.
AREA_TOWN_COUNT: dict[int, Area] = {
    0: Area("Thieves' Woods, maps 0-4", 1),
    1: Area("Delrich Temple, maps 5-19", 2),
    3: Area("Roland Forest, maps 31-34", 3),
    18: Area("Cathedral of Althena, maps 140-150", 4),
    2: Area("Sungrid Bridge, maps 20-30", 5, frontier=True),
    6: Area("Underground Tunnel and Guystole Mine, maps 45-52", 5, frontier=True),
    7: Area("Sandra Desert, maps 53-57", 5, frontier=True),
    8: Area("Elda Canyon, maps 58-60", 5, frontier=True),
    9: Area("Vile Castle first visit, maps 61-84", 5, frontier=True),
    4: Area("Barrel Desert, maps 35-37", 5),
    12: Area("Red Dragon Cave, maps 94-99", 5),
    13: Area("White Dragon Cave, maps 100-105", 5),
    5: Area("Meryod Submarine Cave, maps 38-44", 5),
    10: Area("Valley of Neza, maps 85-87", 6),
    14: Area("Black Dragon Cave, maps 106-111", 6),
    11: Area("Moto Rainforest, maps 88-93", 6),
    15: Area("Blue Dragon Cave, maps 112-120", 7),
    16: Area("Tower of Kirlis, maps 121-128", 7),
    17: Area("Negri Ocean Lab, maps 129-139", 7),
    19: Area("Vile Castle return (flag 0xC9), maps 61-84", 7),
}


@dataclass(frozen=True)
class Office:
    map_id: int
    town: str
    pool: int  # 40 u16 template indices

    @property
    def count(self) -> int:
        return next(t.count for t in TOWNS if t.name == self.town)


OFFICES: tuple[Office, ...] = (
    Office(0x9A, "Port Searis", 0x0209DEB4),
    Office(0xA9, "Perit Village", 0x0209DF04),
    Office(0xBD, "Healriz", 0x0209DF54),
    Office(0xCA, "Port Olbeage", 0x0209DDC4),
    Office(0xEC, "Noapeace", 0x0209DE14),
    Office(0xFC, "Rebric Village", 0x0209DE64),
)


@dataclass(frozen=True)
class Template:
    index: int
    items: tuple[tuple[int, int], ...]  # (item id, count)
    package: bool
    rank: int


def _offset(address: int) -> int:
    return address - ARM9_BASE


def read_templates(data: bytes) -> list[Template]:
    templates = []
    for index in range(1, TEMPLATE_COUNT):
        base = _offset(TEMPLATE_TABLE) + index * TEMPLATE_SIZE
        items = struct.unpack_from(f"<{TEMPLATE_ITEMS}H", data, base)
        raw = struct.unpack_from(
            f"<{TEMPLATE_ITEMS}H", data, base + TEMPLATE_COUNTS_OFFSET
        )
        package = (
            struct.unpack_from("<H", data, base + TEMPLATE_PACKAGE_OFFSET)[0]
            == PACKAGE_SUPPLIED
        )
        rank = data[base + TEMPLATE_RANK_OFFSET]
        pairs = tuple(
            (item, (count >> COUNT_RAW_SHIFT) + 1)
            for item, count in zip(items, raw, strict=True)
            if item != NO_ITEM
        )
        templates.append(Template(index, pairs, package, rank))
    return templates


def read_pool(data: bytes, office: Office) -> tuple[int, ...]:
    return struct.unpack_from(f"<{POOL_ENTRIES}H", data, _offset(office.pool))


def _lower(sources: dict[int, int], item: int, count: int) -> None:
    sources[item] = min(sources.get(item, NEVER), count)


def item_town_counts(data: bytes, frontier_closed: bool = True) -> dict[int, int]:
    """Item id -> earliest town count at which a shop sells it or a regular enemy drops it.

    With frontier_closed, Frontier sources (Lind's shop, the Frontier dungeons) count from
    FRONTIER_REOPEN_COUNT: no Gad office is in the Frontier, and after the Ignatius fight it is closed
    until the airship, so at count 5 an office visit never has them at hand unless farmed earlier.
    """
    sources: dict[int, int] = {}
    for shop in SHOPS:
        count = (
            FRONTIER_REOPEN_COUNT if shop.frontier and frontier_closed else shop.count
        )
        for slot in range(shop.slots):
            entries = struct.unpack_from(
                f"<{SHOP_LIST_ENTRIES}H",
                data,
                _offset(shop.list_base) + slot * SHOP_LIST_SIZE,
            )
            for item in entries:
                if item != NO_ITEM:
                    _lower(sources, item, count)
    enemies = read_enemies(data)
    for group, area in AREA_TOWN_COUNT.items():
        count = (
            FRONTIER_REOPEN_COUNT if area.frontier and frontier_closed else area.count
        )
        for row in rom_area_rows(data, group):
            for drop in enemies[row].drops:
                if drop.chance > 0:
                    _lower(sources, drop.item, count)
    return sources


def template_town_counts(
    data: bytes, frontier_closed: bool = True
) -> dict[int, int | None]:
    """Template index -> earliest town count (1..7) at which all its items are obtainable.

    None means some item has no shop or regular-enemy source (boss, chest or event only).
    """
    sources = item_town_counts(data, frontier_closed)
    result: dict[int, int | None] = {}
    for template in read_templates(data):
        if template.package:
            result[template.index] = FIRST_TOWN_COUNT
            continue
        counts = [sources.get(item) for item, _ in template.items]
        result[template.index] = (
            None if None in counts else max(counts, default=FIRST_TOWN_COUNT)
        )
    return result


def office_summary(
    data: bytes, frontier_closed: bool = True
) -> dict[int, list[tuple[int, int]]]:
    """Office map -> per town count 1..7: (obtainable, rank-allowed) templates of its pool."""
    earliest = template_town_counts(data, frontier_closed)
    ranks = {t.index: t.rank for t in read_templates(data)}
    summary = {}
    for office in OFFICES:
        pool = read_pool(data, office)
        row = []
        for count in range(FIRST_TOWN_COUNT, LAST_TOWN_COUNT + 1):
            rank = min(MAX_RANK, count)
            allowed = [t for t in pool if ranks[t] <= rank]
            ready = [t for t in allowed if (earliest[t] or NEVER) <= count]
            row.append((len(ready), len(allowed)))
        summary[office.map_id] = row
    return summary


def _log_summary(data: bytes, frontier_closed: bool) -> None:
    summary = office_summary(data, frontier_closed)
    header = " | ".join(str(c) for c in range(FIRST_TOWN_COUNT, LAST_TOWN_COUNT + 1))
    log.info("| Office | Town (count) | %s |", header)
    log.info("|---|---|%s", "---|" * LAST_TOWN_COUNT)
    problems = []
    for office in OFFICES:
        cells = []
        for count, (ready, allowed) in enumerate(summary[office.map_id], start=1):
            reachable = count >= office.count
            cell = f"{ready}/{allowed}" if reachable else f"({ready}/{allowed})"
            if reachable and ready < MIN_OBTAINABLE_JOBS:
                cell += " !"
                problems.append((office, count, ready))
            cells.append(cell)
        log.info(
            "| 0x%X | %s (%d) | %s |",
            office.map_id,
            office.town,
            office.count,
            " | ".join(cells),
        )
    for office, count, ready in problems:
        log.info(
            "office 0x%X %s: only %d obtainable at town count %d",
            office.map_id,
            office.town,
            ready,
            count,
        )


def _log_templates(data: bytes, frontier_closed: bool) -> None:
    names = read_names(data)
    earliest = template_town_counts(data, frontier_closed)
    for template in read_templates(data):
        items = ", ".join(f"{names[i]} x{n}" for i, n in template.items)
        log.info(
            "template %3d rank %d count %s: %s",
            template.index,
            template.rank,
            earliest[template.index],
            "Package" if template.package else items,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.gad_jobs")
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    parser.add_argument(
        "--frontier-open",
        action="store_true",
        help="count Frontier sources at the count they are first reached (5)",
    )
    parser.add_argument(
        "--templates", action="store_true", help="also list every template"
    )
    args = parser.parse_args()
    data = args.bin.read_bytes()
    frontier_closed = not args.frontier_open
    if args.templates:
        _log_templates(data, frontier_closed)
    _log_summary(data, frontier_closed)


if __name__ == "__main__":
    main()
