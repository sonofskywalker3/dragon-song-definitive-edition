"""Skills the party learns by level (docs/plan-skills.md, docs/plan-weapon-break.md).

The skills are data (skills_data.py). This feature is put together from these parts:

- feat_skills_table.py: the spell table entries (the stat growth table moves to the cave to make room), the
  names and descriptions, and the per-spell cave tables the hooks read;
- feat_skills_menu.py: Special opens a spell list for everyone, skills are listed by level and cast for MP,
  and a single-enemy skill is aimed on the Fight grid;
- feat_skills_idle.py: the one test for "this cast would do nothing", and the menu's refusal of such a cast;
- feat_skills_tags.py: the grid's name bar lists the highlighted enemy's ailments;
- feat_skills_fx.py: the effect itself and the "No effect!" line;
- feat_skills_look.py: how the cast plays.

Needs manual-targeting (the enemy grid and its helpers).
"""

from dsde.feat_skills_fx import FX_PATCHES
from dsde.feat_skills_idle import IDLE_PATCHES
from dsde.feat_skills_look import LOOK_PATCHES
from dsde.feat_skills_menu import MENU_PATCHES
from dsde.feat_skills_table import table_patches
from dsde.feat_skills_tags import TAG_PATCHES
from dsde.patching import Feature

SKILLS_FEATURE = Feature(
    "skills",
    (
        *table_patches(),
        *MENU_PATCHES,
        *IDLE_PATCHES,
        *TAG_PATCHES,
        *FX_PATCHES,
        *LOOK_PATCHES,
    ),
)
