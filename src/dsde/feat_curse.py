"""Jian's curse no longer weakens his attack (design 11).

The curse (Curse of Lost Equilibrium) is one battle flag at 0x020B85B8 + 0x5C, set at battle start while
story flag 0x33 is set and 0x79 is not (end of the San Coliseum until after the Zethos fight;
docs/re-curse-battle-speed.md part 1). Its readers are Jian's Attack script choice in func_02068308
(three paths swap his 3-hit combo for a single swing) and two Zethos-only rules in his fight (an HP floor
at half, and from round 3 the skill that clears the flag, which plays as Jian landing a real hit).

The story drops the curse, but Jeff keeps the Zethos fight as it is, with no mention of a curse (there is
no curse text in battle). So only Jian's three checks change: each call of the flag getter becomes
"not cursed", and Jian keeps his combo. The flag itself, the floor and the Zethos skill are untouched.
"""

from dsde.patching import Feature, Patch

MOV_R0_0 = 0xE3A00000
JIAN_CURSE_CHECKS = (  # func_02068308: bl func_0202b934 (cursed?) before each Jian attack script choice
    (0x020684F8, "melee attack"),
    (0x02068628, "far attack"),
    (0x02068370, "follow-up attack"),
)
CURSE_CALL_WORDS = {
    0x020684F8: 0xEBFF0D0D,
    0x02068628: 0xEBFF0CC1,
    0x02068370: 0xEBFF0D6F,
}

NO_CURSE_PENALTY = Feature(
    "no-curse-penalty",
    tuple(
        Patch(
            addr, CURSE_CALL_WORDS[addr], MOV_R0_0, f"Jian's {what} ignores the curse"
        )
        for addr, what in JIAN_CURSE_CHECKS
    ),
)
