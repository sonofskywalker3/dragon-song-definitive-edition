# Plan: "No effect!" for a capped skill, and a lasting sign of a lowered stat (static trace, 2026-11-12)

Two follow-ups to Weapon Break (docs/plan-weapon-break.md, src/dsde/feat_skills.py). Everything here was read
from the vanilla USA ARM9, the archives, and the existing features; nothing was run. Tags: **[confirmed]** read
in code or data, **[uncertain]** inferred or not traced.

## A. Saying "No effect!"

Today cave_skill_fx skips the stage when the target's ATK stage (record +0x40) is already below 0, the ATK
DOWN banner still plays, and nothing tells the player.

### A1. What the battle can show

**The message line (recommended).** Window 0xD of the battle's window table (0x020B88B4, 0x30 each) is the
line that reads "Lost Abadon card!", "<item> was stolen!", "<item> broke!", "Escape failed!", and "Pray
unsuccessful!". **[confirmed]**

- Opened with `func_0204582c(0xD, 1, frames)`; every in-action caller passes 0x3C (60 frames). The window
  slides in over 4 frames, counts the timer down in func_02045a64, slides out, and then calls func_02044960,
  which zeroes the four content fields.
- Content is chosen by func_02044990 (0x02044990) from battle work (`[0x020B8550]`) fields, first match wins:
  +0xDA bit 0 "Escape failed!" (string 47), +0xDA bit 1 "Pray unsuccessful!" (51), +0xDC item id + " was
  stolen!" (45), +0xE0 "Lost " + card + " card!" (52, 53), +0xDE item id + " broke!" (46). Strings come from
  the battle string list (base 0x020A42E4, u16 offsets at 0x020A41DC), item names from 0x020A7C30 / 0x020A78EC,
  drawn with func_02045114(handle, x, y, string) and measured with func_020450f8.
- It is already opened from inside effect steps: the card path (func_02030844, decomp line 37667: sets +0xDA
  = 1 and opens the window when a card cannot be used), and the steal and break results inside the hit
  resolver func_02030b44 (lines 37923, 37934). So opening it from cave_skill_fx, which runs in the same kind
  of step, does not touch the round state machine: the window has its own timer and the round does not wait
  for it.
- **No existing string fits.** The whole list (entries 0 to 76; 77 to 131 are blanks) has no "No effect",
  "Nothing happened", or "Miss". The closest are "Cannot use!" (50) and "Pray unsuccessful!" (51).

**The floating popups.** func_0202bf9c(x, y, z, kind) puts a cell of btldata entry 2 over a world position:
kind 0 and 1 are the number and the critical number (with func_0202c15c for the digits), 2 is "MISS!" (cell
10), 3 to 9 are the seven round status icons (cells 11 to 17), 10 is "LEVEL UP!" (cell 18). Entry 2 has 26
cells and nothing that reads "no effect"; a new word means adding cells and tiles to that sprite file, which
no tool here writes yet. The existing MISS popup is free to reuse: the hit resolver's miss path is
`func_0202bf9c(battler +0xD4, +0xD8, +0xDC + 0x20, 2)` then sound 0x16. **[confirmed]**

**The result words.** 0x0213B8F8 word 2: -1 darkens the target's palette briefly, any other nonzero value
brightens it, 0 shows nothing; word 3 nonzero flashes, 0x270F in another way. None of them prints text
(func_02030564, lines 37623 to 37639). **[confirmed]**

### A2. Design

1. **String.** "No effect!" + 0xFF is 11 bytes. Entry 99 (u16 at 0x020A42A2, value 0x0317) already points at
   0x020A45FB, the first blank after Weapon Break's name; write the string there (0x020A45FB to 0x020A4605)
   and point entries 100 to 104, whose blanks it covers, at the blank 0x0307, as the skills feature did for 92
   to 98. The blank block then has 0x020A4606 to 0x020A463E left.
