# Community feedback and outreach research

Researched 2026-10-06. Two parts: (1) what players and critics say is wrong with Lunar: Dragon Song,
writing first, then gameplay the design doc does not already cover, plus concrete fix suggestions;
(2) where Lunar fans and ROM hack audiences gather and how to reach them.

Quotes are short and verbatim from the source unless marked as a paraphrase. View and member counts
are as shown on the date given. Anything not confirmed first-hand is marked **(unverified)**.

## Summary

- **Writing.** The complaints that come up most: (1) the plot rehashes Silver Star, with the Lucia is
  Althena twist in plain sight; (2) flat characters with no banter or arcs; (3) a stiff, literal, lifeless
  localization full of typos and names spelled two ways; (4) an anticlimactic ending in which the villain,
  Ignatius, dies in a cutscene and is never fought. After those: motivations nobody explains, emotional
  beats the story never set up, a shallow racism theme, weak villains, and contradictions with Lunar 1 and 2.
- **Gameplay not yet in the design doc.** Fleeing by blowing into the microphone (very common), slow
  battles, new party members joining at level 1 while enemies scale to Jian's level, Jian's headstand curse,
  scarce MP and expensive healing, Dragon Magic tied to rings, and Gad's Express quests with misspelled
  recipient names or items you can't get.
- **There is demand.** Players keep saying a hack could fix the game, and they list nearly the same fixes
  this hack makes. The biggest example is a 286K-view video from April 2026 that lists the fixes outright.
- **Where people are.** r/Lunar is small: about 1,476 members in February 2025, though its Dragon Song
  threads still draw 80+ comments. The larger audience is the people watching "worst RPG ever" videos:
  three videos with about 677K views between them. Next come r/JRPG, the DS hacking subreddits, and the
  ROM hack news pipeline (Romhack Plaza, then Time Extension).
- **Outreach.** Do not mass-comment on YouTube. YouTube's spam policy names exactly that ("identical or
  similar ... messages across hundreds of videos") as comment spam. Write directly to the 3 to 5 creators
  whose videos fit, send before/after clips, keep a public devlog, and post once in each relevant
  community when there is a playable build.

## Method and access notes

- Read in full or in part: RPGFan (two reviews), Nintendo World Report, WorthPlaying, Hardcore Gaming 101,
  The Game Hoard, DC Game Blog, Arcadia Pod, dreager1, TV Tropes YMMV, Wikipedia, Metacritic user reviews
  (through its JSON backend), the lparchive Let's Play (parts 1, 6, 7, 8, 10, 13, 16, 21 to 23, 32), r/Lunar
  and r/JRPG threads (through the PullPush Reddit archive API), and transcripts of four YouTube videos
  (downloaded captions).
- **Blocked or unreadable:** GameSpot (403), GameFAQs (403), IGN, Eurogamer and web.archive.org (the fetch
  tool refuses them, so 1UP through the archive could not be reached either), RPGamer archive reviews (403;
  only search-engine snippets used), Lunar Threads forum (403), Backloggd (403), the Lunar Fandom wiki (403).
  reddit.com blocks direct access, so Reddit data comes from the PullPush and Arctic Shift archives.
  HowLongToBeat reviews were not checked.
