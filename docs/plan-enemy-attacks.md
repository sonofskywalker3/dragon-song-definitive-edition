# Plan: quick enemy attack animations on Fast

Goal (Jeff): "quick simplified animations that don't look terrible." Measured baseline in
docs/re-enemy-attacks.md: all 150 recorded enemy actions run longer than the 60-frame cutoff on Fast
(shortest 66, median 166, longest 578), because Fast halves only fixed steps and leaves the enemy sprite at 1x.

Four features, all **off by default** (registered in `FEATURES`, not in `DEFAULT_FEATURES`). All of them
check the speed setting (`cave_speed_state`) at run time, so **Normal stays vanilla to the byte** whichever
ones are built in:

| Feature | Lever | What it does | Speed settings |
|---|---|---|---|
| `enemy-sprite-speed` | 2 | the acting enemy's sprite animates at level 2 (3x, Faster's sprite speed, the same level party actors already get on Fast) | Fast |
| `enemy-spell-speed` | 2b | while an enemy acts, its spell effects run faster: effect sprites 3x, effect fixed steps half, effect timer 2x | Fast |
| `enemy-short-moves` | 1 | cut copies of the movement scripts: four hops become one, 60-frame glides 20, the lunge's pause and travel shorter; every animation step kept whole | Fast and Faster |
| `enemy-quick-steps` | 1 + 3 | everything in `enemy-short-moves` plus caps: idle, landing, wind-up and cast-pose animation waits become short fixed steps, long fixed pauses inside skill scripts are cut | Fast and Faster |

`enemy-short-moves` and `enemy-quick-steps` share one hook, so build at most one of them (building both
fails loudly in the patch check). The recommended set is `enemy-sprite-speed enemy-spell-speed
enemy-quick-steps`: **120 of 150 actions under 60 frames on Fast, median 46** (from 166), longest 114 (from
578).

**Revised after the frame-by-frame review (docs/review-enemy-attacks.md, 2026-10-09):** quick-steps now keeps
every wind-up whole (capped, it cut the strike: Deuce and Gideon showed no attack) and uses short-moves' glide
cut (capped, the glide enemies popped in and out). With sprite + spell + quick-steps the fixed build measures
**99 of 150 under 60, median 55, longest 278** (the glides); the tables below are the proposal as first built.
Quick-steps now needs enemy-sprite-speed to be short.

## Results in one table

Fast script frames (round state 7, first step to last), measured by a full Fast sweep of each build:

| Build | Under 60 | Median | Longest |
|---|---|---|---|
| shipping (build/enemy_anims) | 0 | 166 | 578 |
| + enemy-sprite-speed | 4 | 101 | 318 |
| + enemy-spell-speed | 1 | 151 | 578 |
| + enemy-short-moves | 3 | 165 | 538 |
| + enemy-quick-steps | 66 | 69 | 174 |
| + sprite + spell + short-moves (levers 1 and 2) | 44 | 86 | 278 |
| **+ sprite + spell + quick-steps (all levers)** | **120** | **46** | **114** |

Per shared script (Fast frames, range over the actions that run it):

| Script | Actions | before | sprite | spell | short-moves | quick-steps | levers 1+2 | all levers |
|---|---|---|---|---|---|---|---|---|
| 0x02094e84 | 50 | 80-296 | 72-194 | 53-254 | 80-296 | 58-138 | 38-138 | 36-82 |
| 0x020952e4 | 34 | 72-132 | 48-82 | 72-132 | 55-115 | 35-67 | 31-65 | 31-47 |
| 0x02095780 | 28 | 111-253 | 61-129 | 111-253 | 111-253 | 44-98 | 61-129 | 37-98 |
| 0x020955e0 | 10 | 281-498 | 171-278 | 281-498 | 241-458 | 63-114 | 131-238 | 53-114 |
| 0x02095fc0 | 6 | 313-339 | 153-207 | 313-339 | 165-191 | 38-90 | 77-107 | 34-58 |
| 0x02095bb0 | 4 | 169-327 | 101-159 | 169-327 | 169-327 | 79-89 | 101-159 | 59-69 |
| 0x02095294 | 2 | 143-170 | 100-110 | 143-149 | 143-170 | 84 | 85-95 | 48-59 |
| 0x02095334 | 2 | 66-98 | 54-68 | 66-98 | 49-81 | 39-53 | 37-51 | 35-41 |
| 0x02095384 | 2 | 112 | 70 | 112 | 95 | 63 | 53 | 41 |
| 0x02094f44 | 2 | 190-212 | 138-148 | 178-181 | 190-212 | 94 | 104-114 | 56 |
| 0x02095df0 | 1 | 347 | 187 | 347 | 347 | 159 | 187 | 87 |
| 0x02095d30 | 1 | 375 | 295 | 331 | 375 | 167 | 251 | 111 |
| 0x02095820 | 1 | 578 | 318 | 578 | 538 | 114 | 278 | 82 |
| 0x020951f4 | 1 | 135 | 117 | 125 | 135 | 109 | 87 | 69 |
| 0x020951b4 | 1 | 195 | 187 | 120 | 195 | 174 | 112 | 99 |
| 0x02095660 | 1 | 266 | 186 | 240 | 266 | 154 | 160 | 90 |
| 0x02094fa4 | 1 | 114 | 56 | 114 | 114 | 52 | 56 | 28 |
| 0x02095c70 | 1 | 203 | 99 | 203 | 203 | 113 | 99 | 75 |
| 0x020950c4 | 1 | 158 | 120 | 120 | 158 | 124 | 82 | 70 |
| 0x02094e64 | 1 | 226 | 126 | 226 | 226 | 142 | 100 | 72 |

## How it was built and measured

```
uv run python -m dsde.patches --with enemy-sprite-speed enemy-spell-speed enemy-quick-steps --output build/enemy_cut/all.nds
uv run python -m dsde.enemy_anims_run run --variants fast --workers 10 --rom build/enemy_cut/all.nds \
    --out build/enemy_anims_cut --with enemy-sprite-speed enemy-spell-speed enemy-quick-steps
uv run python -m dsde.enemy_cuts_report --steps build/enemy_anims_cut
```

- `dsde.patches --with A B` builds the shipping set plus A and B (positional names still build exactly the
  named set).
- `dsde.enemy_anims_run run|report --rom R --out DIR --with ...`: the recorder (Stage 1's method, unchanged
  plans) on another ROM into another folder; `--with` names the extra features so the Fast pin address and
  the cut scripts are computed from the same layout. The original build/enemy_anims is untouched.