2. **A third +0xDA bit.** Hook 0x020449C0 (`ands r1, r2, #1`, 0xE2121001; r2 = the +0xDA halfword, r5 = text
   handle, r7 = x, r6 = y) with `b ${cave}`:

   ```asm
       tst   r2, #4
       beq   1f
       mov   r2, #0
       str   r2, [sp]                 @ the fifth argument, as the vanilla calls pass it
       ldr   r1, =0x020A41DC
       ldrh  r3, [r1, #198]           @ entry 99
       ldr   r4, =0x020A42E4
       add   r3, r4, r3
       mov   r0, r5
       mov   r1, r7
       add   r2, r6, #1
       bl    0x02045114
       b     0x020449EC               @ the function's epilogue
   1:  ands  r1, r2, #1               @ the replaced instruction; the beq after it reads these flags
       b     0x020449C4
   ```

   **[uncertain]** that r0 at the vanilla call is the handle in r5 (the decompile passes func_020455dc's
   result; check the three instructions before 0x020449E8). Writers of +0xDA store 1 or 2, never OR, and
   func_02044960 clears it, so bit 2 cannot leak.
3. **Trigger.** In cave_skill_fx's capped branch: `[work + 0xDA] = 4`, `func_0204582c(0xD, 1, 0x3C)`, and
   leave the result words at 0. Optionally also the MISS popup over the target with sound 0x16, which costs
   nothing and puts the feedback on the enemy as well as in the bar.
4. **No banner on a capped cast.** cave_skill_anim runs after the game's setup, when the target is resolved
   (battler +0x8C) and its stage is known, and nothing can change the stage before the effect step of the same
   action. Two ways, the first to try in the emulator:
   - swap the target's effect script pointer (battle work +0x78 + 4 * target slot, slot 0 here) for a one-step
     cave script that applies the spell effect without the sprite: `0x80400002, 0, slot 0, anim 0, frames 1`
     (0x00400000 is the "apply the spell effect" bit of 0x02094DD4's `0x80603011`; the fixed one-frame form
     is the last step of the two-step script at 0x02094EC4). The fx hook then runs as today and takes its
     capped branch. **[uncertain]** whether the sprite still shows for that frame;
   - or give the capped cast script variants whose last kick has no effect start (second word 0, no
     0x02000000), so no effect script runs at all, and open the message window from cave_skill_anim. The
     line then shows as Jian starts his run instead of on the kick. Certain to work, slightly early.
5. **MP is still spent.** The cost is taken in func_020514ec when the command resolves, before the action,
   and the target can change after the pick (the picked enemy dies, or a lone enemy is chosen with no grid),
   so a refund would need the reduced cost recomputed (func_0206aabc) and added back. A wasted cast costing
   MP matches a missed attack. To keep the player from wasting it knowingly, add a guard to the grid's
   confirm path in spell mode (feat_targeting_menu.py, disp_confirm): when the highlighted enemy's stage is
   already below 0, play SOUND_REFUSE and stay on the grid. That needs a per-spell "would do nothing" test,
   one compare for Weapon Break.

## B. A lasting sign that an enemy has a stat lowered

### B1. What the engine has

- **Status icons are party-only.** func_0202c268 (called each frame from func_02031be0, after the battlers)
  loops over battlers 0 to 2, reads the status with func_02055294, and keeps one icon (popup kind status + 2,
  cells 11 to 17 of btldata 2) in the fixed popup slots 0x1D to 0x1F at (0x3C + 0x58 * i, 7, 0xC0), beside
  each member's HUD panel. Enemies never get one. The popup table (`[0x020B8624]`, 0x78 each) has 32 slots:
  0 to 0x1C handed out by func_0202c420 to numbers and popups, 0x1D to 0x1F the party's. There is no spare
  fixed slot. **[confirmed]**
- **The "Zzz" is a one-shot.** A new status queues (func_0202d1d4) and plays (func_0202d0d0 ->
  func_0202cb9c(battler, status)) an overlay object in one of eight helper battler slots (0x16 to 0x1D), with
  the status's sprite from the pointer table at 0x02139EBC, placed at the target's position and raised
  0x20000. It plays once and frees the slot. func_0202ce58 replays one for party members at the start of a
  round as a reminder. Nothing stays on screen. **[confirmed]**
