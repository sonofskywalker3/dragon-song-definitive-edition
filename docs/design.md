# Design

Decided 2026-10-05.

## Guiding rule

Play outside of battle should feel like Lunar 1 and 2 (Silver Star Story Complete and Eternal Blue Complete).
Every change to systems outside of battle is judged against that.

The battle system itself stays non-positional. It was different from Lunar 1 and 2 on purpose, and that is fine.

## 1. Running

- Running no longer costs HP.
- It copies the Eternal Blue Complete (PS1) dash: you run for a short time, then drop back to walking,
  and running is unavailable for a short cooldown. No visible stamina bar.
- Reviews put both times at about 3 seconds. Measure the real timings from Eternal Blue Complete and copy them.
- Watch in playtesting: Eternal Blue was criticized because enemies never tire, so they were hard to dodge.
  Dragon Song also shows enemies on the map. Start with the exact Eternal Blue timings and tune from there.

## 2. Battle rewards and area clearing

- One mode. The Combat/Virtue switch is removed.
- Every battle gives EXP (Althena Conduct), items and silver.
- The Virtue mode clock is removed.
- Enemies respawn when you leave an area and come back, not instantly.
- The HP/MP recovery for clearing an area is removed.
- Blue chests stay locked until every enemy in the area is beaten, at your own pace.
- Bosses give EXP (in the original they give none, and their EXP values are 1 to 10 placeholders). Starting
  value: about ten regular enemies' worth at the boss's level, tuned in playtesting. "Regular" means the
  regular enemies of the place the boss is fought in; per-boss numbers in docs/boss-exp.md.
- EXP amounts for regular enemies stay unchanged to start. Enemies reportedly scale with the party's level, so faster leveling
  should not break the balance. Item drops are the bigger balance risk; trim them only if playtesting says so.

## 3. Money

- Battles drop silver. Each enemy's silver is based on its EXP value, tuned in playtesting.
- Gad's Express delivery jobs stay as they are, now optional extra income.

## 4. Targeting

- The player picks the target of each attack on the touch screen, like Lunar 1 and 2.
- If the chosen enemy is already dead when the attack happens, the attack moves to the next enemy in the list.
  An attack is never wasted.

## 5. Party

- Free swapping of who is in the three party slots. Swapping only near the end of the game is the fallback if
  the story cannot handle free swapping.
- Characters out of the party (benched, or away in the story) earn the same EXP as the party. Leveling never
  asks for a choice, so this is safe. Needed because the game does not scale anyone up on rejoining: a
  character comes back at the level they left with.
- Party members knocked out at the end of a battle still earn nothing, as in the original.
- Since the story never has more than 3 characters available at once, free swapping only matters if the story
  changes. Build the benched EXP first; revisit swapping with the story work.
- Characters the story requires are locked in. Characters who die in the story stay gone.
- Characters who leave in the story come back by talking to them in a hub city, at a point that makes sense.
  This is new map content and new dialogue in each character's voice.
- Stat buffs for Lucia, Gabryel, Flora and Rufus are on hold until targeting and swapping have been played.

## 6. Gear breaking and stealing

- Breaking: enemies can still break a piece of gear, but only for the rest of that battle. It comes back when
  the battle ends. The battle cards that block breaking stay useful.
- Stealing: kill the thief and you get the item back. If the thief escapes, or the party runs from the battle,
  the item is gone. No special protection for unique items for now.
- Saving is already allowed anywhere (menu, System, Save), which softens losing an item to a thief.

## 7. Battle controls and pacing

Decided 2026-10-06.

- No microphone. Running from battle is holding L and R together (half a second) on the command screen;
  L and R are for running only, so the game's hold-L/R fast-forward is gone. Any tutorial or on-screen
  hint must say L+R is for running. The battle screen's wooden "MIC" sign is redrawn to say "L+R",
  keeping the running man and the original lettering style.
- Battles should run smoother and faster by default, so that no speed button is needed. If a speed control
  is still needed after playtesting, it is a full battle speed setting like the 2025 Lunar remasters (three
  speeds, battle only), cycled by tapping R alone (L+R stays the run chord). Analysis: docs/re-battle-pacing.md.
