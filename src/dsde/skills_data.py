"""The skills the party learns by level, as data (docs/plan-skills.md).

Each skill is one spell table entry from id 38 up, listed by owner in skills_jian.py, skills_gabryel.py,
skills_rufus.py, and skills_flora.py in the terms of skills_types.py. The feature modules
(feat_skills_*.py) turn the list into the table entries, the names and descriptions, the per-spell cave
tables the hooks read, and the learn levels, so adding a skill of an existing kind is one more `Skill`.
"""

from dsde.skills_flora import FLORA_SKILLS
from dsde.skills_gabryel import GABRYEL_SKILLS
from dsde.skills_jian import JIAN_SKILLS
from dsde.skills_rufus import RUFUS_SKILLS
from dsde.skills_types import (
    BOSS_IMMUNE,
    FIRST_SKILL,
    FLORA,
    GABRYEL,
    JIAN,
    LUCIA,
    RUFUS,
    SURE,
    Kind,
    Look,
    Skill,
    Target,
)

__all__ = [
    "BOSS_IMMUNE",
    "BY_SPELL",
    "FIRST_SKILL",
    "FLORA",
    "GABRYEL",
    "JIAN",
    "LUCIA",
    "RUFUS",
    "SKILLS",
    "SPELL_COUNT",
    "SURE",
    "Kind",
    "Look",
    "Skill",
    "Target",
]

SKILLS: tuple[Skill, ...] = tuple(
    sorted(
        (*JIAN_SKILLS, *GABRYEL_SKILLS, *RUFUS_SKILLS, *FLORA_SKILLS),
        key=lambda skill: skill.spell,
    )
)

DESCRIPTION_MAX = 30
if [skill.spell for skill in SKILLS] != list(
    range(FIRST_SKILL, FIRST_SKILL + len(SKILLS))
):
    raise ValueError("skill spell ids must run from FIRST_SKILL with no gaps")
if any(len(skill.text) > DESCRIPTION_MAX for skill in SKILLS):
    raise ValueError(f"a skill description is longer than {DESCRIPTION_MAX} characters")

SPELL_COUNT = FIRST_SKILL + len(SKILLS)  # spell ids 0 .. SPELL_COUNT - 1 exist
BY_SPELL = {skill.spell: skill for skill in SKILLS}
