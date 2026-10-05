# Plan: broken gear comes back, stolen items come back when the thief dies

Design reference: `docs/design.md` section 6. Background: `docs/re-enemies.md` sections 4 and 5.

Static analysis only (Ghidra decompile `build/arm9_decomp_annot.c` and `uv run python -m dsde.arm9 dis`).
Nothing here has been run in the emulator. Each fact is marked **[confirmed]** (read from code, address
given) or **[uncertain]**. All four ITCM routines below were assembled with `dsde.patching.assemble`
(keystone) as a syntax check: 72 + 92 + 92 + 196 bytes of code plus 104 bytes of data.

## Summary

Four hooks, all single `bl` replacements that call into ITCM and then run the displaced call:

| Hook | Address | Original word | Displaced call | Purpose |
|---|---|---|---|---|
| Battle start | 0x02029BF0 | 0xEB00AA27 | `bl 0x02054494` (battler setup) | clear steal table, snapshot every character's gear |
| Steal | 0x02030F28 | 0xEB00EA97 | `bl 0x0206B98C` (inventory -1) | record (thief battler index, item) |
| Enemy death | 0x02053604 | 0xEB00070A | `bl 0x02055234` (clear status nibble) | give back items this battler stole |
| Battle end | 0x0202AC54 | 0xEB009F0B | `bl 0x02052888` (copy battle stats to save) | put broken gear back, forget unreturned steals |

Breaking needs no hook at the break site: the battle-start snapshot plus the battle-end compare finds every
broken slot, because a break is the only thing that changes equipment during a battle. A break-site hook is
described as an alternative in section 3.4.

## 1. Data structures and game functions

### 1.1 Character equipment **[confirmed]**

- Equipment is 5 halfwords per character at **0x020B4698 + id * 0x5C**: weapon, body, arm, head, accessory.
  Only the first four can break.
  - Evidence: `func_0206b144` pool 0x0206B1C4 = 0x020B4698, indexed `id * 0x5C + slot * 2`; `func_0206b1d0`
    reads `0x020B05B0 + id * 0x5C + 0x40E8 + slot * 2` (same address); `func_0206b4d8` sums gear bonuses over 5
    halfwords from the same place.
  - Slot order: the New Game gear table at 0x02094720 holds, for Jian, 2, 47, 92, 134, 208, and the break
    replacement table holds 1, 45, 91, 133 for Jian's four slots, so slot 0..3 = weapon, body, arm, head.
- Character ids: 0 Jian, 1 Lucia, 2 Gabryel, 3 Flora, 4 Rufus.
- Offsets: with the character struct base at 0x020B4658 (as in `docs/re-field-battle.md`), equipment is
  **+0x40 weapon, +0x42 body, +0x44 arm, +0x46 head, +0x48 accessory**. Note: `docs/re-enemies.md` counts the
  struct from 0x020B465C, which puts the same bytes at +0x3C. The absolute address 0x020B4698 is what matters.
- Slot value 0 means empty: `func_0206b4d8` skips slot items equal to 0.
- **Equipment lives only in the character struct.** The battle does not copy it: `func_0206b144` writes the
  replacement straight into 0x020B4698 + id * 0x5C, and `func_02052888` (battle end copy-back) copies level,
  HP, MP, stats and EXP but not equipment. So gear can be restored any time after the battle, before or
  after `func_02052888`.
- **No stat recompute is needed after the battle.** Out of battle, gear bonuses are added on demand
  (`func_0206b030` reads base stats from the struct, `func_0206b4d8` adds each equipped item's bonuses from
  the item table 0x0209B068). `func_02052888` first calls `func_02055408(record, level)`, which rewrites the
  battle record's stats from the level growth table (0x02094B4C), then copies those base stats to the
  struct. So the struct never holds gear-adjusted stats.

### 1.2 Inventory add/remove: `func_0206b98c(r0 = base, r1 = item id, r2 = delta)` **[confirmed]**

- `r0` = 0x0213B930 (inventory, one byte per item id, at `base + id - 1`), `r1` = item id, `r2` = signed delta.
- New count is clamped to 0..99, stored, and returned in `r0`.
- If `delta > 0` and the item type (item table +0, low nibble) is 5 (cards), it also calls
  `func_0207f930(id - 0xD8)`. Equipment and steal-pool items are never type 5, so this does not matter here.
