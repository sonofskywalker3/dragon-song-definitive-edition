# Build status

Build the ROM with `uv run python -m dsde.patches` (writes `build/dsde.nds`). Feature definitions live in
`src/dsde/features.py`. Emulator tests are plans in `emu/plans/`, run with
`uv run python -m dsde.emu <plan> --rom build/dsde.nds` (BizHawk in `tools/bizhawk`).

| Design item | Feature | State |
|---|---|---|
| 1. Running | `timed-run` | Verified in emulator: no HP cost; 179 frames running, 180 frames cooldown; holding B runs once, a fresh press is needed to run again (as in Lunar 1 and 2) |
| 2. One battle mode | `one-battle-mode` | Verified: battles use Virtue rules (EXP, kills count) and every kill also rolls items; field mode toggle disabled |
| 2. Result screen item list | `result-item-list` | Off. NOP at 0x0203B0E4 makes the result screen skip the EXP step. Items are granted, just not listed. Needs a different fix |
| 2. Virtue clock removed | `no-virtue-clock` | Verified: clock stays 0 after a kill (original: +1 per frame, 3600 = 60 s) |
| 2. Respawn on re-entry | `restock-on-entry` | Built, not verified (needs a door inside a dungeon) |
| 2. No area-clear refill | `no-clear-refill` | Built, not verified (needs an area clear) |
| 2. Bosses give EXP | `boss-exp` | Built: mode -1 (boss/scripted) battles take the EXP path; every boss gets 10x the average regular enemy EXP (77 at level 0, 13048 at level 98, before doubling). Regular battles regression-tested; no boss fight tested yet |
| 3. Silver from battles | `silver-drops` | Verified: the EXP step adds the battle's EXP pool as silver (150 -> 251 for a pool of 101). No on-screen message yet |
| 4. Manual targeting | `manual-targeting` | Verified in emulator (plans `tgt_grid`, `tgt_touch`, `tgt_redirect_pick`, `tgt_redirect_hit`): Fight opens an enemy grid shaped like the battle (back row on top, front row below, left to right); Jian sees only the front row, Flora both rows; D-pad, A, B and tap-twice work; the chosen battler is attacked; a dead chosen target goes to the next enemy, before the attack and at the hit; the item list still works afterwards; `test_exp` unchanged. Not yet seen: a real multi-hit attack, 4 enemies in one row (4th column on page 2), boss fights, mic Run during the picker |
| 5. Benched characters earn EXP | `battle-end-rules` | Verified: with Jian alone, Lucia, Gabryel and Flora each gained the same 152 EXP, levels and stats recomputed by the game's own routines; Rufus too |
| 6. Broken gear back after battle | `battle-end-rules` | Verified with a simulated break (weapon swapped to its replacement mid-battle is back after the battle). Not yet seen with a real breaker enemy |
| 6. Stolen items back if the thief dies | `battle-end-rules` | Verified with temple enemies forced to steal: Fossil stolen mid-battle, returned on the win. Implemented as "a won battle returns all thefts" because enemies change battler slots mid-fight; equivalent since enemies never flee |
| Save glitch (Flora's tunnel line) | `fix-save-glitch` | Script edit verified in the built archive; the game boots and plays with the rebuilt archive. Not yet played through to Flora |

## Test notes

- BizHawk's DS clock is fixed (`UseRealTime: false` in tools/bizhawk/config.ini). With the real clock the game's
  randomness changed every run and battles did not always start.
- The inventory is indexed by item id minus one: item N's count is at 0x0213B930 + N - 1.

- Savestates hold game code in RAM, so patched builds must be tested from power-on (`include boot_to_field`),
  not from a savestate made on the original ROM.
- `warp6` sends Jian through his room's door to map 6 (Delrich Temple) by pinning the destination map at
  0x020B77EC, then moves him onto a spawn point. Apply `cheats_strong` before warping.
