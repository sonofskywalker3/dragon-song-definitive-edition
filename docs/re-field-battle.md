# Reverse engineering: field running, Combat/Virtue mode, targeting, party, save lock

Static analysis of the USA ARM9 binary (extract/arm9/arm9.bin, loaded at 0x02000000, no overlays), done 2026-10-05.
Nothing here has been run in an emulator yet. Each finding is marked **confirmed** (read directly in code or script
data, evidence given) or **uncertain**. File offset in arm9.bin = address - 0x02000000.

## Tools

- `uv run python -m dsde.arm9 annotate` writes build/arm9_decomp_annot.c: the Ghidra decompilation with every
  `DAT_xxxxxxxx` literal-pool reference followed by `/*=value*/`, so globals can be grepped by their real address.
- `uv run python -m dsde.arm9 refs <lo> <hi>` lists every function whose literal pool loads an address in a range.
- `uv run python -m dsde.arm9 dis <func or address>` disassembles a function with capstone (dev dependency).
- `uv run python -m dsde.script build/unpacked/script/NNN.bin [--text] [--reach]` disassembles an event script.

## Key globals (confirmed)

| Address | What |
|---|---|
| 0x020B05B0 | G, the game state block (saved data lives inside it) |
| 0x020B05BC | G+0xC, u16 frame counter, +1 per main loop |
| 0x020B464C / 50 / 54 | party slots (G+0x409C+4i): s16 character id (-1 empty), s16 slot index |
| 0x020B4658 + id*0x5C | character structs (id 0 Jian, 1 Lucia, 2 Gabryel, 3 Flora, 4 Rufus) |
| 0x020B4824 | money (G+0x4274) |
| 0x020B4848 | Combat/Virtue mode byte (G+0x4298): 0 Combat, 1 Virtue |
| 0x020B4880 | play time in frames (60 per second) |
| 0x020B4904 / 06 / 08 | dungeon group, map index in group, 32 x 6-byte per-map enemy table |
| 0x020B4640 | pointer to the main event script context (story flag bits at its start) |
| 0x020AFF74 | pad struct: +6 newly pressed, +8 released, +0xA held |
| 0x020AFF84 | main/field state block, field state at +0x8C |
| 0x020B6BE4 | field state block F (s16 current map id at +0) |
| 0x020B6CB0 | the player's field object |
| 0x020B6FD4 | 32 map objects x 0x40 bytes |
| 0x020B8550 / 8620 / 8640 | battle round context / battle stat records (0x6C) / battlers (300 bytes) pointers |
| 0x020B85B8 | battle context (mode copy at +8) |
| 0x020B8800 | battle touch command UI state |

## Summary

1. **Running** is B held plus a direction; the microphone is unrelated (it is the battle Run command). Running is
   exactly 2x walking speed (the movement step runs twice a frame). Every 180 frames of running (3 seconds at 60 fps)
   each party member loses 1 HP, floored at 1; running is refused while anyone is at or below a third of max HP.
   Two branch patches remove the cost; a timed run plus cooldown fits in place in the freed code.
2. **Combat/Virtue**: mode byte 0x020B4848, toggled by R or the touch button. In Virtue each kill gives EXP and counts
   toward the map's 5 to 7 enemy total; in Combat kills give item rolls and are not counted, so the spawner refills the
   map within 32 frames. The Virtue clock (3600 ticks, 60 s at 60 fps) revives one kill each time it fills. Blue chests
   already check `kills >= total`. Area clear gives +30% HP/MP, not a full heal. Single-instruction patch points given.
3. **Attack targeting**: the player never picks. When the attacker's turn starts the game picks the lowest-HP front-row
   enemy 70% of the time and a random one 30%. Targets are chosen at execution, so a single attack never whiffs; a hit
   inside a multi-hit action whiffs if its target already died. A single-ally target picker page already exists in the
   touch UI and is the model for an enemy picker.
4. **Party**: script ops 0x1B (join) and 0x1C (leave) only edit the slot shorts; character structs (level, EXP, gear)
   are untouched, so leaving members keep everything. EXP goes only to living battle party members, full amount each.
   Level-up never asks for a choice. Rufus' level 15 is hard-coded at New Game.
5. **Save lock**: Save is disabled by story flag 0xCF or by being on maps 79 to 82 or 150. Flora's Underground Tunnel
   line sets 0xCF (script 010 at 0x3F50) as a "line already said" marker, and nothing ever clears it: that is the US
   save glitch. The Lind fortune teller never touches 0xCF (it sets drop-luck flags 0xD1 to 0xD5).

## 1. Field running

Player field update: `func_02024b34(player, input_override)` at 0x02024b34, called once per field frame from the field state machine `func_0201e6a0` (state 0x29, `func_02024b34(0x020B6CB0, 0xffff)` path also used for scripted moves). The player object is at 0x020B6CB0. All addresses below are in arm9.bin (file offset = address - 0x02000000).

### How running is triggered (confirmed)

- Running is the **B button held** while a direction is held. Nothing else.
  - 0x02024b48 reads the held-keys halfword from the pad struct at 0x020AFF74 (`+0xA` held, `+0x6` newly pressed, `+0x8` released; filled by `func_0201a2f4` from REG_KEYINPUT 0x04000130 and the ARM7 extra keys at 0x027FFFA8).
  - 0x02024bcc `ands r0, r5, #2` / 0x02024bd4 `strne r0, [sp, #8]`: the "running" flag on the stack is `held & KEY_B`.
  - If the direction table lookup (0x0208D9F4) gives -1 (no direction), the flag is cleared, so standing still with B held is not running.
- **The microphone has nothing to do with field running** (confirmed). The only caller of the mic-blow detector `func_0206bafc` is the battle command input `func_0203a34c` (0x0203a34c), where blowing into the mic picks command 1 for the whole party (the battle Run/escape). The detector counts 8-bit mic samples outside 0x20..0xE0 after a 30-frame warm-up and fires when the count passes 9. Mic sampling is started by `func_0206bc0c` (from `main` and `func_0203add0`) and stopped by `func_0206ba74`.

### Running is refused at low HP (confirmed)

0x02024bfc to 0x02024c54: if B is held, for each of the 3 party slots (`func_0206e620(slot)` returns the character struct or 0), if `HP <= maxHP / 3` (magic 0x55555556 = divide by 3), the running flag is cleared and player `+0x40` gets bits 0x6000 (the "tired" pose). This is the "cannot run below a third of HP" rule from the guides.

### Run speed (confirmed 2x walk; absolute speed likely)

- The movement body is a loop `do { ... } while (local_5c < 2)` (counter at `[sp, #0x1c]`, compare at 0x02025234 `cmp r0, #2`). When not running it `break`s after one pass (0x02025184 `beq 0x20256b0`). When running it runs **twice per frame**, so running is exactly 2x walking speed on the same terrain.
- The per-step distance comes from the cosine/sine tables pointed to by 0x020A7878 / 0x020A7874 (0x1000 at angle 0, 0x0B50 on diagonals), times the terrain multiplier table 0x0209E034 (`0x1000, 0xA66, 0x99A, 0x99A` = 1.0, 0.65, 0.6, 0.6). Positions are 20.12 fixed point in pixels, so walking is likely 1 px/frame and running 2 px/frame (uncertain only because Ghidra misreads the argument list of the step routine `func_02025ed0`).
- Walk animation advances `+2 mod 0x60` per frame; running advances `+1 mod 0x3C` per sub-step (twice a frame).

### HP drain (confirmed)

The drain counter is 8 bits at player `+0x40`, bits 5..12 (`(flags & 0x1fff) >> 5`). Disassembly:

```
02025188  ldr   r0, [sp, #0x1c]        ; sub-step index
02025194  add   r0, sb, #0x40
0202519c  bic   r1, r1, #0x6000
020251a0  orr   r1, r1, #0x2000        ; running pose
020251a8  bne   #0x2025228             ; only count on the first sub-step
020251ac..020251cc                      ; counter = counter + 1 (bits 5..12)
020251dc  cmp   r1, #0xb4               ; 180
020251e0  blo   #0x2025228
020251e4..020251f4                      ; counter = 0
020251f8  mov   r0, r6                  ; for slot 0..2
020251fc  bl    #0x206e620              ;   char = party character in slot
02025208  add   r0, r0, #0x10           ;   &char.HP
02025214  bl    #0x20224bc              ;   approach(&HP, 1, 1): HP - 1, never below 1
02025224  bl    #0x207184c              ; redraw the top-screen party HP/MP panel
```

