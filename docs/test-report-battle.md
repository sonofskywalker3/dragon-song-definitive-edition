# Battle test report: boss EXP and multi-hit targeting

Tested 2026-10-05 in BizHawk (tools/bizhawk) from power-on with the patched ROM `build/par_b/dsde_b.nds`,
starting from the in-game save (`--save`, plans begin with `include boot_from_save`). Command:

```
uv run python -m dsde.emu emu/plans/<plan>.plan --rom build/par_b/dsde_b.nds --save --out build/par_b[/<plan>]
```

| Test | Feature | Result |
|---|---|---|
| 1. Boss EXP in a scripted boss fight (Sasquatch, Delrich Temple) | `boss-exp`, `silver-drops`, `result-screens` | Pass |
| 2. Manual targeting with a real multi-hit attack (Jian's combo, Flora's bow) | `manual-targeting` | **Fail on commit eafc271** (bug below), pass after the fix in this commit |

## 1. Boss EXP: Sasquatch

### How the fight is reached

The game's event scripts start a battle with script op **0x10** (handler func_020408dc, 8 bytes:
`10 00 type a b`). With type 3 it requests battle id `a`: the op stores type and id at script context
+0x268/+0x26A, and the field loop (func_0201e6a0, decomp around line 26654) then writes
`0x020B77E4+0x54 = 1`, `0x020B77E4+0x56 = id` and sets the field state (0x020AFF84+0x8C, that is 0x020B0010)
to 0x73. Battle init (func_020297d4 state 0) passes +0x56 as the event battle id when +0x54 is set, and
func_0202b948 stores it at battle ctx 0x020B85B8+6 and sets the mode (ctx+8) to -1.

All type 3 ops in the 28 scripts (script, offset, battle id): 005 0x3978 (3), 0x3A90 (15), 0x3B94 (16);
006 0x2274 (9); 009 0x5B78 (6); 013 0x0D48 and 0x1040 (1), 0x0DB0 and 0x1060 (0x13), 0x0E18 and 0x1080
(0x14), 0x0E80 and 0x10A0 (0x15); 014 0x08E8 (2); 015 0x4298 (4), 0x42D4 (0x16), 0x4310 (0x17), 0x434C
(0x18), 0x43A8 (5); 017 0x1604 (8); 020 0x105C (7); 021 0x4540 (0x11), 0x4B44 (0x0C), 0x5470 (0x0D), 0x5838
(0x0E); 022 0x10F0 (0x0A); 023 0x2AAC (0x0B), 0x2C40 (0x12). Script 013 belongs to maps 5 to 18 (Delrich
Temple), and its ids 1, 0x13, 0x14, 0x15 are the four Sasquatch fights (docs/re-enemies.md). They are touch
events 15 to 18 (script 013 0x0CC8), each guarded by a map-local flag 0x27E..0x281.

The test save is right after the intro, so the story has not reached the temple fights. The plan therefore
stands Jian in Delrich Temple (map 6, the `warp6` door warp without its last step onto an enemy spawn point)
and does the field loop's three writes itself (event battle id 1). Everything from there on (battle init,
mode, the fight, the result screens) is the game's own scripted-battle path. Not tested: walking into the
Sasquatch on its map with the story at that point.

### Plan

`emu/plans/boss_sasquatch.plan` (with `cheats_strong`: Jian 999 HP, 255 attack and defence, test only).

### Observed (ROM built from eafc271)

Formation: battler 9 = row 136 (Sasquatch), battlers 8 and 10 = row 28 (its two helpers).

| Value | Address | Observed |
|---|---|---|
| Event battle id | u16 0x020B85BE (ctx+6) | 0 -> 1 at battle init (frame 2652) |
| Battle mode | u16 0x020B85C0 (ctx+8) | 0xFFFF (-1) from frame 2652 |
| EXP pool | u32 0x020B8610 | 0 -> 50 (helper, frame 3267) -> 1053 (Sasquatch kill, +1003, frame 3679) -> 1103 (second helper, frame 4391) |
| Silver | u32 0x020B4824 | 150 -> 1253 (+1103, frame 4587, the EXP step) |
| Jian's EXP | u32 0x020B4694 | 0 -> 2206 (pool x 2) when the battle ends (frame 5414) |
| Jian's level | u32 0x020B4664 | index 0 -> 6 (Lv 1 -> Lv 7) |

The Sasquatch's +1003 matches `boss-exp`: 10x the average regular EXP is 77 at level 0 and 13048 at
level 98, and Sasquatch fights force enemy level 7: 77 + (13048 - 77) * 7 / 98 = 1003.

Result pages, in order: the Althena Conduct page with the pool (2206), the pour, the page with Jian 2206
waiting for A, then "Items received!" with Healing Drop x1, Beast's Horn x1 and "Silver 1103", then the
field (Jian Lv 7, HP 87/87).

Screenshots (eafc271 build): `build/par_b/boss_intro.png` (Sasquatch and helpers),
`build/par_b/boss_fight70.png` (pool page, 2206), `build/par_b/boss_exp_page.png` (Jian 2206, OK),
`build/par_b/boss_items_page.png` (items and Silver 1103), `build/par_b/boss_after.png` (back on the field).

