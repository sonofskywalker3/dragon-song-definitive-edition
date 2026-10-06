# Enemies, level scaling, EXP, stealing and breaking (reverse engineering notes)

Static analysis of the USA ARM9 binary (`extract/arm9/arm9.bin`, loaded at 0x02000000) and the Ghidra
decompilation in `build/arm9_decomp.c`. Function names are the dsd/Ghidra `func_<address>` names.
Ghidra prints globals as `DAT_<literal pool address>`; the value in the pool is given where it matters.

Each finding is marked **[confirmed]** (read directly from code or data, evidence given) or
**[uncertain]** (inference). "Confirmed" here means "the code says so"; nothing below has been run in an
emulator yet. The last section lists the in-emulator checks that would close the open points.

Tooling: `uv run python -m dsde.enemies` prints every enemy row with names, stat ranges, EXP, actions
(steal and break flagged) and drops; `--level N` prints the stats at enemy level N; `--out FILE` writes
the table to a file. Code: `src/dsde/enemies.py`.

## Key addresses

| What | Address | Evidence |
|---|---|---|
| Enemy stat table, 157 rows of 0x54 bytes | 0x02097CE4 to 0x0209B068 | pool words at 0x02054478, 0x02054DB4, 0x02069578 and others all hold 0x02097CE4; rows are indexed `id * 0x54` |
| Enemy drop table, 157 rows of 0x0C bytes | 0x02097588 to 0x02097CE4 | `func_02069e00`, `func_02069dd0`, `func_02069f34` (pools 0x02069F2C, 0x02069DFC, 0x0206A26C) |
| Item table, 0x14 bytes per item id | 0x0209B068 | `func_0206b674`, `func_0206b98c`, `func_0206b1d0` |
| Broken-gear replacement table, u16 [slot][character] | 0x0209D0FC | `func_0206b1d0`, `func_0206b144` |
| Name strings (item ids, cards = 216 + species, party 270 to 274) | 0x020A7C2E, 0xFF separated, u16 offset table at 0x020A78EC | decoded by `dsde.enemies.read_names` |
| Character records, 0x5C bytes each, character id order | 0x020B465C (Jian) | cheat file (Jian HP 0x020B4668), `func_02054494` reads `0x020B05B0 + id*0x5C + 0x40AC..` |
| Character level (u32) | record + 0x08, Jian 0x020B4664 | written back from the battle actor's level in `func_02052888`; raised by the level-up code in `func_02052c2c` |
| Party slots (3 x u32) | 0x020B464C | cheat file; `func_02054494` reads `0x020B05B0 + i*4 + 0x409C` |
| Inventory counts, one byte per item id, index id - 1 | 0x0213B930 | `func_0206b98c`; cheat file "Have All Weapons" starts here with item 1 |
| Combat/Virtue mode flag (u8, 1 = Virtue, 0 = Combat) | 0x020B4848 (game state 0x020B45B0 + 0x298) | see section 3 |
| Silver | 0x020B4824 (game state + 0x274) | cheat file; only script opcode `func_02040160` and shops write it |
| Battle setup struct | 0x020B85B8 | `+0x00` area group, `+0x04` map, `+0x06` boss battle type, `+0x08` mode for this battle, `+0x48` loot list (4 x item/count), `+0x58` EXP pool |
| Battle actors, 0x6C bytes each (0 to 2 party, 4 to 11 enemies) | pointer stored at 0x020B8620 | cheat file "P1 infinite health" loads the same pointer |
| Battle objects, 300 bytes each (AI command +0x84, steal/break mark +0x88) | pointer stored at 0x020B8640 | `func_02054494`, `func_020514ec` |
| Battle work struct (card protection flags at +0, stolen item id at +0xDC, EXP counter at +0x148) | pointer stored at 0x020B8550 | `func_02030b44`, `func_0206a744`, `func_02052c2c` |

## 1. Enemy record layout **[confirmed]**

