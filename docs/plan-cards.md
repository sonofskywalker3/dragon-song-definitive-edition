# Plan: the card overhaul, with a dragon ring slot and a card slot (design, 2026-11-25)

Approved by Jeff 2026-11-25 (section 8). Nothing here is built yet. It supersedes the "cards lose their battle use" line of
docs/plan-skills.md and item 7 of docs/playtest-feedback.md. Background: docs/re-cards.md (what each card does),
docs/re-mp-jobs-rings.md 3 (slots and Dragon Magic), docs/re-enemies.md (drops, stealing), docs/design.md 10
(dragon rings). Tags: **[confirmed]** read in code or data, **[inferred]** fits the code but not run,
**[verify]** must be checked in the emulator before building on it. Both editions get all of it (gameplay, not story).

## 1. Why

The level-learned skills took over most card effects, so the cards became redundant, but a skill belongs to one
character: when that character is away, the party loses it, and some card effects are in no kit at all. A card
slot makes each effect a loadout choice for any member. The dragon ring slot does the same for Dragon Magic and
frees the accessory slot, as Lunar 1 and 2 do.

## 2. What the player sees

### 2.1 Two new slots for every member

- **Dragon ring slot.** Holds one of the four dragon rings (Blazing 0xCB, Tidal 0xCC, Gale 0xCD, Earth 0xCE).
  Anyone can wear one. The wearer gets the ring's +10 INT and its spell, listed in that member's Special list and
  cast at its 10 MP. A ring spell is listed only while worn, so Jian loses a ring's spell when he gives the ring
  away. The accessory slot keeps ordinary rings and amulets only. The Black Dragon and Dark Jian both drop an
  Earth Ring **[confirmed: drop rows 149 and 151]**, so two members can wear Earth; this plan allows it.
- **Card slot.** Holds one card: a monster card (an ability used from the Special list, or from the field Magic
  page for the six field cards) or a boss card (a permanent passive). One copy of each card exists, so a card is
  in one slot at a time. The six "character cards" the dragons drop (items 270 to 275, Jian to Althena) stay
  collectibles and cannot be slotted.

### 2.2 Equipping (Jeff, 2026-11-25, after seeing the real Item page)

The Item page is a grid of category icons (Weapons, Armor, Arm, Head, Accessories; then Tools, Cards, Rare
Items, Quest Items). An equipment category opens a page for one member at a time: the member's portrait with L
and R to change member, their stats, a box comparing the worn item with the highlighted one (each with its own
small item icon, the stat change, and the item's description line), and below it the items that member can
wear. A equips the highlighted item at once, swapping out the worn one, which goes back into the list. Worn
items are not listed, and no page takes an item off. **[seen: diag_item_page, diag_item_page2]**

- **Dragon rings** stay on the Accessories page. A on a dragon ring puts it in the member's ring slot, leaving
  the accessory alone; the comparison box shows the member's current dragon ring as the worn side.
- **Cards get an equip page like the Accessories page.** The Cards icon opens the same kind of page: portrait,
  L and R, stats, and the comparison box, with the card list below. A card's lines in the box are its name, its
  points as current/max (a boss card shows none), and what it does in the slot (the description line). A slots
  it into that member. Today's Cards viewer moves to the bestiary (2.7).
- **Moving and taking off.** A dragon ring or a card worn by another member stays in the list, marked as worn;
  picking it moves it to this member and empties the other member's slot. Picking the member's own worn ring or
  card takes it off. **[how the list marks a worn entry is settled when the page is built; pictures to Jeff]**
- When a member leaves the party (Lucia, Rufus), that member's ring and card slots are cleared, so a unique card
  stays usable by the others. Equipping never takes an item out of the bag (func_0206b46c only writes the slot;
  equipped copies are subtracted for display through func_0206b880), so clearing the slot is all it takes
  **[confirmed]**. This extends the existing leaving-member code.

### 2.3 The Status page

The equipment box shows five rows at a time and now has seven entries: the five slots, then the ring, then the
card. Up and Down scroll it (Up/Down are unused on that page today **[confirmed by the scroll trial]**). A small
arrow shows that more rows are above or below. The offset resets to the top when the page opens and on each L/R
member switch. Icons: the ring row uses the ring icon of section 6; the card row uses the menu's card
icon (frame 12). An empty slot shows the row's icon and no name, as the other slots do.

### 2.4 Battle

- **The Item command lists items only.** The Tools / Cards choice goes; Item opens the item list directly.
- **A slotted monster card is the last entry of its wearer's Special list**, after every spell, ring spell
  included. The name bar shows its name and its points, as the Cards page shows them today. Using it costs 100
  points and the turn, as today; it costs no MP. Silence does not block it (cards were items).
- A card at 0 points stays in the slot, greyed out, and cannot be picked until a kill recharges it (2.6). Nothing
  is ever "Lost".
- A boss card in the slot adds nothing to the Special list except Morus's Steal (section 5).

### 2.5 Field

The six field cards (Blob, Ohainkaru, Mad Fang, Ghoula, Treant, Gloomwing) are used from the wearer's field
Magic page, last in the list, for 100 points, with today's effects and today's rule that the map must still have
enemies (func_0206e838). The Magic page is enabled for a member who has a field card even with no spell.
The other cards do not show in the field.

### 2.6 Getting and recharging cards

- **The first won battle against a species gives its card**, every time, no roll, full, in addition to the
  normal item drops; the results screen lists it as it lists a drop today.
- **Every later kill of that species recharges its card by 100 points**, capped at the card's full value,
  wherever the card is (slot or bag). Three Blobs in one battle give +300. Kills are counted during the battle
  and the card and recharges are granted only when the battle is won: an escape or a loss gives nothing. No
  message for a recharge: the points on the card show it. **[Proposal: a results line "Blob card +100" if Jeff
  wants it.]**
- The normal item drop is unchanged: the roll that would have landed on the card slot gives slot 0 instead, as
  vanilla does once a card is owned (docs/re-enemies.md, drop table).
- **Boss cards always drop** (vanilla: 30 to 50%, and a boss is fought once). Gideon 2, Gideon 3, and Ignatius
  have no source today and stay collection cards for now (decision 2).

### 2.7 The bestiary (Jeff, 2026-11-25)

Today's Cards viewer (the card's art, name, max points, attribute and weakness icons, and a description) becomes
a bestiary for looking at the cards collected: the card art stays; the points go; in their place the enemy's
class (beast, slime, human, beastman, Vile Tribe, boss, and so on: a table to draft for Jeff), its stats (HP,
ATK, DEF, AGI, INT, DEX, LUCK at a stated level), and its attribute and weakness. Placement: an entry in the
System list beside Music Hall, another collection viewer (a proposal, open to change).