- One tick per frame while B and a direction are held (even when walking into a wall). At **180 frames** every party member loses **1 HP**, floored at 1 (running can never kill).
- The game logic runs at 60 fps (one `VBlankIntrWait` per `main` loop iteration; the play-time counter at 0x020B4880 counts frames and caps at 0x0CDFD7F0 = 999:59:00 at 60 fps). So the drain is **1 HP per 3 seconds of running** at full speed, not 5. The reported "about 5 seconds" is probably field slowdown or loose timing (uncertain; an emulator frame count settles it).
- The counter is never reset when you stop running, so partial progress carries over between runs.
- The drain is flat: it does not scale with max HP or level (matches TV Tropes / DCGB).

### Other field HP drains found nearby (confirmed, not running)

- `func_02024b34` tail: in area groups where `func_0206ef50` (terrain bitmap at 0x02091AF8 / 0x02091B78) is true, every 20 moving frames (counter byte 0x020B4852, `> 0x13`) `func_0206ed94(1)` takes 1 HP from everyone (floored at 1). Probably damaging floors.
- In area group 4 (`func_0206f028() == 4`, map id range from table 0x0209E118), byte 0x020B4854 counts frames and every 250 frames takes 1 HP from everyone unless item 0x185 is owned (`func_0206ba54(0x0213B930, 0x185)`). Looks like an environmental hazard (heat or cold) with a protective item.
- Map hazards in `func_02022f98` (object types 6, 7, 0xB) also call `func_020224bc(&HP, 1, n)`.
- `0x020B484A` is a countdown that, while non-zero, swaps left/right and up/down (`func_0201a358`): a field confusion effect.

### Patch plan

Remove the HP cost (two instruction patches, both ARM):

| Address | Original | Patch | Effect |
|---|---|---|---|
| 0x020251E0 | `blo 0x2025228` | `b 0x2025228` (0xEA000010) | the 180-frame drain never fires |
| 0x02024BF8 | `beq 0x2024c58` | `b 0x2024c58` (0xEA000016) | skip the HP <= 1/3 "too tired" check |

(Encode the branch words with an assembler or capstone/keystone and verify; the hex above is computed as `0xEA000000 | ((target - (addr + 8)) >> 2)`: 0x2025228 - 0x20251E8 = 0x40 -> 0x10; 0x2024C58 - 0x2024C00 = 0x58 -> 0x16.)

Timed run plus cooldown, no bar, fully in place (no code cave needed):

- After the two patches above, the HP-check block 0x02024BFC..0x02024C54 (23 instructions) and the drain block 0x020251AC..0x02025224 (31 instructions) are dead code and can be rewritten.
- Reuse the 8-bit counter at player `+0x40` bits 5..12 as a run state `c`: 0 = ready, 1..R = running, R+1..R+C = cooldown. Put the logic in the 0x02024BFC block, which runs every frame before movement (it sits right after `[sp, #8]` = B held):
  - if `c == 0` and B held: `c = 1`.
  - if `1 <= c <= R`: if B held, `c += 1`, else `c = R + 1` (early release starts cooldown; change if the Eternal Blue behaviour differs).
  - if `c > R`: `c += 1`; if `c > R + C`: `c = 0`.
  - running flag `[sp, #8]` = B held and `1 <= c <= R`.
- 8 bits allow at most 255 ticks. Three seconds of running plus three of cooldown is 360 frames, so tick every second frame (test bit 0 of the global frame counter halfword at 0x020B05BC = G + 0xC, incremented once per `main` loop) or tick once per frame with R + C <= 255.
- The original drain block then only needs to keep setting the 0x2000 running pose; or leave it NOP'd and set the pose in the new block.
- Check that nothing else reads `+0x40` bits 5..12 (none found in `func_02024b34`; the scripted-move path uses bit 20 and bits 13..14 only).

### Emulator checks

1. Hold B and walk, watch Jian's HP at 0x020B4668 and count frames between decrements (expect 180).
2. Confirm the walk/run step in pixels by watching the player position words at 0x020B6CB0 + 4 / + 8 (20.12 fixed point).
3. With a party member at or below a third of max HP, confirm player `+0x40` bits 13..14 = 3 and no running.

## 2. Combat/Virtue mode, Virtue clock, respawn, area clear, blue chests

All addresses are ARM9 (loaded at 0x02000000). "Decomp" means build/arm9_decomp_annot.c.
G = 0x020B05B0 (save/game state block). F = 0x020B6BE4 (field state block, Ghidra types it as `short *`, so a
decomp index `F[0x632]` is byte offset 0xC64).

### Summary of the mechanism

- Mode flag: byte 0x020B4848 (G+0x4298). 0 = Combat, 1 = Virtue. Toggled by R or by tapping a touch button.
- The flag is read in exactly three places: the toggle itself, the touch button redraw, and battle setup. Battle setup
  copies it into the battle context (0x020B85B8 + 8). Everything mode specific in battle reads that copy.
- Virtue: an enemy death adds Althena Conduct (EXP) and the battle returns result 1, which bumps the per-map kill
  counter. Combat: an enemy death rolls item drops instead, and the battle returns result 0, which removes the map
  symbol without counting it, so the spawner replaces it within 32 frames (the "instant" respawn).
- Per-map table: 32 entries of 6 bytes at 0x020B4908 (G+0x4358): u16 clock, u16 clock limit (0xE10), u8 kills,
  u8 total (random 5 to 7). Area clear = kills == total. The Virtue clock revives one kill each time it fills.
- The whole table resets only when you enter a map in a different dungeon group (group table 0x02091C78).
- Blue chests check kills >= total. Area clear refills 30% of max HP and MP through state 0x1B.

### 2.1 Where the mode flag lives (confirmed)

- Byte 0x020B4848 = G+0x4298. It is inside the block that new game clears: func_0201881c memsets
  `param_1 + 0x409c` for 0x39C bytes (G+0x409C..G+0x4437), so a new game starts at 0 (Combat). It is part of G,
  so it is presumably saved with the game (uncertain, the save code was not traced).
- A constant propagation scan of every function for loads/stores that resolve to 0x020B4848 finds only:
  - func_0201e6a0 0x0201F144..0x0201F168 (toggle, see 2)
  - func_0206f3a4 0x0206F574, 0x0206F58C (touch button icon frame `2 - flag`)
  - func_020297d4 0x020298E0 and 0x02029984: `ldrb r0, [r0, #0x298]` with r0 = 0x020B45B0 (battle init states 0 and 1)
- Meaning of 0/1 confirmed from battle: value 1 leads to the EXP path (see 4).

### 2.2 How it is toggled (confirmed)

Field main loop func_0201e6a0, field state 0x14 (free walking; state is `*(0x020AFF84 + 0x8C)`), decomp around
line 26860:

```c
iVar19 = func_020273b0(0x020b7f28,&local_50);   // touch button under the stylus
if ((pressed & 0x100) != 0) iVar19 = 2;          // R button
if ((pressed & 0x800) != 0) iVar19 = 6;          // Y button
...
if (iVar19 == 2) {
  iVar19 = func_02071c4c(0xffffffff);
  if ((iVar19 != 0) && (*(0x020b6a18) == 0)) {   // map allows it, stylus was not already down
    *(0x020b4848) ^= 1;
    func_020275d8(0x020b7f28,1,2 - flag);         // redraw touch button
    func_020275b4(0x020b7f28,2,*(short*)(0x0209e148+0x10) + flag,0);
    func_02043fd8(0,0);                           // sound
  }
}
```

- Inputs: R (newly pressed, bit 0x100 of pad+6 at 0x020AFF7A) or tapping lower screen button id 2.
- 0x020B6A18 holds last frame's touch state (written at the end of the same function), so a held stylus does not
  retoggle.
