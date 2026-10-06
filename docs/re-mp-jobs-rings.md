# MP and healing, Gad's Express jobs, equipment slots and Dragon Magic rings (reverse engineering notes)

Static analysis of the USA ARM9 binary (`extract/arm9/arm9.bin`, loaded at 0x02000000; file offset = address -
0x02000000) and the Ghidra output in `build/arm9_decomp_annot.c`, done 2026-10-06 for a design discussion. Nothing
here was run in an emulator. Each finding is marked **[confirmed]** (read in code or data, evidence given) or
**[uncertain]**. Notes about the PS1 Lunar games are from memory and marked **(unverified)**.

Character record base: this doc uses **0x020B4658 + id * 0x5C** (G + 0x40A8, the base `func_020554f4` and
`func_0206ecc8` use), as docs/re-field-battle.md does. docs/re-enemies.md uses 0x020B465C, 4 bytes later, so its
"+0x3C equipment" is the same memory as "+0x40" here (0x020B4698 for Jian).

Answers in one line each:

1. **MP.** Lucia starts with 18 MP and the basic heal costs 10, so the complaint is accurate. No shop sells any MP
   item, Mental Gum is not obtainable from any enemy or shop, and Mental Drop only drops from three bosses. MP items
   restore a percentage (Mental Gum 20%, which is 3 MP for Lucia at level 1). There are no working inns. Healing
   statues fully restore HP and MP. Recommendation: put Mental Gum and Mental Drop in every item shop and raise
   Mental Gum to a useful amount (data only), then playtest before touching spell costs or growth.
2. **Gad's Express.** Jobs are generated: 240 templates (required items and counts) plus a random recipient from the
   destination town. 10 recipient names in the job menu do not match the NPC's own name in the dialogue. No required
   item is strictly impossible, but many jobs offered by early offices need items that only drop in much later
   areas. Quitting costs 10% to 25% of the job's fee depending on rank, and the game keeps exactly one job slot.
   Recommendation: fix the names, and swap the late-only items in early offices' templates for items from the same
   office's own region (data only).
3. **Rings.** Five equipment slots: weapon, body, arm, head and one accessory. Dragon Magic rings are accessories, so
   only one works at a time. A dedicated ring slot is feasible but the equipment menu UI is the expensive part.
   Recommendation: let Dragon Magic work from the inventory (a few instructions in one function), which frees the
   accessory slot and lets all owned rings work at once.

---

## 1. MP and healing

### 1.1 The spell table **[confirmed]**

Table at **0x02094978**, 0x26 entries of 0x0C bytes (accessors `func_02050094` flags, `func_020500c4` cost,
`func_020500ac` +0x0A; availability `func_02050c50`, castability `func_02050a74`, effect `func_020500dc`):

| Offset | Type | Meaning |
|---|---|---|
| +0x00 | u32 | flags. 0x1 usable in the field, 0x2 usable in battle, 0x10 heal 1.25x to 1.74x caster INT, 0x20 heal 0.5x to 0.99x INT, 0x4 revive (HP = max HP / 10), 0x8000000 cure status, 0x1000000 / 0x2000000 / 0x4000000 stat buffs, 0x80 escape battle, 0x200 Gabryel, 0x400 Rufus, 0x100000 / 0x200000 / 0x400000 / 0x800000 Dragon Magic rings 0xCB to 0xCE, 0x40000000 all targets, 0x80000000 single ally |
| +0x04 | u32 | MP cost (file offset 0x9497C + spell * 0xC) |
| +0x08 | u8 | Lucia minimum level (all 0 for her spells) |
| +0x09 | u8 | Flora minimum level (all 0, except 255 for spell 5) |
| +0x0A | u16 | animation or effect index **[uncertain]** |