- **Palette effects can be held, but only stone survives.** func_02034458(battler, kind, flags) starts a
  palette effect in the per-battler table at `[0x020B862C]` (0x14 each): flag 0x20 holds it (stone:
  kind 6, flag 0x20), flag 8 is the slow fade used for deaths (kind 2 to dark, kind 1 to light), flag 4 a
  short flash. A new effect saves the old one at +0x0C, but the updater restores the saved one only when its
  kind is 6 (decomp line 40200). So any held tint other than stone's grey is gone after the enemy's next hit
  flash. Kind 2, the darkening the debuff uses, is also the death fade, so holding it would make a weakened
  enemy look like a dying one. **[confirmed for the flags and the restore test; the colours of kinds 0, 4, 5,
  7 not traced]**
- **The picker.** While the enemy grid is up the bottom bar shows the highlighted enemy's name (drawn by
  func_02044c00 from the card item name of the grid cell, feat_targeting_names.py) and the cursor corners
  frame it on the field (feat_targeting_brackets.py). The corners prove a path for drawing our own sprites at
  an enemy's screen position: the hook on the render call at 0x02031C58 runs every frame after all battlers
  have submitted their sprite requests (0x30 bytes each in the pool at `[0x020B8618]`: position, inverse
  scale at +0x18, pieces), bounds the enemy's opaque pixels, and submits copies of menu buttons there with
  func_02036360. Requests can be scaled and land on either screen. **[confirmed in src]**
- **Font.** The dialogue font (pack/005, 8 x 16 cells, one byte per character) has the letters, digits,
  `! ? - , . : '`, and a solid down-pointing triangle in cell 1 (the page-turn mark). It has no arrow glyphs:
  cells 0xC3 and 0xC4, the up and down arrows of the Japanese font, are blank in the USA font. **[confirmed
  for pack/005; uncertain that the battle name bar uses the same font file]**
- **btldata 157.** One animation, four 16 x 16 cells (sword, armor, ring, hat), in no table. It is an
  ordinary battle sprite file, so it draws through the same request path as any effect sprite, but the
  status-icon drawer cannot use it: that drawer only shows cells of btldata 2. Using 157 means loading it
  (battle files are loaded by entry number into the work slots at +0x50.. only for an action) or copying its
  tiles into the shared OBJ tile buffer at battle start. **[confirmed format; loading path uncertain]**

### B2. Options, cheapest first

1. **A tag on the name bar while the enemy is highlighted.** After the name, draw "ATK-" (later "DEF-",
   or both) when the highlighted enemy's stage is below 0: "Bealzebub  ATK-". All glyphs exist, the bar
   already composes two strings side by side for "<item> was stolen!" (func_020450f8 for the width), and the
   grid cell to battler map is in cave_tgt_state. One hook in the name drawer plus a few bytes of text. It
   shows only while picking, which is when the player decides. Unknowns: the exact draw site in func_02044c00
   for the list page and the bar's width with a 12-letter name.
2. **A small icon beside the enemy on the field, all the time.** From the render hook, for every living
   enemy with a lowered stat, submit one small sprite at a corner of its bounding box, as the cursor corners
   are submitted. It shows on both screens and through every phase of the battle, and several icons can
   stack for several stats. The work is the art source: the hook can only draw tiles that are in the shared
   OBJ tile buffer. Candidates: the sword of the Fight command button (a menu sprite; whether its tiles stay
   in the buffer outside the command page is not checked) drawn at reduced scale, plus a down arrow of one or
   two 8 x 8 tiles written into a free tile of the buffer from cave data; or the sword and armor cells of
   btldata 157 copied into the buffer at battle start. Unknowns: a free tile range and palette in the OBJ
   buffer, the cost of bounding eight enemies a frame (the corners bound one), and hiding the icon while the
   enemy is mid-attack or dying.
3. **A held tint.** `func_02034458(enemy, kind, 0x20)` after the stage is applied, plus a patch so the
   updater restores that kind after hit flashes as it does kind 6. Small code, no art, but one tint cannot
   say which stat is down, it fights the stone, death, and status flashes for the same palette slot, and the
   usable kinds are not identified.

### B3. Recommendation

Build option 1 with the "No effect!" work: it is a few dozen instructions, needs no art, and covers the
moment the information matters. Then prototype option 2, which is what Jeff described (sword and down arrow
by the monster); its first step is an emulator look at what the OBJ tile buffer holds during a battle and
whether the Fight button's sword is there to borrow. Skip the tint.
