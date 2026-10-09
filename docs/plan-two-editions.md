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

## Feature split (proposed; Jeff decides the flagged rows)

| Feature | Edition | Note |
|---|---|---|
| timed-run, pocketwatch, walk-speed, no-virtue-clock, restock-on-entry, no-clear-refill, fix-save-glitch, statue-any-side | Engine | field mechanics and fixes |
| one-battle-mode, silver-drops, boss-exp, result-screens, battle-end-rules, leave-drops-gear, hold-lr-to-run, mic-sign | Engine | battle rules and rewards |
| manual-targeting and its sub-features, battle-speed, battle-pace, kill-on-hit, battle-flow, enemy-sprite-speed, enemy-spell-speed, enemy-quick-steps, enemy-preload (if adopted) | Engine | battle pacing and control |
| mp-economy, spell-levels, gad-express | Engine | balance; Gad's job logic, not his dialogue |
| field-menu, town-menu-dpad, town-brackets, still-hud, text-speed, title-seal, guidebook, experience-name | Engine | interface; the guidebook describes whichever edition it is built into (needs an edition-aware page) |
| text-edits: recipient names matched to dialogue, the "Anyway..." trim | Engine | fixes, not story |
| **no-curse-penalty** | **Jeff's call** | mechanical (Jian keeps his combo) but the vanilla text still calls him cursed; in the Story edition it is replaced by the curse rework |
| **opening-run** (Jian woken from downstairs, runs out of the inn, asides close themselves) and the **Fountain Square** fix (Lucia waits without the Jack detour) | **Jeff's call** | the same story told faster: pacing or story? Recommendation: Engine, since no line of plot changes |
| the rewritten opening narration (retranslated from the Japanese) | Story | wording of the story |
| party-chat and every line in party_chat_lines.py | Story | |
| curse rework (below), fluff-gate cuts, Ignatius fight, new ending, all bible work | Story | |

## The curse in the Story edition (Jeff, 2026-10-09)

The curse stays, explained better and made less punishing:

- **What it does:** Jian cannot be healed except by the Goddess's power, at healing statues. Items and
  healing spells do not restore his HP while he is cursed. He keeps his full attack (vanilla takes his
  3-hit combo away; that penalty is gone in both editions if no-curse-penalty stays on).
- **Why it still matters:** annoying enough that no beastman army would recruit him, which is Zethos's
  reason for cursing him in the first place (009 #13: to stop Gabryel recruiting a human).
- **How it breaks:** in the Zethos fight, on round 3 (the round the vanilla AI already switches to the
  curse-clearing skill, func_020695c0 case 6), Zethos says something like "I may have been wrong about you.
  Let's make this a fair fight," then the flash, and Jian can use items again from that turn.
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