- func_02071c4c(-1) gate: returns 1 only if the current map id (F+0) is 0..0x96, is not map 4, and the map has at
  least one enemy spawn point (F+0xC10 != 0). The button is only drawn on such maps (func_0206f3a4).
- Asm: 0x0201F114 `cmp r0,#2`, 0x0201F120 `bl func_02071c4c`, 0x0201F128 `beq 0x0201F260` (skip if not
  allowed), 0x0201F138 `bne 0x0201F260` (skip if stylus held), 0x0201F14C `eor r2,r2,#1`, 0x0201F150 `strb r2,[r5]`.

### 2.3 Battle context copy (confirmed)

func_020297d4 (battle top level), states 0 and 1 (0x020298D8..0x02029924 and 0x0202997C..):

```
020298d8  ldr  r0, =0x020b45b0
020298e0  ldrb r0, [r0, #0x298]      ; mode flag
020298ec  cmp  r0, #0
02029900  movne r5, #1
02029920  str  r5, [sp]               ; 5th arg
02029924  bl   func_0202b948          ; (ctx=0x020b85b8, map, formation, event_battle_id, mode)
```

func_0202b948 stores it at ctx+8 (halfword):

```c
if (param_5 == 1) { ctx[4] = 1; if (ctx[3] != 0) ctx[4] = -1; }   // ctx[3] = event battle id (+6)
else ctx[4] = 0;
```

So ctx+8 = 1 for a normal map encounter in Virtue, -1 for a scripted/boss battle in Virtue, 0 in Combat.
Getter func_0202b118 = `ldrsh r0,[r0,#8]`. Its callers: func_02053384 (enemy death), func_020297d4 (intro
state 4 at 0x02029F40, result routing at 0x0202A8E0 and 0x0202A9F4), func_0203b03c (item list on the result screen,
0x0203B0DC).

### 2.4 EXP is Virtue only (confirmed)

func_02053384 (damage resolution for one battler; runs when an enemy, flag 8, drops to 0 HP):

```
02053608  ldr r0,[r6] ; ands r0,r0,#8 ; beq 0x02053684      ; not an enemy -> normal death
02053614  bl  func_0202b118 ; cmp r0,#1 ; bne 0x02053684    ; ctx+8 != 1 -> Combat path
02053624  orr flags,#0x4000000                             ; "purified" death animation
02053668  bl  func_02053880(enemy_stats, 10)                ; EXP value (formula: other agent)
02053674  bl  func_0202af3c(ctx, exp)                       ; ctx+0x58 += exp
02053680  b   0x020536D4
02053684  ...  orr flags,#0x8000000                         ; normal kill animation
020536cc  mov r0,r7 ; bl func_02069f34                      ; item drop roll -> func_0202afc0(ctx,item,1), ctx+0x48
020536d4  mvn r5,#0
```

- So per enemy you get either EXP (Virtue, ctx+8 == 1) or an item roll (anything else). Scripted battles in Virtue
  have ctx+8 = -1 and take the item path, so they give no EXP through this route (uncertain whether bosses give EXP
  somewhere else; not traced).
- End of battle: func_02052fb8 sets the pool `battle+0x144 = ctx+0x58 * 2` (EXP is doubled), then func_02052c2c
  pours it into each battler with func_02031b70 == 1 (alive) whose status is not 1, 4 or 7, capped at the level 99
  value. Only battlers in the three party slots exist, so only party members get EXP (relevant to topic 4).
- Result routing (func_020297d4 case 10 sub 1, line ~33470): mode 1 goes to sub-state 2 (EXP screen, which then
  chains to 0x28), otherwise straight to 0x28. Items in ctx+0x48 are always granted by func_0202af50 in case 9,
  regardless of mode. func_0203b03c draws the item list only when mode != 1.
- Battle result passed back to the field (ctx+0xC, func_0202b8fc / func_0202b904), case 9 line ~33419:
  1 = won in Virtue, 0 = won in Combat; also 2 = party fled (code -4), 3 = lost (code -3).
- Also noted (not my topic): the mic "blow to run" in battle is func_0206bafc called from func_0203a34c and gated by
  func_020457cc(10).

### 2.5 Per-map enemy table, area clear, respawn (confirmed)

Structures:
- 0x020B4904 (s16): current dungeon group id, from table 0x02091C78 (pairs `[start, end)` of map ids, 19 groups:
  0-5, 5-20, 20-31, 31-35, 35-38, 38-45, 45-53, 53-58, 58-61, 61-85, 85-88, 88-94, 94-100, 100-106, 106-112,
  112-121, 121-129, 129-140, 140-151, terminated by -1).
- 0x020B4906 (s16): index of the current map within its group (map - group start), -1 outside any group.
- 0x020B4908 + idx*6: `u16 clock; u16 clock_limit; u8 kills; u8 total;` (32 entries).
- F+0xC10 (0x020B77F4): number of enemy spawn points on this map (map objects of kind 0x19), coordinates at
  0x020B77F8 (s16 x, s16 y pairs). F+0xC64 (0x020B7848): "area just cleared" flag.
- Map objects: 32 x 0x40 bytes at 0x020B6FD4. +0x14 kind (1 = NPC/object, 3 = enemy symbol, 4 = chest,
  6 = trap, 0xB = projectile...), +0x20 chest opened, +0x22 chest needs area clear.

Map entry, func_0201d92c (only when the load flags include 0x20, which normal entries use; the after-battle
reload uses 0xFFFFFF5E, which does not):
- 0x0201E068 `bl func_0206eee0` (group of new map); if it differs from 0x020B4904, 0x0201E07C `bl func_0206ee90`
  marks all 32 entries uninitialised (kills = total = 0xFF) and stores the new group.
- 0x0201E0EC `ldrb r0,[r6,#4]; cmp r0,#0xff; bne 0x0201E11C`: first visit initialises the entry:
  `total = rand%3 + 5` (func_02070714), `kills = 0`, `clock = 0`, `clock_limit = 0xE10` (0x0201E10C).
- Then it spawns `min(spawn_points, 8, total - kills)` enemy symbols at random distinct spawn points.

So vanilla respawn after leaving: entries persist while you stay inside the same dungeon group (each map keeps its
own kills), and are wiped when you enter a map of a different group.

Battle won, field state 0x7B (func_0201e6a0 0x02020900..0x020209A8):

```
02020904  bl func_0202b904              ; battle result (ctx+0xc)
02020908  cmp r0,#0 ; beq 0x02020970     ; Combat win: just delete the symbol
02020910  cmp r0,#1 ; beq 0x02020924     ; Virtue win
02020918  cmp r0,#2 ; beq 0x02020988     ; fled: symbol flags |= 0x168000 (0xB4 frame no-contact timer)
02020924  bl func_0206ec54               ; current entry
02020934  strh r1,[r0]                   ; clock = 0
02020940  cmp kills,total ; bhs skip
02020950  kills += 1
02020960  if kills == total: strb 1,[F,#0xc64]   ; area cleared
02020980  bl func_02026254               ; delete the symbol
```

Spawner, field state 0x14 every frame (0x0201F990..0x0201FA20):

```
0201f998  idx = *(s16*)0x020b4906 ; if idx == -1 skip
0201f9a8  if (frame_counter@0x020b4880 & 0x1f) skip      ; every 32 frames ([0x020b45b0+0x2d0])
0201f9b8  if (*(u16*)(0x020b47b0+0xcc) & 1) skip         ; script command disables spawning
0201f9c4  n = func_020706e4()                            ; enemy symbols (kind 3) on the map
0201f9d0  if n >= spawn_points (F+0xc10) skip
0201f9f4  if total <= kills + n skip
0201fa1c  func_020704d0(0,-1,&camera)                    ; spawn at a random spawn point that is off screen
```

- Combat mode respawn (confirmed by reading the logic, the "instant" respawn): a Combat win removes the symbol but
  does not add a kill, so `kills + n` drops below `total` and the spawner puts a fresh symbol at an off-screen spawn
  point within 32 frames.
