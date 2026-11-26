"""An enhanced cast: what a skill or a healer's spell does when a worn card enhances it (docs/plan-cards.md 8).

The cards feature decides whether a cast is enhanced (feat_card_boost.py): when it takes the card's points with
the MP, it writes the caster's battler index into the boost state, and when the Special list's OK is pressed it
writes the stage limit the refusal test uses. Without the cards feature the state never names a caster, so
nothing here changes a cast.

An enhanced cast, by what it does:
- a stat skill moves the stat 2 stages (and is refused only at 2 stages past 0; feat_skills_idle.py reads the
  limit);
- a status skill always lands on a regular monster (bosses keep their immunities), and marks its target so the
  status it queues is the strong kind: blind lasts 4 to 6 turns instead of 2 to 4, poison takes 10% of max HP a
  turn instead of 5% (feat_skills_fx.py marks, the status setter here reads the mark);
- Tender Rain heals each ally to full, Miracle Tears revives at full HP, and Divine Rain's regen is 10% of max
  HP a turn instead of 5%.
"""

from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    BATTLE_WORK_PTR,
    BATTLER_RECORD,
    BATTLER_SIZE,
    BATTLERS_PTR,
    RECORD_SIZE,
    RECORDS_PTR,
    hook,
)
from dsde.skills_types import STATUS_BLIND, STATUS_POISON

TENDER_RAIN, DIVINE_RAIN, MIRACLE_TEARS = 2, 4, 5

# The boost state (cave_skill_boost)
STATE_ACTOR = 0  # s8: the battler whose cast is enhanced, -1 for none
STATE_LIMIT = (
    1  # u8: how many stages past 0 a stat skill may go (1, or 2 for an enhanced cast)
)
STATE_PENDING = (
    4  # u8 per stat record: the status queued on it comes from an enhanced cast
)
STATE_STRONG = 20  # u8 per stat record: its poison is the strong kind
RECORD_SLOTS = 16
NO_ACTOR = 0xFF
PLAIN_LIMIT = 1
BOOST_LIMIT = 2

WORK_ACTOR = 0x32  # battle work: the acting battler (s16)
RECORD_MAX_HP = 0x1C
RECORD_STATUS = 0x08
RECORD_TURNS = 0x4C  # s16: turns the status has left (func_02055070 counts it down)
STATUS_MASK = 0xF
RANDOM = 0x02011424

STRONG_BLIND_TURNS = (
    4  # plus two coin flips: 4 to 6 (the game's own 2 to 4 is 2 plus two coin flips)
)
POISON_RATE = 5  # percent of max HP a turn
STRONG_POISON_RATE = 10

# func_0205511c (set a battler's status): its common exit, `ldr r0, [pc, #0x1c]` (the stat records pointer);
# r4 = the record's offset (record index * 0x6C)
STATUS_EXIT = 0x0205520C
STATUS_EXIT_WORD = 0xE59F001C
# The end-of-turn poison tick: `mov r1, #5`, the percent of max HP it takes
POISON_RATE_SITE = 0x0202E25C
POISON_RATE_WORD = 0xE3A01005
# func_020500dc, per target: `bl func_02050850` (the heal amount; r6 = the spell, r7 = the target)
HEAL_SITE = 0x020501D0
HEAL_WORD = 0xEB00019E
HEAL_AMOUNT = 0x02050850
# The revive's HP: `adds sb, r1, sb` (sb = max HP / 10; ip = the target's battler offset, r3 = the battlers)
REVIVE_SITE = 0x02050188
REVIVE_WORD = 0xE0919009
# Divine Rain's regen: `orr r2, r2, #0x10` into the battle flags word
REGEN_SITE = 0x02050394
REGEN_WORD = 0xE3822010
REGEN_PLAIN = 0x10  # 5% a turn
REGEN_STRONG = 0x08  # 10% a turn (Namia's bit)

STATE_ASM = f"""
    .byte {NO_ACTOR}, {PLAIN_LIMIT}, 0, 0
    .space {RECORD_SLOTS * 2}
    .align 2
"""