Heal amount (`func_02050850`): `INT * (rand % 50 + 125) / 100` for flag 0x10, `INT * (rand % 50 + 50) / 100` for
flag 0x20. INT is the caster's (record +0x30 in the field, battle actor +0x34 in battle). Capped at max HP, and a
target at 0 HP is not healed by these flags.

**Spells are learned by max MP, not by level.** `func_02050c50` shows a spell when the level byte is reached (always
true: the bytes are 0) **and** the character's max MP is at least the spell's cost. So Lucia "learns" Tender Rain
when her max MP reaches 30. Any change to MP costs or MP growth also moves when spells appear. Casting
(`func_02050a74`) checks current MP against the cost after reductions (`func_0206aabc`: cost / 2 for an equipped
item with effect 0x29, cost / 3 for effect 0x2A, minimum 1).

The Lucia and Flora spells (names from the battle string list at 0x020A44xx, in table order; the order matches the
flags, so the mapping is **[uncertain]** but very likely):

| # | Name | MP | Flags | Effect | Who |
|---|---|---|---|---|---|
| 1 | Healing Water | 10 | 0x80000013 | one ally, 1.25x to 1.74x INT, field and battle | Lucia, Flora |
| 2 | Tender Rain | 30 | 0xC0000023 | all allies, 0.5x to 0.99x INT | Lucia, Flora |
| 3 | Cure Squall | 8 | 0x88000003 | cure status, one ally | Lucia, Flora |
| 4 | Divine Rain | 40 | 0xC0000802 | battle only, all; sets battle flag 0x10 **[uncertain]** what it does | Lucia, Flora |
| 5 | Miracle Tears | 50 | 0x80000006 | revive one ally at 10% HP | Lucia only |
| 6 | Escape | 5 | 0xC0000009 | field only **[uncertain]** (dungeon exit) | Lucia, Flora |
| 7 | Quick | 20 | 0xC4000002 | stat buff (stat 6) | Lucia, Flora |
| 8 | Grand Weapon | 24 | 0xC1000002 | stat buff (stat 4) | Lucia, Flora |
| 9 | Grand Shell | 28 | 0xC2000002 | stat buff (stat 5) | Lucia, Flora |
| 10 to 13 | Inferno, Loud Call, Wind Cutter, Lunar Quake | 10 each | 0x40100102 etc. | Dragon Magic, one per ring 0xCB to 0xCE | Jian |
| 14 | Gale Cut | 10 | 0x40040202 | | Gabryel |
| 15 | Thunder Sword | 10 | 0x40080402 | | Rufus |

Entries 16 to 37 cost 1 or 10 and have no names in that list (enemy or internal skills **[uncertain]**).

### 1.2 MP growth **[confirmed]**

`func_020554f4` recomputes all eight stats from the level using the per-character table at **0x02094B4C**
(0x60 bytes per character: for each of HP, MP, ATK, DEF, AGI, INT, DEX, LUCK a triple {level-0 value, level-98 value,
curve mode}), evaluated by `func_020552cc`. Every character uses mode 0, linear:
`stat = min + (max - min) * level_index / 98` (level index 0 = level 1). MP entry: +0x0C min, +0x10 max, +0x14 mode.
Mode 1 is a stepped curve using the 6 weights at 0x020A5864; unused. Gear adds no HP or MP (item stats are ATK, DEF,
AGI, INT, DEX, LUCK only). On level-up current MP is rescaled to the new maximum, not refilled
(docs/re-field-battle.md section 3).

| Character | MP L1 | L5 | L10 | L20 | L30 | L50 | L99 | INT L1 / L10 |
|---|---|---|---|---|---|---|---|---|
| Jian | 10 | 14 | 20 | 31 | 42 | 65 | 120 | 4 / 22 |
| Lucia | 18 | 29 | 43 | 72 | 101 | 159 | 300 | 14 / 49 |
| Gabryel | 16 | 21 | 29 | 43 | 58 | 88 | 160 | 9 / 35 |
| Flora | 18 | 27 | 40 | 64 | 89 | 139 | 260 | 14 / 49 |
| Rufus | 10 | 13 | 18 | 27 | 36 | 55 | 100 | 5 / 24 |

