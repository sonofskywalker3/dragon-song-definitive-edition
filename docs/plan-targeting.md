# Plan: manual Attack targeting (design item 4)

Static analysis of the USA ARM9 binary, 2026-10-05. Nothing here has been run in an emulator. Each fact is
marked **confirmed** (read in code, address given) or **uncertain**. Function names are the Ghidra names in
`build/arm9_decomp.c`; register notes come from `uv run python -m dsde.arm9 dis`.

Design (docs/design.md section 4): when the player picks Attack, the player chooses the enemy. If that enemy is
dead when the attack happens, the attack goes to the next living enemy in the list. Multi-hit attacks move their
remaining hits to the next living enemy instead of whiffing. Auto battle keeps the game's own rule.

## Summary of the approach

- **UI**: reuse the item list page (page 4) as an enemy list, switched on by a mode byte in ITCM. Page 4 already
  has everything the picker needs: list rows with name labels, a highlight, a keyboard cursor with a 2D grid,
  paging dots, an OK button (id 6, the A button) and a back button (id 7, the B button), and the info window
  that prints the highlighted entry's name. Enemy names come for free: an enemy's card item id
  (0xD8 + species) has both a name string and a pre-rendered name label.
- **Storage**: the chosen enemy battler index (4..11) goes in the member's `+0x8C`, the same field the
  ally picker writes. The game clears it every round, and the vanilla UI never writes 4..11 there for a party
  member, so 4..11 at execution time means "player chose this".
- **Execution**: one BL hook in func_020514ec replaces the auto rule's call to func_02050f78 when a manual
  target is present, redirecting to the next living enemy in list order if it died.
- **Per hit**: one BL hook in func_02030b44 replaces the "target dead, whiff" test with a redirect for party
  Attack hits.
- 4 hooked words, all new code in ITCM (estimate 0.6 to 0.9 KB of the ~31 KB cave).

## 1. The existing single-ally picker (page 6), end to end

All **confirmed** unless marked.

**Reached from**: page 2 (spell list) when the spell's flags `& 0xC0000000 == 0x80000000` (single ally), and page 4
(item list) button id 6 (OK). Both save the previous page in `0x020B8800 + 0xC` (short, `[3]`), set
`+0xA = 6` and flag bit 1 (`[0] |= 2`), and slide out the list rows 8..13 and dots 14..19 (func_02036694 page 2
branch and page 4 `uVar9 == 6`).

**Draw**: func_0203962c `case 6` (0x0203962c) creates buttons 8, 9, 10 with id 10 through func_02037934(index, 10),
slides in button 5 (Back, id 8, offset 1000) and buttons 8..10, and sets the help line to system string 0x2C
via func_020350c4(0x2C). String 0x2C decodes to "Who to use it for?" (table: u16 offsets at 0x020A41DC into
0x020A42E4; encoding `A` = 0x02, `a` = 0x3A, space = 0x00). func_02037934 `case 10` (decomp line ~43278):

