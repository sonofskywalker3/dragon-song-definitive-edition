# Boss EXP

Design item 2 says bosses give EXP worth about ten regular enemies at the boss's level. The `boss-exp`
feature sets each boss's two EXP fields (level 0 at row +0x14, level 98 at row +0x28) to
`BOSS_EXP_FACTOR` (10) times the average of the same fields over the regular enemies of the place the boss
is fought in. EXP is linear in level, so the boss pays ten of that area's regulars at whatever level the
fight rolls. Code and tables: `src/dsde/boss_exp.py`.

The first version used ten times the average of every regular row in the game, which overpaid early bosses
because early species have low EXP curves (Sasquatch gave 1003 at level 7, about 20 of its own helpers).

## How each boss's area was found

- **Boss fights.** Event scripts start them with op 0x10 type 3 (`10 00 03 00 <id>`). The id is the battle
  type that `func_0202b948` turns into the boss row (table in docs/re-enemies.md). Every such op is listed
  in docs/test-report-battle.md section 1.
- **Script to maps.** The map table at 0x02091D18 (0x28 bytes per map) holds the map's script in byte +2.
  Dungeon maps 0 to 150 map to scripts as follows: 013 maps 5 to 19, 014 maps 31 to 34, 015 maps 140 to
  150, 017 maps 94 to 99, 006 maps 100 to 105, 022 maps 106 to 111, 023 maps 112 to 120, 020 maps 58 to 60,
  021 maps 61 to 84. Scripts 005 (San Coliseum) and 009 (Zethos Castle) belong to towns, which have no
  encounters.
- **Maps to area group.** The dungeon group table at 0x02091C78 (docs/re-field-battle.md section 2.5), the
  same group the battle context keeps at +0x00. Maps 61 to 84 switch to group 19 once story flag 0xC9 is set;
  script 021 sets it at 0x46A8, after the Ignatius fight (0x4540) and before the three Gideon fights.
- **Area group to regular rows.** `func_0202b3f0` fills a regular battle from two lists of 8 rows (front,
  back; -1 empty) at `[0x020A789C + 4 * group]`, after the lead row that `func_0202b948` takes from the s16
  pair at `0x02096E28 + 4 * group`. The regular rows of an area are the union of both. `uv run python -m
  dsde.boss_exp` checks the written-out lists in `boss_exp.py` against the ROM and prints the table below.
- **Dark Jian** has no script op of its own: `func_020297d4` chains event battle 10 (Black Dragon) into
  battle type 0x19, so Dark Jian is fought in the Black Dragon Cave.
- **Helpers.** Only the Sasquatch fights have regular helpers (`func_0202b1a4`): rows 28, 40, 9, and 1 with
  72 for battle ids 1, 0x13, 0x14, 0x15. Their EXP at level 7 (50, 46, 37, 36, 40) is close to the temple
  average (39), so the temple's own encounter rows are used. The Caucus fight's helpers (Orcus, Morus) are
  bosses, and the Blue Dragon's summons are row 156.
