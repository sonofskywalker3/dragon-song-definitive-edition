# MP economy in the PS1 Lunar games, and what it means for Dragon Song

Research for design item 8 (MP and spells), done 2026-10-06. The goal is "the original Lunar feel translated to this
game's economics": how much MP items cost and restore relative to MP pools, what healing spells cost, and how much
silver a battle pays, in Lunar: Silver Star Story Complete (SSSC, PS1, 1999) and Lunar 2: Eternal Blue Complete
(EBC, PS1, 2000). This game's own numbers are from [re-mp-jobs-rings.md](re-mp-jobs-rings.md) section 1.

Markers: **[sourced]** = a PS1-specific source states it; **[conflict]** = PS1 sources disagree;
**[unverified]** = estimate, memory, or a source whose version is unclear. Nothing here was checked in an emulator.

## Short answer

- **The owner's memory is EBC, half right.** EBC (PS1) sells Star Light for **2000 silver**, and one FAQ says it
  restores "about 20 MP" (another says about 1/3 of max MP). SSSC (PS1) sells it for **1000** and it restores
  **30 to 40 MP**. **Silver Light is never sold in either PS1 game.** It restores all MP and comes only from
  chests. No source supports "Silver Light 20000 for about 100 MP".
- **The 50 / 30 MP, 120 / 80 MP, 4000 / 255 MP snippet is the Sega CD Lunar: The Silver Star** (rpgclassics
  Sega CD shrine). That source gives them as buy prices (section 1.1 has the buy vs sell check). If they are
  right, MP items were cheap shop goods on Sega CD and the PS1 remakes made them rare and expensive.
- **Seed of Vigor restores MP, not HP,** in both versions that have it (Sega CD: 255 MP; Saturn: "a lot of
  your MP"). The full HP item with a similar name is **Vigor Peach** (Sega CD: 255 HP to all allies, chests only;
  Saturn: "all of your HP"). Neither item is in SSSC (PS1) or EBC (PS1).
- **The PS1 pattern (both games):**
  1. The first heal costs 4 MP, which is 5 to 10% of the healer's MP. That is 10 to 25 casts per full pool.
  2. The one buyable MP item restores about **a third of a healer's pool**. Where it is first sold, it costs
     **about 6 to 10 regular battles' worth of silver**. It is not sold in the first region.
  3. A full-MP item exists, but only in chests (and it sells back for a lot in EBC).
  4. Towns and some dungeons have **Althena statues that fully restore HP and MP for free**. Neither PS1 game
     has paid inns (see section 4). Walking back to a statue is the normal way to refill.
- **This game today breaks pattern 1 and 2:** the first heal is 56% of Lucia's MP at level 1, and the MP items
  are cheap but never sold.
- **Proposal (section 7):** Healing Water 10 to 4 MP and the other Lucia/Flora spells cut to about 40%; Lucia's
  level 1 MP 18 to 24; Mental Gum restores 35% and costs 600 S in item shops; Mental Drop restores 100% and is
  still not sold. Everything except the shop lists is a data edit. It relies on spell unlocking being uncoupled
  from MP cost first.

## 1. MP items

