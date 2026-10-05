# Build status

Build the ROM with `uv run python -m dsde.patches` (writes `build/dsde.nds`). Feature definitions live in
`src/dsde/features.py`. Emulator tests are plans in `emu/plans/`, run with
`uv run python -m dsde.emu <plan> --rom build/dsde.nds` (BizHawk in `tools/bizhawk`).

| Design item | Feature | State |
|---|---|---|
| 1. Running | `timed-run` | Verified in emulator: no HP cost; 179 frames running, 180 frames cooldown, runs again if B stays held |
| 2. One battle mode | `one-battle-mode` | Verified: battles use Virtue rules (EXP, kills count) and every kill also rolls items; field mode toggle disabled |
| 2. Result screen item list | `result-item-list` | Off. NOP at 0x0203B0E4 makes the result screen skip the EXP step. Items are granted, just not listed. Needs a different fix |
| 2. Virtue clock removed | `no-virtue-clock` | Verified: clock stays 0 after a kill (original: +1 per frame, 3600 = 60 s) |
| 2. Respawn on re-entry | `restock-on-entry` | Built, not verified (needs a door inside a dungeon) |
| 2. No area-clear refill | `no-clear-refill` | Built, not verified (needs an area clear) |
| 2. Bosses give EXP | none yet | Todo |
| 3. Silver from battles | none yet | Todo, new code |
| 4. Manual targeting | none yet | Todo, new UI code |
| 5. Benched characters earn EXP | none yet | Todo |
| 6. Broken gear back after battle | none yet | Todo |
| 6. Stolen items back if the thief dies | none yet | Todo |
| Save glitch (Flora's tunnel line) | `fix-save-glitch` | Script edit verified in the built archive; the game boots and plays with the rebuilt archive. Not yet played through to Flora |

## Test notes

- Savestates hold game code in RAM, so patched builds must be tested from power-on (`include boot_to_field`),
  not from a savestate made on the original ROM.
- `warp6` sends Jian through his room's door to map 6 (Delrich Temple) by pinning the destination map at
  0x020B77EC, then moves him onto a spawn point. Apply `cheats_strong` before warping.
