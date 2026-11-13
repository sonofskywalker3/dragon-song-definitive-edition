"""Learned skills cast on allies: the caster alone, or one ally from the game's ally picker.

- A skill cast on its caster alone (skills_data.Skill.self_only) skips the ally picker: choosing it on the
  Special list ends the member's command with the member as the target.
- Any other one-ally skill uses the game's ally picker (page 6). Jeff's rule holds there too: a pick the
  skill would do nothing to (the ally's stat is already raised, or the ally is knocked out) is refused with
  "No effect!" on the name bar, the picker stays up, and no MP is taken.

All-ally skills have no picker; feat_skills_idle.py refuses them at the list when they would do nothing to
anyone, and feat_skills_look.py passes over the allies they would do nothing to.
"""

from dsde import targeting_consts as T
from dsde.patching import AsmPatch, CaveCode
from dsde.skills_common import (
    FX_KIND,
    FX_SELF,
    FX_SIZE_SHIFT,
    STRING_NO_EFFECT,
    hook,
)
from dsde.skills_data import SPELL_COUNT, Kind

LIST_OK_ALLY = 0x02036D10  # Special list OK, target bits 0x80000000: `beq 0x02036D88` (the ally picker)
LIST_OK_ALLY_WORD = 0x0A00001C
ALLY_PICKER = 0x02036D88
# The ally picker (page 6), a portrait pressed for a spell (the page it came from, menu + 0xC, is 2):
# `beq 0x02037398`, which stores the spell and the target (r8 - 8, the party slot) and ends the command.
# r1 = the menu, r7 = 0 (stay), r8 = the button
ALLY_OK = 0x02037348
ALLY_OK_WORD = 0x0A000012
ALLY_OK_STORE = 0x02037398
FIRST_ALLY_BUTTON = 8

# Entered by `beq` from the Special list's OK handler for a spell on one ally (the handler's r4, r5, and r7
# go on; r6, r8, and sb are free). A skill cast on its caster alone needs no picker: the member is the
# target and the command ends, or the cast is refused if it would do nothing. Any other one-ally spell goes
# to the ally picker as before.
SELF_ASM = f"""
    ldr   r6, self_menu
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    cmp   r1, #{SPELL_COUNT}
    bhs   {ALLY_PICKER:#x}
    ldr   r0, self_fx
    add   r0, r0, r1, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [r0, #{FX_SELF}]
    cmp   r0, #0
    beq   {ALLY_PICKER:#x}
    ldrh  sb, [r6, #{T.MENU_MEMBER:#x}]
    mov   r0, sb
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   ${{cave_skill_refuse}}
    ldr   r1, self_battlers
    ldr   r1, [r1]
    mov   r2, #{T.BATTLER_SIZE:#x}
    mla   r8, r2, sb, r1
    strh  sb, [r8, #{T.TARGETS:#x}]
    b     ${{cave_skill_done}}
self_menu:
    .word {T.MENU:#x}
self_fx:
    .word ${{cave_skill_fx}}
self_battlers:
    .word {T.BATTLERS_PTR:#x}
"""

# Entered by `beq` from the ally picker when a portrait is pressed for a spell (r8 = the button; the
# handler's r4, r5, and r7 go on to its epilogue; r6 is free, and the store that follows reloads r1). A
# learned skill is refused there if it would do nothing to that ally, or the ally is knocked out: "No
# effect!" on the name bar, the picker stays up, no MP is taken. The game's own spells go on as before.
ALLY_ASM = f"""
    ldr   r6, ally_menu
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    cmp   r1, #{SPELL_COUNT}
    bhs   ally_store
    ldr   r0, ally_fx
    add   r0, r0, r1, lsl #{FX_SIZE_SHIFT}
    ldrb  r0, [r0, #{FX_KIND}]
    cmp   r0, #{Kind.NONE}
    beq   ally_store
    ldr   r0, ally_battlers
    ldr   r0, [r0]
    sub   r2, r8, #{FIRST_ALLY_BUTTON}
    mov   r3, #{T.BATTLER_SIZE:#x}
    mla   r0, r3, r2, r0
    bl    {T.BATTLER_ALIVE:#x}
    cmp   r0, #0
    movle r0, #{STRING_NO_EFFECT}
    ble   ${{cave_skill_refuse}}
    sub   r0, r8, #{FIRST_ALLY_BUTTON}
    ldrh  r1, [r6, #{T.MENU_SPELL:#x}]
    bl    ${{cave_skill_idle}}
    cmp   r0, #0
    bne   ${{cave_skill_refuse}}
ally_store:
    mov   r1, r6
    b     {ALLY_OK_STORE:#x}
ally_menu:
    .word {T.MENU:#x}
ally_fx:
    .word ${{cave_skill_fx}}
ally_battlers:
    .word {T.BATTLERS_PTR:#x}
"""

ALLY_PATCHES: tuple[CaveCode | AsmPatch, ...] = (
    CaveCode("cave_skill_self", SELF_ASM, "a skill on its caster needs no ally picker"),
    hook(
        LIST_OK_ALLY,
        LIST_OK_ALLY_WORD,
        "beq ${cave_skill_self}",
        "a skill on its caster needs no ally picker",
    ),
    CaveCode("cave_skill_ally", ALLY_ASM, "a wasted skill on an ally is refused"),
    hook(
        ALLY_OK,
        ALLY_OK_WORD,
        "beq ${cave_skill_ally}",
        "a wasted skill on an ally is refused",
    ),
)
