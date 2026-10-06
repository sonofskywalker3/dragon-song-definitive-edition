# Reverse engineering: Jian's curse and battle pacing

Investigation for a design discussion, 2026-10-06. Nothing here is implemented. Static analysis of the USA
ARM9 binary (build/arm9_decomp_annot.c, `uv run python -m dsde.arm9 dis`) and the event scripts
(`uv run python -m dsde.script`), plus emulator measurements on a ROM built from the working tree
(`build/par_d/dsde_d.nds`, which includes the other agent's uncommitted `hold-lr-to-run`). Findings are
marked **confirmed** (read in code or script, or measured) or **uncertain**.

Diagnostic plans added: `emu/plans/diag_speed_base.plan`, `diag_speed_l.plan`, `diag_speed_r.plan`,
`diag_curse_attack.plan`, `diag_curse_shots.plan`. Logs and screenshots are in `build/par_d/<plan>/`.

## Part 1: Jian's curse (Curse of Lost Equilibrium)

### 1.1 What the curse is in battle (confirmed)

The whole effect is one short in the battle setup struct: **0x020B85B8 + 0x5C** (getter `func_0202b934`,
setter `func_0202b91c`). It is computed once per battle in `func_0202b948` (battle init):

```
0202b968  strh   r0, [r7, #0x5c]        ; cursed = 0
0202b970  mov    r1, #0x79 ; bl func_02041918   ; story flag 0x79 set? -> not cursed
0202b98c  mov    r1, #0x33 ; bl func_02041918   ; story flag 0x33 set?
0202b99c  strheq r0, [r7, #0x5c]        ; cursed = 1
```

So **cursed = story flag 0x33 set and story flag 0x79 clear**. The engine reads flag 0x33 nowhere else.

The flag is read in four places:

1. **Jian's Attack script choice**, `func_02068308` (sets the action script at battler +0xC8 and the
   animation id at battle work +0x50 from the per-character table at 0x020953D4, 0x12 bytes per character).
   Three paths check the curse, all only for character id 0:

   | Path | Check at | Not cursed | Cursed |
   |---|---|---|---|
   | Melee Attack (front row) | 0x020684F8 | script 0x02095AF0 (3 hit steps), anim table +4 = 0x0E | script 0x020958C0 (1 hit step, the script Lucia/Gabryel/Rufus use), anim table +6 = 0x0D |
   | Attack when target/battler +0x2E flag routes to the far script | 0x02068628 | 0x02095560 (3 hits) | 0x020954F0 (1 hit) |
   | Follow-up actor (`param_2 & 1`, battler 13, the second actor of state 8) | 0x02068370 | 0x02095134 (3 hits) | 0x02095064 (1 hit) |

   Only Jian's row has different +4 and +6 animation ids (0x0E combo, 0x0D single swing); every other
   character has the same id in both. The 3 hits are three 0x41 steps (wait for animation end + hit),
   playing sequences 1, 2 and 3 of animation 0x0E; the cursed script has one 0xC1 step.
2. **Zethos fight, HP floor**, `func_02053384`: in event battle 6 (Zethos) while cursed, an enemy's HP
   cannot drop below half its max.
3. **Zethos fight, AI**, `func_020695c0` case 6: while cursed, rounds 0 to 2 (battle ctx +0x0A, likely
   the round counter) Zethos attacks on about 5 of 8 turns; from round 3 on he picks **action 3**. Row 143
   (Zethos) action 3 is flags 0x11406 with skill id **21**; skill 21 in the effect table at 0x02094978
   (0x0C per entry) is `0x82, 0x0A, 0x6FFFF`, and effect bit 0x80 makes `func_020500dc` call
   `func_0202b91c(ctx, 0)`: **Zethos himself lifts the curse mid-fight**. Not cursed: he picks action 0 or
   1 at random every turn and has no HP floor.
4. The setter is called only from that skill effect. Nothing else ever clears it in battle.

Measured (`diag_curse_attack`, curse poked to 1 before the command): the cursed Attack runs script
0x020958C0 and its action takes **181 frames** against **217** for the combo (`diag_speed_base`). One hit
did 153 damage, the same as the combo's first hit in docs/test-report-battle.md, so the curse costs about
**two thirds of Jian's Attack damage** for 36 frames saved. Screenshots `build/par_d/diag_curse_shots/`
show a plain single swing (no headstand or other special pose in battle).

### 1.2 What sets and clears it (confirmed)

Raw scan of every script for `set flag` / `clear flag` and flag-list tests of 0x33 and 0x79:

- **Set 0x33: script 005 at 0x3E3C**, the end of the San Coliseum (script 005, maps 186 to 198). After the
  Moran fight (event battle 0x10 at 0x3B94) Jian collapses, the "Strange Girl" Gabryel appears,
  **party join 2 at 0x3D88** (this is Gabryel's first join, at level 1), the message at 0x127D ("My
  body... won't do what I tell it to! I can't perform any of my special skills! ... No standing on my
  head!" / "the Curse of Lost Equilibrium" / "Zethos... You'll have to meet with him"), then
  `set_flag 0x33` and a map change.
- **0x33 is never cleared.** The curse ends because **0x79** is set: **script 009 at 0x6044**, Zethos
  Castle (maps 223 to 225), after the Zethos fight (event battle 6 at 0x5B78), the "you're back to
  normal! The Curse of Lost Equilibrium has been broken!" line (0x23C9) and the reveal that Gabryel is
  Zethos's daughter; right after it come flags 0x1F8, 0x1FA, 0x1FB and **party leave 2 at 0x605C**.
- 0x79 is a general "after Zethos" chapter flag: about 35 NPC branches test it (scripts 001, 003, 004, 005,
  007, 009, 015, 018). 0x33 is tested by script 001 0x6A78 (the Port Searis ferryman sails only after the
  Coliseum) and script 005 (Coliseum state).

Asides for the other docs (not edited here): docs/re-field-battle.md's party table calls 005 0x3D88
"Gabryel rejoins in Leephon City" and 009 0x605C "separated after Gronk". By the script text, 005 is the
San Coliseum first join and 009's leave follows the Zethos fight. docs/story-party-timeline.md steps 6 and 7
have the same order question.

### 1.3 How much of the story is cursed

From flag 0x33 (end of the Coliseum) to flag 0x79 (after Zethos). Script-to-map from the map table at
0x02091D18 (+2 = script), place names from the scripts' own text and docs/story-party-timeline.md:

| Place | Script, maps | Battles | Notes |
|---|---|---|---|
| San Coliseum aftermath, Healriz | 005 (186 to 198), 004 (176 to 185) | none (towns) | curse scene, Gabryel joins at level 1 |
| Port Olbeage | 007 (199 to 212) | none | Carmen: "The Curse of Lost Equilibrium? ... you're going to be stuck like that for a long time" (0x0C5C) |
| Cathedral of Althena | 015 (140 to 150, 11 maps) | regular encounters; **4 Deuces** (event battles 4, 0x16, 0x17, 0x18; flags 0x6B to 0x6E) and **Gronk** (5; flag 0x6F) | the one dungeon of the stretch |
| Capture, Leephon City, Zethos Castle | 008 (213 to 222), 009 (223 to 225) | **Zethos** (6), Jian solo | saving disabled after Gronk until Zethos (SaveFAQ, docs/story-party-timeline.md) |

Party for the whole stretch: Jian (cursed), Lucia, Gabryel (from level 1). The slog players describe is the
Cathedral plus its five boss fights with a one-swing Jian and a level 1 Gabryel at the same time.
Uncertain: maps 35 to 49 and 85 to 93 have no map script (script 0) and no names; some field maps on the way
from Healriz to the Cathedral may be among them.

### 1.4 How the curse shows outside battle (confirmed static, uncertain visually)

Nothing in the engine. Flag 0x33 is read only by battle init and by script branches, and no field sprite or
walk code looks at it. Outside battle the curse exists only as dialogue: the 005 curse scene, Carmen in Port
Olbeage (007), Lucia at Zethos Castle ("You'd better put my poor Jian back to normal", 009 0x1CE3), the lift
line after the fight (009 0x23C9), Zethos "You look all better now" (009 0x31A6). Note the story text says the
curse **stops** his headstands; nothing shows Jian on his head while cursed. Scripted poses in the 005 and 009
scenes (ops 0x37/0x40) were not viewed.

### 1.5 Options

| # | Option | Code change | Story scripts | Cost | Risks |
|---|---|---|---|---|---|
| C1 | **No curse at all** | NOP `strheq r0,[r7,#0x5c]` at 0x0202B99C | none (optionally text edits) | 1 instruction | Dialogue says he is cursed while he fights normally, from the Coliseum to Zethos. Zethos becomes an ordinary fight: no HP floor, no lift spell, killable from turn 1 (Jian solo, fight level 10) |
| C2 | **Curse ends at Gronk** (or after the 4th Deuce) | replace the 0x33 test with a cave: cursed = 0x33 and not 0x79 and not 0x6F | none needed; text edits recommended in 009 (0x1CE3, 0x23C9) | small cave | The Cathedral is still cursed, so most of the slog stays. Zethos fight as in C1. Lucia's "put my poor Jian back to normal" and the lift line no longer fit. A real "curse lifted" moment at Gronk would need new script ops in 015 (relocating code and jumps: high cost) |
| C3 | **Soften: 2 hits** | cave copy of 0x02095AF0 with hit step 7 removed; point the cursed load at 0x02068534 (and 0x02068660, 0x020683A4 paths) at it; use the combo animation (load anim from +4 instead of +6 at 0x0206852C, or change Jian's +6 entry in 0x020953D4 from 0x0D to 0x0E) | none | small, 3 sites | Animation sequence 2 must flow into the recovery step without a pop: needs an emulator look. The literal 0x020958C0 is shared with the other characters, so patch the code, not the literal. Keeps redirect on the second hit (a kill moves hit 2 to the next enemy) |
| C4 | **Soften: 1 hit, more damage** | hook `bl func_0205212c` at 0x02030DA4 in `func_02030b44`: after the call, if the attacker is battler 12 (or 13) holding Jian (character id 0) on an Attack and 0x020B8614 == 1, multiply r0 (damage) by 2 (or 3) | none | one hook, about 15 instructions | Overkill on the one hit is wasted (no redirect inside one hit). At x3 the curse becomes cosmetic. Card or status rules that force damage to 1 run after the call and still apply |
| C5 | Keep vanilla | none | none | none | The most common early-game complaint stays |

### 1.6 Recommendation

**C4 at x2**: keep the story gag (the single swing, every line of dialogue, the Zethos lift scene and its
fight mechanics) and touch no story script. Jian's Attack goes from one third to two thirds of the combo's
damage, and the action stays 36 frames shorter than the combo. If playtesting still finds the Cathedral a
slog, raise the factor to 3, or switch to C3 (2 hits, closer to "the curse costs him his finisher"). C1 and
C2 are cheap in code but leave five or more scenes of dialogue describing a curse the player never feels.

## Part 2: battle pacing

### 2.1 The game already has a fast-forward (confirmed)

`func_020297d4` (battle main, every frame) starts with:

```c
held = func_0201a3b8(0x020AFF74);        // pad +0x0A, keys held this frame
*(int *)0x020B8540 = 0;
if (held & 0x200) *(int *)0x020B8540 = 1;   // L
if (held & 0x100) *(int *)0x020B8540 += 2;  // R
```

So the speed level s at **0x020B8540** is 0 to 3: L = 1, R = 2, L+R = 3. Only two places read it
(literal-pool scan of the whole binary finds three references, the third being the writer):

- `func_02031e08`, battler and effect-object sprite animation: the frame accumulator at object +0x102 gets
  `step * (1 + s)` per frame (step 0x20, 0x80 or 0x100 by object type), so **sprite animation runs at 2x
  with L, 3x with R, 4x with L+R**.
- `func_0207d1b8`, the spell/effect script timer (0x0213F148 +0xA2): counts down by `1 + s / 2`, so **spell
  effects run at 2x with R or L+R**, normal with L alone.

Nothing else speeds up: frame-count steps of action scripts, moves, the camera, the kill hold and fade, the
front-row refill, status ticks and windows all run at normal speed.

Holding the button is required every frame; there is no toggle and no option. This is the "fast-forward"
reviewers mention (docs/research-bugs-thieves.md: added to the English releases).

**Conflict with `hold-lr-to-run` (other agent's uncommitted feature):** it flees when L and R have been held
together for 30 frames during command input. L+R is also the strongest fast-forward. A player holding L+R
through the enemies' turns arrives at the command menu with both held and runs from the battle half a second
later. Needs a decision before that feature ships (different run chord, or count only presses that start
inside the command menu).

### 2.2 How a round is paced (confirmed)

Round state machine: `func_0202d22c`, state at battle work (pointer 0x020B8550) +0x2E, actor at +0x32.
Main states: 1 pick next actor and targets (`func_020514ec`), 5 load the action's animations
(`func_02068890` -> `func_02068308`) and start the camera turn (`func_02028540`), 6 wait for the animation
load and the camera, 7 run the action script of battler 12 (8/9: follow-up actor battler 13), 0xC apply HP
(`func_020532ac`), 0xD kill hold and fade, 0xE..0x10 end-of-action and status ticks (0xF: poison etc., 30
frame waits at +0xD6), 0x11 front-row refill (64 frames, constant 0x40 in `func_02053918`).

Action scripts: 16-byte steps at battler +0xC8, current step +0xCC, advanced by `func_02031514` each
frame. Word 0 bits 0-1 pick the wait: **1 = until the sprite animation ends** (battler +0xFA bit 0x80),
**2 = a fixed frame count, the s16 at +0x0C**, counted by battler +0xCE (+1 per frame). Other bits: 0x10
moving, 0x40 hit, 0x80 hand over to the follow-up actor, 0x20 end, 0x80000000 last step, 0x2000000 also
wait for effect objects; +8 animation slot, +0xA sequence. Moves started by a step (`func_0202fdf0`,
`func_020303e8`) use the same +0x0C as their duration (object +0xB0), counted by +0xB4 in `func_0202f230`.

Measured, first Delrich Temple battle (Jian with test stats kills his target in one action, then
two enemies attack), frames at 60 per second:

| Segment | No button | L held | R held |
|---|---|---|---|
| Whole round (state 5 of Jian to state 0) | **749** | 607 | **571** |
| Jian's action script (combo) | 217 | 149 | 113 |
| Kill hold and fade (state 0xD) | 151 | 93 | 93 |
| Front-row refill (state 0x11) | 64 | 64 | 64 |
| One enemy turn (state 5 to next state 5) | 155 | 147 | 147 |
| of which camera turn (state 6) | 17 | 16 | 16 |
| of which enemy action script | 117 | 87 | 87 |
| of which fixed-frame steps in it (0x02095334: 8, 30, 30) | 68 | 68 | 68 |
| after-action state 0xE | 28 | 32 | 32 |

Jian's combo steps without a button: ready 29, leap 6 + 6, wind-up 18 + 10, swings 28 + 38 + 18,
recover 30, leap home 8 + 8, finish 18. The fast-forward halves the player's attacks but barely touches
enemy turns, because enemy attacks are mostly fixed-frame moves (30 frames out, 30 back).

Not blocking the round (static): damage numbers (effect array at 0x020B8624) and the face flash (30 frames,
`func_02034458`) run alongside. The EXP pour on the result screen (`func_02052c2c`, 64 steps every 4 frames,
about 256 frames) is skipped by A already.

### 2.3 Options

| # | Option | Change | Cost | Risk |
|---|---|---|---|---|
| S1 | **Default fast-forward**: start the level at 2 instead of 0 (R speed without holding); L adds 1 | `func_020297d4`: the `*0x020B8540 = 0` store (one immediate) | 1 instruction | Very low: it is the shipped, tested fast-forward. Measured gain about 24% per round. No way back to normal speed unless a button subtracts instead (still cheap: a few instructions) |
| S2 | **Extend the fast-forward to frame-count waits**: scale the per-frame counters by `1 + s/2` like the game does for effects: step counter +0xCE in `func_02031514`, move counter +0xB4 in `func_0202f230`, effect-object step counter +0xB8 in `func_02031408` | 3 small hooks | Medium. Waits and moves use the same duration, so they stay in step, but `func_0202f230` must clamp t to the duration (some paths do, check all) or positions overshoot on odd durations. Enemy turns would shrink from about 150 to about 115 frames |
| S3 | **Halve step durations in data** (+0x0C of every type-2 step) | rewrite the action-script tables | Low code, high audit cost | Same effect as S2 but always on, and the step tables are shared and not all found; a 1-frame step cannot halve. S2 is the better form |
| S4 | **Shorten specific waits**: front-row refill 0x40 -> 0x20, kill hold (0x3C at `func_020532ac`) and fade, status tick 0x1E | constants | small each | Low. Refill: back-row enemies slide twice as fast. Kill hold: less time to read the last damage number |
| S5 | **Global frame skip** (run the battle update twice per frame, or skip every other animation update) | main loop | small code | **High**: the battle frame also submits 3D geometry, OAM, sound triggers and reads pad edges (A to skip, command input). Running it twice per VBlank double-reads presses, double-fires sounds and can tear the 3D frame. Not recommended |
| S6 | **Option toggle** (menu entry) | new option UI and a save slot for it | high (UI work) | Low technically. A button convention (S1 with "hold L for normal speed") gives most of the value without UI |

Desync risk in general is low for S1 to S4: battles are not networked or recorded, and the random number
calls happen at decision points (target pick, hit rolls), not per frame, so changing frame counts changes
which values the RNG gives later (different but valid battles). Broken-effect risk is mostly in S2/S3 moves
(overshoot) and in S5.

### 2.4 Recommendation

**S1 now, S2 next, S4 for the refill.** S1 makes every battle use the game's own R speed with no input (one
instruction, already shipped and tested by the developers), and holding L still adds more. S2 then gives enemy
turns and moves the same treatment, which is where the fast-forward does nothing today; it needs a measured
pass with `diag_speed_*` plans and screenshots of leaps and enemy lunges. Shortening the 64-frame refill (S4)
is a cheap extra. Skip S5. Decide the L+R run chord at the same time, since L+R is the fast-forward's top
level.
