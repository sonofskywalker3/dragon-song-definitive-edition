# Opening: wake-up call and scripted run out of the inn

Research and prototype for playtest feedback item 2 (docs/playtest-feedback.md): skip Jian's
self-introduction, have Cherenkov call from downstairs, then a scripted run from Jian's room (map 163)
through the inn hall (160) and lobby (155) out of the front door, with Jian's introduction shown as
text while he runs. Dialogue in the prototype is placeholder text (tone rules: docs/style-rules.md).

Prototype: feature `opening-run` in `src/dsde/feat_opening.py`, registered in `FEATURES` but not in
`DEFAULT_FEATURES`. Test plan: `emu/plans/opening_run.plan` (New Game, no save).

## 1. Map 196 and the end of the vanilla wake-up

The op `10 0002 80C4 0064` at script 001 0x63C8 is dead code: it is never executed.

- Op 0x00 is not a yield. Its handler (func_02041808) advances the pc, clears the running flag
  (ctx +0xE8) and the map request (ctx +0x268): the event ends. The wake-up ends with op 0x00 at
  0x63C4, right after "Right then! I'd better go looking for Lucia...", and nothing jumps to 0x63C8
  (`dsde.script --reach` no longer lists it now that 0x00 counts as a stop).
- Emulator (`emu/plans/opening_vanilla.plan`, vanilla ROM, shots build/par_o/vanilla/ov_*.png): after
  that message the player has control in map 163; the map id never changes to 196.
- The operand would mean map `0x80C4 & 0x1FF` = 196, facing `0x80C4 >> 13` = 4 (down), entrance 100.
  Map 196 belongs to script 005 (map table byte +2), the San Coliseum / Healriz group (maps 186 to 198);
  its entry handler (script 005 0x2F0C -> 0x2F4C) plays the "Strange Girl" scene at 0x3EAC once flag
  0x33 is set. The jump looks like a developer shortcut left behind.

## 2. How a map's entry event is found

- Map table at 0x02091D18, 0x28 bytes per map, maps 0 to 259. Byte +2 is the map's script (an entry of
  script.dat). func_0201d92c loads it on a map change (func_02041a68(ctx, 6, script)).