So at level 1 Lucia casts Healing Water once (10 of 18 MP, 56%) for 17 to 24 HP; Jian has 28 max HP. At level 10
she has 4 casts (43 MP) healing 61 to 85 of Jian's 117 max HP. She learns Tender Rain at level 6, Divine Rain at
level 9 and Miracle Tears at level 13 (first level whose max MP reaches the cost).

### 1.3 Healing and MP items **[confirmed]**

Item table 0x0209B068, 0x14 bytes per item (type u16 at +0, effect id u16 at +2, six stat shorts at +4, price u32 at
+0x10; sell price is half unless type has 0x8000). Medicine effects are 0x0C-byte entries at 0x0209D124 indexed by
`effect - 0x100`: u32 flags, u16 HP percent (+4), u16 MP percent (+6). `func_0206a8b8` applies them in the field and
in battle: `HP += maxHP * value / 100` (flag 0x10), `MP += maxMP * value / 100` (flag 0x20). **They are
percentages.**

| Item (id) | Effect | Buy price | Where it comes from |
|---|---|---|---|
| Healing Gum (0x114) | 30% HP | 15 | every item shop |
| Healing Drop (0x115) | 60% HP | 80 | every item shop; Sasquatch, Raft, Sharif drops |
| Mental Gum (0x116) | 20% MP | 30 | **no shop, no enemy drop**; chests or events only, if anywhere **[uncertain]** (chest contents not read) |
| Mental Drop (0x117) | 50% MP | 240 | **no shop**; boss drops only: Armored Boar 50%, Moran 100% x2, Deuce (orb guardian) 50% |
| Antidote (0x118) | cure | 10 | every item shop |
| Paraclean (0x119) | cure | 20 | every item shop |
| Prayer Water (0x11A) | cure + 10% HP | 100 | not sold |
| Angel's Tears (0x11B) | revive 10% HP | 300 | every item shop |
| Dragon's Wing (0x11C) | effect 9 **[uncertain]** (likely escape or warp) | 80 | not sold |

Percent MP restore is weak exactly when MP is scarce: Mental Gum gives Lucia 3 MP at level 1 and 8 MP at level 10;
Mental Drop gives 9 and 21.

MP cost reducers: Holy Umbrella (item 21, Lucia's weapon, effect 0x29, 2300 S, sold in the town of maps 0xC7 to
0xC9) halves her spell costs; Magic Booster (item 200, accessory, effect 0x2A, not sold) divides them by 3.

### 1.4 Shops **[confirmed]**

shoppack.dat holds only graphics (CLT8 cell layouts). The inventories are in ARM9. `func_0206be90` builds the
6-item page list for the current shop from 30-entry u16 lists (0x3C bytes each), chosen by the current map id
(`*(s16 *)0x020B6BE4`) and the shop slot index `*(u16 *)(0x020B77E4 + 0x54)` (1 weapons, 2 armor, 3 items, 4 to 6
sundries). `func_0206bcb4` picks the shop type from the same map ranges.

| Maps (town) | List base (slot 1 at base, slot n at base + (n - 1) * 0x3C) | Slots |
|---|---|---|
| 0x97 to 0x99 (first town, script 001, Gad's head office) | 0x0209D914 | 3 |
| 0xA6 to 0xA8 (script 003) | 0x0209D644 | 3 |
| 0xBA to 0xBC (script 005) | 0x0209D6F8 | 3 |
| 0xC7 to 0xC9 and 0xD0 (script 007) | 0x0209DAB8 | 6 (slot 4 empty) |
| 0xE0 (script 009, accessory shop) | 0x0209D608 | 1 fixed list |
| 0xE2 to 0xE5 (script 010) | 0x0209D9C8 | 4 |
| 0xE9 to 0xEB (script 011) | 0x0209D7AC | 3 |
| 0xF9 to 0xFB (script 012) | 0x0209D860 | 3 |

Every item shop (slot 3) sells exactly the same five things: Healing Gum, Healing Drop, Antidote, Paraclean,
Angel's Tears, with 25 empty entries left in each list. No shop anywhere sells Mental Gum, Mental Drop, Prayer
Water or Dragon's Wing. The accessory shop at map 0xE0 sells 11 rings and charms (Evasion, Protection, Magic,
Lucky, Refresh, Resist, Alert rings, Amulet, Talisman, Spirit Guard, Amethyst). Full lists: run the dump in the
appendix.

