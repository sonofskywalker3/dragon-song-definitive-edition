# Two editions: Classic and Retold

Named Engine and Story until 2026-10-09 (the v0.1.6 day); Jeff renamed them Classic and Retold.

Jeff (2026-10-09): "I can't assume no one liked the story, so forcing my take on them to play the game with a
better engine is wrong. We need to make 2 versions: one with only the engine changes, the other with the
story/dialog changes."

Every change in this hack is a feature in `src/dsde/features.py`, so an edition is a feature list and a
patch file. Two lists, two `.bps` files per release:

- **Classic edition** (`Dragon Song Definitive Edition vX.Y.Z (Classic).bps`): mechanics, pacing, interface,
  and bug fixes. The vanilla story, dialogue, and gates stay as the original wrote them.
- **Retold edition** (`... (Retold).bps`): the Classic edition plus the rewrite: party chat, the character
  work in docs/story-bible.md, the curse rework below, the fluff cuts, and the new ending.

## Feature split (as built 2026-10-09; the curse row is still being built)

| Feature | Edition | Note |
|---|---|---|
| timed-run, pocketwatch, walk-speed, no-virtue-clock, restock-on-entry, no-clear-refill, fix-save-glitch, statue-any-side | Classic | field mechanics and fixes |
| one-battle-mode, silver-drops, boss-exp, result-screens, battle-end-rules, leave-drops-gear, hold-lr-to-run, mic-sign | Classic | battle rules and rewards |
| manual-targeting and its sub-features, battle-speed, battle-pace, kill-on-hit, battle-flow, enemy-sprite-speed, enemy-spell-speed, enemy-quick-steps, enemy-preload (if adopted) | Classic | battle pacing and control |
| mp-economy, spell-levels, gad-express | Classic | balance; Gad's job logic, not his dialogue |
| field-menu, town-menu-dpad, town-brackets, still-hud, text-speed, title-seal, guidebook, experience-name | Classic | interface; the guidebook describes whichever edition it is built into (needs an edition-aware page) |
| text-fixes: recipient name tags matched to the job menu (Balam, Gobbi, Tartaglia, Laban, Devida) | Classic | fixes, not story: only the speaker tag over a line changes |
| **curse rework** (below) | **Both** | Jeff, 2026-10-09: "both versions will say he's cursed going forward." It replaces no-curse-penalty in both editions. Only the Retold edition changes any curse wording |
| **opening-run**: the vanilla wake-up and self-introduction, then Jian walks out of the inn, the story flags set so Cherenkov and Jack are optional | Retold | Jeff, 2026-10-09 (final): "the engine shouldn't walk out on the engine brand, it should be a fully vanilla intro, no code changes other than the faster text when you hold the button." The Classic intro is vanilla, BUT the story flags are still set (feature opening-flags) so Lucia waits at the fountain without the Cherenkov -> Jack chain (Jeff: "keep the flags that let me go straight to Lucia even on Classic"); text-speed is the only other change |
| **opening-flags**: the vanilla intro unchanged; after "Right then!" closes, flags 0xC (Lucia left) and 0xD (Lucia at the fountain) are set, so Lucia waits at Fountain Square without the Cherenkov -> Jack chain; Cherenkov and Jack say their vanilla lines for that state | Classic | Jeff, 2026-10-09: "keep the flags that let me go straight to Lucia even on Classic." opening-run builds on it in Retold |
| **opening-text**: Cherenkov's wake-up call, Jian's asides on the walk, Cherenkov's lobby line; **text-edits**: the rewritten opening narration and the "Anyway..." cut; **title-seal-retold** | Retold | the Classic edition changes no wording in dialogue or narration |
| UI labels that describe changed mechanics: guidebook, mic-sign ("L+R"), experience-name | Classic | the engine makes no sense without them; Jeff may veto |
| party-chat and every line in party_chat_lines.py | Retold | not in RETOLD_FEATURES yet: off by default while Jeff writes the lines (`--with party-chat`) |
| curse rework (below), fluff-gate cuts, Ignatius fight, new ending, all bible work | Retold | |

## Classification of the opening and text patches

Every patch in feat_opening.py, feat_opening_asides.py, and feat_text.py, read one by one. Rule: a patch that
changes what a line of dialogue or narration says is Retold; mechanics, flags, timing, and name-tag fixes are
Classic. Mixed features were split.