## 3. Monster cards: basic or upgraded by wearer

Rule (decided): a card whose effect overlaps a kit skill gives the **basic** version to a wearer who has not
learned that skill and the **upgraded** version to one who has. "Learned" means learned by level by now, the
same test that lists the skill (func_02050c50 and the skills framework's level table), including a skill that is
hidden because its all-target upgrade replaced it in the list. The basic version works on one picked target with
the skill's rules (its success roll, its "No effect!" refusal); the upgraded version works on all targets. A card
with no overlapping skill has one version.

Every use, either version, plays the card's own animation from today (the wearer's item pose, then the card's
effect on each target), never the paired skill's look, so a borrowed effect needs no new animation on a member
who could never learn the skill. Only the targets and the rules change.

A consequence of the rule as decided: the all-target version comes as soon as the base skill is learned, long
before the skill's own upgrade (Quetzalcoatl gives Jian all-enemies ATK down from level 9, War Breaker comes at
30; Shreeker gives Gabryel all-enemies poison from 13, Venom Storm at 31). The card's points are the limit.

Uses = full value / 100 (docs/re-cards.md 1). Flags read from the card effect table **[confirmed]**.

### 3.1 Paired cards

| Card (uses) | Effect today | Pairs with | Basic (anyone else) | Upgraded (knows the skill) |
|---|---|---|---|---|
| Quetzalcoatl (20) | ATK down, all enemies | Weapon Break (Jian 9) | ATK down, one enemy | all enemies |
| Abadon (14) | DEF down, all enemies | Armor Break (Jian 14) | DEF down, one enemy | all enemies |
| Ikontabipu (13) | sleep, all enemies, never misses | Knockout Kick (Jian 25) | sleep one enemy, 70% | all enemies, each 70% (decision 1) |
| Shreeker (12) | poison, all enemies | Venom Claw (Gabryel 13) | poison one enemy | all enemies |
| Asmodee (18) | blind, all enemies | Blinding Swipe (Gabryel 17) | blind one enemy | all enemies |
| Tick (13) | paralysis, all enemies | Water Bind (Flora 16), Howl (Gabryel 26; fear is the same status) | paralysis on one enemy, 70% | all enemies, each 70% |
| Comet (12) | INT up, all allies | Stratagem (Rufus 19) | INT up, one ally | all allies |
| Namia (13) | regen 10% of max HP a turn, party | Divine Rain (Lucia 11, Flora 20) | Divine Rain's 5% regen | Namia's 10% (stacks with Divine Rain: 15%) |
| Shaitan (10) | revive all allies, full HP | Miracle Tears (Lucia 13, Flora 32) | revive one ally, full HP | revive all allies |
| Vitra (13) | all allies to full HP | Tender Rain (healers 8) | one ally to full HP | all allies to full HP |
| Bealzebub (9) | party never misses | Focus (Jian 19) | one version: Focus is already party-wide, so this is how the party gets it while Jian is away or below 19 | |

Notes:
- Tick keeps its own rule in both versions: with no living enemy in the front row the use turns into a plain
  attack **[confirmed]**. It is a check on the front row, not a limit on targets.
- Vitra and Shaitan are their own effects (fill HP, revive at full) on one picked ally; Tender Rain and Miracle
  Tears only decide who gets the upgrade. The basic heal versions open the ally picker as Rufus's orders do.

### 3.2 Cards with one version