# -> r0 = 1 if the acting battler's cast is enhanced, else 0. Keeps r1 to r3 and ip.
BOOSTED_ASM = f"""
    push  {{r1, lr}}
    ldr   r0, bo_work
    ldr   r0, [r0]
    ldrsh r0, [r0, #{WORK_ACTOR:#x}]
    ldr   r1, bo_state
    ldrsb r1, [r1, #{STATE_ACTOR}]
    cmp   r0, r1
    moveq r0, #1
    movne r0, #0
    pop   {{r1, pc}}
bo_work:
    .word {BATTLE_WORK_PTR:#x}
bo_state:
    .word ${{cave_skill_boost}}
"""

# r0 = a battler index -> r0 = its stat record index. Keeps r1 to r3 and ip.
RECORD_OF_ASM = f"""
    push  {{r1, r2}}
    ldr   r1, ro_battlers
    ldr   r1, [r1]
    mov   r2, #{BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0, #{BATTLER_RECORD:#x}]
    pop   {{r1, r2}}
    bx    lr
ro_battlers:
    .word {BATTLERS_PTR:#x}
"""

# In place of the status setter's exit load (r4 = record offset): a status queued by an enhanced cast is the
# strong kind. Blind gets 4 to 6 turns; poison is marked strong. Any status set clears the record's mark, and
# a poison set without it is the plain kind. Ends with the replaced load.
STATUS_EXIT_ASM = f"""
    push  {{r4-r6, lr}}
    mov   r5, #0
st_index:
    cmp   r4, #{RECORD_SIZE:#x}
    subhs r4, r4, #{RECORD_SIZE:#x}
    addhs r5, r5, #1
    bhs   st_index
    ldr   r6, st_state
    add   r6, r6, r5
    ldrb  r4, [r6, #{STATE_PENDING}]
    mov   r0, #0
    strb  r0, [r6, #{STATE_PENDING}]
    ldr   r0, st_records
    ldr   r0, [r0]
    mov   r1, #{RECORD_SIZE:#x}
    mla   r5, r1, r5, r0
    ldr   r0, [r5, #{RECORD_STATUS:#x}]
    and   r0, r0, #{STATUS_MASK:#x}
    cmp   r0, #{STATUS_POISON}
    strbeq r4, [r6, #{STATE_STRONG}]
    cmp   r0, #{STATUS_BLIND}
    cmpeq r4, #1
    bne   st_done
    bl    {RANDOM:#x}
    and   r4, r0, #1
    bl    {RANDOM:#x}
    and   r0, r0, #1
    add   r0, r0, r4
    add   r0, r0, #{STRONG_BLIND_TURNS}
    strh  r0, [r5, #{RECORD_TURNS:#x}]
st_done:
    pop   {{r4-r6, lr}}
    ldr   r0, st_records
    bx    lr
st_state:
    .word ${{cave_skill_boost}}
st_records:
    .word {RECORDS_PTR:#x}
"""

# In place of `mov r1, #5` in the poison tick: 10 for a strong poison on the acting battler. Keeps r0, r2, r3.
POISON_RATE_ASM = f"""
    push  {{r0, lr}}
    ldr   r0, pr_work
    ldr   r0, [r0]
    ldrsh r0, [r0, #{WORK_ACTOR:#x}]
    bl    ${{cave_skill_record_of}}
    ldr   r1, pr_state
    add   r1, r1, r0
    ldrb  r1, [r1, #{STATE_STRONG}]
    cmp   r1, #0
    moveq r1, #{POISON_RATE}
    movne r1, #{STRONG_POISON_RATE}
    pop   {{r0, pc}}
pr_work:
    .word {BATTLE_WORK_PTR:#x}
pr_state:
    .word ${{cave_skill_boost}}
"""

