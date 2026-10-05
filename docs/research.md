# Research before building

Each item is something to learn from the game itself before the matching fix in [design.md](design.md) is built.

| # | Question | Needed for | Status |
|---|---|---|---|
| 1 | Do enemies scale with the party's level, and how (caps, rate)? Source so far: TV Tropes only | Battle rewards | Answered from code ([re-enemies.md](re-enemies.md)): enemy level = highest party level minus a small random amount, clamped to a per-area range. Emulator check pending |
| 2 | Does leveling up ever ask the player to choose something (skills, stats)? | Party: benched EXP | Answered from code ([re-field-battle.md](re-field-battle.md)): no choices on level-up |
| 3 | In the original game, what happens when a character's target dies before their attack: switch or miss? | Targeting | Answered from code: the game auto-targets (70% lowest-HP front enemy, 30% random). Single attacks never whiff; extra hits of a multi-hit move on a dead target are wasted |
| 4 | Who joins, leaves and dies in the story, and when? Where could returning characters wait? | Party | Answered from fan sources, see [story-party-timeline.md](story-party-timeline.md). Never more than 3 characters available at once; Lucia leaves for good, Rufus dies |
| 5 | Exact run time and cooldown of the Eternal Blue Complete (PS1) dash | Running | Reviews say about 3 s run, 3 s cooldown. Exact timing still to be measured |
| 6 | Do thieves run away after stealing in the original game, and how often? Morus is a known thief | Stealing | Answered from code: thieves take only materials and sundries (items 287 to 386), never gear. No enemy ever flees |
| 7 | What is the GameFAQs "Save Glitch FAQ" about, and is it a bug worth fixing? | Possible new fix | Root cause found: story flag 0xCF is set by Flora's tunnel line and never cleared. Fix: point that line at an unused flag |
| 8 | Enemy EXP values, to base the new silver drops on | Money | Enemy EXP table dumped (src/dsde/enemies.py). No silver field exists; silver drops need new code |

## Starting points

- RetroArch cheat file in the ROMs project, `tmp/lrdb/cht/Nintendo - Nintendo DS/Lunar - Dragon Song (USA).cht`,
  gives RAM addresses for every character's stats, money, the three party slots and a removed debug room.
- `extract/files/btldata.dat` probably holds enemy data (items 1, 6, 8).
- `extract/files/script.dat` and `evedata.dat` probably hold the story text and events (item 4).
- Sources: [RPGFan review](https://www.rpgfan.com/review/lunar-dragon-song/),
  [Arcadia Pod review](https://arcadiapod.com/2022/02/08/review-lunar-dragon-song-2005/),
  [TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/LunarDragonSong),
  [Thinking Inside the Box](https://wwwthinkinginsidethebox.blogspot.com/2014/04/lunar-dragon-songs-gameplay.html),
  [Save Glitch FAQ](https://gamefaqs.gamespot.com/ds/925564-lunar-dragon-song/faqs/41373).
