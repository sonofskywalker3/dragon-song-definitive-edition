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
always on (it says which build this is). Where a switch below needs a feature split, the split is real work; the
builder reports any line that cannot be separated cleanly instead of forcing it.

**Exploring (approved, Jeff, 2026-11-26)**

| # | Switch | Today's feature |
|---|---|---|
| 1 | No HP drain while running | timed-run |
| 2 | Timed dash with cooldown (needs 1) | timed-run |
| 3 | Run gauge in the pocketwatch (needs 2) | timed-run, pocketwatch |
| 4 | Walking and running 50% faster | walk-speed |
| 5 | No slowdown on ramps and stairs | walk-speed |
| 6 | Enemies return when you enter an area, not on a timer | restock-on-entry, no-virtue-clock |
| 7 | Clearing an area no longer refills HP and MP | no-clear-refill |
| 8 | Healing statues work from any side, heal faster, and cure status | statue-any-side |
| 9 | D-pad in town and world map menus | town-menu-dpad |
| 10 | B in a town menu selects Leave town | town-menu-dpad |
| 11 | The HUD stops pulsing | still-hud |

**Menus and text (12 to 19) approved, Jeff, 2026-11-26; the rest proposed, for review group by group**

| # | Group | Switch | Today's feature |
|---|---|---|---|
| 12 | Menus and text | Select opens Save | field-menu |
| 13 | | Select leaves the menu from any screen | field-menu |
| 14 | | Faster menus (shorter waits, fades, and key repeat) | field-menu |
| 15 | | Hold A for fast text | text-speed |
| 16 | | Hold B for fast text and auto-advance | text-speed |
| 17 | | The guidebook explains this version's rules | guidebook |
| 18 | | "Experience" in place of "Althena Conduct" | experience-name |
| 19 | | Name and typo fixes in the job menu and messages | text-fixes |
| 20 | Battles | Experience and items from every battle (one battle mode) | one-battle-mode |
| 21 | | Silver from battles | silver-drops |
| 22 | | Bosses give experience | boss-exp |
| 23 | | The reworked result screens | result-screens |
| 24 | | Pick your own targets | manual-targeting |
| 25 | | Battle speeds with R (and their sign) | battle-speed |
| 26 | | Faster party actions | battle-pace, battle-flow |
| 27 | | Enemies die on their killing hit | kill-on-hit |
| 28 | | Faster enemy animations | enemy-sprite-speed |
| 29 | | Faster enemy spells | enemy-spell-speed |
| 30 | | Shorter enemy steps | enemy-quick-steps |
| 31 | | Hold L and R to run instead of the microphone (the sign follows) | hold-lr-to-run, mic-sign |
| 32 | | Broken and stolen gear returned after a win | battle-end-rules |
| 33 | | Benched members gain experience | battle-end-rules |
| 34 | | A leaving member drops their gear | leave-drops-gear |
| 35 | | No curse penalty | no-curse-penalty |
| 36 | | The curse blocks healing | curse-no-healing |
| 37 | Spells and skills | Spells cost about 40% of their MP | mp-economy |
| 38 | | MP items restore a flat amount | mp-economy |
| 39 | | Healers learn spells by level | spell-levels |
| 40 | | Level-learned skills for Jian, Gabryel, Rufus, and Flora (needs 24) | skills |
| 41 | | Special list icons (off: the blank boxes) (needs 40) | skill-icons |
| 42 | | Poison wears off after 2 to 4 turns | poison-turns |
| 43 | Cards | Ring and card slots; cards used from the Special list (needs 40) | cards |
| 44 | | Cards power up matching skills (needs 43; its poison power-up needs 42) | cards (feat_card_boost, feat_skills_boost) |
| 45 | | Changed cards: Insector, Ochu, Kuntukapu 2 to 4 rounds; Hellbird, Termite on one ally; Yeti steals | cards (feat_card_changes) |
| 46 | | Boss card passives, Moran, Orcus, and Morus's Steal | cards (feat_card_bosses, steal) |
| 47 | | Card drops and recharge; boss cards always drop | cards (feat_card_drops) |
| 48 | | What each card does, on the equip page | cards (card_text) |
| 49 | | The bestiary (the System list's Bestiary plank) (needs 43) | bestiary |
| 50 | Fixes and extras | Flora's tunnel save lock fix | fix-save-glitch |
| 51 | | Gad's Express jobs grow with the journey | gad-express |
| 52 | | The intro sends Jian straight to Lucia | opening-flags |
| 53 | | Party chat on Y (default off) | party-chat |
| 54 | Story | Retold: text edits, the walk-out opening and narration, the blue seal (needs 15 or 16 and 52, as the opening needs text-speed and opening-flags today) | text-edits, opening-run, opening-text, title-seal-retold |

## 4. Dependencies

From `features.REQUIRES` (build order) and what each change needs to make sense:
- skills needs manual-targeting; cards needs skills; skill-icons needs skills.
- The timed dash needs no HP drain; the run gauge needs the timed dash.
- Card enhancement of poison (10% a turn) needs poison-turns (Jeff: no whole-battle poison at 10%).
- The opening's walk-out needs text-speed and opening-flags.
- In the window a switch whose need is off is greyed out with the reason; switching a need off switches its
  dependents off.

## 5. Questions for Jeff, one at a time

1. Platform and license (section 2).
2. The switch list (section 3): which splits matter enough to build before the release.
3. Where it ships: GitHub releases beside the two patches, and the README's "Which patch to pick".