# r0 = a battler index -> r0 = its max HP. Keeps r1 to r3 and ip.
MAX_HP_ASM = f"""
    push  {{r1, lr}}
    bl    ${{cave_skill_record_of}}
    ldr   r1, mh_records
    ldr   r1, [r1]
    push  {{r2}}
    mov   r2, #{RECORD_SIZE:#x}
    mla   r0, r2, r0, r1
    pop   {{r2}}
    ldr   r0, [r0, #{RECORD_MAX_HP:#x}]
    pop   {{r1, pc}}
mh_records:
    .word {RECORDS_PTR:#x}
"""

# In place of `bl func_02050850`: an enhanced Tender Rain heals the target's max HP (the game caps it at full).
HEAL_ASM = f"""
    push  {{r4, lr}}
    bl    {HEAL_AMOUNT:#x}
    cmp   r6, #{TENDER_RAIN}
    popne {{r4, pc}}
    mov   r4, r0
    bl    ${{cave_skill_boosted}}
    cmp   r0, #0
    moveq r0, r4
    popeq {{r4, pc}}
    mov   r0, r7
    bl    ${{cave_skill_max_hp}}
    pop   {{r4, pc}}
"""

# In place of `adds sb, r1, sb` (the revive's HP, a tenth of max): an enhanced Miracle Tears revives at full.
# Sets Z as the replaced instruction would (sb is never negative).
REVIVE_ASM = f"""
    add   sb, r1, sb
    cmp   r6, #{MIRACLE_TEARS}
    bne   rv_done
    push  {{r0, lr}}
    bl    ${{cave_skill_boosted}}
    cmp   r0, #0
    beq   rv_plain
    mov   r0, r7
    bl    ${{cave_skill_max_hp}}
    mov   sb, r0
rv_plain:
    pop   {{r0, lr}}
rv_done:
    cmp   sb, #0
    bx    lr
"""

# In place of `orr r2, r2, #0x10` (Divine Rain's 5% regen bit): an enhanced Divine Rain sets the 10% bit.
REGEN_ASM = f"""
    push  {{r0, lr}}
    bl    ${{cave_skill_boosted}}
    cmp   r0, #0
    orreq r2, r2, #{REGEN_PLAIN:#x}
    orrne r2, r2, #{REGEN_STRONG:#x}
    pop   {{r0, pc}}
"""

BOOST_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_boost", STATE_ASM, "the enhanced cast state"),
    CaveCode("cave_skill_boosted", BOOSTED_ASM, "is this cast enhanced"),
    CaveCode("cave_skill_record_of", RECORD_OF_ASM, "a battler's stat record"),
    CaveCode("cave_skill_max_hp", MAX_HP_ASM, "a battler's max HP"),
    CaveCode("cave_skill_status_exit", STATUS_EXIT_ASM, "an enhanced status"),
    hook(
        STATUS_EXIT,
        STATUS_EXIT_WORD,
        "bl ${cave_skill_status_exit}",
        "an enhanced status",
    ),
    CaveCode("cave_skill_poison_rate", POISON_RATE_ASM, "a strong poison takes 10%"),
    hook(
        POISON_RATE_SITE,
        POISON_RATE_WORD,
        "bl ${cave_skill_poison_rate}",
        "a strong poison takes 10%",
    ),
    CaveCode("cave_skill_heal", HEAL_ASM, "an enhanced Tender Rain heals to full"),
    hook(
        HEAL_SITE,
        HEAL_WORD,
        "bl ${cave_skill_heal}",
        "an enhanced Tender Rain heals to full",
    ),
    CaveCode(
        "cave_skill_revive", REVIVE_ASM, "an enhanced Miracle Tears revives at full"
    ),
    hook(
        REVIVE_SITE,
        REVIVE_WORD,
        "bl ${cave_skill_revive}",
        "an enhanced Miracle Tears revives at full",
    ),
    CaveCode("cave_skill_regen", REGEN_ASM, "an enhanced Divine Rain regen is 10%"),
    hook(
        REGEN_SITE,
        REGEN_WORD,
        "bl ${cave_skill_regen}",
        "an enhanced Divine Rain regen is 10%",
    ),
)
