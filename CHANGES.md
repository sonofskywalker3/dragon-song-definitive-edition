# Changes

Every change Dragon Song: Definitive Edition makes to Lunar: Dragon Song (DS, USA), grouped by area, then the
version history. How each change was built and tested is in [docs/status.md](docs/status.md); the reasons behind
the design are in [docs/design.md](docs/design.md).

## Exploring

- **Running costs no HP.** Hold B to dash for about 3 seconds, then it cools down for about 3 seconds, like the
  Eternal Blue dash. Holding B runs once; press it again to run again. The run is ready again whenever you enter
  a new area.
- **Walking is 50% faster, and running is 3 times the original walking speed.** Scripted walks in cutscenes keep
  their original speed.
- **Ramps and stairs no longer slow you down.** On a slope you used to drop to less than half speed (walking 0.65
  pixels a frame instead of 1.5 in this hack). Diagonal input still follows the slope.
- **Enemies come back when you leave an area and return**, not on a timer. The Virtue clock is gone.
- **Blue chests stay locked until every monster in the area is beaten**, at your own pace. The monster count is
  below the pocketwatch. An opened blue chest stays open.
- **No HP and MP refill for clearing an area** (the original gave back 30%).
- **Healing statues heal at once.** They fully restore HP and MP, now also cure status (poison and the like),
  and no longer pan the camera over to the statue and back.
- **Lucia is at Fountain Square** once Cherenkov tells you she left. The original only put her there after you
  had found Jack in his house, and nothing in the game points you to him.
- **The Underground Tunnel save glitch is fixed.** Talking to Flora twice there no longer locks out saving.
- **Town and world map menus work with the D-pad.** In a "Select place to go" menu, Up and Down pick a place,
  Left and Right switch tabs, and A goes there. Touch works as before, and the D-pad no longer drags the map
  icon around.

## Menus and text

- **Select opens the Save screen** straight from the field. The menu fades in on the save screen without
  passing through the other menus; B goes back to the System menu as usual. Where saving is not allowed, Select
  opens the menu as X does.
- **Select anywhere in the menu drops straight back to the map.** It is ignored only while a save is being
  written.
- **Faster menus.** Opening a screen takes 11 frames instead of 42, going back 10 instead of 41, the fades into
  and out of the menu take 10 frames instead of 30, and a held key repeats after 12 frames, then every 4 (the
  original never repeated).
- **Faster text.** Hold A to type three times as fast (press A again to turn the page), or hold B to type as fast
  and turn the pages by itself.
- **The Adventure Guidebook (Start) describes this version:** running without an HP cost, saving with Select,
  battles, battle speeds, enemies, and blue chests, in the book's own lettering.
- **"Althena Conduct" is called "Experience"** on the status screen.

## Battles

### Rewards

- **One battle mode.** The Combat / Virtue switch is gone: every battle gives experience, items, and silver.
- **Battles drop silver**, as much as the battle's experience. The victory screen counts the silver up next to the
  experience, and a second page lists the items received.
- **Bosses give experience** (in the original they gave almost none): about ten regular enemies' worth from the
  area they are fought in.
- **Characters out of the party earn the same experience as the party**, including characters who have not
  joined yet, so nobody falls behind.
- **Broken gear comes back after the battle**, and an item stolen by a thief is returned if you win.

### Targets

- **You pick targets** on the touch screen or with the D-pad, as in Lunar 1 and 2. The picker is laid out like the
  battlefield (back row on top), and its blue corners also frame the chosen enemy on the battle screen, so you
  can watch the enemies instead of the menu.
- **An attack is never wasted.** If your target dies before the hit lands, the attack moves to the next enemy.
- **Fight attacks right away when only one enemy is in reach.** Jian and Lucia only hit the front row, so in the
  first battles (one enemy in front, one flying behind) there is nothing to choose and the picker is skipped.
  With two or more enemies in reach, you pick.
- **Flying enemies drop into an empty front slot during an attack**, column by column, so Jian hits them in their
  new place instead of leaping up at them. Columns that were already empty when the action started refill after
  the action, as in the original.
- **Enemies die on the hit that kills them** (Fast and Faster). A combo that kills several enemies shows each one
  die as it falls, while the attacker moves on.

### Speed

- **Battle speed:** tap R to cycle **Fast** (the default), **Faster**, and **Normal** (the original timing).
  - Fast trims the waits: quicker moves and lunges, shorter kill flashes, damage numbers that do not hold up the
    next action, a quicker back-row refill, and faster intro and victory screens (the experience pour can always
    be skipped with A). The first temple battle takes 25 seconds on Fast, against 32 with the original game's
    own fast-forward held down and 38 without it.
  - Faster adds the original game's animation fast-forward on top.
- **Lucia, Gabryel, and Rufus attack faster** on Fast and Faster (Lucia's attack: 204 frames down to 76). Jian's
  combo is unchanged.
- **The next character no longer waits for a defeated enemy's sparkles** to finish (92 frames down to 16 between
  attackers), except after the last enemy, so the end of a battle plays as before.