| Card (uses) | Effect (today's) |
|---|---|
| Onlooker (11) | AGI down, all enemies |
| Chupacabra (16) | DEX down, all enemies |
| Enigma (17) | INT down, all enemies |
| Thanatos (14) | LUCK down, all enemies |
| Duager (12) | every stat down, all enemies |
| Sturge (11) | LUCK up, all allies |
| Evil Earth (15) | DEX up, all allies |
| Dagon (18) | stone, one enemy |
| Phantom (14) | silence, all enemies |
| Druid (17) | "confusion": each turn 50% lost, all enemies (no attacking allies; it is closer to numb) |
| Insector (12) | party damage dealt x 1.75 to 2.00, this battle |
| Ochu (13) | party damage taken x 0.50 to 0.75, this battle |
| Kuntukapu (11) | regen 5% of max MP a turn, party (decided: no pair) |
| Hellbird (10) | all allies to full MP |
| Yeti (18), Termite (10) | enemy steals or breaks miss, this battle |
| Ice Mongrel (10) | escape the battle |
| Field: Blob (8), Ohainkaru (16), Mad Fang (16), Ghoula (14), Treant (13), Gloomwing (13) | today's field effects |

### 3.3 Stat and status rules for cards (decision 1)

Today a stat card moves a stage per use and uses stack to four stages (a boss's hit goes from 42 to 1), and a
status card never misses a regular enemy. The skills have a rule against that: one stage at most and a success
roll (docs/plan-skills.md, balance rules). **Recommendation:** every card, one-version cards included, follows
the same rules: a stat card moves each target one stage at most and is refused when every target is already
there; sleep, paralysis, and stone roll 70% on regular enemies; bosses keep their immunities; poison and blind
still always land. Without it, Enigma or Duager used four times trivializes every boss, and recharging from easy
kills makes the strong battle-wide cards (Insector, Ochu) cheap to keep using.

## 4. Boss cards: permanent passives

A boss card in the card slot gives its wearer a passive while worn and never uses points. Each is fitted to the
boss's stats, attacks, or element (stats at the boss's minimum fight level). Seventeen get a passive now:
fourteen are item data only (the card's six stat shorts and its gear effect id, which the stat and effect code
reads once it includes the card slot) and three are new code. Gideon 2, Gideon 3 (a small HP hook), and Ignatius
wait (decision 2). Bonuses are first numbers to tune in play.

| Boss card | What stands out | Passive | How |
|---|---|---|---|
| Sasquatch | DEF-heavy brawler | DEF +8, ATK +4 | data |
| Armored Boar | its charge is a double-damage hit | DEF +8, 20% chance a hit does double damage | data (gear effect 0x27) |
| Raft | the fastest Coliseum fighter | AGI +12, DEX +5 | data |
| Sharif | blinds the party | LUCK +10, immune to blind | data (0x10) |
| Moran | breaks gear | **decided**: the wearer's attacks may lower the target's DEF one stage | new code |
| Deuce | the orb guardian wall | DEF +12, LUCK +8 | data |
| Gronk | wind caster | INT +12, 25% less wind damage | data (0x21) |
| Zethos | top ATK of his time | ATK +12, LUCK +10 | data |
| Caucus | casts and heals the trio | INT +10, regain 2% max HP each own turn | data (0x1D) |
| Orcus | breaks gear | **decided**: the wearer's attacks may lower the target's ATK one stage | new code |
| Morus | thief | **decided**: Steal (section 5) | new code |
| Red Dragon | fire | ATK +12, 25% less fire damage | data (0x22) |
| White Dragon | fastest dragon, wind | AGI +15, 25% less wind damage | data (0x21) |
| Black Dragon | DEF nearly double the others, earth | DEF +15, 25% less earth damage | data (0x20) |
| Blue Dragon | water caster | INT +15, 25% less water damage | data (0x1F) |
| Dark Jian | a mirror of Jian | +5 to all six stats | data |
| Gideon | sword, sleep strike | ATK +15, DEX +10 | data |
| Gideon 2 | caster form | later (decision 2): INT +15, regain 1% max MP each own turn | data (0x1E) |
| Gideon 3 | huge HP | later (decision 2): max HP +15% | small hook |
| Ignatius | the unbeatable foe | later (decision 2): 25% less damage from everything | data (0x25) |

- **Moran and Orcus:** once per attack action (Fight, Stone Throw, Savage Rush), on its first landed hit, a 25%
  chance that the target's DEF (Moran) or ATK (Orcus) drops one stage, through func_02054dec as Jian's breaks
  do, only if the stage is not already below 0 (the skill cap), bosses included. Jian's combo and Savage Rush's
  two swipes get one roll, not one per hit. The name bar tag shows it; a banner after the hit if the attack
  script can take one cheaply.
- Gear effects are one id per item, so each data card has at most one effect; the six stat shorts are halved
  under the curse like any equipment **[confirmed: func_0206b4d8]**.
- No theft or break protection passives (decided).
- Element names follow the dragons (fire, water, wind, earth) **[inferred]**; the resistance bytes and the gear
  effects 0x10, 0x1D to 0x27 in func_0206ab6c's switch are **[confirmed]**; each still gets one equip and one
  battle to see it work.

## 5. Morus's Steal

- With the Morus card slotted, the wearer's Special list has **Steal** (free, costs the turn).
- Pick one enemy (the enemy grid, any row). The roll is the game's hit chance, `DEX * 8 / (DEX * 8 + target AGI)`
  (89% at equal stats), halved: **about 45% at equal stats**. On success the item is the enemy's drop slot 1
  (the rarer one) 25% of the time and slot 0 otherwise; a slot with no item, a dragon ring, or a key item (ids 387
  and up) falls back to the other slot, and with neither, "Nothing to steal". The card slot (slot 2) is never
  stolen.
- Silence blocks Steal, as it blocks other skills.
- Each enemy can be robbed once; a second try on it is refused up front ("No effect!", as a wasted skill is).
- The stolen item goes to the bag at once, separate from the normal drop at the end.
- Message: "Stole <item>!" **[verify that the game's "<item> was stolen" line (enemy steals) can be reused with a
  new verb; else "No effect!" on a miss and the item name alone on success]**.

## 6. The ring slot icon

Jeff (2026-11-25): use the game's own ring item icon (the plain gold band drawn beside the accessory "Ring",
item 0xD7, in the Item page's comparison box) instead of the hollowed shield, if it can be shown on the Status
page. Each accessory has its own small icon there (Counter Prototype a blue charm, Ring a gold band, Blazing Ring
a red ring); where the game keeps them and how it picks one per item is not found yet (no per-item icon field in
the item table, no icon character in the names, none in sysmenupack's or common's 16x16 sheets). Fallback: the
hollowed shield (option 2), `.planning/ring_options.png`.

## 7. How it is built

### 7.1 Slots in the character record **[verify first]**

The record is 0x5C bytes per character at 0x020B4658; the five equipment u16s are at +0x40 (Jian 0x020B4698),
indexed `slot * 2` **[confirmed]**. Slots 5 and 6 fall at +0x4A and +0x4C. The save copies 0x39C bytes from
0x020B464C, which covers every record, so they persist **[confirmed: func_0206da14, func_0206d7fc]**. Two
writers zero them today: game init, and **func_020555e8** (decomp lines 61108 and 61109), reached from
func_020186b8, a stash-and-restore reset that keeps EXP and cards, from field states 0xC and 0xD of
func_0201e6a0. That second writer must keep slots 5 and 6. Before anything else: a read and write watch on
+0x4A, +0x4C (and +0x5A as the fallback) through equip, battle, the curse, a member leaving and rejoining, the
func_020186b8 path, save, and load. A watch cannot prove that nothing reads them, so also list every instruction
that loads from a record with an offset of 0x4A to 0x4D.

**Slot 5 = card, slot 6 = ring.** Cards have item type 0x8005 (low nibble 5), so the equip routine's "slot =
type" puts a card in slot 5; the 34 monster cards and the 17 boss cards with passives get the five "who may equip" bits (0x10 to 0x100),
the six character cards and the three deferred boss cards do not. The rings keep type 0x8014 (accessory, so the Item page keeps them on its
accessory page) with all five "who" bits, and func_0206b46c sends 0xCB to 0xCE to slot 6. The Status page shows
slot 6 before slot 5.

Old saves: on load, a dragon ring found in a member's accessory slot moves to slot 6.

### 7.2 Equipment code

Each place has its own fix; none is a blanket `< 5` to `< 7` **[confirmed by reading each]**:

| Function | What it is | Change |
|---|---|---|
| func_0206b930 | "may this member equip it": false when the type's low nibble is above 4 | allow nibble 5 (cards with "who" bits) |
| func_0206b880 | how many members wear an item: looks only in the slot named by the type; its `< 5` is the member loop | look in slot 5 for cards and slot 6 for rings; the member loop stays 5 |
| func_0206b8ec | does a member wear this item (Dragon Magic's cast test) | search slots 0 to 6 |
| func_0206b4d8 | stat totals | add slots 5 and 6 |
| func_0206b0fc's users: func_0206ab6c (gear effects; its bound is `if (4 < i) return`, decomp ~73713) and func_0206aabc (MP cost) | gear effects | include slots 5 and 6 |
| func_02055760 | copies a five-per-member default gear table (0x02094720) | unchanged |
| func_0206b144 | break's "replace with the default item" | unchanged |
| func_0206b1d0 | break picker | unchanged (4) |

Then the Item page's "who" picker preview (the callers of func_0206b030 around decomp lines 54616, 55160, 64463,
and 69627) and the per-slot menu routines func_02064824, func_02064a4c, func_02065240, func_02059f84, and
func_02056420 take the old item from slot 6 for a ring and slot 5 for a card. Search the rest of arm9 for slot
reads by address (record + 0x40 + 2 * n) before calling it done.

A monster card's item +2 is its card effect id (0x117 to 0x139); the gear effect switch ignores ids above 0x2D
**[confirmed]**, so a slotted monster card adds nothing there. Boss cards get gear effect ids at +2; check that
nothing else (the Cards page's "usable" test, the card command) reads a boss card's +2 as a card effect.

### 7.3 Dragon Magic for anyone

- Listing (func_02050c50): a ring spell (flags 0x100000 to 0x800000) is listed for any member whose slot 6
  holds that ring, and no longer for Jian from the bag alone.
- Casting (func_02050a74): the same test on the caster's slot 6, for every member.
- The look: Jian keeps his four Dragon Magic files (btldata 19 to 22) in slot 0. For anyone else: decision 3.

### 7.4 Monster cards in the Special list and the field Magic page

Card entries do not pretend to be spells. Spell ids index the spell table everywhere (func_02050a74, targeting
flags, descriptions, the field name pool 0x0205C108), so a card entry carries a **marker** that every consumer
checks first, through one set of shared helpers (name, description, icon, targets, usable, cost).

- The list builders (battle func_02035e00 case 2, field func_02064ff0) pass through the skills framework's sort
  and compaction (feat_skills_order.py). After the sort, append one entry for the slotted card: the marker plus
  the card's item id. Morus's Steal is an ordinary new skill (spell id 63) and sorts normally. Id 63 is the last
  one the sort key's 6 id bits hold (`KEY_ID_BITS`); widen the key before adding any later skill.
- Name bar: the card's name and points; description line: the card's description; row icon: the card icon.
- Cast: a card entry issues today's card command (command 4 with that item), so the effect, the animation, and
  the 100-point charge (func_0207f83c) stay the game's own, and no MP path is touched. The battler keeps the
  version (basic or upgraded) chosen when the entry was picked. In the card effect path: basic narrows the
  targets to the one picked (the enemy grid for enemies, the ally picker for allies); every use applies the rules
  of 3.3 (one stage, 70% rolls, and the refusal before the turn through the skills framework's idle test and
  the grid's veto).
- The battle auto or AI caller (decomp ~58339) handles a card entry or skips it.
- func_0207f83c: at 0 points the card is no longer removed and "Lost <name> card" no longer shows. A card at 0 is
  listed greyed and refused when picked.
- The "has any spell" test (func_02050ec8) also answers yes for a member with a slotted card or Steal, so Special
  (battle) and the Magic page (field) are enabled.
- Battle Item menu: drop the Tools / Cards choice (func_02035e00's card list, +0x82 = 0).

### 7.5 Drops and recharge

Normal enemy drops run from func_02069f34, which calls the roll func_02069e00; the card id is
`(row >> 2) + 0xD8` and the owned test is func_0206ba54 (the bag count, which includes a slotted card). Both run
as each enemy dies, before the battle is won, and DE's `one-battle-mode` already changes this path (vanilla
Virtue mode gave EXP instead of a drop), so the hook goes after that patch. During the battle, count kills per
species in a small battle-time table; on victory (the results step) grant each card not yet owned at full value,
and add 100 per kill (not counting the one that won it) to each owned card's counter (0x020B4884 + 2 * (card -
0xD8)), capped at its full value (0x0209EA14 + 8 * (card - 0xD8)). The new card does not use the four-entry
loot buffer. Bosses: the card slot's chance becomes 100% for all 20 (func_02069f34's boss branch).

