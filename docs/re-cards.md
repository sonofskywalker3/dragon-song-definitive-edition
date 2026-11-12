# Enemy cards: what each effect really does (reverse engineering notes)

Static trace of the vanilla USA ARM9 (2026-11-12), nothing here was run in the emulator. **[confirmed]** means
read in the code or data; **[inferred]** means the code fits but a reader or a run is missing. Card list with
effect ids: `docs/re-skills.md` and the dump in section 7. Related: `docs/re-enemies.md` (cards as drops, Yeti
and Termite), `docs/re-mp-jobs-rings.md` (spell flags).

## 1. How a card is used

- A card is an item (ids 216 to 269, `216 + species`). Item table +2 is the effect id; the effect is a 0x0C
  entry at 0x0209D124 + 12 * (effect - 0x100): `u32 flags, u32 amount, u16 mask, u16 effect row`.
- In battle it is the character's command for the round (command 4, the same slot as Fight / Special / Item),
  so **it costs that character's turn**. **[confirmed]** (func at 0x02051xxx, decomp line 58360 onward).
- **Durability [confirmed]:** each card has a counter (s16 at 0x020B4884 + 2 * (card - 0xD8)), set from the
  table at 0x0209EA14 + 8 * (card - 0xD8) when the card is picked up, and every use takes 100
  (`func_0207f83c`, battle and field). At 0 the card is removed and "Lost <name> card" shows. So a card has
  **value / 100 uses**: Blob 8, Bealzebub 9, Ice Mongrel / Termite / Hellbird / Shaitan 10, Onlooker /
  Kuntukapu / Sturge 11, Shreeker / Insector / Comet / Duager 12, Namia / Treant / Tick / Gloomwing /
  Ikontabipu / Vitra / Ochu 13, Abadon / Phantom / Ghoula / Thanatos 14, Evil Earth 15, Mad Fang /
  Ohainkaru / Chupacabra 16, Enigma / Druid 17, Yeti / Dagon / Asmodee 18, Quetzalcoatl 20. Boss cards have
  values too (2000 to 5000) but no effect. A card only drops while it is not in the inventory
  (docs/re-enemies.md), so it has to break before it can be farmed again.
- Flags: 0x80000000 targets the party side, 0x40000000 all targets, 0x1 usable in the field, 0x2 usable in
  battle. Buff cards are all allies, debuff and status cards are all enemies, Dagon is the only single-enemy
  card. **[confirmed from the flags; the target loop itself was not read]**
- Tick card (item 0xE2) only: if no enemy is alive in battlers 8 to 11 (the front row) the command turns into
  a plain attack. **[confirmed]**, reason unknown.

## 2. Stat stages (buff and debuff cards, and Quick / Grand Weapon / Grand Shell)

**[confirmed]** `func_02054dec(record, stat, +1 / -1)` moves a signed stage (shorts at record +0x40 ATK, +0x42
DEF, +0x44 AGI, +0x46 INT, +0x48 DEX, +0x4A LUCK), clamped to **-4 .. +8**. The recompute (`func_02054ebc`
party, `func_02069ad8` enemies) multiplies the base stat by the table at 0x02094754 / 100, result clamped
to 1 .. 999:

| Stage | -4 | -3 | -2 | -1 | 0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Percent | 20 | 40 | 60 | 80 | 100 | 125 | 155 | 190 | 230 | 275 | 325 | 380 | 440 |

- One use is one stage, and **uses stack**.
- **Duration: the whole battle.** The only writers are `func_02054dec` (callers: the three spell flags and
  the card function, always +1 or -1) and the zeroing in battle setup (`func_02054104`, `func_02054494`).
  There is no turn counter.
- **Bosses are not protected.** `func_0206a2f8` applies the stage with no check of the enemy row, so every
  debuff works on every boss.
- Spells: flags 0x1000000 / 0x2000000 / 0x4000000 are +1 ATK / DEF / AGI (Grand Weapon, Grand Shell, Quick).
  Cards: flag 0x1000000 is +1 and 0x2000000 is -1 on every stat whose bit is set in the mask (bit 4 ATK,
  5 DEF, 6 AGI, 7 INT, 8 DEX, 9 LUCK). So the party has no spell for INT / DEX / LUCK up or for any down.

### Where each stat is read **[confirmed]**

- **Physical damage** (`func_0205212c`): `raw = ATK * 2 * f / 64 - DEF` with f = 57..72 (72 on a critical),
  `damage = (raw / 2) * 60 / 100`, minimum 1. So roughly `0.3 * (2 * ATK - DEF)`.
