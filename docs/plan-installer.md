# Plan: the custom installer (design for approval, 2026-11-26)

Approved build list point 8 (docs/plan-cards.md 8): a third download beside the Classic and Retold patches that
builds a patch from a list of switches. The story is one switch (all or none); every engine and gameplay change is
its own switch, as fine as Jeff's examples (HP drain while running; B in a town menu selecting Leave town);
dependencies switch on or grey out; the defaults equal the full release. Jeff hopes it replaces the two edition
patches in time. Nothing here is built.

**Decided (Jeff, 2026-11-26): the linker route, and the project is MIT licensed** (LICENSE added). Keystone stays
a build tool on our side only; the installer ships no Keystone, so nothing in it is GPL. Questions 2 and 3 in
section 5 are still open.

## 1. Why the installer has to build, not combine

A patch cannot be cut into one piece per switch. The new code lives in one shared space (the ITCM cave), and each
piece's address depends on which other pieces are in; many pieces call each other or patch the same game code; the
data files (menus, icons, text) are compressed archives rebuilt as a whole. So the installer has to do what
`dsde.patches` does: lay out the chosen code, assemble it, patch the user's ROM, and rebuild it. Precomputing every
combination is out of the question with about 60 switches.

## 2. Platform: options

| | Windows app | Web page | Linker (Windows app or web page) |
|---|---|---|---|
| What it is | the existing Python build, bundled as one .exe (PyInstaller) with dsd.exe; a window with the switches | the same build run in the browser | we assemble each piece ahead of time with its address references marked; the installer only places the pieces, fills in the addresses, and patches |
| Work | small: a switch window and packaging | large: Python, Keystone, dsd, and Pillow in WebAssembly | medium: a relocation format, a small linker, and our own archive rebuild in place of dsd's |
| Runs on | Windows (Mac and Linux later, the same way) | anything with a browser | either |
| Licenses | bundles Keystone (GPL-2.0): the .exe must be offered under the GPL, with its source | bundles Keystone the same way | ships no Keystone: no GPL constraint |

- The repository has **no license file today**, so the GPL point needs a decision either way: release the
  installer (or the whole project) under the GPL, or take the linker route.
- dsd (ds-decomp) is MIT: bundling it needs only its notice.
- The output is a patched `.nds` from the player's own ROM (checked by SHA-1, as the README asks), plus an
  optional `.bps` of their choice so they can share settings without sharing a ROM.

## 3. The switches

The story is one switch: Retold's text edits, the walk-out opening and its narration, and the blue seal (with it
off, the seal is Classic's red). Everything else is engine and gameplay, one switch per change Jeff can name, built
into both editions alike. Defaults: all on (the full release), except party chat (off, as now). The title seal is
always on (it says which build this is), and so is the save glitch fix (fix-save-glitch: talking to Flora in the
Underground Tunnel after she leaves no longer locks Save for the rest of the game; Jeff, 2026-11-26: "just fix it"). Where a switch below needs a feature split, the split is real work; the
builder reports any line that cannot be separated cleanly instead of forcing it.

**Exploring (approved, Jeff, 2026-11-26)**

| # | Switch | Feature |
|---|---|---|
| 1 | No HP drain while running | no-run-hp-cost |
| 2 | Timed dash with cooldown (needs 1) | timed-run (needs 1) |
| 3 | Run gauge in the pocketwatch (needs 2) | pocketwatch (needs 2 and 6) |
| 4 | Walking and running 50% faster | walk-speed |
| 5 | No slowdown on ramps and stairs | no-ramp-slowdown |
| 6 | Enemies return when you enter an area, not on a timer | restock-on-entry, no-virtue-clock |
| 7 | Clearing an area no longer refills HP and MP | no-clear-refill |
| 8 | Healing statues work from any side, heal faster, and cure status | statue-any-side (with the cure and the camera from mp-economy) |
| 9 | D-pad in town and world map menus | town-menu-dpad |
| 10 | B in a town menu selects Leave town | town-menu-leave |
| 11 | The HUD stops pulsing | still-hud |

**Menus and text (12 to 19), Battles (20 to 36), Spells and skills (37 to 42), and Cards (43 to 45), Fixes and extras (46, 47), and the Retold story (48): every switch approved, Jeff, 2026-11-26; the rest proposed, for review group by group. Every switch gets a tooltip saying exactly what it does (Jeff).**