- Virtue mode: every win adds a kill, so the map runs dry after `total` wins. The spawner still tops the map up from
  the remaining budget when `total` exceeds the number of spawn points.

### 2.6 The Virtue clock (confirmed)

Field state 0x14, every frame (0x02021F6C..0x0202200C; decomp line ~28015):

```c
e = func_0206ec54();                         // current entry
if (e) {
  if (e->kills != 0 && e->kills < e->total && ++e->clock > e->clock_limit) {
    e->clock = 0;
    e->kills -= 1;                            // one defeated enemy comes back
    func_020719dc(hud, e->total, e->kills);   // kill counter on the top screen
  }
  func_0201ace4(*0x020aff50, 0, 0x1000, -(e->clock * 0x10000 / e->clock_limit), 0);  // clock hand rotation
}
```

- The clock is a per-map tick counter that fills to 0xE10 = 3600 ticks, counted only in free-walk state 0x14
  (menus, scripts and battle pause it). Each fill revives one kill. It is reset to 0 by every Virtue win
  (0x02020934) and stops once the map is cleared (kills == total) or when kills == 0.
- It runs regardless of the mode flag; in pure Combat play kills never rise above 0 so it never moves.
- Duration: 3600 ticks = 60 s if the field runs at 60 fps, 120 s at 30 fps. **Uncertain** which; see tests.
- The kill counter HUD (`total`, `kills`) is drawn by func_0207184c -> func_020719dc.

### 2.7 Blue chests (confirmed)

func_0201e6a0 state 0x14, A pressed next to a map object (decomp ~line 26985, asm near 0x0201F2A4):

```c
if (obj->kind == 4 && obj->opened == 0 && obj->y < player_y &&
    (obj->needs_clear == 0 || func_0206ec84() != 0)) {    // +0x20, +0x22
  func_0206eb60(0x66); obj->opened = 1; F->field_0x9e = obj->id; state = 0x42;
}
```

func_0206ec84: returns 0 (locked) only while `idx != -1 && kills < total`; otherwise 1. So blue chests are
already locked until every enemy on that map is beaten (kills counted only in Virtue in vanilla). Maps outside
every group (idx == -1) never lock.

### 2.8 Area clear HP/MP refill (confirmed)

- After a Virtue win that makes kills == total, F+0xC64 = 1 (0x0202096C).
- Field state 0x11 (resume) checks it: `if (F[0xc64]) { F[0xc64] = 0; state = 0x1b; } else state = 0x14;`
- State 0x1B (0x0201FA24): `func_0206ecc8(30, 30); state = 0x3c;`
- func_0206ecc8(hp_pct, mp_pct): for each party slot, `HP += maxHP*30/100; MP += maxMP*30/100`, capped. So the
  refill is +30% of max HP and MP, not a full heal.
- State 0x3C (0x0201FA40) finds the map object of kind 1 with id 0x37D (same id the A-button Althena statue full heal
  checks) and plays a 60 frame effect on it (func_0201d878), then state 0x3D. The statue full heal (A on object
  0x37D) also goes to state 0x3C.

### 2.9 Patch points

All are single ARM instruction edits in arm9.bin (file offset = address - 0x02000000).

1. Remove the mode switch, force one mode with EXP and items (confirmed sites; behaviour after patch untested):
   - Ignore R/tap: 0x0201F128 `beq 0x0201F260` -> `b 0x0201F260` (change condition nibble 0x0 to 0xE).
   - Force Virtue semantics in battle: 0x020298E0 and 0x02029984 `ldrb r0,[r0,#0x298]` -> `mov r0,#1`. Map battles
     then give EXP and return result 1 (kills counted). Scripted battles get ctx+8 = -1 (same as vanilla Virtue).
   - Also roll items on every Virtue kill: 0x02053680 `b 0x020536D4` -> `b 0x020536CC`, so the EXP path falls into
     `mov r0,r7; bl func_02069f34` (r7 still holds the battler index). Items are granted by func_0202af50 in every
     mode.
   - Show the item list on the result screen in Virtue: 0x0203B0E4 `beq 0x0203B3B8` -> NOP (0xE1A00000).
   - Hide the touch button: func_0206f3a4 draws button 2 only when func_02071c4c is true (loop at the top and the
     block at 0x0206F574). **Uncertain** cleanest edit; a test should confirm what the empty slot looks like.
   - Silver from battles (design 3) has no vanilla code path; it needs new code (code cave).
2. Remove the Virtue clock: 0x02021F80 `beq 0x02021FDC` -> `b 0x02021FDC`. Kills then never decay. The clock hand
   sprite still draws (frozen at 0); to hide it, skip 0x02021FDC..0x0202200C or the sprite load in func_0201d92c
   (**uncertain** which graphic slot is the clock; test needed).
3. Respawn only on re-entry: with kills counted in every battle (patch 1) the spawner can no longer refill a map
   past `total`. To also restock each map when you walk back in (instead of only on dungeon group change), make the
   init unconditional: 0x0201E0F4 `bne 0x0201E11C` -> NOP. Every fresh entry (load flag 0x20) then rerolls total and
   zeroes kills; the after-battle reload (flag 0xFFFFFF5E) does not reach this code, so battles do not restock.
   Alternative scope: keep vanilla (reset per dungeon group) by leaving it alone.
4. Remove the area clear refill: 0x0201FA2C `bl func_0206ecc8` -> NOP, and 0x0201FA34 `mov r1,#0x3c` -> `mov r1,#0x14`
   to skip the statue sparkle too. Or drop the flag at the source: 0x0202096C `strbeq r1,[r0,#0xc64]` -> NOP.
5. Blue chests locked until clear: already vanilla behaviour via func_0206ec84. Needed only: kills must count in all
   battles (patch 1) and must not decay (patch 2). If patch 3 is used, a returning player must clear the map again
   to open an unopened blue chest (opened chests stay opened if the open state is saved; **uncertain**, see tests).

### 2.10 Open items and emulator tests

- Field frame rate (decides 60 s vs 120 s clock, and run drain timing in topic 1): with a RAM watch on
  `*(u16*)(0x020B4908 + 6 * *(s16*)0x020B4906)` after one Virtue kill on a map with several enemies, count how many
  emulator frames it takes for the u16 to go from 0 to 3600.
- Confirm 0/1 meaning on screen: watch byte 0x020B4848 while pressing R on a dungeon map; the lower screen icon
  should change, and 1 should give the EXP screen after a battle.
- Do bosses/scripted battles give EXP? Fight a story battle in Virtue and watch `ctx+0x58` (0x020B8610) and the
  party EXP at char+0x3C (Jian 0x020B4694).
- Blue chest persistence: open a blue chest, leave the dungeon group, return; check whether the chest object comes
  back with +0x20 == 0 (and whether an event flag via func_0206eb60(0x66) records it).
- What load flags other paths pass to func_0201d92c (save load, warp, menu return) to make sure patch 3 does not
  restock on a menu close: break on 0x0201E0EC and note r1/param_2 at entry.
- State 0x3D onward after the sparkle: check whether any "area cleared" message depends on state 0x3C before
  shortcutting it.

## 3. Battle targeting, EXP distribution and level-up choices

All addresses are ARM9 (loaded at 0x02000000). Function names are the dsd/Ghidra names in
`build/arm9_decomp.c`. "Confirmed" means read directly in the code; "uncertain" means inferred.

### Battle data structures