Side finding: when the shop slot index is 4 and the shop is not in buy mode, prices are multiplied by 150%
(`func_02046910`, `func_02046b94`), so selling to the first sundries shop pays 1.5x **[uncertain]** what that shop is.

### 1.5 Other MP recovery **[confirmed unless marked]**

- **Healing statues**: the field loop `func_0201e6a0` (decomp around line 26977) sets HP = max HP and MP = max MP for
  the three party slots when the player uses a map object whose id is 0x37D (with a facing check). Status is not
  touched, which matches the "statues do not cure poison" complaint. How many statues exist and where needs the map
  data **[uncertain]**.
- **Inns**: none found. The only inn dialogue (script 005, Tartallia) always says all rooms are taken. **[uncertain]**
  that no other script has a paid rest; no script heal opcode was found in the text search.
- **Area clear**: `func_0206ecc8(30, 30)` gave +30% HP and MP when a map was cleared. Our `no-clear-refill` feature
  removed it, so in this hack the statues and items are the only MP sources.
- Level-ups do not refill (rescale only).

### 1.6 What the PS1 games did (unverified)

From memory, not checked: in Silver Star Story Complete and Eternal Blue Complete every town has an inn that fully
restores HP and MP for a small fee, MP-restoring items are sold in ordinary shops, and dungeons have save or healing
points. Healing spells are cheap relative to the MP pool from early on. Treat all of this as unverified.

### 1.7 Options

| Option | How | Work | Risk |
|---|---|---|---|
| A. MP items in shops | Write item ids 0x116 and 0x117 into free entries of each item shop list (slot 3 bases above). Data only | under an hour | none technical; Mental Drop at 240 S may still be expensive early, check with battle silver |
| B. Stronger MP items | Raise the MP percent at 0x0209D124 + 2 * 0xC + 6 (Mental Gum) and + 3 * 0xC + 6 (Mental Drop), for example 40% and 100%; or change the price at item + 0x10 | minutes | percentages stay weak at low level; a flat amount needs a code change in `func_0206a8b8` (new code, small) |
| C. Lower spell costs | Edit the u32 at 0x0209497C + spell * 0xC, for example Healing Water 10 to 6 | minutes | also makes spells appear earlier (learning is "max MP >= cost"); Tender Rain at 20 would come at level 2 instead of 6. Can be decoupled by patching the cost check in `func_02050c50` to use a separate threshold |
| D. Raise MP growth | Edit MP min/max at 0x02094B4C + char * 0x60 + 0x0C / + 0x10 | minutes | same spell-timing coupling; also helps Jian's Dragon Magic. Existing saves update at the next stat recompute |
| E. Statues also cure status | Clear the status low bits (record +0x08) in the statue block | small ARM patch | low |
| F. Partial area-clear refill, MP only | Restore the `func_0206ecc8` call with (0, 30) | small, we already patch that site | goes against design item 2 (no clear refill); a design decision, not a technical one |
| G. Inns | New script content or reuse of the statue routine at an NPC | larger (map/script work) | moderate |