| # | Group | Switch | Feature |
|---|---|---|---|
| 12 | Menus and text | Select opens Save | menu-select-save |
| 13 | | Select leaves the menu from any screen | menu-select-exit |
| 14 | | Faster menus (shorter waits, fades, and key repeat) | menu-speed |
| 15 | | Hold A for fast text | text-hold-a |
| 16 | | Hold B for fast text and auto-advance | text-hold-b |
| 17 | | The guidebook explains this version's rules | guidebook (each rewritten page with its own switch) |
| 18 | | "Experience" in place of "Althena Conduct" | experience-name |
| 19 | | Name and typo fixes in the job menu and messages | text-fixes |
| 20 | Battles | Experience and items from every battle (one battle mode) | one-battle-mode |
| 21 | | Silver from battles | silver-drops |
| 22 | | Bosses give experience | boss-exp |
| 23 | | The reworked result screens | result-screens (the Silver line only with 21) |
| 24 | | Pick your own targets | manual-targeting |
| 25 | | Battle speeds with R (and their sign) | battle-speed |
| 26 | | Faster party actions | battle-pace, battle-flow |
| 27 | | Enemies die on their killing hit | kill-on-hit |
| 28 | | Faster enemy animations | enemy-sprite-speed |
| 29 | | Faster enemy spells | enemy-spell-speed |
| 30 | | Shorter enemy steps | enemy-quick-steps |
| 31 | | Hold L and R to run instead of the microphone (the sign follows) | hold-lr-to-run, mic-sign |
| 32 | | Broken and stolen gear returned after a win | gear-return |
| 33 | | Benched members gain experience | benched-exp |
| 34 | | A leaving member drops their gear | leave-drops-gear |
| 35 | | No curse penalty | no-curse-penalty |
| 36 | | Curse restricts healing (tooltip: while cursed, items don't heal Jian and healing magic heals him less; statues and revives still work) | curse-no-healing |
| 37 | Spells and skills | Spells cost about 40% of their MP | spell-costs |
| 38 | | MP items restore a flat amount | mp-items (with Mental Gum in shops) |
| 39 | | Healers learn spells by level | spell-levels |
| 40 | | Level-learned skills for Jian, Gabryel, Rufus, and Flora (needs 24) | skills (needs 24) |
| 41 | | Special list icons for every spell and skill (off: the blank boxes). Needs nothing: the icons are data; only the card entry's icon hook needs 43, and the build's REQUIRES entry naming skills goes | skill-icons |
| 42 | | Poison wears off after 2 to 4 turns | poison-turns |
| 43 | Cards | Dragon ring slot: a ring slot for every member, and a ring's Dragon Magic for whoever wears it | ring-slot |
| 44 | | Card system overhaul (tooltip, short: equip monster cards to use them in battle or power up skills; they recharge as you fight). The card slot, cards used from the Special list, power-ups, changed cards, boss passives and Morus's Steal, drops and recharge, and what each card does on the equip page; one switch (Jeff, 2026-11-26: too granular otherwise; nobody wants to equip a card without its text). Needs 40 | cards (needs 40 and 42) |
| 45 | | The bestiary (the System list's Bestiary plank) (needs 44) | bestiary (needs 44) |
| 46 | Fixes and extras | Gad's Express jobs grow with the journey | gad-express |
| 47 | | Retold party chat on Y (default off; the original game's think-aloud is party chat too, so the name says which) | party-chat |
| 48 | Story | Retold story: text edits, the intro sending Jian straight to Lucia (opening-flags; Jeff, 2026-11-26: it changes the story path, so Retold only, and the Classic build drops it), the walk-out opening and narration, the blue seal (needs 15 or 16, as the opening needs text-speed today) | text-edits, opening-flags, opening-run, opening-text, title-seal-retold |

**The Retold story switch's details panel** (approved, Jeff, 2026-11-26; in Jeff's voice, and the same paragraph goes
in the README's Story section; update it as the rewrite grows):

> **Retold story**
> I'm rewriting the game's dialogue to be truer to Lunar: The Silver Star and Lunar 2: Eternal Blue, the canon this
> story leads into. The rewrite rests on research into every earlier script of both games and the original Japanese
> of each, Dragon Song's included. It has only just begun: so far, a new opening narration retranslated from the
> Japanese and a new wake-up scene. More arrives with each release.
> Off: the original English dialogue, word for word.

**Found in the code (step 1 of the build, 2026-11-26).** The Feature column above is the split being built. What the
code showed beyond the approved list, and what was done:
- 3 needs 6: the watch hand's code replaces the Virtue clock's tick, so with the gauge on and 6 off, enemies would
  come back neither on a timer nor on entry.
- 8 takes the statues' status cure and the dropped camera pan, which lived in mp-economy; Mental Gum at 1000 in
  shops goes with 38.
- 23's Silver line reads 21's amount: the line is built only when 21 is on.
- 26 to 30 read 25's speed setting, and 26's no wait for the sparkles reads 27's death timers: both live in a
  small shared piece built with any of 25 to 30. With 25 off the setting stays at Fast.
- 17's pages each follow their own switch, so the guidebook never describes a rule that is off.
- 44 needs 42 (section 4: no whole-battle poison at 10%).
- 48 no longer needs 15 or 16: the opening's aside check gets its own hook when both are off.
- Hooks two or three switches share (12 to 14; 15, 16, and the opening; 32 and 33; 43 and 44) are built in one
  version per mix of those switches (`patching.Glue`, `features.GLUE`).

## 4. Dependencies

From `features.REQUIRES` (build order) and what each change needs to make sense:
- skills needs manual-targeting; cards needs skills; skill-icons needs nothing (its card hook is built only with
  cards).
- The timed dash needs no HP drain; the run gauge needs the timed dash and enemies returning on entry (6).
- Card enhancement of poison (10% a turn) needs poison-turns (Jeff: no whole-battle poison at 10%).
- The opening's walk-out needs opening-flags.
- In the window a switch whose need is off is greyed out with the reason; switching a need off switches its
  dependents off.

## 5. Questions for Jeff, one at a time

1. Platform and license (section 2).
2. The switch list (section 3): which splits matter enough to build before the release.
3. Where it ships: GitHub releases beside the two patches, and the README's "Which patch to pick".