- On entry the field (func_0201e6a0) restarts the script from its first op (func_02041988) with
  var 0 (ctx +0x204) = 1 and var 1 (ctx +0x206) = the map id. Talking to an NPC sets var 0 = 10
  (0x4D for a Gad's Express delivery) and var 1 = the NPC id. Each script file starts with a dispatcher:
  script 001 at 0x54B4 sends var 0 == 1 to 0x56B4, which handles map 163 (0x5718) and 164 (0x56D8) and
  stops for every other map. Maps 160 and 155 have no entry event.
- A script cannot keep running across a map change. Op 0x10 (func_020408dc) stores its request at
  ctx +0x268 and stops the script; the field then acts on it: type 2 calls func_0201d8f8(map & 0x1FF,
  x 9999, entrance, facing = bits 13..15) and fades out. The new map's entry event (above) is where a
  multi-map scene continues. A flag tells the entry handler whether the scene is in progress.
- Door links: map table +0x20 points to 12-byte records {u16 door, u16 9999, u16 entrance, u16 facing,
  u16 map, u16 0}, groups ended by 0xFFFF. Room 163 -> hall 160 entrance 400 (facing 3); hall -> lobby
  155 entrance 101 (facing 3); lobby front door -> map 285 entrance 0. The script's own later warp from
  the room (script 001 0x6EA4, `a0609001`) uses the same hall entrance.
- Map 285 (0x11D) is past the map table: it is the Port Searis town map, the "Select place to go" menu
  (Inn 1F, Restaurant, Jose's house, Isabella's house), not a walkable street.
- Op semantics checked in the handlers (src/dsde/script.py names fixed): 0x13 jumps if all its flags
  are set, 0x14 if any is set, 0x15 if none is set (0x14 and 0x15 were swapped). 0x0D compares two
  operands and jumps, 0x0E does the same as a call. The low byte of their mode word gives each operand's
  source in 2 bits (0 immediate, 1 s8 at ctx +0x1F4, 2 s16 var at ctx +0x204, 3 s32 at ctx +0x224), the
  high byte the comparison (0 ==, 1 !=, 2 >, 3 >=, 4 <, 5 <=, 10 and, 11 or). Flags are a bit array at
  the start of the script context (flag n in word n >> 5).

## 3. Text while Jian moves: yes

Op 0x44 only hands the route to the actor (player: block 0x020B6BE4 +0x108) and the field moves it
every frame; op 0x0F blocks only the script. So `0x44 route; 0x0F msg; 0x45 wait` shows the box while
Jian runs. Seen in `opening_run` (build/par_o/run1/run.log): the route pointer 0x020B6CEC was non-zero
from frame 8587 to 8644 while the aside box was open, and Jian moved from (174,154) to (275,198) under
it (shots op_12 to op_14). A box only closes once its text has finished typing; when the route ends
first, Jian stands until A, then op 0x45 returns at once.

Route units, measured: each entry is (direction, ticks, speed). One tick moves speed / 0x1000 pixels:
2 px straight at 0x2000, and (1.75, 0.875) px on a diagonal (the 2:1 screen diagonal, the same as
walking with the D-pad). The legs follow the owner's walked path, so collision was not tested.

## 4. Implementation (as built in the prototype)

All in script 001; appended code goes at 0x7620, after the two messages `text-edits` moves to the end
of the file (0x7560..0x761C, the Balam renames). `opening-run` writes those same bytes too, so the
layout is identical with or without `text-edits` and in either feature order (checked by applying both
orders to the vanilla file).

In place (each patch checks the vanilla bytes):

| Offset | Vanilla | New |
|---|---|---|
| 0x62CC | msg "....It's morning...?" | jump to the new wake-up (0x7620) |
| 0x54C0 | dispatcher: map entry -> 0x56B4 | map entry -> new block (checks hall and lobby, then 0x56B4) |
| 0x5F90 | Cherenkov's first lobby line (0x0BD2, repeats the oversleep joke) | placeholder line |

Appended code:

1. Wake-up: Cherenkov's call (placeholder), the vanilla waking pose and its 90-frame wait (copied from
   0x62D4..0x6303, Jian with a "?" balloon), Jian's reply, Cherenkov, Jian. Sets the vanilla flags 0x1
   (woken up; the room's entry event skips the wake-up from then on) and 0x1E2, plus RUN_FLAG 0x1DF.
   Resets the pose (vanilla 0x6318..0x6327), starts the room route, shows the first aside, waits for
   the route, then `goto_map 160, entrance 400, facing down-right`.
2. Entry block: `if var1 == 160 goto hall`, `if var1 == 155 goto lobby`, else the vanilla handler.
   Hall and lobby legs start with `if none of [0x1DF] goto 0x56B4`, so outside the run both maps behave
   as before (seen: re-entering the lobby from the town map gives control at once).
3. Hall leg: fade in (op 0x1D 3, 0x80: the field leaves the screen dark for the entry event), route,
   aside, wait, `goto_map 155, entrance 101`.
4. Lobby leg: fade in, route to the front door, aside, wait, clear 0x1DF, `goto_map 285, entrance 0`.
   Control returns on the town map menu, which is what the front door leads to.

The self-introduction (portrait screen, op 0x35, the UI calls 0x74E8 and 0x7520) and "Right then!"
are skipped: the jump at 0x62CC leaves 0x62D4..0x63C4 unreached. RUN_FLAG 0x1DF: no script sets or
tests it (0x1D1..0x1E0 are free in every script); 0x1E0 + n are the destination flags read by code,
and no code check with a constant uses 0x1D0..0x1DF.

Placeholder text and route lengths are constants at the top of feat_opening.py; a page break inside a
message is a new item in its tuple. Lines must stay within 30 characters (feat_text.py).

## 5. Prototype status

Verified in the emulator from New Game (`opening_run`, build/par_o/dsde_o.nds = default features +
`opening-run`, log build/par_o/run1/run.log, contact sheet build/par_o/run1/opening_sheet.png):

| Stage | Frames | Shots (build/par_o/run1/) |
|---|---|---|
| Wake-up call, Jian's "?" pose, reply, "Get moving!", "I'm up!" | map 163 from 8159 | op_02 to op_11 |
| Room run with aside, out of the door | route 8587..8644 | op_12 to op_14 |
| Hall run (Inn 2F) with aside, to the stairs at (72,278) | map 160 at 8699, route to 8905 | op_16 to op_20 |
| Lobby run (Inn 1F) past Cherenkov's counter to the door at (371,317) | map 155 at 8937, route to 9097 | op_21 to op_25 |
| Town map menu, player in control | map 285 at 9129 | op_28 |
| Back to Inn 1F from the menu, walk, out again: no rerun | 9225, 10142 | op_29 to op_control |

Not seen: Cherenkov's replacement lobby line (two attempts did not reach the counter's talk spot; the
built script shows the op at 0x5F8C pointing at the new text).

## Open questions

- Control returns on the town map menu (the door's own destination). If the owner wants control at
  the door instead, end the lobby leg without the map change (clear the flag and stop; the player then
  walks out).
- Does Jian use his running animation on a 0x2000 route? The shots look like his walk cycle moving at
  double speed; not compared with field running.
- Placement of the asides (one per map now) and their lengths against the leg lengths; the first box
  types slower than the room leg runs.
- Cherenkov stands in the lobby during the run and says nothing; his first-talk line needs final text.
- Sound: no door sound on the scripted map changes (vanilla doors may play one).