| Address | What | Status |
|---|---|---|
| `*(0x020B8640)` | Battler array, 300 (0x12C) bytes each. Index 0..2 = party slots, 4..7 = enemy back row, 8..11 = enemy front row, 12 = scratch copy of the acting battler, 13 = scratch copy of a counter/cover battler | Confirmed for 0..2, 4..11, 12, 13 (see below); the row names are inferred |
| `*(0x020B8620)` | Battle stat records, 0x6C bytes each, indexed by battler `+0x10`. `+4` character id, `+8` status (low 4 bits), `+0xC` level (0 based), `+0x14` HP, `+0x18` MP, `+0x1C` max HP, `+0x20` max MP, `+0x50` EXP | Confirmed (func_02027edc prints `+0xC + 1`, `+0x14`, `+0x1C`, `+0x18`, `+0x20`; func_02052888 copies `+0x50` to the save EXP field) |
| `*(0x020B8550)` | Battle round context. `+0x30` turn counter, `+0x38` turn order list (shorts), `+0x32` acting battler, `+0xCA` counter/cover battler, `+0x148` EXP pool still to pay out, `+0x14C` EXP paid per tick | Confirmed |
| `0x020B8800` | Touch command UI state. `[0]` flags, `[1]` result code for the battle loop, `+8` (short) current page, `+0xA` (short) next page, `[4]` chosen command, `+0x34`/`[0xd]` battler whose command is being entered, `[0xf]` list scroll offset, `[0x20]` chosen spell/item | Confirmed |
| `*(0x020B86FC)` | Touch buttons, 0x16 entries x 200 bytes. Word 0 low 12 bits = button id, bit 31 = not active. Created by func_02037934(index, type) | Confirmed |

Battler fields used for actions (all confirmed from func_0203a34c, func_02036694, func_020514ec, func_02031b48):

- `+0x00` flags. Bit 3 (`& 8`) set = enemy. Bit 0 = present, bit 25 = removed.
- `+0x04` character id for party battlers (0 Jian, 1 Lucia, 2 Gabryel, 3 Flora, 4 Rufus; func_02050c50 uses 1 and 3 as the Althena magic users, 0 for the dragon rings), enemy type id for enemies (0x96, 0x97 are special bosses).
- `+0x84` (short) action: 0 none, 1 Attack, 2 spell/special, 3 guard/other, 4 item.
- `+0x86` (short) spell or item id.
- `+0x8C` (short x 8) target list; `+0x8E` second target (or -1).
- func_02031b48 resets `+0x84`, `+0x88` to 0 and all eight `+0x8C` targets to 0xFFFF.

Alive test (confirmed), func_02031b70:

```c
// returns -1 not present, 0 present with HP <= 0, 1 alive
if ((flags & 1) && !(flags & 0x2000000) && battler[4] < 0xc) {
  rec = *(0x020B8620) + battler[+0x10] * 0x6c;
  if (rec->flags & 1) return rec->hp(+0x14) < 1 ? 0 : 1;
}
return -1;
```

### Round flow (where commands are entered and where they run)

Battle main loop is func_020297d4; the battle sub state is read with func_0202b8ec(0x020B85B8). Confirmed:

1. Sub state 1: func_0203add0 (load UI, start mic), **func_02031b10 clears every battler's action and targets** (calls func_02031b48 on battlers 0..11), func_0202f1e8.
2. Sub state 2: func_0203aa10 builds the command UI (page 0) for the first living party member (func_0203629c(1)).
3. Sub state 3: func_0203a34c each frame. It calls func_02036694 when a button is tapped, which returns 2 when the current member's command is final. func_0203a34c then writes `+0x84` from `[4]` (`[4]==3 -> 1 Attack`, `4 -> 2 spell`, `5 -> 4 item`, else 0). The loop advances to the next living member (func_0203629c(1)); when none is left it goes to sub state 4. Result 3 goes back one member (func_02036200), result 1 is Run, result 4 is Auto.
4. Sub state 4 / field state 8: func_0202d22c runs the round. In its state 1 it takes the next battler from the turn order, checks it is alive and not disabled by status, and **only then calls func_020514ec(actor) to choose the targets** (call at 0x0202d4xx, decomp line `func_020514ec(*(short *)(ctx + 0x32) * 300 + battlers)`). The attack animation script then applies each hit through func_02030b44.

Because func_02031b10 runs before input (sub state 1) and nothing else clears `+0x8C` until the actor's turn, a target written during command input survives until func_020514ec. Confirmed.

### How the Attack target is chosen today

**Confirmed: the player never picks the Attack target.** Tapping Attack (page 1, button id 3, handled in func_02036694 `case 1: case 3`) just sets `[4] = 3` and ends that member's input; no target is stored. The target is chosen by the game at the moment the attack starts, in func_020514ec, party branch (`(flags & 8) == 0`, `+0x84 == 1`), disassembly 0x02051bd8..0x02051c80:

```asm
02051bd8  ldr   r1, [r4, #4]        ; character id
02051bdc  cmp   r1, #3
02051be0  bne   #0x2051c0c
02051be4  ldr   r0, =0x0213b908
02051bec  ldrb  r6, [r0, #0x11]
02051bf0  bl    rand                ; func_02011424
02051bf8  bl    divmod              ; hits = rand % byte[0x0213b919] + 1
02051c00  cmp   r8, #1
02051c04  movgt sb, #3              ; more than one hit -> random targets
...
02051c0c  mov   r0, #0xd
02051c10  bl    func_0206b8ec       ; is item 0x0D in this character's equipment?
02051c18  moveq sl, #0              ; yes -> may hit both rows
02051c1c  cmp   r5, #0x46           ; r5 = rand % 100
02051c20  movge sb, #3              ; 30% of the time -> random target
```

then for each hit `target[i] = func_02050f78(mode, rows)`, stored in `+0x8C + 2*i`.

func_02050f78(mode, rows) (confirmed) looks at the 8 enemy battlers 4..11, skips dead ones and ones outside `rows`
(0 = all, 1 = battlers 4..7, 2 = battlers 8..11), scores each by mode, sorts, and picks randomly among those tied
for best:

- mode 1: lowest current HP (`func_02053880(rec, 0)` = `+0x14`).
- mode 2: score from (max HP minus HP) scaled by 100 (most damaged); not used for party attacks.
- mode 3: random 0..99 per enemy (so a random enemy).

So the rule for a party member's Attack is (confirmed):

- Default rows = 2 (battlers 8..11, the front row). Rows = 0 (front and back) if the character has equipment id 0x0D (func_0206b8ec checks the five shorts at save `+0x40E8`). The item name for id 0x0D is uncertain.
- 70%: the front-row enemy with the **lowest current HP** (ties random).
- 30%: a **random** front-row enemy.
- Character id 3 (Flora by the id order above) gets `rand % byte[0x0213b919] + 1` hits, each with its own target, and uses random targeting whenever it rolls more than one hit. Which character id 3 is in this context and what 0x0213B908 holds are uncertain (0x0213B908 is also read as a status-chance table in func_02030b44).

Enemies targeting the party use func_0205124c over battlers 0..2: 50% highest current HP (mode 0), 50% random (mode 3) for physical attacks (`iVar6 < 0x32`), confirmed in func_020514ec enemy branch.

Auto battle (Run/Auto page result 4, `ctx+0x28 == 1`): func_02050f1c sets every living party member to `+0x84 = 1` each round, so it uses the same rule. Confirmed.

### What happens if the target is already dead

Two levels, both confirmed:

1. **Between command input and the attack: not possible for Attack.** Targets are picked when the attacker's turn starts, from the enemies alive at that moment (func_02050f78 skips `func_02031b70 < 1`). So vanilla never "aims at" an enemy that died earlier in the round.
2. **Within one action (multi-hit), the hit whiffs, no redirect.** func_02030b44 (per-hit damage, called from the animation script) does:

   ```c
   target = attacker->targets[(hitflags >> 12) & 7];          // +0x8C list
   if (!(*param_2 & 0x40) || func_02031b70(target) < 1) goto LAB_02031120;  // skip damage
   ```

   LAB_02031120 only does end-of-hit bookkeeping; no other target is tried. So if a multi-hit attack (or a cover/counter case using battler 13) lists an enemy that an earlier hit killed, that hit is wasted.

For single-ally spells and items (the only commands with a player target today) the stored target is re-checked at turn start in func_020514ec: if `func_02031b70(target) > 0` it is kept, otherwise it is replaced by `func_0205124c(1)` (the living ally with the lowest HP). Confirmed. Single-enemy spells cast by the party use `func_02050f78(3, 0)`: a random living enemy in either row (the player does not choose). Confirmed (branch `(spellflags & 0xC0000000) == 0`). Note research.md item 3 is answered: original behaviour is "pick at execution, so no whiff", except inside multi-hit actions.

### Touch command UI and where to insert a target step