- **Towns.** San Coliseum (Raft, Sharif, Moran) and Zethos Castle use the nearest dungeon before them in the
  story (docs/story-party-timeline.md): the script 014 dungeon (Armored Boar's) and the Cathedral of Althena.

## Result

EXP before the game's doubling. "Fight level" is the lowest enemy level the fight can roll: the boss's
`area_min` override where it has one (Sasquatch 7, Coliseum and Zethos 10, Gideon 40, Gideon 2 and 3 42,
Ignatius 97), otherwise the area minimum of its maps. Higher party levels raise it (docs/re-enemies.md
section 2).

| Row | Boss | Place (area group) | EXP level 0 | EXP level 98 | Fight level | EXP there |
|---|---|---|---|---|---|---|
| 136 | Sasquatch | Delrich Temple (1) | 40 | 4929 | 7 | 389 |
| 137 | Armored Boar | script 014 dungeon, maps 31 to 34 (3) | 44 | 6015 | 10 | 653 |
| 138 | Raft | San Coliseum, uses group 3 | 44 | 6015 | 10 | 653 |
| 139 | Sharif | San Coliseum, uses group 3 | 44 | 6015 | 10 | 653 |
| 140 | Moran | San Coliseum, uses group 3 | 44 | 6015 | 10 | 653 |
| 141 | Deuce (all four) | Cathedral of Althena (18) | 148 | 10424 | 10 | 1196 |
| 142 | Gronk | Cathedral of Althena (18) | 148 | 10424 | 10 | 1196 |
| 143 | Zethos | Leephon, uses group 18 | 148 | 10424 | 10 | 1196 |
| 144 | Caucus | Elda Canyon (8) | 126 | 12571 | 16 | 2157 |
| 145 | Orcus | Elda Canyon (8) | 126 | 12571 | 16 | 2157 |
| 146 | Morus | Elda Canyon (8) | 126 | 12571 | 16 | 2157 |
| 147 | Red Dragon | Red Dragon Cave (12) | 79 | 13557 | 23 | 3242 |
| 148 | White Dragon | White Dragon Cave (13) | 65 | 13395 | 24 | 3329 |
| 149 | Black Dragon | Black Dragon Cave (14) | 69 | 15375 | 28 | 4442 |
| 150 | Blue Dragon | Blue Dragon Cave (15) | 70 | 20125 | 36 | 7437 |
| 151 | Dark Jian | Black Dragon Cave (14) | 69 | 15375 | 28 | 4442 |
| 152 | Gideon | Vile Castle return (19) | 148 | 21654 | 40 | 8925 |
| 153 | Gideon 2 | Vile Castle return (19) | 148 | 21654 | 42 | 9364 |
| 154 | Gideon 3 | Vile Castle return (19) | 148 | 21654 | 42 | 9364 |
| 155 | Ignatius | Vile Castle, first visit (9) | 148 | 13192 | 97 | 13058 (unwinnable fight) |

Notes for playtesting:

- The Caucus fight has three boss rows, so it pays about 30 regulars' worth.
- The Cathedral's encounter rows (group 18) are the first variants of late-game species, so its bosses pay
  more than the bosses just before it (1196 against 653 at level 10).
- The place names of groups 3 (maps 31 to 34) and 18 come from the scripts' bosses and the story order,
  not from a map name table.

## Emulator check

`emu/plans/boss_sasquatch.plan` on `build/par_b/dsde_b.nds`, screenshots in `build/par_b/boss_area/`.
Jian's first combo kills the Sasquatch and both Yeti helpers: EXP pool 0 to 489 (Sasquatch 389, helpers 50
each), silver 150 to 639, Jian 0 to 978 EXP (pool x 2). Before this change the same fight gave a pool of
1103. Regression `test_exp_fast` (regular battle on map 6) is unchanged: pool 101, silver 150 to 251, Jian
202 EXP.

Three more scripted boss fights, same trick as `boss_sasquatch` (Jian stands in Delrich Temple, map 6,
party level 1, and the plan does the field loop's three writes with the boss's battle id), on
`build/par_c/dsde_c.nds` built from ffa9c41. Plans `emu/plans/boss_raft.plan`, `emu/plans/boss_gronk.plan`,
`emu/plans/boss_reddragon.plan`; logs and screenshots in `build/par_c/boss_raft/`, `build/par_c/boss_gronk/`,
`build/par_c/boss_reddragon/`. In all three the battle mode u16 0x020B85C0 goes to 0xFFFF (-1) at battle
init, the event battle id u16 0x020B85BE holds the battle id, the formation is the boss alone in battler 9,
and the boss's battle stat record (0x0228E860 + 9 * 0x6C) holds its level at +0x0C and the EXP the kill adds
at +0x50. The battle background is the boss's own (coliseum, cathedral, lava cave), not the temple's.

| Plan | Battle id | Row | Level rolled | Expected EXP | Record +0x50 | Pool | Silver | Jian EXP |
|---|---|---|---|---|---|---|---|---|
| `boss_raft` | 3 | 138 Raft | 10 (Coliseum override) | 44 + 5971 * 10 / 98 = 653 | 653 | 0 to 653 | 150 to 803 | 0 to 1306 |
| `boss_gronk` | 5 | 142 Gronk | 4 (map 6 area_min) | 148 + 10276 * 4 / 98 = 567 | 567 | 0 to 567 | 150 to 717 | 0 to 1134 |
| `boss_reddragon` | 8 | 147 Red Dragon | 4 (map 6 area_min) | 79 + 13478 * 4 / 98 = 629 | 629 | 0 to 629 | 150 to 779 | 0 to 1258 |

Silver rises by the pool and Jian's EXP by pool x 2 (the game's doubling) in each fight. Gronk and the Red
Dragon have no area_min override, so the temple's level 4 is what they roll here; in their own places they
roll 10 and 23 or more (1196 and 3242). Raft dies to Jian's first combo, Gronk (810 HP) and the Red Dragon
(1122 HP) take several actions.

Result pages look right in all three: the EXP page shows Jian's total and the Silver line with no Althena
Conduct window (`raft_r5.png`, `gronk_r16.png`, `reddragon_r11.png`), then "Items received!" because each
boss dropped items: Healing Drop x2 and the Raft card (`raft_r6.png`), Counter Type 2 and the Gronk card
(`gronk_r17.png`), Blazing Ring and the Red Dragon card (`reddragon_r12.png`). Intros: `raft_intro.png`,
`gronk_intro.png`, `reddragon_intro.png`. **Pass.**
