# Two editions: Engine and Story

Jeff (2026-10-09): "I can't assume no one liked the story, so forcing my take on them to play the game with a
better engine is wrong. We need to make 2 versions: one with only the engine changes, the other with the
story/dialog changes."

Every change in this hack is a feature in `src/dsde/features.py`, so an edition is a feature list and a
patch file. Two lists, two `.bps` files per release:

- **Engine edition** (`Dragon Song Definitive Edition vX.Y.Z (Engine).bps`): mechanics, pacing, interface,
  and bug fixes. The vanilla story, dialogue, and gates stay as the original wrote them.
- **Story edition** (`... (Story).bps`): the Engine edition plus the rewrite: party chat, the character
  work in docs/story-bible.md, the curse rework below, the fluff cuts, and the new ending.

## Feature split (as built 2026-10-09; the curse row is still being built)

| Feature | Edition | Note |
|---|---|---|
| timed-run, pocketwatch, walk-speed, no-virtue-clock, restock-on-entry, no-clear-refill, fix-save-glitch, statue-any-side | Engine | field mechanics and fixes |
| one-battle-mode, silver-drops, boss-exp, result-screens, battle-end-rules, leave-drops-gear, hold-lr-to-run, mic-sign | Engine | battle rules and rewards |
| manual-targeting and its sub-features, battle-speed, battle-pace, kill-on-hit, battle-flow, enemy-sprite-speed, enemy-spell-speed, enemy-quick-steps, enemy-preload (if adopted) | Engine | battle pacing and control |
| mp-economy, spell-levels, gad-express | Engine | balance; Gad's job logic, not his dialogue |
| field-menu, town-menu-dpad, town-brackets, still-hud, text-speed, title-seal, guidebook, experience-name | Engine | interface; the guidebook describes whichever edition it is built into (needs an edition-aware page) |
| text-fixes: recipient name tags matched to the job menu (Balam, Gobbi, Tartaglia, Laban, Devida) | Engine | fixes, not story: only the speaker tag over a line changes |
| **curse rework** (below) | **Both** | Jeff, 2026-10-09: "both versions will say he's cursed going forward." It replaces no-curse-penalty in both editions. Only the Story edition changes any curse wording |
| **opening-run**: the vanilla wake-up and self-introduction, then Jian walks out of the inn, the story flags set so Cherenkov and Jack are optional (they can still be talked to) | Engine | Jeff: "leave out anything that changes any wording, let them walk out of the room, but do go ahead and set the flags" |
| **opening-text**: Cherenkov's wake-up call, Jian's asides on the walk, Cherenkov's lobby line; **text-edits**: the rewritten opening narration and the "Anyway..." cut; **title-seal-story** | Story | the Engine edition changes no wording in dialogue or narration |
| UI labels that describe changed mechanics: guidebook, mic-sign ("L+R"), experience-name | Engine | the engine makes no sense without them; Jeff may veto |
| party-chat and every line in party_chat_lines.py | Story | not in STORY_FEATURES yet: off by default while Jeff writes the lines (`--with party-chat`) |
| curse rework (below), fluff-gate cuts, Ignatius fight, new ending, all bible work | Story | |

## Classification of the opening and text patches

Every patch in feat_opening.py, feat_opening_asides.py, and feat_text.py, read one by one. Rule: a patch that
changes what a line of dialogue or narration says is Story; mechanics, flags, timing, and name-tag fixes are
Engine. Mixed features were split.

| Patch (script 001 unless noted) | Was in | Now in | Why |
|---|---|---|---|
| Recipient speaker tags: Bram -> Balam (001), Gobi -> Gobbi (004), Tartallia -> Tartaglia (005), Raiban -> Laban (007), Davida -> Devida (011); 19 messages | text-edits | text-fixes (Engine) | a name fix: the tag now matches the job menu; no line says anything different |
| Y-hint "Anyway..." cut (018) | text-edits | text-edits (Story) | removes words from what Jian says: a wording change |
| Opening narration rewrite (026) | text-edits | text-edits (Story) | wording |
| The messages text-fixes moves to the end of 001, written again so the layout holds | opening-run | opening-run (Engine) | same bytes as text-fixes (Balam) |
| Walk out of the inn: room, hall, and lobby legs, the map-entry block for 160 and 155, RUN_FLAG 0x1DF | opening-run | opening-run (Engine) | movement; each leg has an empty aside slot |
| Flags 0x1, 0x1E2, 0xC (Lucia left), 0xD (Lucia at the fountain) set on the walk | opening-run | opening-run (Engine) | Jeff: "do go ahead and set the flags" |
| Fountain Square (164) entry checks 0xC instead of 0xD (0x56E8) | opening-run | opening-run (Engine) | a flag check |
| Asides close by themselves when the walk ends (cave_aside_autoclose; text-speed calls it) | opening-run | opening-run (Engine) | timing, no text; with no aside in the Engine walk it never fires |
| Field bottom screen restored at the start of the walk (op `32 0001 0001`, docs/re-opening.md) | (new) | opening-run (Engine) | closes the "Right then!" box and brings the HUD back, so the HUD shows during the whole walk as in normal play |
| Jump at 0x63C4 (after "Right then! I'd better go looking for Lucia...") to the walk | (new) | opening-run (Engine) | the vanilla wake-up plays as written, then the walk |
| Wake-up jump at 0x62CC to Cherenkov's call, Jian's replies, the vanilla waking pose | opening-run | opening-text (Story) | new dialogue; skips the self-introduction |
| The three asides on the walk ("I'm Jian. I'm a courier...") | opening-run | opening-text (Story) | new text; not vanilla (they replace the self-introduction), so not in the Engine edition at all |
| Cherenkov's three lobby lines -> "Jian, what are you doing?! Get to Fountain Square!..." | opening-run | opening-text (Story) | wording; in the Engine edition he says his vanilla line for the flags (0x0CA9, "Get over to the Fountain Square, on the double!") |
| The restore op replaced by a jump | (new) | opening-text (Story) | the room aside's box replaces "Right then!" |
| Title seal says ENGINE | title-seal | title-seal (Engine) | which build a screenshot is from |
| Title seal says STORY | (new) | title-seal-story (Story) | repaints title-seal's tiles |

