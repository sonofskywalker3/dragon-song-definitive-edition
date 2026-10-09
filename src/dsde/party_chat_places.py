"""Places for party chat: named map id ranges (docs/re-party-chat.md).

Ranges come from the map table (0x02091D18, byte +2 = the map's script, one script per town or area)
and the area groups (table 0x02091C78); names from docs/re-mp-jobs-rings.md and docs/re-field-battle.md.
Single maps (Jian's room and so on) are from the Port Searis research in docs/re-field-battle.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Place:
    """Where a chat can play: one or more inclusive map id ranges."""

    name: str
    maps: tuple[tuple[int, int], ...]

    def __add__(self, other: "Place") -> "Place":
        return Place(f"{self.name} or {other.name}", self.maps + other.maps)


def one_map(name: str, map_id: int) -> Place:
    return Place(name, ((map_id, map_id),))


def maps(name: str, first: int, last: int) -> Place:
    return Place(name, ((first, last),))


# Fields and dungeons (area groups, maps 0..150; enemy maps)
THIEVES_WOODS = maps("Thieves' Woods", 0, 4)
DELRICH_TEMPLE = maps("Delrich Temple", 5, 19)
SUNGRID_BRIDGE = maps("Sungrid Bridge", 20, 30)
ROLAND_FOREST = maps("Roland Forest", 31, 34)
BARREL_DESERT = maps("Barrel Desert", 35, 37)
MERYOD_CAVE = maps("Meryod Submarine Cave", 38, 44)
UNDERGROUND_TUNNEL = maps("Underground Tunnel and Guystole Mine", 45, 52)
SANDRA_DESERT = maps("Sandra Desert", 53, 57)
ELDA_CANYON = maps("Elda Canyon", 58, 60)
VILE_CASTLE = maps("Vile Castle", 61, 84)
VALLEY_OF_NEZA = maps("Valley of Neza", 85, 87)
MOTO_RAINFOREST = maps("Moto Rainforest", 88, 93)
RED_DRAGON_CAVE = maps("Red Dragon Cave", 94, 99)
WHITE_DRAGON_CAVE = maps("White Dragon Cave", 100, 105)
BLACK_DRAGON_CAVE = maps("Black Dragon Cave", 106, 111)
BLUE_DRAGON_CAVE = maps("Blue Dragon Cave", 112, 120)
TOWER_OF_KIRLIS = maps("Tower of Kirlis", 121, 128)
NEGRI_OCEAN_LAB = maps("Negri Ocean Lab", 129, 139)
CATHEDRAL_OF_ALTHENA = maps("Cathedral of Althena", 140, 150)

# Towns (maps 151 and up; one script per town)
PORT_SEARIS = maps("Port Searis", 151, 165)
PERIT_VILLAGE = maps("Perit Village", 166, 175)
HEALRIZ = maps("Healriz", 176, 185)
SAN_COLISEUM = maps("San Coliseum side of Healriz", 186, 198)
PORT_OLBEAGE = maps("Port Olbeage", 199, 212)
LEEPHON_CITY = maps("Leephon City", 213, 222)
ZETHOS_CASTLE = maps("Zethos Castle", 223, 225)
LIND_VILLAGE = maps("Lind Village", 226, 232)
NOAPEACE = maps("Noapeace", 233, 248)
REBRIC_VILLAGE = maps("Rebric Village", 249, 256)

# Single maps in Port Searis (docs/re-field-battle.md)
INN_LOBBY = one_map("the inn lobby", 155)
JACKS_HOUSE = one_map("Jack's house", 159)
INN_HALL = one_map("the inn hall", 160)
JIANS_ROOM = one_map("Jian's room", 163)
FOUNTAIN_SQUARE = one_map("Fountain Square", 164)

ANYWHERE = None
