# Enemy attack animations: forcing a battle, timing every action

Research only (2026-10-08): no ROM patches. Every enemy action that can be forced was recorded on Fast (the
default battle speed), Normal, and the vanilla ROM, with per-frame logs, a shot of both screens every 2nd frame
of the Fast turn, and a GIF. Claims are marked **confirmed** (measured or read in code, evidence given) or
**uncertain**.

Cutoff: an action is "too long" when its action script runs more than **60 frames on Fast**, from the first
step to the last (frames in round state 7).

## Result in one paragraph

151 distinct actions (34 normal species x their distinct actions, 20 bosses); 150 recorded, 1 not reachable.
**All 150 run longer than 60 frames on Fast** (confirmed): the shortest is the Bealzebub lunge (66 frames,
script 0x02095334); the median is 166; the longest is Morus' steal (578). Fast only halves the
*fixed* steps (type 2); enemy sprites still animate at 1x on Fast (sprite level 0, `lvl 0` in every Fast log),
so the animation-driven steps (type 1) are untouched and dominate: Shaitan's 469 Fast frames are 409
animation, 60 fixed (confirmed, timing.json).

## 1. Forcing a battle (reusable)

### 1.1 Regular enemies (confirmed: 3 proof species, then all 34 normal species)

1. Boot from `build/emu/saves/start.SaveRAM` (`include boot_from_save`) and walk into Delrich Temple (map 6)
   without touching an enemy (`boss_gronk.plan`'s copy of warp6 without its last move).
2. Make the row tough and predictable by poking its record (row base = 0x02097CE4 + row * 0x54, RAM, so no
   patch): HP at level 0 and 98 (+0x04, +0x18) = 30000; AI class bits 0..1 of +0x00 = 3 (func_02069848: class
   3 above half HP always acts); cumulative chances +0x2C.. = 0xFFFF for the slots before the wanted action and
   100 from it on (func_02069a38 takes the first slot with `rand % 100 <= chance`).
3. Overwrite the formation at the entry of func_0202bc28, which func_020297d4 calls right after
   func_0202b948 (states 0 and 1): new plan command `execpoke ADDR KIND TARGET VALUE` (a write done by an
   `event.on_bus_exec` callback). Battle ctx 0x020B85B8: lead row +0x32 (0x020B85EA), eight slots +0x34..
   (0x020B85EC + 2 * i, -1 empty, slot i = battler 4 + i; slots 0..3 back row, 4..7 front). Only the slot the
   game itself gives the lead (slot 5, or slot 1 when the species flag & 4 of 0x02096EDC + species * 0x1C
   is set, func_0202b3f0) holds the row.
4. Start a regular battle through the field's own state: `poke u16 0x020B7838 0`, `poke u16 0x020B783A 0`
   (formation 0), `poke u32 0x020B0010 0x73`.
5. Keep Jian alive: `pinptr u32 0x020B8620 0x14 999` (new command: pin [pointer] + offset; stat record 0 HP).
   Pinning the character record (cheats_strong) does not hold battle HP.
6. Wait for battle main state 7 (`waituntil u32 0x020B0010 7 3000`), **then 110 more frames** (the
   Manual/Auto window slides in; pressing earlier picks Manual), then Auto: `press Right 3`, `wait 10`,
   `press A 3`, `wait 20`, `press A 3` (the second A confirms).
7. On the DE ROM pin the speed setting byte (`cave_speed_state`, ITCM): **picking Auto switches the setting to
   Faster** (feat_battle_speed). `pin u8 <cave_speed_state> 1` for Fast, 0 for Normal; the address moves with
   the feature layout (0x01FF9C6C at 6b551f5; `dsde.enemy_anims_run.speed_pin` computes it). Never pin it on
   the vanilla ROM.

Exact plan, Ice Mongrel (row 20) alone, action 0, Fast: `emu/plans/enemy_force.plan` (run:
`uv run python -m dsde.emu emu/plans/enemy_force.plan --rom <copy of build/dsde.nds> --save
build/emu/saves/start.SaveRAM --out <dir>`; create `<dir>/rec` first). Core lines:

```
poke u16 0x02098378 30000
poke u16 0x0209838C 30000
poke u32 0x02098374 0x3
poke u16 0x020983A0 100
execpoke 0x0202BC28 u16 0x020B85EA 20
execpoke 0x0202BC28 u16 0x020B85EC 0xFFFF      # slots 0..4, 6, 7 the same
execpoke 0x0202BC28 u16 0x020B85F6 20          # slot 5
poke u16 0x020B7838 0
poke u16 0x020B783A 0
poke u32 0x020B0010 0x73
rec ice 2 2 1 20
```

Verified: battler 9 holds row 20 after setup (`battlers` c20), and the enemy turns logged row 20 (confirmed).
A back-row flyer alone (Bealzebub, slot 1) acts normally (confirmed).

### 1.2 Bosses (confirmed for all 20)

Use the boss's own event battle instead of the formation poke: `poke u16 0x020B7838 1`,
`poke u16 0x020B783A <battle id>`, `poke u32 0x020B0010 0x73` (ids in docs/re-enemies.md and
`BOSS_BATTLES` in src/dsde/enemy_anims.py). Same row pokes; Caucus' fight pokes Orcus and Morus too, the Blue
Dragon's pokes the bubble row 156. The recorder's row filter skips the other enemies' turns.

Seven bosses do not take their action from the chance table (func_020695c0 and func_0202efdc, confirmed
in code): Gronk (every 20th round, including round 0: action 3), Zethos (action 1 or 3 by a ctx flag and the
round), Red and White Dragon (every 5th round, including round 0: action 2), Black Dragon (every 4th: action
1), Blue Dragon (every 4th round below half HP: action 2), and Dark Jian (copies Jian's command: Fight action
0, spell action 1, command 4 action 2). For these the action is also written into the actor when its action
starts: new command `execpokereg ADDR REG OFFSET KIND VALUE` at func_02068034 (called from func_02068890 in
round state 5 with r0 = the acting battler): +0xC0 action index (u32), +0x84 AI command (u16, 1 physical, 2
skill), +0x86 skill id. Exceptions measured with the chance table alone because the setup write stalled or
lost turns: Black Dragon action 0 and Blue Dragon action 1 (the summary then takes the turn that ran the
action's own script).

### 1.3 Recorder (new plan commands, emu/run_plan.lua)

- `rec NAME EVERY TURNS SHOTTURNS [ROW]`: a turn is the run of frames where battle work (0x020B8550) +0x32
  is an enemy (4..11) in battle main state 8; it ends when the actor changes (the next actor's turn starts).
  Each frame logs to NAME.rec: round state (+0x2E), battler 12 (the scratch copy every action runs on) step
  +0xCC, step counter +0xCE, script pointer +0xC8, position +0xD4/+0xD8/+0xDC, the speed level 0x020B8540, and
  work +0x36. Shots `rec/NAME_tT_fFFFF.png` (both screens) every EVERY frames of the first SHOTTURNS turns.
- `waitrec N`, `waituntil KIND ADDR VALUE N`, `pinptr KIND PTR OFFSET VALUE`, `execpoke`, `execpokereg`.

### 1.4 The sweep

- `uv run python -m dsde.enemy_anims` lists every distinct action with its static script.
- `uv run python -m dsde.enemy_anims_run run --workers 10` runs everything (151 actions x fast, normal,
  vanilla = 453 runs, about 65 minutes with 10 EmuHawk instances). Each worker has its own ROM copy and out dir
  under build/enemy_anims/_work. Rebuild build/dsde.nds first (`uv run python -m dsde.patches`).
- Re-record one action: `uv run python -m dsde.enemy_anims_run run --only 020_Ice_Mongrel_a0_attack
  --variants fast` (or `fast,normal,vanilla`).
- `uv run python -m dsde.enemy_anims_run report` prints the table below and writes
  build/enemy_anims/summary.json.

**build/ is not committed.** The recordings live only on this machine in build/enemy_anims/ (2.4 GB with the
work dirs); rerun the sweep to regenerate them.

## 2. Output per action

`build/enemy_anims/<row>_<name>_a<slot>_<kind>[_x<extra>]/`, where row is the first row that has the action,
slot the action slot 0..3, kind attack, steal, break, or skill<id>, and extra the action's extra value (low
nibble: likely a status effect, uncertain):

- `frame_NNNN.png`: both screens (256 x 384), every 2nd frame of the Fast turn, from the actor change (round
  state 1, then 5 load, 6 camera turn) to the next actor's start. `anim.gif`: those frames at 30 fps
  (palettegen stats_mode=diff, paletteuse bayer, as build/gifs).
- `fast.rec`, `normal.rec`, `vanilla.rec`: raw per-frame logs (2 turns each). `run_*.log`, `*_cmd.png`,
  `*_end.png`: plan logs and check shots.
- `timing.json`: per variant, per turn: `script`, `script_frames` (round state 7), `turn_frames`,
  `camera_frames` (states 5 and 6), `damage_wait_frames` (state 0xE), `interrupt_frames` (states 8..11, see
  4), `round_states` histogram, `steps` (step index, frames, kind from the script, the step's fixed frame
  count), `speed_level`, and `positions` ([frame in turn, round state, step, x, y, z] every frame; x and y look
  like screen pixels, z the jump height, uncertain units).
- `summary.json` (top level): one record per action with the turn used for each variant.

## 3. Action scripts (confirmed in code)

- Battler + 0xC8 holds the script, +0xCC the step, +0xCE the step counter. A step is 16 bytes: u32 flags
  (bits 0..1 kind: 1 = wait for the sprite animation to end (battler +0xFA & 0x80), 2 = fixed, ends when the
  counter reaches s16 +0xC; bit 31 last step; 0x20 / 0x80 / 0x2000000 end-of-action, hit, and wait-for-effects
  variants), u32 move or effect word, s16 +8 animation slot (battle work +0x5C + 4 * slot), s16 +0xA sound,
  s16 +0xC frames (func_02031514, func_020316e0).
- Which script (func_02068034, enemies; AI command +0x84): physical (1): action extra & 0xF0 = 0x10, 0x20,
  0x30 give 0x02095DF0, 0x02095BB0, 0x02095820; otherwise table 0x020A784C[flags & 0xFF] (0: 0x02095780,
  1: 0x02095FC0, 2: 0x020952E4, 3: 0x02095334, 4: 0x02095384, 5: 0x020955E0, 8: 0x02094FA4); Dark Jian's
  action 0 uses 0x02095C70. Skill (2 or 4): u32 at 0x02096188 + 0x10 * u16[0x02094982 + 0xC * skill]; most
  skills share the cast script 0x02094E84 (two animation steps), the spell effect itself runs in the effect
  scripts (work +0x78) and is part of the second step's wait. Druid rows 132..135 with action 1 swap in
  0x02094F74 (two targets) or 0x02095174 (three) (confirmed in code; seen only on vanilla, see 5).
- The animation behind a type-1 step is the species' battle animation: species table 0x02096EDC + 0x1C *
  species, +0x12 and +0x14 (or +0x16 / +0x18 by action flags) into work +0x50.. (func_02068034), so its length
  is set by the sprite's cel durations, not by the script (uncertain beyond that: cel data not decoded).

### What Fast changes for an enemy turn (confirmed, measured)

| Part | Normal = vanilla | Fast |
|---|---|---|
| Camera turn (states 5, 6) | 18 for a regular enemy (7 to 19 in boss fights, where the camera may already be close) | 10 (7 to 13) |
| Fixed steps (type 2) | as written (8, 30, ...) | half, plus a lag frame now and then (30 becomes 15 to 17) |
| Animation steps (type 1) | sprite cels at 1x | unchanged (enemy sprites stay at level 0) |
| Damage-number wait (state 0xE) | 1 to 42 (28 for one plain hit) | 1 (the round does not wait, P6) |

Example, generic lunge 0x02095334 (Bealzebub): Normal 8, 32, 19, 8, 32 = 99; Fast 4, 17, 20, 8, 17 = 66.

## 4. Things that are not the action

- **Interrupt frames (round states 8..11)**: the hit step can return -2 (step flag 0x80 while battle work
  +0xCA holds a battler), and the round runs states 8..11 for 25 to 100 frames before the script resumes. They
  appear mostly on actions with a nonzero extra value (status effects) and now and then on plain attacks
  (vanilla Ice Mongrel turn 2: 100 frames). Probably Jian's counter or a status reaction (uncertain). They are
  excluded from `script_frames` and listed as `interrupt_frames`.
- Jian is the only target: whole-party actions hit one character. Hits and misses both occur (the Ice Mongrel
  GIF shows "MISS"), and a hit adds Jian's hurt animation, which runs on another battler and does not change
  the enemy's script frames as far as these logs show (uncertain).
- Enemy level is set by map 6 (about 6), HP by the poke; neither changes the animation (uncertain for bosses
  whose AI depends on HP).

## 5. Differences between DE Normal and vanilla (confirmed, measured)

- Steal and break actions run 8 to 60 frames longer on vanilla: Ice Mongrel steal 379 / 387, Yeti steal 211 /
  265, Abadon break 141 / 177, Sturge steal 147 / 189, Ochu steal 117 / 177, Thanatos steal 267 / 311, Duager
  break 135 / 177, Morus steal 639 / 675 (DE Normal / vanilla). DE changed stealing and breaking (theft table,
  leave-drops-gear); which wait it shortens is uncertain (likely the "was stolen" / "broke" message).
- Druid action 1 (skills 26..29): vanilla runs the two-target script 0x02094F74 (284 to 352 frames), DE (both
  speeds) the plain cast 0x02094E84 (240 to 308 on Normal). Cause uncertain: func_02068034 picks it from the
  number of filled targets (+0x8C list), so DE's targeting changes probably leave one target where vanilla
  had two.
- Small differences of 1 to 2 frames between turns and runs are lag frames (the slot-switch hitch of
  docs/re-battle-pacing.md 2). Orcus' break (175 / 133) and Caucus' skills (2 frames) differ by outcome.
- Everything else: DE Normal = vanilla to the frame (confirmed: 135 of 150 actions identical).

## 6. Not reached

- **Dark Jian action 1 (skill 13)**: Dark Jian copies Jian's command (func_0202efdc), and Jian on Auto only
  fights; forcing it with `execpokereg` left Dark Jian on action 0 (the logged script is 0x02095C70 every
  turn). Its folder exists but shows action 0 (GIF renamed `INVALID_shows_action0_anim.gif`). Needs Jian to
  cast a spell (command 2) in a Manual battle. Static script 0x02095EC0, 16 steps, 93 fixed frames on Normal.
- **0% actions** (cumulative chance does not grow, never picked by the roll): Zethos 1 and 3, Red Dragon 2,
  White Dragon 2, Black Dragon 1, and Blue Dragon 2 happen through the round rules of 1.2 (real in play,
  recorded). Blue Dragon action 3 (skill 1) and Comet's second slot (same as its first) are never chosen by
  any code read (confirmed for func_020695c0's cases); Blue Dragon 3 was recorded anyway by forcing.

## 7. Shared scripts

Variants of a species that share flags, extra value, and skill id run the same script with the same sprite, so
they were measured once (Rows column). Scripts shared across species (Fast frames range, confirmed):

| Script | Steps (a = animation, fNN = fixed frames on Normal) | Actions | Fast | Species |
|---|---|---|---|---|
| 0x02094E84 | a a | 50 | 80 to 296 | every spell caster: Treant, Comet, Evil Earth, Asmodee, Druid, Raft, Sharif, Moran, Gronk, Caucus, Morus, Red/White/Black/Blue Dragon, Dark Jian, Gideon 2 and 3, Ignatius |
| 0x020952E4 | f8 f30 a a f30 (lunge) | 34 | 72 to 132 | Onlooker, Termite, Abadon, Insector, Ikontabipu, Hellbird, Sturge, Vitra, Quetzalcoatl, Ohainkaru, Ochu, Chupacabra, Enigma, Sharif, Moran |
| 0x02095780 | a f6 f6 a a a a f8 f8 a (hop in, hit, hop back) | 28 | 111 to 253 | Shreeker, Namia, Mad Fang, Yeti, Tick, Thanatos, Duager, Sasquatch, Armored Boar, Raft, Deuce, Zethos, Orcus, Gideon |
| 0x020955E0 | a f60 a a a a f60 a (slow glide) | 10 | 281 to 498 | Dagon, Shaitan, Phantom, Ghoula, Morus |
| 0x02095FC0 | 4 hops in (a f4 f4), attack, 4 hops back (a f6 f6) | 6 | 313 to 339 | Blob, Ice Mongrel |
| 0x02095BB0 | as 0x02095780 with two more animation steps | 4 | 169 to 327 | Deuce, Orcus, Gideon |
| 0x02095334 | f8 f30 a a f30 (lunge) | 2 | 66 to 98 | Bealzebub, Kuntukapu |
| 0x02095384 | f8 f30 a a f30 (lunge) | 2 | 112 | Gloomwing |
| 0x02095294 | a f30 f30 f30 a | 2 | 143 to 170 | Treant, Evil Earth (skills 8 and 7) |
| 0x02094F44 | a f60 a | 2 | 190 to 212 | Caucus, Blue Dragon (skill 2) |

One-action scripts: 0x02094E64 Gideon 3 skill 30; 0x02094FA4 Blue Dragon bite; 0x020950C4 Gideon 2 skill 20;
0x020951B4 White Dragon skill 23; 0x020951F4 Red Dragon skill 22; 0x02095660 Black Dragon skill 24; 0x02095820
Morus steal; 0x02095C70 Dark Jian; 0x02095D30 Zethos skill 21; 0x02095DF0 Zethos x8010.

## 8. Every action

Fast, Normal, and Vanilla: frames in round state 7 (first action-script step to the last) of the turn used
(summary.json `turn`, normally turn 1). "> 60": over the cutoff on Fast. Fast turn / camera / dmg wait: the
whole Fast turn from the actor change to the next actor's start, the camera turn in it, and the damage-number
wait. Steps: step index, Fast frames, a (animation) or f (fixed); a step's frames include its lag frames.

| Folder | Rows | Script | Fast | Normal | Vanilla | > 60 | Fast turn / camera / dmg wait | Fast steps (step:frames, a = animation, f = fixed) |
|---|---|---|---|---|---|---|---|---|
| 000_Blob_a0_attack | 0,1,2,3 | 0x02095fc0 | 313 | 353 | 353 | yes | 331 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:18a 13:70a 14:8a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:18a |
| 001_Blob_a1_attack_x3 | 1 | 0x02095fc0 | 313 | 353 | 353 | yes | 331 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:18a 13:70a 14:8a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:18a |
| 002_Blob_a1_attack_x2 | 2 | 0x02095fc0 | 313 | 353 | 353 | yes | 331 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:18a 13:70a 14:8a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:18a |
| 003_Blob_a1_attack_x4 | 3 | 0x02095fc0 | 313 | 353 | 353 | yes | 331 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:18a 13:70a 14:8a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:18a |
| 004_Onlooker_a0_attack | 4,5,6,7 | 0x020952e4 | 100 | 133 | 133 | yes | 118 / 10 / 1 | 0:4f 1:15f 2:56a 3:10a 4:15f |
| 004_Onlooker_a1_attack_x2 | 4,5 | 0x020952e4 | 100 | 133 | 133 | yes | 150 / 10 / 1 | 0:4f 1:15f 2:56a 3:10a 4:15f |
| 006_Onlooker_a1_attack_x3 | 6 | 0x020952e4 | 100 | 133 | 133 | yes | 145 / 10 / 1 | 0:4f 1:15f 2:56a 3:10a 4:15f |
| 007_Onlooker_a1_attack_x4 | 7 | 0x020952e4 | 100 | 133 | 133 | yes | 147 / 10 / 1 | 0:4f 1:15f 2:56a 3:10a 4:15f |
| 008_Shreeker_a0_attack | 8,9,10,11 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:25a 1:3f 2:3f 3:26a 4:40a 5:26a 6:26a 7:4f 8:4f 9:26a |
| 008_Shreeker_a1_attack_x3 | 8,9 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:25a 1:3f 2:3f 3:26a 4:40a 5:26a 6:26a 7:4f 8:4f 9:26a |
| 010_Shreeker_a1_attack_x6 | 10,11 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:25a 1:3f 2:3f 3:26a 4:40a 5:26a 6:26a 7:4f 8:4f 9:26a |
| 012_Namia_a0_attack | 12,13,14,15 | 0x02095780 | 141 | 155 | 155 | yes | 159 / 10 / 1 | 0:15a 1:3f 2:3f 3:16a 4:48a 5:16a 6:16a 7:4f 8:4f 9:16a |
| 012_Namia_a1_attack_x6 | 12,13,14,15 | 0x02095780 | 141 | 155 | 155 | yes | 159 / 10 / 1 | 0:15a 1:3f 2:3f 3:16a 4:48a 5:16a 6:16a 7:4f 8:4f 9:16a |
| 016_Treant_a0_skill18 | 16,17,18,19 | 0x02094e84 | 178 | 190 | 190 | yes | 196 / 10 / 1 | 0:51a 1:127a |
| 016_Treant_a1_skill8 | 16,17,18,19 | 0x02095294 | 143 | 189 | 189 | yes | 161 / 10 / 1 | 0:51a 1:15f 2:15f 3:15f 4:47a |
| 020_Ice_Mongrel_a0_attack | 20,21,22,23 | 0x02095fc0 | 339 | 379 | 379 | yes | 357 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:20a 13:40a 14:60a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:20a |
| 020_Ice_Mongrel_a1_steal | 20,21,22,23 | 0x02095fc0 | 339 | 379 | 387 | yes | 357 / 10 / 1 | 0:19a 1:2f 2:2f 3:20a 4:2f 5:2f 6:20a 7:2f 8:2f 9:20a 10:2f 11:2f 12:20a 13:40a 14:60a 15:20a 16:3f 17:3f 18:20a 19:3f 20:3f 21:20a 22:3f 23:3f 24:20a 25:3f 26:3f 27:20a |
| 024_Mad_Fang_a0_attack | 24,25,26,27 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:50a 5:40a 6:20a 7:4f 8:4f 9:20a |
| 024_Mad_Fang_a1_attack_x3 | 24,25,26,27 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:50a 5:40a 6:20a 7:4f 8:4f 9:20a |
| 028_Yeti_a0_attack | 28,29,30,31 | 0x02095780 | 197 | 211 | 211 | yes | 215 / 10 / 1 | 0:29a 1:3f 2:3f 3:30a 4:50a 5:14a 6:30a 7:4f 8:4f 9:30a |
| 028_Yeti_a1_steal | 28,29,30,31 | 0x02095780 | 197 | 211 | 265 | yes | 215 / 10 / 1 | 0:29a 1:3f 2:3f 3:30a 4:50a 5:14a 6:30a 7:4f 8:4f 9:30a |
| 032_Termite_a0_attack | 32,33,34,35 | 0x020952e4 | 96 | 129 | 129 | yes | 114 / 10 / 1 | 0:4f 1:15f 2:38a 3:24a 4:15f |
| 036_Abadon_a0_attack | 36,37,38,39 | 0x020952e4 | 108 | 141 | 141 | yes | 126 / 10 / 1 | 0:4f 1:15f 2:42a 3:32a 4:15f |
| 036_Abadon_a1_break | 36,37,38,39 | 0x020952e4 | 108 | 141 | 177 | yes | 126 / 10 / 1 | 0:4f 1:15f 2:42a 3:32a 4:15f |
| 036_Abadon_a2_attack_x6 | 36,37,38,39 | 0x020952e4 | 108 | 141 | 141 | yes | 126 / 10 / 1 | 0:4f 1:15f 2:42a 3:32a 4:15f |
| 040_Tick_a0_attack | 40,41,42,43 | 0x02095780 | 151 | 165 | 165 | yes | 169 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:42a 5:16a 6:20a 7:4f 8:4f 9:20a |
| 040_Tick_a1_attack_x2 | 40 | 0x02095780 | 151 | 165 | 165 | yes | 169 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:42a 5:16a 6:20a 7:4f 8:4f 9:20a |
| 041_Tick_a1_attack_x4 | 41,42,43 | 0x02095780 | 151 | 165 | 165 | yes | 195 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:42a 5:16a 6:20a 7:4f 8:4f 9:20a |
| 044_Bealzebub_a0_attack | 44,45,46,47 | 0x02095334 | 66 | 99 | 99 | yes | 84 / 10 / 1 | 0:4f 1:17f 2:20a 3:8a 4:17f |
| 048_Insector_a0_attack | 48,49,50,51 | 0x020952e4 | 88 | 121 | 121 | yes | 106 / 10 / 1 | 0:4f 1:17f 2:30a 3:20a 4:17f |
| 048_Insector_a1_attack_x3 | 48 | 0x020952e4 | 88 | 121 | 121 | yes | 106 / 10 / 1 | 0:4f 1:17f 2:30a 3:20a 4:17f |
| 049_Insector_a1_attack_x6 | 49,50 | 0x020952e4 | 88 | 121 | 121 | yes | 167 / 10 / 1 | 0:4f 1:17f 2:30a 3:20a 4:17f |
| 051_Insector_a1_attack_x4 | 51 | 0x020952e4 | 88 | 121 | 121 | yes | 106 / 10 / 1 | 0:4f 1:17f 2:30a 3:20a 4:17f |
| 052_Gloomwing_a0_attack | 52,53,54,55 | 0x02095384 | 112 | 145 | 145 | yes | 130 / 10 / 1 | 0:4f 1:17f 2:40a 3:36a 4:15f |
| 052_Gloomwing_a1_attack_x5 | 52,53,54,55 | 0x02095384 | 112 | 145 | 145 | yes | 157 / 10 / 1 | 0:4f 1:17f 2:40a 3:36a 4:15f |
| 056_Kuntukapu_a0_attack | 56,57,58,59 | 0x02095334 | 98 | 131 | 131 | yes | 116 / 10 / 1 | 0:4f 1:17f 2:36a 3:26a 4:15f |
| 060_Ikontabipu_a0_attack | 60,61,62,63 | 0x020952e4 | 112 | 145 | 145 | yes | 130 / 10 / 1 | 0:4f 1:17f 2:44a 3:30a 4:17f |
| 060_Ikontabipu_a1_attack_x1 | 60,61,62,63 | 0x020952e4 | 112 | 145 | 145 | yes | 181 / 10 / 1 | 0:4f 1:17f 2:44a 3:30a 4:17f |
| 064_Dagon_a0_attack | 64,65,66,67 | 0x020955e0 | 295 | 355 | 355 | yes | 313 / 10 / 1 | 0:43a 1:30f 2:44a 3:40a 4:20a 5:44a 6:30f 7:44a |
| 068_Hellbird_a0_attack | 68,69,70,71 | 0x020952e4 | 90 | 123 | 123 | yes | 108 / 10 / 1 | 0:4f 1:17f 2:30a 3:24a 4:15f |
| 072_Sturge_a0_attack | 72,73,74,75 | 0x020952e4 | 114 | 147 | 147 | yes | 132 / 10 / 1 | 0:4f 1:17f 2:52a 3:26a 4:15f |
| 072_Sturge_a1_steal | 72,73,74,75 | 0x020952e4 | 114 | 147 | 189 | yes | 132 / 10 / 1 | 0:4f 1:17f 2:52a 3:26a 4:15f |
| 072_Sturge_a2_attack_x2 | 72,73,74,75 | 0x020952e4 | 114 | 147 | 147 | yes | 132 / 10 / 1 | 0:4f 1:17f 2:52a 3:26a 4:15f |
| 076_Vitra_a0_attack | 76,77,78,79 | 0x020952e4 | 98 | 131 | 131 | yes | 116 / 10 / 1 | 0:4f 1:17f 2:44a 3:18a 4:15f |
| 080_Quetzalcoatl_a0_attack | 80,81,82,83 | 0x020952e4 | 108 | 141 | 141 | yes | 126 / 10 / 1 | 0:4f 1:17f 2:48a 3:24a 4:15f |
| 080_Quetzalcoatl_a1_break | 80,81,82,83 | 0x020952e4 | 108 | 141 | 141 | yes | 126 / 10 / 1 | 0:4f 1:17f 2:48a 3:24a 4:15f |
| 084_Comet_a0_skill16 | 84,84 | 0x02094e84 | 158 | 170 | 170 | yes | 176 / 10 / 1 | 0:99a 1:59a |
| 085_Comet_a0_skill18 | 85,85 | 0x02094e84 | 226 | 238 | 238 | yes | 244 / 10 / 1 | 0:99a 1:127a |
| 086_Comet_a0_skill19 | 86,86 | 0x02094e84 | 162 | 174 | 174 | yes | 180 / 10 / 1 | 0:99a 1:63a |
| 087_Comet_a0_skill17 | 87,87 | 0x02094e84 | 190 | 202 | 202 | yes | 208 / 10 / 1 | 0:99a 1:91a |
| 088_Ohainkaru_a0_attack | 88,89,90,91 | 0x020952e4 | 104 | 137 | 137 | yes | 122 / 10 / 1 | 0:4f 1:15f 2:48a 3:22a 4:15f |
| 088_Ohainkaru_a1_attack_x2 | 88,89,90,91 | 0x020952e4 | 104 | 137 | 137 | yes | 122 / 10 / 1 | 0:4f 1:15f 2:48a 3:22a 4:15f |
| 092_Shaitan_a0_attack | 92,93,94,95 | 0x020955e0 | 469 | 529 | 529 | yes | 487 / 10 / 1 | 0:79a 1:30f 2:80a 3:54a 4:36a 5:80a 6:30f 7:80a |
| 092_Shaitan_a1_attack_x1 | 92,93,94,95 | 0x020955e0 | 469 | 529 | 529 | yes | 487 / 10 / 1 | 0:79a 1:30f 2:80a 3:54a 4:36a 5:80a 6:30f 7:80a |
| 096_Phantom_a0_attack | 96,97,98,98,99 | 0x020955e0 | 281 | 341 | 341 | yes | 299 / 10 / 1 | 0:35a 1:30f 2:36a 3:54a 4:24a 5:36a 6:30f 7:36a |
| 096_Phantom_a1_break | 96,97,99 | 0x020955e0 | 325 | 385 | 385 | yes | 343 / 10 / 1 | 0:35a 1:30f 2:36a 3:54a 4:68a 5:36a 6:30f 7:36a |
| 096_Phantom_a2_attack_x3 | 96,97,98,99 | 0x020955e0 | 281 | 341 | 341 | yes | 325 / 10 / 1 | 0:35a 1:30f 2:36a 3:54a 4:24a 5:36a 6:30f 7:36a |
| 100_Ochu_a0_attack | 100,101,102,103 | 0x020952e4 | 84 | 117 | 117 | yes | 102 / 10 / 1 | 0:4f 1:17f 2:40a 3:8a 4:15f |
| 100_Ochu_a1_steal | 100,101,102,103 | 0x020952e4 | 84 | 117 | 177 | yes | 102 / 10 / 1 | 0:4f 1:17f 2:40a 3:8a 4:15f |
| 104_Evil_Earth_a0_skill17 | 104,105,106 | 0x02094e84 | 188 | 200 | 200 | yes | 206 / 10 / 1 | 0:97a 1:91a |
| 105_Evil_Earth_a1_skill7 | 105,106 | 0x02095294 | 170 | 195 | 195 | yes | 188 / 10 / 1 | 0:97a 1:15f 2:15f 3:15f 4:28a |
| 107_Evil_Earth_a0_skill19 | 107 | 0x02094e84 | 160 | 172 | 172 | yes | 178 / 10 / 1 | 0:97a 1:63a |
| 107_Evil_Earth_a1_skill1 | 107 | 0x02094e84 | 166 | 166 | 166 | yes | 184 / 10 / 1 | 0:97a 1:69a |
| 108_Chupacabra_a0_attack | 108,109,110,111 | 0x020952e4 | 132 | 165 | 165 | yes | 150 / 10 / 1 | 0:4f 1:17f 2:56a 3:40a 4:15f |
| 108_Chupacabra_a1_attack_x6 | 108,109,110,111 | 0x020952e4 | 132 | 165 | 165 | yes | 150 / 10 / 1 | 0:4f 1:17f 2:56a 3:40a 4:15f |
| 112_Enigma_a0_attack | 112,113,114,115 | 0x020952e4 | 72 | 105 | 105 | yes | 90 / 10 / 1 | 0:4f 1:17f 2:24a 3:12a 4:15f |
| 112_Enigma_a1_attack_x5 | 112,113,114,115 | 0x020952e4 | 72 | 105 | 105 | yes | 90 / 10 / 1 | 0:4f 1:17f 2:24a 3:12a 4:15f |
| 116_Ghoula_a0_attack | 116,117,118,119 | 0x020955e0 | 415 | 475 | 475 | yes | 433 / 10 / 1 | 0:63a 1:30f 2:64a 3:72a 4:28a 5:64a 6:30f 7:64a |
| 116_Ghoula_a1_attack_x2 | 116,117,118,119 | 0x020955e0 | 415 | 475 | 475 | yes | 433 / 10 / 1 | 0:63a 1:30f 2:64a 3:72a 4:28a 5:64a 6:30f 7:64a |
| 119_Ghoula_a2_attack_x7 | 119 | 0x020955e0 | 415 | 475 | 475 | yes | 433 / 10 / 1 | 0:63a 1:30f 2:64a 3:72a 4:28a 5:64a 6:30f 7:64a |
| 120_Thanatos_a0_attack | 120,121,122,123 | 0x02095780 | 253 | 267 | 267 | yes | 271 / 10 / 1 | 0:39a 1:3f 2:3f 3:40a 4:56a 5:24a 6:40a 7:4f 8:4f 9:40a |
| 120_Thanatos_a1_steal | 120,121,122,123 | 0x02095780 | 253 | 267 | 311 | yes | 271 / 10 / 1 | 0:39a 1:3f 2:3f 3:40a 4:56a 5:24a 6:40a 7:4f 8:4f 9:40a |
| 124_Asmodee_a0_skill17 | 124 | 0x02094e84 | 180 | 192 | 192 | yes | 198 / 10 / 1 | 0:89a 1:91a |
| 124_Asmodee_a1_skill32 | 124 | 0x02094e84 | 151 | 151 | 151 | yes | 200 / 10 / 1 | 0:89a 1:62a |
| 125_Asmodee_a0_skill16 | 125 | 0x02094e84 | 152 | 160 | 160 | yes | 170 / 10 / 1 | 0:89a 1:63a |
| 125_Asmodee_a1_skill31 | 125 | 0x02094e84 | 151 | 151 | 151 | yes | 217 / 10 / 1 | 0:89a 1:62a |
| 126_Asmodee_a0_skill18 | 126 | 0x02094e84 | 216 | 228 | 228 | yes | 234 / 10 / 1 | 0:89a 1:127a |
| 126_Asmodee_a1_skill36 | 126 | 0x02094e84 | 151 | 151 | 151 | yes | 231 / 10 / 1 | 0:89a 1:62a |
| 127_Asmodee_a0_skill19 | 127 | 0x02094e84 | 152 | 164 | 164 | yes | 170 / 10 / 1 | 0:89a 1:63a |
| 127_Asmodee_a1_skill35 | 127 | 0x02094e84 | 151 | 151 | 151 | yes | 193 / 10 / 1 | 0:89a 1:62a |
| 128_Duager_a0_attack | 128,129,130,131 | 0x02095780 | 121 | 135 | 135 | yes | 139 / 10 / 1 | 0:17a 1:3f 2:3f 3:10a 4:26a 5:26a 6:18a 7:4f 8:4f 9:10a |
| 128_Duager_a1_break | 128,129,130 | 0x02095780 | 121 | 135 | 177 | yes | 139 / 10 / 1 | 0:17a 1:3f 2:3f 3:10a 4:26a 5:26a 6:18a 7:4f 8:4f 9:10a |
| 132_Druid_a0_skill18 | 132 | 0x02094e84 | 296 | 308 | 308 | yes | 314 / 10 / 1 | 0:169a 1:127a |
| 132_Druid_a1_skill28 | 132 | 0x02094e84 | 296 | 308 | 352 | yes | 314 / 10 / 1 | 0:169a 1:127a |
| 132_Druid_a2_skill33 | 132 | 0x02094e84 | 216 | 216 | 216 | yes | 259 / 10 / 1 | 0:169a 1:47a |
| 133_Druid_a0_skill16 | 133 | 0x02094e84 | 228 | 240 | 240 | yes | 246 / 10 / 1 | 0:169a 1:59a |
| 133_Druid_a1_skill26 | 133 | 0x02094e84 | 228 | 240 | 284 | yes | 246 / 10 / 1 | 0:169a 1:59a |
| 133_Druid_a2_skill34 | 133 | 0x02094e84 | 216 | 216 | 216 | yes | 261 / 10 / 1 | 0:169a 1:47a |
| 134_Druid_a0_skill17 | 134 | 0x02094e84 | 260 | 272 | 272 | yes | 278 / 10 / 1 | 0:169a 1:91a |
| 134_Druid_a1_skill27 | 134 | 0x02094e84 | 260 | 272 | 316 | yes | 278 / 10 / 1 | 0:169a 1:91a |
| 134_Druid_a2_skill35 | 134 | 0x02094e84 | 216 | 216 | 216 | yes | 259 / 10 / 1 | 0:169a 1:47a |
| 135_Druid_a0_skill19 | 135 | 0x02094e84 | 232 | 244 | 244 | yes | 250 / 10 / 1 | 0:169a 1:63a |
| 135_Druid_a1_skill29 | 135 | 0x02094e84 | 232 | 244 | 288 | yes | 250 / 10 / 1 | 0:169a 1:63a |
| 135_Druid_a2_skill37_x7 | 135 | 0x02094e84 | 216 | 216 | 216 | yes | 273 / 10 / 1 | 0:169a 1:47a |
| 136_Sasquatch_a0_attack | 136 | 0x02095780 | 196 | 211 | 211 | yes | 311 / 13 / 1 | 0:28a 1:3f 2:3f 3:30a 4:50a 5:14a 6:30a 7:4f 8:4f 9:30a |
| 137_Armored_Boar_a0_attack | 137 | 0x02095780 | 111 | 125 | 125 | yes | 129 / 10 / 1 | 0:7a 1:3f 2:3f 3:8a 4:42a 5:24a 6:8a 7:4f 8:4f 9:8a |
| 137_Armored_Boar_a1_attack_x2003 | 137 | 0x02095780 | 111 | 125 | 125 | yes | 155 / 10 / 1 | 0:7a 1:3f 2:3f 3:8a 4:42a 5:24a 6:8a 7:4f 8:4f 9:8a |
| 138_Raft_a0_attack | 138 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:50a 5:40a 6:20a 7:4f 8:4f 9:20a |
| 138_Raft_a1_attack_x2000 | 138 | 0x02095780 | 183 | 197 | 197 | yes | 201 / 10 / 1 | 0:19a 1:3f 2:3f 3:20a 4:50a 5:40a 6:20a 7:4f 8:4f 9:20a |
| 138_Raft_a2_skill1 | 138 | 0x02094e84 | 116 | 116 | 116 | yes | 134 / 10 / 1 | 0:47a 1:69a |
| 139_Sharif_a0_attack | 139 | 0x020952e4 | 114 | 147 | 147 | yes | 132 / 10 / 1 | 0:4f 1:15f 2:48a 3:32a 4:15f |
| 139_Sharif_a1_attack_x2 | 139 | 0x020952e4 | 114 | 147 | 147 | yes | 164 / 10 / 1 | 0:4f 1:15f 2:48a 3:32a 4:15f |
| 139_Sharif_a2_skill16 | 139 | 0x02094e84 | 106 | 118 | 118 | yes | 124 / 10 / 1 | 0:47a 1:59a |
| 140_Moran_a0_attack | 140 | 0x020952e4 | 112 | 145 | 145 | yes | 130 / 10 / 1 | 0:4f 1:17f 2:52a 3:24a 4:15f |
| 140_Moran_a1_attack_x6 | 140 | 0x020952e4 | 112 | 145 | 145 | yes | 130 / 10 / 1 | 0:4f 1:17f 2:52a 3:24a 4:15f |
| 140_Moran_a2_break | 140 | 0x020952e4 | 112 | 145 | 145 | yes | 130 / 10 / 1 | 0:4f 1:17f 2:52a 3:24a 4:15f |
| 140_Moran_a3_skill16 | 140 | 0x02094e84 | 110 | 122 | 122 | yes | 128 / 10 / 1 | 0:51a 1:59a |
| 141_Deuce_a0_attack | 141 | 0x02095780 | 247 | 261 | 261 | yes | 265 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:44a 7:4f 8:4f 9:32a |
| 141_Deuce_a1_attack_x2001 | 141 | 0x02095780 | 247 | 261 | 261 | yes | 315 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:44a 7:4f 8:4f 9:32a |
| 141_Deuce_a2_attack_x20 | 141 | 0x02095bb0 | 327 | 341 | 341 | yes | 345 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:60a 7:20a 8:44a 9:4f 10:4f 11:32a |
| 141_Deuce_a3_attack_x23 | 141 | 0x02095bb0 | 327 | 341 | 341 | yes | 371 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:60a 7:20a 8:44a 9:4f 10:4f 11:32a |
| 142_Gronk_a0_skill18 | 142 | 0x02094e84 | 224 | 236 | 236 | yes | 242 / 10 / 1 | 0:97a 1:127a |
| 142_Gronk_a1_skill28 | 142 | 0x02094e84 | 224 | 236 | 236 | yes | 242 / 10 / 1 | 0:97a 1:127a |
| 142_Gronk_a2_skill1 | 142 | 0x02094e84 | 166 | 166 | 166 | yes | 184 / 10 / 1 | 0:97a 1:69a |
| 142_Gronk_a3_skill37_x7 | 142 | 0x02094e84 | 144 | 144 | 144 | yes | 201 / 10 / 1 | 0:97a 1:47a |
| 143_Zethos_a0_attack | 143 | 0x02095780 | 219 | 233 | 233 | yes | 237 / 10 / 1 | 0:31a 1:3f 2:3f 3:26a 4:50a 5:40a 6:32a 7:4f 8:4f 9:26a |
| 143_Zethos_a1_attack_x8010 | 143 | 0x02095df0 | 347 | 361 | 361 | yes | 365 / 10 / 1 | 0:31a 1:3f 2:3f 3:26a 4:50a 5:40a 6:40a 7:48a 8:40a 9:32a 10:4f 11:4f 12:26a |
| 143_Zethos_a3_skill21 | 143 | 0x02095d30 | 375 | 405 | 405 | yes | 393 / 10 / 1 | 0:31a 1:3f 2:3f 3:26a 4:106a 5:15f 6:88f 7:37a 8:32a 9:4f 10:4f 11:26a |
| 144_Caucus_a0_skill18 | 144 | 0x02094e84 | 215 | 227 | 225 | yes | 233 / 10 / 1 | 0:88a 1:127a |
| 144_Caucus_a1_skill16 | 144 | 0x02094e84 | 151 | 159 | 157 | yes | 169 / 10 / 1 | 0:88a 1:63a |
| 144_Caucus_a2_skill1 | 144 | 0x02094e84 | 158 | 158 | 158 | yes | 177 / 11 / 1 | 0:89a 1:69a |
| 144_Caucus_a3_skill2 | 144 | 0x02094f44 | 190 | 220 | 220 | yes | 237 / 11 / 1 | 0:89a 1:32f 2:69a |
| 145_Orcus_a0_attack | 145 | 0x02095780 | 119 | 133 | 133 | yes | 134 / 7 / 1 | 0:17a 1:3f 2:3f 3:10a 4:24a 5:26a 6:18a 7:4f 8:4f 9:10a |
| 145_Orcus_a1_break_x3 | 145 | 0x02095780 | 161 | 175 | 133 | yes | 202 / 7 / 1 | 0:17a 1:3f 2:3f 3:10a 4:24a 5:68a 6:18a 7:4f 8:4f 9:10a |
| 145_Orcus_a2_attack_x20 | 145 | 0x02095bb0 | 169 | 183 | 183 | yes | 184 / 7 / 1 | 0:17a 1:3f 2:3f 3:10a 4:24a 5:26a 6:24a 7:26a 8:18a 9:4f 10:4f 11:10a |
| 146_Morus_a0_skill17 | 146 | 0x02094e84 | 260 | 272 | 272 | yes | 278 / 10 / 1 | 0:169a 1:91a |
| 146_Morus_a1_attack | 146 | 0x020955e0 | 498 | 559 | 559 | yes | 613 / 13 / 1 | 0:98a 1:30f 2:80a 3:48a 4:32a 5:100a 6:30f 7:80a |
| 146_Morus_a2_steal_x8030 | 146 | 0x02095820 | 578 | 639 | 675 | yes | 693 / 13 / 1 | 0:98a 1:30f 2:80a 3:48a 4:32a 5:48a 6:32a 7:100a 8:30f 9:80a |
| 147_Red_Dragon_a0_skill16 | 147 | 0x02094e84 | 121 | 133 | 133 | yes | 169 / 11 / 1 | 0:62a 1:59a |
| 147_Red_Dragon_a1_skill32 | 147 | 0x02094e84 | 110 | 110 | 110 | yes | 189 / 10 / 1 | 0:63a 1:47a |
| 147_Red_Dragon_a2_skill22 | 147 | 0x020951f4 | 135 | 177 | 177 | yes | 181 / 9 / 1 | 0:15a 1:32f 2:16a 3:36a 4:36a |
| 148_White_Dragon_a0_skill18 | 148 | 0x02094e84 | 209 | 221 | 221 | yes | 247 / 11 / 1 | 0:82a 1:127a |
| 148_White_Dragon_a1_skill31 | 148 | 0x02094e84 | 130 | 130 | 130 | yes | 216 / 10 / 1 | 0:83a 1:47a |
| 148_White_Dragon_a2_skill23 | 148 | 0x020951b4 | 195 | 225 | 225 | yes | 235 / 13 / 1 | 0:10a 1:32f 2:37f 3:116a |
| 149_Black_Dragon_a0_skill25 | 149 | 0x02094e84 | 165 | 177 | 177 | yes | 185 / 12 / 1 | 0:41a 1:124a |
| 149_Black_Dragon_a1_skill24_x2000 | 149 | 0x02095660 | 266 | 346 | 346 | yes | 286 / 12 / 1 | 0:69a 1:40f 2:10f 3:13f 4:10f 5:10f 6:10f 7:43f 8:61a |
| 150_Blue_Dragon_a0_skill17 | 150 | 0x02094e84 | 202 | 214 | 214 | yes | 221 / 11 / 1 | 0:111a 1:91a |
| 150_Blue_Dragon_a1_attack | 150 | 0x02094fa4 | 114 | 134 | 134 | yes | 130 / 8 / 1 | 0:58a 1:20f 2:36a |
| 150_Blue_Dragon_a2_skill2 | 150 | 0x02094f44 | 212 | 242 | 242 | yes | 259 / 11 / 1 | 0:111a 1:32f 2:69a |
| 150_Blue_Dragon_a3_skill1 | 150 | 0x02094e84 | 180 | 180 | 180 | yes | 199 / 11 / 1 | 0:111a 1:69a |
| 151_Dark_Jian_a0_attack | 151 | 0x02095c70 | 203 | 217 | 217 | yes | 221 / 10 / 1 | 0:29a 1:3f 2:3f 3:18a 4:10a 5:28a 6:38a 7:18a 8:30a 9:4f 10:4f 11:18a |
| 151_Dark_Jian_a1_skill13 | 151 | ? | n/a | n/a | n/a | ? |  |  |
| 151_Dark_Jian_a2_skill1 | 151 | 0x02094e84 | 80 | 80 | 80 | yes | 98 / 10 / 1 | 0:11a 1:69a |
| 152_Gideon_a0_attack | 152 | 0x02095780 | 247 | 261 | 261 | yes | 265 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:44a 7:4f 8:4f 9:32a |
| 152_Gideon_a1_attack_x2001 | 152 | 0x02095780 | 247 | 261 | 261 | yes | 315 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:44a 7:4f 8:4f 9:32a |
| 152_Gideon_a2_attack_x20 | 152 | 0x02095bb0 | 327 | 341 | 341 | yes | 345 / 10 / 1 | 0:43a 1:3f 2:3f 3:32a 4:62a 5:20a 6:60a 7:20a 8:44a 9:4f 10:4f 11:32a |
| 153_Gideon_2_a0_skill20_x8000 | 153 | 0x020950c4 | 158 | 158 | 158 | yes | 176 / 10 / 1 | 0:47a 1:80f 2:31a |
| 153_Gideon_2_a1_skill18 | 153 | 0x02094e84 | 224 | 236 | 236 | yes | 242 / 10 / 1 | 0:97a 1:127a |
| 154_Gideon_3_a0_skill16 | 154 | 0x02094e84 | 102 | 106 | 106 | yes | 120 / 10 / 1 | 0:35a 1:67a |
| 154_Gideon_3_a1_skill30 | 154 | 0x02094e64 | 226 | 226 | 226 | yes | 285 / 10 / 1 | 0:95a 1:131a |
| 155_Ignatius_a0_skill16 | 155 | 0x02094e84 | 254 | 254 | 254 | yes | 309 / 11 / 1 | 0:137a 1:117a |