- The inventory count includes equipped items (re-enemies section 5).
- Standard ARM calling convention: r0 to r3 and r12 are clobbered, r4 to r11 preserved.

### 1.3 Break: `func_0206b1d0(r0 = char id) -> slot or -1` and `func_0206b144(r0 = char id, r1 = slot) -> old item` **[confirmed]**

- `func_0206b1d0` picks a random breakable slot (item flag 0x8000 at item table +0 excludes a slot), applies
  the per-type chances, and returns -1 if the slot already holds that character's replacement item
  (`table[slot * 5 + char]` at 0x0209D0FC). So **one slot can break at most once per battle** as long as the
  replacement is still in it.
- `func_0206b144` (0x0206B144 to 0x0206B1C0):
  - `func_0206b98c(0x0213B930, old, -1)` at 0x0206B17C (r2 = -1 from `mvn r2, #0` at 0x0206B160)
  - `func_0206b98c(0x0213B930, repl, +1)` at 0x0206B1A4, `repl = halfword at 0x0209D0FC + (slot * 5 + char) * 2`
  - `strh repl, [0x020B4698 + char * 0x5C + slot * 2]` at 0x0206B1B0
  - returns the old item id in r0.
- There is no separate "equip" function. Equipping is the halfword store; stats in battle are refreshed by
  `func_02054ebc(actor, 1)` (called right after the break at 0x02030FB0 onward).

### 1.4 The resolver `func_02030b44(r0 = attacker battler, r1 = hit data, r2 = flags)` **[confirmed]**

Register map inside it (prologue 0x02030B44 to 0x02030BB4):