**Recommendation: A plus B first** (data only, no code risk): sell Mental Gum (30 S) and Mental Drop (240 S) in every
item shop from the first town, and raise Mental Gum so one Gum is about one Healing Water at level 1 (for example 60%
gives 10 MP at level 1, 25 MP at level 10). Playtest, then consider C with the threshold decoupled if healing still
feels starved. D is the most "Lunar-like" but changes spell timing and late-game balance for every character.

---

## 2. Gad's Express delivery jobs

### 2.1 How jobs work **[confirmed]**

Jobs are generated, not a fixed list. Code: `func_0204ccd4` (the Gad's Express menu), `func_0206cfc0` (build the
four offered jobs), `func_0206cc2c` (destination, recipient, fee), `func_0206c98c` (load the current job),
`func_02071e94` (have the items?), `func_02071e24` (take the items).

- **Templates** at **0x020A8E3C**, 241 entries of 0x1A bytes (0 is empty): u16 item[5] at +0, u16 count_raw[5] at +0x0A
  (count = raw / 4 + 1), u16 at +0x14 = 1 for "Package supplied" jobs, u8 rank 1 to 4 at +0x16, u16 at +0x18 = its
  own index. Except the Package jobs, **the player must bring the listed items from the inventory**; they are removed
  on delivery.
