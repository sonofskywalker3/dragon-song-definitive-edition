# Build status

Build the ROM with `uv run python -m dsde.patches` (writes `build/dsde.nds`). Feature definitions live in
`src/dsde/features.py`. Emulator tests are plans in `emu/plans/`, run with
`uv run python -m dsde.emu <plan> --rom build/dsde.nds` (BizHawk in `tools/bizhawk`).

| Design item | Feature | State |
|---|---|---|
| 1. Running | `timed-run` | Verified in emulator: no HP cost; 179 frames running, 180 frames cooldown; holding B runs once, a fresh press is needed to run again (as in Lunar 1 and 2) |
| 2. One battle mode | `one-battle-mode` | Verified: battles use Virtue rules (EXP, kills count) and every kill also rolls items; field mode toggle disabled |
| 2. Result screen item list | `result-screens` | Verified (plans `test_result_silver1`, `test_result_silver3`, `test_result_noitems`): after the EXP page, A opens a second page, "Items received!" with the dropped items, then A leaves. Only shown when items dropped; with no items one A on the EXP page leaves the battle as in the original. EXP (202), silver (150 -> 251) and the items are still granted. Shows at most 4 items, as in the original |
| 2. Virtue clock removed | `no-virtue-clock` | Verified: clock stays 0 after a kill (original: +1 per frame, 3600 = 60 s) |
| 2. Respawn on re-entry | `restock-on-entry` | Verified (docs/test-report-field.md): leaving map 6 for map 7 and coming back rerolls the map (kills 2/5 to 0/6, 6 symbols); no restock while staying, after a battle or after the menu. An opened blue chest stays opened |
| 2. No area-clear refill | `no-clear-refill` | Verified (docs/test-report-field.md): clearing map 6 gives no HP/MP (original: +30%, states 0x1B and 0x3C); blue chest locked before the clear, opens after |
| 2. Bosses give EXP | `boss-exp` | Verified in a scripted Sasquatch fight (`boss_sasquatch`): mode -1 (boss/scripted) battles take the EXP path; each boss gets 10x the average EXP of the regular enemies of its own area, linear in level (docs/boss-exp.md, check with `uv run python -m dsde.boss_exp`). Sasquatch at level 7: 389 (was 1003), pool 489 with its two helpers, Jian +978. Regular battles unchanged (`test_exp_fast`). Also verified in scripted Raft (`boss_raft`, level 10, pool 653), Gronk (`boss_gronk`) and Red Dragon (`boss_reddragon`) fights, both at the temple's level 4 (pools 567 and 629): mode -1, the boss's EXP matches docs/boss-exp.md for the rolled level, silver + pool, Jian + pool x 2, EXP page with the Silver line and the item page shown. Not played: a boss at its own area's level, or reached through the story |
| 3. Silver from battles | `silver-drops` | Verified: the EXP step adds the battle's EXP pool as silver (150 -> 251 for a pool of 101). Shown on the EXP page as a "Silver 101" line in a member line box, in black text, at the left x of the first member line and one empty row below the last member (`result-screens`, plans `test_result_silver1/2/3`, shots r1_exp, r2_exp, r3_exp). The Althena Conduct window (title banner and pool box) is no longer shown; the pool still counts down and is awarded. The member lines move up into its rows, keeping their staggered x, so all three members, the gap and the Silver line fit on the top screen |
| 4. Manual targeting | `manual-targeting` | Verified in emulator (plans `tgt_grid`, `tgt_touch`, `tgt_redirect_pick`, `tgt_redirect_hit`): Fight opens an enemy grid shaped like the battle (back row on top, front row below, left to right); Jian sees only the front row, Flora both rows; D-pad, A, B and tap-twice work; the chosen battler is attacked; a dead chosen target goes to the next enemy, before the attack and at the hit; the item list still works afterwards; `test_exp` unchanged. Multi-hit (`tgt_multihit_jian`, `tgt_multihit_flora`): later hits move to the next enemy once the first kills, and the attacker's lunge follows a redirect (Jian hops to the new enemy between hits, or leaps straight to it when the target died before the action; docs/test-report-battle.md section 3). The Blue Dragon's summons (row 156, whose own name slot is "Jian") show as "Bubble" with an icon drawn from their own battle sprite, seen in a scripted Blue Dragon fight (`tgt_bluedragon`, shot build/par_a/bluedragon/bd_picker_sheet.png; also `tgt_row156`); `tgt_grid` and `tgt_touch` unchanged, the item list still prints counts. Not yet seen: 4 enemies in one row (4th column on page 2), mic Run during the picker |
| 5. Benched characters earn EXP | `battle-end-rules` | Verified: with Jian alone, Lucia, Gabryel and Flora each gained the same 152 EXP, levels and stats recomputed by the game's own routines; Rufus too |
| 6. Broken gear back after battle | `battle-end-rules` | Verified with a simulated break (weapon swapped to its replacement mid-battle is back after the battle). Not yet seen with a real breaker enemy |
| 6. Stolen items back if the thief dies | `battle-end-rules` | Verified with temple enemies forced to steal: Fossil stolen mid-battle, returned on the win. Implemented as "a won battle returns all thefts" because enemies change battler slots mid-fight; equivalent since enemies never flee |
| Save glitch (Flora's tunnel line) | `fix-save-glitch` | Verified (docs/test-report-field.md): talking to Flora twice in the Underground Tunnel sets flag 0x5E, 0xCF stays clear, Save still works (original: 0xCF set, Save struck out) |
| Text edits | `text-edits` | Script text changes listed in `src/dsde/feat_text.py` (`TEXT_EDITS`). Intro: "her servant the Dragonmaster" -> "her champion the Dragonmaster," (script 026; the message moves to the end of the file because it grows). Verified (`text_intro`, build/par_a/intro/intro_page1.png): the line shows with no blank line after it and the whole intro plays to the end |

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
  With the current build that battle is won near frame 4260, so its later presses run into the result pages; the
  `test_result_silver*` and `test_result_noitems` plans use 52 presses instead. `party3_strong` pins the party slots to
  Jian, Lucia and Gabryel (all strong) for three-member tests.
- EXP page windows: the table at 0x020B88B4 (0x30 bytes per window, 14 windows) holds flags, state, final and start
  x/y (+0x10..+0x1c), width and height (+0x20, +0x24) and the current x/y (+0x28, +0x2c); func_02045ccc fills in the
  fixed geometry. Pool window 6 is at y 5 (7 rows: 3 banner, 4 box), members 7..9 at y 12, 16, 20 (4 rows each), so
  three members fill the top screen. `result-screens` reuses window 6 as the Silver line (member frame from source
  tilemap row 0x1A, text drawn in black with func_02045114 palette 0; the palette argument selects BG palette
  11 + n, names use 4, or 1 when the member is down) and moves the members up 7 rows to y 5, 9, 13. `party2_strong`
  pins Jian and Lucia (third slot 65535) for two-member tests.