- **Magic damage** (flag 0x100): the same with the caster's INT against the target's INT.
- **Heals**: caster INT * 1.25..1.74 (docs/re-mp-jobs-rings.md).
- **Hit chance** (`func_0205265c`): `DEX * 8 / (DEX * 8 + target AGI)`; a miss is rescued with chance
  `(LUCK / 8 + 2) / 256`. Equal stats give 89%.
- **Critical**: `min(64, (LUCK / 8 + 1) / 2 + 16) / 512`, 3.7% at LUCK 42, 4.3% at LUCK 100.
- **Turn order** (func at decomp 36690): each battler rolls `AGI * 2 + rand(0 .. AGI * 2)`, highest first.

### Worked numbers (level 20 base stats, no gear; enemy rows at level index 19)

| Case | Stage 0 | 1 use | 2 uses | 3 uses | 4 uses |
|---|---|---|---|---|---|
| ATK down, Abadon (ATK 62) hits Jian (DEF 41) | 24 | 16 | 9 | 1 | 1 |
| ATK down, Gronk (ATK 92) hits Rufus (DEF 78) | 31 | 20 | 9 | 1 | 1 |
| ATK down, Gronk hits Jian (DEF 41) | 42 | 31 | 20 | 9 | 1 |
| DEF down, Jian (ATK 56) hits Abadon (DEF 44) | 20 | 22 | 25 | 28 | 31 |
| DEF down, Rufus (ATK 106) hits Gronk (DEF 57) | 46 | 49 | 53 | 57 | 60 |
| ATK up (Grand Weapon), Rufus hits Gronk | 46 | 61 | 81 | 103 | |
| INT down, Gronk (INT 102) magic on Lucia (INT 88) | 34 | 22 | 10 | | |
| AGI down, Jian (DEX 58) hit chance on Gronk (AGI 58) | 88.9% | 91.0% | 93.2% | | 97.7% |
| DEX down, Gronk (DEX 62) hit chance on Jian (AGI 70) | 87.6% | 84.8% | 80.9% | | 57.8% |
| AGI up (Quick), Gronk hit chance on Jian | 87.6% | 85.1% | 82.1% | 78.9% | |

Reading: because damage is `2 * ATK - DEF`, **the attacker's stat counts double**. ATK down and INT down cut
a third of the damage per use and reach 1 damage in three or four uses, on bosses too. ATK up is +33% per
use. DEF down is +7 to +10% per use. AGI, DEX and LUCK changes move a hit chance or a 4% critical chance by
two or three points per use.

## 3. Status cards

**[confirmed]** Status is the low nibble of record +0x08; a higher number replaces a lower one, never the
reverse (`func_0205511c`). Mask bit n in the card is status n. Names: 6 and 4 from the medicines (Antidote
cures mask 64, Paraclean mask 16); the rest are named here by what the code does **[inferred names]**.

| # | Card | Name | Effect (confirmed) | Lasts |
|---|---|---|---|---|
| 1 | Ikontabipu | sleep | no action; evasion halved and 25% of attacks cannot miss; the first damage clears it | 2 to 4 own turns |
| 2 | Asmodee | blind | own attacks: half accuracy and a flat 50% miss on top; own evasion halved | 2 to 4 |
| 3 | Druid | confusion or numb | 50% chance to lose each turn | 2 to 4 |
| 4 | Tick | paralysis | no action; evasion halved, 25% cannot miss; damage does not clear it | 2 to 4 |
| 5 | Phantom | silence | cannot use skills (`func_02055274`); attacks normally | 2 to 4 |
| 6 | Shreeker | poison | loses 5% of max HP at the end of each own turn, never the last HP | until cured or the battle ends |
| 7 | Dagon (one enemy) | stone | no action for 4 to 6 turns; DEF x 4/3; evasion halved | 4 to 6 |

- **Chance against regular enemies: 100%.** The card function has no roll for an enemy target unless the row
  has flag 0x80000000.
- **Bosses** (rows 136 to 156 all carry 0x80000000): immune to 1, 3, 4, 5 and 7; **blind and poison always
  land**. Poison is 61 HP per turn on Gronk (1223 HP) and 79 on the Red Dragon (1581) at that level, about as
  much as a strong hit, every turn, for one card use.
- Against the party the same statuses roll against the resistance bytes at 0x0213B908 + n (from gear).
- For comparison, a weapon's on-hit status is a 20% roll on regular enemies and never works on bosses
  (`func_02030b44`).

## 4. Battle-wide cards (bits of the battle flags word, `[0x020B8550]`)

Set by `func_0206a744`; the word is zeroed at battle start, so each lasts one battle. **[confirmed]** readers:

| Card | Effect flag | Bit | What it does |
|---|---|---|---|
| Yeti | 0x8000 | 0x01 | enemy steal attacks miss (damage too) |
| Termite | 0x10000 | 0x02 | enemy break attacks miss (damage too) |
| Bealzebub | 0x20000 | 0x04 | party physical attacks skip the hit roll: they always hit |
| Namia | 0x2000 | 0x08 | each party member regains 10% of max HP at the end of their own turn |
| (Divine Rain, spell flag 0x800) | | 0x10 | the same, 5%; adds to Namia and to gear (byte 0x0213B910) |
| Kuntukapu | 0x4000 | 0x20 | each party member regains 5% of max MP at the end of their own turn |
| Insector | 0x40000 | 0x40 | damage the party deals x 1.75 to 2.00 |
| Ochu | 0x80000 | 0x80 | damage the party takes x 0.50 to 0.75 |

## 5. The remaining cards

- **Ice Mongrel** (0x1000): escape from the battle. **[confirmed in docs/re-enemies.md]**
- **Vitra**: all allies HP +100% of max. **Hellbird**: all allies MP +100% of max. **Shaitan**: revive all
  allies (revive flag, amount 100). **[confirmed from flags and amounts; `func_0206a8b8`]**
- Field cards (`func_0206e718`, usable only while the map still has enemies, `func_0206e838`):
  - **Ohainkaru**: field mode 1 for 500 frames, enemy symbols move at speed 0 (frozen). **[confirmed]**
  - **Blob**: field mode 2 for 500 frames, enemy symbols at half speed. **[confirmed]**
  - **Mad Fang / Ghoula**: write 1 / 0 into bits 9..12 of every enemy symbol's flags (object type 3). The
    symbol AI reads that field when the player comes in range; which way it turns (flee or chase) was not
    traced. **[inferred: Mad Fang scares symbols off, Ghoula undoes it or draws them in]**
  - **Treant / Gloomwing**: write 30 and 60 to two byte pairs (0x020B49D0/1 and 0x020B49D2/3). Readers not
    found. **[unknown]**
- All 20 boss cards have effect 0: nothing.

## 6. Effect sprites, targets and size

- Each target gets its own effect script (battle work +0x78 + 4 * target, effect battlers 14 + i;
  docs/plan-enemy-attacks.md), so a banner is already drawn **once per target at that target's position**;
  an all-enemies card looks like one big effect only because every enemy gets one at the same time.
  **[confirmed for enemy skills; the card path uses the same effect rows]**
- Cell sizes: stat banners (btldata 298 to 310) 38 x 117 up to 64 x 126 pixels, a strip of text that rises
  about 80 pixels over nine cells; the status rings (314) 34 x 36; the heal sparkle (158) 36 x 70; the unused
  water ribbon (313) 68 x 72.
- Every battle sprite is a request in the pool at `*0x020B8618`, and the request carries a scale (+0x18 is the
  inverse of the drawn scale, docs/plan-targeting.md): the renderer already scales sprites for the field's
  perspective. So drawing an effect smaller is a number in its request, not redrawn art. **[inferred: the
  field exists and the renderer uses it; where an effect's request gets its scale was not traced]**

## 7. Verdict by group

| Group | Cards | Verdict |
|---|---|---|
| ATK down, INT down, all-stats down | Quetzalcoatl, Enigma, Duager | strong: -33% damage taken per use, stacks to 1 damage, works on bosses |
| ATK-side party help | Insector (x 1.75 to 2 damage dealt), Ochu (x 0.5 to 0.75 taken), Bealzebub (never miss) | strong, one use per battle |
| Poison, blind | Shreeker, Asmodee | strong on bosses (5% max HP a turn; half their attacks miss) |
| Sleep, paralysis, stone, confusion | Ikontabipu, Tick, Dagon, Druid | strong on regular enemies (guaranteed, 2 to 6 lost turns), nothing on bosses |
| Regen | Namia (10% HP a turn), Kuntukapu (5% MP a turn) | meaningful in long fights |
| Full heals | Vitra, Hellbird, Shaitan | strong (the only MP refill for the whole party) |
| Protection | Yeti, Termite | meaningful only where thieves and breakers are |
| INT up | Comet | meaningful for healers (+25% healing a use) |
| DEF down | Abadon | marginal (+7 to 10% damage a use) |
| AGI down, DEX down, DEX up, LUCK up / down, silence | Onlooker, Chupacabra, Evil Earth, Sturge, Thanatos, Phantom | near useless (two or three points of hit chance, a 4% critical) |
| Field cards | Blob, Ohainkaru, Mad Fang, Ghoula, Treant, Gloomwing | convenience at best; two not understood |
| Boss cards | 20 cards | no effect at all |