| Patch (script 001 unless noted) | Was in | Now in | Why |
|---|---|---|---|
| Recipient speaker tags: Bram -> Balam (001), Gobi -> Gobbi (004), Tartallia -> Tartaglia (005), Raiban -> Laban (007), Davida -> Devida (011); 19 messages | text-edits | text-fixes (Classic) | a name fix: the tag now matches the job menu; no line says anything different |
| Y-hint "Anyway..." cut (018) | text-edits | text-edits (Retold) | removes words from what Jian says: a wording change |
| Opening narration rewrite (026) | text-edits | text-edits (Retold) | wording |
| The messages text-fixes moves to the end of 001, written again so the layout holds | opening-run | opening-run (Retold) | same bytes as text-fixes (Balam) |
| Walk out of the inn: room, hall, and lobby legs, the map-entry block for 160 and 155, RUN_FLAG 0x1DF | opening-run | opening-run (Retold) | movement; each leg has an empty aside slot |
| Flags 0x1, 0x1E2, 0xC (Lucia left), 0xD (Lucia at the fountain) set on the walk | opening-run | opening-run (Retold) | Jeff: "do go ahead and set the flags" |
| Flags 0xC and 0xD set over the vanilla stop and the dead goto_map at 0x63C4..0x63CF (set, set, stop) | (new) | opening-flags (Classic) | flags only, no map reload, no walk |
| Fountain Square (164) entry checks 0xC instead of 0xD (0x56E8) | opening-run | opening-run (Retold) | a flag check |
| Asides close by themselves when the walk ends (cave_aside_autoclose; text-speed calls it) | opening-run | text-speed (both) | timing, no text; with no aside up it never fires |
| Field bottom screen restored at the start of the walk (op `32 0001 0001`, docs/re-opening.md) | (new) | opening-run (Retold) | closes the "Right then!" box and brings the HUD back, so the HUD shows during the whole walk as in normal play |
| Jump at 0x63C4 (after "Right then! I'd better go looking for Lucia...") to the walk, over opening-flags' first two ops | (new) | opening-run (Retold) | the vanilla wake-up plays as written, then the walk |
| Wake-up jump at 0x62CC to Cherenkov's call, Jian's replies, the vanilla waking pose | opening-run | opening-text (Retold) | new dialogue; skips the self-introduction |
| The three asides on the walk ("I'm Jian. I'm a courier...") | opening-run | opening-text (Retold) | new text; not vanilla (they replace the self-introduction), so not in the Classic edition at all |
| Cherenkov's three lobby lines -> "Jian, what are you doing?! Get to Fountain Square!..." | opening-run | opening-text (Retold) | wording; in the Classic edition he says his vanilla line for the flags (0x0CA9, "Get over to the Fountain Square, on the double!") |
| The restore op replaced by a jump | (new) | opening-text (Retold) | the room aside's box replaces "Right then!" |
| Title seal: red, CLASSIC | title-seal | title-seal (Classic) | which build a screenshot is from |
| Title seal: blue, RETOLD | (new) | title-seal-retold (Retold) | repaints title-seal's palette and tiles |

Jeff, 2026-10-09 (final): the Classic opening is fully vanilla, so opening-run moved to the Retold edition with
opening-text; the rows above say where each patch now lives. Then (same day) Jeff: "I told you to keep the flags
that let me go straight to Lucia even on Classic", so opening-flags sets them in Classic. opening-run (after
opening-flags and text-speed), opening-text, and title-seal-retold patch bytes that opening-flags, opening-run, and
title-seal write, so `dsde.patches` refuses a
list that has them without, or before, those (`REQUIRES` in features.py).

## Feature lists and commands

- `CLASSIC_FEATURES` (features.py; `DEFAULT_FEATURES` and the old name `CLASSIC_FEATURES` are the same list):
  timed-run, one-battle-mode, no-virtue-clock, restock-on-entry, no-clear-refill, fix-save-glitch, silver-drops,
  boss-exp, result-screens, battle-end-rules, manual-targeting, text-fixes, hold-lr-to-run, leave-drops-gear,
  battle-speed, no-curse-penalty, curse-no-healing, battle-pace, kill-on-hit, battle-flow, mp-economy,
  spell-levels, walk-speed, gad-express, mic-sign, text-speed, opening-flags, experience-name, title-seal, town-menu-dpad,
  field-menu, guidebook, still-hud, statue-any-side, pocketwatch, enemy-sprite-speed, enemy-spell-speed,
  enemy-quick-steps.
- `RETOLD_FEATURES = CLASSIC_FEATURES +` text-edits, opening-run, opening-text, title-seal-retold (old name
  `RETOLD_FEATURES`).

```
uv run python -m dsde.patches                          # Classic edition -> build/dsde.nds
uv run python -m dsde.patches --edition retold         # Retold edition -> build/dsde-retold.nds
uv run python -m dsde.patches --edition retold --with party-chat --output build/x.nds
uv run python -m dsde.bps release "rom/Lunar - Dragon Song (USA).nds" 0.1.6
    # -> build/release/Dragon Song Definitive Edition v0.1.6 (Classic).bps and (Retold).bps, SHA-1s logged
uv run python -m dsde.edition_check build/release/dsde-classic_extract/files/script.dat --classic
    # lists every changed script message; fails unless each is a text-fixes rename
```