`func_02069ad8` (enemy stat setup) reads the row as `puVar5 = id * 0x54 + 0x02097CE4`:

```c
uVar2 = func_02069d7c((int)(short)puVar5[1],(int)(short)puVar5[6],uVar4);   // HP  (+0x04, +0x18)
*(undefined4 *)(param_1 + 0x1c) = uVar2;                                     // actor max HP
...
uVar2 = func_02069d54(puVar5[5],puVar5[10],uVar4);                           // EXP (+0x14, +0x28)
*(undefined4 *)(param_1 + 0x50) = uVar2;
```

| Offset | Type | Meaning | Evidence |
|---|---|---|---|
| +0x00 | u32 | flags. Bit 31 boss, bit 30 stagger gauge (dragons, Gideon 3), bits 0-1 AI aggression class, bits 4-7 differ between the four variants of a species (meaning unknown) | bit 31: `func_02069848`, `func_02030b44`; bit 30: `func_02069ad8` calls `func_02069ab0` (gauge = max HP / 4, min 100), used in `func_02053384`; bits 0-1: `func_02069848` |
| +0x04 to +0x12 | s16 x 8 | stats at level 0: max HP, max MP, attack, defense, agility, intelligence, dexterity, luck | actor offsets 0x1C, 0x20, 0x24, 0x28, 0x30, 0x34, 0x38, 0x3C, which `func_02052888` copies to the character record at the same offsets the cheat file names Max HP, Max MP, Atk, Def, Agi, Int, Dex, Luck |
| +0x14 | u32 | Althena Conduct (EXP) at level 0 | `func_02069d54(puVar5[5], puVar5[10], level)` into actor +0x50, which is what the kill code adds to the EXP pool |
| +0x18 to +0x26 | s16 x 8 | the same eight stats at level 98 | second argument of each `func_02069d7c` call |
| +0x28 | u32 | EXP at level 98 | |
| +0x2C | s16 x 4 | cumulative chance (out of 100) of picking action 0..3 | `func_02069a38`: first `i` with `rand % 100 <= chance[i]` |
| +0x34 + 8*i | u32, u16, s16 | action i: flags, extra value, skill id | `func_0206957c` (+0x34), `func_020699f0` (+0x38), `func_02069a14` (+0x3A) |

Action flags used in `func_020514ec`: bits 12-15 targeting (1 one random party member, 2 whole party),
**bit 27 (0x08000000) = steal**, **bit 26 (0x04000000) = break gear**, bit 8 = can be covered, bits
9-10 = use the skill id at +0x3A. `func_020514ec` sets the attacker's `+0x88` to 1 (steal) or 2 (break),
which the hit code in `func_02030b44` acts on (section 4 and 5).

There is **no level field, no silver field and no item field** in the 0x54 record. All 84 bytes are
accounted for above. Drops live in the separate drop table.

### Row id to enemy name **[confirmed]**

`func_0206892c` maps a row id to a species: rows below 0x88 use `min(id >> 2, 0x21)` (four rows per
species, species 0 to 33), rows from 0x88 up use `id - 0x66` (one row per boss, species 34 up). The
species index lines up with the enemy names in the name block, and the same index gives the card item
(`216 + species`), which `func_02069dd0` uses as `(id >> 2) + 0xD8`.