opening-text and title-seal-story patch bytes that opening-run and title-seal write, so `dsde.patches` refuses a
list that has them without, or before, those (`REQUIRES` in features.py).

## Feature lists and commands

- `ENGINE_FEATURES` (features.py; `DEFAULT_FEATURES` is the same list): timed-run, one-battle-mode,
  no-virtue-clock, restock-on-entry, no-clear-refill, fix-save-glitch, silver-drops, boss-exp, result-screens,
  battle-end-rules, manual-targeting, text-fixes, hold-lr-to-run, leave-drops-gear, battle-speed,
  no-curse-penalty, battle-pace, kill-on-hit, battle-flow, mp-economy, spell-levels, walk-speed, gad-express,
  mic-sign, opening-run, text-speed, experience-name, title-seal, town-menu-dpad, field-menu, guidebook,
  still-hud, statue-any-side, pocketwatch, enemy-sprite-speed, enemy-spell-speed, enemy-quick-steps.
- `STORY_FEATURES = ENGINE_FEATURES +` text-edits, opening-text, title-seal-story.

```
uv run python -m dsde.patches                          # Engine edition -> build/dsde.nds
uv run python -m dsde.patches --edition story          # Story edition -> build/dsde-story.nds
uv run python -m dsde.patches --edition story --with party-chat --output build/x.nds
uv run python -m dsde.bps release "rom/Lunar - Dragon Song (USA).nds" 0.1.6
    # -> build/release/Dragon Song Definitive Edition v0.1.6 (Engine).bps and (Story).bps, SHA-1s logged
uv run python -m dsde.edition_check build/release/dsde-engine_extract/files/script.dat --engine
    # lists every changed script message; fails unless each is a text-fixes rename
```

Checked 2026-10-09 (builds in build/editions/): the Engine build changes 19 script messages, every one a
recipient name tag (build/editions/engine_script_diff.txt); the Story build adds the narration, the wake-up,
the asides, Cherenkov's line, and the Anyway cut (story_script_diff.txt). Emulator, New Game
(emu/plans/editions_opening.plan) and the start save (editions_boot.plan): build/editions/engine_*.png and
story_*.png (0 title seal, 1 narration page 1, 2 to 4 the walk through room, hall, and lobby, 5 the town map,
6 the field from the start save, 7 and 8 Cherenkov and Jack with the walk's flags). The Engine edition shows the
vanilla narration, the self-introduction, and "Right then!", then walks out with the HUD on the bottom screen;
Cherenkov then says his vanilla "Get over to the Fountain Square, on the double!" and Jack his vanilla "I just
saw Lucia in Fountain Square. I thought she was waiting for you...?" (emu/plans/editions_npcs.plan,
editions_jack.plan).

Still open: the guidebook describes the same mechanics in both editions (no edition-aware page yet); the curse
rework (curse-no-healing) goes into ENGINE_FEATURES when it lands; party-chat into STORY_FEATURES when its
lines are written.

## The curse in both editions (Jeff, 2026-10-09)

The curse stays in both editions, made "annoying enough to prioritize removing it, but not so annoying that it
becomes the most memorable part of the game for the wrong reasons." Battles stop taking three times as long;
the player may have to run from some encounters and come back for blue chests. **Must be playtested** (healing
only at statues has to be a viable route from the San Coliseum to Zethos). Wording: the Engine edition keeps
every vanilla curse line, including "The Curse of Lost Equilibrium has been broken!"; only the Story edition
rewrites them.

- **What it does:** Jian cannot be healed except by the Goddess's power, at healing statues. Items and
  healing spells do not restore his HP while he is cursed. He keeps his full attack (vanilla takes his
  3-hit combo away; that penalty is gone in both editions if no-curse-penalty stays on).
- **Why it still matters:** annoying enough that no beastman army would recruit him, which is Zethos's
  reason for cursing him in the first place (009 #13: to stop Gabryel recruiting a human).
- **How it breaks:** in the Zethos fight, on round 3 (the round the vanilla AI already switches to the
  curse-clearing skill, func_020695c0 case 6), the flash, and Jian can use items again from that turn. In
  the Story edition Zethos first says something like "I may have been wrong about you. Let's make this a
  fair fight"; the Engine edition keeps the vanilla lines.
- **Engine pieces:** the curse flag (battle ctx +0x5C, story 0x33 and not 0x79) and its readers are mapped in
  docs/re-curse-battle-speed.md part 1; the healing block is a new check in the item-use and spell-target
  paths for Jian while the flag holds (and the field menu's item use on him); the round-3 line is a battle
  message before the existing skill; the existing "The Curse of Lost Equilibrium has been broken!" line
  (009 0x23C9) is rewritten to match.

## Release mechanics

- `dsde.patches` gets `--edition engine|story` (two feature lists in features.py: `ENGINE_FEATURES` and
  `STORY_FEATURES = ENGINE_FEATURES + story`), and the release step produces both `.bps` files with their
  SHA-1s in the notes.
- The title seal should say which edition it is (so bug reports say which build).
- Saves: both editions must load each other's saves and the original's; story flags used by party chat and
  choices (0x244..0x25F and the read-flag pool) are harmless in the Engine edition because nothing reads
  them there.