Pages (`0x020B8800 + 8`), built by func_0203962c from `+0xA` whenever flag bit 1 is set (confirmed):

| Page | Buttons created (index, id) | Meaning (ids inferred from handlers) |
|---|---|---|
| 0 | (8,1) (9,2) | top level: 1 opens the command page, 2 is the second top button (calls func_02037848, likely Auto) |
| 1 | (4,10) (8,3) (9,4) (10,5) | commands: 3 Attack, 4 Special/Magic (checks func_02050ec8), 5 Item; ids 6, 7, 8 are always-present buttons from func_02039b20 |
| 2 | list rows 8..13 (id 0xE), built by func_020359f4/func_02035310 | spell list; id 6 confirms the highlighted entry |
| 3 | (8,0xC) (9,0xD) | item category page |
| 4, 5 | list pages | item lists |
| 6 | (8,10) (9,10) (10,10), back = id 8 | **existing target picker** for single-ally spells/items: target = button index - 8 (0..2), written to `+0x8C` in func_02036694 `case 6: uVar9 == 10` |
| 7 | | confirm/back page |

The existing target page 6 is reached from page 2 when the spell's flags are `0x80000000` (single ally) and from page 4 button 6. It saves the previous page in `+0xC` (`[3]`) and, on confirm, writes `+0x86`, `[4]`, `+0x8C = index - 8`, returns 2.

Insertion point for player-chosen Attack targets (confirmed locations, approach is a proposal):

- **UI**: in func_02036694 `case 1` (page 1), `uVar9 == 3` (Attack), around 0x02036800 (the block that sets `[4] = uVar9` and returns 2). Instead of returning 2, switch to a new enemy-target page (copy page 6: set `+0xA` to the new page number, `[3] = 1`, flag bit 1) and return 0. The new page needs up to 8 buttons for living enemies. Page 6 only creates 3 buttons over the party portraits, so the enemy picker needs new button placements (or reuse the list-row buttons 8..13 with id 0xE and enemy names, as func_020359f4 does for spells). The confirm handler writes `+0x8C = enemy battler index (4..11)` and returns 2 (func_0203a34c then sets `+0x84 = 1`).
- **Execution**: func_020514ec party Attack branch at 0x02051bd8. Before it overwrites `+0x8C`, read the stored target; if it is 4..11 and `func_02031b70 > 0`, use it; otherwise walk to the next living enemy (design rule: next in the list, never wasted). Also handle the row rule (default front row only) and the multi-hit character.
- **Per hit**: to make multi-hit attacks never waste a hit, change the skip in func_02030b44 (the `func_02031b70(puVar10) < 1` test) to retarget to the next living enemy instead of jumping to LAB_02031120.
- Auto battle (func_02050f1c) and the mic/Run path set actions without a target; they will keep using the vanilla rule if the execution patch falls back when `+0x8C` is 0xFFFF.

Related (for topic 1): the **microphone is a battle feature, not field running**. func_0203a34c calls func_0206bafc (mic loudness detector over the sampling buffer started by func_0206bc0c) only in battle; a blow sets all three party actions to 0, `[1] = 1` and returns 1 = Run. In func_020297d4 sub state 3 result 1: if not a special battle (`func_0202b90c == 0`), escape succeeds when `rand % 10 >= number of living enemies` (func_020531a0 counts them), else a failure message and the round runs with the party idle. Escape always fails in battles where func_0202b90c != 0 (likely bosses). Confirmed reading; the exact meaning of the two branches (success vs failure) is from the follow-up states (0x130 countdown then fade out = escaped) and is likely but should be checked in the emulator.

### EXP distribution (confirmed)

func_02052c2c (battle results, sub state 10/2) pays the pool `ctx+0x148` in ticks of `ctx+0x14C` (A or a tap pays all at once). For each battler 0..2:

```c
if (func_02031b70(battler) == 1) {                // in the party AND HP > 0
  rec = stats[battler->+0x10];
  if (rec->status != 1 && rec->status != 4 && rec->status != 7) {
    rec->exp(+0x50) += tick;                      // full amount, not split
    cap at exp table [char][98];                  // func_020553ac(0x62, char)
    newLevel = func_020553c8(exp, char);          // per-character table at *(0x020A587C + char*4)
    if (rec->level < newLevel) { level up }
  }
}
```

Then func_02052888 (battle end, sub state 0xE) copies level, max HP, stats, EXP back to the save structs **only for the three party slots** (`*(short *)(0x020B05B0 + 0x409C + i*4)`, i.e. 0x020B464C/50/54) and only if the battler exists. It also sets HP 0 to 1, so KO'd members leave battle with 1 HP.

So:

- **Only battle party members get EXP.** Characters not in the three slots are not in the battle and receive nothing. Confirmed.
- **Party members who are KO'd (HP 0) or have status 1, 4 or 7 get nothing** for that battle. The status names for 1, 4, 7 are uncertain (likely stone/KO-type statuses).
- Each eligible member gets the full pool (no split). Confirmed.
- The pool size (`ctx+0x148`) is set elsewhere; that is the EXP-formula agent's area. Not traced here.

For the benched-EXP design: the simplest hook is in func_02052888 or func_02052c2c: after paying the battlers, add the same total to the save EXP (`0x020B05B0 + 0x40E4 + id*0x5C`, i.e. character struct `+0x3C`) of characters not in a slot, then recompute level and stats with func_020553c8 and func_020554f4 (both already used by new-game setup func_020555e8). Proposal.

### Level-up never asks for a choice (confirmed)

- Level comes from EXP through a table (func_020553c8), capped at index 0x62 (level 99).
- On level-up func_02055408(rec, level) recomputes max HP, max MP and the six other stats from a fixed per-character growth table at 0x02094B4C (0x60 bytes per character: 8 stats x 3 parameters, evaluated by func_020552cc). Current HP and MP are rescaled to the new maximum (`func_02015f80(oldHp * newMax, oldMax)`). Nothing is random and nothing is chosen.
- Spells are not stored per character; they are derived on demand by func_02050c50 from the spell table at 0x02094978 (0x26 entries, 0xC bytes each):
  - Lucia (id 1): available when her level `>= byte[0x02094980 + spell*0xC]`.
  - Flora (id 3): when her level `>= byte[0x02094981 + spell*0xC]`.
  - Jian (id 0): spells flagged 0x100000/0x200000/0x400000/0x800000 need dragon ring items 0xCB/0xCC/0xCD/0xCE (owned, and equipped for casting, func_02050a74).
  - Gabryel (id 2): spells with flag 0x200; Rufus (id 4): flag 0x400.
  - Also requires max MP >= the spell's cost (func_020500c4).
  So a benched character who levels up silently gains exactly what an active one would. Confirmed.
- Save character struct (0x020B4658 + id*0x5C) `+0xC` is the 0-based level, `+0x3C` EXP; new game sets Rufus `+0xC = 14` (level 15) and his EXP from the table (func_02055760), so Rufus' join level 15 is hard-coded at new game. Confirmed.

### Things to check in an emulator

1. Attack targeting: with three front-row enemies at different HP, attack many times and log battler `+0x8C` at 0x02051c80 (after func_02050f78). Expect about 70% lowest HP, 30% random. Confirms rows 8..11 = front row.
2. With all front-row enemies dead but back-row ones alive: does func_02053918 move them forward before the next party turn, or does func_02050f78 get zero candidates (divide by zero in func_02015f80)? Break on func_02050f78 return with rows = 2 and no living 8..11.
3. Which character has id 3 in battle and what byte 0x0213B919 holds (multi-hit count). Read battler `+4` for each slot in a fight with Flora.
4. Item 0x0D: which equipment it is (lets the wearer hit the back row).
5. Escape: confirm `rand % 10 >= living enemies` is the success branch (count successes with 1 vs 4 enemies).
6. Status codes 1, 4, 7 in stat record `+8`: which statuses block EXP.

## 4 and 5. Party slots, story party changes, save-disable flag

All addresses are ARM9 (loaded at 0x02000000). "G" is the big game-state block at 0x020B05B0. Snippets are from
build/arm9_decomp_annot.c. Script offsets are byte offsets inside build/unpacked/script/NNN.bin.

