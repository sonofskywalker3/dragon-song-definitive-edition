# Review: do the enemy attack cuts look smooth or janky?

Critic's review (2026-10-09) of the four off-by-default features in docs/plan-enemy-attacks.md, judged against
Jeff's bar: "quick simplified animations that don't look terrible." Every verdict comes from the frames (the
PNG shots, read image by image), backed by the per-frame position logs. Recordings are Fast, Jian as the only
target, from the forcing method in docs/re-enemy-attacks.md.

## Verdict in one paragraph

**Turn on enemy-sprite-speed, enemy-spell-speed, and the fixed enemy-quick-steps, together.** The first two are
SMOOTH on all 150 actions. Quick-steps as proposed was not: its 16-frame wind-up cap cut exactly the frames
that show the attack (the claw slash, punch, swing, or spark is drawn in the last third of the wind-up), so 7
boss actions (Deuce, Gideon) and Kuntukapu showed no attack at all before the damage, 62 more attacks lost their
strike flash or popped in and out of a glide, and 21 casts lost their charge-up. The fix (committed) keeps every wind-up whole and uses
short-moves' glide cut; sprite-speed already makes those steps short. A second fix (Jeff's request after the
highlights) keeps the whole cast pose for Druid, Gronk, Gideon 2, and Blue Dragon, whose charge-up glow comes
at the very end of the pose. Re-recorded and reviewed: **87 of 150 actions under 60 frames on Fast, median 58**
(before 0 of 150, median 166; as proposed 120, median 46). The costs are the five glide species (Dagon,
Shaitan, Phantom, Ghoula, Morus), now 131 to 278 frames (before 281 to 578), and those 21 casts, now 72 to 138
(before 144 to 296).

## Verdict per feature

