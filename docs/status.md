# Build status

Build the ROM with `uv run python -m dsde.patches` (writes `build/dsde.nds`). Feature definitions live in
`src/dsde/features.py`. Emulator tests are plans in `emu/plans/`, run with
`uv run python -m dsde.emu <plan> --rom build/dsde.nds` (BizHawk in `tools/bizhawk`).

| Design item | Feature | State |
|---|---|---|
| 1. Running | `timed-run` | Verified in emulator: no HP cost; 179 frames running, 180 frames cooldown; holding B runs once, a fresh press is needed to run again (as in Lunar 1 and 2) |
| 2. One battle mode | `one-battle-mode` | Verified: battles use Virtue rules (EXP, kills count) and every kill also rolls items; field mode toggle disabled |
| 2. Result screen item list | `result-screens` | Verified (plans `test_result_pages`, `test_result_pages_boss`): after the EXP page, A opens a second page, "Items received!" with the dropped items (or "No items dropped."), then A leaves. EXP (202), silver (150 -> 251) and the four items are still granted; same with the battle mode pinned to -1 (boss rules). Skipped when nothing dropped and no silver was gained. Shows at most 4 items, as in the original |
| 2. Virtue clock removed | `no-virtue-clock` | Verified: clock stays 0 after a kill (original: +1 per frame, 3600 = 60 s) |
| 2. Respawn on re-entry | `restock-on-entry` | Built, not verified (needs a door inside a dungeon) |
| 2. No area-clear refill | `no-clear-refill` | Built, not verified (needs an area clear) |
| 2. Bosses give EXP | `boss-exp` | Built: mode -1 (boss/scripted) battles take the EXP path; every boss gets 10x the average regular enemy EXP (77 at level 0, 13048 at level 98, before doubling). Regular battles regression-tested; no boss fight tested yet |
| 3. Silver from battles | `silver-drops` | Verified: the EXP step adds the battle's EXP pool as silver (150 -> 251 for a pool of 101). Shown as "Silver 101" on the item page (`result-screens`) |
| 4. Manual targeting | `manual-targeting` | Verified in emulator (plans `tgt_grid`, `tgt_touch`, `tgt_redirect_pick`, `tgt_redirect_hit`): Fight opens an enemy grid shaped like the battle (back row on top, front row below, left to right); Jian sees only the front row, Flora both rows; D-pad, A, B and tap-twice work; the chosen battler is attacked; a dead chosen target goes to the next enemy, before the attack and at the hit; the item list still works afterwards; `test_exp` unchanged. Not yet seen: a real multi-hit attack, 4 enemies in one row (4th column on page 2), boss fights, mic Run during the picker |
| 5. Benched characters earn EXP | `battle-end-rules` | Verified: with Jian alone, Lucia, Gabryel and Flora each gained the same 152 EXP, levels and stats recomputed by the game's own routines; Rufus too |
| 6. Broken gear back after battle | `battle-end-rules` | Verified with a simulated break (weapon swapped to its replacement mid-battle is back after the battle). Not yet seen with a real breaker enemy |
| 6. Stolen items back if the thief dies | `battle-end-rules` | Verified with temple enemies forced to steal: Fossil stolen mid-battle, returned on the win. Implemented as "a won battle returns all thefts" because enemies change battler slots mid-fight; equivalent since enemies never flee |
| Save glitch (Flora's tunnel line) | `fix-save-glitch` | Script edit verified in the built archive; the game boots and plays with the rebuilt archive. Not yet played through to Flora |

## Test notes

- Parallel runs: build each ROM to its own name and folder (`uv run python -m dsde.patches --output build/par_a/dsde_a.nds`)
  and run with `--out build/par_a` (and `--save` for the fast start). Each ROM name gets its own battery save, so several
  emulators can run at once.

- Fast start: `include boot_from_save` and run with `--save` loads an in-game save made right after the
  intro (about 2200 frames instead of 16000). The save lives in build/emu/saves/start.SaveRAM; recreate it with
  emu/plans/make_save.plan. A battery save only holds progress, so unlike savestates it is safe across builds.

- BizHawk's DS clock is fixed (`UseRealTime: false` in tools/bizhawk/config.ini). With the real clock the game's
  randomness changed every run and battles did not always start.
- The inventory is indexed by item id minus one: item N's count is at 0x0213B930 + N - 1.

- Savestates hold game code in RAM, so patched builds must be tested from power-on (`include boot_to_field`),
  not from a savestate made on the original ROM.
- `warp6` sends Jian through his room's door to map 6 (Delrich Temple) by pinning the destination map at
  0x020B77EC, then moves him onto a spawn point. Apply `cheats_strong` before warping.
- Victory screen flow (func_020297d4 case 10, substate at battle ctx 0x020B85B8 + 0x10): 1 victory poses, 2 and 3 EXP
  pour and level-ups, 0x28 then 99. Substate 99 calls func_0203a34c every frame and leaves the battle on A (it does not
  time out). Windows: 5 item list, 6 Althena Conduct pool, 7..9 party members; func_0204582c(window, open, -1) opens or
  closes one, func_020457cc(window) reads its state (0 while closing). Opening a window while another one in the same
  area is still closing lets the closing one erase parts of the new one.
- `battle_to_victory` fights the first Delrich Temple battle with A presses and stops as the victory starts (frame 7210).
