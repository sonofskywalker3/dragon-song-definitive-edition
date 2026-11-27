"""The card overhaul (docs/plan-cards.md): a card slot and a dragon ring slot for every member.

Two switches: ring-slot (the dragon ring slot and a ring's Dragon Magic for whoever wears it) and cards (the card
overhaul). What the two slots share (the equip routing, the worn count, the equip page's worn item, the Status
page's box, and the spell listing) is glue built for the mix chosen (slots_mix, features.GLUE).

Put together from:
- feat_card_slots.py: the two slots in the character record and the equipment code that reads them;
- feat_card_equip.py: cards and dragon rings equipped on the Item page;
- feat_card_status.py: the Status page's equipment box scrolls to show the ring and card slots;
- feat_ring_slot.py: a ring's Dragon Magic for whoever wears the ring;
- feat_card_use.py: a worn card used from the Special list;
- feat_card_rules.py: one stage at most and a 70% roll for the statuses that take turns;
- feat_card_targets.py: the basic version for a wearer who does not know the card's skill, and the refusal of a
  use that would change nothing;
- feat_card_boost.py: for a wearer who knows it, the card enhances the skill;
- feat_card_changes.py: Insector, Ochu, and Kuntukapu last 2 to 4 rounds; Hellbird and Termite on one ally;
- feat_card_bosses.py: the boss card passives that need code;
- feat_card_drops.py: a species' first won battle gives its card, later kills recharge it, boss cards always drop;
- card_text.py: what each card says on the Cards equip page.

Needs skills (the Special list, the learn levels, and the rules a card shares with the skills).
"""

from dsde.card_text import card_text_patches
from dsde.feat_card_bosses import boss_patches
from dsde.feat_card_boost import boost_patches
from dsde.feat_card_changes import change_patches
from dsde.feat_card_drops import drop_patches
from dsde.feat_card_equip import equip_patches, shared_equip_patches
from dsde.feat_card_slots import (
    card_slot_patches,
    ring_slot_patches,
    shared_slot_patches,
)
from dsde.feat_card_rules import rule_patches
from dsde.feat_card_status import ring_icon_patches, status_patches
from dsde.feat_card_targets import target_patches
from dsde.feat_card_use import use_patches
from dsde.feat_ring_slot import listed_patches, ring_patches
from dsde.patching import Feature

CARDS_NAME = "cards"
RING_SLOT_NAME = "ring-slot"
CARDS = Feature(
    CARDS_NAME,
    (
        *card_slot_patches(),
        *equip_patches(),
        *use_patches(),
        *rule_patches(),
        *target_patches(),
        *boost_patches(),
        *change_patches(),
        *boss_patches(),
        *drop_patches(),
        *card_text_patches(),
    ),
)
RING_SLOT = Feature(
    RING_SLOT_NAME, (*ring_slot_patches(), *ring_icon_patches(), *ring_patches())
)
SLOTS_MIX = (RING_SLOT_NAME, CARDS_NAME)


def slots_mix(mix: frozenset[str]) -> Feature:
    """What the ring slot and the card slot share, for the mix chosen."""
    rings, cards = RING_SLOT_NAME in mix, CARDS_NAME in mix
    return Feature(
        "card-ring-slots",
        (
            *shared_slot_patches(rings, cards),
            *shared_equip_patches(rings, cards),
            *status_patches(rings, cards),
            *listed_patches(rings, cards),
        ),
    )
