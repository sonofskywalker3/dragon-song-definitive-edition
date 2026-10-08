# Field bottom screen (touch HUD): portrait, hint tag, crystal, watch (research 2026-10-08)

Static analysis of the USA ARM9 (extract/arm9/arm9.bin, decomp build/arm9_decomp_annot.c) plus BizHawk runs on
the vanilla ROM and on a copy of the current hack (build/hud/hudhack.nds). Runs used Jeff's own save
(build/gifs/jeff/jeff.SaveRAM: Thieves' Woods, map 1, kills 5/5) and the post-intro save (Jian's room, map 163).
Plans: emu/plans/hud_look.plan, hud_dungeon.plan, hud_enemies.plan, hud_crystal.plan, hud_edges.plan.
Screenshots: build/hud/ (cmp_mode.png, cmp_town_vs_dungeon.png, cmp_tag_tap.png, pulse_vanilla_4frames.png,
v_crystal.png; raw shots in build/hud/v_*/ for vanilla and build/hud/h_*/ for the hack).

## Summary

| Thing on screen | HUD button | Touchable | What it is |
|---|---|---|---|
| "Menu" note | 0 (cell 13), quill 5 (anim 0) | yes, rect 64x24 | same as X: opens the menu |
| Pocketwatch body | 4 (cell 6 open, 7 closed) | no | open on enemy maps, closed elsewhere |
| Pocketwatch hand | 3 (cell 12, affine 0) | no | Virtue clock (frozen at 12 o'clock in the hack) |
| Row of small boxes | BG tiles (func_020719dc) | no | map's enemy total, ticked per kill |
| Jian portrait | 2 (cell 10 Combat, 11 Virtue) | yes on enemy maps, rect 48x48 | **the Combat/Virtue switch** (same as R) |
| Orange tag | 7 (cell 15) | no | backing for the figures |
| Two small figures | 6 (cell 14, affine 5) | yes, rect 48x48 | same as Y: the think-aloud hint (script 018) |
| Crystal in the metal box | 1 (anim 2 Combat, anim 1 Virtue) | no | **Combat/Virtue mode lamp**, not a proximity detector |
| Party HP/MP panel | BG (func_0207184c) | no | |
| Screen edges | none | yes | a touch D-pad: hold the stylus at an edge to walk |

- 1: the portrait is the Combat/Virtue toggle; vanilla tap in a dungeon flips 0x020B4848, in a town nothing. Look
  changes per mode (blue backing Combat, orange Virtue). The hack's 0x0201F128 patch is why it is dead.
- 2: the figures' "bounce" is a scale pulse on affine matrix 5, every field frame, forever, shared with the Menu
  note and the portrait. No condition stops it.
- 3: the crystal shows the battle mode (blue gem Combat, white glow Virtue) and is hidden off enemy maps (the grey
  stone is the background). No enemy distance is read anywhere.
- 4: watch open = `func_02071c4c(-1)`: map id 0..0x96, not map 4, and at least one enemy spawn point.

## HUD button set (confirmed)

- Button set at 0x020B7F28 (func_0206f3a4 builds it; func_020276fc draws it every frame from 0x0202211x):
  +4 active mask, +8 "scroll with camera" mask, buttons at +0xC + id*0x30. Button: +0 type (2 = cell, 3 =
  animated cell), +2 OAM flags, +4 x, +6 y, +0xC graphics handle, +0xE cell (type 2) or +0xD animation (type 3),
  +0x14/+0x16 delayed cell change (cell, frames; func_020275b4 with a non-zero 4th argument), +0x18..+0x28 slide
  from/to with timer, +0x2C..+0x2F touch rect (dx, dy, w, h; set by func_02027484, enabled by bit 0 of +0xB).
- Static table 0x0209E148, 8 bytes per button (cell, x, y, 1); cell >= 0x100 means an animated cell (type 3):

| id | cell | x, y | notes |
|---|---|---|---|
| 0 | 13 | 158, 40 | Menu note; rect (-32, -12, 64, 24) at 0x0206F4CC |
| 1 | 0x101 | 195, 117 | crystal; animation `2 - mode` (0x0206F584) |
| 2 | 10 | 188, 77 | portrait; cell `10 + mode` (0x0206F5A4); rect (-24, -24, 48, 48) at 0x0206F568 only on enemy maps |
| 3 | 12 | 73, 54 | watch hand; flags \|= 0x2020 (affine matrix 0) at 0x0206F554 |
| 4 | 6 | 73, 54 | watch body; cell 7 (closed) at 0x0206F518 when not an enemy map |
| 5 | 0x100 | 158, 40 | Menu quill (animation 0) |
| 6 | 14 | 82, 123 | two figures; rect (-24, -24, 48, 48) at 0x0206F4EC |
| 7 | 15 | 93, 120 | orange tag |

- func_0206f3a4 (0x0206F3A4): clears the set, creates buttons 0..7; buttons 0, 6, and (on enemy maps) 2 get OAM
  flags 0xA025 (0x8000 \| 0x2025 = affine, matrix 5), others 0x8000. Then sets the rects; then
  `func_02071c4c(-1)` at 0x0206F4F4 decides open (rect for 2, hand flags, crystal and portrait frames from the
  mode byte) or closed (body cell 7, hide buttons 1 and 3 with func_02027ae8). Ends with func_0207184c (HP/MP
  panel and kill boxes). Called on map load when the load flags include 0x100 (0x0201E414, after the enemy table
  init at 0x0201E0EC), on menu return (0x0201EC18), and from func_0206f5d0.
- Touch input, field state 0x14 (0x0201F088): `id = func_020273b0(0x020B7F28, &touch)` returns the first active
  button whose rect contains the stylus; then R (0x100) forces 2 and Y (0x800) forces 6. id 0 or X -> menu (state
  0xA6); id 2 -> mode toggle (0x0201F114..); id 6 -> state 0x20 (script 018). No other id is handled.

## 1. Portrait = Combat/Virtue switch (confirmed)

- Button id 2. Its touch rect exists only when `func_02071c4c(-1)` is true (0x0206F540 path), so in towns the
  portrait is just a picture. Handler: the R/portrait block at 0x0201F114..0x0201F168 (docs/re-field-battle.md 2.2):
  needs `func_02071c4c(-1)` (0x0201F120, branch 0x0201F128) and no stylus last frame (0x020B6A18), flips
  0x020B4848, sets crystal animation `2 - mode` and portrait cell `10 + mode`, plays sound 0.
- Vanilla run (hud_dungeon.plan, map 1): tap (188, 77) mode 0 -> 1, tap again -> 0, R -> 1, R -> 0. Town run
  (hud_look.plan, map 163): tap -> stays 0. Hack: every tap and R leaves 0 (one-battle-mode patch at 0x0201F128).
- Looks per mode (cmp_mode.png): Combat = blue backing (cell 10) and blue gem crystal; Virtue = orange backing
  (cell 11) and glowing white crystal. On enemy maps the portrait also pulses (affine 5); in towns it does not.
- The hack leaves the mode at 0, so the HUD always shows the Combat look although battles use Virtue rules.

Proposed: either make it inert (0x0206F3E4 `cmp sl, #2` -> `cmp sl, #0xFF` so it never pulses, and NOP the rect
call at 0x0206F568 so it is not a target), or give it a new job in the 0x0201F114 block (the hack already branches
past the toggle at 0x0201F128; put the new action there, e.g. Status or party chat). Optional cosmetic: show the
Virtue look always by loading `mov r2, #1` instead of the mode byte at 0x0206F574 and 0x0206F58C (crystal
animation 1, portrait cell 11).

## 2. Tag figures = Y hint; the pulse (confirmed)

- Tapping the figures (button 6) is the same as Y: both set id 6 (0x0201F0A0 `movne r0, #6`), which goes to
  state 0x20 and script 018. Vanilla and hack show the same hint (cmp_tag_tap.png: "Well, he ran off toward
  Perit Villa"). The rect is 48x48 around (82, 123): the figures, not the whole tag.
- The "bounce" is a scale pulse, not a frame animation: func_0206f7c4 (0x0206F7C4), called every field frame at
  0x02022108 (outside the state 0x14 block), adds 0x800 to F+0xC4 (0x020B6CA8) and sets affine matrix 5 to scale
  `0x1000 + sin(F+0xC4) >> 3` (sine table 0x02089158), so about +-12% over 32 frames. Every button drawn with
  matrix 5 pulses: Menu note, figures, and the portrait on enemy maps (pulse_vanilla_4frames.png).
- No condition: no flag, map, or hint state is read. F+0xC4 is only reset to 0 when func_0206f3a4 rebuilds the HUD.
- Script 018 is a flag decision tree (0x5124 on: ops 0x13/0x14/0x15 on story flags such as 0xC, 0xD, 0xB, 0x1C,
  0x14, 0x193, 0x15, 0x194, 0x22..0x25, 0x28, 0x1F, 0x195, 0x26A..0x26F, then one 0x0F message). It keeps no record
  of what it said, so vanilla has no notion of "new hint".

Proposed:
- Still frame for the figures only (cheapest, one word): 0x0206F3FC `cmp sl, #6` -> `cmp sl, #0xFF`. Button 6
  then gets plain 0x8000 flags (no affine) and stays at scale 1; its rect is set separately, so the tap still works.
- Stop all three pulses: 0x0206F7E0 `add ip, ip, #0x800` -> `mov ip, #0` (sine of 0 = 0, scale 1.0).
- Pulse only for a new hint: hook the call at 0x02022108 with a cave that writes button 6's flags halfword
  (0x020B8056 = 0x020B7F28 + 0xC + 6*0x30 + 2) as 0xA025 when a "hint new" bit is set and 0x8000 otherwise, then
  tail-calls func_0206f7c4. Set the bit from a hook on the script op 0x19 set-flag handler (0x020405D8, flag id at
  op+2) when the flag is in a build-time bitmap of every flag script 018 tests (parse it with dsde.script);
  clear it on the id 6 path at 0x0201F0A0..(state 0x20). Keep the bit in a free story flag so it is saved
  (uncertain which flag is free in the hack; check diag_flags_ours). False positives are possible (a tested flag
  that does not change the chosen line), never false negatives for script-set flags. Flags set by engine code
  (not op 0x19) would be missed (uncertain whether 018 tests any).

## 3. Crystal = mode lamp, not a proximity detector (confirmed)

- Button 1, an animated cell (type 3). Its animation is written only by the mode toggle (0x0201F14C block) and
  func_0206f3a4 (0x0206F584): animation `2 - mode` (2 = blue gem, Combat; 1 = white glow, Virtue). Off enemy maps
  it is hidden (0x0206F528), and the background's grey stone shows: that is the "grey in towns".
- Run hud_crystal.plan (vanilla, map 1 with kills poked to 0 so 5 symbols spawned): a bus-write trace on its
  animation bytes (0x020B7F70/71) logged nothing while an enemy symbol was moved from far to beside Jian, and the
  crystal looked the same (v_crystal.png). Only its own frame timer (+0x10) ticks.
- The only enemy distance check in the field is the encounter test at 0x02021F40 (`< 0xA000`, 10 px, per axis),
  which starts a battle; nothing feeds the HUD.

## 4. Pocketwatch: open/closed, hand, run gauge

### 4a. What decides open or closed (confirmed)

- `func_02071c4c(-1)` (0x02071C4C) is true when F+0xC10 (0x020B77F4, number of enemy spawn points on the map) is
  not 0, the map id (s16 0x020B6BE4) is 0..0x96, and the map is not 4. func_0206f3a4 reads it at 0x0206F4F4.
  Open: body cell 6, hand (button 3) and crystal shown, kill boxes drawn. Closed: body cell 7, hand and crystal
  hidden.
- Towns are maps 0x97 and up (the guidebook script 027 uses the same < 0x97 test for its Fields page), so they are
  always closed; dungeon rooms without spawn points (and map 4, uncertain what it is) are closed too. Seen:
  map 163 closed, map 1 open (cmp_town_vs_dungeon.png, vanilla and hack identical).
- The place-selector maps (262, 285) are >= 0x97: closed if drawn at all (no free movement there).
- The same predicate also gates the mode toggle (0x0201F120), enemy graphics loading on entry (0x0201D92C body,
  call at decomp line 25956) and a load flag in func_0201d6fc; do not change func_02071c4c itself.

### 4b. Driving the hand from the run timer (confirmed sites; behaviour untested)

- The hand is button 3 with affine matrix 0. Its rotation is set only at 0x02021FDC..0x0202200C, in field state
  0x14 and only when func_0206ec54 returns an enemy table entry (any map 0..150):
  `func_0201ace4(*0x020AFF50, 0, 0x1000, (0x10000 - clock * 0x10000 / limit) & 0xFFFF, 0)`.
  The division is at 0x02021FE8 (func_0201618c), `rsb r0, r0, #0x10000` at 0x02021FEC.
- In the hack the no-virtue-clock patch makes 0x02021F80 `b 0x02021FDC`, so 0x02021F84..0x02021FD8 (22 words)
  is dead and the clock stays 0 (hand at 12 o'clock).
- Run state: player +0x40 (0x020B6CF0) bits 5..12 (feat_run.py: 0 ready, 1..90 running, 91..180 cooldown,
  one tick per 2 frames).
- Patch: 0x02021FDC `ldrh r0, [r4]` -> `b 0x02021F84`, and in the dead block:
  ```
  ldr   r0, =0x020B6CF0
  ldr   r0, [r0]
  mov   r0, r0, lsl #19
  mov   r0, r0, lsr #24        ; c = run state
  cmp   r0, #RUN_TICKS
  rsbhi r0, r0, #RUN_TICKS + COOLDOWN_TICKS   ; cooldown: wind back
  ldr   r1, =0x10000 / RUN_TICKS             ; 728 for 90 ticks
  mul   r0, r1, r0
  b     0x02021FEC             ; rsb, then the vanilla rotation call
  ```
  The hand sweeps one full turn over the 3 s dash and winds back over the cooldown (rotation sense as the vanilla
  clock; flip with `rsb` removal if it runs the wrong way). With different RUN/COOLDOWN lengths, scale each half
  by its own constant.

### 4c. Unlimited running where the watch is closed (proposed)

- Predicate (one cave, used by both the HUD and the run code), `watch_open()`:
  `func_02071c4c(-1) && !(e = func_0206ec54(), e && e->kills >= e->total)` (entry +4 kills, +5 total).
  Every map 0..150 is in a dungeon group (table 0x02091C78 covers 0..151), so the entry exists wherever the watch
  can be open.
- Run code (feat_run.py part 1, the 0x02024BF8 block, about 15 free words): after loading the state, call a cave
  that returns `!watch_open()` (preserve r0..r3); when it is set, clear the state bits in `[r2]` and branch
  straight to 0x02024C58. `[sp, #8]` already holds B-held (vanilla clears it when no direction is held), so
  vanilla's 2x run continues with no timer.
- HUD: 0x0206F4F4 `bl func_02071c4c` -> `bl watch_open`. Leave 0x0206F3F0 (portrait) alone.

### 4d. Close the watch when the area is cleared, reopen on re-entry (proposed)

- Kill counting after a battle: field state 0x7B, 0x02020900..0x020209A8. The map reload (0x02020870,
  `func_0201d92c(map, 0xFFFFFF5E, 0)`, flag 0x100 set, so func_0206f3a4 runs) happens before this, so the HUD
  is built with the old kill count. Then 0x02020950 adds the kill, 0x02020960 compares kills with total
  (0x0202096C was the area-clear flag store, NOP in the hack's no-clear-refill), and every result path ends at
  0x020209A8 `bl func_0207184c` (HP/MP panel and kill boxes).
- Patch: 0x020209A8 `bl 0x0207184C` -> `bl 0x0206F3A4`. func_0206f3a4 rebuilds the whole HUD and itself ends
  with func_0207184c, so after the winning battle the watch closes (body cell 7, hand and crystal hidden) and
  running becomes unlimited through 4c. Alternative scoped to the clear only: 0x0202096C -> `bleq 0x0206F3A4`
  (flags still from the `cmp` at 0x02020960; r0 is reloaded at 0x02020970). Uncertain: func_0206f3a4 clears all 32
  button mask bits (func_02027b78); nothing else should be active in state 0x7B, but test it.
- No open/close animation exists: vanilla only swaps cell 6/7 instantly. The button engine can delay a cell swap
  (+0x14/+0x16) or slide a button (+0x18..+0x28), so a short effect is possible; whether the cell bank holds
  in-between lid frames is unknown.
- Re-entry: with restock-on-entry the enemy entry is re-rolled (kills 0) at 0x0201E0EC, before the HUD build at
  0x0201E414, so the watch opens again and the timed run returns. The run state is already reset per map
  (cave_run_area). Kills never fall in the hack (no Virtue clock), so a cleared map stays closed until you leave.

## 5. Other touch areas (confirmed)

- Menu note (button 0): same as X, plays sound 1, shows button 8 (cell 9 at 140, 37) and goes to state 0xA6.
- Screen edges: when no button is hit and the stylus is down, 0x0201F1xx (decomp line ~26895) turns the touch
  into D-pad bits: x < 16 Left, x >= 240 Right, y < 16 Up, y >= 176 Down; corners (x < 32 or x >= 224 with
  y < 32 or y >= 160) give diagonals. hud_edges.plan: right, top, and bottom edges moved Jian (the left-edge touch
  did not; probably a wall, uncertain). B with an edge touch should run (untested).
- The watch, crystal, kill boxes, tag backing, and HP/MP panel have no touch rect (only buttons 0, 2, and 6 get
  one); tapping the watch and the crystal changed nothing in vanilla.

## Built: `pocketwatch` (2026-10-08)

Sections 4b to 4d are built in src/dsde/feat_watch.py and feat_run.py and verified in BizHawk (docs/status.md,
plans emu/plans/watch_*.plan). Differences from the proposal:
- The hand code replaces 0x02021F78..0x02021FDC (the whole Virtue clock block, so it does not depend on
  `no-virtue-clock`) and joins vanilla at 0x02021FF0, past the `rsb` at 0x02021FEC: with the `rsb` the hand ran
  counterclockwise during the dash.
- The after-battle rebuild uses 0x020209A8 (every result path), not the scoped 0x0202096C; no side effect seen.
- A door poke from a map to the same map does not restock (kills stayed 5 / 5); a door to another map and back
  does (map 1 -> map 4 entrance 101 -> map 1 entrance 101).
- Test pitfall: a symbol pulled onto Jian drops its chest on his spot, and the chest's collision then holds him.

## Open items

- Pick a saved free flag for "hint new" and confirm script 018 only depends on script-set flags.
- What map 4 is (closed watch although inside group 0).
