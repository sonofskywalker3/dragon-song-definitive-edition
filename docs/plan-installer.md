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
off, the seal is Classic's red). The rest are engine and gameplay switches, grouped as the README groups them.
Today's features are coarser than Jeff's examples, so several become two or more switches; the split is real work,
listed per feature in the table. Defaults: all on (the full release), except party chat (off, as now).

| Group | Today's feature | Switches it becomes |
|---|---|---|
| Exploring | timed-run | no HP drain while running; timed dash with cooldown (needs the first); run gauge in the pocketwatch (pocketwatch) |
| | walk-speed | walking and running 50% faster; no slowdown on ramps and stairs |
| | restock-on-entry, no-virtue-clock | enemies return on entering an area, not on a timer |
| | no-clear-refill | clearing an area no longer refills HP and MP |
| | statue-any-side | healing statues work from any side, heal faster, and cure status |
| | town-menu-dpad | D-pad in town and world map menus; B selects Leave town |
| | still-hud | the HUD stops pulsing |
| Menus and text | field-menu | Select opens Save; Select leaves the menu from any screen; faster menus |
| | text-speed | hold A for fast text; hold B for fast text and auto-advance |
| | guidebook | the guidebook explains this version's rules |
| | experience-name | Althena Conduct is called Experience |
| | text-fixes | name and typo fixes in the job menu and messages |
| Battles | one-battle-mode, silver-drops, boss-exp, result-screens | experience, items, and silver from every battle; bosses give experience |
| | manual-targeting | pick your own targets |
| | battle-speed, battle-pace, battle-flow, kill-on-hit, enemy-sprite-speed, enemy-spell-speed, enemy-quick-steps | battle speeds with R; each pacing change on its own (faster party actions, enemies die on their killing hit, faster enemy animations, shorter enemy steps) |
| | hold-lr-to-run, mic-sign | hold L and R to run instead of the microphone (the sign follows) |
| | battle-end-rules, leave-drops-gear | broken and stolen gear returned after a win; benched members gain EXP; a leaving member drops their gear |
| | no-curse-penalty, curse-no-healing | the curse rework |
| Spells and skills | mp-economy | spells cost about 40% of their MP; MP items restore a flat amount |
| | spell-levels | healers learn by level |
| | skills | level-learned skills for Jian, Gabryel, Rufus, and Flora |
| | skill-icons | Special list icons (off: the blank boxes) |
| | poison-turns | poison wears off after 2 to 4 turns |
| Cards | cards | ring and card slots; cards used from the Special list; boss card passives; Steal; drops and recharge (each a switch where the code allows: enhancements, changed cards, boss passives, card drops) |
| Fixes | fix-save-glitch | Flora's tunnel save lock fix |
| | gad-express | Gad's Express jobs grow with the journey |
| | title-seal | the title seal (always on: it says which build this is) |

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