### 7.6 Boss passives

Data: each boss card's six stat shorts and +2 gear effect id. Hooks (Gideon 3's max HP +15% is deferred, decision 2): Moran and Orcus after a landed physical hit in func_02030b44, wearer only
(test the attacker's slot 5; one roll per action); Steal as above. The battle-wide flag word is party-wide, so
none of the wearer-only effects uses it.

### 7.7 Text

- Item descriptions (sysmenupack 058, CMTX, one string per item id): rewrite the 34 monster cards to say what the
  card does in a slot, and the 20 boss cards ("A collection card, it cannot be used" today) to say their passive.
  The four rings: "Grants <spell> to the wearer." Both editions.
- New strings: "Steal", its description, "Stole <item>!", "Nothing to steal".

### 7.8 Modules

New feature `cards` (both editions), split under 400 lines a file: `cards_data.py` (pairs, boss passives, item
type edits), `feat_card_slots.py` (record slots, equipment code, equip routing, leaving members, old saves),
`feat_card_status.py` (Status page scroll, icon, arrow), `feat_card_use.py` (Special and Magic entries, cast
routing, points, no "Lost"), `feat_card_drops.py`, `feat_card_bosses.py` (hooks, Steal), and the ring changes in
`feat_ring_slot.py`. The scroll trial branch (`spike/status-scroll`) is a reference only, never merged.

## 8. Decisions (Jeff, 2026-11-25: "go with what you've got and we'll adjust if needed")

The doc is approved, with each of these recommendations taken:

1. **Card stat and status rules (3.3):** cards follow the skill rules (one stage, 70% rolls, refusal), not
   today's stacking.
2. **Gideon 2, Gideon 3, and Ignatius cards:** they stay collection cards for now (no passive, never slotted)
   and are settled with the Retold Ignatius fight; their draft passives stay in the table for then. So 17 boss
   cards get passives now.
3. **A ring spell on someone other than Jian:** the wearer's own cast pose, then the element effect that the
   party has never used (224 burst, 225 geyser, 226 flame column, 227 shattering boulder, tinted) on each enemy,
   once it is confirmed that Jian's Dragon Magic files show Jian himself. Pictures go to Jeff before it is built.
4. **The boss passive table (section 4)** as drafted; the numbers get tuned in play.

**Revised (Jeff, 2026-11-25, later): a card enhances the matching skill.** It replaces section 3's basic and
upgraded versions for a wearer who knows the skill (the version built in 11.7 and tested in 11.8 for learners
goes):
- A wearer who knows the matching skill no longer lists the card. While the card has points, every cast of the
  skill is enhanced and costs the skill's MP plus 100 points (a one-target skill) or 200 points (an all-target
  skill); at 0 points the skill casts as normal. The name bar shows "+" after the name.
- A wearer who does not know it keeps the card entry: one picked target, 100 points, no MP (as built).
- Enhancements: a stat skill moves 2 stages (Weapon Break, War Breaker, Armor Break, Wall Breaker, Stratagem, War
  Council; the one exception to the one-stage rule). A status that rolls always lands on a regular monster
  (Knockout Kick; Water Bind, Binding Rain, Howl, Dread Roar). A status that already always lands lasts longer
  (Blinding Swipe and Blinding Gale: 4 to 6 turns); Venom Claw and Venom Storm take 10% a turn instead of 5%. Divine Rain regen 10%; Tender Rain heals to full; Miracle Tears revives at full.
  Bosses keep their immunities. Bealzebub keeps one version (Focus cannot be stronger).