### Tooling

- `src/dsde/script.py` (adopted from this research): `uv run python -m dsde.script build/unpacked/script/NNN.bin [--text] [--reach]`. Linear listing from the entry jump, or recursive descent with `--reach`. Scripts have extra entry points that nothing jumps to (they end with op 0x20), so `--reach` misses code; the linear sweep stops at the first unknown op.

### The event script VM (confirmed)

- Interpreter: `func_020418ac`. Opcode is the u16 at the script PC (`ctx+0xE0`); handler table at
  **0x020A3EE8**, 83 entries of `{handler, yield}` (8 bytes each). It keeps dispatching while `yield == 0`.
  ```c
  uVar2 = (uint)*puVar3;
  (**(code **)(0x020a3ee8 + uVar2 * 8))(param_1);
  ...
  } while (*(int *)(0x020a3ee8 + uVar2 * 8 + 4) == 0);
  ```
- Context object (0x2B4 bytes): main field context pointer at **0x020B4640** (= 0x020B45B0 + 0x90), a second
  one at 0x020B4644. Layout: `+0x00..0x5B` flag bits (bit n at `ctx + (n>>5)*4`, bit `n&31`), `+0xDC` script
  base, `+0xE0` PC, `+0xE4` previous PC, `+0xE8` running, `+0xF0..0x1EF` call stack, `+0x1F0` depth,
  `+0x1F4` byte vars, `+0x204` short vars, `+0x224` int vars, `+0x290..0x298` file handle/buffer/loaded id.
  Flag test is `func_02041918(ctx, n)`. Flags 0x260..0x2DF are per-map locals (`func_020419fc` clears them).
- Scripts come from script.dat (archive index 6; index table at 0x020A0650 resolves 6 to "/script.dat").
  `func_02041a68(ctx, 6, n)` loads entry n; the map table at 0x02091D18 (stride 0x28) gives each map's
  script entry in byte +2. Every script file starts with op 0x02 (jump) to its code, text sits before the code.
  `func_02041a40` zeroes `ctx+0xDC..0x270` on load, so the call stack and vars reset per load.
- Opcodes used below: 0x02 jump, 0x03 call, 0x04 ret, 0x0D if-compare goto, 0x0E if-compare call, 0x0F show
  message, 0x13 if all flags set goto, 0x14 if none set goto, 0x15 if any set goto, **0x19 set flag**,
  **0x1A clear flag**, **0x1B party join**, **0x1C party leave**, 0x20 end, 0x21 add money (to 0x020B4824),
  0x31 yes/no prompt, 0x32 multi-purpose "system" op (sub 0x11 = random into int var 0, sub 0x20 = pay money).

### 4. Party

#### Party slot globals (confirmed)

- Three slots at **0x020B464C, 0x020B4650, 0x020B4654** = G+0x409C + 4*i. Each is a pair of shorts:
  `+0` character id (0 Jian, 1 Lucia, 2 Gabryel, 3 Flora, 4 Rufus, -1 empty), `+2` the slot index
  (written by `func_0201d92c` for the map follower sprites).
- Writers found:
  - `func_0201881c` new game: `*(param_1+0x409c)=0; *(param_1+0x40a0)=0xffff; *(param_1+0x40a4)=0xffff;`
    (Jian alone). Same function sets money `G+0x4274 = 0x96` (150 S at 0x020B4824).
  - `func_02040440` = script op **0x1B join**: puts the id from `pc+2` into the first slot that is -1, loads
    its field sprite, yields. If all three slots are full it does nothing (the join is silently dropped).
  - `func_02040238` = script op **0x1C leave**: finds the slot whose `char.id == pc+2`, shifts later slots down
    (`slot[i] = slot[i+1]` for i < 2) and sets slot 2 to -1. If the character is not in the party it does nothing.
  - `func_0201d92c` writes only the `+2` half.
  - Uncertain: no other code store to these addresses was found by literal-pool search; loading a save
    presumably restores them as part of a bulk copy of G (not traced).
- Neither join nor leave touches the character struct, so **a character who leaves keeps level, EXP and
  equipped gear in his/her struct** (confirmed statically: the handlers only edit the slot shorts and sprite
  pointers). This is why Lucia and Rufus "leave with their gear": it stays in their struct, nothing returns it
  to the inventory. A hack can rejoin them with op 0x1B and they come back as they left.

#### Character structs (fields marked)

Base **0x020B4658 + id*0x5C** (= G+0x40A8), 5 characters. Field map:

| Offset | Meaning | Status |
|---|---|---|
| +0x00 | 0 at New Game (1 in the alternate init `func_0201881c`) | uncertain meaning |
| +0x04 | character id | confirmed (`func_02055760`, `func_020554f4` index tables by it) |
| +0x08 | status bitmask (`& 6`, `& 0xF` tests in item use `func_020635cc`) | confirmed bitmask, bit meanings uncertain |
| +0x0C | level, 0-based | confirmed (`func_020555e8`: `+0xC = func_020553c8(EXP, id)`) |
| +0x10/+0x14 | HP / max HP | confirmed (cheat file and `func_020554f4`) |
| +0x18/+0x1C | MP / max MP | confirmed |
| +0x20 ATK, +0x24 DEF, +0x2C AGI, +0x30 INT, +0x34 DEX, +0x38 LUCK | stats recomputed from level by `func_020554f4` from a per-character 0x60-byte growth table at 0x02094B4C | confirmed |
| +0x28 | not written by the stat recompute | unknown |
| +0x3C | total EXP | confirmed (`func_020553ac(level,id)` returns the EXP for a level from the per-character table pointer at 0x020A587C + id*4, capped at level index 0x62) |
| +0x40..+0x49 | 5 equipment shorts (initial values from 0x02094720, 5 per character) | confirmed as initial gear, slot order uncertain |
| +0x4A..+0x59 | 8 shorts, zeroed at New Game | unknown (possibly per-battle state) |

Note for the EXP fork: the EXP table is looked up per character id (pointer table 0x020A587C), not one global table.

#### Rufus' level 15 (confirmed hard-coded)

`func_02055760` (New Game init) sets every character's level to 0 except id 4:
```c
local_30 = 0xe; ...
if (iVar5 == 4) { *(G + 0x40b4 + 4*0x5c) = 0xe; }   // level index 14 = level 15
*(0x40e4) = func_020553ac(level, id);                  // EXP for that level
```
Rufus' struct is built at New Game with level 15 and his starting gear, and op 0x1B does not touch it.
Gabryel and Flora "join at level 1" because their structs were also built at New Game at level index 0.
Whether they stay at level 1 depends on whether out-of-party members earn EXP (other fork).

#### Story party changes (confirmed op, story match marked)

| Script / offset | Op | Story event | Match |
|---|---|---|---|
| 001 0x6BC0 and 0x7360 | join 1 | Lucia joins at game start (0x7360 follows "Oh, Jian, honestly... wake up at a reasonable time") | confirmed |
| 008 0x3C2C | join 2 | Gabryel joins | likely Healriz after the tournament (uncertain) |
| 009 0x605C | leave 2 | Gabryel separated after Gronk (sets flags 0x1F8, 0x1FA, 0x1FB, 0x79 just before) | confirmed in the Zethos/Cathedral script |
| 005 0x3D88 | join 2 | Gabryel rejoins in Leephon City | confirmed (Leephon script) |
| 016 0x14E0 | leave 1 | Lucia kidnapped at Sungrid Bridge | confirmed (Ignatius/Sungrid script) |
| 010 0x3FE0 | join 3 | Flora joins (Underground Tunnel) | op confirmed; which story moment reaches it is uncertain (see below) |
| 019 0x0674, 0x0678 | leave 2, leave 3 | Gabryel and Flora leave at the end of Sandra Desert | confirmed (Elda/Lind script) |
| 020 0x0DC4, 0x0DC8 | join 2, join 4 | Gabryel returns and Rufus joins at the Elda Canyon boss | confirmed (Caucus/Orcus/Morus script) |
| 021 0x3E44 | leave 4 | Rufus stays behind at Vile Castle 4F (followed by clear 0x5, set 0xCD) | confirmed |
| 004 0x7064 | join 3 | Flora rejoins at Titus' house in Healriz | confirmed (Titus script) |
| 026 0x0D64..0x0D74 | leave 1,2,3,4 then join 1 | Ending: party rebuilt as Jian + Lucia | confirmed (Port Searis epilogue script) |