- Victory screen: the Silver line counts up like the EXP does.

## 8. MP and spells

Decided 2026-10-06.

- Spell unlocking is uncoupled from MP cost: each spell unlocks at the level it unlocks at today, so MP
  costs and MP growth can then be tuned freely for balance.
- Healing statues also cure status.
- Mental Gum is sold in shops but expensive (Jeff's reference: priced like Lunar's Starlight), so it stays a
  convenience or emergency item and makes delivery jobs more attractive. Old Lunar games were sparing with
  MP recovery items, and backtracking to a statue to keep a grind going is normal; the current scarcity is
  excessive, not the idea.
- Built 2026-10-06: spell costs about 40% of vanilla (Healing Water 4, Tender Rain 12, Cure Squall 4, Divine Rain 16,
  Miracle Tears 20, Escape 2, Quick 8, Grand Weapon 10, Grand Shell 10); Dragon Magic and Gabryel's and Rufus's
  spells stay at 10. MP growth is unchanged; if it is tuned later, unlocks move to a precomputed level table.
- Mental Gum restores a flat 20 MP and Mental Drop a flat 50 (were 20% and 50% of max); the all-allies MP card keeps
  its percentage. Mental Gum costs 1000 and is sold in the item shop from the third town (San Coliseum) on;
  Mental Drop stays boss-only.

## 9. Gad's Express

Decided 2026-10-06.

- Fix the recipient names that differ between the job menu and the NPC's own dialogue.
- Keep the quit fee (a free quit would be a free reroll of the offered jobs).
- Do not change which items jobs ask for.
- Tie the job pool's growth to places visited or story points instead of deliveries made.
- Rule (decided 2026-10-06): every office's rank starts at 1 and rises by 1 for each new town, up to 4. A town counts
  once its main map has been entered (the game's own destination unlocks, func_02041d38); play starts with 2 (Port
  Searis and Perit), so rank = towns - 1. Rank still sets the fee and quit fee.
- Each office offers up to 3 jobs whose items can all be had by now (sold in a visited town's shop, or dropped in an
  area reachable by then), plus at most one "future" job that cannot be completed yet, paying 1.5 times its fee.
  The player can take the future job for extra money and finish it later. Its title is red in the job list (harder). "Can be had by now" comes from a
  build-time table: each template's earliest town count.

## 10. Dragon rings

Decided 2026-10-06, to build when playtesting reaches the dragons.

- As in Lunar 1 and 2, every character can use the dragon rings.
- Each character gets a separate ring slot, so a ring does not cost the accessory slot.
- A ring's spell is castable by whoever wears that ring; the spells leave Jian's list when he is not
  wearing the ring.

## 11. Jian's curse

Decided 2026-10-06 (dialogue to be written). The curse goes, and so does Zethos's blast at the end of the
San Coliseum. The story never explains why Zethos cursed Jian, and the curse only lifts because Zethos
casts the cure on him mid-fight.

Gabryel's new reason to join: she acts like an impressed fan (a groupie) of the human who won the
tournament and wants to see him take on a bigger challenge: the Beast King is challenging anyone who will
fight him, to test their strength, with a reward. She flirts enough to set up romantic tension with Lucia.
At Zethos Castle the reveal stays: he is her father, and the challenge was a ploy for the real offer
(recruiting fighters for the Frontier against the Vile Tribe).

Why it fits the existing story: Zethos is already known to be coming to watch the tournament and watches
Jian win; Gabryel's first line about Jian is "This is the human who fought so bravely in the Coliseum?";
Zethos says "I can see where your initial interest in these two must have come from, Gabryel"; a priest at
the Cathedral calls her "My lady"; Leephon City already has Zethos posters (could become the challenge).

To change: the Coliseum aftermath (script 005), Carmen in Port Olbeage (007), at Zethos Castle (009)
Lucia's demand, Jian's "why did you do it", "cursed knight", the post-fight curse lines and "You look all
better now"; the Zethos fight keeps its HP floor and the round-3 "real hit" (no curse text in battle; only Jian's attack
ignores the curse, `no-curse-penalty`). Check that the Cathedral detour still has its reason. Story details: docs/re-curse-battle-speed.md
part 1.