| Feature | Verdict | Evidence |
|---|---|---|
| enemy-sprite-speed (lever 2) | **SMOOTH: ship** | rec_sprite: every wind-up keeps its strike, only faster. No half-loaded cel at any step start in the zoomed passes (about 40 species). The existing 2-frame slot hitch (re-battle-pacing.md P9) shows at landings and in White Dragon skill 23 exactly as in the before recordings (Mad Fang before #17, Deuce before #29-30, Gideon before #112, White Dragon before #38 and #58). At 3x it is 1 shot instead of 2, so it is not made more visible. Hit number and flinch stay with the hit step |
| enemy-spell-speed (lever 2b) | **SMOOTH: ship** | No effect is cut off; every effect ends before round state 12. Number and flinch come with or just after the impact, never after the effect has faded (Comet skill 16 ring #19-23, number #25; Gronk tornado #14-41, number #42; Red Dragon fireball #39-44, number #49). The blizzard, tornado, and rock rain look brisk, not frantic |
| enemy-short-moves (lever 1) | **SMOOTH**, but superseded | Lunges (8-frame dash), one-hop Blob and Ice Mongrel, and 20-frame glides: no pops (largest per-frame move 30 px on the hop arc, glide jumps happen undrawn), contact and home points identical. With sprite and spell: 44 of 150 under 60, median 86. The fixed quick-steps now contains these same cuts |
| enemy-quick-steps as proposed (lever 3) | **FIXABLE** (8 actions JANKY as built) | Wind-up cap: strike lost on 59 lunge and hop attacks (8 of them with no visible attack at all); glide sink and emerge capped: the enemy pops out at full size and back in as a speck (11 glide actions); cast pose cap: charge-up lost on 21 casts. Details per action below |
| enemy-quick-steps fixed (this commit) | **SMOOTH** on all 150 | Re-recorded all 149 reachable actions; frame by frame on the fixed recordings of Ice Mongrel, Blob, Kuntukapu, Vitra, Deuce two-hit, Gideon, Dagon, Shaitan, and every whole-pose cast species (Druid a0 and a2, Gronk a0 and a3, Blue Dragon skills 17 and 2, Gideon 2 skills 18 and 20); positions checked on all |

**Alternative set (sprite + spell + short-moves):** SMOOTH everywhere (every strike and glide intact) but 44 of
150 under 60, median 86, because the hop species (Shreeker 99, Deuce 123) keep their landings and crouches. The
fixed quick-steps is that set plus the dropped landing/crouch and the cast and pause caps, which all looked fine.
I would turn on the fixed quick-steps, not short-moves.

## Recommendation: what to turn on, in order

1. **enemy-sprite-speed.** The biggest single win (median 166 to 101), touches nothing but the acting enemy's
   cel rate, and matches what party actors already get on Fast.
2. **enemy-spell-speed.** Spells only; brisk, nothing clipped.
3. **enemy-quick-steps (fixed).** Only together with sprite-speed: its wind-ups and glide steps are now
   animation waits, so without sprite-speed they run at 1x (40 to 62 frames each).
4. Not needed: enemy-short-moves (its cuts are inside the fixed quick-steps; the two cannot be built together).
5. Optional follow-up, if Jeff finds them slow after playing: glide sink and emerge at a 24-frame cap (would
   bring Dagon and Phantom near 100 frames; Shaitan, Ghoula, and Morus would still snap on the emerge).

Watch on hardware: Blob's wobble on Jian (now 28 frames of its 58), Chupacabra (65), the glides, and Druid's
orb hold (about 28 static frames inside its 67-frame pose; a cap can only cut the end, where the throw is).

## What was fixed (src/dsde/feat_enemy_moves.py; DEFAULT_FEATURES untouched)

| Change | Why (frames are the proposed recordings, build/enemy_cut/rec_all_v1) |
|---|---|
| Wind-up kept whole (`Cut` instead of `cap(n, WINDUP)`) in 0x02095780, 0x02095BB0 (both), 0x02095DF0 (both), 0x02095FC0 step 13, and the three lunges (now the `LUNGE` tuple) | The strike is drawn in the last third of the wind-up: at 3x the wind-up is 8 to 34 Fast frames, the cap kept 8 to 10. Deuce and Gideon showed no attack before Jian flinched (#15 f30); Kuntukapu showed nothing before MISS (#16 f32); Ice Mongrel lost its claw slash (before #78-80) |
| Glides 0x020955E0 and 0x02095820 use short-moves' cut (no caps; glide 60 -> 20 kept) | The vanish and reappear are the sprite's own sink, dissolve, or bubble animations (17 to 50 frames at 3x), capped to 4 Fast frames: Dagon v1 #7-8 pops out at full size, #14-15 emerges as a speck that snaps to full size |
| Dark Jian 0x02095C70 and Blue Dragon bite 0x02094FA4 keep the cap | Their strike is in the hit step (wind-up 8 at 3x) |
| CAST_POSE 24 -> 40 tried, then reverted to 24 | 40 showed only Druid's staff sweep (no orb, before #44-88) and Gronk's crouch (no hand sparkle, before #33-48) for 8 more frames per cast |
| Whole cast pose for rows 132-135 (Druid), 142 (Gronk), 150 (Blue Dragon), 153 (Gideon 2) in 0x02094E84, 0x02094F44, 0x020950C4 (`WHOLE_POSE_ROWS`, `WHOLE_POSE`) | At 3x (rec_sprite) the key frame sits at the end of each pose, so no shorter cap shows it: Druid's orb appears 24 frames in and is thrown 54 to 66 frames into its 67-frame pose; Gronk's and Gideon 2's hand sparkle 24 to 40 and burst 42 to 44 of 47; Blue Dragon's sparkle 27 to 41 and burst 41 of 47; Gideon 2 skill 20's slash 18 to 22 of 25 |

Re-recorded: all 149 reachable actions with the wind-up and glide fix (`--only`, 10 workers), then the 60 cast
actions again after the CAST_POSE revert, and the 60 again with the whole-pose rows: exactly the 21 casts of
those rows changed, the other 39 are frame-identical (so the row test matches nothing else).
The swap hook at 0x020688A4 now also reads the actor's row (battler +4, the field the recorder logs) and walks
a table of (script, row or any, cut copy) entries, row-specific entries first; one cut copy is built per script
of a row variant (`QUICK_ROW_VARIANTS`), so a new species needs only its row in `WHOLE_POSE_ROWS`. The proposed recordings were kept in build/enemy_cut/rec_all_v1.
Every action still hits on the same contact point and ends on its home spot (positions identical to the
original recordings at each hit step's first frame and at the last frame; the one difference is Black Dragon
skill 24 ending at x 70, not 68, its idle sway, as before).

## How it was reviewed

- Contact sheets of every shot (cropped to the battlefield, labeled shot #i, turn frame f = 2i, round state,
  step, hit step in red) for all 150 actions before and after; zoomed full-rate crops of the move in, wind-up,
  hit, and return on the frame-by-frame set; per-lever recordings (build/enemy_cut/rec_sprite, rec_spell,
  rec_moves, rec_quick, rec_speedmoves) to attribute each problem to one lever.
- Frame by frame (zoomed, every shot): 9 lunge species (Onlooker, Termite, Abadon, Bealzebub, Gloomwing,
  Chupacabra, Ikontabipu, Vitra, Ochu), 12 hop species including every hop boss (Ice Mongrel, Blob, Shreeker,
  Mad Fang, Yeti, Tick, Thanatos, Sasquatch, Deuce, Zethos, Orcus, Gideon, Dark Jian), every glide species
  (Dagon, Shaitan, Phantom attack and break, Ghoula, Morus attack and steal), Zethos skill 21, and 26 casts
  covering every boss and every skill script: 60+ actions. Every other action: its full contact sheet before
  and after, plus the side-by-side GIF.
- Position logs (fast.rec, timing.json) of all 150: per-frame deltas against their neighbors for pops, the
  position at each hit step and at the end against the original.
- Hit sync: the number or MISS appears 1 shot (2 frames) after each hit step starts and Jian's flinch starts
  with it, in every action, as proposed and fixed; multi-hit scripts flinch once per hit.
- Return and next turn: every action ends home in the idle pose of shot 0, no snap; the next actor's round
  state 1 follows cleanly. The camera (round states 5, 6 and 12 to 16) matches the before recordings.

## Not covered

- **Sound.** The recordings have no audio. The step field +0xA (documented as the sound) is copied unchanged
  into every cut step, and hit steps are never cut, so the hit's sound still starts with the hit. Its values
  (0 to 4, following crouch/hop/land/settle) look more like an animation sequence index than a sound id
  (uncertain); dropped steps (landing, crouch home) drop whatever that field started.
- **Party spells.** No party action is in these recordings; the hooks test the actor (battle work +0x32 in
  4..11) by design, but I did not see a party spell on the patched ROM.
- **Steal and break messages.** Every recorded steal and break missed except the two breaks (Orcus, Phantom),
  whose "Bandana broke!" hold is unchanged from vanilla.
- **Dark Jian action 1** (copied spell, script 0x02095EC0): unreachable by forcing (re-enemy-attacks.md 6) and
  not in the cut table, so it runs uncut and unmeasured. Known gap.
- **Faster.** Quick-steps also runs on Faster (global sprite level 2 there); not recorded.
- **Hardware.** Emulator only; nothing was played on the 3DS.

## Files (build/ is not committed: local only)

- build/enemy_anims_review/<action>.gif: before (left) and fixed after (right), same start frame, the shorter
  side holds its last frame; 150 GIFs.
- build/enemy_anims_review/as_proposed/<action>.gif: the same against the proposed (unfixed) set.
- **build/enemy_anims_review/_highlights.gif**: the ten most-met enemies back to back (Blob, Onlooker, Shreeker,
  Namia, Treant skill 8, Ice Mongrel, Mad Fang, Yeti, Termite, Bealzebub), then Druid skill 18 and Gideon 2
  skill 18 with the whole cast pose, 42 s.
- build/enemy_anims_cut: the fixed recordings; build/enemy_cut/rec_all_v1: the proposed ones.

## Every action

Fast script frames (round state 7). "As proposed" = build/enemy_cut/rec_all_v1 (sprite + spell + quick-steps
before the fix); "Fixed" = build/enemy_anims_cut. Shot numbers #i are frame_NNNN indexes of the recording named
(v1 = as proposed, rec_sprite = sprite-speed alone, levers 1+2 = rec_speedmoves, before = build/enemy_anims).

Counts as proposed: SMOOTH 59, FIXABLE 83, JANKY as built 8 (Kuntukapu, Deuce x4, Gideon x3). Fixed: SMOOTH
150 (the 21 casts that were cut past their charge-up glow, Druid x12, Gronk x4, Gideon 2 x2, Blue Dragon x3, now
keep their whole pose), FIXABLE 0, JANKY 0.

| Action | Script | Before | As proposed | Verdict as proposed | Fixed | Verdict fixed | Notes (shot #i = turn frame 2i) |
|---|---|---|---|---|---|---|---|
| 000_Blob_a0_attack | 0x02095fc0 | 313 | 34 | SMOOTH | 58 | SMOOTH | wind-up 34 at 3x capped to 10: loses a long wobble on Jian and a tiny red tick (rec_sprite #45 f90); reads fine. Fixed: wobble back (fixed #12-26), red tick #23; 34 -> 58 frames |
| 001_Blob_a1_attack_x3 | 0x02095fc0 | 313 | 34 | SMOOTH | 58 | SMOOTH | wind-up 34 at 3x capped to 10: loses a long wobble on Jian and a tiny red tick (rec_sprite #45 f90); reads fine. Fixed: wobble back (fixed #12-26), red tick #23; 34 -> 58 frames |
| 002_Blob_a1_attack_x2 | 0x02095fc0 | 313 | 34 | SMOOTH | 58 | SMOOTH | wind-up 34 at 3x capped to 10: loses a long wobble on Jian and a tiny red tick (rec_sprite #45 f90); reads fine. Fixed: wobble back (fixed #12-26), red tick #23; 34 -> 58 frames |
| 003_Blob_a1_attack_x4 | 0x02095fc0 | 313 | 34 | SMOOTH | 58 | SMOOTH | wind-up 34 at 3x capped to 10: loses a long wobble on Jian and a tiny red tick (rec_sprite #45 f90); reads fine. Fixed: wobble back (fixed #12-26), red tick #23; 34 -> 58 frames |
| 004_Onlooker_a0_attack | 0x020952e4 | 100 | 33 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (lunge step 2): white charge flash and ring lost (before f76-86; v1 wind-up #10-14 f20-28). Fixed: wind-up kept whole: strike back |
| 004_Onlooker_a1_attack_x2 | 0x020952e4 | 100 | 33 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (lunge step 2): white charge flash and ring lost (before f76-86; v1 wind-up #10-14 f20-28). Fixed: wind-up kept whole: strike back |
| 006_Onlooker_a1_attack_x3 | 0x020952e4 | 100 | 33 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (lunge step 2): same as 004 Onlooker. Fixed: wind-up kept whole: strike back |
| 007_Onlooker_a1_attack_x4 | 0x020952e4 | 100 | 33 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (lunge step 2): same as 004 Onlooker. Fixed: wind-up kept whole: strike back |
| 008_Shreeker_a0_attack | 0x02095780 | 183 | 41 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (hop step 4): yellow headbutt star lost (rec_sprite #28-31 f56-62). Fixed: wind-up kept whole: strike back |
| 008_Shreeker_a1_attack_x3 | 0x02095780 | 183 | 41 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (hop step 4): yellow headbutt star lost (rec_sprite #28-31 f56-62). Fixed: wind-up kept whole: strike back |
| 010_Shreeker_a1_attack_x6 | 0x02095780 | 183 | 41 | FIXABLE | 51 | SMOOTH | quick-steps wind-up cap (hop step 4): same as Shreeker a0. Fixed: wind-up kept whole: strike back |
| 012_Namia_a0_attack | 0x02095780 | 141 | 39 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): orange impact sparks lost (rec_sprite #24-26 f48-52). Fixed: wind-up kept whole: strike back |
| 012_Namia_a1_attack_x6 | 0x02095780 | 141 | 39 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): orange impact sparks lost (rec_sprite #24-26 f48-52). Fixed: wind-up kept whole: strike back |
| 016_Treant_a0_skill18 | 0x02094e84 | 178 | 82 | SMOOTH | 82 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 016_Treant_a1_skill8 | 0x02095294 | 143 | 59 | SMOOTH | 59 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 020_Ice_Mongrel_a0_attack | 0x02095fc0 | 339 | 58 | FIXABLE | 68 | SMOOTH | quick-steps wind-up cap (step 13): red claw slash lost (before #78-80 f156-160; levers 1+2 #27-28 f54-56); v1 shows only the cling, MISS #16 f32. Fixed: slash back at fixed #17-18 f34-36, MISS #21 f42 |
| 020_Ice_Mongrel_a1_steal | 0x02095fc0 | 339 | 58 | FIXABLE | 68 | SMOOTH | quick-steps wind-up cap (step 13): red claw slash lost (before #78-80 f156-160; levers 1+2 #27-28 f54-56); v1 shows only the cling, MISS #16 f32. Fixed: slash back at fixed #17-18 f34-36, MISS #21 f42 |
| 024_Mad_Fang_a0_attack | 0x02095780 | 183 | 49 | FIXABLE | 61 | SMOOTH | quick-steps wind-up cap (hop step 4): big red claw slash lost (rec_sprite #27-31 f54-62). Fixed: wind-up kept whole: strike back |
| 024_Mad_Fang_a1_attack_x3 | 0x02095780 | 183 | 49 | FIXABLE | 61 | SMOOTH | quick-steps wind-up cap (hop step 4): big red claw slash lost (rec_sprite #27-31 f54-62). Fixed: wind-up kept whole: strike back |
| 028_Yeti_a0_attack | 0x02095780 | 197 | 39 | FIXABLE | 57 | SMOOTH | quick-steps wind-up cap (hop step 4): club rear and swing lost, the whole attack (rec_sprite #25-31 f50-62); v1: Yeti grabs Jian and MISS. Fixed: wind-up kept whole: strike back |
| 028_Yeti_a1_steal | 0x02095780 | 197 | 39 | FIXABLE | 57 | SMOOTH | quick-steps wind-up cap (hop step 4): club rear and swing lost, the whole attack (rec_sprite #25-31 f50-62); v1: Yeti grabs Jian and MISS. Fixed: wind-up kept whole: strike back |
| 032_Termite_a0_attack | 0x020952e4 | 96 | 37 | FIXABLE | 49 | SMOOTH | quick-steps wind-up cap (lunge step 2): red pincer slash lost (before f54-62; v1 wind-up #10-13). Fixed: wind-up kept whole: strike back |
| 036_Abadon_a0_attack | 0x020952e4 | 108 | 43 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): red claw slash lost (levers 1+2 #18-20 f36-40; v1 never shows it). Fixed: wind-up kept whole: strike back |
| 036_Abadon_a1_break | 0x020952e4 | 108 | 43 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): red claw slash lost (levers 1+2 #18-20 f36-40; v1 never shows it). Fixed: wind-up kept whole: strike back |
| 036_Abadon_a2_attack_x6 | 0x020952e4 | 108 | 43 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): red claw slash lost (levers 1+2 #18-20 f36-40; v1 never shows it). Fixed: wind-up kept whole: strike back |
| 040_Tick_a0_attack | 0x02095780 | 151 | 37 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): red claw slashes lost (rec_sprite #27-30 f54-60). Fixed: wind-up kept whole: strike back |
| 040_Tick_a1_attack_x2 | 0x02095780 | 151 | 37 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): red claw slashes lost (rec_sprite #27-30 f54-60). Fixed: wind-up kept whole: strike back |
| 041_Tick_a1_attack_x4 | 0x02095780 | 151 | 37 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): same as Tick a0. Fixed: wind-up kept whole: strike back |
| 044_Bealzebub_a0_attack | 0x02095334 | 66 | 35 | SMOOTH | 37 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 048_Insector_a0_attack | 0x020952e4 | 88 | 41 | SMOOTH | 49 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 048_Insector_a1_attack_x3 | 0x020952e4 | 88 | 41 | SMOOTH | 49 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 049_Insector_a1_attack_x6 | 0x020952e4 | 88 | 41 | SMOOTH | 49 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 051_Insector_a1_attack_x4 | 0x020952e4 | 88 | 41 | SMOOTH | 49 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 052_Gloomwing_a0_attack | 0x02095384 | 112 | 41 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (lunge step 2): raised wings and pink sparkles lost (levers 1+2 #17-19 f34-38). Fixed: wind-up kept whole: strike back |
| 052_Gloomwing_a1_attack_x5 | 0x02095384 | 112 | 41 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (lunge step 2): raised wings and pink sparkles lost (levers 1+2 #17-19 f34-38). Fixed: wind-up kept whole: strike back |
| 056_Kuntukapu_a0_attack | 0x02095334 | 98 | 41 | JANKY as built | 51 | SMOOTH | quick-steps wind-up cap: hidden behind Jian, its spark burst (before f60-68) is its only visible attack; v1 shows nothing before MISS at #16 f32. Fixed: spark burst back at fixed #17-19, MISS #21 |
| 060_Ikontabipu_a0_attack | 0x020952e4 | 112 | 43 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #19-21 f38-42). Fixed: wind-up kept whole: strike back |
| 060_Ikontabipu_a1_attack_x1 | 0x020952e4 | 112 | 43 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #19-21 f38-42). Fixed: wind-up kept whole: strike back |
| 064_Dagon_a0_attack | 0x020955e0 | 295 | 53 | FIXABLE | 135 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-8, #14-15, #25-26, #32-33; orange crescent and burst lost (before #78-84). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 068_Hellbird_a0_attack | 0x020952e4 | 90 | 39 | FIXABLE | 47 | SMOOTH | quick-steps wind-up cap (lunge step 2): minor: small red peck flash lost (levers 1+2 #16 f32). Fixed: wind-up kept whole: strike back |
| 072_Sturge_a0_attack | 0x020952e4 | 114 | 43 | FIXABLE | 59 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #20-21 f40-42). Fixed: wind-up kept whole: strike back |
| 072_Sturge_a1_steal | 0x020952e4 | 114 | 43 | FIXABLE | 59 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #20-21 f40-42). Fixed: wind-up kept whole: strike back |
| 072_Sturge_a2_attack_x2 | 0x020952e4 | 114 | 43 | FIXABLE | 59 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #20-21 f40-42). Fixed: wind-up kept whole: strike back |
| 076_Vitra_a0_attack | 0x020952e4 | 98 | 37 | FIXABLE | 49 | SMOOTH | quick-steps wind-up cap (lunge step 2): large orange swipe arc and burst lost (before f64-74). Fixed: swipe arc and burst back (fixed #18-20), number #21 |
| 080_Quetzalcoatl_a0_attack | 0x020952e4 | 108 | 37 | FIXABLE | 47 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #17-20 f34-40). Fixed: wind-up kept whole: strike back |
| 080_Quetzalcoatl_a1_break | 0x020952e4 | 108 | 37 | FIXABLE | 47 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #17-20 f34-40). Fixed: wind-up kept whole: strike back |
| 084_Comet_a0_skill16 | 0x02094e84 | 158 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 085_Comet_a0_skill18 | 0x02094e84 | 226 | 82 | SMOOTH | 82 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 086_Comet_a0_skill19 | 0x02094e84 | 162 | 50 | SMOOTH | 50 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 087_Comet_a0_skill17 | 0x02094e84 | 190 | 64 | SMOOTH | 64 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 088_Ohainkaru_a0_attack | 0x020952e4 | 104 | 37 | SMOOTH | 51 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 088_Ohainkaru_a1_attack_x2 | 0x020952e4 | 104 | 37 | SMOOTH | 51 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 092_Shaitan_a0_attack | 0x020955e0 | 469 | 57 | FIXABLE | 215 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-9, #15-16, #26-28, #34-35; red wing flare lost (before #124). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 092_Shaitan_a1_attack_x1 | 0x020955e0 | 469 | 57 | FIXABLE | 215 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-9, #15-16, #26-28, #34-35; red wing flare lost (before #124). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 096_Phantom_a0_attack | 0x020955e0 | 281 | 57 | FIXABLE | 131 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-9, #15-16, #27-28, #34-35; red claw lost (before #78-81). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 096_Phantom_a1_break | 0x020955e0 | 325 | 114 | FIXABLE | 187 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: as Phantom a0; the 68-frame hit step holds on "Bandana broke!" (v1 #20-52), as vanilla. Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 096_Phantom_a2_attack_x3 | 0x020955e0 | 281 | 57 | FIXABLE | 131 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: same as Phantom a0. Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 100_Ochu_a0_attack | 0x020952e4 | 84 | 31 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (lunge step 2): rise-and-slam and burst lost (levers 1+2 #17-26 f34-52); the shell just touches Jian. Fixed: wind-up kept whole: strike back |
| 100_Ochu_a1_steal | 0x020952e4 | 84 | 31 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (lunge step 2): rise-and-slam and burst lost (levers 1+2 #17-26 f34-52); the shell just touches Jian. Fixed: wind-up kept whole: strike back |
| 104_Evil_Earth_a0_skill17 | 0x02094e84 | 188 | 64 | SMOOTH | 64 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 105_Evil_Earth_a1_skill7 | 0x02095294 | 170 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 107_Evil_Earth_a0_skill19 | 0x02094e84 | 160 | 50 | SMOOTH | 50 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 107_Evil_Earth_a1_skill1 | 0x02094e84 | 166 | 46 | SMOOTH | 46 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 108_Chupacabra_a0_attack | 0x020952e4 | 132 | 47 | FIXABLE | 65 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #21-25 f42-50); fixed it runs 65 (over 60). Fixed: wind-up kept whole: strike back |
| 108_Chupacabra_a1_attack_x6 | 0x020952e4 | 132 | 47 | FIXABLE | 65 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #21-25 f42-50); fixed it runs 65 (over 60). Fixed: wind-up kept whole: strike back |
| 112_Enigma_a0_attack | 0x020952e4 | 72 | 31 | SMOOTH | 31 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 112_Enigma_a1_attack_x5 | 0x020952e4 | 72 | 31 | SMOOTH | 31 | SMOOTH | 3x wind-up already about as short as the cap; nothing visible lost |
| 116_Ghoula_a0_attack | 0x020955e0 | 415 | 59 | FIXABLE | 195 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-8, #15-16, #28-29, #35-36; cocoon skipped, scythe arc lost (before #116-120). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 116_Ghoula_a1_attack_x2 | 0x020955e0 | 415 | 59 | FIXABLE | 195 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #7-8, #15-16, #28-29, #35-36; cocoon skipped, scythe arc lost (before #116-120). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 119_Ghoula_a2_attack_x7 | 0x020955e0 | 415 | 59 | FIXABLE | 195 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: same as Ghoula a0. Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 120_Thanatos_a0_attack | 0x02095780 | 253 | 41 | FIXABLE | 57 | SMOOTH | quick-steps wind-up cap (hop step 4): red slash lost (rec_sprite #37-40 f74-80). Fixed: wind-up kept whole: strike back |
| 120_Thanatos_a1_steal | 0x02095780 | 253 | 41 | FIXABLE | 57 | SMOOTH | quick-steps wind-up cap (hop step 4): red slash lost (rec_sprite #37-40 f74-80). Fixed: wind-up kept whole: strike back |
| 124_Asmodee_a0_skill17 | 0x02094e84 | 180 | 64 | SMOOTH | 64 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 124_Asmodee_a1_skill32 | 0x02094e84 | 151 | 37 | SMOOTH | 37 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 125_Asmodee_a0_skill16 | 0x02094e84 | 152 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 125_Asmodee_a1_skill31 | 0x02094e84 | 151 | 37 | SMOOTH | 37 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 126_Asmodee_a0_skill18 | 0x02094e84 | 216 | 82 | SMOOTH | 82 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 126_Asmodee_a1_skill36 | 0x02094e84 | 151 | 37 | SMOOTH | 37 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 127_Asmodee_a0_skill19 | 0x02094e84 | 152 | 50 | SMOOTH | 50 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 127_Asmodee_a1_skill35 | 0x02094e84 | 151 | 37 | SMOOTH | 37 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 128_Duager_a0_attack | 0x02095780 | 121 | 47 | SMOOTH | 51 | SMOOTH | strike lives in the hit step (kept whole) |
| 128_Duager_a1_break | 0x02095780 | 121 | 47 | SMOOTH | 51 | SMOOTH | strike lives in the hit step (kept whole) |
| 132_Druid_a0_skill18 | 0x02094e84 | 296 | 82 | FIXABLE | 138 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 132_Druid_a1_skill28 | 0x02094e84 | 296 | 82 | FIXABLE | 138 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 132_Druid_a2_skill33 | 0x02094e84 | 216 | 36 | FIXABLE | 92 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 133_Druid_a0_skill16 | 0x02094e84 | 228 | 48 | FIXABLE | 104 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 133_Druid_a1_skill26 | 0x02094e84 | 228 | 48 | FIXABLE | 104 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 133_Druid_a2_skill34 | 0x02094e84 | 216 | 36 | FIXABLE | 92 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 134_Druid_a0_skill17 | 0x02094e84 | 260 | 64 | FIXABLE | 120 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 134_Druid_a1_skill27 | 0x02094e84 | 260 | 64 | FIXABLE | 120 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 134_Druid_a2_skill35 | 0x02094e84 | 216 | 36 | FIXABLE | 92 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 135_Druid_a0_skill19 | 0x02094e84 | 232 | 50 | FIXABLE | 106 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 135_Druid_a1_skill29 | 0x02094e84 | 232 | 50 | FIXABLE | 106 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 135_Druid_a2_skill37_x7 | 0x02094e84 | 216 | 36 | FIXABLE | 92 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: the blue orb charge and throw (before #44-88) never show; the staff sweeps twice, then the spell. Fixed: whole pose for rows 132-135 (67 Fast frames at 3x): orb #17-31, throw #32-38, then the spell (132 a0); number and flinch after the effect as before |
| 136_Sasquatch_a0_attack | 0x02095780 | 196 | 38 | FIXABLE | 56 | SMOOTH | quick-steps wind-up cap (hop step 4): rear-up and red slash lost (rec_sprite #26-32 f52-64). Fixed: wind-up kept whole: strike back |
| 137_Armored_Boar_a0_attack | 0x02095780 | 111 | 43 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): minor: big spark burst shortened to a small spark (rec_sprite #19-23 f38-46). Fixed: wind-up kept whole: strike back |
| 137_Armored_Boar_a1_attack_x2003 | 0x02095780 | 111 | 43 | FIXABLE | 53 | SMOOTH | quick-steps wind-up cap (hop step 4): minor: big spark burst shortened to a small spark (rec_sprite #19-23 f38-46). Fixed: wind-up kept whole: strike back |
| 138_Raft_a0_attack | 0x02095780 | 183 | 49 | FIXABLE | 61 | SMOOTH | quick-steps wind-up cap (hop step 4): red slash lost (rec_sprite #27-31 f54-62). Fixed: wind-up kept whole: strike back |
| 138_Raft_a1_attack_x2000 | 0x02095780 | 183 | 49 | FIXABLE | 61 | SMOOTH | quick-steps wind-up cap (hop step 4): same as Raft a0. Fixed: wind-up kept whole: strike back |
| 138_Raft_a2_skill1 | 0x02094e84 | 116 | 46 | SMOOTH | 46 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 139_Sharif_a0_attack | 0x020952e4 | 114 | 41 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): big red tail slash lost (levers 1+2 #18-21). Fixed: wind-up kept whole: strike back |
| 139_Sharif_a1_attack_x2 | 0x020952e4 | 114 | 41 | FIXABLE | 55 | SMOOTH | quick-steps wind-up cap (lunge step 2): same as Sharif a0. Fixed: wind-up kept whole: strike back |
| 139_Sharif_a2_skill16 | 0x02094e84 | 106 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 140_Moran_a0_attack | 0x020952e4 | 112 | 37 | FIXABLE | 49 | SMOOTH | quick-steps wind-up cap (lunge step 2): red slash lost (levers 1+2 #17-21). Fixed: wind-up kept whole: strike back |
| 140_Moran_a1_attack_x6 | 0x020952e4 | 112 | 37 | FIXABLE | 49 | SMOOTH | quick-steps wind-up cap (lunge step 2): same as Moran a0. Fixed: wind-up kept whole: strike back |
| 140_Moran_a2_break | 0x020952e4 | 112 | 37 | FIXABLE | 49 | SMOOTH | quick-steps wind-up cap (lunge step 2): same as Moran a0. Fixed: wind-up kept whole: strike back |
| 140_Moran_a3_skill16 | 0x02094e84 | 110 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 141_Deuce_a0_attack | 0x02095780 | 247 | 41 | JANKY as built | 59 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 141_Deuce_a1_attack_x2001 | 0x02095780 | 247 | 41 | JANKY as built | 59 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 141_Deuce_a2_attack_x20 | 0x02095bb0 | 327 | 59 | JANKY as built | 95 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 141_Deuce_a3_attack_x23 | 0x02095bb0 | 327 | 59 | JANKY as built | 95 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 142_Gronk_a0_skill18 | 0x02094e84 | 224 | 82 | FIXABLE | 118 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: glowing-hand charge lost (before #33-51); the boss just leans. Fixed: whole pose for rows 142 and 153 (47 at 3x): hand sparkle #19-25 and burst #26 (Gronk a0, Gideon 2 a1), then the spell; flinch #60 |
| 142_Gronk_a1_skill28 | 0x02094e84 | 224 | 82 | FIXABLE | 118 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: glowing-hand charge lost (before #33-51); the boss just leans. Fixed: whole pose for rows 142 and 153 (47 at 3x): hand sparkle #19-25 and burst #26 (Gronk a0, Gideon 2 a1), then the spell; flinch #60 |
| 142_Gronk_a2_skill1 | 0x02094e84 | 166 | 46 | FIXABLE | 82 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: glowing-hand charge lost (before #33-51); the boss just leans. Fixed: whole pose for rows 142 and 153 (47 at 3x): hand sparkle #19-25 and burst #26 (Gronk a0, Gideon 2 a1), then the spell; flinch #60 |
| 142_Gronk_a3_skill37_x7 | 0x02094e84 | 144 | 36 | FIXABLE | 72 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: glowing-hand charge lost (before #33-51); the boss just leans. Fixed: whole pose for rows 142 and 153 (47 at 3x): hand sparkle #19-25 and burst #26 (Gronk a0, Gideon 2 a1), then the spell; flinch #60 |
| 143_Zethos_a0_attack | 0x02095780 | 219 | 47 | FIXABLE | 71 | SMOOTH | quick-steps wind-up cap (hop step 4): blue axe swing lost (rec_sprite #37-40 f74-80); only glints at v1 f24-28. Fixed: wind-up kept whole: strike back |
| 143_Zethos_a1_attack_x8010 | 0x02095df0 | 347 | 87 | FIXABLE | 135 | SMOOTH | quick-steps wind-up cap (hop step 4): both axe swings lost (rec_sprite f74-80, f138-142). Fixed: wind-up kept whole: strike back |
| 143_Zethos_a3_skill21 | 0x02095d30 | 375 | 111 | SMOOTH | 111 | SMOOTH | cast pose cap 24 still reaches the raised arm; the lightning finishes before the orb shrinks (v1 #34-53) |
| 144_Caucus_a0_skill18 | 0x02094e84 | 215 | 81 | SMOOTH | 81 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 144_Caucus_a1_skill16 | 0x02094e84 | 151 | 47 | SMOOTH | 47 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 144_Caucus_a2_skill1 | 0x02094e84 | 158 | 46 | SMOOTH | 46 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 144_Caucus_a3_skill2 | 0x02094f44 | 190 | 56 | SMOOTH | 56 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 145_Orcus_a0_attack | 0x02095780 | 119 | 45 | SMOOTH | 49 | SMOOTH | strike lives in the hit step (kept whole) |
| 145_Orcus_a1_break_x3 | 0x02095780 | 161 | 98 | SMOOTH | 101 | SMOOTH | strike in the hit step; the 68-frame hold is the "Bandana broke!" message, as in vanilla (not a lever) |
| 145_Orcus_a2_attack_x20 | 0x02095bb0 | 169 | 69 | SMOOTH | 77 | SMOOTH | strike lives in the hit step (kept whole) |
| 146_Morus_a0_skill17 | 0x02094e84 | 260 | 64 | SMOOTH | 64 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 146_Morus_a1_attack | 0x020955e0 | 498 | 58 | FIXABLE | 238 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: v1 #8-9: vanishes with no bubble; the bubble at Jian is cut to two shots (#14-15). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 146_Morus_a2_steal_x8030 | 0x02095820 | 578 | 82 | FIXABLE | 278 | SMOOTH | quick-steps caps the sink and emerge (PREP / LAND 8; the vanish is the sprite's own animation, 17 to 50 frames at 3x) and the wind-up: the enemy pops out at full size and back in as a speck, strike flash lost: as Morus a1 plus #88-89; both hits keep their sparks; no steal message in this turn (both missed). Fixed: lever 1's glide cut (every animation step whole): full sink, invisible 10-frame glide, full emerge, strike (Dagon fixed #7-15, #21-31, #38-41; Shaitan wing flare #59-62); longer, 135 to 278 frames |
| 147_Red_Dragon_a0_skill16 | 0x02094e84 | 121 | 47 | SMOOTH | 47 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 147_Red_Dragon_a1_skill32 | 0x02094e84 | 110 | 36 | SMOOTH | 36 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 147_Red_Dragon_a2_skill22 | 0x020951f4 | 135 | 69 | SMOOTH | 69 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 148_White_Dragon_a0_skill18 | 0x02094e84 | 209 | 81 | SMOOTH | 81 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 148_White_Dragon_a1_skill31 | 0x02094e84 | 130 | 36 | SMOOTH | 36 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 148_White_Dragon_a2_skill23 | 0x020951b4 | 195 | 99 | SMOOTH | 99 | SMOOTH | one torn frame v1 #33 (f66): the existing slot hitch; the before has it twice (#38, #58) |
| 149_Black_Dragon_a0_skill25 | 0x02094e84 | 165 | 63 | SMOOTH | 63 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 149_Black_Dragon_a1_skill24_x2000 | 0x02095660 | 266 | 90 | SMOOTH | 90 | SMOOTH | ends at x 70, not 68: its idle sway, no visible snap |
| 150_Blue_Dragon_a0_skill17 | 0x02094e84 | 202 | 64 | FIXABLE | 100 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: mouth sparkle lost (before #50-56). Fixed: whole pose for row 150 (47 at 3x): mouth sparkle #20-27, burst #26 (skill 17; skill 2 #37-41), then the spell |
| 150_Blue_Dragon_a1_attack | 0x02094fa4 | 114 | 28 | SMOOTH | 28 | SMOOTH | bubbles still on screen at the turn end, as before (#18-21 against before #61-64) |
| 150_Blue_Dragon_a2_skill2 | 0x02094f44 | 212 | 56 | FIXABLE | 92 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: mouth sparkle lost (before #50-56). Fixed: whole pose for row 150 (47 at 3x): mouth sparkle #20-27, burst #26 (skill 17; skill 2 #37-41), then the spell |
| 150_Blue_Dragon_a3_skill1 | 0x02094e84 | 180 | 46 | FIXABLE | 82 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: mouth sparkle lost (before #50-56). Fixed: whole pose for row 150 (47 at 3x): mouth sparkle #20-27, burst #26 (skill 17; skill 2 #37-41), then the spell |
| 151_Dark_Jian_a0_attack | 0x02095c70 | 203 | 75 | SMOOTH | 75 | SMOOTH | strike lives in the hit step (kept whole) |
| 151_Dark_Jian_a2_skill1 | 0x02094e84 | 80 | 46 | SMOOTH | 46 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 152_Gideon_a0_attack | 0x02095780 | 247 | 41 | JANKY as built | 59 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 152_Gideon_a1_attack_x2001 | 0x02095780 | 247 | 41 | JANKY as built | 59 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 152_Gideon_a2_attack_x20 | 0x02095bb0 | 327 | 59 | JANKY as built | 95 | SMOOTH | quick-steps wind-up cap: no visible attack on a boss; Jian flinches at v1 #15 f30 while the boss stands still (rec_sprite fire punch / sword slash #34-39 f68-78; two-hit: second punch #55-57 f110-114 also lost). Fixed: strike back (Deuce two-hit fixed: punches #21-24 and #39-42, flinches #25 and #43; Gideon: slash #18-23, flinch #24) |
| 153_Gideon_2_a0_skill20_x8000 | 0x020950c4 | 158 | 70 | FIXABLE | 82 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: slash flash at the end of the wind-up lost (before #26-30); the projectile comes straight out. Fixed: whole pose (25 at 3x): slash #14-16, then the projectile; 37 damage in sync |
| 153_Gideon_2_a1_skill18 | 0x02094e84 | 224 | 82 | FIXABLE | 118 | SMOOTH | quick-steps CAST_POSE 24 (12 Fast) ends the pose before its key frame: glowing-hand charge lost (before #33-51); the boss just leans. Fixed: whole pose for rows 142 and 153 (47 at 3x): hand sparkle #19-25 and burst #26 (Gronk a0, Gideon 2 a1), then the spell; flinch #60 |
| 154_Gideon_3_a0_skill16 | 0x02094e84 | 102 | 48 | SMOOTH | 48 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 154_Gideon_3_a1_skill30 | 0x02094e64 | 226 | 72 | SMOOTH | 72 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
| 155_Ignatius_a0_skill16 | 0x02094e84 | 254 | 52 | SMOOTH | 52 | SMOOTH | spell: hit sync, effect end, return, and camera as before |
