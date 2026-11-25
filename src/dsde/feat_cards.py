"""The card overhaul (docs/plan-cards.md): a card slot and a dragon ring slot for every member.

Put together from:
- feat_card_slots.py: the two slots in the character record and the equipment code that reads them;
- feat_card_equip.py: cards and dragon rings equipped on the Item page;
- feat_card_status.py: the Status page's equipment box scrolls to show the ring and card slots;
- feat_ring_slot.py: a ring's Dragon Magic for whoever wears the ring;
- feat_card_use.py: a worn card used from the Special list;
- feat_card_rules.py: one stage at most and a 70% roll for the statuses that take turns.

Needs skills (the Special list, the learn levels, and the rules a card shares with the skills).
"""

from dsde.feat_card_equip import equip_patches
from dsde.feat_card_slots import slot_patches
from dsde.feat_card_rules import rule_patches
from dsde.feat_card_status import status_patches
from dsde.feat_card_use import use_patches
from dsde.feat_ring_slot import ring_patches
from dsde.patching import Feature

CARDS = Feature(
    "cards", (*slot_patches(), *equip_patches(), *status_patches(), *ring_patches(), *use_patches(), *rule_patches())
)