- Poison lasts 2 to 4 turns instead of the whole battle, on monsters and on the party alike, and the party's
  poison (Venom Claw, Venom Storm, Shreeker) lands on a boss 80% of the time (regular monsters: always). Blind the
  same: the party's blind (Blinding Swipe, Blinding Gale, Asmodee) lands on a boss 80% of the time. Jeff: poison for the whole battle plus a stronger tick would take half a boss's HP and more.

**Approved build list (Jeff, 2026-11-25, point by point).** It replaces the matching parts of sections 2 to 5.

1. **Icons and names.** Every Special list entry gets an icon; the worn card's entry shows its card's icon.
   Drawn icons are PNG files in `art/icons/`, read by the build, so an artist can replace a file of the same
   name. `ART-SOURCES.md` lists and links every file (drawn: generated with AI; reused: the game's own item
   icon). Icons: Stone Throw the thrown stone; Weapon Break and War Breaker the sword with the down arrow at
   the bottom left; Rally and Battle Cry the same swords with the up arrow; Stand Fast and Shield Wall the
   breakers' armor with the up arrow; Quick March and Forced March the Escape boot with the up arrow; Focus a
   black crosshair; Knockout Kick a sheep; Gale Cut a wind swirl; Blinding Gale the same wind with a dark
   purple and black glow; Double Strike two impact bursts; Venom Claw bubbles; Venom Rain smaller spread
   bubbles; Blinding Swipe glasses with black lenses; Feral Rage claw slashes with the up arrow; Howl 3 and
   Dread Roar 4 black concentric circles; Water Bind three stacked rings, Binding Rain three stacks of three;
   Healing Water a blue drop, Cure Water a green drop, Tender Rain a wide cloud with rain, Divine Rain a gold
   cloud with white rain, Miracle Tears a slim purple tear; Thunder Sword bolts along the blade; Stratagem the
   Old Book and War Council a map, both with the up arrow. Renames, both editions: Loud Call to Crashing Wave,
   Savage Rush to Double Strike, Cure Squall to Cure Water, Venom Storm to Venom Rain, Feral to Feral Rage.
2. **Cards enhance matching skills** as in the revision above. Focus becomes Jian only; Bealzebub makes it
   party-wide (an enhancement, not one version).
3. **Status rules.** Poison 2 to 4 turns on everyone; the party's poison and blind land on bosses 80% of the
   time; Phantom's silence 2 to 4 turns and 80% on bosses (check vanilla silence first); Kuntukapu's MP regen
   2 to 4 turns.
4. **Changed cards.** Yeti: the user steals one item from the enemy's loot table, 25%, never a card. Termite:
   breaks and steals miss one picked party member this battle. Hellbird: one ally to full MP. Insector and
   Ochu: 2 to 4 turns instead of the whole battle (all three are common: four areas each, Insector and
   Hellbird from the first area). If Insector is still too strong, try x1.50 to 1.75 next.
5. **Boss cards.** The four dragons take 50% less damage from their element; Caucus regains 3% of max HP a
   turn; Morus's Steal 50% with a 10% bonus toward the rarer item (Yeti's is 25%); the rest as section 4.
   Gideon 2, Gideon 3, and Ignatius wait for their source (to do, below).
6. **Field cards** keep vanilla effects and points. Players' descriptions: Mad Fang draws symbols (map
   monsters) toward you; Ghoula makes them flee for a while; Treant restores HP on the map for a while;
   Gloomwing restores 30 MP per member over about 30 seconds.
7. **Getting and recharging** as section 2.6, and the bestiary as 2.7.
8. **Custom installer**, shipped with this release as a third download beside the two IPS files: the story is
   one switch (all or none); every engine and gameplay change is its own switch (for example HP drain while
   running, B in a town menu selecting Leave town); dependencies are switched on or greyed out; defaults match
   the full release. A design (switch list, dependencies, Windows app or web page) goes to Jeff first.

**To do, later (Jeff, 2026-11-25):**
- Gideon 2, Gideon 3, and Ignatius cards: the vanilla unwinnable Ignatius fight stays, then the Gideon fights;
  winning Gideon 2 and 3 gives their cards (vanilla has zeroed card drops there: Gideon 3's drop row
  0x02097CC0 lists the Althena and Ignatius cards at chance 0, Gideon 2's row 0x02097CB4 the Rufus card and its
  own); a chance to save and equip them; then a new, winnable second Ignatius fight, after which the ground
  collapses and he falls, and his card is given. An epilogue or New Game+ uses it later.
- Character cards (Jian, Lucia, Flora, Rufus, Gabryel, Althena): given when the character is first met, not by
  battle. Owned cards of party members add "Summon Lucia" and so on to Jian's field Magic page (no slot
  needed); it asks who to replace. Jian cannot be replaced; story scenes that need a set party lock it and
  restore it; the bench gets full EXP; gear stays on the member. Althena stays a collectible. A passive when
  worn: later.

## 9. Test plan (emulator, both editions)

- Watch on the new slot shorts (7.1) through equip, battle, leave and rejoin, the func_020186b8 reset, save, and
  load; an old save with a ring in Jian's accessory slot.
- Equip a ring and a card on each member from the Item page; the preview compares the right pair; move both to
  another member; take both off. Save, reload, check.
- Status page: seven rows, Up and Down scroll, arrow, L/R resets, both new icons.
- Each ring on Lucia: listed, castable at 10 MP, +10 INT; Jian without it: not listed.
- One paired card in each state: basic on a non-learner, upgraded on a learner, both charge 100 points and no MP;
  0 points greyed and refused; first-win drop, +100 per later kill, cap; nothing after an escape.
- A boss data passive (stat totals change on the Status page), Moran or Orcus on a forced roll,
  Steal success, refusal, and fallbacks.
- Field card from the Magic page on a member with no spell.
- Plans and GIFs under `emu/plans/`; at most two emulator instances at once.

## 10. Build order

1. Watch and readers of the record slots, and the func_020555e8 fix (7.1); stop and re-plan if the shorts are in
   use.