| Rows | Species |
|---|---|
| 0-3 Blob, 4-7 Onlooker, 8-11 Shreeker, 12-15 Namia, 16-19 Treant, 20-23 Ice Mongrel, 24-27 Mad Fang, 28-31 Yeti, 32-35 Termite, 36-39 Abadon, 40-43 Tick, 44-47 Bealzebub, 48-51 Insector, 52-55 Gloomwing, 56-59 Kuntukapu, 60-63 Ikontabipu, 64-67 Dagon | normal |
| 68-71 Hellbird, 72-75 Sturge, 76-79 Vitra, 80-83 Quetzalcoatl, 84-87 Comet, 88-91 Ohainkaru, 92-95 Shaitan, 96-99 Phantom, 100-103 Ochu, 104-107 Evil Earth, 108-111 Chupacabra, 112-115 Enigma, 116-119 Ghoula, 120-123 Thanatos, 124-127 Asmodee, 128-131 Duager, 132-135 Druid | normal |
| 136 Sasquatch, 137 Armored Boar, 138 Raft, 139 Sharif, 140 Moran, 141 Deuce, 142 Gronk, 143 Zethos, 144 Caucus, 145 Orcus, 146 Morus, 147 Red Dragon, 148 White Dragon, 149 Black Dragon, 150 Blue Dragon, 151 Dark Jian, 152 Gideon, 153 Gideon 2, 154 Gideon 3, 155 Ignatius, 156 (name slot is "Jian"; the Blue Dragon's bubbles, labelled "Bubble" in the enemy picker) | bosses |

Supporting evidence for the boss mapping: row 151 is special-cased in `func_02069ad8` to copy Jian's own
stats (HP x6, attack x4/5, defense x6/5), which fits Dark Jian; row 155 has 9999 HP and
`func_02053384` refills its HP every hit, which fits an unwinnable Ignatius fight; row 150 is the Blue
Dragon and `func_02030b44` makes its attacks with flag 0x1000000 summon four copies of row 156 (1 HP
each) in battle types 0x0B/0x12, so row 156 is a Blue Dragon summon, not a Jian enemy. The four rows of a
normal species are area variants with their own level 98 stats, EXP, AI and drops (for example Blob rows
reach 300, 360, 540 and 900 HP at level 98). **[uncertain]** which variant appears where (chosen by the
formation code in `func_0202b3f0` from the area group).

Boss battle type (battle struct +0x06) to row, from `func_0202b948`: 1, 0x13, 0x14, 0x15 Sasquatch
(the four Delrich Temple fights); 2 Armored Boar; 3 Raft; 0x0F Sharif; 0x10 Moran; 4, 0x16, 0x17, 0x18
row 141 "Deuce" (drops the Red, White, Black or Blue Orb depending on which of the four, see
`func_02069f34`); 5 Gronk; 6 Zethos; 7 Caucus (Orcus and Morus join through `func_0202b1a4`); 8 Red,
9 White, 10 Black, 0x0B and 0x12 Blue Dragon; 0x0C, 0x0D, 0x0E Gideon 1 to 3; 0x11 Ignatius; 0x19 Dark Jian.

### Steal and break actions in the table **[confirmed]**

Chance = chance that the enemy picks that action on a turn it acts.

| Steal (bit 27) | Rows: chance |
|---|---|
| Ice Mongrel | 20: 10%, 21: 20%, 22: 20%, 23: 30% |
| Yeti | 28: 20%, 29: 20%, 30: 40%, 31: 30% |
| Sturge | 72: 10%, 73: 20%, 74: 25%, 75: 10% |
| Ochu | 100: 10%, 101: 15%, 102: 20%, 103: 25% |
| Thanatos | 120: 10%, 121: 10%, 122: 15%, 123: 25% |
| Morus (boss) | 146: 30% |

| Break (bit 26) | Rows: chance |
|---|---|
| Abadon | 36: 20%, 37: 20%, 38: 20%, 39: 25% |
| Quetzalcoatl | 80 to 83: 20% each |
| Phantom | 96: 5%, 97: 10%, 99: 10% (row 98 never breaks) |
| Duager | 128: 10%, 129: 15%, 130: 20% (row 131 never breaks) |
| Moran (boss) | 140: 10% |
| Orcus (boss) | 145: 10% |

This matches the FAQ lists in `docs/research-bugs-thieves.md` exactly, except Treant: no Treant row
has the break flag, so Ripclaw's Treant entry is wrong.

### Drop table **[confirmed]**

Drop row (`0x02097588 + id * 12`): u16 chance[3] at +0, unused u16 at +6, item ids at +8 (slot 0) and
+0x0A (slot 1). Slot 2 is always the enemy's own card.

- Normal enemies (`func_02069e00`): roll `rand % 1000 + 1`, take the first slot whose chance is at
  least the roll, so the chances are cumulative. A typical row is (500, 700, 900): 50% item A, 20%
  item B, 20% card, 10% nothing. If the card is already in the inventory, slot 0 is given instead, so
  each card drops once. Every normal drop is a crafting material or sundry (ids 287 to 386), never
  equipment and never silver.
- Bosses (`func_02069f34`, rows above 0x87): each of the three slots rolls separately against its
  own chance; the card slot gives item `id + 0x72`. Examples: Sasquatch 100% Healing Drop, 50% card;
  Armored Boar 100% Counter Type 1, 50% Mental Drop, 50% card; the dragons give their element ring
  100%, the card 50%, and 40% an item whose id (270 to 273) shares its name string with a party member
  (**[uncertain]** what that item is in play).
- Drop level ("tier") in `func_02069f34`: normally 2 (one roll, one item). In area groups 6, 7 and 8 the
  story flags 0xD1, 0xD2, 0xD4, 0xD5 switch it to 0 (50% of drops cancelled), 1 (25% cancelled),
  3 (1 or 2 of the item) or 4 (roll limited to 501..1000 so a drop is guaranteed, 2 or 4 of the item).
  **[uncertain]** what those flags and areas are in the story.
- Drops do not depend on enemy level. **[confirmed]**, nothing in the drop code reads the level.

Full per-row dump: `uv run python -m dsde.enemies`.

## 2. Enemy level scaling **[confirmed]**

### Enemy level

In `func_02054494` (battle start), for each enemy:

```c
local_8c = max over the 3 party slots of record[+0x40B4]      // highest party level
local_88 = local_8c >> 3;  if (local_88 < 1) local_88 = 1;
uVar9 = (local_8c - local_88) + rand() % (local_88 + 1);       // func_02015f80 remainder
uVar6 = *(0x02139EE0);                                         // area minimum
if (uVar6 <= uVar9) { uVar6 = uVar9; if (*(0x02139EDC) < uVar9) uVar6 = *(0x02139EDC); }
enemy.level (+0x0C) = uVar6;
```

So **enemy level = clamp(P - r, area_min, area_max)**, where P is the **highest level among the three
party members** (not Jian alone), and r is uniform in 0..max(1, P/8). Each enemy rolls separately.
Fan sources that say "Jian's level" are close because Jian is usually the highest.

`func_0204f8b0` sets the clamp from the map index when a battle starts:

- `area_max = area_min + 20` if `area_min < 20`, else `min(2 * area_min, area_min + 35)`; then capped at
  80, but never below `area_min`. So enemies stop scaling at enemy level 80 at most, and much earlier
  in early areas (area min 0 caps at 20, min 11 caps at 31, min 25 caps at 50).
- Boss battle types override `area_min`: Sasquatch fights 7, Raft/Sharif/Moran 10, Zethos 10, Gideon 40,
  Gideon 2 and 3 42, Ignatius 97 (max then becomes 97 too). Other boss fights keep the area's value.

Area minimum by map index (map index = battle struct +0x04, area group = battle struct +0x00):

| Maps | Area group | area_min | Alternative |
|---|---|---|---|
| 0-1 | 0 | 0 | |
| 2 | 0 | 2 | |
| 3-4 | 0 | 8 | |
| 5-8 | 1 | 4 | |
| 9-13 | 1 | 5 | |
| 14-19 | 1 | 6 | |
| 20-30 | 2 | 11 | |
| 31 | 3 | 10 | |
| 32 | 3 | 28 | |
| 33-34 | 3 | 10 | |
| 35-37 | 4 | 22 | |
| 38-44 | 5 | 25 | |
| 45-47 | 6 | 12 | |
| 48-52 | 6 | 13 | |
| 53-57 | 7 | 15 | |
| 58-59 | 8 | 16 | |
| 60 | 8 | 17 | |
| 61-62 | 9 | 18 | 37 once story flag 0xC9 is set (group 19) |
| 63-64 | 9 | 19 | 38 after flag 0xC9 |
| 65-78 | 9 | 20 | 40 after flag 0xC9 |
| 79-82 | 9 | 21 | 25 after flag 0xC9 |
| 83-84 | 9 | 21 | |
| 85-86 | 10 | 25 | |
| 87 | 10 | 26 | |
| 88-89 | 11 | 29 | |
| 90-93 | 11 | 30 | |
| 94-99 | 12 | 23 | |
| 100-105 | 13 | 24 | |
| 106-111 | 14 | 28 | |
| 112-120 | 15 | 36 | |
| 121-128 | 16 | 32 | |
| 129-139 | 17 | 34 | |
| 140-150 | 18 | 10 | |
| other | 0 | 0 | |

**[uncertain]** which map index is which place; that needs the map table or an emulator.

### Stats from level

`func_02069d7c` (the eight stats, float math) and `func_02069d54` (EXP, integer math):

```
stat = min + trunc((max - min) * level / 98)      (level <= 0 gives min)
EXP  = min + (max - min) * level / 98
```

The divisor is the float constant 98.0 at 0x02069DCC and the reciprocal multiply 0x5397829D >> 37 at
0x02069D78. Because enemy level never exceeds 80 (97 for Ignatius), the "max" column is never reached.

### Check against the fan data point

Sasquatch (row 136): HP 60 at level 0, 2600 at level 98; Sasquatch fights force `area_min = 7`.
At party level 1 the enemy level is clamped to 7, HP = 60 + trunc(2540 * 7 / 98) = **241**. The Let's
Play reported 240 at Jian level 1, which matches. At party level 9 the code gives level 8 or 9, HP 267 or
293; ABolner's "240 to 251 at level 9" does not match, so either his party level or his HP estimate was
off. **[uncertain]** until checked in an emulator.

## 3. EXP (Althena Conduct) and the Combat/Virtue flag **[confirmed]**

### The mode flag

- Persistent flag: **u8 at 0x020B4848** (game state 0x020B45B0 + 0x298). Nonzero = Virtue (EXP), 0 = Combat (items). Labels corrected by the parent: this agent first had them swapped; docs/re-field-battle.md and fan sources agree Virtue gives EXP.
  The field menu handler `func_0201e6a0` toggles it with `*DAT_0201f5b0 ^= 1` (pool 0x0201F5B0 =
  0x020B4848), gated by `func_02071c4c(-1) != 0` and `*0x020B6A18 == 0`.
- `func_020297d4` reads it (`ldrb r0, [r0, #0x298]` at 0x020298E0 and 0x02029984) and passes it as the
  fifth argument of the battle init `func_0202b948`, which stores the battle's mode at battle struct
  +0x08: **1 for a normal battle in Virtue mode, -1 for any boss battle in Virtue mode, 0 in Combat mode**.

### Where EXP is awarded

- Enemy death, `func_02053384`: when an enemy's HP reaches 0,
  `if (enemy && func_0202b118(battle) == 1)` (battle +0x08 == 1) it adds the enemy's scaled EXP
  (actor +0x50, via `func_02053880(actor, 10)`) to the pool at battle +0x58 (`func_0202af3c`).
  Otherwise it calls `func_02069f34`, the item drop routine. So in one battle an enemy gives **either**
  EXP **or** a drop roll, never both.
- Because boss battles get mode -1, **bosses never give EXP, in either mode, and always roll drops**.
  The boss EXP columns (1 to 10) are unused, except Dark Jian (2 to 1200), which is also a boss battle and
  so also unused.
- Victory, `func_020297d4`: if mode == 1 the result screen goes to the EXP step, otherwise to the item step
  (state 0x28).
- EXP step, `func_02052fb8` then `func_02052c2c`: **total = pool * 2** (`func_0202af34(battle) << 1`),
  counted out in steps of total / 64. **Every party member present gets the full total** (not split),
  except members whose status (actor +0x08) is 1, 4 or 7 (**[uncertain]** which statuses those are,
  likely knocked out or petrified). EXP is capped at the character's level 99 threshold
  (`func_020553ac(0x62, id)`), and the level is recomputed with `func_020553c8`.
- EXP thresholds: per-character table at 0x020947E8 (Jian: 6, 57, 202, 493, 986, ...), the same
  address the "Max level after one battle" cheat zeroes.
- Members outside the three battle slots get nothing; the loop only covers the three battle actors.

### Silver

No battle code writes silver. The enemy record and drop record have no silver field. The only writes
to 0x020B4824 are the script opcode `func_02040160` (event rewards such as Gad's Express) and shops.
**[confirmed]**

## 4. Stealing **[confirmed]**

Code: `func_020514ec` marks the attacker (`+0x88 = 1` for bit 27 actions), `func_02030b44` resolves the hit.

- If bit 0 of the battle work struct flags (`[0x020B8550] + 0`, set by the **Yeti card**) is set, a steal attack
  **misses completely** (`local_48 = -1` forces damage 0), so the card blocks the damage too, not only the
  theft.
- Otherwise, if the attack hits (normal hit check `func_0205265c`), it deals its normal damage and then
  `func_0206b69c` picks **one item uniformly at random among item ids 287 to 386 that you own at least one
  of** (Clay through Apple: smithing materials, crafting parts and delivery-type sundries). It removes one
  unit from the inventory (`func_0206b98c(0x0213B930, item, -1)`) and shows "<item> was stolen".
- **Never stolen:** equipment (ids 1 to 215), equipped gear, cards (216 to 269), healing items and
  medicine (276 to 284), and ids 387 and up (Package, Receipt, key items, orbs). DCGB's complaint about
  "rare delivery items" refers to sundries in the 287 to 386 range, not the Package.
- **Where the item goes:** nowhere. The id is written only to `[0x020B8550] + 0xDC` for the message. It is not
  stored on the thief, so killing the thief cannot return it in the original game.
- Morus steals on her 30% action; with two hits per round (ABolner) she can steal twice.
- Steal chance per enemy turn = (chance the enemy acts at all, `func_02069848`, about 60 to 100%
  depending on AI class (row flags bits 0-1) and whether HP is above half) x (action chance in the table above) x (hit chance).

### Do enemies flee? **[confirmed for the code paths read, not exhaustive]**

No. Evidence:
- The battle message list in ARM9 (around file offset 0xA42C0) has "was stolen", "broke", "Escape
  failed", "Lost <x> card" and similar, but no message for an enemy escaping.
- An enemy leaves battle only through the death path in `func_02053384` (flags 0x4000000 or 0x8000000 on
  the actor). No action flag or AI result removes a living enemy.
- The AI result 3 from `func_02069848` (when the enemy does not act and its species flag bit 2 is clear)
  is a non-attack command, **[uncertain]** what it shows on screen; nothing in the code reached from it
  removes the enemy.

## 5. Equipment breaking **[confirmed]**

Code: `func_020514ec` sets `+0x88 = 2` for bit 26 actions; `func_02030b44` resolves it.

- If bit 1 of the battle work struct flags (set by the **Termite card**) is set, a break attack misses completely, like
  the Yeti card for steals.
- On a hit, `func_0206b1d0(character)` picks one of the four equipment slots at character record
  + 0x3C (0x020B4698 for Jian): weapon, body, arm, head. It ignores slots whose item has flag 0x8000 in
  the item table (Jump Shoes, Bell Shoes, and accessories, which are not in these four slots anyway).
  Then by item type (item table +0, low nibble):
  - weapon (type 0): 40% chance nothing happens
  - body (type 1): 20% chance nothing happens
  - arm (type 2): always breaks, except Rainbow Gauntlet (120) and Crystal Guard (132), which survive 50%
  - head (type 3): always breaks
  - no break if the slot already holds the replacement item.
- `func_0206b144(character, slot)`: removes one copy of the old item from the inventory (the inventory
  count includes equipped gear), adds one replacement, and equips it. The old item is gone for good.
  The replacement comes from the table at 0x0209D0FC (`[slot * 5 + character]`):

| Slot | Jian | Lucia | Gabryel | Flora | Rufus |
|---|---|---|---|---|---|
| Weapon | Battered Shoes | Broken Umbrella | Snapped Claws | Withered Bow | Broken Sword |
| Body | Torn Clothes | Torn Robe | Ripped Uniform | Torn Dress | Battered Armor |
| Arm | Ripped Gloves | Rusty Bracelet | Battered Gauntlet | Battered Wristband | Torn Guard |
| Head | Shredded Bandana | Battered Tiara | Shredded Hairband | Broken Haircomb | Battered Helmet |

  So the fans' "worst item of that type" is right: it is the first (worst) item of that character's list.
- Stats are recomputed at once (`func_02054ebc`).

### The cards **[confirmed]**

Item table +2 is the card's effect id; effects are 0x0C-byte entries at 0x0209D124 indexed by
`effect - 0x100`. `func_0206a744` applies a card in battle:
- Yeti card (item 223) has effect 291, flag 0x8000: sets bit 0 of `[0x020B8550]` (block steal).
- Termite card (item 224) has effect 292, flag 0x10000: sets bit 1 (block break).

The same function sets other battle-wide bits for other cards (effect flag to work-struct bit: 0x2000 to
bit 3, 0x4000 to bit 5, 0x8000 to bit 0, 0x10000 to bit 1, 0x20000 to bit 2, 0x40000 to bit 6,
0x80000 to bit 7). Flag 0x1000 is effect 287, the Ice Mongrel card (item 221), the escape card. **[uncertain]** that the flags
are cleared when a battle starts; that would match "one battle per use".

## Open questions and in-emulator checks

1. **Enemy level and HP.** In a Sasquatch fight with the highest party level at 1, read the enemy actor
   at `[0x020B8620] + 4 * 0x6C`: +0x0C should be 7 and +0x1C (max HP) 241. Repeat at party level 9:
   level 8 or 9, HP 267 or 293. For a normal battle, compare +0x0C with the highest of the party levels
   at 0x020B4664 + id * 0x5C.
2. **Which party members count.** Put a high-level member in slot 2 or 3 and check that enemy levels
   follow that member, not Jian.
3. **EXP doubling.** In Virtue mode, sum +0x50 of every enemy actor before the last hit, then compare with
   the EXP each member gains. Expected: exactly twice the sum, to every living member.
4. **Bosses give no EXP.** Win any boss fight in Virtue mode; expected no EXP screen and a drop roll.
5. **Mode flag.** Toggle Combat/Virtue in the menu and watch 0x020B4848 change (expect 1 = Virtue, 0 = Combat).
6. **Steal pool.** Before an Ice Mongrel or Yeti steal, note the bytes 0x0213B930 + 286 to + 385; the
   stolen item must be one of the nonzero ones there and must not come back after the thief dies.
7. **Card flags lifetime.** Use a Yeti card, end the battle, and check bit 0 of `[0x020B8550]` in the next battle.
8. **Enemy flee.** Watch an enemy's AI command (+0x84 of its 300-byte battle object, pointer at
   0x020B8640) when it equals 3, and confirm nothing leaves the field. A full answer needs a search of all
   writers of the actor alive state, which this pass did not finish.
9. Names of map indexes and area groups (for the level table and the drop "tier" areas 6 to 8), the
   meaning of story flags 0xC9 and 0xD1 to 0xD5, and what items 270 to 274 do.
