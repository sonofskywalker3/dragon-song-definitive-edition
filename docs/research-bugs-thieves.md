# Lunar: Dragon Song (US) research: save glitch, thieves, breakers, level scaling, bugs

Researched 2026-10-05. Each claim is tagged **[confirmed]** (a source states it, URL given) or **[uncertain]** (inference, conflicting sources, or not found). "Confirmed" means "a published source says so", not "verified in the ROM".

## Sources used

| Short name | What it is | URL |
|---|---|---|
| SaveGlitchFAQ | "Save Glitch FAQ" v1.02 (2006-01-30) by Andrea "AquaHaute" Robinson, with Synonymous. Archived 2010-07-14 | https://web.archive.org/web/2010/https://www.gamefaqs.com/ds/925564-lunar-dragon-song/faqs/41373 |
| Ripclaw | FAQ/Walkthrough by A Darkstar Ripclaw, "Version Zeta Final" (2009-01-05) | https://web.archive.org/web/2010/http://www.gamefaqs.com/ds/925564-lunar-dragon-song/faqs/52095 |
| darklao | FAQ/Walkthrough by darklao, v0.96 (2005-11-21), has a per-area bestiary with special attacks | https://web.archive.org/web/2010/http://www.gamefaqs.com/ds/925564-lunar-dragon-song/faqs/39777 |
| ABolner | FAQ/Walkthrough by ABolner, v1.04 (2005-10-09), boss HP ranges | https://web.archive.org/web/2010/http://www.gamefaqs.com/ds/925564-lunar-dragon-song/faqs/39224 |
| CardFAQ | Monster Card FAQ by ARobinson (AquaHaute), v1.03 (2005-10-21) | https://web.archive.org/web/2010/http://www.gamefaqs.com/ds/925564-lunar-dragon-song/faqs/39266 |
| LP | Let's Play Archive, Lunar: Dragon Song (parts 1 to 32) | https://lparchive.org/Lunar-Dragon-Song/ |
| DCGB | DC Game Blog, "Lunar Retrospective: Dragon Song" (2024) | https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/ |
| HG101 | Hardcore Gaming 101 article | https://www.hardcoregaming101.net/lunar-dragon-song/ |
| TVTropes | TV Tropes game page | https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/LunarDragonSong |
| GameHoard | The Game Hoard, "Disaster Report" (2021) | https://thegamehoard.com/2021/11/12/disaster-report-lunar-dragon-song-ds/ |

Not reachable: lunarthreads.com (HTTP 403, and in a real browser it shows "Temporarily closed for maintenance"; topics t=773 "Stealing & Breaking Armor/Weapons" and t=5867 "In this thread we fix Lunar: Dragon Song" look relevant but are not in the Wayback Machine). Neoseeker's info thread had only pre-release news. The archived GameFAQs FAQ list (2010) has exactly six guides: three walkthroughs, Monster Card FAQ, Music Hall Guide, Save Glitch FAQ.

---

## 1. The Save Glitch

### What it is
- **[confirmed]** On the Frontier continent, after Flora leaves the party, certain actions make a red line appear through the "Save" menu option. Saving stays disabled until the DS is powered off; it is not permanent and the save file is **not corrupted**. The fix is to power-cycle and reload the last save (losing unsaved progress). (SaveGlitchFAQ, sections 2.1 and 2.5)

### What triggers it
The FAQ authors say "We're not entirely sure" and list two actions, both only possible on the Frontier continent (SaveGlitchFAQ, section 2.3):
1. **[confirmed as reported, cause uncertain]** Getting a **bad fortune from the fortune-teller in Lind Village**. This does "not NECESSARILY" disable saving.
2. **[confirmed as reported]** Going **back to the Underground Tunnel and talking to Flora after she leaves the party**.

- **[uncertain]** The exact flag or code cause is unknown. Nobody in the sources found the root cause. A plausible ROM-side guess (not sourced): both actions run a script that sets a "save disabled" flag (the same mechanism the game uses deliberately in two places, see below) and never clears it.

### Intended (not a bug) save lockouts
**[confirmed]** (SaveGlitchFAQ, section 2.2) Saving is disabled on purpose in two places:
1. Between the Gronk fight (Cathedral of Althena) and the Beast King Zethos fight. Losing to Zethos means refighting Gronk.
2. Inside the four corner areas before the Chamber of Rebirth. You can only leave by clearing all enemies in Virtue Mode; afterwards you are teleported back to the walkway and can save again.
- **[confirmed]** LP part 16 also notes saving being blocked near the end ("Hm we can't save"), consistent with an intentional lockout. https://lparchive.org/Lunar-Dragon-Song/Update%2016/

