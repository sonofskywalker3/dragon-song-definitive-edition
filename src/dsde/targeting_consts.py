"""Addresses, offsets and constants shared by the manual targeting feature modules."""

# Game addresses
MENU = 0x020B8800  # battle command menu state
BUTTONS_PTR = 0x020B86FC  # pointer to the menu's button array, BUTTON_SIZE bytes each
BATTLERS_PTR = 0x020B8640  # pointer to the battler array, BATTLER_SIZE bytes each
BATTLE_WORK_PTR = 0x020B8550
BUTTON_SIZE = 200
BATTLER_SIZE = 0x12C

SLIDE_BUTTON = 0x020376CC  # (button, 0 out / 1 in, 0)
SLIDE_ALL_OUT = 0x020377F0
PLAY_SOUND = 0x020284D8
LIST_DOTS_AND_LABELS = (
    0x02035D88  # (0): paging dots and item-style row labels from the id list
)
HIGHLIGHTED_ROW = 0x02035724  # -> 0..5, -1 none
OK_BACK_SLIDE = 0x020395E0  # (0 out / 1 in): OK and back buttons
CLEAR_GROUP_HIGHLIGHT = 0x020378B0  # (-1, group)
HIDE_CURSOR_CORNERS = 0x020349E0
MENU_BUTTON = 0x02036694  # the menu's button handler, (button index) -> result
BATTLER_ALIVE = 0x02031B70  # (battler) -> 1 alive, 0 knocked out, -1 absent
HAS_EQUIP_EFFECT = 0x0206B8EC  # (effect, character id) -> 1 if equipped
SPECIES_OF = 0x0206892C  # (enemy row) -> species
AUTO_TARGET = 0x02050F78  # (mode, rows) -> battler index
ATTACK_BLOCK = 0x020368EC  # page 1 Fight: vanilla "command final" block
BUTTON_EPILOGUE = 0x02037690

# Hook sites
FIGHT_JUMP_ENTRY = (
    0x020367FC  # b 0x020368EC: page 1 jump table entry for button id 3 (Fight)
)
MENU_BUTTON_CALL = (
    0x0203A6E0  # bl 0x02036694: the only call of the menu's button handler
)
AUTO_TARGET_CALL = 0x02051C44  # bl 0x02050F78: party Attack target per hit
HIT_ALIVE_CALL = 0x02030BC4  # bl 0x02031B70: "target dead, the hit whiffs"

# Menu fields (offsets from MENU)
MENU_PAGE = 0x08
MENU_NEXT_PAGE = 0x0A
MENU_COMMAND = 0x10  # 3 = Attack, turned into the battler's action by the caller
MENU_HIGHLIGHT = 0x30
MENU_MEMBER = 0x34
MENU_FIRST_SHOWN = 0x3C
MENU_COUNT = 0x40
MENU_IDS = 0x44
MENU_ROW_STYLE = 0x82
MENU_DESCRIPTION = 0x84  # 0 items, 1 spells; 2 and up: no description window
MENU_REBUILD = 2  # flag bit in MENU + 0: build the next page

PAGE_COMMANDS = 1
PAGE_LIST = 4
NO_DESCRIPTION = 2
COMMAND_ATTACK = 3
RESULT_STAY = 0
RESULT_MEMBER_DONE = 2
SOUND_MENU = 1
SOUND_REFUSE = 2
SOUND_BACK = 3
GROUP_LIST = 0x40000

BUTTON_ID_BITS = 20  # button id = word0 & 0xFFF
BUTTON_OK = 6
BUTTON_BACK = 7
BUTTON_ROW = 0x0E
FIRST_ROW_BUTTON = 8  # also page 1's Fight, Special, Item (8..10)
BACK_BUTTON = 5
FIRST_DOT_BUTTON = 0x0E
LIST_ROWS = 6

# Battler fields
CHAR_ID = 0x04
ACTION = 0x84
TARGETS = 0x8C
POSITION_X = 0xD4  # screen position: lower is further left
FLAGS_ENEMY = 0x08
ACTION_ATTACK = 1
COVER_MODE = 0xC8  # battle work: cover/counter in progress

FIRST_ENEMY = 4
FIRST_FRONT = 8
LAST_ENEMY = 11
ROWS_ANY = 0
ROWS_BACK = 1
ROWS_FRONT = 2
CHAR_REACHES_ALL = 3  # this character hits any row
EQUIP_REACHES_ALL = 0x0D
CARD_ITEM_BASE = (
    0xD8  # an enemy's card item id is CARD_ITEM_BASE + species; its name labels the row
)

# ITCM state: +0 mode (1 = page 4 is the enemy list), +1 manual (hit 0 used a manual target),
# +2 last tapped list entry (tap again to confirm), +4 list entry -> battler index (8 bytes)
STATE_MODE = 0
STATE_MANUAL = 1
STATE_LAST_TAP = 2
STATE_FIRST = 3  # first real list entry (0 top row, 1 bottom row)
STATE_MAP = 4
HOLE = 0xFF  # map value of an empty grid cell

# Picker grid and keys
PAD = 0x020AFF74
PAD_PRESSED = 0x0201A3B0  # (pad) -> keys newly pressed
PAD_REPEATED = 0x0201A3B8  # (pad) -> keys pressed or repeating
PAD_DIRECTION = 0x02034A5C  # (keys) -> one direction or diagonal
KEY_A = 1
DIR_RIGHT = 0x10
DIR_LEFT = 0x20
DIR_UP = 0x40
DIR_DOWN = 0x80
MENU_KEYS = 0x02034AE4
MENU_KEYS_CALL = 0x0203A680  # bl 0x02034AE4
BUILD_ROWS = 0x02035310
BUILD_ROWS_CALLS = (
    (0x02034E7C, 0xEB000123),
    (0x02039948, 0xEBFFEE70),
    (0x0203A004, 0xEBFFECC1),
)
DOTS_UPDATE = 0x02035CAC
LOAD_LABELS = 0x02035784  # (0): row labels from the item name images
DOTS_BUILD = 0x020358A4
HIGHLIGHT_BUTTON = 0x02037910  # (button index)
INFO_WINDOW = 0x02035128  # (1): name of the highlighted entry
MOVE_CURSOR_CORNERS = 0x020347C8  # (button, jump)
GROUP_ROWS = 0x200000
SOUND_CURSOR = 0
MENU_CURSOR = 0x28
MENU_CONFIRM = 0x2C
GRID_TOP = 0
GRID_BOTTOM = 1
MAX_ENTRIES = 8