2. Equipment code, equip routing, Item page preview, leaving members, old saves (7.2, 7.1, 2.2).
3. Status page scroll and icons (2.3, 6).
4. Ring spells for anyone (7.3), with pictures of the look to Jeff first (decision 3).
5. Cards in the Special list and the field Magic page, points, no "Lost", Item menu without Cards (7.4).
6. Drops and recharge (7.5).
7. Boss passives: data first, then Moran and Orcus, Steal (7.6, 5).
8. Text (7.7), then the full test plan.

## 11. Built

### 11.1 The record slots are free (2026-11-25)

- **Static.** Every ARM halfword load or store with an offset of 0x4A or 0x4C in arm9 (26 functions) was read:
  the hits are battle records (0x6C each, where +0x4A is a stat stage), stack frames, and menu or save
  structures (0x020A6438, 0x020B6BE4, the save header). None is a character record. Thumb code cannot reach
  those offsets with an immediate. The only references to the record shorts by address are the two zeroing
  loops: game init (func_02055760) and func_020555e8, which zeroes +0x4A to +0x58 of all five records and then
  recomputes the stat totals at +0x4E to +0x58 (func_0206b4d8 adds into +0x4E onward; it never touches +0x4A
  or +0x4C). func_020555e8 runs from func_020186b8: it stashes the character records and five other blocks,
  reinitializes the game (func_0201881c), restores them, and puts back the card counts and each member's EXP
  from a saved buffer. It is reached from field states 0xC and 0xD of func_0201e6a0 after a fade.
- **Watched** (`test_card_slot_watch`, `test_card_slot_battle`, `test_card_slot_reload`): marker values in
  Jian's and Lucia's +0x4A and +0x4C and Jian's +0x5A, a write trace on each, through the Status page, a save
  to album No.1, a won battle (Jian to level 4), and a fresh boot that loads the save. No write was traced and
  every marker came back unchanged, from the battery save too.
- So slot 5 is +0x4A and slot 6 is +0x4C, and func_020555e8's two stores to them (0x0205567C, 0x02055680)
  become no-ops.

### 11.2 Equipment code for slots 5 and 6 (2026-11-25)

feat_card_slots.py, feature `cards` (both editions, after `skills`):
- Item data: the "who" bits (0x1F0) on the 34 monster cards, the 17 boss cards with passives, and the four
  dragon rings; each of those boss cards gets its six stat shorts and gear effect id (cards_data.py).
- func_0206b930 accepts slot number 5 (`cmp r2, #5` to `#6` at 0x0206B950); func_0206b46c's slot (0x0206B4B4)
  comes from cave_card_equip_slot, slot 6 for 0xCB to 0xCE; func_0206b880 is rewritten in place to count
  wearers in the slot the item goes in, a ring's in slot 6, over the same five members; the slot loops of
  func_0206b8ec, func_0206b4d8, func_0206aabc, and func_0206ab6c run to slot 6; func_020555e8's two stores to
  slots 5 and 6 are no-ops.
- A boss card's +2 is also read as a card effect by func_0206aa94, which maps every id below 0x100 to entry 0,
  the same as vanilla's 0, so nothing changes there.
- **Seen** (`test_card_equip_poke`, Jian with the Blazing Ring poked into slot 6 and the Sasquatch card into
  slot 5, first temple battle): his battle record has ATK +2, DEF +4, INT +5, half of +4, +8, +10 because Jian
  is cursed in that save (equipment bonuses are halved, func_0206b4d8); Inferno casts from his Special list
  (MP 10 to 0). The build without the feature: no change and Inferno not castable (MP stays 10).
  `test_skill_lucia_list` and `test_field_menu` unchanged.

### 11.3 Equipping on the Item page (2026-11-25)

- **The page.** func_02063e5c builds the Item page's list (0x0213A008, 8 bytes an entry: item, count): category
  (0x02139FD4 + 4) 1 to 5 lists items of slot number 0 to 4, 6 Tools, 7 Cards (slot number 5), 8 Rare Items, 9
  Quest Items, each item only while the bag holds more than are worn (func_0206b880). State 0x17 opens the equip
  page (0x24, idle 0x1A, equip 0x25: func_0206b46c with the list entry) for categories 1 to 5 and the list page
  (0x1C) for the rest; B on a page (func_0205747c) goes back to the categories, except Cards, which leave through
  the card viewer's exit (0x59).
- **Item icons.** sysmenupack entry 54: a 256-colour palette, then a 16x16 8bpp icon (0x100 bytes) per item from
  item 1 (func_020280e8). Every item has its own: the dragon rings 0xCB to 0xCE are red, blue, green, and brown
  rings, the accessory "Ring" (0xD7) a plain gold band, and each card a monster portrait.
- **Built** (feat_card_equip.py): the Cards category opens the equip page (0x0205CC10); B there goes back to the
  categories (0x02057DD4 compares with 0xFF); the worn item's icon (func_02064824), name (func_02064a4c), and
  stats (the switch in func_02065240) come from cave_card_worn: slot 5 for Cards, slot 6 on the Accessories page
  while a dragon ring is highlighted, else the category's slot.
- **Seen** (`test_card_equip_menu`, Jian with Quetzalcoatl, Sasquatch, and the Blazing Ring): Items, Cards opens
  the equip page; A slots Quetzalcoatl (slot 5 = 236); with Sasquatch highlighted the box shows Quetzalcoatl worn
  and ATK 19, DEF 27 up; A swaps in Sasquatch (250); B goes back; Accessories, Blazing Ring: the box compares it
  with the empty ring slot (INT 4 to 14), A puts it in slot 6 (0xCB), and Counter Prototype stays on (0xD0).
- **One of a kind** (cave_card_equip_slot in func_0206b46c, cave_card_list_worn at the list builder's worn count
  0x02063EC4): a dragon ring or a card anyone may wear stays listed while worn; picking the one the member wears
  takes it off; picking one worn by another member with no free copy moves it (the second Earth Ring is a free
  copy). The list's OK/NO mark for a card is whether the member can wear it (0x02063D88 compares with 7).
