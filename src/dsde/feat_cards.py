"""The card overhaul (docs/plan-cards.md): a card slot and a dragon ring slot for every member.

Put together from:
- feat_card_slots.py: the two slots in the character record and the equipment code that reads them.

Needs skills (the Special list, the learn levels, and the rules a card shares with the skills).
"""

from dsde.feat_card_slots import slot_patches
from dsde.patching import Feature

CARDS = Feature("cards", (*slot_patches(),))