- **Picking Auto switches the battle speed to Faster.** R still changes it.

### Controls

- **No microphone.** Run from a battle by holding L and R together for half a second on the command screen; the
  battle sign says L+R instead of MIC. L and R no longer fast-forward.

### Story mechanics

- **Jian's curse no longer weakens his attack** (he keeps his 3-hit combo). The story around the curse is still to
  be rewritten.

## Spells and MP

- **Spells cost about 40% of their old MP:** Healing Water 4 (was 10), Tender Rain 12 (30), Cure Squall 4 (8),
  Divine Rain 16 (40), Miracle Tears 20 (50), Escape 2 (5), Quick 8 (20), Grand Weapon 10 (24), and Grand Shell
  10 (28). Dragon Magic and Gabryel's and Rufus' skills are unchanged.
- **Lucia learns her spells by level**, not all at once when her MP grows: Healing Water at 1, Cure Squall 2,
  Escape 3, Quick 4, Tender Rain 6, Grand Weapon 7, Grand Shell 8, Divine Rain 10, and Miracle Tears 12 (she used
  to have six by level 5). Flora follows the same levels.
- **Mental Gum restores 20 MP and Mental Drop 50 MP**, instead of a small share of max MP. Mental Gum costs 1000
  silver and is sold in every item shop from the third town on; Mental Drop is still a rare reward.

## Party

- **Leaving characters leave their gear behind** in the inventory, so it is not lost with them.

## Gad's Express

- **Delivery jobs grow with your journey.** An office's rank starts at 1 and goes up by one with each new town
  you reach (not with deliveries made), and it only offers jobs whose items you can actually find by then.
- **One "future" job** among the offers, shown in red, asks for items from further ahead and pays 1.5 times as
  much.
- **Recipient names match.** Ten people had one name in the job menu and another in their own dialogue; both now
  use the name from the Japanese release.

## Story and text

- **A new opening narration**, retranslated from the Japanese release and checked against Lunar 1 and 2: the
  Dragonmaster is Althena's champion (not her servant), Althena is the source of the world's magic, and the
  Beastmen and Humans are set up as the Japanese has them, with the Beastmen in power and a peace that only holds
  while the two races keep apart.
- **A new wake-up.** Instead of Jian introducing himself to an empty room, Cherenkov shouts up the stairs to get
  him out of bed, and Jian walks out of the inn, his thoughts introducing him on the way. Each thought closes by
  itself as he reaches the next door.
- **Cherenkov's lobby line** points you to Fountain Square.
- The Y-button think-aloud no longer opens with a stray "Anyway...".

## Presentation

- **A "Definitive Edition" seal** on the title screen.

## Fixes

- A crash when an enemy was killed by a counterattack during its own attack (v0.1.3).

## Version history

### v0.1.3 (2026-10-08)

- Walking 50% faster and running 3 times as fast; no slowdown on ramps; the run is ready again in each new area.
- Healing statues heal at once, with no camera pan.
- Lucia is at Fountain Square without finding Jack first.
- Select opens the Save screen, and Select in the menu goes straight back to the map; faster menus.
- Town and world map menus work with the D-pad.
- Hold A or B for faster text; Jian's thoughts on the way out of the inn close by themselves.
- The Adventure Guidebook is rewritten; "Althena Conduct" is now "Experience".
- Flying enemies drop into empty front slots during an attack, and Jian no longer leaps up at them.
- Lucia, Gabryel, and Rufus attack faster, and the next character no longer waits for a defeated enemy's
  sparkles.
- Picking Auto switches to Faster; the top battle speed is now called Faster (it was Fastest).
- Lucia and Flora learn their spells by level.
- Fixed a crash when an enemy was killed by a counterattack during its own attack.

### v0.1.2 (2026-10-07)

- The target picker's blue corners also frame the chosen enemy on the battlefield.
- A "Definitive Edition" seal on the title screen.
- A smaller patch: changed game files are packed the way the game packs them.

### v0.1.1 (2026-10-07)

- The new opening narration, retranslated from the Japanese release.
- The reworked wake-up: Cherenkov's new lines, and Jian walks out of the inn on clean paths.
- The Y-button hint no longer opens with a stray "Anyway...".

### v0.1.0 (2026-10-06)

- First playable demo: running without an HP cost, faster walking, respawn on re-entry, blue chests that unlock
  once an area is cleared, statues that cure status, and the save glitch fixed.
- One battle mode with experience, items, and silver from every fight; boss experience; target picking;
  experience for benched characters; broken and stolen items returned; running with L+R; three battle speeds.
- Cheaper spells, flat MP items, and Mental Gum in shops.
- Gad's Express jobs that grow with the journey, a future job, and matching recipient names.

## Not changed yet

- The story and dialogue past the opening, including the curse and Gad's first package (planned next).
- Some enemy attack animations are slow (the Ice Mongrel hops forward and back four times). A pass over every
  enemy is planned.