| Register / stack | Value |
|---|---|
| r7 | attacker battler index (param 1) |
| r6 | attacker battler object (`[0x020B8640] + r7 * 300`) |
| r4 | target battler index |
| r5 | target battler object |
| [sp, #0x1C] | target index * 300 |

**The attacker index is never the real enemy index.** Every caller passes 0xC or 0xD (decomp lines around
`func_0202d22c` case 7 and case 9, and `func_02031238`'s loop): 12 is the scratch copy of the acting battler,
13 the scratch copy of the counter/cover battler. The real indices are:

- r7 == 12: acting battler = `ldrsh [ctx, #0x32]`, ctx = `[0x020B8550]` (the same field `func_020514ec` and
  `func_020317d8` use for the acting battler).
- r7 == 13: counter battler = `ldrsh [ctx, #0xCA]` (`func_020317e8(ctx+0xCA battler, 0xD)` makes the copy).

Steal block (0x02030EE0 to 0x02030F3C), taken when `[r6 + 0x88] == 1`:

```
02030ef8  bl   0x0206b69c          ; pick item (0 if nothing to steal)
02030efc  ldr  r1, =0x020b8550
02030f00  ldr  r2, [r1]
02030f04  strh r0, [r2, #0xdc]     ; ctx+0xDC = stolen item (for the message)
02030f08  ldr  r0, [r1]
02030f0c  ldrh r1, [r0, #0xdc]     ; r1 = item id
02030f10  cmp  r1, #0
02030f14  beq  0x02030fd0          ; nothing stolen
02030f18  ldr  r0, =0x0213b930     ; r0 = inventory
02030f1c  mov  r3, #0x11
02030f20  mvn  r2, #0              ; r2 = -1
02030f24  str  r3, [sp, #0x14]
02030f28  bl   0x0206b98c          ; <- STEAL HOOK (word 0xEB00EA97)
```

At 0x02030F28: r0 = 0x0213B930, r1 = stolen item id (287 to 386), r2 = -1, r7 = 12 or 13. **[confirmed]**

Break block (0x02030F40 to 0x02030FCC), taken when `[r6 + 0x88] == 2`:

```
02030f50  ldr  r0, [r0, #4]        ; target battler +4 = character id
02030f54  bl   0x0206b1d0          ; r0 = slot or -1
02030f58  mov  r1, r0              ; r1 = slot
02030f5c..64                       ; -1 -> skip
02030f80  ldr  r0, [r0, #4]        ; r0 = character id again
02030f84  bl   0x0206b144          ; break (word 0xEB00E86E); returns old item
02030f98  strh r0, [ctx, #0xde]    ; old item id for the "broke" message
```

The Termite card (bit 1 of `[ctx]`) and Yeti card (bit 0) checks are earlier, at 0x02030C24 to 0x02030C78
(`local_48 = -1` forces a miss). Nothing in this plan touches them, so **card protection is unchanged**.

### 1.5 Enemy death: `func_02053384(r0 = battler index)` **[confirmed]**

- Its only caller is the loop at the end of `func_020532ac`, which calls it
  for battlers 0 to 11. So r0 is the real battler index, the same index space as `[ctx+0x32]` and
  `[ctx+0xCA]` above.
- r7 = battler index, r6 = battler object, r4 = record offset (index into `[0x020B8620]` * 0x6C).
- 0x020535DC to 0x020535F4: if HP (record +0x14) after damage is still above 0, skip.
  0x020535F8: HP = 0. 0x020535FC `mov r0, r7`. **0x02053604 `bl 0x02055234`** (word 0xEB00070A).
  Every death of every battler (party or enemy, either kill path) passes here.
- After it, the code splits into the 0x4000000 path (EXP kill) and the 0x8000000 path (item roll at
  0x020536D0 `bl 0x02069f34`). The `one-battle-mode` feature patches 0x02053680 so the EXP path also falls into
  0x020536CC; hooking 0x02053604 instead works with or without that feature.
- `func_02055234(r0 = battler)` only clears the low 4 status bits of the record (0x02055234 to 0x02055268);
  it uses only r0 to r3.
- Party battlers are 0 to 2, enemies 4 to 11 (`docs/re-field-battle.md` section 3), so a party death can
  never match a thief entry.

### 1.6 Battle state machine and the two lifetime hooks **[confirmed for the paths read]**

`func_020297d4` runs the battle; its state is `[0x020AFF84 + 0x8C]`.

- **Start:** state 2 (0x02029A10 onward) allocates and zeroes the battle context (`func_02005f74(ctx, 0,
  0x188)` at 0x02029AD4), then sets up the battlers: 0x02029BEC `bl 0x02033afc`, **0x02029BF0
  `bl 0x02054494`** (void, no arguments: its prologue writes r0 to r3 before reading them), 0x02029BF4
  `bl 0x02027edc`. State 0 and state 1 (the chained battle restart for battle type 10) both lead to state 2,
  so this runs once per battle.
  - Side finding: since the context is zeroed here, the Yeti/Termite card bits in `[ctx]` reset every
    battle (answers re-enemies open question 7 statically).
- **End:** every outcome reaches state 0xE:
  - win: state 9, 10, 0xB, 0xC, 0xD, 0xE
  - successful run: state 8 countdown (`ctx+0x130`) sets state 0xD, then 0xE
  - party wiped (`func_0202d22c` returns -3): state 0xD, then 0xE
  - special end for battle type 0xB, and type 10 chain step: state 0xD, then 0xE
  State 0xE (0x0202AC50): `bl 0x02028478`, **0x0202AC54 `bl 0x02052888`** (void, no arguments), then the
  battle buffers are freed (context at `func_02005224(..., [0x020B8550])`). No other exit from the battle
  state machine was found. **[uncertain]** that nothing outside `func_020297d4` ends a battle (a full search
  for writers of `[0x020AFF84 + 0x8C]` was not done).

## 2. ITCM layout

Code goes in the cave from 0x01FF8300 (`dsde.patching.ITCM_CAVE`), as `CaveCode` blocks; data is also a
`CaveCode` block made of `.word 0` lines so it is part of the ITCM image and starts zeroed at boot.

```
cave_bs_data:                     ; 104 bytes
  +0x00  steal table, 16 entries x 4 bytes
           +0 u8  thief battler index (4..11)
           +1 u8  unused
           +2 u16 item id, 0 = empty entry
  +0x40  gear snapshot, 5 characters x 8 bytes (4 halfwords: weapon, body, arm, head)
```

Constants:

| Name | Value |
|---|---|
| INVENTORY | 0x0213B930 |
| INV_ADD | 0x0206B98C |
| CHAR_EQUIP | 0x020B4698 (stride 0x5C) |
| BREAK_TABLE | 0x0209D0FC (u16 [slot * 5 + char]) |
| CTX_PTR | 0x020B8550 |
| STEAL_MAX | 16 |

Max breaks in one battle is 12 (3 members x 4 slots), which the snapshot covers without a table. Steals are
unbounded in principle (a thief can steal every turn), so the steal table has 16 entries; if it ever fills,
further steals behave as in the original game (gone).

All `b`/`bl` targets in main RAM (0x0205xxxx, 0x0206xxxx) are within +-32 MB of ITCM, so plain relative
branches work, as `cave_silver` already does.

## 3. The routines

Each hook site is patched like `SILVER_HOOK` in `src/dsde/features.py`:
`AsmPatch(addr, addr + 4, old_word, old_word, "bl ${cave_label}", note)`.

### 3.1 Battle start: 0x02029BF0, original 0xEB00AA27 (`bl 0x02054494`)

Live registers: none needed by the displaced call (void, no arguments). r4 to r8 belong to
`func_020297d4` and must survive; this routine only uses r0 to r3 and r12. lr = 0x02029BF4 on entry and is
left untouched, so the tail branch returns straight to the caller.

```
cave_bs_start:
    ldr   r0, bs_data
    mov   r1, #0
    mov   r2, #16              ; STEAL_MAX
clear_loop:
    str   r1, [r0], #4
    subs  r2, r2, #1
    bne   clear_loop
    ldr   r1, char_equip       ; r0 now points at the snapshot
    mov   r2, #5
snap_loop:
    ldr   r3, [r1]             ; weapon, body
    ldr   r12, [r1, #4]        ; arm, head
    str   r3, [r0], #4
    str   r12, [r0], #4
    add   r1, r1, #0x5c
    subs  r2, r2, #1
    bne   snap_loop
    b     0x02054494           ; displaced call, returns to 0x02029BF4
bs_data:
    .word ${cave_bs_data}
char_equip:
    .word 0x020B4698
```

0x020B4698 and the 0x5C stride are word aligned, so the two word loads per character are safe.
Snapshotting all five characters (not only the three in the party) keeps the code simple; benched members'
gear cannot change in battle, so they always compare equal.

### 3.2 Steal: 0x02030F28, original 0xEB00EA97 (`bl 0x0206B98C`)

Live on entry: r0 = INVENTORY, r1 = item, r2 = -1 (the call's arguments, must reach `func_0206b98c`
unchanged), r7 = 12 or 13. r3 is dead (its value 0x11 was already stored to [sp, #0x14]).

```
cave_bs_steal:
    push  {r0-r3, lr}
    mov   r3, r7
    ldr   r12, ctx_ptr
    ldr   r12, [r12]
    cmp   r7, #12
    ldrsheq r3, [r12, #0x32]   ; acting battler
    cmp   r7, #13
    ldrsheq r3, [r12, #0xca]   ; counter battler
    ldr   r0, bs_data
    mov   r2, #16
find:
    ldrh  r12, [r0, #2]
    cmp   r12, #0
    beq   found
    add   r0, r0, #4
    subs  r2, r2, #1
    bne   find
    b     done                 ; table full: item is lost as before
found:
    strb  r3, [r0]
    strh  r1, [r0, #2]
done:
    pop   {r0-r3, lr}
    b     0x0206B98C           ; displaced call, returns to 0x02030F2C
ctx_ptr:
    .word 0x020B8550
bs_data:
    .word ${cave_bs_data}
```

### 3.3 Enemy death: 0x02053604, original 0xEB00070A (`bl 0x02055234`)

Live on entry: r0 = dying battler index (= r7), r4/r6/r7 belong to `func_02053384` (preserved by the
convention). `func_02055234` needs only r0.

```
cave_bs_dies:
    push  {r4-r6, lr}
    mov   r4, r0
    ldr   r5, bs_data
    mov   r6, #16
loop:
    ldrh  r1, [r5, #2]
    cmp   r1, #0
    beq   next
    ldrb  r0, [r5]
    cmp   r0, r4
    bne   next
    mov   r0, #0
    strh  r0, [r5, #2]         ; clear first, so a second pass cannot give it twice
    ldr   r0, inventory
    mov   r2, #1
    bl    0x0206B98C           ; item back (+1)
next:
    add   r5, r5, #4
    subs  r6, r6, #1
    bne   loop
    mov   r0, r4
    pop   {r4-r6, lr}
    b     0x02055234           ; displaced call, returns to 0x02053608
inventory:
    .word 0x0213B930
bs_data:
    .word ${cave_bs_data}
```

The item comes back silently. A "got back <item>" message would need the battle message system
(`func_0204582c(0xD, 1, 0x3C)` shows the steal message using ctx+0xDC); left as a follow-up.

### 3.4 Battle end: 0x0202AC54, original 0xEB009F0B (`bl 0x02052888`)

Live on entry: nothing needed by the displaced call (void). r4 to r8 belong to `func_020297d4`; this
routine saves r4 to r10 (8 registers with lr, keeps the stack 8-byte aligned).

For each character 0..4 and slot 0..3: if the slot now holds that character's replacement item for that
slot and the snapshot holds something else, undo `func_0206b144` exactly: put the old item back in the slot,
inventory -1 replacement, +1 old item. Then empty the steal table (thieves who lived keep their loot).

```
cave_bs_end:
    push  {r4-r10, lr}
    bl    0x02052888           ; displaced call first (it does not touch gear or inventory)
    ldr   r4, char_equip
    ldr   r5, bs_snap
    mov   r6, #0               ; character id
char_loop:
    mov   r7, #0               ; slot
slot_loop:
    mov   r10, r7, lsl #1
    ldrh  r8, [r4, r10]        ; gear now
    ldrh  r9, [r5, r10]        ; gear at battle start
    cmp   r8, r9
    beq   slot_next
    add   r2, r7, r7, lsl #2   ; slot * 5
    add   r2, r2, r6           ; + character
    mov   r2, r2, lsl #1
    ldr   r3, break_table
    ldrh  r2, [r3, r2]         ; this slot's broken replacement
    cmp   r8, r2
    bne   slot_next            ; changed by something other than a break: leave it
    strh  r9, [r4, r10]        ; re-equip the original
    ldr   r0, inventory
    mov   r1, r8
    mvn   r2, #0
    bl    0x0206B98C           ; replacement -1
    cmp   r9, #0
    beq   slot_next            ; slot was empty before: nothing to give back
    ldr   r0, inventory
    mov   r1, r9
    mov   r2, #1
    bl    0x0206B98C           ; original +1
slot_next:
    add   r7, r7, #1
    cmp   r7, #4
    blt   slot_loop
    add   r4, r4, #0x5c
    add   r5, r5, #8
    add   r6, r6, #1
    cmp   r6, #5
    blt   char_loop
    ldr   r0, bs_data
    mov   r1, #0
    mov   r2, #16
clear_loop:
    str   r1, [r0], #4
    subs  r2, r2, #1
    bne   clear_loop
    pop   {r4-r10, pc}
char_equip:
    .word 0x020B4698
bs_snap:
    .word ${cave_bs_data} + 0x40   ; or a separate label on the snapshot
break_table:
    .word 0x0209D0FC
inventory:
    .word 0x0213B930
bs_data:
    .word ${cave_bs_data}
```

(`${cave_bs_data} + 0x40` is substituted as `0x1ff8xxx + 0x40`, which keystone accepts in `.word` (checked).)

### 3.5 Alternative for breaking: hook the break itself

If the snapshot approach is not wanted, hook **0x02030F84, original 0xEB00E86E (`bl 0x0206B144`)**.
On entry r0 = character id, r1 = slot (from `mov r1, r0` at 0x02030F58); after the call r0 = old item and
the slot holds the replacement. The ITCM wrapper would `push {r0, r1, r4, lr}`, read
`inventory[repl - 1]` before the call (to know whether the +1 was clamped at 99), call `0x0206B144`, and
append (char, slot, old item, clamped flag) to a 12-entry table; it must return the old item in r0. The
battle-end loop then walks that table instead of the snapshot. This costs a fifth hook but fixes the
99-replacement edge case below.

## 4. What can go wrong

| Case | What happens | Status |
|---|---|---|
| Same character breaks twice | Different slots each restore independently (the loop covers all 4 slots). | confirmed by design |
| Same slot broken twice | Cannot happen: `func_0206b1d0` refuses a slot that already holds the replacement. | confirmed (0x0209D0FC compare at its end) |
| Original item was already the worst item | `func_0206b1d0` refuses it; snapshot equals current; nothing to do. | confirmed |
| Empty slot (item 0) | `func_0206b1d0` treats item 0 as a breakable weapon-type slot (item 0's table entry is all zero), and `func_0206b144` then decrements the inventory byte at 0x0213B92F (id 0 - 1). Original-game bug. The end routine re-empties the slot and removes the replacement but does not try to add item 0. The stray write to 0x0213B92F stays. | confirmed code path, **uncertain** whether a slot can actually be empty in play |
| Player already holds 99 of the replacement | The break's +1 is clamped (no new copy), but the restore still does -1: the player loses one junk replacement item. Fix with the 3.5 variant if it matters. | confirmed (clamp in `func_0206b98c`) |
| Player holds 99 of the original | Break makes it 98, restore makes it 99: fine. Only if a battle drop of the same item lands in between (drops are paid in the result states 9/10, before 0xE) would one copy be lost to the cap. | confirmed |
| Stolen item count | Steal pool only picks items with count >= 1, so the -1 is real; the +1 at death cannot exceed the old count (nothing adds sundries mid-battle). | confirmed (`func_0206b69c`) |
| Equipment changed mid-battle by the player | Not found: battle commands are attack, spell, item, run, auto. The compare also requires "current == replacement", so any other change is left alone. | **uncertain** (no in-battle equip menu seen) |
| Thief identity | The resolver's attacker is the scratch copy 12/13; the hook maps it to `ctx+0x32` / `ctx+0xCA`. If some other caller passes a real index, the routine stores it as is, which is also correct. | confirmed (all three callers) |
| Thief killed by a forced kill (battle type 0x12 sets +0x60 of species 0x9C) | Goes through 0x02053604 like any death: item returns. | confirmed |
| Battle won while the thief is still alive | Only possible if a battle can end in victory with enemies standing (for example some boss fights). The item stays gone. If the design wants "a win always returns it", the end routine can check the outcome (`func_0202b118(0x020B85B8) == 1` is what state 9 uses to pick the win result) and return every entry. | **uncertain** whether such battles exist; design question |
| Enemies fleeing | Enemies never leave battle except by dying (re-enemies section 4). "Thief escapes" only happens when the party runs or loses. | confirmed for the paths read |
| Party wiped | State 0xE still runs: gear is restored, steals forgotten, then the game-over flow. Harmless, and correct for scripted losses. | confirmed |
| Chained battles (type 10) | Each battle passes state 2 and 0xE, so each gets its own snapshot and restore. | confirmed |
| Soft reset or crash mid-battle | ITCM keeps stale entries, but the start hook clears and resnapshots before anything can be recorded. | confirmed by design |
| Hook sites already used | 0x02053680 (`one-battle-mode`) and 0x02052FE0 (`silver`) are near but not the same words. No feature patches 0x02029BF0, 0x0202AC54, 0x02030F28, 0x02053604. | confirmed (features.py) |
| Stack alignment | `cave_bs_dies` pushes 4 registers and `cave_bs_end` 8, so calls out keep 8-byte alignment; `cave_bs_steal` pushes 5 but calls nothing before popping. | confirmed |

## 5. Emulator checks once built

1. Let an enemy break a weapon (Termite card off), win: the weapon is equipped again, the replacement count
   is back to its old value, the weapon's count is back.
2. Same, but run away; same, but lose a scripted fight if one is reachable.
3. Termite card on: no break, nothing changes.
4. Ice Mongrel or Yeti steals, kill it: the item count at 0x0213B930 + id - 1 goes back up at the moment it
   dies. Steal then run: the item stays gone. Next battle: the steal table is empty (no stale returns).
5. Counter-steal: if any enemy steals on a counter (index 13 path), check the right enemy is recorded
   (read the ITCM table at `cave_bs_data`).
