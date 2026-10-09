# Reverse engineering: battle pacing and a battle speed toggle

Investigation for a design decision, 2026-10-06. Nothing here is implemented. Follows up
docs/re-curse-battle-speed.md part 2 (the game's L/R fast-forward, options S1 to S6) now that L and R are
reserved for running (`hold-lr-to-run`, commit f5fc061 NOPs the two fast-forward stores at 0x0202980C and
0x02029820, so the speed level at 0x020B8540 stays 0).

Sources: static analysis of the USA ARM9 (build/arm9_decomp_annot.c, `uv run python -m dsde.arm9 dis`) and
emulator runs on ROMs built from the current tree (`build/par_f/dsde_f.nds`, same patches as f5fc061).
Findings are marked **confirmed** (read in code or measured) or **uncertain**.

Plans added: `emu/plans/diag_pace_round.plan` (whole temple battle, state log), `diag_pace_frames.plan`
(screenshot of every frame of round 1), `diag_pace_spell.plan` (party of three, Lucia casts Heal, every
frame of her action), `diag_pace_party3.plan` (command menu screenshots). Logs and shots in
`build/par_f/<run>/` (round, frames, spell, party3, round_s1, round_s2).

For the forced-speed measurements two throwaway ROMs were made by patching a copy of the built ROM (not
src/): the `mov r2, #0` at 0x020297FC (the value func_020297d4 stores into the speed level every frame)
became `mov r2, #1` (`dsde_s1.nds`) and `mov r2, #2` (`dsde_s2.nds`), which is what holding L or R did before.

All frame counts are at 60 frames per second (1 second = 60 frames).

## 1. Frame budget

### 1.1 Addresses used (confirmed)

| What | Where |
|---|---|
| Battle main state | u32 0x020B0010 (0x020AFF84 + 0x8C), func_020297d4: 0..2 setup, 3 fade in, 4 enemy rows fade in, 5 enemy pop-in and hold, 6 opening message, 7 command input, 8 round, 9 and 10 victory, 0xB.. exit |
| Battle substate | u16 0x020B85C8 (ctx 0x020B85B8 + 0x10): in state 7, 1 start, 2 command window slide-in, 3 input, 4 close; in state 10, 1 victory poses, 2 EXP pour, 3 level-up hold, 0x28/99 result page |
| Round state | battle work (pointer 0x020B8550, 0x02282940 in these runs) + 0x2E, func_0202d22c (states listed in docs/re-curse-battle-speed.md 2.2) |
| Work counters | +0xCE/+0xD0 (intro and kill hold/fade), +0xD4 (front-row refill), +0xD6/+0xD8 (status ticks) |
| Battler 12 action step | battlers (pointer 0x020B8640, 0x0228EDA0) + 12 * 300 + 0xCC |

### 1.2 Regular temple battle (warp6, Jian alone with test stats)

From `diag_pace_round` (A pressed every 22 frames from the first command to the field; build/par_f/round).
Five enemies (three bugs in the back row, skeleton and spider in front). Jian's combo kills one or more
enemies per action; the battle ends after two rounds.

| Phase | Frames | Kind |
|---|---|---|
| Field to battle (touch to battle main state 0) | 91 | field side transition |
| Setup, fade in (states 0..3) | 13 | loading, 7 lag frames |
| Enemy rows fade in (state 4: two 32-frame blends) | 68 | fixed (0x20 per row, func_020297d4 case 4) |
| Enemy pop-in (state 5: 4 columns x 16 frames, then a 64-frame hold) | 128 | fixed (0xF and 0x3F in case 5) |
| **Intro total, battle start to first command** | **209** | |
| Command window slide-in (state 7 substate 2) | 30 | fixed (counter +0x36 to 0x1F, func_0203aa10); 11 lag frames inside it |
| Command input | player | 4 presses for Fight, pick, OK with manual targeting |
| **Round 1** (Jian kills one, then two enemies attack) | **749** | |
| . Jian: load and camera (round states 5, 6) | 8 | |
| . Jian: action script (combo, 12 steps) | 216 | 188 animation-driven, 28 fixed (leaps 6+6, 8+8) |
| . Kill: hold, the dying enemy flashes white (state 0xD, +0xD0 = 0x3C) | 60 | fixed, 0x02053338 |
| . Kill: fade with a halo (blend, +0xD0 = 0x20) | 32 | fixed, 0x0202DE4C |
| . Kill: wait for the rising sparkles (func_0202cb44, effect battlers 0x16..0x1D) | 59 | animation-driven (about 151 frames from the kill) |
| . After-action and status ticks (states 0xE..0x10) | 6 | no damage numbers left by then |
| . Front-row refill (state 0x11, back-row bug flies down) | 64 | fixed, 0x40 in func_02053918 |
| . Enemy 9 turn | 152 | |
| . . load and camera turn (states 5, 6; camera 0x10) | 18 | fixed (0x0202D67C), 2 frames loading |
| . . action script 0x02095334 (steps 8, 30, 19, 8, 30 frames + 4 lag) | 99 | 68 fixed (lunge out 30, back 30, ready 8), 27 animation |
| . . apply HP (0xC, 0xD) | 2 | |
| . . wait for damage numbers (state 0xE, func_0202c3e8) | 28 | fixed number lifetime (8 rise + 0x3C hold, func_0202c15c) |
| . . status ticks (0xF) | 3 | |
| . Back-row actor 4 skipped (cannot reach) | 4 | |
| . Enemy 10 turn | 138 | as enemy 9, camera already close (7) |
| . End of round, camera back (21, overlaps the next slide-in) | 9 | |
| **Round 2** (Jian's combo finishes the battle) | **383** | Jian 216, kill 151, rest 16 |
| Victory: setup | 22 | |
| Victory poses (substate 1) | 136 | animation (script 0x020950F4) plus a 0x3C hold per battler |
| EXP pour (substate 2) | 273 | 64 steps every 4 frames; A skips it, see 1.5 |
| Level-up hold (substate 3) | 136 | 0x28 counter plus number popups |
| **Victory to result page** | **568** | |
| Result page (waits for A), item page, fade to field | 66 + 98 | |

Whole battle from touch to field: about 2470 frames (41 s), of which the player chose commands for about
280 frames. Two rounds took 1132 frames; the intro and the victory took 777.

### 1.3 Party of three with a spell (diag_pace_spell)

Jian, Lucia and Gabryel (party3_strong), same temple battle. Lucia casts Heal on Jian.

| Segment | Frames |
|---|---|
| Round 1 (Gabryel kill, Jian kill, Lucia Heal, one enemy attack) | 1289 |
| Gabryel: camera 7, action 202, kill 151, after 6, refill 64 | 430 |
| Jian: as in 1.2 | 446 |
| Lucia's Heal: camera 18, cast pose 149 (one animation-driven step), heal step 69, end 8 | 244 |
| Enemy 10 turn | 152 |
| Back-row skips and end | 13 |

So a party round is roughly 400 to 450 frames per party member who kills, 250 per spell like Heal and
140 to 150 per enemy who attacks. Every kill costs about 150 frames of hold, fade and sparkles plus 64 for
the refill when a front-row slot opens.

### 1.4 Fixed, animation-driven and low-information time

- **Fixed frame counts** (do not scale with the old fast-forward): action-script steps of type 2 and the
  moves they start (all enemy lunges: 68 of an enemy's ~97 script frames), the kill hold 60 and fade 32,
  the refill 64, camera turns 16, the damage-number lifetime (8 + 60), status tick waits 30, the
  command window slide-in 32, the intro fades and pop-in (196), the victory holds, the EXP pour (256).
- **Animation-driven** (scale with the speed level at 0x020B8540): steps of type 1 (wait for the sprite
  animation to end: most of a party member's attack and spell poses), the death sparkles, the victory
  poses, and effect scripts (func_0207d1b8).
- **Dead time in the strict sense (nothing on screen changes) does not exist**: in 604 consecutive frames
  of round 1 no run of identical frames was longer than 2 frames (section 2). The time that feels dead is
  low-information time: the 60-frame white flash before an enemy fades, the sparkles after it, the
  28 to 32 frames where the round waits for a damage number that has already been read, the 64-frame
  refill, the 64-frame hold after the enemies have appeared, and the 32-frame menu slide-in every round.

### 1.5 Small findings

- **The EXP pour ignores 3 of 4 A presses (confirmed).** func_02052c2c only checks for a new A press on
  frames where its counter (+0x150) & 3 == 0, so a tap is accepted only if its first frame lands on one of
  every four frames. In the run, A pressed every 22 frames never skipped the 273-frame pour. Checking the
  press every frame (or remembering it) is a small fix.
- The damage-number wait grows when actions get faster: with the sprite speed forced to 2x the enemy's
  script shrank from 99 to 87 frames and state 0xE grew from 28 to 32. The number lifetime is the floor of
  an enemy turn.

## 2. Smoothness

Measured with `exec 0x020297D4` (one log line each time the battle main runs) and a screenshot of every
frame (`diag_pace_frames`, `diag_pace_spell`).

- **The battle runs at 60 Hz (confirmed).** Battle main ran once on every emulated frame and never twice;
  no 30 fps mode.
- **Lag frames (frames where the game did not finish its update) are few and clustered:**
  - opening the command window each round: 11 lag frames inside the 30-frame slide-in (2845..2855,
    3766..3776);
  - **2 frames at steps 1, 2 and 4 of the enemy lunge script** (3476, 3508, 3535 and again for enemy 10).
    Each is a 3-frame hitch, 3 per enemy turn, visible as a small stutter as the enemy starts its lunge,
    its swing and its return. First guessed to be a sprite load at an animation slot switch; **the cause
    is a sound bank load** (confirmed 2026-10-09, section 7: the lunge's steps 1, 2 and 4 are the steps
    that play a sound, and its sounds alternate between two banks that cannot both be loaded);
  - battle start (7 frames) and the victory setup (5 frames).
  - Lucia's Heal had **no** lag frames and no long repeats.
- **Repeated identical frames:** 123 of 603 frames (both screens) were identical to the previous one, in
  runs of 1 or 2 frames: sprite cels change every 2 to 4 frames by design (the animation data), while
  moves, flashes and numbers update every frame. The kill hold and fade had no repeated frames. The
  enemy turn had the most (41 of 99) because the attacker stands still between its cels.
- **Pauses between turns:** each actor starts with 7 to 18 frames of load and camera turn, and each enemy
  turn ends with the 28 to 32-frame damage-number wait. These are the only between-turn pauses; the
  bigger gaps are the kill sequence and the refill.
- Not measured: attack spells that use the effect-script system (0x0213F148; Heal did not touch it) and
  boss effects. A run with an attack spell would complete this section.

## 3. Speed-up candidates

Savings are per round of 1.2 (749 frames: one party kill, two enemy attacks) unless noted. "Measured"
means from the forced-speed ROMs; other figures are estimates from the budget.

| # | Candidate | Saves | Implementation | Risk |
|---|---|---|---|---|
| P1 | **Game's own speed level forced on** (0x020B8540 = 1: sprites 2x; = 2: sprites 3x and effect scripts 2x) | measured: **142** at level 1 (749 to 607), **178** at level 2 (571); victory poses 136 to 120 / 104 | Change `mov r2, #0` at 0x020297FC to the level (or to a load of the setting, see 4.2). Readers: func_02031e08 (sprite accumulator, `mla` at 0x02031FF4) and func_0207d1b8 (effect timer) | Very low: shipped behaviour. At level 2 a party attack looks brisk but intact (developers' own R speed). One cel per frame at most, so very short cels cannot go faster than 1 per frame |
| P2 | **Scale fixed-frame steps and moves** by the same factor (step counter +0xCE, move counter +0xB4) | at 2x: 14 for Jian, 34 per enemy turn: **82**; at 3x: 109 | Hooks at 0x0203153C (`add r0, r0, #1` of the step counter in func_02031514) and 0x0202F258 / 0x0202F270 (move counter in func_0202f230): add k instead of 1. Effect-object steps (+0xB8 in func_02031408) the same way | Medium-low. Step and move use the same duration, so they stay in step; func_0202f230 clamps t to the duration at 0x0202F2A0 (check the other move paths before shipping). Enemy lunges get twice as fast; needs a visual check |
| P3 | **Shorter kill sequence**: hold 60 to 20, fade 32 to 16 | 76 per action with a kill at level 0; at level 2 the sparkles (about 50 frames at 3x) become the floor, so about **45** | Immediates 0x02053338 (`mov r6, #0x3c`) and 0x0202DE4C (`mov r6, #0x20`); the fade step size (`<<4 >>5` of the counter) needs a matching change or the blend jumps | Low. Less time to see which enemy died; the flash still shows |
| P4 | **Faster refill**: 64 to 32 frames | **32** per refill | func_02053918: 0x0205394C / 0x02053950 (`cmp/movge #0x40`) and 0x02053970 (`rsb #0x40`); the curve `(0x40 - t)^2 * 0x70 >> 12` needs t doubled or the constant scaled so the end position is the same | Low. Back-row enemy flies down twice as fast |
| P5 | **Shorter damage numbers**: hold 60 to 24 (rise 8 kept) | about **20 to 30 per enemy turn**, more once P1/P2 shorten scripts (the 0xE wait becomes the floor otherwise) | 0x0202C1F8 `mov r2, #0x3c` in func_0202c15c (also 0x0202C204 / 0x0202C210 for the 0x18 / 0x28 variants) | Low. 24 frames (0.4 s) is enough to read a 3-digit number; Lunar 1/2 numbers are shorter still (uncertain, from memory) |
| P6 | **Do not wait for damage numbers** at the end of an action (state 0xE skips func_0202c3e8) | all of the 0xE wait: **56** (28 per enemy turn), up to 64 at level 2 | Hook the `bl func_0202c3e8` at the top of case 0xE in func_0202d22c to return 0; the numbers keep animating over the next actor's camera turn (29 slots) | Medium-low. Numbers overlap the start of the next turn. Combine with P5 rather than replace it |
| P7 | **Faster camera turns**: 16 to 8 frames | 8 to 10 per actor: **~25** | 0x0202D67C `mov r2, #0x10` (func_02028540 duration in round state 5) and the round-end call in func_020297d4 case 8 | Low-medium: a faster swing can look like a snap. Small gain |
| P8 | **Overlap the next actor with the previous actor's return** | up to 30 per enemy turn | Battler 12 (and 13) is the single scratch copy every action runs on, and func_0202d22c only starts the next actor from state 1. Overlap needs a second scratch battler or starting the next camera turn during the return step | **High**: deep change to the round machine. Not recommended; P2 halves the return move instead |
| P9 | **Move enemy sound bank loads off the action** (the 2-frame hitches; section 7) | no frames saved; the first load of a turn lands on a still frame | Built as `enemy-preload` (off by default): switch the bank before step 0 | Low-medium; loads between two banks inside one action stay (heap too small) |
| P10 | **Intro trim**: rows 32 to 16 each, columns 16 to 8, hold 64 to 16 | **~110 per battle** | func_020297d4 case 4 (`0x20` compares) and case 5 (`0xF`, `0x3F`) | Low. The enemies still appear column by column |
| P11 | **EXP pour**: accept A on any frame; optionally 2 frames per step instead of 4 | up to 256 per battle when skipped; 128 if halved | func_02052c2c: move the A check out of the `& 3` gate | Very low |
| P12 | **Command window slide-in** 32 to 16 | 16 per round | counter +0x36 limit 0x1F in func_0203aa10 / func_0203a34c | Low |
| S5 | Run the battle update twice per frame | everything | main loop | **High**, rejected in docs/re-curse-battle-speed.md 2.3 (double pad reads, double sounds, 3D tearing) |

Desync and RNG: as in the earlier doc, random calls happen at decision points, so shorter waits give
different but valid battles. Battles are not recorded or networked.

## 4. Proposals

### 4.1 What the Lunar remasters do (sources at the end)

Lunar Remastered Collection (2025, PS4/PS5, Xbox, Switch, PC):

- **Three speeds** (1x, 2x, 3x). Steam store page: "Battle speed can now be adjusted at any point during
  battle, with three speeds to choose from." Reviews: "increase the speed up to 3x the normal with a flick
  of the L2 or R2 buttons".
- **Switched in battle only, with the triggers**: right trigger speeds up, left trigger slows down
  (L2/R2, LT/RT). RPG Site (PC port): "only lets you adjust the battle speed by using the trigger buttons
  while in battle"; there is no menu option for it. RPG Site's walkthrough mentions a trophy for adjusting
  it.
- **Battles only**: no source mentions map or cutscene speed; RPG Site contrasts it with the mobile
  Silver Star Story Touch, which has separate map and battle speeds from 1x to 3x. Default is 1x
  (reviewers describe the original speed as the default).
- **Persistence (uncertain)**: an achievement guide snippet (XboxAchievements, page not readable here, only
  the search summary) says the speed must be set again every time the game is loaded. Whether it carries
  from one battle to the next within a session is not stated anywhere I could read; the "change it at any
  time in battle" wording suggests it does.
- **What it scales (uncertain)**: no source says whether enemy turns, text and effects are included.
  Players describe whole battles (with Auto battle) running up to 3x, which reads as a global battle
  clock, not just animations. On-screen indicator: battle option icons exist (RPG Site mentions icon
  scaling issues) but the speed display is not described.

### 4.2 Default pacing package (no button)

Goal: every battle feels about twice as fast as the original with nothing to hold, and nothing looks
broken. In order of value for effort:

1. **P1 at level 2** (the developers' own R speed, always on): 749 to 571 measured.
2. **P2 at 2x** for fixed steps and moves, so enemy turns speed up too (the old fast-forward never did).
3. **P5 + P6**: damage numbers hold 24 frames and the round does not wait for them.
4. **P3, P4**: kill hold 20, fade 16, refill 32.
5. **P10, P11, P12**: intro trim, EXP pour skip on any frame, faster command window.
6. Later, after a look: P7 (camera 8), P9 (enemy hitches).

Estimated round of 1.2 with items 1 to 4: Jian about 106 (8 + script 98), kill about 50, refill 32; each
enemy turn about 75 (camera 10, script 53, rest 12); total about **330 to 360 frames instead of 749**
(5.5 to 6 s instead of 12.5 s). Intro 209 to about 100, victory to result page 568 to about 260 with A,
so the sample battle goes from about 41 s to about 20 s. Estimates; every item needs its own emulator
pass (plans like `diag_pace_round` before and after, screenshots of lunges, kills and the refill).

### 4.3 A remaster-style speed toggle

If a control is wanted, make it a **battle speed setting with three levels**, like the remasters, where
the default package above is the middle level:

| Level | Name | Sprite / effect level (0x020B8540) | Fixed waits (P2..P7) |
|---|---|---|---|
| 1 | Normal (original) | 0 | original |
| 2 | Fast (default) | 2 | halved, trims of 4.2 |
| 3 | Faster | 3 (sprites 4x, effects 2x) | divided by 3 |

- **What it scales**: everything that counts frames in battle through one multiplier k read by every
  hook: sprite accumulator (already reads 0x020B8540), effect timer (same), step counter, move counter,
  effect-object steps, kill hold and fade, refill, damage numbers, camera, status ticks, victory poses and
  holds. The intro and the result pages can follow it too. Text: battle messages appear in window 0xD and
  are not typed out (uncertain); field text speed stays with the existing Message Speed option.
- **Where the state lives**: in battle, keep using 0x020B8540: remove the per-frame `str r2, [r1]` at
  0x02029804 (or store the setting there instead of 0), so all current readers follow it, and add the new
  hooks as readers. Battle-only by construction: only battle code reads it. For persistence, store the
  level in the save data: the Message Speed byte is 0x020B4849 (save block 0x020B45B0 + 0x299, values 0..2)
  and is compared as a whole byte in three places (func_02066db8, func_02040910 at its table read,
  func_02066f08), so either find a byte the save block never uses (not done) or use bits 2..3 of that byte
  and mask those three readers. Copy it into 0x020B8540 at battle init (func_0202b948). If "exactly like
  the remasters" matters more than convenience, keep it in RAM only and reset to Fast on load (the
  remasters reportedly reset on load, uncertain).
- **Input** (L and R are taken):
  - **Select cycles the level** during battle (Normal, Fast, Faster). Select is free in battle since the
    run moved to L+R (commit 37e74a4); no battle input code read pad bit 0x4 in what I checked
    (func_0203a34c, func_0203aa10; uncertain beyond those). X is used (opens a window from the command
    screen, func_0203a34c `& 0x400`).
  - Alternatively Y (0x800), not checked as thoroughly.
  - A touch target is possible later: the wooden sign on the battle screen (MIC, NAME, X) is already
    proposed for a touch-and-hold run.
  - A System menu entry is the high-cost option: that menu is drawn from icons and graphics (System
    items: Message Speed, Save, Music, Title, Album), and a new entry needs art and layout. The game even
    has a cut label for it: "Battle Animation" (with "Text Speed" and "Return"), see 4.4.
- **UI feedback**: a menu sound (func_020284d8 with a cursor sound id) and a short line in the bottom help
  strip (the box that shows "Manual" / "Fight"), for example "Battle speed: Fast", plus a small x1/x2/x3
  marker on the top status bar if space allows. Exact text routine to use: uncertain, func_02066f90 draws
  the menu strings.

### 4.4 The cut "Text Speed" / "Battle Animation" options and "Change speed" (coordinator lead)

- **"Text Speed", "Battle Animation", "Return" (confirmed dead).** They are strings 0x15, 0x16 and 0x17 of
  the string table at 0x020A3CDC (u16 offsets) / 0x020A3D2C (text), text at 0x020A3D99, 0x020A3DA4 and
  0x020A3DB5 (the game's own encoding: space 0x00, A..Z 0x02..0x1B, a..z 0x3A..0x53, 0xFF ends a string).
  The table has five code references (0x020216DC, 0x020425F0, 0x0206D36C, 0x0206D708, 0x0207009C, plus
  0x020A3D18 for entries 0x1E..) and they read entries 0, 4, 0x1D, 0x21, 0x22, 0x23, 0x24 and 0x1E..0x20,
  never 0x15..0x17. No code draws these labels and no setting is behind them: the remains of a cut options
  screen. Nothing in the binary skips or shortens battle animations by option.
- **"Change speed" is the Message Speed help line (confirmed).** It is string 0x42 of the menu table at
  0x020A6438 / 0x020A65F4 (text at 0x020A67C4). The System menu (func_02059f84) shows help string
  0x29 + id; ids 0x15..0x1A are the six System entries' help lines ("Change message speed", "Save the
  game", "Enjoy game music", "Back to Title Screen", "Change speed", "Select Album"). Id 0x19 ("Change
  speed") is set in case 0x38, the state that opens the Message Speed window (case 0x39 draws the
  "Message Speed" title, case 0x3A takes the choice). The choice is stored by func_02066da8 in
  **0x020B4849** (0, 1, 2), turned into 1, 2 or 4 characters per step by the table at 0x0208D750, and read
  by the script message handler func_02040910 and the menu text printer func_02066f08. Battle code does
  not read it.
- So there is no existing battle speed or battle animation option to reuse; a toggle (4.3) is new work,
  but the "Battle Animation" label text already exists if a menu entry is ever built.

## 5. Recommendation

Ship the default package of 4.2 (P1 level 2, P2 2x, P5 + P6, P3, P4, then P10..P12) so that battles run
at roughly twice the original pace with no input, and fix the EXP pour's A skip (P11) regardless. If a
control is still wanted after playtesting, add the three-level Select toggle of 4.3 with Fast as the
default and Normal as the original game, which matches the remasters' three speeds and in-battle
switching while keeping L and R for running. Skip P8 and S5.

## 6. Actor flow (2026-10-08, feature `battle-flow`)

Jeff (3DS, Fast): Lucia's attack is slow and the wait between characters is long. Measured on Fast in the first
temple battle (Jian + Lucia, `diag_pace2_fast`; every hit kills):

| | Jian's Fight (state 7) | gap after it | Lucia's Fight | Jian lands -> Lucia leaps |
|---|---|---|---|---|
| Fast before | 203 | 92 (state 0xD 77) | 204 | 150 |
| Fast after | 203 | 16 | 76 | about 34 |
| Normal (unchanged) | 217 | 151 + refill 64 | 218 | |

- Lucia, Gabryel, Rufus and cursed Jian share the one-hit script at 0x020958C0 (16-byte steps; word 0 bits 0..1:
  1 = wait for the animation, 2 = fixed frames). Almost all of Lucia's 204 frames wait on her animations (row 1 of
  0x020953D4: 17 18 19 19 1A 19 1B 1C 1C), whose cels last 6 frames. Sprites advance by 0x100 * (1 + level) a
  sprite update (func_02031e08, level loaded at 0x02031FF0); a cel lasts at least 2 frames, so +2 levels (3x)
  is the limit through the sprite level.
- After a kill, state 0xD first runs vanilla's hold and fade of deferred deaths (+0xCE phases 1, 2), then waited
  in func_0202cb44 for the effect battlers 0x16..0x1D (the death sparkles: 151 frames at 1x, 75 at 2x or 3x).
- `battle-flow` (Fast and Faster only): the acting copy of a party member other than Jian animates at +2
  levels and the sparkles at +1; state 0xD waits only while a kill-on-hit death timer runs, or the full vanilla
  wait when no enemy is left alive (end of battle unchanged: `tgt_drop_exp` still pays 202 EXP and 101 silver).
  Jian keeps his speed: Jeff said his attacks already felt right.
- Not measured: Gabryel, Rufus, Flora, spells cast on Fast (the +2 also applies to cast poses), bosses.

## 7. Enemy action hitches are sound bank loads (P9, 2026-10-09, feature `enemy-preload`)

### 7.1 Cause (confirmed, vanilla and DE)

The hitch is not a sprite load: round state 5 already queues every animation slot the actor uses
(func_0201a710 / func_0201a7d8, async) and state 6 waits for the queue (func_0201a530) before step 0. The
lunge's lagging steps are not even the slot switches (0x02095334: step 1 keeps slot 1, step 3 changes the
animation without lag). What steps 1, 2 and 4 share is a **step sound** (u16 at step +6, played by
func_020316e0 through func_02067448).

- func_02028234 plays a battle sound id. Ids 0x1F..0x5C need a sound effect bank: **bank 2** for 0x1F, 0x23,
  0x25..0x39, **bank 3** for 0x22, 0x3A..0x4A, **bank 4** for 0x4B..0x5C (its jump table); lower ids (hits
  0x16, 0x1C, 0x1D, steps 0x13, 0x19) are in the system bank and never switch. The loaded bank is s16
  0x020B8564 (-1 at battle start). When a sound needs another bank, func_02028234 stops a flagged looping
  sound (func_02028434), pops the sound heap to level 3 (func_02043eb0) and loads the bank and its wave
  archive (func_02043f5c, NNS bank load) **from the card, synchronously**.
- The sound heap is a static 512 KB frame heap (0x020B9D20, created by func_020441ec; heap 0x020B9D60 to
  0x02139D20). In battle, level 1 holds the system bank 0 and its waves (about 160 KB), levels 2 and 3 the
  battle music (about 173 KB), level 4 one effect bank. Free with no effect bank: 190,684 bytes (measured).
  The banks with their wave archives (sound_data.sdat): bank 2 142,760 bytes, bank 3 164,672, bank 4
  129,148. **Two effect banks never fit at once** (2 + 4 = 271,908). The main heap (OS heap 0, 2 MB at
  0x02140540..) had only 225 KB free (largest block) at the command phase of a one-enemy battle, so a
  second buffer is not an option either.
- A switch costs **2 lag frames** for bank 2 or 4 and **3** for bank 3 (the read size). Measured with exec
  hooks: 0x020297D4 (battle main, a frame without a line is a lag frame), 0x02028234 (sound played), and
  0x020283D4 (the switch branch, r0 = the old bank). In every run, every switch gave 2 or 3 lag frames on
  the same frames as two NNS file reads from 0x02086B64, and no enemy action lagged without a switch.

What that means per action: a species whose action uses one bank lags once, on the first sound, and only
when the previous sound in the battle came from another bank (in a battle against one species: turn 1
only). The generic lunge plays 0x52 (bank 4, the move sound), 0x28 (bank 2, the attack sound), then 0x52
again, so it reloads twice **inside every turn** (3 times when bank 4 was not loaded): the temple battle of
1.2. Sounds come from three places: step sounds (step +6: func_02067448(12, kind, 0); kinds 1 and 3 read the
species table 0x02096EDC + 0x1C * species at +4 and +6), animation cel sounds (cel +4 of the slot data,
func_02032a0c, then func_02067448(12, kind, 1): kind 1 reads +8; the hopper Tick's 0x29 comes this way),
and the effect scripts of skills (func_0203162c, effect battlers 14+; kind 0x12 is 0x3A, the cast sound).

### 7.2 The fix (`enemy-preload`, off by default)

src/dsde/feat_enemy_preload.py. Both `bl func_020316e0` that start step 0 at the end of round state 6
(0x0202D840, 0x0202D874) call a cave first. For an enemy actor (battler 4..11) it predicts the first sound
of the action that needs a bank, in play order: per step, the step sound, then the cel sounds of the step's
animation (slot data at battle work +0x5C + 4 * slot, loaded by then: animation table at +8, 0xC per
animation, first cel +0, cel count +8; cel table at +0xC, 0x18 per cel). For a skill whose own steps play
none, the first target's effect script (work +0x78), with only the kinds that do not read a battler. If the
bank differs from 0x020B8564 it does what func_02028234 does (stop the flagged sound, pop, load, store the
bank) and then runs func_020316e0(12). The load's lag frames fall between the end of the camera turn and the
first step, where the screen is still, and the action's first sound finds its bank loaded.

It cannot remove a reload inside one action (the lunge's 4, 2, 4): that needs two banks in memory (7.1).
Not covered: party actors, the follow-up actor (round states 0x14..0x16), and the reaction sounds of round
states 8..11 (Jian's counter plays 0x42, bank 3).

### 7.3 Measured (forced battles of docs/re-enemy-attacks.md 1.1, two turns each)

Lag frames inside the enemy action (round state 7) per turn, turn 1 / turn 2; in brackets the lag frames the
fix moved to the still frame before step 0. Before = current build, after = `--with enemy-preload`; Fast.
Vanilla gives the same numbers as before (Tick not run on vanilla). For Druid and Gronk the third moved frame
falls on step 0's first frame, before the caster moves.

| Species (folder) | Bank sounds | Before | After |
|---|---|---|---|
| Ice Mongrel (020_Ice_Mongrel_a0_attack) | 0x5A (4) | 2 / 0 | 0 (2) / 0 |
| Onlooker (004_Onlooker_a0_attack, lunge 0x020952E4) | 0x4C (4) | 2 / 0 | 0 (2) / 0 |
| Bealzebub (044_Bealzebub_a0_attack, lunge 0x02095334) | 0x52 (4), 0x28 (2), 0x52 (4) | 6 / 4 | 4 (2) / 4 |
| Shreeker (008_Shreeker_a0_attack, hopper) | none | 0 / 0 | 0 / 0 |
| Tick (040_Tick_a0_attack, hopper, cel sound) | 0x29 (2) | 2 / 0 | 0 (2) / 0 |
| Shaitan (092_Shaitan_a0_attack, glide) | 0x4F (4) | 2 / 0 | 0 (2) / 0 |
| Druid (132_Druid_a0_skill18, caster) | 0x3A (3, effect) | 3 / 0 | 0 (3) / 0 |
| Sasquatch, boss (136_Sasquatch_a0_attack) | 0x55 (4) | 2 / 0 | 0 (2) / 0 |
| Gronk, boss (142_Gronk_a0_skill18) | 0x3A (3, effect) | 3 / 0 | 0 (3) / 0 |

- Normal speed (Bealzebub, Ice Mongrel, Druid, Gronk): the same numbers as Fast.
- Script frames (`enemy_anims_run`, Fast, turn 1 / turn 2): each turn-1 action is 2 or 3 frames shorter
  (Ice Mongrel 68 to 65, Bealzebub 37 to 34, Druid 138 to 135), turn 2 unchanged: the frames moved, the turn
  is as long as before.
- Frames (`frame_NNNN.png`, both screens every 2nd frame) identical at the same index: Shreeker 35 of 35,
  Bealzebub 27 of 28, Ice Mongrel 38 of 43, Sasquatch 80 of 86, Shaitan 86 of 117, Druid 47 of 78, Gronk 44
  of 68; the rest differ only in timing (the enemy's pose and effects one shot apart, and Jian's
  idle cel, which keeps its own phase), checked side by side for Shaitan and Druid. No new or missing
  content. All runs completed both turns.
- Temple battle (Delrich Temple by warp6, Jian's HP pinned, Manual, 8 enemy turns: Bealzebub-family row 45,
  Tick, Thanatos): lag frames inside enemy actions 26 before, 16 after; 10 moved to the still frame. The 16
  left are row 45's lunge reloading inside its turns (4 per turn); 3 more in round state 11 (the counter's
  bank 3 sound) are unchanged.

Recordings: build/p9/rec (after) and build/p9/rec_before; lag surveys build/p9/s_*.txt (not committed). To
re-measure, add `exec 0x020297D4 main`, `exec 0x020283D4 switch` and `exec 0x02028234 play` to a plan and
compare the logged frame numbers with the `rec` log (rec frame F of a turn is run frame start + F - 1).

Risk: the bank now changes up to one action earlier than before, so a sound of the previous action still
playing from the old bank stops sooner (vanilla stops it too, at the first sound that switches). Whether
any audible tail is cut was not checked (uncertain); listen on hardware before turning it on.

## Sources (remasters)

- Steam store page, LUNAR Remastered Collection: https://store.steampowered.com/app/3255380/LUNAR_Remastered_Collection/
- One More Game review (L2/R2, up to 3x): https://onemoregame.ph/2025/04/lunar-remastered-collection-review/
- RPG Site, Steam Deck impressions (trigger buttons in battle only; Touch version map and battle speeds): https://www.rpgsite.net/feature/17173-lunar-remastered-collection-steam-deck-performance-review-recommended-settings-vs-silver-star-story-touch-comparison-rog-ally
- RPG Site walkthrough (trigger buttons, trophy): https://www.rpgsite.net/guide/17159-lunar-remastered-collection-guide-lunar-silver-star-story-walkthrough
- RPGFan review (up to 3x): https://www.rpgfan.com/review/lunar-remastered-collection/
- PlayStation Blog (adjustable Battle Speed-Up option): https://blog.playstation.com/2025/03/18/lunar-remastered-collection-bringing-new-fans-to-an-old-favorite/
- Game Rant (speed up combat three times): https://gamerant.com/lunar-remastered-collection-improvements/
- Analog Stick Gaming review (toggle kept at max): https://www.analogstickgaming.com/game-reviews/2025/4/13/lunar-remastered-collection
- XboxAchievements guide (reset on load; search summary only, page returned 403): https://www.xboxachievements.com/game/lunar-remastered-collection/guide/