- the button is for battler `index - 8` (0..2), only if func_02031b70 >= 0 (present, alive or KO'd, so revive
  items can target KO'd allies);
- sprite: anim set `0x020B8758` (party portraits), frame = character id (`+0x7A`/`+0xBC` = battler `+4`);
- position y = 0x78; x = 0x80 (1 member), 0x40 / 0xC0 (2), 0x30 / 0x80 / 0xD0 (3); slides in from x = -64.

So it iterates **party battlers 0..2 only** and shows **character portraits**. It cannot show enemies without new
graphics, which is why the plan uses the list page instead.

**Touch input**: func_02039bec does the hit test (func_0202b74c against the button box at `+0xC0..+0xC6`, set by
func_02036064). The portrait buttons are group 0x10000 (word0 `0xA001000A`). For id 10 it sets the info window
to mode 1 (`0x020B8800 + 0x90 = 1`, `+0x94 = index - 8`), so window 0 prints the ally's name, and returns the
button index. func_0203a34c then calls func_02036694(index) (call at 0x0203A6E0): one tap confirms.

**Keyboard input**: func_02034ae4 (called at 0x0203A680) sets `0x020B8800 + 0x2C = 1` when A is newly pressed;
for pages 0, 1, 3, 6 the generic tail moves the cursor `+0x28` by +1/-1 on Right/Left over buttons 8.. that exist
and are not disabled (func_02034a20), and moves the four cursor-corner sprites (buttons 0..3, id 0x11) with
func_020347c8. func_02039bec then activates the cursored button when `+0x2C` is set, so A confirms the cursored
portrait. B (`param_3 & 2`) activates the visible button with id 7 or 8: on page 6 that is Back (index 5, id 8).

**Confirm** (func_02036694 `case 6`, `uVar9 == 10`, 0x02037340): by `[3]`:
- 2 (spell): `battler[+0x86] = [0x20]` (spell id), `[4] = 4`, `battler[+0x8C] = index - 8`;
- 4 (item): `battler[+0x86] = [0x20]` (item id), `[4] = 5`, `battler[+0x8C] = index - 8`;
then slides everything out (func_020377f0), `+0xA = 1`, flag bit 1, func_02039570(0), sound 1, returns 2.
The battler is `0x020B8800 + 0x34` (`[0xd]`, the member whose command is being entered).
func_0203a34c (0x0203A794..) turns `[4]` into `+0x84`: 3 -> 1 Attack, 4 -> 2 spell, 5 -> 4 item.

**Cancel** (`uVar9 == 8`, 0x020372BC): slides out buttons 8..10 and 5, `+0xA = [3]` (back to the list),
func_020378b0(-1, 0x40000), func_02035104, func_0204582c(0, 1, -1), sound 3.

**Where the choice lives per battler**: `+0x8C` (short, first of 8 target slots) = ally battler index;
`+0x86` = spell or item id; `+0x84` = action, written by func_0203a34c.

**Enemies on the touch screen** (observation, uncertain for other battles): the battle scene spans both screens.
In `build/emu/b2.png` (256x384, top screen above bottom) the two front-row mushrooms are drawn on the bottom screen
at about y = 13..46, above the command panel, while the flying enemy is on the top screen at y = 105. So tapping
enemies directly is only partly possible and would need the 3D position projected to screen space. Not planned;
a list on the bottom screen is used instead.

## 2. Routing Attack into a target page

### Where Attack is chosen (confirmed)

func_02036694 page 1 (`case 1`) jumps through a table: 0x020367E8 `addls pc, pc, r6, lsl #2`, so id 3 (Attack)
uses the entry at **0x020367FC = 0xEA00003A (`b 0x020368EC`)**. The Attack block 0x020368EC..0x02036914:

```asm
020368ec  mov  r7, #2              ; result: member's command is final
020368f0  bl   func_020377f0       ; slide all buttons out
020368f4  ldr  r1, =0x020B8800
020368f8  mov  r0, r5              ; r5 = 1
020368fc  ldr  r2, [r1]
02036900  str  r6, [r1, #0x10]     ; [4] = 3
02036904  orr  r2, r2, #2
02036908  strh r0, [r1, #0xa]      ; next page = 1 (for the next member)
0203690c  str  r2, [r1]
02036910  bl   func_020284d8       ; sound 1
02036914  b    0x02037690          ; epilogue
```

Registers at the jump-table entry (confirmed, 0x02036694..0x020367E8): r0 = button array base, r1 = 0x020B8800,
r2 = 1, r4 = &0x020B86FC, r5 = 1 (bVar4), r6 = button id (3), r7 = 0 (result), r8 = button index, sb = 0xC8,
sl = page. The epilogue 0x02037690 reads only r5 (hide or show the cursor corners) and r7 (return value) and then
pops r4..sl, lr, so a routine entered by B may clobber every register except sp, as long as it sets r5 and r7.

### Why page 4 and not a new page number

The page number `0x020B8800 + 8` is switched on by jump tables bounded at 7 in func_0203962c (builder),
func_02036694 (buttons), func_02034ae4 (keys) and func_02035128 (info window). A new page 8 would need hooks in
all of them. Reusing page number 4 with an ITCM mode byte needs a hook only where page 4 behaves differently:
its OK, back and row buttons, all of which pass through the single func_02036694 call at 0x0203A6E0.

What page 4 gives without new code (all confirmed):

- Builder (func_0203962c default path for pages 2, 4, 5): slides in the actor portrait (button 4), OK (index 6,
  id 6), back (index 7, id 7), the dots (func_020359f4, from flags at `+0xA8`) and the rows (func_02035310: up to
  6 rows at indices 8..13, id 0xE, group 0x200000, from the list of ids at `0x020B8800 + 0x44`, count `+0x40`,
  first shown entry `+0x3C`, style `+0x82` = 0 item rows / 1 spell rows). Highlights row `[10] = +0x30` and puts
  the info window in mode 2 (func_02035128(1): page 4 -> func_02035834 = 0 -> mode 2 with the highlighted id).
- Info window mode 2 (func_02044c00, 0x02044CDC..0x02044CF8) prints the name string of the id
  (0x020A7C30 + u16 at 0x020A78EC + 2*id) and, for `0xD8 <= id < 0x114`, returns without printing a count.
  Card ids are 0xD8 + species (docs/re-enemies.md; func_0206892c maps an enemy row to its species), so the
  window prints the enemy's name.
- Row labels: func_02035d88(0) sets the dot flags and calls func_02035784(0), which copies 0x100-byte name images
  from the item-name file (`*0x020B86E8`, sysmenupack.dat entry 0x36 loaded by func_02028160) at
  `0x200 + (id - 1) * 0x100` into the row label slots `*(0x020B87C8 + 0x2C) + row * 0x100`. Entry 0x36 is
  107008 bytes = 0x200 + 416 images (build/unpacked/sysmenupack/054.bin), so every card id up to 0x10E has an
  image. Confirmed by size; that the images for boss ids 0xFA..0x10E show the boss names is **uncertain**.
- Keyboard: func_02034ae4 `case 4` moves the highlight over the 6 rows with the D-pad and pages at the edges,
  re-uploading labels. A activates OK (index 6 comes before the rows in func_02039bec's loop), B activates id 7.
- The item description window (window 4) is shown only while `0x020B8800 + 0x84` (`[0x21]`) < 2
  (func_02039570). Setting it to 2, the value func_0203aa10 uses at the start of input, keeps it off.

### Enemy list contents and order (proposal)

Eligibility follows the game's own melee rule (func_020514ec 0x02051BD8..0x02051C18, confirmed): character id 3
or a character with equipment 0x0D (func_0206b8ec(0x0D, char id)) may hit any enemy (rows 0); everyone else hits
battlers 8..11 only (rows 2). If no living enemy is eligible, list every living enemy (vanilla would divide by
zero in func_02050f78 in that case; whether the game ever lets it happen is **uncertain**).

Order ("the list" for the redirect rule): front battlers 8..11 first, then back 4..7, each sorted by the battler
position word `+0xD4` ascending, ties by battler index. `+0xD4/+0xD8/+0xDC` are confirmed position fields
(func_02030b44 0x02030C78..0x02030C88 passes them to the damage-number effect func_0202bf9c), but that `+0xD4`
is the left-to-right screen axis is **uncertain** (emulator check 2). If it is not, use whichever axis is, or
plain battler index order.

Card id per entry: `0xD8 + func_0206892c(battler[+4])`. Note: row 156 (the Blue Dragon's summons) maps to
species 54, whose name slot is "Jian" (docs/re-enemies.md); special-case it to the Blue Dragon's id if wanted.

### ITCM state

```
tgt_state:
  +0  u8 mode      1 = page 4 is the enemy picker
  +1  u8 manual    1 = hit 0 of the current Attack used a manual target (read by later hits)
  +2  s8 last_row  last tapped row button index, for tap-again-to-confirm
  +4  u8 map[8]    list entry -> battler index 4..11
```

### Hook A: Attack opens the enemy list (0x020367FC)

Patch: **0x020367FC: 0xEA00003A (`b 0x020368EC`) -> `b ${cave_tgt_open}`** (B, not BL; in range).

```asm
cave_tgt_open:                  @ entered by B from the page 1 jump table
    ldr   r4, =0x020B8800
    ldrh  r0, [r4, #0x34]       @ member entering a command
    ldr   r1, =0x020B8640
    ldr   r1, [r1]
    mov   r2, #0x12C
    mla   r8, r0, r2, r1        @ r8 = member battler
    mov   r0, r8
    bl    tgt_rows              @ r0 = 0 (any row) or 2 (front only)
    bl    tgt_fill_list         @ r0 = rows; fills +0x44 ids, +0x40 count, map[]; returns count
    cmp   r0, #1
    bgt   1f
    blt   0f                    @ no enemy: vanilla rule
    ldr   r1, =tgt_state
    ldrb  r0, [r1, #4]          @ exactly one choice: store it, no page
    strh  r0, [r8, #0x8c]
0:  mov   r5, #1
    mov   r6, #3
    mov   r7, #0
    b     0x020368EC            @ original Attack block
1:  mov   r0, #0
    str   r0, [r4, #0x3c]       @ first shown entry
    strh  r0, [r4, #0x82]       @ item-style rows
    str   r0, [r4, #0x30]       @ cursor starts on row 0
    mov   r0, #2
    str   r0, [r4, #0x84]       @ [0x21] = 2: no description window
    mov   r0, #0
    bl    0x02035D88            @ dots + row labels from the card ids
    ldr   r5, =0x020B86FC       @ slide out page 1: buttons 8, 9, 10 and Back (5)
    ldr   r0, [r5]
    add   r0, r0, #0x640
    mov   r1, #0
    mov   r2, #0
    bl    0x020376CC
    ldr   r0, [r5]
    ldr   r1, =0x708
    add   r0, r0, r1
    mov   r1, #0
    mov   r2, #0
    bl    0x020376CC
    ldr   r0, [r5]
    ldr   r1, =0x7D0
    add   r0, r0, r1
    mov   r1, #0
    mov   r2, #0
    bl    0x020376CC
    ldr   r0, [r5]
    add   r0, r0, #0x3E8
    mov   r1, #0
    mov   r2, #0
    bl    0x020376CC
    mov   r0, #4
    strh  r0, [r4, #0xa]        @ next page = 4 (built next frame by func_0203962c)
    ldr   r0, [r4]
    orr   r0, r0, #2
    str   r0, [r4]
    ldr   r1, =tgt_state
    mov   r0, #1
    strb  r0, [r1, #0]          @ mode on
    mvn   r0, #0
    strb  r0, [r1, #2]          @ no row tapped yet
    mov   r0, #1
    bl    0x020284D8            @ menu sound, as the Special/Item branches
    mov   r5, #1
    mov   r7, #0                @ command not final yet
    b     0x02037690            @ epilogue
```

The slide-out list copies the Special branch (func_02036694 page 1 `case 4`: offsets 0x640, 0x708, 2000, 1000);
func_0203962c then builds page 4 on the next call (single call site 0x0202A3A4, confirmed) because `+0xA` and
flag bit 1 are set. Optional nicety: start the cursor on the row of the enemy this character chose last round
(keep `last_pick[3]` in ITCM).

### Hook B: page 4 buttons while the picker is on (0x0203A6E0)

Patch: **0x0203A6E0: 0xEBFFEFEB (`bl func_02036694`) -> `bl ${cave_tgt_dispatch}`**. Only call site (confirmed).
In: r0 = button index (from func_02039ba0). Out: r0 = result (0 stay, 2 member done). Must keep r4..r11.

```asm
cave_tgt_dispatch:
    push  {r4-r6, lr}
    mov   r4, r0
    ldr   r5, =tgt_state
    ldr   r6, =0x020B8800
    ldrb  r0, [r5, #0]
    cmp   r0, #0
    beq   9f
    ldrsh r0, [r6, #8]
    cmp   r0, #4
    movne r0, #0
    strbne r0, [r5, #0]         @ left page 4 some other way (mic Run): drop the mode
    bne   9f
    ldr   r0, =0x020B86FC
    ldr   r0, [r0]
    mov   r1, #200
    mla   r0, r4, r1, r0
    ldr   r0, [r0]
    lsl   r0, r0, #20
    lsr   r0, r0, #20           @ button id
    cmp   r0, #6
    beq   1f                    @ OK button or A: confirm
    cmp   r0, #7
    beq   2f                    @ back button or B: cancel
    cmp   r0, #0xE
    bne   9f
    ldrsb r1, [r5, #2]
    cmp   r1, r4
    beq   1f                    @ second tap on the same row: confirm
    strb  r4, [r5, #2]          @ first tap: vanilla highlights it, info window shows the name
9:  mov   r0, r4
    bl    0x02036694
    pop   {r4-r6, pc}

1:  bl    0x02035724            @ highlighted row 0..5, -1 none
    cmp   r0, #0
    blt   8f
    ldr   r1, [r6, #0x3c]
    add   r0, r0, r1
    add   r1, r5, #4
    ldrb  r0, [r1, r0]          @ chosen enemy battler
    ldrh  r1, [r6, #0x34]
    ldr   r2, =0x020B8640
    ldr   r2, [r2]
    mov   r3, #0x12C
    mla   r1, r1, r3, r2
    strh  r0, [r1, #0x8c]       @ manual target
    mov   r0, #3
    str   r0, [r6, #0x10]       @ [4] = 3 -> +0x84 = 1 Attack
    bl    0x020377F0            @ slide every button out (buttons 0..19, rows and dots included)
    mov   r0, #1
    strh  r0, [r6, #0xa]        @ next page 1
    ldr   r0, [r6]
    orr   r0, r0, #2
    str   r0, [r6]
    mov   r0, #0
    strb  r0, [r5, #0]          @ mode off
    bl    0x02039570            @ r0 = 0
    mov   r0, #1
    bl    0x020284D8
    bl    0x020349E0            @ hide cursor corners, as the vanilla epilogue does
    mov   r0, #2
    pop   {r4-r6, pc}

2:  mov   r0, #0
    bl    0x020395E0            @ OK and back buttons out
    @ rows 8..13 and dots 14..19 out: for i in 0..5:
    @   0x020376CC(btns + (i + 0xE) * 200, 0, 0); 0x020376CC(btns + (i + 8) * 200, 0, 0)
    @ (same loop as func_02036694 page 4 uVar9 == 7)
    mov   r0, #1
    strh  r0, [r6, #0xa]        @ back to the command page
    ldr   r0, [r6]
    orr   r0, r0, #2
    str   r0, [r6]
    mvn   r0, #0
    mov   r1, #0x40000
    bl    0x020378B0
    mov   r0, #0
    strb  r0, [r5, #0]
    bl    0x02039570            @ r0 = 0
    mov   r0, #3
    bl    0x020284D8            @ back sound
    bl    0x020349E0
    mov   r0, #0
    pop   {r4-r6, pc}

8:  mov   r0, #2                @ nothing highlighted (should not happen)
    bl    0x020284D8            @ error sound, as other refusals use
    mov   r0, #0
    pop   {r4-r6, pc}
```

After result 2, func_0203a34c (0x0203A744..0x0203A7D4, confirmed) writes `+0x84 = 1` and the battle loop moves to
the next member exactly as after vanilla Attack. The stale-mode check is safe because vanilla page 4 is only
reachable through page 3, whose button press passes through this hook first.

Paging dots (group 0x20000) and the D-pad never reach func_02036694, so they work unchanged.

## 3. The consume point: func_020514ec

### What it does today (confirmed)

Party Attack branch, 0x02051BD8..0x02051CC8. Before the loop: r4 = actor, r8 = hit count (1, or
`rand % byte[0x0213B919] + 1` for character id 3), sb = mode (1 lowest HP, 3 random: 30% or multi-hit),
sl = rows (2 front, 0 both). Loop (r7 = hit index):

```asm
02051c3c  mov   r0, sb
02051c40  mov   r1, sl
02051c44  bl    func_02050f78       ; <- hook point
02051c48  add   r1, r4, r7, lsl #1
02051c4c  strh  r0, [r1, #0x8c]     ; target[i]
          ... (+0x2E bit i for listed flying enemies when sl != 2)
02051ca4  add   r7, r7, #1
02051ca8  cmp   r7, r8
02051cac  blt   0x2051c3c
02051cb0  ldrsh r0, [r4, #0x8c]     ; no target -> +0x84 = 0
```

When the call for hit 0 runs, `+0x8C` still holds whatever was there before the turn: 0xFFFF (cleared by
func_02031b10 in battle sub state 1 every round, decomp line 33181, and before every Auto round, line 33402),
0..2 (an ally picked for a spell or item, then Auto overrode `+0x84`), or 4..11 (only Hook B writes that for a
party member). So 4..11 at hit 0 means "player chose this". Confirmed by reading every writer of party `+0x8C`
in the UI (func_02036694 pages 2, 5, 6 write 0 or 0..2).

### Hook C (0x02051C44)

Patch: **0x02051C44: 0xEBFFFCCB (`bl func_02050f78`) -> `bl ${cave_tgt_pick}`**.
In: r0 = mode, r1 = rows, r4 = actor (read only), r7 = hit index. Out: r0 = target. Keep r4..r11.

```asm
cave_tgt_pick:
    push  {r4-r6, lr}
    mov   r5, r0                @ mode
    mov   r6, r1                @ rows
    ldr   r2, =tgt_state
    cmp   r7, #0
    bne   1f
    mov   r3, #0
    strb  r3, [r2, #1]          @ hit 0: forget the previous action
    ldrsh r0, [r4, #0x8c]
    cmp   r0, #4
    blt   8f
    cmp   r0, #11
    bgt   8f                    @ no manual target: vanilla rule
    mov   r3, #1
    strb  r3, [r2, #1]
    b     2f
1:  ldrb  r3, [r2, #1]
    cmp   r3, #0
    beq   8f                    @ later hit of a vanilla attack
    ldrsh r0, [r4, #0x8c]       @ hit 0's resolved target
2:  mov   r1, r6
    bl    tgt_next              @ itself if alive, else next living in list order, -1 none
    cmp   r0, #0
    popge {r4-r6, pc}
8:  mov   r0, r5
    mov   r1, r6
    bl    0x02050F78
    pop   {r4-r6, pc}
```

All hits of a manual Attack (character id 3's multi-hit included) go to the chosen enemy; the hit hook below moves
later hits on when it dies. The +0x2E flying-enemy bits after the call keep working because they read the stored
result. The 70/30 roll and the hit-count roll still consume `rand`, so the RNG sequence is unchanged.

### Helpers (pseudo C, ARM in ITCM, must keep r4..r11)

```c
int tgt_rows(battler *b) {                 // same rule as 0x02051BD8..0x02051C18
    int id = b->char_id;                   // +4
    if (id == 3) return 0;
    return func_0206b8ec(0x0D, id) == 1 ? 0 : 2;
}

// key(b): (b >= 8 ? 0 : 1), then battler[b].+0xD4, then b. Lower key = earlier in the list.
static bool eligible(int b, int rows) { return rows == 0 || (rows == 2 ? b >= 8 : b < 8); }

int tgt_fill_list(int rows) {              // writes 0x020B8800+0x44 (u16 ids), +0x40 count, tgt_state.map
    for (pass = rows; ; pass = 0) {
        n = living enemies b in 4..11 with func_02031b70(b) > 0 and eligible(b, pass), sorted by key;
        if (n || pass == 0) break;
    }
    for k < n: ids[k] = 0xD8 + func_0206892c(battler[b_k].+4); map[k] = b_k;
    *(u32 *)(0x020B8800 + 0x40) = n; return n;
}

int tgt_next(int start, int rows) {        // start may be dead or removed; its +0xD4 is still readable
    for (pass = rows; ; pass = 0) {
        best = first = -1;
        for b in 4..11 with func_02031b70(b) > 0 and eligible(b, pass):
            if (b == start) return b;
            if (key(b) > key(start) && (best < 0 || key(b) < key(best))) best = b;
            if (first < 0 || key(b) < key(first)) first = b;
        if (best >= 0) return best;
        if (first >= 0) return first;      // wrap to the top of the list
        if (pass == 0) return -1;
    }
}
```

Battler pointer: `*(0x020B8640) + b * 0x12C`. func_02031b70 takes the battler pointer.

## 4. Multi-hit redirect: func_02030b44

### What it does today (confirmed)

```asm
02030b78  cmp     r3, #0              ; r3 = ctx(0x020B8550)->+0xC8, cover/counter mode
02030b8c  lsreq   r1, fp, #0xc        ; fp = param_3 (hit flags)
02030b90  andeq   r1, r1, #7
02030b94  addeq   r1, r6, r1, lsl #1  ; r6 = attacker (battler 12 or 13, the scratch copy)
02030b98  ldrsheq r4, [r1, #0x8c]     ; r4 = target index
02030ba4  mul     r1, r4, r1          ; r1 = r4 * 300
02030bac  streq   r4, [sp, #4]        ; local_4c
02030bb0  str     r1, [sp, #0x1c]
02030bb4  add     r5, r5, r1          ; r5 = target battler
02030bb8  ands    r1, r2, #0x40
02030bbc  beq     0x2031120
02030bc0  mov     r0, r5
02030bc4  bl      func_02031b70       ; <- hook point
02030bc8  cmp     r0, #0
02030bcc  ble     0x2031120           ; dead target: the hit whiffs
```

The rest of the function keeps the target only in r4, r5, `[sp+4]` and `[sp+0x1c]` (every later use checked in
the disassembly: 0x02030C00..0x02031204). The attacker is battler 12, a copy of the actor made by
func_020317e8(actor, 12) (decomp line ~35870) after targeting, so its `+0x84` and `+0x8C` are the resolved ones
(**uncertain** only in timing; vanilla attacks working implies the copy follows func_020514ec).

### Hook D (0x02030BC4)

Patch: **0x02030BC4: 0xEB0003E9 (`bl func_02031b70`) -> `bl ${cave_tgt_hit}`**.
In: r0 = r5 = target battler. Live in caller: r4 target index, r5 target ptr, r6 attacker, fp hit flags, and
`[caller sp + 4]`, `[caller sp + 0x1c]`. The hook may change r4 and r5 on purpose; r0..r3, ip are scratch.

```asm
cave_tgt_hit:
    push  {lr}                  @ caller sp = sp + 4
    bl    0x02031B70
    cmp   r0, #0
    popgt {pc}                  @ alive: unchanged
    ldr   r1, =0x020B8550
    ldr   r1, [r1]
    ldrsh r1, [r1, #0xc8]
    cmp   r1, #0
    popne {pc}                  @ cover/counter: leave alone
    ldr   r1, [r6]
    tst   r1, #8
    popne {pc}                  @ enemy attacker
    ldrsh r1, [r6, #0x84]
    cmp   r1, #1
    popne {pc}                  @ only Attack (multi-target spells keep skipping dead slots)
    cmp   r4, #4
    poplt {pc}
    cmp   r4, #11
    popgt {pc}
    push  {r0}
    mov   r0, r6
    bl    tgt_rows
    mov   r1, r0
    mov   r0, r4
    bl    tgt_next
    cmp   r0, #0
    poplt {r0, pc}              @ nobody left: whiff as before
    add   sp, sp, #4
    mov   r4, r0                @ caller's target index
    ldr   r1, =0x020B8640
    ldr   r1, [r1]
    mov   r2, #0x12C
    mul   r3, r0, r2
    add   r5, r1, r3            @ caller's target pointer
    str   r4, [sp, #8]          @ caller [sp+4]
    str   r3, [sp, #0x20]       @ caller [sp+0x1c]
    lsr   r1, fp, #12
    and   r1, r1, #7
    add   r1, r6, r1, lsl #1
    strh  r4, [r1, #0x8c]       @ keep the slot in step for any later reader
    mov   r0, #1
    pop   {pc}
```

This applies to every party Attack, Auto included, which matches "never wasted". It runs only when the slotted
target is dead, so vanilla single hits are unaffected.

## 5. Keyboard and cancel

All vanilla page 4 behaviour (confirmed in func_02034ae4 `case 4/5` and func_02039bec):

- D-pad moves the highlight over the rows (2D grid, pages at the edges when there are more than 6 entries);
  the info window shows the highlighted enemy's name.
- A = OK button (id 6) -> Hook B confirm. B = back button (id 7) -> Hook B cancel, back to the command page with
  the same member (`+0x34` unchanged, `[4]` untouched, `+0x8C` untouched).
- Touch: tap a row to highlight it, tap it again or tap OK to confirm; tap Back to cancel.

L/R cycling is not in vanilla page 4. If wanted, hook **0x0203A680: 0xEBFFE917 (`bl func_02034ae4`)**: call the
original, then if the mode byte is set and L or R is newly pressed (pad struct 0x020AFF74 `+6`; DS key bits
0x200 L, 0x100 R, **uncertain** that the pad word uses hardware bit order), move `+0x28` by one row, call
func_02037910(row + 8), func_020378b0(-1, 0x200000), func_02035128(1), func_020347c8(button, 0) and sound 0, as
func_02034ae4 does after its own row move (confirmed).

## Patch list

| Address | Original | New | Purpose |
|---|---|---|---|
| 0x020367FC | 0xEA00003A `b 0x020368EC` | `b ${cave_tgt_open}` | Attack opens the enemy list |
| 0x0203A6E0 | 0xEBFFEFEB `bl 0x02036694` | `bl ${cave_tgt_dispatch}` | OK / Back / row taps while picking |
| 0x02051C44 | 0xEBFFFCCB `bl 0x02050F78` | `bl ${cave_tgt_pick}` | use the stored target, redirect if dead |
| 0x02030BC4 | 0xEB0003E9 `bl 0x02031B70` | `bl ${cave_tgt_hit}` | per-hit redirect instead of whiff |
| 0x0203A680 (optional) | 0xEBFFE917 `bl 0x02034AE4` | `bl ${cave_tgt_keys}` | L/R cycling |

All branch encodings were checked against their targets. In `src/dsde/features.py` this is one Feature
(`manual-targeting`) with CaveCode blocks (`cave_tgt_open`, `cave_tgt_dispatch`, `cave_tgt_pick`, `cave_tgt_hit`,
helpers, `tgt_state` as `.word 0` / `.byte` data) and AsmPatch entries of one word each, like `silver-drops`.

## Risks, riskiest first

1. **Page 4 reuse** (Hooks A and B). Anything page-4-specific that the hooks do not intercept runs as the item
   list would. Reviewed: builder, keys, dots, info window, description window (suppressed by `[0x21] = 2`),
   func_02035310's page 5 only 0xDD check. Not reviewed: the scroll buttons 0x14/0x15 (ids 0xF/0x10,
   group 0x100000) and any header art that says "Items". Emulator check 1.
2. **Row labels for enemies**: the card-name images exist by file size; their look in item-style rows and the
   boss ids 0xFA..0x10E are unverified.
3. **Duplicate names** ("Blob, Blob"): the list order is meant to match left to right on screen, but nothing on
   the battle scene marks which enemy is highlighted. A top-screen marker needs research (candidates: spawning an
   effect from func_0202bf9c at the enemy's `+0xD4/+0xD8/+0xDC`, its types 3..9 are unidentified; or blinking the
   enemy). Ship the list first, add a marker if playtesting asks for it.
4. **Hook D frame offsets**: correct for this build (0x02030B44 prologue `sub sp, sp, #0x2c`, slots 4 and 0x1C);
   any other patch to func_02030b44's prologue would break them.
5. **Redirect animation**: a redirected later hit lands on the new enemy while the attacker's lunge was aimed at
   the first one. Cosmetic; check how it looks.
6. **Position axis**: list order depends on `+0xD4` being horizontal.
7. **Front row empty with rows = 2**: the list falls back to all enemies and tgt_next does the same, so a manual
   attack never hits func_02050f78's zero-candidate path; a vanilla Auto attack still can (unchanged behaviour).

## Emulator checks (BizHawk plans, keyboard only)

1. Pick Attack with 2+ enemies: page 4 opens with enemy names, D-pad moves, info window names the enemy, B goes
   back to the command page for the same member, A confirms and the next member's command page opens.
   Watch `battler[member] + 0x8C` (pointer at 0x020B8640, 0x12C per battler) after confirm: 4..11.
2. Log `+0xD4/+0xD8/+0xDC` of each enemy in a 3-enemy fight with a screenshot: which axis is left to right.
3. Kill the chosen enemy with an earlier party member, then let the next member's manual attack run: break at
   0x02051C48 and confirm r0 is the next enemy in the list.
4. Multi-hit (character id 3): kill the target with hit 1, confirm hit 2 damages the next enemy (watch HP at
   `*(0x020B8620) + rec * 0x6C + 0x14`) and the kill gives EXP and drops normally.
5. After a kill, read the dead battler's `+0x00` flags: does bit 0 stay set (does not matter for tgt_next, which
   uses only the dead battler's position, but confirms the alive test).
6. Auto battle and the microphone Run still behave as vanilla; after a mic Run during the picker, the next
   round's item list works (mode byte dropped).
7. A boss fight with adds (Caucus with Orcus and Morus): labels and names correct.
8. One-enemy battle: Attack confirms at once, no list.

## Findings from the emulator (2026-10-05)

Built as `manual-targeting` in `src/dsde/feat_targeting.py` (execution hooks C and D, list order),
`feat_targeting_menu.py` (hooks A and B) and `feat_targeting_picker.py` (the grid). What turned out
different from the plan above:

- **Page 4 is a grid of icons, not a list of name rows.** Each "row" button is a 32 x 32 cell showing the
  item image; for a card id that is a small picture of the enemy. Six cells per page in three columns of
  two (cell i at x = 0x70 + (i >> 1) * 0x2A, y = 0x68 + (i & 1) * 0x20, centres). The highlighted cell is
  covered by the red OK stamp, and the bottom bar prints the highlighted enemy's name, with NO (B) and OK (A)
  at its ends. The vanilla D-pad handler moves +-2 for Left/Right and +-1 for Up/Down inside a column.
- **Layout follows the battle screen** (Jeff's request after the first build): top grid row = back-row
  enemies (battlers 4..7), bottom grid row = front-row enemies (8..11), each left to right. Cell 2c holds the
  c-th back-row enemy, cell 2c + 1 the c-th front-row enemy; empty cells are holes. Two extra hooks make
  holes work: the three calls of func_02035310 (0x02034E7C, 0x02039948, 0x0203A004) go through a wrapper that
  zeroes the hole buttons, and the key handler call at 0x0203A680 (the plan's optional L/R site) goes to our
  own D-pad handler while the picker is up (Left/Right along the row skipping holes, Up/Down to the nearest
  column with an enemy). A member who reaches only the front row gets a bottom row with an empty top row.
  The first highlighted cell is the first real one (top-left, or bottom-left if the top row is empty).
- **Position axis confirmed**: battler `+0xD4` is the horizontal screen position, lower = further left
  (73 and 118 for the two enemies of each row in the temple battle).
- **Dead targets are usually replaced, not left empty**: when a front-row enemy dies, a back-row enemy is
  copied into its battler slot (seen as battler 6 becoming battler 10). A chosen slot whose enemy died
  therefore often holds the enemy that stepped forward, and the attack hits that one. The "next enemy in
  the list" redirect runs when the slot stays dead (no back row left), verified both before the attack
  (`tgt_redirect_pick`: 9 dead -> attack on 10) and between target resolution and the hit
  (`tgt_redirect_hit`: hit moved to 10, its HP 32 -> 0). Hook D's frame offsets were right.
- **Character id 3 is Flora**, not Rufus (docs/re-field-battle.md). She reaches both rows. The multi-hit roll
  could not be forced: byte 0x0213B919 read 1 at the roll even with the address pinned to 4, so a real
  2+ hit attack is not tested yet. Later hits use the same hook D path that was verified.
- **Touch**: tapping a cell highlights it; tapping the same cell again comes back to the button hook with the
  same row and confirms (the OK stamp does not intercept). The harness could not tap anywhere before: the
  BizHawk config binds the mouse to the touch axes, which overrides the Lua position (the game always saw
  the centre). `dsde.emu` now runs EmuHawk with a copy of the config without that binding.
- Menu field `+0x2C` is set to 1 by the list-page builder itself (`[0xb] = 1`), it is not a leftover A press.
- The picker sets the member's `+0x8C` to -1 when Fight is opened, so a stale ally index never survives.
- Unverified: boss name images (Gideon shows as "Gideon 2"/"Gideon 3" by name string), 4 enemies in one row (the 4th column lands on page 2), mic Run while the
  picker is up.
- **Multi-hit attacks (tested 2026-10-05, docs/test-report-battle.md)**: Jian has a real 3-hit combo until
  the curse, and Flora's hit count comes from her weapon (effect 0x2B = up to 2, 0x2C = up to 3; Composite
  Bow, item 39, is 0x2C), rebuilt from gear at every action by func_0206ab6c, which is why pinning
  0x0213B919 did nothing. Hits of one action only queue damage in the stat record (+0x60) and HP drops when
  the action ends, so the original hook D never saw the target dead and every later hit landed on an enemy
  the first hit had already killed. Fixed with `cave_tgt_live`: an enemy counts as dead once HP plus the
  queued damage is 0 or less (hook D and the next-enemy search). Verified: Jian's combo goes 9, 10, 10 and
  Flora's three arrows 9, 10, 10 after the first hit kills 9.
- **Redirect animation (2026-10-06)**: the lunge is aimed once at action step 0 from slot 0, so a
  redirect only moved the damage. `feat_targeting_anim.py` re-aims after every step when the target is
  dead or doomed and hits remain, and hops the attacker to the new enemy (docs/test-report-battle.md
  section 3).
- **Blue Dragon's summons (2026-10-06)**: row 156 maps to species 54, one past the last enemy species
  (Ignatius, card 0x10D), so its card id 0x10E is the Jian character card: Jian's portrait and "Jian". The
  game never names them on screen (no target selection, no summon message); fan walkthroughs call them
  bubbles (lparchive.org Lunar: Dragon Song update 14, retromaggedon.com walkthrough), and they are drawn
  as white and purple bubbles. `feat_targeting_names.py` shows row 156 as item 0x19C, an unused
  placeholder named "K26", renamed "Bubble" (its string runs on into K27's, and K27 points at K28's). Its
  icon (sysmenupack entry 0x36: a 256-color BGR555 palette, then 16x16 8bpp icons of four 8x8 tiles) is
  made at build time from the bubbles' battle sprite: the species table at 0x02096EDC (0x1C bytes per
  species, +0x10) names their btldata entry, 0xDD, an MCE0 sprite file (format in `src/dsde/mce.py`);
  its cell 3, a 15 x 14 frame of the wobble, is copied unscaled with each color mapped to the nearest
  icon palette color. The info window (func_02044c00) prints no name
  for ids 0x1A0 and up and a count after anything outside 0xD8..0x113, so 0x19C is treated as a card at
  0x02044CE4. Verified in a scripted Blue Dragon fight (`tgt_bluedragon`): "Blue Dragon", then "Bubble"
  twice for the front-row bubbles.

## Cursor corners on the field (2026-10-07)

Jeff: the picker's blue corners should also frame the highlighted enemy on the battle field. Built in
`feat_targeting_brackets.py` (part of `manual-targeting`):

- Every battle sprite is a request in the pool at *0x020B8618 (0x30 bytes each); func_02033804 turns them
  into OAM for both screens on one canvas, y 0..191 the touch screen and -192..-1 the top screen. The corner
  tiles (OBJ tiles 0x46..0x49, 8bpp) are in the OBJ buffer both engines get, with identical palettes, so a
  corner request lands correctly on either screen.
- The hook replaces `bl 0x02033804` at 0x02031C58 (after every battler's request). While the picker is up it
  bounds the opaque pixels of the highlighted enemy's request (pieces at +0x14, OAM shape/size in the piece's
  attribute bits 4..7, tiles at 64 * ((tile >> 1 for 4bpp) + request +0x28) in *0x020B861C). The request's
  +0x18 is the inverse of the drawn scale (func_02001364 = 0x1000000 / x, as the renderer uses it).
- It submits a stack copy of each corner button (buttons 0..3, 200 bytes) moved to the box with func_02036360,
  so the real buttons' animation is untouched.
- Seen (`tgt_brackets`): Jian's picker on the skeleton and the spider, Flora's on the flying back row (top
  screen), corners gone once the action starts; the Blue Dragon (`diag_brackets_boss`): the box runs off the
  left edge with the dragon, only its right corners show.

## No leap at an out-of-reach enemy mid-combo (2026-10-07)

Jeff: Jian leapt up at a flying back-row enemy when his combo killed the last front-row enemy. The next-enemy
search fell back to every row when nobody was in reach, and both mid-action redirects (the hit hook and the
lunge follow-up in feat_targeting_anim.py) used it. Now `cave_tgt_reach` searches the attacker's rows only and
the mid-action redirects use it: with nobody left in reach the remaining swings stay on the first target and
whiff, as in vanilla. The game's refill brings the back row down after the action, and the next attack hits
it in the front row. `cave_tgt_next` (reach, then every row) is kept for the start of an action only.
Seen in `tgt_no_leap`: both front enemies die at frames 3049 and 3077, no flyer takes damage, slots 9 and 10
are refilled at 3266 and the next round's attack hits slot 9 (300 -> 164); `tgt_multihit_jian` still goes
9, 10, 10.