| Game (version) | Item | Price | Restores | Where sold | Source |
|---|---|---|---|---|---|
| SSSC (PS1) | Star Light | 1000 | 30 to 40 MP, one ally | Meribia (Black Rose Street, Ramus' shop), Vane, Reza Thieves' Guild, Pao. First chance: first visit to Meribia, party about level 12 to 14 | **[sourced]** rpgclassics PS1 shrine [healing items](https://shrines.rpgclassics.com/psx/lsssc/items/healing.shtml), [shops](https://shrines.rpgclassics.com/psx/lsssc/shops.shtml) |
| SSSC (PS1) | Silver Light | not sold | all MP, one ally | chests only (Myght's Tower, Talon Mines, Grindery, red chests in several towns) | **[sourced]** same shrine; [Lunar wiki](https://lunar.fandom.com/wiki/Silver_Light) |
| EBC (PS1) | Star Light | 2000 (sells 1000) | "about 1/3 of total MP" (Sybillium FAQ) or "about 20 MP" (DWagoner FAQ) | Meribia (9th town on the list), Vane, Neo-Vane, Ramus in Vane on disc 3 | **[sourced]** price and shops: Shotgunnova [shop list](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/52748), Sybillium [FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10184). Amount **[conflict]**, see below |
| EBC (PS1) | Silver Light | not sold (sells for 5000) | all MP, one ally | chests only (East Nota, Meribian Sewers, Vane, Azado, Pentagulia, Zaback, Neo-Vane and later) | **[sourced]** Sybillium FAQ; [Lunar wiki](https://lunar.fandom.com/wiki/Silver_Light) |
| Lunar: The Silver Star (Sega CD) | Starlight | 50 | 30 MP | Meribia, Vane, Lyton | **[sourced]** rpgclassics Sega CD shrine [items](https://shrines.rpgclassics.com/sega_cd/ltss/items/normal.shtml), [shops](https://shrines.rpgclassics.com/sega_cd/ltss/shops.shtml) |
| Lunar: The Silver Star (Sega CD) | Silver Light | 120 | 80 MP | Meribia, Vane, Cadin | same |
| Lunar: The Silver Star (Sega CD) | Seed of Vigor | 4000 | 255 MP | (shop not listed by the shrine) | same |
| Lunar: The Silver Star (Sega CD) | Garlic / Smoked Fish | 24 / 4 | 45 / 5 MP (as listed) | Lann, Meryod, Lyton, Cadin | same |
| Silver Star Story (Saturn) | Star Light / Silver Light | not given | "a little" / "some" MP | not given | [almarsguides Saturn item list](https://almarsguides.com/retro/walkthroughs/saturn/games/lunarsilverstarstory/misc/lists/items/) **[unverified]** numbers |

### 1.1 Buy price or sell price? Seed of Vigor?

The owner remembers buy prices around Starlight 2000 (about 20 MP) and Silver Light 20000 (about 100 MP), and
suspects that 50 / 120 / 4000 are sell prices kept low so MP items are not resold. What each source says:

| Source | Price shown | Buy or sell | Notes |
|---|---|---|---|
| SSSC PS1 shrine, [shops](https://shrines.rpgclassics.com/psx/lsssc/shops.shtml) | Star Light 1000 | **buy**: it is in five shop inventories ("the Item for sale and its price in Silver") | Silver Light is in no shop, so it has no buy price |
| EBC, Shotgunnova [shop list](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/52748) | Star Light 2000 | **buy** (shop inventories) | |
| EBC, Sybillium [FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10184) item list | Star Light "Buy/Sell: 2000$/1000$"; Silver Light "Buy/Sell: No/5000$" | both, labeled | Selling is half the buy price. Silver Light cannot be bought and **sells for 5000**, which is high, not set low |
| Sega CD shrine, [shops](https://shrines.rpgclassics.com/sega_cd/ltss/shops.shtml) | Starlight 50, Silver Light 120 in the Meribia and Vane magic shops; Starlight 50 in Lyton; Silver Light 120 in Cadin | **buy**, as listed in shop inventories | One fan source only |
| Sega CD shrine, [items](https://shrines.rpgclassics.com/sega_cd/ltss/items/normal.shtml) | Starlight 50, Silver Light 120, Seed of Vigor 4000 (column "COST") | not stated, presumably buy | Herb is 50 here but 80 in every shop table of the same shrine, so the item page is not fully reliable. 50 is not half of 80 either, so it is not simply a sell price |

Verdict: **the PS1 buy prices are Star Light 1000 (SSSC) and 2000 (EBC); Silver Light has no buy price in
either PS1 game.** The owner's "Starlight 2000 for about 20 MP" matches EBC (PS1) exactly, per DWagoner's FAQ.
Nothing supports "Silver Light 20000 for about 100 MP" in any version found; the nearest numbers are EBC's sell
value of 5000 (so 10000 if it followed the half rule) and the Sega CD's 80 MP restore. For the Sega CD, the one
source found gives 50 / 120 / 4000 as buy prices, and the sell-price theory cannot be ruled out without a second
Sega CD source **[unverified]**. Even so, the 4000 for Seed of Vigor sits in the same column as the 50 and 120,
so all three are the same kind of price.

Seed of Vigor, per version:

| Version | Seed of Vigor | Vigor Peach | Source |
|---|---|---|---|
| Sega CD (Lunar: The Silver Star) | 255 MP, one ally, 4000 | 255 HP, all allies, chests only (Silver Spire, Goddess Tower) | Sega CD shrine items page |
| Saturn (Silver Star Story) | "Restores a lot of your MP" | "Restores all of your HP" | [almarsguides Saturn list](https://almarsguides.com/retro/walkthroughs/saturn/games/lunarsilverstarstory/misc/lists/items/) |
| SSSC (PS1) | not in the shrine's healing list or any shop | not listed | rpgclassics PS1 shrine |
| EBC (PS1) | not in any FAQ item list | not listed (Passion Fruit is EBC's full HP item) | Sybillium, DWagoner |

Notes:

- **EBC Star Light amount [conflict].** Two PS1 FAQs disagree. "About 20 MP" and "1/3 of max MP" agree if the
  author measured it on a pool of about 60, which is plausible for a mid-game character, so the item may be a
  percentage. Not settled. Either way it is a few heals, not a refill.
- **EBC Star Light in Larpa [conflict].** Kiko-kun's [FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10153)
  lists Star Light 2000 and Angel's Tear 600 in Larpa (the first town after the Blue Spire). Shotgunnova's
  dedicated shop list has neither in Larpa, and Angel's Tear at 1000 everywhere. The shop list is the more careful
  source.
- **The Lunar wiki's "2000 Silver" for Star Light** comes with SSSC shop locations, but the 2000 matches only EBC.
  The SSSC PS1 shrine lists 1000 in all five shops. Treat 1000 as SSSC and 2000 as EBC.
- **Not researched:** Lunar Legend (GBA), Silver Star Harmony (PSP) and the 2025 Lunar Remastered Collection.
  The Remastered Collection is built on the PS1 versions, but whether it changed any prices was not checked.

## 2. Healing and key spells

### SSSC (PS1), from the rpgclassics PS1 shrine ([Luna](https://shrines.rpgclassics.com/psx/lsssc/magic/luna.shtml), [Jessica](https://shrines.rpgclassics.com/psx/lsssc/magic/jessica.shtml), [Mia](https://shrines.rpgclassics.com/psx/lsssc/magic/mia.shtml), [Nash](https://shrines.rpgclassics.com/psx/lsssc/magic/nash.shtml)) **[sourced]**

| Character | Joins at about | First spells (MP) | Later spells (MP, level) |
|---|---|---|---|
| Luna | level 1 | Healing Song 4 (one ally) | Purity Song 4 (L5), Temptation 7 (L7), Cascade 10 (L9), Tranquil Song 15 (all allies, L10), Escape Song 10 (L12) |
| Nash | level 13 | Stone 6, Thunder Bomb 6 | Confusion 12 (L12), Spark Ball 10 (L18), Thunder Thrust 18 (L23), Thunderbolt 15 (L34) |
| Jessica | level 17 | Heal Litany 4 (one ally) | Cleanse 4 (L14), Calm Litany 15 (all, L16), Escape 20 (L20), Saint 12 (L25), Althena Litany 10 (full HP, L31), Miracle 20 (revive, L35) |
| Mia | level 18 | Ice Lance 5, Flame Circle 7, Ice Shell 11 | Blizzard 10 (L15), Ice Wall 15 (L21), Flame Bomb 13 (L24), Flameria 30 (L35) |
| Alex | level 1 | Sword Dance 6 | Explosion Staff 9 (L10), Flash Cut 18 (L18) |

Join levels are the first rows of each character's level chart. Party members join at Alex's current level.

### EBC (PS1), from GameFAQs PS1 FAQs ([DWagoner](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10097), [Kiko-kun](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10153), [Sybillium](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10184)) **[sourced]**

| Character | Joins at about | First spells (MP) | Later spells (MP, level) |
|---|---|---|---|
| Gwyn (temporary) | level 9 | Heal Litany 4, Calm Litany 12 (all) | Fractured Armor 6 (L10) |
| Ronfar | level 12 | Heal Litany 4, Calm Litany 12 (all), Clean Litany 3 | Saint 5 (L15), Escape 2 (L16), Purity Litany 12 (full HP, L18), Revive 12 (L21), Tranquil 24 (L34), Miracle 30 (L46) |
| Jean | level 16 | Moth Dance 6, Sleep Step 5, Bee Dance 7 | Butterfly Dance 9 (L20), Blue Dragon Fist 32 (L46) |
| Lemina | level 20 | Flame 4, Flame Bomb 7, Burning Rain 10, Ice Pick 4, Magic Seal 3 | Pyro Pillar 14 (L31), Crematorium 30 (L34), Catastrophe 55 (L51) |
| Leo | late | Flash Blade 8, Buzz Blade 18, Grizzle Blade 20, Earth Prayer 15 | Rock Riot 14 (L36) |
| Lucia | AI-controlled | Heal Litany and attack spells | **Costs 0 MP: her MP is unlimited** (DWagoner, [Lunar wiki](https://lunar.fandom.com/wiki/Lucia)) |
| Hiro | level 1 | Boomerang 3 (L5) | Poe Sword 6 (L7), Squall 7 (L9), Vortex 10 (L20) |

Sybillium's FAQ prints Ronfar's Heal Litany as 14 MP. Three other FAQs and the Lunar wiki say 4, so 14 is a typo.

**The PS1 shape:** single heal 4, group heal 12 to 15 (3 to 4 times the single heal), revive 12 to 30, full
single heal 10 to 12. Healing costs do not rise with the game's progress; the pools do.

## 3. MP pools by level

### SSSC (PS1), base stats from the rpgclassics PS1 level charts ([Luna](https://shrines.rpgclassics.com/psx/lsssc/levelcharts/luna.shtml), [Mia](https://shrines.rpgclassics.com/psx/lsssc/levelcharts/mia.shtml), [Nash](https://shrines.rpgclassics.com/psx/lsssc/levelcharts/nash.shtml), [Jessica](https://shrines.rpgclassics.com/psx/lsssc/levelcharts/jessica.shtml), [Alex](https://shrines.rpgclassics.com/psx/lsssc/levelcharts/alex.shtml)) **[sourced]**

| Character | L1 | L5 | L10 | L15 | L20 | L30 | L40 | L50 | L99 |
|---|---|---|---|---|---|---|---|---|---|
| Luna | 40 | 65 | 94 | 125 | (leaves at 19: 148) | | | | |
| Nash | | | | 82 | 97 | 131 | 182 | 230 | 400 |
| Jessica | | | | | 100 (89 at L17) | 138 | 176 | 214 | 400 |
| Mia | | | | | 153 (141 at L18) | 213 | 272 | 333 | 555 |
| Alex | 10 | 22 | 35 | 47 | 59 | 85 | 118 | 164 | 340 |

### EBC (PS1): no level table found **[unverified]**

No PS1 stat table turned up (GameFAQs FAQs have none; Lunar Threads, LunarNET and NeoGAF block fetches). Fragments:

- Hiro has 34 MP at level 5 in the sample status screen of ATadeo's [FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10185) (probably a real screen, not certain).
- A search snippet from a Lunar Threads post gives level 99 MP: Ronfar 600, Jean 350, Lemina 850 (version not stated).
- If Star Light's "about 20 MP" equals "1/3 of max", the author's character had about 60 MP.

Taken together, a mid-game EBC healer probably has 50 to 100 MP, so Heal Litany at 4 MP is about 4 to 8% of the
pool. Treat that as an estimate.

## 4. Battle income and resting

### Silver per enemy

SSSC (PS1), rpgclassics PS1 shrine enemy pages ([Caldor](https://shrines.rpgclassics.com/psx/lsssc/enemies/caldor.shtml), [Katarina](https://shrines.rpgclassics.com/psx/lsssc/enemies/katarina.shtml), [Marius](https://shrines.rpgclassics.com/psx/lsssc/enemies/marius.shtml), [Stadius](https://shrines.rpgclassics.com/psx/lsssc/enemies/stadius.shtml), [Frontier and end](https://shrines.rpgclassics.com/psx/lsssc/enemies/frontend.shtml)) **[sourced]**; EBC (PS1), ATadeo's [FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10185) enemy list **[sourced]**:

| Stage | SSSC area: silver per enemy | EBC area: silver per enemy |
|---|---|---|
| First dungeon | White Dragon Cave: 6 to 22 | Blue Spire: 1 to 15; Larpa Pass 5 to 13 |
| Early | Weird Woods, Old Hag's Forest: 14 to 50 | Starlight Forest 6 to 32; Takkar Pass 7 to 32 |
| Where the MP item is first sold | Meribian Sewers: 27 to 63 | Meribia Sewers: 29 to 221 (average about 115) |
| Mid | Meryod Woods, Damon's Spire: 108 to 225 | Taben's Peak 49 to 231; Zaback Mines 84 to 505 |
| Late | Black Dragon Fortress 203 to 378; Goddess Tower 225 to 450 | Zophar's Keep 90 to 777 |

Bosses: the first EBC boss (Guardian) gives 121 EXP and 100 silver (ATadeo). Most EBC boss entries list only EXP.

**Per battle [unverified]:** neither source gives formation sizes. Assuming 2 to 4 enemies per battle, an SSSC
battle pays about 30 to 60 silver in the first region, 100 to 150 in the Meribian Sewers and 500 to 1000 late;
an EBC battle pays 10 to 40 in the first region, 250 to 350 in the Meribia Sewers and 1000 or more late.

### Resting

- Neither PS1 game has a paid inn in its script. Both use **Althena statues** that restore HP and MP for free:
  SSSC "[They heal at the statue.]" in Burg, EBC Ruby's "stand at the statue and send a prayer" at the start
  (local scripts `build/research/lunar_scripts/sssc_script.txt` line 405 and `ebc_script.txt` line 171), and
  every walkthrough sends the player back to statues ("You can always run back to Burg and use Althena's Statue",
  [rpgclassics walkthrough](https://shrines.rpgclassics.com/psx/lsssc/text_walkthrough/caldor2.shtml)).
- Kiko-kun mentions a Larpa shrine that takes silver donations, and says to skip it because the statue heals for
  free.
- So section 1.6 of re-mp-jobs-rings.md ("every town has an inn for a small fee") is wrong for the PS1 games.
  Free statues, not inns.

## 5. HP items for comparison

| Game | Item | Price | Restores | Source |
|---|---|---|---|---|
| SSSC (PS1) | Herb | 40 | 50 HP | rpgclassics PS1 shrine |
| SSSC (PS1) | Healing Nut | 200 | 150 HP | same |
| SSSC (PS1) | Angel's Tear | 600 | revive | same; [Lunar wiki](https://lunar.fandom.com/wiki/Angel%27s_Tear) |
| EBC (PS1) | Herb | 40 | about 40 to 50 HP | Shotgunnova shop list; Sybillium; DWagoner |
| EBC (PS1) | Healing Nut | 200 | 200 HP | same |
| EBC (PS1) | Angel's Tear | 1000 (600 in one FAQ) | revive at about half HP | same **[conflict]** on price |
| EBC (PS1) | Passion Fruit | 1000, shop only in the epilogue | all HP | Sybillium; [Lunar wiki](https://lunar.fandom.com/wiki/Passion_Fruit) |
| Sega CD Lunar 1 | Herb / Calm Herb / Herb of Althena | 80 / 100 / 2300 | 45 / 200 / all HP (party) | rpgclassics Sega CD shrine |
| This game | Healing Gum / Healing Drop / Angel's Tears | 15 / 80 / 300 | 30% / 60% HP / revive 10% | re-mp-jobs-rings.md 1.3 |

In both PS1 games the MP item costs 25 to 50 Herbs. This game's Mental Gum costs 2 Healing Gums.

## 6. Comparison

| Measure | SSSC (PS1) | EBC (PS1) | This game today |
|---|---|---|---|
| (a) First heal cost as % of healer's MP at the start | Healing Song 4 / Luna 40 at L1 = **10%** (Jessica at join: 4 / 89 = 4.5%) | Heal Litany 4 / Ronfar about 50 to 80 at join = **5 to 8%** [unverified pool] | Healing Water 10 / Lucia 18 at L1 = **56%** (23% at L10) |
| Casts per full pool, early | 10 | about 12 to 20 | 1 at L1, 4 at L10 |
| (b) MP item restore as % of a typical pool | Star Light 30 to 40 MP vs Luna about 107 to 119 (L12 to 14) = **about 30%**; 7 to 10 Healing Songs | Star Light about 1/3 of max (or about 20 MP) = **about 33%**; about 5 Heal Litanies | Mental Gum 20% = 3 MP at L1, 8 at L10 (under one Healing Water at L1); Mental Drop 50% |
| (b) MP item price in battles' silver where first sold | 1000 vs 100 to 150 per Sewers battle = **about 7 to 10 battles** | 2000 vs 250 to 350 per Sewers battle = **about 6 to 8 battles** | Gum 30 vs about 100 per early battle = **0.3 battles**, but not sold anywhere; Drop 240 = 2.4 battles, boss drops only |
| MP item price vs basic HP item | 25 Herbs | 50 Herbs | 2 Healing Gums |
| First region sells MP items | no | no | no (none sold at all) |
| Full-MP item | Silver Light, chests only | Silver Light, chests only (sells for 5000) | none (Mental Drop is 50%, boss drops only) |
| Free full refill | Althena statues in towns and some dungeons | same | healing statues (map object 0x37D); no inns; area-clear refill removed by this hack |

What the PS1 games did: MP was rarely the hard limit for a single heal, because a basic heal was a small slice
of the pool. What made you walk back to a statue was a long dungeon draining many casts. The buyable MP item was
a pricey top-up worth about a third of a pool, and full refills were treasure. This game has the opposite
problem: the pool is one heal deep, so no item price can fix it alone.

## 7. Proposal for this game

It assumes spell unlocking is uncoupled from MP cost first (design item 8; re-mp-jobs-rings.md option C notes the
`func_02050c50` threshold patch). Without that patch, cutting costs would make every spell appear at level 1 or 2.

### 7.1 Spell costs (data: u32 at 0x0209497C + spell * 0xC)

Target the PS1 shape: single heal about 5 to 10% of the healer's pool from early on, group heal 3 times the single
heal.

| # | Spell | Now | Proposed | PS1 equivalent |
|---|---|---|---|---|
| 1 | Healing Water | 10 | **4** | Healing Song 4, Heal Litany 4 |
| 2 | Tender Rain | 30 | **12** | Calm Litany 12, Tranquil Song 15 |
| 3 | Cure Squall | 8 | **4** | Purity Song 4, Clean Litany 3 |
| 4 | Divine Rain | 40 | **16** | |
| 5 | Miracle Tears | 50 | **20** | Revive Litany 12, Miracle Litany 20 to 30 |
| 6 | Escape | 5 | **2** | Escape Litany 2 |
| 7 | Quick | 20 | **8** | Speed Storm 8 |
| 8 | Grand Weapon | 24 | **10** | Cascade Song 10, Power Flame 9 |
| 9 | Grand Shell | 28 | **10** | Ice Shell 8 to 11 |

Dragon Magic (10 MP each, Jian) and the Gabryel and Rufus skills are left alone here; that is a separate question
about Jian's MP (10 at L1).

### 7.2 MP growth (data: MP min at 0x02094B4C + char * 0x60 + 0x0C)

Raise Lucia's level 1 MP from 18 to **24** and keep her level 99 value (300). Optionally raise Flora's level 1 MP
from 18 to 22. With Healing Water at 4:

| Lucia | L1 | L5 | L10 | L20 | L30 | L50 |
|---|---|---|---|---|---|---|
| Max MP (proposed) | 24 | 35 | 49 | 78 | 106 | 162 |
| Healing Water casts | 6 | 8 | 12 | 19 | 26 | 40 |
| Healing Water as % of pool | 17% | 11% | 8% | 5% | 4% | 2.5% |

From about level 5 on this matches SSSC's Luna (10% at L1, 6% at L5) and EBC's Ronfar (about 5 to 8%). Level 1
stays a little tighter than Luna, which fits a first dungeon.

### 7.3 Mental Gum and Mental Drop

| Item | Now | Proposed | Why |
|---|---|---|---|
| Mental Gum (0x116) | 20% MP, 30 S, not sold | **35% MP, 600 S, in every item shop** (optionally from the second town on, as the PS1 games do) | Star Light is about a third of a pool in both PS1 games. 600 S is about 6 early battles (about 100 S each), in line with the 6 to 10 battles Star Light costs where it is first sold. As battle silver grows with level, it gets cheaper in battle terms, as Star Light did (about 1 to 2 battles late in SSSC). It is 40 Healing Gums, within the PS1 range of 25 to 50 Herbs |
| Mental Drop (0x117) | 50% MP, 240 S, boss drops only | **100% MP, not sold**, keep the boss drops (add chest copies if chest data gets edited). Optionally set its price to 4000 so one sells for 2000 | This is Silver Light: a full refill found as treasure, never bought |

With the proposed growth, one Mental Gum gives Lucia 8 MP at L1 (2 Healing Waters), 17 at L10 (4) and 27 at L20
(6 to 7). SSSC's Star Light gave 7 to 10 heals and EBC's about 5. If 35% feels stingy in playtesting, 40% is the
next step.

Percent restore is the right choice here (no code change). EBC's Star Light appears to be a share of max MP too,
and a flat amount would need a change in `func_0206a8b8`. A flat 30 MP Gum (SSSC-style) would be worth 7 heals at
level 1 and too little by level 50.

### 7.4 What not to change

- Healing statues stay the main refill (they are the PS1 Althena statues). Design item 8 already adds status
  curing to them.
- No inns are needed to match the PS1 feel; neither PS1 game has one.
- Area-clear refill stays removed (design item 2).

### 7.5 Edits in one place

| Edit | Address | Kind |
|---|---|---|
| Uncouple spell unlocking from MP cost | `func_02050c50` | small ARM patch (prerequisite) |
| Lucia/Flora spell costs (7.1) | 0x0209497C + spell * 0xC | data |
| Lucia level 1 MP 18 to 24 (Flora 18 to 22 optional) | 0x02094B4C + char * 0x60 + 0x0C | data |
| Mental Gum 35%, price 600 | 0x0209D124 + 2 * 0xC + 6; item 0x116 + 0x10 | data |
| Mental Drop 100% (price 4000 optional) | 0x0209D124 + 3 * 0xC + 6; item 0x117 + 0x10 | data |
| Mental Gum in item shops | free entries of each slot 3 list (re-mp-jobs-rings.md 1.4) | data |

## 8. Open points

- EBC Star Light: flat 20 MP or a third of max MP. One test in EBC would settle it.
- EBC MP pools by level. The EBC estimates in sections 3 and 6 rest on fragments.
- Formation sizes in both games, which turn silver per enemy into silver per battle.
- This game's regular-battle silver at mid and late levels. Enemy EXP is linear in level (docs/boss-exp.md), so it
  grows with level. Raft at level 10 gives 653 as about ten regulars, so a level 10 regular enemy pays about 65
  and a battle maybe 130 to 260. This needs a measurement before tuning the Mental Gum price further.
- Whether the 2025 Remastered Collection changed any PS1 prices.

## Sources

- rpgclassics, Lunar: Silver Star Story Complete (PS1) shrine: [index](https://shrines.rpgclassics.com/psx/lsssc/),
  [shops](https://shrines.rpgclassics.com/psx/lsssc/shops.shtml), [healing items](https://shrines.rpgclassics.com/psx/lsssc/items/healing.shtml),
  [magic](https://shrines.rpgclassics.com/psx/lsssc/magic.shtml), [level charts](https://shrines.rpgclassics.com/psx/lsssc/levelcharts.shtml),
  [enemies](https://shrines.rpgclassics.com/psx/lsssc/enemies.shtml), [walkthrough](https://shrines.rpgclassics.com/psx/lsssc/walkthrough.shtml)
- rpgclassics, Lunar: The Silver Star (Sega CD) shrine: [items](https://shrines.rpgclassics.com/sega_cd/ltss/items/normal.shtml),
  [shops](https://shrines.rpgclassics.com/sega_cd/ltss/shops.shtml), [Luna's magic](https://shrines.rpgclassics.com/sega_cd/ltss/magic/luna.shtml)
- GameFAQs, Lunar 2: Eternal Blue (PlayStation, i.e. Eternal Blue Complete), read through archive.org copies:
  [Shotgunnova shop list](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/52748),
  [Sybillium FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10184),
  [ATadeo FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10185),
  [DWagoner FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10097),
  [Kiko-kun FAQ](https://gamefaqs.gamespot.com/ps/197807-lunar-2-eternal-blue/faqs/10153)
- Lunar wiki (fandom), read through its API: [Star Light](https://lunar.fandom.com/wiki/Star_Light),
  [Silver Light](https://lunar.fandom.com/wiki/Silver_Light), [Herb](https://lunar.fandom.com/wiki/Herb),
  [Healing Nut](https://lunar.fandom.com/wiki/Healing_Nut), [Angel's Tear](https://lunar.fandom.com/wiki/Angel%27s_Tear),
  [Passion Fruit](https://lunar.fandom.com/wiki/Passion_Fruit), [Horam](https://lunar.fandom.com/wiki/Horam),
  [Ronfar](https://lunar.fandom.com/wiki/Ronfar), [Lucia](https://lunar.fandom.com/wiki/Lucia)
- [almarsguides, Silver Star Story (Saturn) item list](https://almarsguides.com/retro/walkthroughs/saturn/games/lunarsilverstarstory/misc/lists/items/)
- Local PS1 scripts: `build/research/lunar_scripts/sssc_script.txt`, `build/research/lunar_scripts/ebc_script.txt`