- **Offices** (Gad's office map, template pool): 0x9A (first town) 1 to 40, 0xA9 41 to 80, 0xBD 81 to 120, 0xCA 121 to
  160, 0xEC 161 to 200, 0xFC 201 to 240 (pools at 0x0209DEB4, 0x0209DF04, 0x0209DF54, 0x0209DDC4, 0x0209DE14,
  0x0209DE64). Each office offers 4 distinct random templates from the first `rank * 10` entries of its pool. Within
  each block of 40: entries 1 to 10 are rank 1, 11 to 20 rank 2, and so on; the first of each block is the Package job.
- **Rank** per office: completed-job counters at 0x020B4864 + office (6 bytes); rank = min(4, (count - 1) / 5 + 1). So
  the rank rises every 5 deliveries made from that office, regardless of story progress.
- **Destination**: a random unlocked place (7 unlock bytes at 0x020B486A, set by `func_0207200c`), places 0, 0x29,
  0x2A, 0x36, 0x37, 0x39, 0x3A (table 0x0209DCDC). Then a random recipient in that place: per-place lists of target
  map (s16) and recipient index (below). The Package job goes to another Gad office (recipient 0, Gad).
- **Recipient**: the job stores the recipient's "value" from 0x0209DFA4[index]; the town's event script compares its
  job variable with that value (`if_cmp_call 0d000201...`) and runs that NPC's "A package for me?" block. The menu
  shows string 74 + index of the shop string table (u16 offsets at 0x020A4D28, text at 0x020A4E2C).
- **Fee**: sum of item sell value x count, adjusted for item variety and rank, times an office factor (0x0209DC88:
  270, 260, 300, 290, 280, 265 %), a rank factor (0x0209DC40: 200, 150, 125, 110 %) and a distance factor
  (0x0209DC58: 100 to 115 %). Stored at 0x020B4860.
- **Current job**: one slot only: template 0x020B4858, place 0x020B485A, map 0x020B485C, recipient value
  0x020B485E, fee 0x020B4860. The menu refuses a second job ("Already have a Job!").
- **Quitting** (menu case 0xF, `func_0206c2d4`): costs **fee x {10, 15, 20, 25}% for rank 1 to 4** (table
  0x0209DC4C), and a supplied Package is taken back. The first story job apparently cannot be quit: the menu shows "Cannot cancel job" while the byte at 0x020B4871 (set by `func_02071d04` after the first delivery) is 0 **[uncertain]**.

### 2.2 Recipient names that do not match the NPC **[confirmed]**

Menu name (string table, ARM9) against the speaker name in the same NPC's delivery dialogue (script text), matched by
recipient value and town script:

| Menu shows | NPC calls themselves | Place / map | Script | Likely correct (my reading) |
|---|---|---|---|---|
| Balam | Bram | 0 / 0x97 | 001 | unclear, pick one |
| Timathy | Timothy | 0 / 0xA2 | 001 | Timothy |
| Gobbi | Gobi | 0x2A / 0xB3 | 004 | Gobbi (the town's names are Italian opera figures) |
| Paoro | Paolo | 0x2A / 0xBB | 005 | Paolo |
| Tartaglia | Tartallia | 0x2A / 0xBF | 005 | Tartaglia |
| Laban | Raiban | 0x36 / 0xCB | 007 | Laban (biblical, like Absalom and Ira next to him) |
| eva | Eva | 0x36 / 0xD2 | 007 | Eva |
| Pazolini | Pasolini | 0x37 / 0xDC | 008 | Pasolini |
| Devida | Davida | 0x39 / 0xEB | 011 | unclear |
| Esthel | Esther | 0x3A / 0xFB | 012 | Esther |

The other 44 names match. The r/l and spelling swaps look like romanization errors. Players following the menu name
look for an NPC who never introduces himself by it. **[uncertain]** whether any destination map is unreachable at
some story point (for example a town closed by the story); that needs playing.

### 2.3 Rare or impossible items **[confirmed for the data, area order uncertain]**

Cross-check of all 240 templates against every enemy drop row (0x02097588) and every shop list:

- **No required item is strictly impossible.** Every item is either sold (the sundries shops at maps 0xE2 to 0xE5 and
  0xC7 to 0xC9 / 0xD0 sell some of them) or dropped by at least one enemy row, and every normal enemy row appears in
  some area group's formation pool (0x020A789C).
- **Many are effectively impossible when offered.** Because rank grows with deliveries, not story, an early office
  soon offers jobs whose items only drop in much later areas. Examples from the first town's office (0x9A), with the
  only area groups whose enemies drop the item and that group's minimum enemy level as a stand-in for story order:
  template 11 (rank 2) Shiro's Tail x5: group 10 only (level 25+); 18 and 19 (rank 2) Wooden Doll x5: group 11 only
  (29+); 23 (rank 3) Shell x3: group 13 only (24+); 31 (rank 4) Galvoln: groups 16 and 19 (32+); 39 (rank 4) Stuffed
  Animal: group 15 only (36+). Every office has roughly 20 to 30 such item entries in its templates; the second office (0xA9) asks for
  Fire Heart, Steel, Tidal Heart, Earth Heart and Plastic Case.
- Single-source items with one drop row at 20 to 35%: Sun Rays (one Gloomwing variant, group 10), Steel (one Blob
  variant), Gold Nugget (one Comet variant), Galvoln (one Thanatos variant), Cow Bone (one Mad Fang variant), and
  about 60 more; the appendix script lists them.
- In the original game drops only came from Combat-mode battles and thieves steal exactly these items (ids 287 to
  386, docs/re-enemies.md section 4). The hack already drops items in every battle and returns stolen items, which
  softens this a lot.
- "Area group to story order" is **[uncertain]**: it uses the area minimum level from docs/re-enemies.md.

### 2.4 Options

| Option | How | Work | Risk |
|---|---|---|---|
| Fix names in the menu | Rewrite strings in the shop string block (0x020A4E2C) and rebuild its u16 offset table (0x020A4D28); the 10 fixes shrink the block by 1 to 3 bytes overall, so it fits in place | a few hours with a small builder | low; the block is shared with shop texts, so rebuild all offsets, not just one |
| Fix names in the dialogue | Change the speaker tags with the existing `text-edits` feature (scripts can grow) | small per name | low; best for names where the dialogue is wrong (Gobi, Tartallia, Raiban) |
| Replace late-only items in early templates | Edit item ids and counts in the 0x1A-byte templates at 0x020A8E3C so each office only asks for items that drop in or before its region, or that are sold | half a day (needs a table of "available by office") | low; the fee is computed from item prices, so it adjusts by itself |
| Gate rank by story | Cap `func_02071fa8`'s result by a story flag or by the number of unlocked places | small ARM patch | low to moderate |
| Lower or remove the quit fee | Zero the four shorts at 0x0209DC4E..0x0209DC54 (data only) | minutes | none; the design doc keeps jobs as optional income, so a free quit fits |
| Several jobs at once | New job slots in the save, new menu, delivery check per slot | large | high (save layout, menu UI, script variable) |

**Recommendation:** fix all 10 names (menu or dialogue, whichever is wrong per the table), zero the quit fee, and
retarget the late-only items in the first three offices' templates. Leave one-job-at-a-time alone: with battle
silver the jobs are optional, and multiple slots is the only expensive change here.

---

## 3. Equipment slots and Dragon Magic rings

### 3.1 Slots **[confirmed]**

Each character has **five u16 slots at record + 0x40** (0x020B4698 + id * 0x5C), and the slot index equals the item
type (low nibble of the item type word): **0 weapon, 1 body, 2 arm, 3 head, 4 accessory**. Equipping
(`func_0206b46c`) writes the item into slot `type`; bits 4 to 8 of the type word say who may equip it (0x10 Jian,
0x20 Lucia, 0x40 Gabryel, 0x80 Flora, 0x100 Rufus). So there is exactly **one accessory slot**, and every ring,
charm and Dragon Magic ring competes for it.

Record layout around the slots: +0x40..+0x49 slots; +0x4A..+0x59 eight shorts filled by `func_0206b4d8` (equipment
stat totals: +0x4E..+0x58 are ATK, DEF, AGI, INT, DEX, LUCK bonuses; +0x4A and +0x4C are only zeroed at init
**[uncertain]** whether anything reads them); +0x5A..+0x5B no literal reference found **[uncertain]** (padding).

Side finding: `func_0206b4d8` halves all equipment stat bonuses when `*(0x020AFF84 + 0x88) == 3` **[uncertain]**
what state that is (possibly Jian's curse).

### 3.2 Dragon Magic **[confirmed]**

- Rings: Blazing Ring 0xCB (203), Tidal Ring 0xCC, Gale Ring 0xCD, Earth Ring 0xCE. Type 0x8014: accessory, Jian
  only, not sellable; each gives +10 INT. Dropped 100% by the four dragons (docs/re-enemies.md).
- **Listing** (`func_02050c50`, Jian = id 0): a spell with ring flag 0x100000 / 0x200000 / 0x400000 / 0x800000 is shown
  if the matching ring is **in the inventory** (`func_0206ba54(0x0213B930, ring)`), plus max MP >= cost.
- **Casting** (`func_02050a74`): the same spell is usable only if the ring is **equipped** (`func_0206b8ec(ring, 0)`
  searches all five of Jian's slots). The four checks are independent `if`s, so the code would allow several rings at
  once; only the single accessory slot prevents it. The spell table entries 10 to 13 are otherwise ordinary (10 MP).
- Callers of `func_02050a74`: battle menu (around decomp lines 41261, 41712, 42210, 42292), battle AI or auto
  (58339), field menu (62481, 69669). No other code checks for 0xCB to 0xCE.

### 3.3 What a dedicated ring slot would take

| Part | What changes | Size |
|---|---|---|
| Record layout | A sixth u16. Slot 5 at +0x4A falls naturally out of the `slot * 2` indexing, but +0x4A is inside the stat-total block (only zeroed today); +0x5A is the other candidate. Must be proven unused with a write watch | small, needs verification |
| Save format | None if the slot stays inside the 0x5C record (the record is part of the saved G block) **[uncertain]**: confirm the save copies the whole record | none to small |
| Equip routing | `func_0206b46c`: send 0xCB to 0xCE to slot 5 instead of slot `type` | small |
| Slot loops | Change `< 5` to `< 6` in `func_0206b8ec` (has item equipped), `func_0206b0fc` users (`func_0206ab6c` battle effects, `func_0206aabc` MP cost), `func_0206b4d8` (stat totals), `func_0206b880`, `func_02055760`, `func_0206b144`; leave the break picker `func_0206b1d0` at 4 | about 10 one-instruction patches |
| Equipment menu UI | `func_02064824`, `func_02064a4c`, `func_02065240`, `func_02059f84`, `func_02056420` have one hardcoded case per slot (1 to 5) with literal slot addresses; a sixth row needs layout cells (sysmenupack CLT8 data), touch areas, cursor movement, labels, the stat-preview path and unequip | the bulk of the work |
| Stat recompute | `func_02054ebc` / `func_0206ab6c` run off the slot loops, so they follow once the loops are 6 | covered above |

Estimate: 3 to 6 days including emulator testing, most of it the menu. Risk medium to high: menu layout data is not
yet reverse engineered, and a missed `< 5` loop silently ignores the ring.

### 3.4 Cheaper alternatives

| Option | How | Work | Risk / effect |
|---|---|---|---|
| **A. Dragon Magic from the inventory** | In `func_02050a74`, Jian branch: accept the spell when `func_02050c50` already said yes (it only does so when the ring is owned), i.e. skip or force the four `func_0206b8ec` tests. One branch or four call sites | an hour plus a battle test | low. All owned rings work at once; the accessory slot is free for other rings. Rings still give +10 INT only when equipped |
| B. Rings count from the inventory but only one at a time | Same patch, but pick the "active" element from a new menu toggle | days (UI) | moderate |
| C. Equipped ring counts for all owned rings | Accept a ring spell if any Dragon Magic ring is equipped and the matching ring is owned | small | low; keeps the accessory cost but removes the one-element limit |
| D. Move rings to another existing slot | Retype rings to head (3) or weapon (0) | data only | bad trade: costs headgear or weapon |

**Recommendation: A.** It is the smallest change, touches no menu or save data, and answers both complaints (one
spell at a time, costs the accessory slot). The remaining complaint ("the same spell with different elements") is
about content, not slots. Watch the balance: Jian then has four 10-MP spells and only 10 to 42 MP early, so MP still
limits him.

---

## Emulator checks that would close the open points

1. Mental Gum on Lucia at level 1 (pin 0x020B4670 MP low, give item 0x116 at 0x0213B930 + 0x115): MP should rise by
   3 (20% of 18).
2. With a Dragon Magic ring only in the inventory, open Jian's Special list: expect the spell listed but not usable
   (`func_02050a74` returns -1). After option A it should cast.
3. Write-watch record +0x4A, +0x4C and +0x5A..+0x5B (Jian: 0x020B46A2, 0x020B46A4, 0x020B46B2) through equip, battle,
   save and load, to confirm a free u16 for a sixth slot.
4. Use a healing statue while poisoned: HP/MP full, poison stays.
5. Take a job at the first office and read 0x020B4858..0x020B4861; quit and check silver drops by fee x 10%.
6. Visit Raiban / Laban (map 0xCB) with a job for "Laban" to confirm the recipient value 50 matches.

## Appendix: how the tables were dumped

Scratch scripts (not committed) read `extract/arm9/arm9.bin` with `dsde.enemies.read_names` for item names and
the decoding above: spell table 0x02094978, growth 0x02094B4C, medicine effects 0x0209D124, shop lists
0x0209D608..0x0209DC1F, job templates 0x020A8E3C, recipient tables 0x0209DC34..0x0209DDC3 and 0x0209DFA4,
formation pools via 0x020A789C, drops via 0x02097588. Script speakers came from
`uv run python -m dsde.script build/unpacked/script/NNN.bin --text` (scripts 001, 003, 004, 005, 007, 008, 009, 011, 012).
A `dsde` command that prints these tables would be a natural follow-up if any of the options is built.