- Cut scripts live in ITCM, so the logged script pointer is an ITCM address; the analysis maps it back to
  the original (timing.json `script`, with `cut_script` = the copy's address) and reads the cut copy's steps,
  so `steps` lists the cut steps with their flags.
- `dsde.enemy_cuts_report F1 F2 ...` prints the before/after table (same turn choice as the runner's summary).
- The per-lever sweeps are in build/enemy_cut/rec_sprite, rec_spell, rec_moves, rec_quick, rec_speedmoves;
  the all-levers sweep (frames, anim.gif, timing.json per action, summary.json) in build/enemy_anims_cut,
  same folder names as build/enemy_anims. Not committed (build/).
- Each per-lever ROM is in build/enemy_cut/<name>.nds. A full Fast sweep takes 12 to 20 minutes with 10
  workers (Dark Jian action 1, unreachable, always runs into the 600 s plan timeout).

## Lever 2: enemy-sprite-speed (src/dsde/feat_enemy_speed.py)

**Change.** Hook at 0x02031FF4 in func_02031e08 (`mla r2, r1, r4, r2`, word 0xE0222491, replaced by `bl
cave_enemy_sprite`). There r1 is the speed level after feat_battle_flow's own hook at 0x02031FF0, r4 the
sprite step (0x100 for enemies), r5 the battler index, r6 the battler. On Fast, for battlers 12 and 13 (the
acting copies) whose flags have bit 3 (enemy, the same test func_02068890 uses), the level becomes at least
`ENEMY_LEVEL` = 2. Everything else (party, idle enemies, hurt reactions, effect battlers 14+) keeps its level.

**Measured.** Level 1 (2x) was tried first on six actions: Onlooker 100 -> 72, Shreeker 183 -> 103, Ice
Mongrel 339 -> 215, Shaitan 469 -> 267, Druid skill 18 296 -> 228, Gronk 224 -> 176. Level 2 (3x): 68, 99,
207, 255, 194, 174. The gain from 1 to 2 is small because the animation advances at most one cel per sprite
update (the floor): an animation step at 2x is already close to its cel count. Level 2 is kept because it
is the level party actors already get on Fast (feat_battle_flow ACTOR_BONUS), so both sides animate alike.
Evidence: every animation step in rec_sprite's timing.json shrinks by 2x to 2.5x (Shreeker step 4 40 -> 18,
Druid step 0 169 -> 67) while fixed steps keep their frames. `speed_level` in the logs stays 0: it is the
global level, the bonus is applied per battler inside the hook.

**Alone:** 4 of 150 under 60, median 101. Worst: Morus' steal 578 -> 318. Typical: a 0x02095780 hopper
183 -> 99.

**Risks.** Shared by every enemy action (no per-script knowledge). The damage number, flinch and sound are
started by the hit step's start (func_02030b44), not by the animation, so they come earlier with the
animation, in the same order. A faster cel rate makes the existing 2-frame animation-slot hitch
(docs/re-battle-pacing.md 2) easier to see; if the critic finds a stutter at the start of an animation, the
smoothness fix is a P9-style preload, not reverting the speed (follow-up, not done here).

**Look for.** Stutter or skipped poses at the start of each animation step; any party sprite changing speed
(it must not).

## Lever 2b: enemy-spell-speed (src/dsde/feat_enemy_speed.py)

**Finding.** A cast's second step (`0x82000001`, wait for animation and effects) waits on the per-target
effect scripts, not on the caster: battle work +0x78 + 4 * i holds an effect step list per target, +0x98 + 2
* i is busy until it ends (func_02031238 / func_02031408, checked by func_020314d8), and each runs on effect
battler 14 + i. The global effect timer of func_0207d1b8 (the one that reads the speed level as 1 + level /
2) changed nothing alone (Druid skill 18 step 1: 127 -> 126).

**Change.** Three hooks, all active only while an enemy (battle work +0x32 in 4..11) is the actor on Fast
(`cave_enemy_turn`):
- 0x02031FE4 (`add r2, r2, r4`, the 1x sprite step in func_02031e08): effect battlers 14..21 get two more
  steps (level 2, 3x).
- 0x020314A0 (`ldrsh ip, [r4, #0xc]`, an effect step's frame count in func_02031408): halved, rounded up.
  (The first try hooked the counter add at 0x02031438 and hung every spell: lr holds work +0xB8 there and a
  `bl` loses it. Fixed by hooking the compare instead.)
- 0x0207D1EC (`ldr r2, [r2]` in func_0207d1b8): the effect timer reads at least level 2 (2x).

**Measured.** Druid skill 18 step 1: 127 -> 71; Comet / Gronk skill 18 the same; Black Dragon skill 24 266
-> 240; Gideon 2 skill 20 158 -> 120; Caucus skill 2 190 -> 181. Ignatius skill 16 (117) did not change:
its effect is not on these paths (uncertain which).

**Risks.** Party spells are untouched (actor check). Damage numbers of a spell are started by the effect
steps (func_02030b44 from func_02031238), so they come with the faster effect, in order. Effects that
loop until the timer ends could look cut short.

**Look for.** Spell effects that end before their damage number shows, effects that look clipped, and any
party spell that got faster (it must not).

## Lever 1: enemy-short-moves (src/dsde/feat_enemy_moves.py)

**Mechanism.** Hook at 0x020688A4 (`bl func_02068034` in func_02068890, the enemy branch only, word
0xEBFFFDE2): after the game picks the actor's script (+0xC8), on Fast and Faster a table lookup swaps a
known script for a cut copy in ITCM. Normal and every party action keep the original lists. No code
compares +0xC8 with a script address (literal-pool scan: only func_02068034 and func_02068308 load script
addresses), so swapping the pointer is safe; the battler 12 copy (func_020317e8) takes the swapped pointer.

**Move semantics (func_0202fdf0, func_020303e8; confirmed in code and by position traces).** A step with
0x200000 stores the start (+0x50) and the target (+0x5C, 14/16 of the way to the target battler). A move
step (0x7000 kind, duration = its frames, +0xB0, counted by +0xB4) heads for an absolute point: the target,
or home with 0x8000. Only 0x10000 without 0x20000 makes a partial hop (current + a quarter of start to
target, arc +0x74 = 0x20), which is how 0x02095FC0 walks in four hops; its fourth hop (0x31016) aims at the
absolute target. So one hop with the fourth hop's flags (0x31016 in, 0x39016 home) and 8 frames covers the
whole distance and lands on the same contact point. A first try used 0x1016 / 0x9016 (arc 0x40, the
0x02095780 hop): the Ice Mongrel left the top of the screen mid-jump, so the cut keeps the low arc.

**Cuts** (Normal frames; Fast halves fixed steps):

| Script | Actions | Cut |
|---|---|---|
| 0x02095FC0 (Blob, Ice Mongrel) | 6 | steps 0, 1 (0x31016, 8 frames), 2, 12..15, 16 (0x39016, 8), 17, 27: one hop each way instead of four |
| 0x020955E0 glide (Dagon, Shaitan, Phantom, Ghoula, Morus) | 10 | fixed move steps 1 and 6: 60 -> 20 |
| 0x02095820 (Morus' steal) | 1 | steps 1 and 8: 60 -> 20 |
| 0x020952E4, 0x02095334, 0x02095384 lunges | 38 | pause step 0: 8 -> 2; lunge out (1) and back (4): 30 -> 16 |

**Evidence.** Ice Mongrel (rec_moves): contact point at the hit step (161, 150) = vanilla; home at the end
(64, 52) = vanilla; script 339 -> 191. Over all 150 actions (all-levers sweep), the position at the start of
every hit step and the position at the end are identical to the original recording (one exception below).

**Alone:** 3 of 150 under 60, median 165: movement is a small part of most actions. Worst affected: Morus'
steal 578 -> 538; Ice Mongrel 339 -> 191; lunges 72..132 -> 55..115.

**Risks.** The glide steps (0x10003012 / 0x1000B012) also set the battler's bit 31 (the "vanish" of the
glide: the enemy is not drawn while it glides), so a shorter glide is a shorter vanish. Lunge travel at 16
frames is still a visible dash. The hop arcs are the game's own low arc.

**Look for.** Teleports (a frame-to-frame jump of more than about 40 px outside the vanish), an enemy
leaving the screen, the enemy not back home at the end.

## Lever 3: enemy-quick-steps (src/dsde/feat_enemy_moves.py)

**Change.** Lever 1's cuts plus caps: an animation-wait step (kind 1) becomes a fixed step (kind 2) of N
frames, so its animation starts and is cut after N frames (Fast: N / 2). Hit steps (0x40 / 0xC1), the step
that can return -2 (flag 0x80, the interrupt states 8..11), wait-for-effects steps (0x2000000), the end bits
and the last step are never removed; only their position in the list changes where steps before them are
dropped. Constants: PREP 8 (crouch before a hop or glide), WINDUP 16 (attack wind-up, slot 0 seq 0), LAND 8
(settle at the end), CAST_POSE 24, PAUSE 16 (fixed pauses inside skill scripts). Dropped: the landing
animation between a hop in and the wind-up, and the crouch before the hop home.

| Script | Actions | Cut (steps kept, c = capped) |
|---|---|---|
| 0x02094E84 cast | 50 | 0c(24), 1 (spell; waits for its effects) |
| 0x020952E4 / 0x02095334 / 0x02095384 lunges | 38 | as lever 1, wind-up 2c(16) |
| 0x02095780 hop | 28 | 0c(8), 1, 2, 4c(16), 5 (hit), 7, 8, 9 land(8) |
| 0x020955E0 glide | 10 | 0c, 1 (20), 2c, 3c(16), 4 (hit), 5c, 6 (20), 7 land |
| 0x02095FC0 four hops | 6 | 0c, one hop in, 2, 13c(16), 14 (hit), one hop home, 17, 27 land |
| 0x02095BB0 two hits | 4 | 0c, 1, 2, 4c, 5 (hit 0x41), 6c, 7 (hit 0xC1), 9, 10, 11 land |
| 0x02095294 (Treant, Evil Earth skills) | 2 | 0c(24), three effect pauses 30 -> 16, 4 |
| 0x02094F44 (Caucus, Blue Dragon skill 2) | 2 | 0c(24), 1 (60 -> 16), 2 |
| one-action scripts | 10 | 0x02095DF0, 0x02095C70, 0x02095D30, 0x02095820, 0x020951F4, 0x020951B4, 0x02095660, 0x020950C4, 0x02094E64, 0x02094FA4: pose / wind-up capped, fixed pauses 16 |

The last landing step keeps the moving bit 0x10 (`land()`): the mover only advances while the current step
has it, and in Sasquatch's interrupted turn (94 interrupt frames) the hop home started a frame late and froze
7 px short of home in the air when the landing became a short fixed step. With 0x10 it finishes (checked:
end position = vanilla in every action).

**Alone:** 66 of 150 under 60, median 69.

**Risks.** Caps cut an animation mid-cel and start the next sequence: a wind-up that is cut can look like a
twitch, a cast pose cut at 24 frames (12 on Fast) may never reach its raised-hands frame for the slow
casters (Druid's 169-frame pose). Shared scripts: one cap changes every action in the row of the table above.
Hit timing: the damage number, flinch and sound start at the hit step's start, which now comes earlier, but
the order (move in, wind-up, hit, number, move home) is unchanged and the hit step itself is never capped.

**Look for.** Twitchy wind-ups, cast poses that never show the cast, an attack whose number appears before
the enemy reaches the target (it should not: contact position checked), double flinches.

## Per-frame evidence

From the all-levers sweep (build/enemy_anims_cut, positions [frame, round state, step, x, y, z] in
timing.json):

- Contact and home: for every one of the 150 actions the (x, y) at the first frame of each hit step and at
  the last script frame equals the original recording's. One exception: Black Dragon skill 24 ends at x 70
  instead of 68 (it has no hit step and never moves; its idle sway, not the script).
- Interrupt frames (states 8..11) are unchanged per action (the cut never removes the 0x80 step); they are
  excluded from the script frames as before.
- Ice Mongrel, all levers: steps 0:4f 1:4f 2:2f 3:10f 4:27a 5:4f 6:3f 7:4f (58 frames, from 339): crouch
  4, one hop 6 frames to (161, 150), wind-up 10, hit 27 (its 60-frame strike at 3x), hop home to (64, 52).

## Still over 60 with all levers, and why

| Action | Before | All levers |
|---|---|---|
|  016_Treant_a0_skill18  |  178  |  82  |
|  085_Comet_a0_skill18  |  226  |  82  |
|  087_Comet_a0_skill17  |  190  |  64  |
|  096_Phantom_a1_break  |  325  |  114  |
|  104_Evil_Earth_a0_skill17  |  188  |  64  |
|  124_Asmodee_a0_skill17  |  180  |  64  |
|  126_Asmodee_a0_skill18  |  216  |  82  |
|  132_Druid_a0_skill18  |  296  |  82  |
|  132_Druid_a1_skill28  |  296  |  82  |
|  134_Druid_a0_skill17  |  260  |  64  |
|  134_Druid_a1_skill27  |  260  |  64  |
|  142_Gronk_a0_skill18  |  224  |  82  |
|  142_Gronk_a1_skill28  |  224  |  82  |
|  143_Zethos_a1_attack_x8010  |  347  |  87  |
|  143_Zethos_a3_skill21  |  375  |  111  |
|  144_Caucus_a0_skill18  |  215  |  81  |
|  145_Orcus_a1_break_x3  |  161  |  98  |
|  145_Orcus_a2_attack_x20  |  169  |  69  |
|  146_Morus_a0_skill17  |  260  |  64  |
|  146_Morus_a2_steal_x8030  |  578  |  82  |
|  147_Red_Dragon_a2_skill22  |  135  |  69  |
|  148_White_Dragon_a0_skill18  |  209  |  81  |
|  148_White_Dragon_a2_skill23  |  195  |  99  |
|  149_Black_Dragon_a0_skill25  |  165  |  63  |
|  149_Black_Dragon_a1_skill24_x2000  |  266  |  90  |
|  150_Blue_Dragon_a0_skill17  |  202  |  64  |
|  151_Dark_Jian_a0_attack  |  203  |  75  |
|  153_Gideon_2_a0_skill20_x8000  |  158  |  70  |
|  153_Gideon_2_a1_skill18  |  224  |  82  |
|  154_Gideon_3_a1_skill30  |  226  |  72  |

- **Spells (0x02094E84 and other skill scripts):** the remaining frames are the spell effect itself
  (step 1 = 52 to 70 frames for skills 17 and 18 at 2x). Cutting further means editing the effect step lists
  (the +0x78 scripts, shared with the party's spells through the skill table) or running them at 3x, which
  makes the big spells look frantic. Not done.
- **Break actions (Phantom 1, Orcus 1):** the hit step holds 68 frames at any sprite speed (vanilla 68 too),
  so it waits on something other than the sprite, probably the "broke" message (DE changed breaking). Needs
  the message wait found; not a script cut.
- **Multi-hit attacks (Zethos x8010, Dark Jian, Orcus x20):** two or three hit steps, each kept whole.
- **Zethos skill 21, White Dragon skill 23, Black Dragon skill 24, Gideon 2 skill 20, Red Dragon skill 22:**
  fixed steps with the wait-for-effects bit; the remaining frames are their effects.

Lever 3's further halving of fixed steps was applied only to the skill scripts' long pauses (30 / 60 / 74 /
80 -> 16 or 32), since after levers 1 and 2 the fixed steps were already short everywhere else.

## Every action

Before = build/enemy_anims (shipping Fast), then each lever alone, then levers 1 + 2 (sprite + spell +
short-moves), then all levers (sprite + spell + quick-steps); "< 60" and the steps are for all levers.

| Action | Script | Before | sprite | spell | short-moves | quick-steps | levers 1+2 | all levers | < 60 | all levers: steps |
|---|---|---|---|---|---|---|---|---|---|---|
| 000_Blob_a0_attack | 0x02095fc0 | 313 | 153 | 313 | 165 | 38 | 77 | 34 | yes | 0:4f 1:4f 2:2f 3:10f 4:3a 5:4f 6:3f 7:4f |
| 001_Blob_a1_attack_x3 | 0x02095fc0 | 313 | 153 | 313 | 165 | 38 | 77 | 34 | yes | 0:4f 1:4f 2:2f 3:10f 4:3a 5:4f 6:3f 7:4f |
| 002_Blob_a1_attack_x2 | 0x02095fc0 | 313 | 153 | 313 | 165 | 38 | 77 | 34 | yes | 0:4f 1:4f 2:2f 3:10f 4:3a 5:4f 6:3f 7:4f |
| 003_Blob_a1_attack_x4 | 0x02095fc0 | 313 | 153 | 313 | 165 | 38 | 77 | 34 | yes | 0:4f 1:4f 2:2f 3:10f 4:3a 5:4f 6:3f 7:4f |
| 004_Onlooker_a0_attack | 0x020952e4 | 100 | 68 | 100 | 83 | 37 | 51 | 33 | yes | 0:1f 1:8f 2:10f 3:6a 4:8f |
| 004_Onlooker_a1_attack_x2 | 0x020952e4 | 100 | 68 | 100 | 83 | 37 | 51 | 33 | yes | 0:1f 1:8f 2:10f 3:6a 4:8f |
| 006_Onlooker_a1_attack_x3 | 0x020952e4 | 100 | 68 | 100 | 83 | 37 | 51 | 33 | yes | 0:1f 1:8f 2:10f 3:6a 4:8f |
| 007_Onlooker_a1_attack_x4 | 0x020952e4 | 100 | 68 | 100 | 83 | 37 | 51 | 33 | yes | 0:1f 1:8f 2:10f 3:6a 4:8f |
| 008_Shreeker_a0_attack | 0x02095780 | 183 | 99 | 183 | 183 | 55 | 99 | 41 | yes | 0:4f 1:3f 2:3f 3:8f 4:11a 5:4f 6:4f 7:4f |
| 008_Shreeker_a1_attack_x3 | 0x02095780 | 183 | 99 | 183 | 183 | 55 | 99 | 41 | yes | 0:4f 1:3f 2:3f 3:8f 4:11a 5:4f 6:4f 7:4f |
| 010_Shreeker_a1_attack_x6 | 0x02095780 | 183 | 99 | 183 | 183 | 55 | 99 | 41 | yes | 0:4f 1:3f 2:3f 3:8f 4:11a 5:4f 6:4f 7:4f |
| 012_Namia_a0_attack | 0x02095780 | 141 | 81 | 141 | 141 | 47 | 81 | 39 | yes | 0:4f 1:3f 2:3f 3:10f 4:7a 5:4f 6:4f 7:4f |
| 012_Namia_a1_attack_x6 | 0x02095780 | 141 | 81 | 141 | 141 | 47 | 81 | 39 | yes | 0:4f 1:3f 2:3f 3:10f 4:7a 5:4f 6:4f 7:4f |
| 016_Treant_a0_skill18 | 0x02094e84 | 178 | 154 | 122 | 178 | 138 | 98 | 82 | no | 0:12f 1:70a |
| 016_Treant_a1_skill8 | 0x02095294 | 143 | 100 | 143 | 143 | 84 | 95 | 59 | yes | 0:12f 1:8f 2:8f 3:8f 4:23a |
| 020_Ice_Mongrel_a0_attack | 0x02095fc0 | 339 | 207 | 339 | 191 | 90 | 107 | 58 | yes | 0:4f 1:4f 2:2f 3:10f 4:27a 5:4f 6:3f 7:4f |
| 020_Ice_Mongrel_a1_steal | 0x02095fc0 | 339 | 207 | 339 | 191 | 90 | 107 | 58 | yes | 0:4f 1:4f 2:2f 3:10f 4:27a 5:4f 6:3f 7:4f |
| 024_Mad_Fang_a0_attack | 0x02095780 | 183 | 101 | 183 | 183 | 71 | 101 | 49 | yes | 0:4f 1:3f 2:3f 3:10f 4:17a 5:4f 6:4f 7:4f |
| 024_Mad_Fang_a1_attack_x3 | 0x02095780 | 183 | 101 | 183 | 183 | 71 | 101 | 49 | yes | 0:4f 1:3f 2:3f 3:10f 4:17a 5:4f 6:4f 7:4f |
| 028_Yeti_a0_attack | 0x02095780 | 197 | 89 | 197 | 197 | 45 | 89 | 39 | yes | 0:4f 1:3f 2:3f 3:10f 4:7a 5:4f 6:4f 7:4f |
| 028_Yeti_a1_steal | 0x02095780 | 197 | 89 | 197 | 197 | 45 | 89 | 39 | yes | 0:4f 1:3f 2:3f 3:10f 4:7a 5:4f 6:4f 7:4f |
| 032_Termite_a0_attack | 0x020952e4 | 96 | 66 | 96 | 79 | 49 | 49 | 37 | yes | 0:1f 1:8f 2:8f 3:12a 4:8f |
| 036_Abadon_a0_attack | 0x020952e4 | 108 | 72 | 108 | 91 | 59 | 55 | 43 | yes | 0:1f 1:8f 2:10f 3:16a 4:8f |
| 036_Abadon_a1_break | 0x020952e4 | 108 | 72 | 108 | 91 | 59 | 55 | 43 | yes | 0:1f 1:8f 2:10f 3:16a 4:8f |
| 036_Abadon_a2_attack_x6 | 0x020952e4 | 108 | 72 | 108 | 91 | 59 | 55 | 43 | yes | 0:1f 1:8f 2:10f 3:16a 4:8f |
| 040_Tick_a0_attack | 0x02095780 | 151 | 93 | 151 | 151 | 45 | 93 | 37 | yes | 0:4f 1:3f 2:3f 3:8f 4:7a 5:4f 6:4f 7:4f |
| 040_Tick_a1_attack_x2 | 0x02095780 | 151 | 93 | 151 | 151 | 45 | 93 | 37 | yes | 0:4f 1:3f 2:3f 3:8f 4:7a 5:4f 6:4f 7:4f |
| 041_Tick_a1_attack_x4 | 0x02095780 | 151 | 93 | 151 | 151 | 45 | 93 | 37 | yes | 0:4f 1:3f 2:3f 3:8f 4:7a 5:4f 6:4f 7:4f |
| 044_Bealzebub_a0_attack | 0x02095334 | 66 | 54 | 66 | 49 | 39 | 37 | 35 | yes | 0:1f 1:10f 2:10f 3:4a 4:10f |
| 048_Insector_a0_attack | 0x020952e4 | 88 | 66 | 88 | 71 | 51 | 49 | 41 | yes | 0:1f 1:10f 2:10f 3:10a 4:10f |
| 048_Insector_a1_attack_x3 | 0x020952e4 | 88 | 66 | 88 | 71 | 51 | 49 | 41 | yes | 0:1f 1:10f 2:10f 3:10a 4:10f |
| 049_Insector_a1_attack_x6 | 0x020952e4 | 88 | 66 | 88 | 71 | 51 | 49 | 41 | yes | 0:1f 1:10f 2:10f 3:10a 4:10f |
| 051_Insector_a1_attack_x4 | 0x020952e4 | 88 | 66 | 88 | 71 | 51 | 49 | 41 | yes | 0:1f 1:10f 2:10f 3:10a 4:10f |
| 052_Gloomwing_a0_attack | 0x02095384 | 112 | 70 | 112 | 95 | 63 | 53 | 41 | yes | 0:1f 1:10f 2:8f 3:14a 4:8f |
| 052_Gloomwing_a1_attack_x5 | 0x02095384 | 112 | 70 | 112 | 95 | 63 | 53 | 41 | yes | 0:1f 1:10f 2:8f 3:14a 4:8f |
| 056_Kuntukapu_a0_attack | 0x02095334 | 98 | 68 | 98 | 81 | 53 | 51 | 41 | yes | 0:1f 1:10f 2:8f 3:14a 4:8f |
| 060_Ikontabipu_a0_attack | 0x020952e4 | 112 | 72 | 112 | 95 | 61 | 55 | 43 | yes | 0:1f 1:10f 2:10f 3:12a 4:10f |
| 060_Ikontabipu_a1_attack_x1 | 0x020952e4 | 112 | 72 | 112 | 95 | 61 | 55 | 43 | yes | 0:1f 1:10f 2:10f 3:12a 4:10f |
| 064_Dagon_a0_attack | 0x020955e0 | 295 | 175 | 295 | 255 | 63 | 135 | 53 | yes | 0:4f 1:10f 2:4f 3:8f 4:9a 5:4f 6:10f 7:4f |
| 068_Hellbird_a0_attack | 0x020952e4 | 90 | 64 | 90 | 73 | 51 | 47 | 39 | yes | 0:1f 1:10f 2:8f 3:12a 4:8f |
| 072_Sturge_a0_attack | 0x020952e4 | 114 | 76 | 114 | 97 | 53 | 59 | 43 | yes | 0:1f 1:10f 2:8f 3:16a 4:8f |
| 072_Sturge_a1_steal | 0x020952e4 | 114 | 76 | 114 | 97 | 53 | 59 | 43 | yes | 0:1f 1:10f 2:8f 3:16a 4:8f |
| 072_Sturge_a2_attack_x2 | 0x020952e4 | 114 | 76 | 114 | 97 | 53 | 59 | 43 | yes | 0:1f 1:10f 2:8f 3:16a 4:8f |
| 076_Vitra_a0_attack | 0x020952e4 | 98 | 66 | 98 | 81 | 45 | 49 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 080_Quetzalcoatl_a0_attack | 0x020952e4 | 108 | 64 | 108 | 91 | 51 | 47 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 080_Quetzalcoatl_a1_break | 0x020952e4 | 108 | 64 | 108 | 91 | 51 | 47 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 084_Comet_a0_skill16 | 0x02094e84 | 158 | 108 | 136 | 158 | 70 | 86 | 48 | yes | 0:12f 1:36a |
| 085_Comet_a0_skill18 | 0x02094e84 | 226 | 176 | 170 | 226 | 138 | 120 | 82 | no | 0:12f 1:70a |
| 086_Comet_a0_skill19 | 0x02094e84 | 162 | 112 | 138 | 162 | 74 | 88 | 50 | yes | 0:12f 1:38a |
| 087_Comet_a0_skill17 | 0x02094e84 | 190 | 140 | 152 | 190 | 102 | 102 | 64 | no | 0:12f 1:52a |
| 088_Ohainkaru_a0_attack | 0x020952e4 | 104 | 68 | 104 | 87 | 47 | 51 | 37 | yes | 0:1f 1:8f 2:8f 3:12a 4:8f |
| 088_Ohainkaru_a1_attack_x2 | 0x020952e4 | 104 | 68 | 104 | 87 | 47 | 51 | 37 | yes | 0:1f 1:8f 2:8f 3:12a 4:8f |
| 092_Shaitan_a0_attack | 0x020955e0 | 469 | 255 | 469 | 429 | 81 | 215 | 57 | yes | 0:4f 1:10f 2:4f 3:10f 4:11a 5:4f 6:10f 7:4f |
| 092_Shaitan_a1_attack_x1 | 0x020955e0 | 469 | 255 | 469 | 429 | 81 | 215 | 57 | yes | 0:4f 1:10f 2:4f 3:10f 4:11a 5:4f 6:10f 7:4f |
| 096_Phantom_a0_attack | 0x020955e0 | 281 | 171 | 281 | 241 | 69 | 131 | 57 | yes | 0:4f 1:10f 2:4f 3:10f 4:11a 5:4f 6:10f 7:4f |
| 096_Phantom_a1_break | 0x020955e0 | 325 | 227 | 325 | 285 | 114 | 187 | 114 | no | 0:4f 1:10f 2:4f 3:10f 4:68a 5:4f 6:10f 7:4f |
| 096_Phantom_a2_attack_x3 | 0x020955e0 | 281 | 171 | 281 | 241 | 69 | 131 | 57 | yes | 0:4f 1:10f 2:4f 3:10f 4:11a 5:4f 6:10f 7:4f |
| 100_Ochu_a0_attack | 0x020952e4 | 84 | 70 | 84 | 67 | 35 | 53 | 31 | yes | 0:1f 1:10f 2:8f 3:4a 4:8f |
| 100_Ochu_a1_steal | 0x020952e4 | 84 | 70 | 84 | 67 | 35 | 53 | 31 | yes | 0:1f 1:10f 2:8f 3:4a 4:8f |
| 104_Evil_Earth_a0_skill17 | 0x02094e84 | 188 | 128 | 150 | 188 | 102 | 90 | 64 | no | 0:12f 1:52a |
| 105_Evil_Earth_a1_skill7 | 0x02095294 | 170 | 110 | 149 | 170 | 84 | 85 | 48 | yes | 0:12f 1:8f 2:8f 3:8f 4:12a |
| 107_Evil_Earth_a0_skill19 | 0x02094e84 | 160 | 100 | 136 | 160 | 74 | 76 | 50 | yes | 0:12f 1:38a |
| 107_Evil_Earth_a1_skill1 | 0x02094e84 | 166 | 106 | 132 | 166 | 80 | 72 | 46 | yes | 0:12f 1:34a |
| 108_Chupacabra_a0_attack | 0x020952e4 | 132 | 82 | 132 | 115 | 67 | 65 | 47 | yes | 0:1f 1:10f 2:8f 3:20a 4:8f |
| 108_Chupacabra_a1_attack_x6 | 0x020952e4 | 132 | 82 | 132 | 115 | 67 | 65 | 47 | yes | 0:1f 1:10f 2:8f 3:20a 4:8f |
| 112_Enigma_a0_attack | 0x020952e4 | 72 | 48 | 72 | 55 | 39 | 31 | 31 | yes | 0:1f 1:10f 2:8f 3:4a 4:8f |
| 112_Enigma_a1_attack_x5 | 0x020952e4 | 72 | 48 | 72 | 55 | 39 | 31 | 31 | yes | 0:1f 1:10f 2:8f 3:4a 4:8f |
| 116_Ghoula_a0_attack | 0x020955e0 | 415 | 235 | 415 | 375 | 73 | 195 | 59 | yes | 0:4f 1:10f 2:4f 3:10f 4:13a 5:4f 6:10f 7:4f |
| 116_Ghoula_a1_attack_x2 | 0x020955e0 | 415 | 235 | 415 | 375 | 73 | 195 | 59 | yes | 0:4f 1:10f 2:4f 3:10f 4:13a 5:4f 6:10f 7:4f |
| 119_Ghoula_a2_attack_x7 | 0x020955e0 | 415 | 235 | 415 | 375 | 73 | 195 | 59 | yes | 0:4f 1:10f 2:4f 3:10f 4:13a 5:4f 6:10f 7:4f |
| 120_Thanatos_a0_attack | 0x02095780 | 253 | 129 | 253 | 253 | 53 | 129 | 41 | yes | 0:4f 1:3f 2:3f 3:8f 4:11a 5:4f 6:4f 7:4f |
| 120_Thanatos_a1_steal | 0x02095780 | 253 | 129 | 253 | 253 | 53 | 129 | 41 | yes | 0:4f 1:3f 2:3f 3:8f 4:11a 5:4f 6:4f 7:4f |
| 124_Asmodee_a0_skill17 | 0x02094e84 | 180 | 128 | 152 | 180 | 102 | 90 | 64 | no | 0:12f 1:52a |
| 124_Asmodee_a1_skill32 | 0x02094e84 | 151 | 84 | 151 | 151 | 73 | 63 | 37 | yes | 0:12f 1:25a |
| 125_Asmodee_a0_skill16 | 0x02094e84 | 152 | 96 | 152 | 152 | 74 | 74 | 48 | yes | 0:12f 1:36a |
| 125_Asmodee_a1_skill31 | 0x02094e84 | 151 | 84 | 151 | 151 | 73 | 63 | 37 | yes | 0:12f 1:25a |
| 126_Asmodee_a0_skill18 | 0x02094e84 | 216 | 164 | 160 | 216 | 138 | 108 | 82 | no | 0:12f 1:70a |
| 126_Asmodee_a1_skill36 | 0x02094e84 | 151 | 84 | 151 | 151 | 73 | 63 | 37 | yes | 0:12f 1:25a |
| 127_Asmodee_a0_skill19 | 0x02094e84 | 152 | 100 | 152 | 152 | 74 | 76 | 50 | yes | 0:12f 1:38a |
| 127_Asmodee_a1_skill35 | 0x02094e84 | 151 | 84 | 151 | 151 | 73 | 63 | 37 | yes | 0:12f 1:25a |
| 128_Duager_a0_attack | 0x02095780 | 121 | 75 | 121 | 121 | 57 | 75 | 47 | yes | 0:4f 1:3f 2:3f 3:10f 4:15a 5:4f 6:4f 7:4f |
| 128_Duager_a1_break | 0x02095780 | 121 | 75 | 121 | 121 | 57 | 75 | 47 | yes | 0:4f 1:3f 2:3f 3:10f 4:15a 5:4f 6:4f 7:4f |
| 132_Druid_a0_skill18 | 0x02094e84 | 296 | 194 | 240 | 296 | 138 | 138 | 82 | no | 0:12f 1:70a |
| 132_Druid_a1_skill28 | 0x02094e84 | 296 | 194 | 240 | 296 | 138 | 138 | 82 | no | 0:12f 1:70a |
| 132_Druid_a2_skill33 | 0x02094e84 | 216 | 114 | 213 | 216 | 58 | 92 | 36 | yes | 0:12f 1:24a |
| 133_Druid_a0_skill16 | 0x02094e84 | 228 | 126 | 214 | 228 | 70 | 104 | 48 | yes | 0:12f 1:36a |
| 133_Druid_a1_skill26 | 0x02094e84 | 228 | 126 | 214 | 228 | 70 | 104 | 48 | yes | 0:12f 1:36a |
| 133_Druid_a2_skill34 | 0x02094e84 | 216 | 114 | 213 | 216 | 58 | 92 | 36 | yes | 0:12f 1:24a |
| 134_Druid_a0_skill17 | 0x02094e84 | 260 | 158 | 222 | 260 | 102 | 120 | 64 | no | 0:12f 1:52a |
| 134_Druid_a1_skill27 | 0x02094e84 | 260 | 158 | 222 | 260 | 102 | 120 | 64 | no | 0:12f 1:52a |
| 134_Druid_a2_skill35 | 0x02094e84 | 216 | 114 | 213 | 216 | 58 | 92 | 36 | yes | 0:12f 1:24a |
| 135_Druid_a0_skill19 | 0x02094e84 | 232 | 130 | 214 | 232 | 74 | 106 | 50 | yes | 0:12f 1:38a |
| 135_Druid_a1_skill29 | 0x02094e84 | 232 | 130 | 214 | 232 | 74 | 106 | 50 | yes | 0:12f 1:38a |
| 135_Druid_a2_skill37_x7 | 0x02094e84 | 216 | 114 | 213 | 216 | 58 | 92 | 36 | yes | 0:12f 1:24a |
| 136_Sasquatch_a0_attack | 0x02095780 | 196 | 88 | 196 | 196 | 44 | 88 | 38 | yes | 0:3f 1:3f 2:3f 3:10f 4:7a 5:4f 6:4f 7:4f |
| 137_Armored_Boar_a0_attack | 0x02095780 | 111 | 61 | 111 | 111 | 55 | 61 | 43 | yes | 0:4f 1:3f 2:3f 3:10f 4:11a 5:4f 6:4f 7:4f |
| 137_Armored_Boar_a1_attack_x2003 | 0x02095780 | 111 | 61 | 111 | 111 | 55 | 61 | 43 | yes | 0:4f 1:3f 2:3f 3:10f 4:11a 5:4f 6:4f 7:4f |
| 138_Raft_a0_attack | 0x02095780 | 183 | 101 | 183 | 183 | 71 | 101 | 49 | yes | 0:4f 1:3f 2:3f 3:10f 4:17a 5:4f 6:4f 7:4f |
| 138_Raft_a1_attack_x2000 | 0x02095780 | 183 | 101 | 183 | 183 | 71 | 101 | 49 | yes | 0:4f 1:3f 2:3f 3:10f 4:17a 5:4f 6:4f 7:4f |
| 138_Raft_a2_skill1 | 0x02094e84 | 116 | 88 | 87 | 116 | 80 | 54 | 46 | yes | 0:12f 1:34a |
| 139_Sharif_a0_attack | 0x020952e4 | 114 | 72 | 114 | 97 | 57 | 55 | 41 | yes | 0:1f 1:8f 2:8f 3:16a 4:8f |
| 139_Sharif_a1_attack_x2 | 0x020952e4 | 114 | 72 | 114 | 97 | 57 | 55 | 41 | yes | 0:1f 1:8f 2:8f 3:16a 4:8f |
| 139_Sharif_a2_skill16 | 0x02094e84 | 106 | 80 | 84 | 106 | 70 | 58 | 48 | yes | 0:12f 1:36a |
| 140_Moran_a0_attack | 0x020952e4 | 112 | 66 | 112 | 95 | 51 | 49 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 140_Moran_a1_attack_x6 | 0x020952e4 | 112 | 66 | 112 | 95 | 51 | 49 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 140_Moran_a2_break | 0x020952e4 | 112 | 66 | 112 | 95 | 51 | 49 | 37 | yes | 0:1f 1:10f 2:8f 3:10a 4:8f |
| 140_Moran_a3_skill16 | 0x02094e84 | 110 | 78 | 88 | 110 | 70 | 56 | 48 | yes | 0:12f 1:36a |
| 141_Deuce_a0_attack | 0x02095780 | 247 | 123 | 247 | 247 | 51 | 123 | 41 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:4f 6:4f 7:4f |
| 141_Deuce_a1_attack_x2001 | 0x02095780 | 247 | 123 | 247 | 247 | 51 | 123 | 41 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:4f 6:4f 7:4f |
| 141_Deuce_a2_attack_x20 | 0x02095bb0 | 327 | 159 | 327 | 327 | 79 | 159 | 59 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:8f 6:10a 7:4f 8:4f 9:4f |
| 141_Deuce_a3_attack_x23 | 0x02095bb0 | 327 | 159 | 327 | 327 | 79 | 159 | 59 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:8f 6:10a 7:4f 8:4f 9:4f |
| 142_Gronk_a0_skill18 | 0x02094e84 | 224 | 174 | 168 | 224 | 138 | 118 | 82 | no | 0:12f 1:70a |
| 142_Gronk_a1_skill28 | 0x02094e84 | 224 | 174 | 168 | 224 | 138 | 118 | 82 | no | 0:12f 1:70a |
| 142_Gronk_a2_skill1 | 0x02094e84 | 166 | 116 | 133 | 166 | 80 | 82 | 46 | yes | 0:12f 1:34a |
| 142_Gronk_a3_skill37_x7 | 0x02094e84 | 144 | 94 | 135 | 144 | 58 | 72 | 36 | yes | 0:12f 1:24a |
| 143_Zethos_a0_attack | 0x02095780 | 219 | 123 | 219 | 219 | 71 | 123 | 47 | yes | 0:4f 1:3f 2:3f 3:10f 4:15a 5:4f 6:4f 7:4f |
| 143_Zethos_a1_attack_x8010 | 0x02095df0 | 347 | 187 | 347 | 347 | 159 | 187 | 87 | no | 0:4f 1:3f 2:3f 3:10f 4:15a 5:16a 6:8f 7:16a 8:4f 9:4f 10:4f |
| 143_Zethos_a3_skill21 | 0x02095d30 | 375 | 295 | 331 | 375 | 167 | 251 | 111 | no | 0:4f 1:3f 2:3f 3:12f 4:8f 5:44f 6:25a 7:4f 8:4f 9:4f |
| 144_Caucus_a0_skill18 | 0x02094e84 | 215 | 163 | 159 | 215 | 137 | 107 | 81 | no | 0:11f 1:70a |
| 144_Caucus_a1_skill16 | 0x02094e84 | 151 | 95 | 151 | 151 | 73 | 73 | 47 | yes | 0:11f 1:36a |
| 144_Caucus_a2_skill1 | 0x02094e84 | 158 | 106 | 149 | 158 | 80 | 72 | 46 | yes | 0:12f 1:34a |
| 144_Caucus_a3_skill2 | 0x02094f44 | 190 | 138 | 181 | 190 | 94 | 104 | 56 | yes | 0:12f 1:10f 2:34a |
| 145_Orcus_a0_attack | 0x02095780 | 119 | 73 | 119 | 119 | 55 | 73 | 45 | yes | 0:4f 1:3f 2:3f 3:8f 4:15a 5:4f 6:4f 7:4f |
| 145_Orcus_a1_break_x3 | 0x02095780 | 161 | 125 | 161 | 161 | 98 | 125 | 98 | no | 0:4f 1:3f 2:3f 3:8f 4:68a 5:4f 6:4f 7:4f |
| 145_Orcus_a2_attack_x20 | 0x02095bb0 | 169 | 101 | 169 | 169 | 89 | 101 | 69 | no | 0:4f 1:3f 2:3f 3:8f 4:15a 5:8f 6:16a 7:4f 8:4f 9:4f |
| 146_Morus_a0_skill17 | 0x02094e84 | 260 | 158 | 222 | 260 | 102 | 120 | 64 | no | 0:12f 1:52a |
| 146_Morus_a1_attack | 0x020955e0 | 498 | 278 | 498 | 458 | 74 | 238 | 58 | yes | 0:3f 1:10f 2:4f 3:8f 4:15a 5:4f 6:10f 7:4f |
| 146_Morus_a2_steal_x8030 | 0x02095820 | 578 | 318 | 578 | 538 | 114 | 278 | 82 | no | 0:3f 1:10f 2:4f 3:8f 4:15a 5:8f 6:16a 7:4f 8:10f 9:4f |
| 147_Red_Dragon_a0_skill16 | 0x02094e84 | 121 | 83 | 101 | 121 | 69 | 61 | 47 | yes | 0:11f 1:36a |
| 147_Red_Dragon_a1_skill32 | 0x02094e84 | 110 | 72 | 101 | 110 | 58 | 50 | 36 | yes | 0:12f 1:24a |
| 147_Red_Dragon_a2_skill22 | 0x020951f4 | 135 | 117 | 125 | 135 | 109 | 87 | 69 | no | 0:12f 1:10f 2:5a 3:16a 4:26a |
| 148_White_Dragon_a0_skill18 | 0x02094e84 | 209 | 153 | 153 | 209 | 137 | 97 | 81 | no | 0:11f 1:70a |
| 148_White_Dragon_a1_skill31 | 0x02094e84 | 130 | 74 | 121 | 130 | 58 | 52 | 36 | yes | 0:12f 1:24a |
| 148_White_Dragon_a2_skill23 | 0x020951b4 | 195 | 187 | 120 | 195 | 174 | 112 | 99 | no | 0:11f 1:10f 2:8f 3:70a |
| 149_Black_Dragon_a0_skill25 | 0x02094e84 | 165 | 143 | 93 | 165 | 135 | 71 | 63 | no | 0:12f 1:51a |
| 149_Black_Dragon_a1_skill24_x2000 | 0x02095660 | 266 | 186 | 240 | 266 | 154 | 160 | 90 | no | 0:14f 1:8f 2:4f 3:4f 4:7f 5:4f 6:4f 7:22f 8:23a |
| 150_Blue_Dragon_a0_skill17 | 0x02094e84 | 202 | 138 | 164 | 202 | 102 | 100 | 64 | no | 0:12f 1:52a |
| 150_Blue_Dragon_a1_attack | 0x02094fa4 | 114 | 56 | 114 | 114 | 52 | 56 | 28 | yes | 0:9f 1:8f 2:11a |
| 150_Blue_Dragon_a2_skill2 | 0x02094f44 | 212 | 148 | 178 | 212 | 94 | 114 | 56 | yes | 0:12f 1:10f 2:34a |
| 150_Blue_Dragon_a3_skill1 | 0x02094e84 | 180 | 116 | 146 | 180 | 80 | 82 | 46 | yes | 0:12f 1:34a |
| 151_Dark_Jian_a0_attack | 0x02095c70 | 203 | 99 | 203 | 203 | 113 | 99 | 75 | no | 0:4f 1:3f 2:3f 3:8f 4:13a 5:22a 6:10a 7:4f 8:4f 9:4f |
| 151_Dark_Jian_a2_skill1 | 0x02094e84 | 80 | 72 | 53 | 80 | 80 | 38 | 46 | yes | 0:12f 1:34a |
| 152_Gideon_a0_attack | 0x02095780 | 247 | 123 | 247 | 247 | 51 | 123 | 41 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:4f 6:4f 7:4f |
| 152_Gideon_a1_attack_x2001 | 0x02095780 | 247 | 123 | 247 | 247 | 51 | 123 | 41 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:4f 6:4f 7:4f |
| 152_Gideon_a2_attack_x20 | 0x02095bb0 | 327 | 159 | 327 | 327 | 79 | 159 | 59 | yes | 0:4f 1:3f 2:3f 3:10f 4:9a 5:8f 6:10a 7:4f 8:4f 9:4f |
| 153_Gideon_2_a0_skill20_x8000 | 0x020950c4 | 158 | 120 | 120 | 158 | 124 | 82 | 70 | no | 0:12f 1:42f 2:16a |
| 153_Gideon_2_a1_skill18 | 0x02094e84 | 224 | 174 | 168 | 224 | 138 | 118 | 82 | no | 0:12f 1:70a |
| 154_Gideon_3_a0_skill16 | 0x02094e84 | 102 | 72 | 102 | 102 | 78 | 50 | 48 | yes | 0:12f 1:36a |
| 154_Gideon_3_a1_skill30 | 0x02094e64 | 226 | 126 | 226 | 226 | 142 | 100 | 72 | no | 0:12f 1:60a |
| 155_Ignatius_a0_skill16 | 0x02094e84 | 254 | 104 | 254 | 254 | 128 | 86 | 52 | yes | 0:12f 1:40a |