- **TCRF:** not usable. curl gets a Cloudflare challenge, and the fetch tool returned text that was not the
  article (it read like an attempt to manipulate an AI reader), so nothing from it is used. Search engines
  only show that the page lists unused areas and debug features and is marked as a stub
  ([TCRF](https://www.tcrf.net/Lunar:_Dragon_Song), **unverified**).
- The "how common" counts are the number of distinct sources, among the roughly 30 reviewed, that raise
  the point. They are a ranking aid, not a survey.

---

# Part 1: complaints and suggestions

## 1A. Writing, script and story complaints (ranked)

| # | Complaint | Sources raising it | Where in the game |
|---|-----------|--------------------|-------------------|
| 1 | Story is a rehash of Silver Star; Lucia is Althena twist is obvious | ~12 | Whole game; reveal at Ignatius fight |
| 2 | Characters are flat, no banter, no arcs | ~11 | Whole party |
| 3 | Localization is lifeless, literal, awkward, nothing like Working Designs | ~11 | Whole script, NPCs especially |
| 4 | Anticlimactic ending; Ignatius never fought, falls to his death | ~11 | Vile Castle / ending |
| 5 | Motivations and events poorly explained; joins and leaves with no reason | ~8 | Healiz, Jian leaving party, Flora joining |
| 6 | Typos and names spelled two ways | ~7 | Gad's Express menus, Gabryel/Gabriel |
| 7 | Contradicts Lunar 1 and 2 lore | ~7 | Frontier, Vile Tribe origin, resonance |
| 8 | Emotional beats not set up (romance, group hug, Lucia's "death") | ~6 | Ending, Black Dragon area |
| 9 | Racism theme shallow and dropped | ~6 | Healiz, beastmen NPCs |
| 10 | Villains weak (Ignatius, Morus, Zethos's plan) | ~6 | Mid and late game |
| 11 | Long, repetitive exposition and repeated lines | ~5 | Intro, Zethos, Jian's "save Lucia" |
| 12 | Lucia sidelined as damsel, absent most of the game | ~5 | After Sunrid Bridge |
| 13 | Reusing the name "Lucia" from Lunar 2 | ~5 | Whole game |
| 14 | No cutscenes, voice or FMV; static images | ~5 | Presentation |
| 15 | Rufus underused, dies off screen, nobody mourns | ~4 | Late game |
| 16 | Gabryel told not shown; betrayal subplot resolved in seconds | ~4 | Healiz / coliseum |
| 17 | Narm: the "curse" that stops headstands; robotic flirting NPCs | ~4 | Early game, towns |
| 18 | Flora has no personality | ~3 | From Lynn Village on |
| 19 | Pacing: first half rushed, Dragon Trials long, Negri Lab padding | ~3 | Second half |

Details, with 1 to 3 sources each:

1. **Rehash of Silver Star.** Same four-dragon trials, same goddess reincarnation twist, told sooner and less well.
   - HG101: "basically a simplified retread of *Silver Star Story*" ([HG101](https://www.hardcoregaming101.net/lunar-dragon-song/))
   - lparchive part 7: "the game is just flat-out telling us that Lucia is Althena's reincarnation" ([LP 07](https://lparchive.org/Lunar-Dragon-Song/Update%2007/))
   - r/Lunar, 2026: "We have The Silver Star at home." ([r/Lunar](https://reddit.com/r/Lunar/comments/1vhq1ma/how_is_the_story_in_dragon_song/))

2. **Flat characters.**
   - RPGFan (Patrick Gann): "I can't remember one single dialogue that I would consider significant" ([RPGFan 2](https://www.rpgfan.com/review/lunar-dragon-song-2/))
   - ItsChocobose (YouTube, 2026-09-25): "These are concepts of characters, not actual characters." ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
   - i am a dot (YouTube): "the characters need to have some more inter-personal banter" ([video](https://www.youtube.com/watch?v=g3ZHiycAYeQ))

3. **Lifeless or literal localization.** Often compared with Working Designs' lively PS1 scripts.
   - WorthPlaying: "a translation so literal it's almost nonsense, and one riddled with typos" ([WorthPlaying](https://worthplaying.com/article/2005/11/12/reviews/28955-nds-review-lunar-dragon-song/))
   - HG101 calls the English script "sterile and boring" next to Working Designs ([HG101](https://www.hardcoregaming101.net/lunar-dragon-song/))
   - ItsChocobose: "weirdly beige, grammatically functional, emotionally vacant" ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
   - Note: the lparchive LP has a reader comparing a Black Dragon line with the Japanese and finding the
     Japanese clearer ([LP 13](https://lparchive.org/Lunar-Dragon-Song/Update%2013/); the exact wording is
     **unverified**: the summarizer garbled it). Famitsu praised the Japanese version's "excellent" story and
     characterization ([Wikipedia](https://en.wikipedia.org/wiki/Lunar:_Dragon_Song)). Both hint that part of
     the problem is the English script, not the story underneath.

4. **Anticlimactic ending.**
   - RPGFan (Gann): "it would be like ending Silver Star two thirds of the way through" ([RPGFan 2](https://www.rpgfan.com/review/lunar-dragon-song-2/))
   - TV Tropes: Ignatius is "shafted as a Cutscene Boss" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))
   - dreager1: "a main villain who actually goes out without a fight" ([dreager1](https://dreager1.com/2021/04/18/lunar-dragon-song-review/))

5. **Motivations not explained.**
   - Nintendo World Report: "the specific chain of events is so poorly explained" ([NWR](https://nintendoworldreport.com/review/4413))
   - RPGFan (Mickey Shannon): "little motivation is given as to why a character joins or leaves the party" ([RPGFan 1](https://www.rpgfan.com/review/lunar-dragon-song/))
   - Nudl on Flora: "no reason to help Jon and Gabriel whatsoever" (auto-captions spell Jian as "Jon") ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

6. **Typos and inconsistent names.**
   - RPGFan (Gann): "in a few menus, one will see the name Gabriel instead" ([RPGFan 2](https://www.rpgfan.com/review/lunar-dragon-song-2/))
   - WorthPlaying: told to deliver to "Laban", the NPC is "Raiban" ([WorthPlaying](https://worthplaying.com/article/2005/11/12/reviews/28955-nds-review-lunar-dragon-song/))
   - lparchive part 6: "Names being inconsistent happens a lot in this game" ([LP 06](https://lparchive.org/Lunar-Dragon-Song/Update%2006/))

7. **Lore contradictions with Lunar 1 and 2.**
   - lparchive part 10, on Titus's Vile Tribe origin story: "This is blatantly wrong." ([LP 10](https://lparchive.org/Lunar-Dragon-Song/Update%2010/))
   - TV Tropes: "Where is Althena's Sword? What happened to all the other Dragonmaster armors?" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))
   - r/Lunar: "literally had to wait til the end for it to reference something" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))

8. **Emotional payoffs with no setup.**
   - lparchive part 16: "we have no investment in their relationship" ([LP 16](https://lparchive.org/Lunar-Dragon-Song/Update%2016/))
   - lparchive part 13, on the group hug: "trying to have pay-off for stuff that it never set-up" ([LP 13](https://lparchive.org/Lunar-Dragon-Song/Update%2013/))
   - TV Tropes "Tear Dryer": Lucia "dies and then is revived within a 3-minute interval" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))

9. **Racism theme shallow.**
   - ItsChocobose: its message is something "stitched on a throw pillow" ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
   - DC Game Blog: "The two races mingle a lot more than the opening suggests" ([DC Game Blog](https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/))
   - dreager1: "not handled nearly as well" as Arc the Lad ([dreager1](https://dreager1.com/2021/04/18/lunar-dragon-song-review/))

10. **Weak villains.**
    - ItsChocobose: an evil Dragonmaster "should be absolutely devastating. It isn't." ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
    - r/Lunar: Ignatius is "a Ghaleon clone with all the Charisma of a dishcloth" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))
    - lparchive part 7: "they should just talk about all the evil they're gonna do. *Threatening.*" (sarcasm) ([LP 07](https://lparchive.org/Lunar-Dragon-Song/Update%2007/))

11. **Long, redundant exposition.** Directly relevant to playtest item 2 (Jian's self-introduction).
    - Nudl, on the opening's self-introduction: "That's some necessary info right there." (sarcasm) ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))
    - lparchive part 1: "a static, rambling text dump explaining the backstory" ([LP 01](https://lparchive.org/Lunar-Dragon-Song/Update%2001/)); part 6, on Zethos's speeches: "will you all shut up already!" ([LP 06](https://lparchive.org/Lunar-Dragon-Song/Update%2006/))
    - dreager1: Jian keeps saying he has to save Lucia: "He says this a whole lot." ([dreager1](https://dreager1.com/2021/04/18/lunar-dragon-song-review/))

12. **Lucia sidelined.**
    - The Game Hoard: "unable to do much more than be the damsel in distress" ([Game Hoard](https://thegamehoard.com/2021/11/12/disaster-report-lunar-dragon-song-ds/))
    - RPGFan (Gann): "Take a boy, put him with a girl. Then take away the girl" ([RPGFan 2](https://www.rpgfan.com/review/lunar-dragon-song-2/))

13. **The name "Lucia".** A different character from Lunar 2's Lucia, and players find that confusing.
    - DC Game Blog notes two characters from different games share the name ([DC Game Blog](https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/))
    - An r/Lunar user says the two names differ in vowel length in Japanese ([r/Lunar](https://reddit.com/r/Lunar/comments/1mcfht4/dragon_song/), **unverified**)
    - Related: the main cast's surnames echo the band Genesis (Collins, Banks), noted by ItsChocobose ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))

14. **No cutscenes or voice.**
    - ItsChocobose: "you get a powerpoint" ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
    - Not fixable through text. Listed for completeness.

15. **Rufus underused.**
    - r/Lunar: "the coolest party member gets eaten off screen" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))
    - DC Game Blog: "The death of Rufus is hardly touched upon" ([DC Game Blog](https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/))

16. **Gabryel told, not shown.**
    - lparchive part 6: "Those sound like interesting character moments. I wish I had seen them" ([LP 06](https://lparchive.org/Lunar-Dragon-Song/Update%2006/))
    - Nudl, on the princess reveal: "They make up 10 seconds later." ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

17. **Narm.**
    - TV Tropes: players find it "impossible to take this 'Curse' seriously" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))
    - HG101: flirty female NPCs "come off as weirdly robotic instead of goofily charming" ([HG101](https://www.hardcoregaming101.net/lunar-dragon-song/))

18. **Flora has no personality.**
    - i am a dot: "Flora... man I have no idea. Give her a personality." ([video](https://www.youtube.com/watch?v=g3ZHiycAYeQ))
    - Nudl: "this character is insanely bland" ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

19. **Pacing.**
    - DC Game Blog: the first half "moves rather quickly", then "the same amount of time" goes to the Trials ([DC Game Blog](https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/))
    - TV Tropes "Padding": Negri Ocean Lab, with doors "only unlocked by levers that are always on the opposite side" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))

**Dissenting views** (worth keeping in mind): RPGFan's Shannon calls it "an intriguing story with at least two
major plot twists" ([RPGFan 1](https://www.rpgfan.com/review/lunar-dragon-song/)). One r/JRPG user found the story
and characters "alright, if flat" ([r/JRPG](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/)).
One r/Lunar user praises the side plots on beastmen racism ([r/Lunar](https://reddit.com/r/Lunar/comments/1vhq1ma/how_is_the_story_in_dragon_song/)).
The consensus: the bones are fine and the telling is poor, which is exactly what a script pass can address.

**Background that matters for the script:** no writer is credited ([LP 16](https://lparchive.org/Lunar-Dragon-Song/Update%2016/)).
A fan consultant from Lunar-Net says Ubisoft brought in fans to advise, but "the fans' suggestions,
corrections, and input were being ignored" ([LP 22](https://lparchive.org/Lunar-Dragon-Song/Update%2022/)).
The consultants "never played any part of the game" ([LP 23](https://lparchive.org/Lunar-Dragon-Song/Update%2023/)).
This rests on a single forum source ([ItsChocobose](https://www.youtube.com/watch?v=XnoEOkb8jWQ) flags it the same way).

## 1B. Gameplay complaints not covered by docs/design.md (ranked)

Already covered by the design doc and left out here: running HP cost, the Combat/Virtue split, money only from
deliveries, no targeting, gear breaking, theft, boss EXP, benched EXP, area-clear refill and respawn timer.

| # | Complaint | Sources | Notes |
|---|-----------|---------|-------|
| 1 | Flee by blowing into the microphone; background noise triggers it | ~8 | Very common, easy to explain in a clip |
| 2 | New members (Gabryel, Flora) join at level 1 while enemies scale to Jian | ~7 | Benched EXP does not cover first joins |
| 3 | Battles are slow; long animations | ~5 | The game has a fast-forward button, which i am a dot mentions |
| 4 | Jian's curse (one hit instead of three) lasts hours | ~5 | Early game slog |
| 5 | MP scarce, healing costs most of Lucia's MP, no MP restoratives sold | ~5 | |
| 6 | Gad's Express: wrong or misspelled names, rare or impossible items, quit fee, one job at a time | ~6 | Less important now that battles drop silver |
| 7 | Dragon Magic tied to rings, one spell at a time, costs the accessory slot | ~4 | |
| 8 | Cards: one per enemy type, limited uses, some do nothing, others trivialize fights | ~4 | |
| 9 | Item menu split into many categories | ~3 | |
| 10 | Lucia weak; only Jian does real damage | ~3 | Design doc's stat buffs are on hold |
| 11 | Lucia leaves with the good gear found in the bridge dungeon | 2 | |
| 12 | Unclear directions early (finding Lucia, Thieves' Woods back and forth) | 2 | |
| 13 | Negri Ocean Lab lever backtracking | 2 to 3 | |
| 14 | Single mentions: healing statues do not cure poison, no statues in three late dungeons, can't delete save files, constantly pulsing touch icons, vague giant's stone puzzle, forced walking segments, high shop prices | 1 each | |

Sources:

1. **Microphone flee.**
   - TV Tropes: "it precludes you from playing the game near any source of constant noise" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))
   - r/JRPG: "The sound from the bus caused me to automatically run away from battles." ([r/JRPG](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/))
   - ItsChocobose: "the only RPG I know where you could lose progress to a sneeze" ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))

2. **Level 1 joins.**
   - i am a dot: "The enemies' strength is based off of Jian's current level, not anyone else's." ([video](https://www.youtube.com/watch?v=g3ZHiycAYeQ))
   - A streamer's issue list: "New chars keep joining at level 1 with no gear" ([pastebin](https://pastebin.com/GPSJaE6p), linked from [r/JRPG](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/))

3. **Slow battles.**
   - NWR: "battles are still agonizingly slow and uneventful" ([NWR](https://nintendoworldreport.com/review/4413))
   - The Game Hoard: "everyone takes their time executing attacks" ([Game Hoard](https://thegamehoard.com/2021/11/12/disaster-report-lunar-dragon-song-ds/))

4. **Jian's curse.**
   - r/JRPG: it "stays that way for a couple of hours that are a brutal slog" ([r/JRPG](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/))
   - TV Tropes "Slow-Paced Beginning" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))

5. **MP.**
   - r/Lunar: "The basic heal spell at the start of the game takes up all your MP" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))
   - pastebin list: "They don't sell it and all the skills cost a ton." ([pastebin](https://pastebin.com/GPSJaE6p))

6. **Gad's Express.**
   - pastebin list: "Some of the quests are literally impossible." ([pastebin](https://pastebin.com/GPSJaE6p))
   - RPGFan (Gann): "not only tedious, but it is also useless" ([RPGFan 2](https://www.rpgfan.com/review/lunar-dragon-song-2/))

7. **Dragon Magic rings.**
   - TV Tropes: "you can only ever use one at a time" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong))
   - r/Lunar: "the same spell with different elements" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))

8. **Cards.**
   - ItsChocobose: "some cards can't be used at all" ([video](https://www.youtube.com/watch?v=XnoEOkb8jWQ))
   - The Game Hoard: "almost every boss becomes easier if you poison them" ([Game Hoard](https://thegamehoard.com/2021/11/12/disaster-report-lunar-dragon-song-ds/))

9. **Item menu.**
   - pastebin list: "The items menu is divided into 9 pages" ([pastebin](https://pastebin.com/GPSJaE6p))
   - Nudl: "an unnecessarily wide array of item categories" ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

10. **Weak Lucia.**
    - pastebin list: "He hits for 300 when everyone else hits for 30." ([pastebin](https://pastebin.com/GPSJaE6p))

11. **Lucia's gear lost.**
    - r/Lunar: she gets good gear, then is "permanently removed from you" ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))
    - Nudl: "All the equipment and experience I worked for gone." ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

12. **Directions.**
    - i am a dot: "if you follow the directions the game gives you, you will be criss-crossing this map" ([video](https://www.youtube.com/watch?v=g3ZHiycAYeQ))

13. **Negri Lab.**
    - TV Tropes "Padding" ([TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/YMMV/LunarDragonSong)); lparchive chapter 15 is titled "Levers" ([LP index](https://lparchive.org/Lunar-Dragon-Song))

14. **Single mentions.**
    - Statues: Nudl ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))
    - Save files: r/Lunar ([thread](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/))
    - Pulsing icons: [pastebin](https://pastebin.com/GPSJaE6p)
    - Stone puzzle and forced walking: [DC Game Blog](https://www.dcgameblog.com/2024/04/lunar-retrospective-dragon-song/)
    - Prices: Nudl ([video](https://www.youtube.com/watch?v=NxU3DSIhMWU))

## 1C. Concrete suggestions people have made

- **i am a dot** ("My Brief Obsession with the Worst RPG Ever Made", 286K views) gives a full fix list
  ([video](https://www.youtube.com/watch?v=g3ZHiycAYeQ)):
  - Both items and EXP after every battle, and keep the blue chests.
  - Make pathfinding more obvious.
  - Pick targets, which gives Flora more to do against airborne enemies.
  - Running should not hurt.
  - No item durability.
  - Keep the cards, maybe rebalanced.
  - Rename terms to be "more fantasy-like".
  - More party banter and real arcs.
  - "play up the love story between Jian and Lucia".
  - Have Gabryel distrust humans at first and learn to be an ally.
  - Give Flora a personality.

  Of these, the hack already covers rewards, blue chests, targeting, running and breaking.
- **The Game Hoard** ([review](https://thegamehoard.com/2021/11/12/disaster-report-lunar-dragon-song-ds/)).
  These fixes are implied by its complaints rather than stated as a list; the summarizer drew them out, so
  the exact framing is **unverified**:
  - Faster battles.
  - Unified rewards.
  - Targeting.
  - No running drain.
  - Equipment repair.
  - Give Flora a revive spell.
- **r/Lunar, Sept 2025:** "if some genius could just fix the game ... I know for a fact this game would actually
  be considered good" (running, both rewards, targeting) ([r/Lunar](https://reddit.com/r/Lunar/comments/1n9qrnp/extremely_hot_take/)).
- **r/Lunar, May 2025** (88 comments): the original post hoped the remaster collection would include it with
  "being able to target enemies" fixed ([r/Lunar](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/)).
- **r/romhacking, Aug 2022, "Fixing Lunar: Dragon Song":**
  - Remove the running damage.
  - Buff weapons so they break less easily.
  - Choose enemies.
  - A fourth fix that the archive cuts off.

  It drew one reply: "I'm down with this." ([r/romhacking](https://reddit.com/r/romhacking/comments/wjc50q/fixing_lunar_dragon_song/))
- **r/JRPG** comments: "feel like a romhack could fix the game then", "It needs a romhack that fixes the fatal
  flaw of the battle system", "hope someone fixes it" ([r/JRPG](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/)).
- **Lunar Threads** has a thread titled "In this thread we fix Lunar: Dragon Song"
  ([link](https://www.lunarthreads.com/viewtopic.php?t=5867)). It returned 403. A search engine summary says it
  covers plot, characters, villain and a script rewrite (**unverified**). Worth reading by hand in a browser.
- **The lparchive LPer** rewrote one scene and "tweaked the ending" as bonus updates
  ([LP index](https://lparchive.org/Lunar-Dragon-Song), [LP 21](https://lparchive.org/Lunar-Dragon-Song/Update%2021/)).
- The Japanese script may be the best guide for a rewrite (see 1A item 3). Recruiting someone who reads Japanese
  to compare lines against Lunar Genesis is a concrete ask for the community.

---

# Part 2: community and outreach

## 2A. Where Lunar fans gather

| Place | Size / activity | Notes |
|-------|-----------------|-------|
| r/Lunar | 1,476 members (Arctic Shift snapshot, Feb 2025, before the remaster) | Small but Dragon Song threads still get 10 to 88 comments in 2025 to 2026 ([88-comment thread](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/)). Current size **unverified** (reddit blocked) |
| r/JRPG | 255,696 (Feb 2025 snapshot); GummySearch shows 331k ([GummySearch](https://gummysearch.com/r/JRPG/)) | Has a "Is Lunar Dragon Song really that bad?" thread with hack requests ([thread](https://reddit.com/r/JRPG/comments/qjy5e8/is_lunar_dragon_song_really_that_bad/)) |
| r/nds | 49,376 (Feb 2025); GummySearch 63k ([GummySearch](https://gummysearch.com/r/nds/)) | DS players |
| r/NDSHacks | 18,435 (Feb 2025); GummySearch 24k ([GummySearch](https://gummysearch.com/r/NDSHacks/)) | DS hacking specifically |
| r/3dshacks | 142,622 (Feb 2025) | TWiLight Menu++ users, the hack's target hardware path |
| r/romhacking | 12,877 (Feb 2025); GummySearch 16k ([GummySearch](https://gummysearch.com/r/romhacking/)) | Has the 2022 "Fixing Lunar: Dragon Song" post |
| r/retrogaming | 404,689 (Feb 2025); GummySearch 518k ([GummySearch](https://gummysearch.com/r/retrogaming/)) | Broad, strict on self-promotion in many such subs (**unverified** for this one) |
| r/patientgamers, r/SBCGaming, r/RetroHandhelds | 846k, 247k, 37k (GummySearch, date not shown) ([1](https://gummysearch.com/r/patientgamers/), [2](https://gummysearch.com/r/SBCGaming/), [3](https://gummysearch.com/r/RetroHandhelds/)) | Handheld emulation players; good for a finished release |
| Lunar Threads forum | Exists, 403 to tools ([site](https://www.lunarthreads.com/viewtopic.php?t=5867)) | Long-running Lunar forum with a "fix Dragon Song" thread; activity **unverified** |
| Lunar-Net | Historic fansite; was Ubisoft's official Dragon Song site ([ItsChocobose](https://www.youtube.com/watch?v=XnoEOkb8jWQ), [RPGFan history](https://www.rpgfan.com/feature/rpgfan-founders-roundtable/)) | Current status **unverified** (domain did not respond) |
| Lunar Fandom wiki | Exists, 403 to tools | Useful for names and terms; not a community hub |
| Steam forums for Lunar Remastered Collection | Active discussion boards ([Steam](https://steamcommunity.com/app/3255380/discussions/0/597398453436344518)) | New fans from the 2025 remaster ([Wikipedia](https://en.wikipedia.org/wiki/Lunar_Remastered_Collection)); posting about a different game there may be off-topic |
| Lunar Discord | **Not found.** Searches only turned up unrelated "Lunar" servers | Ask on r/Lunar whether one exists |

Context: the Lunar Remastered Collection (April 2025, Switch/PS4/Xbox/PC) brought renewed interest
([Wikipedia](https://en.wikipedia.org/wiki/Lunar_Remastered_Collection)). It left Dragon Song out, and Dragon Song
is "the only game in the entire series that has never been re-released or remade"
([ItsChocobose](https://www.youtube.com/watch?v=XnoEOkb8jWQ)). That gap is the hack's pitch.

## 2B. YouTube creators and videos that covered Dragon Song

Views as shown on 2026-10-06. Exact dates come from the video pages; dates marked "~" are YouTube's relative dates.

| Video | Channel | Views | Date | Why relevant |
|-------|---------|-------|------|--------------|
| [My Brief Obsession with the Worst RPG Ever Made](https://www.youtube.com/watch?v=g3ZHiycAYeQ) | i am a dot | 286,450 | 2026-04-29 | Lists the exact fixes the hack makes. Top contact |
| [The Worst RPG Ever Made.](https://www.youtube.com/watch?v=tki3wwn8QGQ) | flyann | 254,857 | 2022-03-21 | Twitch streamer with a Discord; "flyann plays and talks about the worst RPG ever made" |
| [I Played the WORST RPG Ever Made So YOU Don't Have To](https://www.youtube.com/watch?v=NxU3DSIhMWU) | Nudl | 135,502 | 2025-12-05 | Mocks the Jian intro the hack is rewriting |
| [Lunar Complete Series Retrospective](https://www.youtube.com/watch?v=4TKnNs-N7HI) | Xygor Gaming | 67,566 | 2021-07-22 | Has an "Other Lunar Games" chapter (coverage of DS **unverified**); has a Discord |
| [Lunar: Dragon Song by Highspirits (RPG Limit Break 2019)](https://www.youtube.com/watch?v=ziVKOlMmsKM) | RPG Limit Break | 40,656 | 2019-05-14 | Speedrun community; runner Highspirits |
| [The Magical Wonder of Lunar, Complete Series Retrospective](https://www.youtube.com/watch?v=eQtn1Kbef18) | Gaming Broductions | 38,472 | 2025-05-01 | Dragon Song chapter at 30:40 |
| [Lunar: Dragon Song Nintendo DS Gameplay](https://www.youtube.com/watch?v=6fJ19ZwZKEY) | IGN | 23,318 | ~2011 | Old trailer-style footage |
| [Lunar Dragon Song Review](https://www.youtube.com/watch?v=REBbVl-Gr78) | AtticusMJ | 20,644 | 2008-11-02 | Old |
| [1990s Critics Review Lunar: The Silver Star, Eternal Blue & Dragon Song](https://www.youtube.com/watch?v=MScdMh-nd6o) | Defunct Games | 8,875 | ~2024 | Retro press angle |
| [Lunar Dragon Song (NINTENDO DS) Part 1 A Terrible Game At Its Finest?](https://www.youtube.com/watch?v=nuYOnX-H7ZE) | Were1974 | 5,344 | ~2023 | Full 18-part LP |
| [Lunar Dragon Song: The JRPG That Actively Hates You](https://www.youtube.com/watch?v=yRdGXyQMZuA) | Dallah Games | 3,633 | 2025-04-18 | Self-described "huge Lunar fan" |
| [WORST JRPGs EVER #14: Lunar: Dragon Song (NDS)](https://www.youtube.com/watch?v=11PpuVM_Puo) | Erick Landon RPG | 3,101 | 2025-05-01 | JRPG channel; also covered the remaster (17.5K) |
| [Lunar Dragon Song: The Shocking Truth Behind the "Best JRPG" Ever Made! (April Fools 2025)](https://www.youtube.com/watch?v=c90_Wp-R-as) | Shinky JRPGs | 2,354 | 2025-04-01 | JRPG channel |
| [Lunar Dragon Song: Final Boss](https://www.youtube.com/watch?v=ocubmDmUfT8) | DragonmasterAlex | 1,692 | ~2023 | Lunar-themed channel |
| [Lunar Dragon Song Review](https://www.youtube.com/watch?v=WPegKR6m094) | LoneCourier2281 | 1,612 | ~2014 | Same name posts on r/Lunar ([thread](https://reddit.com/r/Lunar/comments/1krcpwi/thoughts_on_lunar_dragon_song/)) |
| [How One Bad Sequel Derailed a Classic JRPG Legacy](https://www.youtube.com/watch?v=XnoEOkb8jWQ) | ItsChocobose | 1,431 | 2026-09-25 | Eleven days old; asks if the game "deserves redemption". Natural follow-up |

Lunar-focused creators who skipped Dragon Song: The Unhinged Gamer (multi-hour Lunar 1 and 2 retrospectives;
[video](https://www.youtube.com/watch?v=dxtVbnDjFzQ)). A creator on r/Lunar said they were "really reluctant to
play it even for a pro[ject]" ([r/Lunar](https://reddit.com/r/Lunar/comments/1jov7s9/project_question/)). A fixed
version gives such creators a reason to cover it.

Written coverage: the lparchive LP by Camel Pimp (2014 to 2015) is the community's go-to reference and gets
linked in Reddit threads ([r/Lunar](https://reddit.com/r/Lunar/comments/1mcfht4/dragon_song/)).

**The "niche" concern, honestly.** The dedicated Lunar community is small (r/Lunar about 1.5k in early 2025).
Interest in Dragon Song as "the worst RPG ever made" is not: the top three videos have about 677K views between
them, two of them posted in the last 11 months. The hook that travels is "someone fixed the worst RPG",
not "a Lunar prequel hack".

## 2C. ROM hack communities and news outlets

- **Romhack Plaza** ([site](https://romhackplaza.org/)): the renamed RHDO (August 2024)
  ([Wikipedia, ROM hacking](https://en.wikipedia.org/wiki/ROM_hacking)). Time Extension's story on the Jarvas
  fix hack credits the patch's release on Romhack Plaza
  ([Time Extension](https://www.timeextension.com/news/2024/11/one-of-the-worst-famicom-action-rpgs-has-just-got-a-fanmade-overhaul)).
  Its search showed no Lunar entries, so a Dragon Song entry would be the first.
- **Romhack.ing (RHDI)** ([site](https://romhack.ing/)): successor database to romhacking.net, alpha August 2024,
  public registration March 2025 ([Wikipedia](https://en.wikipedia.org/wiki/ROM_hacking)). Submission rules **unverified**.
- **romhacking.net**: stopped taking submissions on 2024-08-01; now read-only and archived
  ([Time Extension](https://www.timeextension.com/news/2024/08/romhacking-net-is-winding-down-after-almost-20-years),
  [Shacknews](https://www.shacknews.com/article/140817/romhacking-is-shutting-down)). Its forum has a thread titled
  "DS Editing Resources for Lunar: Dragon Song" ([link](https://www.romhacking.net/forum/index.php?topic=31958.0),
  content 403, **unverified**).
- **Time Extension** covers fix-up hacks of disliked games regularly
  ([Jarvas Redux](https://www.timeextension.com/news/2024/11/one-of-the-worst-famicom-action-rpgs-has-just-got-a-fanmade-overhaul)).
  It also announced the romhacking.net and CDRomance closures
  ([CDRomance](https://www.timeextension.com/news/2024/12/fan-translation-and-rom-hack-site-cdromance-is-no-longer-being-updated)).
- **Shacknews** runs ROM hack roundups, including script and "improvement" hacks
  ([list](https://www.shacknews.com/article/142170/cool-rom-hacks-list)).
- **Retro Handhelds** (retrohandhelds.gg) covers mods for handheld players ([example](https://retrohandhelds.gg/modders-turn-canceled-gba-game-into-reality/)).
- **Indie Retro News** covered Super Pitfall 30th Anniversary ([article](https://www.indieretronews.com/2016/09/super-pitfall-30th-anniversary-edition.html)).
- **GBAtemp** returned 403 to tools. It is a long-standing DS and 3DS hacking forum, but its section names and
  rules are **unverified** here.
- **Reddit**: r/romhacking, r/NDSHacks, r/3dshacks (sizes above).
- **Technical peers:** the ds-decomp project (the hack uses its `dsd` tool, per README.md) and the melonDS and
  TWiLight Menu++ communities. A short write-up of the ITCM and secure-area work could interest them
  (**unverified** that they take such posts).

## 2D. How comparable "fix a disliked game" hacks got attention

1. **Mirai Shinwa Jarvas Redux** (Famicom, by Mentil, 2024).
   - Released on Romhack Plaza, then picked up by Time Extension under the headline "One Of The Worst Famicom
     Action RPGs Has Just Got A Fanmade Overhaul".
   - It replaced a hated mechanic (EXP-based magic) and fixed soft locks
     ([Time Extension](https://www.timeextension.com/news/2024/11/one-of-the-worst-famicom-action-rpgs-has-just-got-a-fanmade-overhaul)).
   - **What worked:** a short, concrete change list and a "worst game gets redeemed" angle. The same shape fits Dragon Song.
2. **Super Pitfall 30th Anniversary Edition** (NES, by nesrocks, 2016).
   - Fixed a notoriously bad game while keeping its layout. Covered by Indie Retro News.
   - Original designer David Crane praised it, per search summaries (**unverified**)
     ([Indie Retro News](https://www.indieretronews.com/2016/09/super-pitfall-30th-anniversary-edition.html),
     [TASVideos thread](https://tasvideos.org/Forum/Posts/439056)).
   - **What worked:** visible before/after polish, and respect for the original.
3. **FlamePurge's Phantasy Star II "Improvement" and Breath of Fire "War of the Goddess"**.
   - Localization fixes and a full script rewrite that gives characters more personality.
   - Featured in a Shacknews roundup ([Shacknews](https://www.shacknews.com/article/142170/cool-rom-hacks-list),
     [WotG page](https://imminent-aardwolf-9aa.notion.site/Breath-of-Fire-War-of-the-Goddess-08382e50603f4dde8e731f296b3fa9a9)).
   - **What worked:** a script rewrite counts as a legitimate hack, and optional toggles (such as double EXP) widen the audience.
4. **Un-Worked Designs** (Lunar SSSC, Lunar 2, Sega CD Lunar).
   - Undoes Working Designs' difficulty changes. Mirrored widely
     ([retrogametalk](https://retrogametalk.com/repo/psx-iso/lunar-silver-star-story-complete-un-working-designs-hack/),
     [CDRomance](https://cdromance.org/sega_cd_isos/lunar-the-silver-star-un-working-designs/)).
   - **What worked:** proof that Lunar fans already accept, and spread, balance-fix hacks.
5. **Mega Man Star Force DX** (DS).
   - Kept going through one long community-forum thread with versioned releases and emulator compatibility
     notes (melonDS on Android), despite little mainstream press
     ([forum](https://forums.therockmanexezone.com/mega-man-star-force-dx-t16546-s460.html)).
   - **What worked:** a single home thread and steady changelogs.
6. **Drayano's Pokemon Blaze Black / Volt White** (DS).
   - Improvement hacks aimed at a slow early game and other flaws. Among the best known DS hacks
     ([TV Tropes](https://www.tvtropes.org/pmwiki/pmwiki.php/Creator/Drayano60)).
   - **What worked:** thorough documentation of every change.
7. **Kaze Emanuar** (Super Mario 64).
   - Technical YouTube explainers about optimizing the game drew mainstream coverage
     ([Gizmodo](https://gizmodo.com/mario-64-mod-gamecube-nintendo-64-graphics-fps-framerat-1850048235),
     [eXputer](https://exputer.com/news/nintendo/modder-fix-super-mario-64-code/)).
   - **What worked:** "how I fixed it" videos reach people outside the niche.

## 2E. Should you comment on many YouTube videos?

**No, not as a campaign.** YouTube's spam policy defines comment spam as "high-volume, repetitive, or deceptive
comments ... to drive traffic to or engagement with content". Its example is "Posting identical or similar
'check out my channel' messages across hundreds of videos". Penalties include removal, warnings or strikes,
and termination after three strikes in 90 days
([YouTube policy](https://support.google.com/youtube/answer/2801973)). Beyond the policy:
- YouTube runs spam filters on comments, and creators can raise the strictness of comments held for review
  ([9to5Google](https://9to5google.com/2022/06/30/youtube-comment-spam-policies/)). A repeated comment with a
  link may simply never be shown (likely but **unverified**: YouTube does not publish what its filters catch).
- Viewers of "worst game" videos read self-promotion as an ad.
- Most of the listed videos are years old, and few people read new comments on them.

**Acceptable at small scale:** one specific, non-repetitive comment on two or three videos where it adds to the
discussion. For example, on i am a dot's video: "You listed seven fixes; a hack in progress does five of them,
here is a clip." Post only once there is something to show, ideally without a link (or as the video's
rules allow).

**Better alternatives, in order of value:**
1. **Contact creators directly.**
   - Write to i am a dot, ItsChocobose, Nudl and flyann (business email in the channel's About tab, or Bluesky
     and Twitter, both listed in their descriptions: [i am a dot](https://www.youtube.com/watch?v=g3ZHiycAYeQ),
     [ItsChocobose](https://www.youtube.com/watch?v=XnoEOkb8jWQ)).
   - Keep it to one paragraph, a 30-second before/after clip, and a link to the repo.
   - Offer a build to try, not a request for coverage.
   - Their own videos make the hook: i am a dot's fix list, ItsChocobose's "redemption" question, Nudl's jab at the Jian intro.
2. **Post progress in fan communities.**
   - One post on r/Lunar now ("fan project fixing Dragon Song: here is what changes, looking for playtesters
     and Japanese readers").
   - Then r/NDSHacks and r/romhacking when there is a patch.
   - r/JRPG and r/3dshacks at a 1.0 or a solid beta.
   - Check each subreddit's self-promotion rules first (**unverified** here). Always distribute a patch, never the ROM.
3. **A public devlog.** GitHub Discussions or Releases with short entries ("Running no longer costs HP: here is
   why and how"). This gives creators and news writers something to link.
4. **Before/after clips.**
   - Running HP drain vs. Eternal Blue style dash.
   - The targeting prompt.
   - The single reward screen.
   - Gear coming back after battle.
   - The rewritten Jian opening.

   Short, silent, captioned clips travel best on Reddit, Bluesky and in emails.
5. **Submit to Romhack Plaza and Romhack.ing at release.** Time Extension is the outlet most likely to pick it up
   from there, as with Jarvas. Pitch Time Extension directly with the "worst RPG redeemed" angle.

## 2F. Recommended outreach plan

1. **Now (pre-release):**
   - Make the repo presentable: a README "what changes" list mapped to the complaints in Part 1, and a changelog.
   - Make three or four before/after clips.
   - Post once on r/Lunar asking for playtesters and anyone who reads Japanese.
   - Read the Lunar Threads "fix Dragon Song" thread by hand and post there too.
2. **First playable patch** (running, rewards, targeting, breaking and theft verified on hardware):
   - Release it on GitHub, Romhack Plaza and Romhack.ing.
   - Post on r/NDSHacks and r/romhacking.
   - Email i am a dot and ItsChocobose first, then Nudl, flyann, Dallah Games and Erick Landon RPG.
3. **Script pass:**
   - A second wave of posts on the writing fixes (Jian intro, typos, names, the ending).
   - This is the part Lunar fans care most about, and the clearest difference from "just a cheat patch".
4. **Track** where downloads and stars come from, and stop doing what does not work.

---

## Items marked unverified

- Current r/Lunar size (only the February 2025 snapshot); existence of a Lunar Discord.
- Contents of the Lunar Threads "fix Dragon Song" thread and the romhacking.net "DS Editing Resources" thread.
- TCRF page contents.
- The exact Japanese vs English Black Dragon line (lparchive part 13).
- Japanese vowel-length difference between the two Lucias.
- Whether Xygor's retrospective covers Dragon Song.
- David Crane's praise of Super Pitfall 30th (from search summaries).
- GBAtemp section names and each subreddit's self-promotion rules.
- RPGamer review wording (only search snippets were reachable; not quoted above).