### How to avoid it
**[confirmed]** (SaveGlitchFAQ, section 2.4)
- Do not get your fortune told; or save right before talking to the fortune-teller and, after a bad fortune, check the Save option and reset if it is struck out. The FAQ author did not know whether fortunes are random or condition-based.
- Do not talk to Flora in the Underground Tunnel after she leaves. Using the Althena statue there and shopping in Lind are fine. Talking to her does not affect when she rejoins.

### Region
- **[confirmed]** Present in the **North American** release. Synonymous tested the Japanese version (Lunar Genesis) and **it does not occur there at all** (v1.02 changelog: "Received confirmation that the glitch does not appear in the Japanese version at all"). (SaveGlitchFAQ, sections 2.1 and 3.3)
- **[uncertain]** European release: the FAQ author did not know.

---

## 2. Thieves and equipment breakers

### General mechanics
- **[confirmed]** Stolen items are gone permanently; they are not returned at the end of battle. (LP part 2: https://lparchive.org/Lunar-Dragon-Song/Update%2002/ ; DCGB ; GameHoard)
- **[uncertain]** What can be stolen: the LP author thinks only sundries and items, not equipment ("I could be wrong"). TV Tropes' "Breakable Weapons" entry says monsters "may break or steal a character's weapon or armor". No source gives a confirmed case of equipped gear being stolen, so treat "steals equipment" as unconfirmed. DCGB says theft targets inventory items and complains it tends to hit rare delivery items.
- **[confirmed]** A broken equipment piece is not removed; it is replaced by the worst item of that equipment class (for example "Broken Umbrella" for Lucia). Lind Village sells the broken items. (LP part 7: https://lparchive.org/Lunar-Dragon-Song/Update%2007/ ; Ripclaw weapons section: "Jian ends up with this if his weapon gets broken", "Lucia ends up with this if her weapon gets broken")
- **[confirmed]** There is no repair. (TVTropes, GameHoard)
- **[confirmed]** Breaking is fairly rare per hit. (LP part 9: https://lparchive.org/Lunar-Dragon-Song/Update%2009/)

### Enemies that steal
| Enemy | Where (per darklao bestiary) | Source |
|---|---|---|
| Yeti | Thieves' Woods, Valley of Neza | darklao (SpAtk: Steal); Ripclaw list |
| Sturge | Delrich Temple, Guystole Mine, Meryod Cave | darklao (SpAtk: Blind, Steal); Ripclaw list |
| Thanatos | Delrich Temple, Cathedral of Althena, Elda Canyon, Sandra Desert | darklao; Ripclaw list |
| Ice Mongrel | Moto Rainforest, White Dragon Cave (darklao lists Thieves' Woods Ice Mongrel without Steal) | darklao; Ripclaw list |
| Ochu | White Dragon Cave | darklao; Ripclaw list |
| **Morus** (boss, with Caucus and Orcus, Elda Canyon) | Elda Canyon | Ripclaw: "Morus can also steal items, as well as stealing two items in the same move"; ABolner: "If Morus physically attacks, she does two per round, and always steals something if she hits" |

All rows **[confirmed]** by the cited FAQ; darklao's location column is per-area bestiary listings and may be incomplete.

- **[confirmed, story event]** In Thieves' Woods a monster group (Yetis / "monkey mob" / Sasquatch bandits) steals Jian's delivery package in a cutscene; the four Sasquatch minibosses in Delrich Temple are those thieves. This is scripted, not the battle steal. (Ripclaw; LP part 1; DCGB)

### Does any enemy run away / escape after stealing?
- **[uncertain, not found]** No source I could reach describes any enemy fleeing a battle, after stealing or otherwise. The FAQs, LP, and reviews describe stealing only as permanent item loss. The only "flee" mechanics found are player-side: the **Ice Mongrel card** (100% escape from non-boss battles), the **Ghoula card** (map symbols flee from you for a while), the DS microphone "Run" command, and in LP part 14 map enemy symbols hiding in trees. If this matters for the hack, it needs to be checked in the ROM's battle AI / action tables.

### Enemies that break equipment
| Enemy | Source |
|---|---|
| Duager (Guystole Mine onward; Orcus is "a beefed-up version of a Duager") | darklao, Ripclaw, darklao tip #3 |
| Abadon (Barrel Desert, Sandra Desert, Red Dragon Cave) | darklao, Ripclaw |
| Phantom (Cathedral of Althena, Elda Canyon) | darklao bestiary and tip #3 |
| Quetzalcoatl (Red Dragon Cave, White Dragon Cave) | darklao, Ripclaw |
| Treant (Roland Forest, dragon caves, Moto Rainforest) | Ripclaw list only (darklao bestiary does not mark it) |
| **Moran** (boss, 3rd San Coliseum fight; tail swipe poisons and can break) | Ripclaw, ABolner ("This guy can and will break your equipment") |
| **Orcus** (boss, Elda Canyon trio) | Ripclaw |
| "Ball-and-chain enemies" in Cathedral of Althena | ABolner (likely the Phantom, **[uncertain]** match) |
| Elda Canyon minibosses, and an Elda-area enemy that broke three pieces in a row | DCGB |
| An unnamed Sandra Desert enemy that "likes to break equipment" | DCGB |

Rows are **[confirmed]** for the named source.
- **[uncertain]** "Scorpion" identity: a search snippet mentioned a scorpion in Sandra Desert that breaks weapons (attributed to the inaccessible lunarthreads thread). Abadon is the darklao-listed breaker in Sandra Desert, and Moran attacks with a tail, so either could be the "scorpion"; no reachable source pairs the name with the sprite.

### Cards that protect
- **[confirmed]** **Termite** card: "Prevent equipment from getting broken" / "Enemies that can destroy equipment will be unable to do so". Max Point 1000, Rock attribute, weak to Fire. (Ripclaw card list; CardFAQ)
- **[confirmed]** **Yeti** card: "Prevent items from getting stolen" / "Enemies that can steal will be unable to do so". Max Point 1800, Fire attribute, weak to Water and Electricity. (Ripclaw; CardFAQ; LP part 2)
- **[confirmed]** Protection lasts one battle per use, and cards have limited uses before they break (re-obtain by farming the enemy). (darklao tip #3: "a Termite card can protect you for one battle, it has limited uses"; HG101)

---

## 3. Does enemy strength scale with party level?

Short answer: **[confirmed]** multiple independent sources say yes, for regular enemies as well as bosses, keyed mainly to Jian's level. **[uncertain]** the formula, and how steep it is (one data point suggests boss HP scaling is small).

Evidence for scaling:
- **[confirmed]** Ripclaw ("Why Power Leveling Won't Work"): monsters and bosses base their stats on Jian's level; "You go up a level, their stats go up."
- **[confirmed]** darklao (tip #1): "Enemy strengths, including their stats and AC rewards, are based on your own levels, and on the area in the game they're in. This applies to bosses as well." Example: first-area enemies have 20 to 70 HP depending on your levels.
- **[confirmed]** LP part 4: scaling "seems to go by Jian's level alone"; EXP rewards scale too; loot does not. https://lparchive.org/Lunar-Dragon-Song/Update%2004/
- **[confirmed]** LP part 2: "enemies scale with your level", contrasts with Silver Star Story where only bosses scaled, with a cap. https://lparchive.org/Lunar-Dragon-Song/Update%2002/
- **[confirmed]** ABolner: "Boss HP is variable with your level; I'm almost sure of this", and gives HP as ranges (for example Sasquatch 240 to 251 at Jian/Lucia level 9).
- **[confirmed]** TVTropes "Level Scaling": foes scale with player level, extended from bosses to all enemies.
- **[confirmed]** DCGB: author observed it ("enemies seem to scale up with the player") but notes it is not stated in the manual.

Evidence that it is weak or capped:
- **[confirmed]** HG101: "Technically the enemies scale up with you ... but there are either level caps or they don't increase proportionally", and you "can generally just out-level your opponents".
- **[confirmed, single data point]** LP part 17 (level 1 attempt): Sasquatch had 240 HP with Jian at level 1, versus ABolner's 240 to 251 at level 9. So that boss's HP barely moved over 8 levels. https://lparchive.org/Lunar-Dragon-Song/Update%2017/
- **[uncertain]** Nobody published a formula or fixed-vs-scaled stat tables. No enemy list with fixed stats was found (darklao's bestiary lists only special attacks and drops). Confirming the formula needs ROM/RAM inspection (compare one enemy's stats at two Jian levels).

---

## 4. Other known US-version bugs and translation issues

- **[confirmed]** Save Glitch above is the only bug with a dedicated GameFAQs guide, and is described as "a known glitch in the North American version". (SaveGlitchFAQ)
- **[confirmed]** Courier-job package names are often misspelled (translation). (TVTropes, "Blind Idiot Translation")
- **[confirmed]** Card descriptions are sometimes unclear due to translation (LP part 1).
- **[confirmed, not a bug]** The battle speed-up button (hold R / triggers) was added to the English releases. (TVTropes; ABolner)
- **[confirmed, design]** Running drains HP at a flat rate that does not scale; running is disabled when any member drops to about 1/3 HP. (TVTropes; DCGB; LP part 14)
- **[uncertain]** DCGB suspects the Red Dragon boss AI "broke" (went passive after taking heavy damage); LP part 11 says a dragon boss can be staggered/stunned for two rounds by enough damage per round. Likely intended stagger mechanics, not a bug.
- **[uncertain]** LP part 27 (fan-consultant commentary): the US translation and bug-fixing reportedly ran in parallel with Japanese development on a tight schedule. Anecdotal; could explain US-only bugs like the save glitch.
- No other freezes, crashes, or soft-locks in the US version were found in reachable sources.
