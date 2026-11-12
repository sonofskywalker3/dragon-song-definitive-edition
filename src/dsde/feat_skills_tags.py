"""The enemy grid's name bar lists what ails the highlighted enemy.

Nothing on the battlefield shows that an enemy has a stat lowered or which status it has, so the place to
tell the player is where a target is chosen: the grid's name bar (Jeff, 2026-11-12: with that, no always-on
icon beside the monster is needed). Fight's grid shows the tags as well as a spell's.
"""

from dsde import targeting_consts as T
from dsde.jp_hint_pairs import END
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    BATTLER_RECORD,
    BATTLERS_PTR,
    DRAW_TEXT,
    LAST_ENEMY,
    RECORD_ATK_STAGE,
    RECORD_DEF_STAGE,
    RECORD_SIZE,
    RECORD_STATUS,
    RECORDS_PTR,
    STATUS_MASK,
    byte_list,
    code,
    encode,
    hook,
)

NAME_BAR_CARD_RETURN = (
    0x02044CF0  # func_02044c00: `addlt sp, sp, #8` after a card name was drawn
)
NAME_BAR_CARD_RETURN_WORD = 0xB28DD008
GLYPH_DOWN = 1  # the font's solid down triangle
# Name bar tags for statuses 1 to 7 (docs/re-cards.md), three letters each so an entry is 4 bytes
STATUS_TAGS = ("Slp", "Bld", "Cnf", "Par", "Sil", "Psn", "Stn")
TAG_RIGHT = 0x1B  # last text cell that shows on the name bar (cells are 8 pixels; text starts at cell 4)
TAG_BUFFER = 12  # "ATKvDEFvPsn" and the end byte: fits beside a 12-letter name


def _stat_tag(stat: str) -> bytes:
    """A lowered stat on the name bar: its three letters and the down triangle."""
    return bytes([*(code(char) for char in stat), GLYPH_DOWN, END])


# Replaces `addlt sp, sp, #8` (bllt) in the name bar's drawing, func_02044c00, on the path that has just
# drawn a card name and returns: the enemy grid labels its cells with card names. r6 = text handle,
# r8 = x, r7 = y. While the grid is up, everything that ails the highlighted enemy follows its name,
# right-aligned: "ATK" and "DEF" with a down triangle for a lowered stat, and three letters for its status
# (an enemy has one status at a time), with no spaces so that all three fit beside the longest names, for
# example "ATKvDEFvPsn". Ends with the replaced instruction and the lt flags its two successors need.
# (A conditional `bl` to a local label assembles as a branch to itself, hence the branches around `bl`.)
TAG_ASM = f"""
    push  {{r4, r5, r6, lr}}
    ldr   r4, tag_state
    ldrb  r0, [r4, #{T.STATE_MODE}]
    cmp   r0, #0
    beq   tag_out
    ldr   r0, tag_menu
    ldrsh r0, [r0, #{T.MENU_PAGE:#x}]
    cmp   r0, #{T.PAGE_LIST}
    bne   tag_out
    bl    {T.HIGHLIGHTED_ROW:#x}
    cmp   r0, #0
    blt   tag_out
    ldr   r1, tag_menu
    ldr   r1, [r1, #{T.MENU_FIRST_SHOWN:#x}]
    add   r0, r0, r1
    add   r1, r4, #{T.STATE_MAP}
    ldrb  r0, [r1, r0]
    cmp   r0, #{LAST_ENEMY}
    bhi   tag_out
    ldr   r1, tag_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r0, r2, r0, r1
    ldr   r0, [r0, #{BATTLER_RECORD:#x}]
    ldr   r1, tag_records
    ldr   r1, [r1]
    mov   r2, #{RECORD_SIZE:#x}
    mla   r4, r2, r0, r1
    adr   r5, tag_buffer
    ldrsh r0, [r4, #{RECORD_ATK_STAGE:#x}]
    cmp   r0, #0
    bge   tag_no_atk
    adr   r1, tag_atk
    bl    tag_append
tag_no_atk:
    ldrsh r0, [r4, #{RECORD_DEF_STAGE:#x}]
    cmp   r0, #0
    bge   tag_no_def
    adr   r1, tag_def
    bl    tag_append
tag_no_def:
    ldr   r0, [r4, #{RECORD_STATUS:#x}]
    and   r0, r0, #{STATUS_MASK:#x}
    sub   r0, r0, #1
    cmp   r0, #{len(STATUS_TAGS)}
    bhs   tag_built
    adr   r1, tag_status
    add   r1, r1, r0, lsl #2
    bl    tag_append
tag_built:
    adr   r1, tag_buffer
    subs  r4, r5, r1
    beq   tag_out
    mov   r0, #{END:#x}
    strb  r0, [r5]
    sub   sp, sp, #8
    mov   r0, #1
    str   r0, [sp]
    mov   r0, r6
    add   r1, r8, #{TAG_RIGHT + 1:#x}
    sub   r1, r1, r4
    add   r2, r7, #1
    adr   r3, tag_buffer
    bl    {DRAW_TEXT:#x}
    add   sp, sp, #8
tag_out:
    pop   {{r4, r5, r6, lr}}
    add   sp, sp, #8
    mov   r0, #0
    cmp   r0, #1
    bx    lr
tag_append:
    ldrb  r0, [r1], #1
    cmp   r0, #{END:#x}
    strbne r0, [r5], #1
    bne   tag_append
    bx    lr
tag_state:
    .word ${{cave_tgt_state}}
tag_menu:
    .word {T.MENU:#x}
tag_battlers:
    .word {BATTLERS_PTR:#x}
tag_records:
    .word {RECORDS_PTR:#x}
tag_atk:
    .byte {byte_list(_stat_tag("ATK"))}
    .align 2
tag_def:
    .byte {byte_list(_stat_tag("DEF"))}
    .align 2
tag_status:
{chr(10).join(f"    .byte {byte_list(encode(tag))}" for tag in STATUS_TAGS)}
tag_buffer:
    .space {TAG_BUFFER}
"""

TAG_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode(
        "cave_skill_tag", TAG_ASM, "the name bar lists the highlighted enemy's ailments"
    ),
    hook(
        NAME_BAR_CARD_RETURN,
        NAME_BAR_CARD_RETURN_WORD,
        "bllt ${cave_skill_tag}",
        "the name bar lists the highlighted enemy's ailments",
    ),
)