Rerun on the fixed build (this commit, with the results agent's work in progress in the tree):
`build/par_b/boss_fixed/boss_sheet.png`. Same totals (pool 1103, silver 150 -> 1253, Jian 0 -> 2206), but
Jian's first combo now kills all three enemies in one action (see test 2), so the plan is timed for that.

**Pass.**

## 2. Manual targeting with a real multi-hit attack

### Multi-hit attacks that exist

- **Jian's 3-hit combo.** He has it from the start until the curse after the San Coliseum tournament. One
  target pick (hit index 0), then three hits through func_02030b44, all on target slot +0x8C.
- **Flora's bow.** func_020514ec 0x02051BD8: for character id 3 the hit count is
  `rand % byte[0x0213B919] + 1`. That byte (+0x11 of the 0x13-byte block at 0x0213B908) is rebuilt from the
  actor's five gear slots by func_0206ab6c at every action, so pinning it has no effect (the earlier
  finding in docs/plan-targeting.md). Equipment effect (u16 at 0x0209B06A + item * 0x14) 0x2B sets it to 2,
  0x2C to 3: **Great Bow (item 36)** gives up to 2 hits, **Composite Bow (item 39)** up to 3.
- Gale Cut and Thunder Sword are spells, not Attack; hook D leaves spells alone by design.

### Plans

Temple battle (warp6) with back row battlers 4, 5, 6 and front row 9 (left) and 10 (right). HP of stat
record r is at 0x0228E860 + r * 0x6C + 0x14 (pointer at 0x020B8620; record r = battler r here). The
chosen target gets HP 1, the others 300 (back) or 999 (front). Logged: `exec 0x02051C48` (target pick per
hit index), `exec 0x02030BC8` (each hit, r4 = target battler), and the damage queue at record +0x60.

- `emu/plans/tgt_multihit_jian.plan`: Jian alone, Fight, picks the bottom-left cell (battler 9).
- `emu/plans/tgt_multihit_flora.plan`: Flora alone (slot 0 = 3, slot 1 empty), Composite Bow poked into her
  weapon slot (0x020B47AC = 39), DEX and AGI 255 so the arrows land and she acts first, Fight, Down, picks
  battler 9.

### Bug found (eafc271)

Every hit of a multi-hit attack landed on the chosen enemy even after the first hit had killed it; the
next enemy was never hit.

| Run | Hits (target battler, queued damage on it) | HP afterwards |
|---|---|---|
| Jian, eafc271 | 9 (-153), 9 (-406 total), 9 (-551 total) | 9: 1 -> 0, 10: 999 (untouched) |
| Flora, eafc271 (rolled 3 hits) | 9 (-37), 9 (-68 total), 9 (-104 total) | 9: 1 -> 0, 10: 999 (untouched) |

Screenshots: `build/par_b/mhj_sheet.png` (the damage numbers 153, 253 and 145 all over the skeleton in
slot 9, the spider in slot 10 untouched), `build/par_b/mhf_t*.png` (Flora).

Cause: hits of one action do not lower HP. func_02030b44 queues each hit's damage with func_02053798
(stat record +0x60, `pending += -damage`), and the queue is applied to HP (+0x14) and cleared when the
action ends (frame 3270 in the Jian run, after all three hits). So the redirect hook D, which asked
func_02031b70 "is the target alive", always got "alive" during the combo. Vanilla does the same, so this
was the vanilla "overkill is wasted" rule surviving the design's "an attack is never wasted".

### Fix (this commit)

`src/dsde/feat_targeting.py`: new cave helper `cave_tgt_live` (battler -> func_02031b70's answer, but 0
when the battler is alive and HP + queued damage <= 0). Hook D (`cave_tgt_hit`) calls the game's alive
check first and, when the target is alive, `cave_tgt_live`; a party Attack hit on an enemy that is dead
or already doomed moves to the next living enemy. Every other hit (spells, enemy attacks, cover) gets the
game's own answer as before. The next-enemy search (`cave_tgt_ok`) also uses `cave_tgt_live`, so a hit is
not redirected onto another enemy that this action already killed. At command time and at the target pick
the queue is empty, so the picker and hook C behave as before. New constants in
`src/dsde/targeting_consts.py` (STATS_PTR, STAT_SIZE, STAT_HP, STAT_PENDING_HP, STAT_RECORD).

### Observed after the fix

| Run | Hits (target battler, queued damage) | HP afterwards |
|---|---|---|
| Jian | 9 (-153), 10 (-253), 10 (-398 total) | 9: 1 -> 0, 10: 999 -> 601 |
| Flora (rolled 3 hits) | 9 (-37), 10 (arrow missed, accuracy roll), 10 (-32) | 9: 1 -> 0, 10: 999 -> 967 |

Screenshots: `build/par_b/tgt_multihit_jian/mhj_sheet_fixed.png` (153 on the skeleton, then 253 and 145
on the spider, which flashes red), `build/par_b/tgt_multihit_flora/mhf_t*.png`.

Regression on the fixed build: `tgt_redirect_hit` (dead target between pick and hit -> 10, HP 32 -> 0) and
`tgt_redirect_pick` (dead target before the pick -> 10) still pass (`build/par_b/tgt_redirect_*`); the
boss fight above finishes with the same EXP and silver.

**Pass after the fix.**

### Notes

- Jian's animation still swings at the original enemy; only the damage number and flash move to the new
  one. Cosmetic.
- When every enemy the attacker reaches is dead or doomed, the next-enemy search falls back to every row
  (existing `cave_tgt_next` rule), so Jian's later combo hits can land on a back-row enemy. With nobody left
  the hit lands on the doomed enemy as in vanilla.
- A front-row slot freed by a kill is refilled from the back row after the action (battler 4 moved into
  slot 8, a back-row Tick into slot 9), as noted in docs/plan-targeting.md.
- Still not tested: Great Bow (2 hits), multi-hit with Flora in a party of three, Auto battle with a
  multi-hit attacker.