This answers story-party-timeline open question 3: Gabryel **is** formally removed (009) and re-added (005),
with her struct (level, gear) untouched.

Uncertain: in script 010 the join at 0x3FE0 is reached by a jump at 0x3FD8 after a decode gap (data or a
mis-sized op at 0x3FA8). The Flora tunnel block at 0x3F20 branches on flag 0xC9 (set only in script 021, late
game) to a "poor Rufus... payback" line that seems to lead into that join, which would be a late-game
rejoin path in the tunnel. Needs a cleaner decode or an emulator check.

### 5. The save-disable flag (confirmed) and the US save glitch (confirmed for Flora, not for the fortune)

#### What greys out Save

System menu (`func_02059f84`, menu state 0x33 draws the System list, state 0x35 handles the press). Both call
`func_02056f0c` -> **`func_0206de4c`**:
```c
iVar1 = func_02041918(*(0x020b45b0 + 0x90), 0xcf);   // story flag 0xCF
if (iVar1 != 0) return 0;                              // Save disabled
for (i = 0; table_0209e028[i] != -1; i++)              // s16 list {79, 80, 81, 82, 150}
  if (*(short *)0x020b6be4 == table_0209e028[i]) return 0;   // current map id
return 1;
```
When it returns 0, state 0x33 draws the Save button with palette 0x1A (the red line) and state 0x35 plays
the error sound instead of saving.

So there are two locks:
1. **Story flag 0xCF** (RAM: `*(u32*)0x020B4640 + 0x19`, bit 0x80).
2. **Map list at 0x0209E028**: maps 79 to 82 (map table byte +2 = script 21, the endgame script: the four
   Chamber of Rebirth side rooms) and map 150 (script 15, the Cathedral of Althena script with Gronk, the
   Deuces, the Priest). Map 150 being the Gronk-to-Zethos lockout is likely but uncertain.

#### Who sets and clears flag 0xCF

Every `set flag`/`clear flag` op with operand 0xCF in all 28 scripts (raw scan for `19 00 CF 00` / `1A 00 CF 00`):

- script 021 0x54D8: `set_flag 0xCF`, endgame (Chamber of Rebirth approach). This is the intended
  "no saving from here on" lock. Script 021 also tests 0xCF to skip the Chamber of Rebirth intro once seen
  (0x4C20) and script 018 tests it in the late-game party-chat hints (0x601C).
- **script 010 0x3F50: `set_flag 0xCF`**, in Flora's Underground Tunnel dialogue:
  ```
  03f20: if_all_set_goto [0xC9] -> 0x3f6c        ; late game branch
  03f2c: if_all_set_goto [0xCF] -> 0x3f58        ; "already said it" branch
  03f40: Flora: "That's just too much! I did my best as a guide, and then I just get cast aside! Lovely!"
  03f50: set_flag 0xCF                            ; <- marks the line as seen, reusing the save-lock flag
  03f58: Flora: "I want to go along... I do. But I can't leave my brother here, and I'm sure you'll be fine..."
  ```
- **Nothing ever clears 0xCF** (no `1A 00 CF 00` anywhere, and the only engine reference is the read in
  `func_0206de4c`).

So the "talk to Flora in the Underground Tunnel after she leaves" half of the US save glitch is fully
explained: the script writer used story flag 0xCF as a "has said her line" flag, but 0xCF is the global
save-lock flag. It stays set until power off because it is never cleared; reloading a save restores the
saved flag block (which was saved before 0xCF got set, since saving was impossible afterwards). The second
talk takes the 0x3F58 branch, which matches the FAQ's "talking to her does not affect when she rejoins".

#### The Lind fortune teller (no static cause found)

Script 010 0x3884..0x3A1C (Vile Tribe fortune teller in Lind): asks for 100 S (op 0x32 sub 0x20 deducts
money at 0x020B4824), rolls `op 0x32 sub 0x11` (random 0..4 into int var 0), branches with op 0x0D (goto,
not call, so no call-stack leak), and each outcome first calls 0x3A08 (clear flags 0xD1..0xD5) then sets one
of **0xD1 (Extremely Bad Luck), 0xD2 (Unlucky), 0xD3 (Lucky), 0xD4 (Very Lucky), 0xD5 (Super Lucky)**. It
never touches 0xCF or any word that holds it. The luck flags are read only by `func_02069f34`, which picks
the battle drop table row (drop luck), not by the save check. (Note for the other fork: the fortune changes
item drops for the rest of the session.)

Conclusion (uncertain): the fortune teller is probably a false lead in the FAQ (players who got a bad fortune
had likely also talked to Flora, since both are in the same Frontier stretch), or the cause is dynamic and not
visible statically.

#### Suggested fix

Change script 010 so Flora's line uses a free flag instead of 0xCF: the u32 at 0x3F34 (flag operand of the
check at 0x3F2C) and the s16 at 0x3F52 (operand of the set at 0x3F50). Candidate free flags, not referenced by
any decoded script op or by engine code: 0x4F to 0x5F (engine reads only 0x33, 0x34, 0x6F, 0x78, 0x79, 0xC9,
0xCF, 0xD1, 0xD2, 0xD4, 0xD5). Pick one and confirm in RAM that nothing sets it during a playthrough.
Patching `func_0206de4c` instead would also remove the intended endgame lock, so the script edit is better.

### Emulator tests to settle the rest

1. Save glitch: on a Frontier save after step 12, watch the byte at `*(u32*)0x020B4640 + 0x19`. Talk to Flora
   in the Underground Tunnel: bit 0x80 should turn on and Save should get the red line. Then reload, buy
   fortunes until each of the 5 outcomes has appeared, and confirm bit 0x80 stays off and Save stays enabled.
2. Confirm map 150 is the Gronk-to-Zethos stretch: read the s16 at 0x020B6BE4 (current map id) while Save is
   greyed between Gronk and Zethos.
3. Flora's join in 010: break on `func_02040440` (0x02040440) and check `ctx+0xE0` at the step-10 join to see
   whether the join at 010:0x3FE0 is the step-10 join, and whether flag 0xC9 is set at that point.
4. Leave/rejoin keeps gear: after Lucia leaves (step 9) dump her struct at 0x020B46B4..0x020B470F; it should
   still hold her level, EXP and the gear shorts at +0x40.

## Notes for the enemy and reward research

Stumbled on while doing the above, not investigated further:

- Item drops are rolled per kill in `func_02069f34` (table 0x02097588), only in Combat mode in vanilla (topic 2).
- The fortune teller's luck flags 0xD1 to 0xD5 are read only by `func_02069f34`, so a fortune changes drop luck.
- Battle EXP is accumulated per kill in battle context +0x58 via `func_02053880(enemy, 10)`, doubled at the end
  (`func_02052fb8`), then paid from round context +0x148.
- The EXP table is per character, through the pointer table at 0x020A587C.

## Open questions for the emulator

1. Field frame rate in practice: count frames between run HP ticks (expect 180) and the Virtue clock fill (expect 3600).
2. Whether bosses and scripted battles give EXP (they take the item path, ctx+8 = -1).
3. Map 150 is the Gronk to Zethos save lock (read the s16 at 0x020B6BE4 there).
4. Watch the 0xCF bit (`*(u32*)0x020B4640 + 0x19`, bit 0x80) while talking to Flora in the tunnel and while taking fortunes.
5. Back-row behaviour when the front row is empty (does `func_02050f78` get zero candidates?).
6. Escape success branch (`rand % 10 >= living enemies`), status codes 1, 4 and 7, equipment item 0x0D, and which
   character uses the multi-hit roll at 0x0213B919.
7. Load flags passed to `func_0201d92c` by save load, warp and menu return (matters for the restock-on-entry patch).
8. Whether an opened blue chest stays open after its map restocks.