- **Points** (cave_card_count in place of the equip page's count block 0x0205D788): a monster card shows its points
  as current/max (glyphs from the menu's short strings: digits 0 to 9, 10 blank, 11 "/"), a boss card nothing,
  anything else "x" and the count as before.
- **Seen** (`test_card_equip_menu` again, Quetzalcoatl at 1500 points): the box shows 1500/2000; after A the card
  stays listed and, with Sasquatch highlighted, the box shows Quetzalcoatl as worn and no count for Sasquatch.
  `test_card_equip_move` (Jian and Lucia): Jian slots Quetzalcoatl; on Lucia's page it is still listed and A moves
  it (Lucia 236, Jian 0); A again takes it off (Lucia 0); back on Jian's page A slots it again.
- **Open, for Jeff with pictures:** how the list marks an entry worn by someone else, and whether the box's "new"
  side should read blank when the pick takes the worn item off (it shows the item's name today).
- **Review fixes.** Moving a ring or card with no free copy now clears only the first member who wears it (with
  both Earth Rings worn, a third member's pick took both). The two loops that hide the box's icon when the worn
  slot is empty (0x0205CF60 and 0x0205D670, states 0x18 and 0x19) ask cave_card_worn too, so the Cards page and
  the ring slot behave as the game's own pages do: with nothing worn the box shows a black square on the worn
  line and no icon beside the new item, exactly as the Accessories page does for a member with no accessory
  (`diag_empty_worn`, on the build without the card feature). Not changed: func_02056420's preview (types 0 to
  4 only) belongs to a screen that never offers a dragon ring or a card.

### 11.4 Leaving members and old saves (2026-11-25)

- The leave wrapper of `leave-drops-gear` (feat_party.py) clears seven slots instead of five, so a leaving
  member's card and ring stay with the party; without the card feature the two extra slots are always 0.
  **Not seen in the emulator:** `test_leave_gear` no longer reaches its leave (the opening now skips Jian's
  wake-up scene it pokes; it fails the same way on the build without the card feature), so `test_card_leave`,
  made from it, needs a new way to the leave.
- An old save is read back (func_0206d7fc, at its `mov fp, #1`) with any dragon ring in an accessory slot moved
  to the empty ring slot (cave_card_load_rings). **Seen** (`make_old_ring_save` on the build without the card
  feature: Jian wears the Blazing Ring as his accessory and saves; `test_card_old_save` on the new build loads
  it): slot 4 is 0 and slot 6 is 0xCB.

### 11.5 The Status page (2026-11-25)

feat_card_status.py. State 8 draws the box's rows; the two item loads (0x0205B17C for the empty test and the
row's icon, 0x0205B1DC for the name) read entry (row + offset) of the list slot 0 to 4, ring slot, card slot;
state 9's first instruction (0x0205B364) reads Up and Down and redraws through state 8; state 7's first
(0x0205AEE0) puts the offset back to 0, so the page opens and each L/R switch starts at the top. After the rows
(0x0205B220) an up arrow (menu glyph 14) at column 0x1D, row 4, and a down arrow (glyph 15) at row 16 show rows
hidden above or below; the rows' text colour argument is 1 (the Item page's 5 draws nothing here).

The ring icon: the menu icons are cell list sysmenupack 30 (CLT8: 20 frames of one 16x16 piece, frame 2n an
icon, 2n + 1 its greyed twin in the second palette) over art sysmenupack 42 (NTC8: two palettes, 52 tiles: sword,
armor, hat, bracelet, amulet, bag, card, a 32x32 box, bag, key). The Ring item's icon (sysmenupack 54, item 0xD7)
is mapped to the art's first palette and appended as tiles 52 to 55, and frames 20 and 21 copy the sword's two
pieces with tile 52.

**Seen** (`test_card_status`, Jian with the Blazing Ring and the Sasquatch card, Lucia in the party): five rows
and a down arrow; Down twice shows gloves to card, the ring row with the gold band and the card row with the card
icon, and an up arrow; Down again does nothing; R to Lucia and L back start at the top; the top menu and the Item
page's icons are unchanged.

### 11.6 Dragon Magic for anyone (2026-11-25)

feat_ring_slot.py: at the end of func_02050c50 (`cmp r6, #1`, 0x02050DDC) a ring spell is listed exactly when the
member wears its ring in the ring slot; casting follows from func_02050a74. **Seen** (`test_ring_lucia`, Jian and
Lucia, Lucia wearing the Blazing Ring, the Tidal Ring only in the bag): Lucia's list shows Healing Water and
Inferno; Inferno costs her 10 MP (18 to 8) and hits every enemy (556); Jian, wearing no ring, has nothing listed.
The look: the cast swaps Lucia's sprite for Jian's mid-cast, because the Dragon Magic files (btldata 19 to 22)
are Jian's body in the cast poses; the pillar on the enemies is a separate effect (`diag_dragon_magic_*` record the
four spells as Jian casts them). Jeff (2026-11-25): keep the right character and the right effect. Built: the
action setup's switch on spell - 10 (0x020686A8) is skipped for a caster who is not Jian, so its default puts the
caster's own Special file in slot 0; the cast script is unchanged, and the ring's effect (flame pillar, water,
wind cloud, earth aura), which does not come from that file, plays as for Jian. **Seen** (`test_ring_look_*`,
Lucia wearing each ring): she steps up and raises her umbrella in her own pose, the ring's effect plays around
the enemies, and each enemy takes the damage (556 for Inferno). Decision 3's element bursts are not used.

### 11.7 Cards in the Special list (2026-11-25)

The card ability is one spell id, 63 (skills_cards.py, in the skills list so every spell table covers it: learn
level past the last, so never learned by level; all enemies, so the menu takes it with no picker). Steal moves to
64. feat_card_use.py: the listing tail (cave_ring_listed) lists it in battle for a member whose card slot holds a
battle card (a monster card that is not a field card) with at least 100 points (cave_card_usable);
func_02050a74 returns 1 for it at once, the "cost" the menu needs to accept the pick; when the action runs, the
resolver's party branch (0x02051A08) turns a Special with spell 63 into the item command (4) with the worn card,
before the Special branch's silence test and MP charge, so the card's effect, animation, and points are the
game's. **Seen** (`test_card_use`, Lucia wearing Quetzalcoatl at 2000 points): her list shows Healing Water and
the card entry ("Use the card in your slot"); A uses it in her item pose, ATK DOWN on every enemy, points 2000 to
1900, MP unchanged. The name bar shows the worn card's name (the skills' name hook, for spell 63, takes the item
name of the member's card slot) and its uses left, points / 100 (cave_card_bar in place of the cost at
0x02044E88, never marked short of MP): "Quetzalcoatl 20". The battle Item command opens the item list directly:
the command page's Item case (0x02036804) jumps to the Tools button's block of the Tools / Cards page (0x02036F2C),
and the list's Back (0x0203727C) goes to the command page (`test_card_item_command`: Item shows Healing Gum, B
the command page, Item again the list, Fight the enemy grid). A card at 0 points: func_0207f83c no longer takes it out of the bag
(0x0207F894) and returns 1 (0x0207F898), so no "Lost" line; the card spell's castable answer is -1 with no battle
card worn (not listed), 0 below 100 points (listed with the NO mark, refused), else 1 (`test_card_empty`: one use
at 100 points, then 0, the card still in the bag; next round "Quetzalcoatl 0" with the NO mark, A refused). Rules (feat_card_rules.py): a card's stage change in func_0206a2f8 goes
through cave_card_stage, which skips a raise on a stat already above 0 and a lowering on one already below 0
(the calls at 0x0206A398 and 0x0206A43C); a card's sleep, paralysis, or stone on a regular enemy is resisted
when the status loop's roll (0 to 99) is 70 or more (0x0206A560, where the game had "lands"). **Seen**
(`test_card_rules`, Quetzalcoatl in rounds 1 and 2): battler 9's ATK stage goes to -1 and stays there; points
2000, 1900, 1800. Not seen: the 70% roll.