`--edition classic|retold` and `edition_check --engine` still work for one release (old names; patches logs a
warning).

Checked 2026-10-09 after the rename (builds in build/editions/): the Classic build changes 19 script messages,
every one a recipient name tag (build/editions/classic_script_diff.txt); the Retold build adds the narration,
the wake-up, the asides, Cherenkov's line, and the Anyway cut (retold_script_diff.txt, 32 changed messages).
Title screens: build/editions/classic_0_title.png (red seal, CLASSIC) and retold_0_title.png (blue seal,
RETOLD); the field from the start save: classic_6_boot_from_save.png, retold_6_boot_from_save.png
(emu/plans/diag_title.plan, editions_boot.plan). The opening walk (now Retold only) was checked before the
rename: New Game (editions_opening.plan) shows the vanilla narration, self-introduction, and "Right then!" then
the walk with the HUD on the bottom screen when opening-run is built without opening-text; with the walk's flags
Cherenkov says his vanilla "Get over to the Fountain Square, on the double!" and Jack his vanilla "I just saw
Lucia in Fountain Square. I thought she was waiting for you...?" (editions_npcs.plan, editions_jack.plan).

Classic opening-flags, checked 2026-10-09 (emu/plans/editions_classic_lucia.plan, then editions_classic_npcs.plan
with the same --out): New Game, the vanilla intro to "Right then!" and control in Jian's room
(build/editions/classic_1_control_after_intro.png); pin-warped to Fountain Square, Lucia's object 0xC8 is active
(+0x14 = 1; 0xFF on the vanilla ROM at the same point) and talking at her spot plays the vanilla parasol scene
("Hey... This is Lucia's parasol...", classic_2_fountain_lucia_scene.png; vanilla: nothing,
vanilla_2_fountain_no_scene.png). Cherenkov says his vanilla "Get over to the Fountain Square, on the double!"
(classic_3_cherenkov.png) and Jack his vanilla "I just saw Lucia in Fountain Square. I thought she was waiting for
you...?" (classic_4_jack.png). The camera does not follow the plan's warps (black or blue patches on the top
screen).

Still open: the guidebook describes the same mechanics in both editions (no edition-aware page yet);
party-chat goes into RETOLD_FEATURES when its lines are written.

## The curse in both editions (Jeff, 2026-10-09)

The curse stays in both editions, made "annoying enough to prioritize removing it, but not so annoying that it
becomes the most memorable part of the game for the wrong reasons." Battles stop taking three times as long;
the player may have to run from some encounters and come back for blue chests. **Must be playtested** (healing
only at statues has to be a viable route from the San Coliseum to Zethos). Wording: the Classic edition keeps
every vanilla curse line, including "The Curse of Lost Equilibrium has been broken!"; only the Retold edition
rewrites them.

- **What it does:** Jian cannot be healed except by the Goddess's power, at healing statues. Items and
  healing spells do not restore his HP while he is cursed. He keeps his full attack (vanilla takes his
  3-hit combo away; that penalty is gone in both editions if no-curse-penalty stays on).
- **Why it still matters:** annoying enough that no beastman army would recruit him, which is Zethos's
  reason for cursing him in the first place (009 #13: to stop Gabryel recruiting a human).
- **How it breaks:** in the Zethos fight, on round 3 (the round the vanilla AI already switches to the
  curse-clearing skill, func_020695c0 case 6), the flash, and Jian can use items again from that turn. In
  the Retold edition Zethos first says something like "I may have been wrong about you. Let's make this a
  fair fight"; the Classic edition keeps the vanilla lines.
- **Engine pieces:** the curse flag (battle ctx +0x5C, story 0x33 and not 0x79) and its readers are mapped in
  docs/re-curse-battle-speed.md part 1; the healing block is a new check in the item-use and spell-target
  paths for Jian while the flag holds (and the field menu's item use on him); the round-3 line is a battle
  message before the existing skill; the existing "The Curse of Lost Equilibrium has been broken!" line
  (009 0x23C9) is rewritten to match.

## Release mechanics

- `dsde.patches` gets `--edition classic|retold` (two feature lists in features.py: `CLASSIC_FEATURES` and
  `RETOLD_FEATURES = CLASSIC_FEATURES + the rewrite`), and the release step produces both `.bps` files with their
  SHA-1s in the notes.
- The title seal should say which edition it is (so bug reports say which build).
- Saves: both editions must load each other's saves and the original's; story flags used by party chat and
  choices (0x244..0x25F and the read-flag pool) are harmless in the Classic edition because nothing reads
  them there.
