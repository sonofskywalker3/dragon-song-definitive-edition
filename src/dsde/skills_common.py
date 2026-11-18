"""Addresses, record layouts, and small helpers shared by the skills feature modules (feat_skills_*.py)."""

from pathlib import Path

from dsde.jp_hint_pairs import END, USA_TABLE
from dsde.patching import AsmPatch

VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"

SPELL_TABLE = 0x02094978  # 0x0C per spell: u32 flags, u32 MP cost, u8 Lucia level, u8 Flora level, u16 row
SPELL_ENTRY_SIZE = 0x0C
VANILLA_SPELL_COUNT = 0x26  # the loops over the table stop here in the original
FLAG_BATTLE = 0x2  # usable in battle
RING_FLAGS = 0x00F00000  # Dragon Magic: one bit per ring
NEVER = 0xFF  # level byte: never learned

# Battle string list: u16 offsets from the text base; a spell's name is entry spell + 0x35
STRING_OFFSETS = 0x020A41DC
STRING_BASE = 0x020A42E4
SPELL_NAME_FIRST = 0x35
STRING_NO_EFFECT = 99  # our "No effect!" (feat_skills_table.py)

# Battlers and their stat records
BATTLERS_PTR = 0x020B8640
BATTLER_SIZE = 0x12C
BATTLER_RECORD = 0x10  # stat record index
BATTLER_ENEMY = 8  # flag bit in battler + 0
BATTLER_ROW = 0x04  # an enemy's row in the enemy table (a party member's character id)
BATTLER_POSITION = 0xD4  # x, y, z words: where popups over the battler go
BATTLER_COMMAND = 0x84
ACTION_SPECIAL = 2  # battler command (the menu's command number for it is 4)
BATTLER_SCRIPT = 0xC8
FIRST_ENEMY = 4  # enemy battlers are 4..11; 4..7 the back row
FIRST_FRONT_ENEMY = 8
LAST_ENEMY = 11
RECORDS_PTR = 0x020B8620
RECORD_SIZE = 0x6C
RECORD_STATUS = 0x08  # low nibble: the battler's status, 0 none
STATUS_MASK = 0xF
RECORD_STAGES = 0x38  # the s16 stage of stat n (4..9) is at RECORD_STAGES + 2 * n
RECORD_ATK_STAGE = 0x40
RECORD_DEF_STAGE = 0x42

BATTLE_WORK_PTR = 0x020B8550  # its first word: battle-wide flags (skills_data.FLAG_*)
WORK_SLOT0 = 0x50  # btldata entry of animation slot 0 (slot 1 is the move file, slot 2 the effect sprite)
WORK_EFFECT_SPRITE = 0x54  # btldata entry of animation slot 2, the effect row's sprite
WORK_EFFECT_MODE = 0x74  # 0 = no effect helpers this action (as for Fight); the effect row's value otherwise
WORK_MESSAGE = 0xDA  # message line bits: 1 "Escape failed!", 2 "Pray unsuccessful!"
MESSAGE_NO_EFFECT = 4  # our bit: "No effect!"
MESSAGE_WINDOW = 0xD
MESSAGE_FRAMES = 0x3C
OPEN_WINDOW = 0x0204582C  # (window, 1, frames)
TARGET_BITS = 0xC0000000  # spell flags: who it is cast on (skills_data.Target)
ALL_TARGETS = 0x40000000  # set for both all-enemy and all-ally spells
DRAW_TEXT = 0x02045114  # (handle, x, y, string, [sp] = style)

# Per-spell effect record in cave_skill_fx: 8 bytes per spell id
FX_SIZE_SHIFT = 3
FX_KIND = 0  # skills_data.Kind
FX_ARG = 1  # a stat id, a status, or a battle flag mask, by kind
FX_DELTA = 2  # s8
FX_LOOK = 3  # skills_data.Look
FX_CHANCE = 4  # percent chance for a status to land; 100 = no roll
FX_SELF = 5  # 1 = cast on the caster with no ally picker
FX_SPRITE = (
    6  # u16 btldata entry shown in place of the effect row's sprite; 0 = the row's own
)
FX_SIZE = 1 << FX_SIZE_SHIFT

# Character table: 0x12 bytes of btldata entries per character
CHARACTER_FILES = 0x020953D4
CHARACTER_FILES_SIZE = 0x12
FILE_ATTACK = 0x04  # the attack's sprite file
FILE_ITEM_POSE = 0x0E  # the pose for using an item or a card
LEVEL_INDEX = 0x020B4664  # u32 level index (0 = level 1) in Jian's field record; + 0x5C per character
CHARACTER_RECORD_SIZE = 0x5C

_CODES = {char: code for code, char in USA_TABLE.items()}


def encode(text: str) -> bytes:
    """Text in the game's character codes, with the end byte."""
    return bytes(_CODES[char] for char in text) + bytes([END])


def code(char: str) -> int:
    return _CODES[char]


def byte_list(data: bytes) -> str:
    """Bytes as the operand list of a `.byte` line."""
    return ", ".join(str(byte) for byte in data)


def hook(addr: int, old: int, asm: str, note: str) -> AsmPatch:
    """Replace the one instruction at addr (vanilla word `old`)."""
    return AsmPatch(addr, addr + 4, old, old, asm, note)