Basic and upgraded, and the refusal (feat_card_targets.py). Each monster card has an 8-byte record built from
its effect entry and its pair (basic version: none, one enemy, one ally, or Namia's regen; what "would change
nothing" means: the stats it moves and which way, its status, or its battle flag bit) and two learner slots
(character, learn level index: a skill's level, or the healers' spell-levels schedule for Tender Rain, Divine
Rain, and Miracle Tears). cave_card_basic gives the basic version for a wearer who is not a learner or whose
level index is below the learn level; cave_card_targets turns it into target bits (one enemy, one ally, or the
card's own). The Special list's OK handler reads spell 63's bits from it (0x02036CE0, in place of the spell
table): a basic use opens the enemy grid or the ally picker as a one-target skill does, with the card's test
written into spell 63's effect record so the grid and the picker refuse a wasted pick through the skills' own
test; an all-target use is refused at the list when every living target would be unchanged (cave_card_idle:
every stat it moves already a stage past 0 that way, a status already held or a boss immune to it, or the battle
flag already set). The resolver's item branch takes the same bits (0x02051F58), and a one-enemy card uses the
enemy picked on the grid (0x02051F84, the skills' cave_skill_pick), Dagon included. Namia: func_0206a744 sets
Divine Rain's 5% bit (0x10) instead of Namia's 10% bit (0x08) for a wearer who has not learned Divine Rain
(0x0206A790, the actor from the battle work's +0x32). Tick with no living front-row enemy is never refused,
since the game turns it into a plain attack. **Seen:**
- `test_card_basic`: Lucia with Quetzalcoatl (not a learner) gets the enemy grid; one enemy's ATK goes to -1,
  points 2000 to 1900; with every enemy already at -1, the pick shows "No effect!", the grid stays up, and the
  points stay 1900.
- `test_card_upgrade`: Jian at level 9 (Weapon Break learned) with Quetzalcoatl: no grid, ATK DOWN on all five
  enemies, points 2000 to 1900; next round the card is refused at the list with "No effect!".
- `test_card_ally`: Lucia with Comet (Rufus's pair) gets the ally picker ("Who to use it for?"); Jian's INT goes
  to +1, points 1300 to 1200; with both at +1 the pick is refused.
- `test_card_namia`: Lucia (level 1) with Namia: the battle flags get 0x10, not 0x08; points 1300 to 1200.
- `test_card_auto`: Auto with Jian and Lucia both wearing Quetzalcoatl at 2000: several rounds, the points never
  move (Auto never uses the card).

Not seen: Shaitan's and Vitra's basic versions on a picked ally (the same picker as Comet, Kind NONE so no
refusal), a status card's refusal (the skills' status test, written into spell 63's record).

### 11.8 Every pair, basic and upgraded (2026-11-25)

`emu/gen_card_pair_plans.py` writes `test_card_pair_*`: one round of the first temple battle per case, the wearer
in party slot 1 (Jian in slot 0) at a level that makes the card basic (Lucia at 1) or upgraded (the learner at
a level past the paired skill), the effect watched in the battle stat records. The Special list is a 3 x 2 grid;
the card is its last entry, and Right from the last column goes to the next page (Gabryel at 26 has six skills
before it). **Seen**, points 1300 to 1200 in each:

| Card | Basic (Lucia, one picked target) | Upgraded |
|---|---|---|
| Abadon | one enemy's DEF -1 | Jian at 25: all five enemies' DEF -1 |
| Ikontabipu | the one roll missed (30%) | Jian at 25: three of five asleep (rolls 53, 0, 70, 34, 95: under 70 lands) |
| Shreeker | one enemy poisoned | Gabryel at 26: all five poisoned |
| Asmodee | one enemy blinded | Gabryel at 26: all five blinded |
| Tick | the one roll missed | Flora at 20 and Gabryel at 26: each paralysis one of five |
| Comet | (11.7) Jian's INT +1 | Rufus at 19: both allies' INT +1 |
| Namia | (11.7) bit 0x10 | Lucia at 13: bit 0x08 |
| Vitra | Jian picked, 100 HP to full, Lucia stays at 100 | Lucia at 13: both to full |
| Quetzalcoatl | (11.7) | (11.7) |

The 70% roll was broken until this run: the hook read r2, which the boss test's call before it overwrites, so
every sleep, paralysis, and stone from a card was resisted; it reads the roll from r5 now (the game computes it
there and copies it to r2). Not seen: Shaitan (a knocked-out ally could not be set up by poking HP: the game
still gave Jian his turn), a status card's refusal.

### 11.9 Icons and renames (approved list, point 1; 2026-11-25)

`feat_skill_icons.py` (feature `skill-icons`, both editions). The Special list's boxes already draw a picture
per spell from sysmenupack entry 0x35 (a palette and 256 images, image = spell - 1); the game fills only
images 0 to 14, so every skill from id 38 was a blank box. The entry is rebuilt on the item icons' palette
(entry 0x36), with every listed spell's image: the PNGs in `art/icons/`, the Boots for Escape, the four
Dragon Rings for Dragon Magic, and the game's own sigil (recolored) for Quick, Grand Weapon, and Grand Shell.
The hook at 0x020357F4 copies the worn card's icon from the item icon file for the card entry. The field Magic
page reads the same file, so the healers' icons show there too.

Renames: Cure Squall to Cure Water in place in the string list (which the field Magic page shares); Loud Call
to Crashing Wave from the name cave (battle only; it is longer); Savage Rush, Venom Storm, and Feral in
`skills_gabryel.py`. Seen in the emulator: Gabryel's, Rufus's, and Lucia's lists with every icon, the card
entry with its card's icon (Comet, Shreeker), and the names Cure Water, Crashing Wave, Venom Rain, and Feral
Rage on the name bar. The first build reached Crashing Wave's string with an `adr` out of range: Keystone
prints the error and still returns a broken instruction, so highlighting the ring broke the list. It loads a
pointer now. To do: make the build fail on Keystone's printed errors (they bypass Python's stderr on
Windows; a check in a child process).
