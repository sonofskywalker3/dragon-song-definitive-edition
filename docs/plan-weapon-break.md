# Plan: Weapon Break, the first level-learned skill (static trace, 2026-11-12)

Jian learns Weapon Break at level 9: 8 MP, one enemy picked by the player, ATK down one stage, never below
stage -1. This is the end-to-end prototype for docs/plan-skills.md. Everything below was read from the vanilla
USA ARM9 and the archives; nothing has been run. Tags: **[confirmed]** read in code or data, **[uncertain]**
inferred or not traced. Addresses are vanilla; words in parentheses are the vanilla instruction words to check.

Short version: no table has to move for one skill. Spell entry 38 is an unused row inside the table's own
footprint, the name list has spare slots, MP is charged by the game's own Special path, and the stat stage
and its recompute are two existing calls. The real work is the target pick from the Special list and the
description file, which needs 23 records appended.

## 1. Spell table space

Table 0x02094978, 0x0C per entry: u32 flags, u32 MP cost, u8 Lucia level, u8 Flora level, u16 effect row.

**Entry 38 is free [confirmed by data, uncertain that nothing indexes it].** The 12 bytes at 0x02094B40 are
`00000000 00000000 FF FF 0000`: a blank row with both level bytes at "never", sitting between entry 37 and the
stat growth table at 0x02094B4C (which has its own pool words, 0x020554F0 and 0x020555E4). No pool word points
into 0x02094B40..0x02094B4B. So the prototype writes entry 38 in place and raises four loop bounds; nothing
moves.

Pool words that point at the table **[confirmed, full scan of arm9 for words in the table's range]**:

| Pool word | Value | Reader |
|---|---|---|
| 0x020500A8 | 0x02094978 (+0 flags) | func_02050094 |
| 0x020500C0 | 0x02094982 (+0x0A row) | func_020500ac |
| 0x020500D8 | 0x0209497C (+4 cost) | func_020500c4 |
| 0x02050720 | 0x02094978 | func_020500dc (effect) |
| 0x0205084C | 0x02094978 | func_02050748 (cure) |
| 0x02050A70 | 0x02094978 | func_02050850 (heal) |
| 0x02050C48 | 0x02094978 | func_02050a74 (castable) |
| 0x02050E5C | 0x02094980 (+8 Lucia level) | func_02050c50 (listed) |
| 0x02050E64 | 0x02094981 (+9 Flora level) | func_02050c50 |
| 0x02050E68 | 0x02094978 | func_02050c50 |

Loop bounds 0x26 **[confirmed; the other `cmp #0x26` sites in arm9 are in unrelated functions]**:

| Address | Word | Function |
|---|---|---|
| 0x02035F64 | 0xE3560026 | func_02035e00 case 2: fills the battle Special list (menu ids at 0x020B8844, max 0x1E) |
| 0x02050EB0 | 0xE3540026 | func_02050e74: first castable spell |
| 0x02050F04 | 0xE3540026 | func_02050ec8: "has any spell" (enables Special in battle, the Magic page in the field) |
| 0x02065068 | 0xE3580026 | func_02064ff0: fills the field Magic list (10 shown; stack buffer sized for 0x26 entries) |

**Prototype:** three data words (0x02094B40 flags, 0x02094B44 cost, 0x02094B48 levels and row) and the four
bounds to 0x27. feat_mp and feat_spell_levels keep poking the table in place; nothing to redirect.

**Later, for the full kit (about 25 more entries):** the table has to move, and the ITCM cave is reachable
because every reader uses an absolute pool word. Then: the ten pool words above get the new base (+0, +4, +8,
+9, +0x0A), the four bounds get the new count, and the cave copy must be built from the vanilla bytes plus the
cost and level edits of feat_mp.py (`NEW_SPELL_COSTS`) and feat_spell_levels.py (`SCHEDULE`), because their
`Patch` records address the old table and would no longer be read. The cleanest shape is one module that owns
the whole table and emits it as cave data. Cave space: 14,152 bytes used, **17,848 bytes free** with the
default features (cave ends at 0x01FFBA48); a 64-entry table is 768 bytes. **[confirmed by layout_cave]**

## 2. Name and description

**Name [confirmed].** Battle and field menus draw spell names from the battle string list: text base
0x020A42E4, u16 offset table 0x020A41DC (132 entries), strings end with 0xFF, same character codes as the item
names. The Special name bar (func_02044c00 case 3) uses index `spell + 0x35`, so Healing Water (1) is entry 54
and Thunder Sword (15) is entry 68. The field menu uses the same list (pool 0x0205C108 = 0x020A4246, which is
entry 53 of the same table). Spell 38 is entry 91.

Entries 77 to 131 are 55 two-byte blank strings (0x020A45CF to 0x020A463D); only 77 to 90 can ever be asked
for (enemy skills 24 to 37, whose names are never shown). So:

- write `Weapon Break` + 0xFF (13 bytes) at 0x020A45ED, over the blanks of entries 92 to 98;
- set offset entry 91 (u16 at 0x020A4292, vanilla 0x0307) to 0x0309;
- tidy: point entries 92 to 98 at the blank 0x0307.

This is byte data inside arm9 (`byte_patches`; the offset entry is not word-aligned). The blank block holds
about 80 bytes of names; the full kit needs more, which the duplicated save-error strings (entries 73 to 76
repeat 70 to 72) or a second list in the cave can supply later (the cave is not reachable from a u16 offset, so
that needs a code change in func_02044c00).

**Description [confirmed].** sysmenupack entry 61 ("CMTX"). The battle loads it whole (pointer at 0x020B8700)
and sets the text base to file + 0x24. func_02044fec draws the record at `base + spell * 0x3D`: fixed
61-byte records (two lines of up to 30 characters, 0xFF ends the text; the u16 table after the header is
not used by this reader). The file has exactly 16 records (0 = "DAMMY", 1 to 15 the player spells) and ends
at 0x3F4, so spell 38 would read past the buffer. Fix: one `DataPatch` on sysmenupack entry 61 at offset 0x3F4
with `old = b""` and 23 new records (16 to 37 a lone 0xFF, 38 the text). `apply_data` appends when the offset
is the end of the entry, and the entry is recompressed. Item descriptions are the same format in entry 58
(text base file + 0x346, 417 records).

Text: `Lower one monster's attack` (26 characters, one line).

**Field menu [confirmed for the list, uncertain for its description reader].** func_02064ff0 lists every
spell func_02050c50 accepts with the field flag, castable or not, so a battle-only skill would appear greyed
in Jian's Magic page, as Dragon Magic presumably does (not checked on screen). The field loads the same entry
61 through func_02066c88(4, 0x3D, 0x10, 0); its description reader was not traced. For the prototype the skill
is hidden in the field (section 3), which avoids that reader.

## 3. Learn and cast checks

Levels: u32 level index (0 = level 1) at 0x020B4664 + 0x5C * character; Jian's is **0x020B4664**. The game
reads the field record even in battle. Level 9 is index 8. **[confirmed: the Lucia and Flora compares at
0x02050CC4 and 0x02050CF8]**

**Listing, func_02050c50.** The Jian branch starts at 0x02050D24 (`mov r0, #0xc`, 0xE3A0000C); r8 = spell,
r7 = 0 in the field, r6 = result so far (0), r5 = character id. Patch that word to `b ${cave_skill_list}`:

```asm
cave_skill_list:
    cmp   r7, #0                @ field: not shown (prototype)
    beq   1f
    ldr   r0, =cave_skill_levels
    ldrb  r0, [r0, r8]          @ Jian's learn level index for this spell, 255 = not learned by level
    cmp   r0, #255
    beq   1f
    ldr   r1, =0x020B4664
    ldr   r1, [r1]
    cmp   r1, r0
    movhs r6, #1
    b     0x02050DDC            @ the common tail (max MP against cost, then return r6)
1:  mov   r0, #0xc              @ the replaced instruction
    b     0x02050D28            @ ring tests as before
```

`cave_skill_levels` is 0x27 bytes of cave data, all 255 except `[38] = 8`. The tail's max-MP test is already
neutralised by spell-levels (`bl func_020500c4` at 0x02050DE8 returns 0); without that feature Jian's 18 max
MP at level 9 still passes a cost of 8. Gabryel (0x02050DA8) and Rufus (0x02050DC4) take the same hook later
with a level row each.

**Castable, func_02050a74.** For Jian (r6 = 0) a listed spell is castable only with its ring equipped
(0x02050AF8 to 0x02050B78). Patch 0x02050AF8 (`mov r0, #0xc`, 0xE3A0000C) to `b ${cave_skill_cast}`:

```asm
cave_skill_cast:                @ sb = spell, r6 = 0 (Jian), r7 = -1
    mov   r0, #0xc
    mul   r1, sb, r0
    ldr   r0, =0x02094978
    ldr   r4, [r0, r1]          @ flags, as the replaced code loads them
    tst   r4, #0x00F00000       @ no ring bit: a level skill, already listed
    moveq r7, #1
    beq   0x02050B88            @ MP test
    b     0x02050B08            @ ring tests, r4 loaded
```

The MP test that follows compares battle MP (stat record +0x18) with the cost because flag 0x2 is set.
**MP is charged by the game**: func_020514ec, for a party Special, calls func_02050a74 again and subtracts its
return from record +0x18 (decomp line 58339). **[confirmed]**

**Does Special open for Jian with no ring? [confirmed by code path]** The command page's Special button
(func_02036694 page 1 case 4, 0x02036988) asks func_02050ec8(member, 1). It is 0 for Jian without a ring
today, and becomes 1 from level 9 once spell 38 is listed. Before level 9 nothing changes.

## 4. Target picking

**Vanilla [confirmed].** The Special list's OK handler reads the spell's flags at 0x02036CE0 and branches on
`flags & 0xC0000000`: 0x80000000 (one ally) opens the ally picker (page 6); everything else, including 0
(one enemy), goes to 0x02036D20, which stores the spell in battler +0x86, sets menu +0x10 to 4, writes **0**
to battler +0x8C and ends the member's command. No enemy is ever picked in the menu. When the action runs,
func_020514ec's party Special branch (0x02051CCC) handles 0 at 0x02051D2C: `func_02050f78(3, 0)`, a uniformly
random living enemy of either row (mode 3 gives each living enemy `rand % 100` and takes the highest; the row
filter 0 allows all), stored in +0x8C.

**Cards [confirmed for the resolver, menu side not read].** The item branch of func_020514ec uses the item
flags' top two bits the same way: 0 is `func_02050f78(3, 0)`. The Dagon card (flags 0x04000002) therefore
stones a random living enemy. The Tick card (item 0xE2) is special-cased to random front-row enemies and is
refused when the front row is empty, which is its "on the ground" wording.

**The Fight grid today [confirmed in src].** cave_tgt_open (from the Fight entry of the command page) clears
battler +0x8C to -1, fills the grid for the rows the member reaches (cave_tgt_fill), and switches to page 4 with
`cave_tgt_state` mode 1. cave_tgt_dispatch (wrapping the menu's button handler at 0x0203A6E0) confirms by
writing the enemy's battler index (4 to 11) to +0x8C and menu +0x10 = 3 (Attack), or cancels to the command
page. cave_tgt_pick (0x02051C44) uses a 4 to 11 value in +0x8C through cave_tgt_next (that enemy, or the next
living one). The target slots are cleared to 0xFFFF every round (func_02031b10), so a stale pick cannot leak.

**Smallest change for a picked single-enemy spell:**

1. **Open.** 0x02036CFC (`beq 0x02036D20`, 0x0A000007) becomes `beq ${cave_skill_open}`. The spell id is
   already in menu +0x80. The cave clears +0x8C, calls cave_tgt_fill with ROWS_ANY, and:
   - one enemy: stores it and ends the command with its own copy of the 0x02036D20 block that leaves +0x8C
     alone (the vanilla block zeroes it at 0x02036D58);
   - several: slides the Special rows out the way the one-ally branch does (0x02036D88: button 4, the OK and
     back pair, row buttons 8 + i and dots 0xE + i), then opens page 4 as cave_tgt_open's `open_list` does,
     with mode **2** in `cave_tgt_state`.
2. **Confirm.** In cave_tgt_dispatch's confirm path, mode 2 writes battler +0x86 = menu +0x80 and menu +0x10 =
   4 (Special) in place of 3. Cancel can go to the command page as it does for Fight.
3. **Use the pick.** 0x02051D34 (`bl func_02050f78`, 0xEBFFFC8F) becomes `bl ${cave_skill_pick}`: with r4 =
   actor, a +0x8C of 4 to 11 goes through cave_tgt_next(r0 = that index, r1 = ROWS_ANY); anything else, or no
   living enemy, falls through to the original call. The caller stores r0 in +0x8C at 0x02051D3C.

**[uncertain]** Step 1's page change from the Special list (page 2) to the grid (page 4): both pages use the
same row buttons, and the only vanilla example of leaving page 2 for a picker goes to page 6, which uses
different ones. This needs frames from the emulator. The fallback is to ship step 3 alone first: the skill
then hits a random enemy exactly as a vanilla single-enemy spell would, and every other piece can be tested.

## 5. The effect

func_020500dc(caster battler, target battler, spell) runs once per target. On entry r8 = caster, r7 =
target, r6 = spell, r5 = flags, r4 = 4 for a party caster. It zeroes the four result words at 0x0213B8F8, then
applies revive, heal, cure, element damage, the buffs, and the status skills 0x1F to 0x25.

**Flags for entry 38: 0x00000002** (battle use only). Top bits 0 = one enemy. With no other bit: no heal
(func_02050850 needs 0x10 or 0x20), no cure (0x08000000), no element or weapon damage (0x1000 to 0x8000,
0xC0000, 0x100000 to 0x800000), no buff, not a ring spell, not field-usable, and the id is outside the status
switch. Vanilla would do nothing at all for it. **[confirmed]**

**Hook:** 0x020503A0 (`ands r0, r5, #0x1000000`, 0xE2150401), the first buff test, becomes
`bl ${cave_skill_fx}`:

```asm
cave_skill_fx:                  @ r6 = spell, r7 = target battler index; must return the flags of the ands
    push  {r4, lr}
    cmp   r6, #38
    bne   9f
    ldr   r0, =0x020B8640
    ldr   r0, [r0]
    mov   r1, #0x12C
    mla   r4, r7, r1, r0        @ r4 = target battler
    ldr   r0, [r4, #0x10]       @ stat record index
    ldr   r1, =0x020B8620
    ldr   r1, [r1]
    mov   r2, #0x6C
    mla   r0, r0, r2, r1        @ r0 = target stat record
    ldrsh r1, [r0, #0x40]       @ ATK stage
    cmp   r1, #0
    blt   9f                    @ already lowered: no second stage
    push  {r0}
    mov   r1, #4                @ stat 4 = ATK
    mvn   r2, #0                @ -1
    bl    0x02054DEC
    pop   {r0}
    mov   r1, #1
    ldr   r2, [r4]
    tst   r2, #8                @ enemy target
    blne  0x02069AD8            @ enemy recompute
    bleq  0x02054EBC            @ party recompute (not reachable for this skill)
    ldr   r0, =0x0213B8F8
    mvn   r1, #0
    str   r1, [r0, #8]          @ result word 2 = -1, as a debuff card sets it
9:  ands  r0, r5, #0x1000000    @ the replaced instruction, last so its flags survive the pop
    pop   {r4, pc}
```

(As written the `blne` / `bleq` pair needs the flags kept across the first call; write it as a real branch.)

This mirrors the card path **[confirmed]**: func_0206a2f8, for an effect with flag 0x02000000, calls
func_02054dec(record, stat, -1) for each stat in the mask, sets result word 2 to -1, and recomputes with
func_02069ad8 when the **target** is an enemy (battler flag 8), func_02054ebc otherwise. The spell buffs in
func_020500dc pick the recompute by the caster's side, which is the same thing for a party buff but would be
wrong for a debuff on an enemy, so the hook tests the target.

**[uncertain]** What the battle shows from the result words. A debuff card leaves words 0 and 1 at 0 and word
2 at -1 and the screen shows only the banner, so the same values should show the same; the capped case leaves
all four at 0, which is what a spell that does nothing leaves, and whether that prints a "0" or "MISS" is not
traced. If it does, set word 2 to 2, the value the card path uses for a resisted status.

A general form for later skills is a cave table per spell (kind, stat, delta, cap) read by the same hook; the
status skills can call the body of func_0206a2f8's status block or func_0202d1d4(target, status) directly.

## 6. Animation

Effect table 0x02096180, 0x10 per row: u16 0, u16 slot count, s32 effect sprite, u32 caster script, u32
per-target effect script. All 49 rows are used, but a row can be shared.

**Prototype: row 27, the Quetzalcoatl card's row [confirmed].** Rows 21 to 26 are the six "UP" banners (sprites
298 to 303, effect script 0x02094E14) and rows 27 to 33 the six "DOWN" banners and "STATUS DOWN" (304 to 310,
effect script 0x02094DD4); all thirteen use caster script **0x02095294**, not the generic cast 0x02094E84:
animation 0 of slot 0, then animation 1 held for three 30-frame steps and a last step that waits for the
effects. Row 27 = sprite 304, "ATK DOWN".

For a party Special (func_02068308 case 2) slot 0 is the character table's +0x0C file unless the spell is 10 to
13; Jian's is **btldata 18**, the same file his card use loads (+0x0E is also 18). It has 2 animations, 9
cells: he raises a fist and a ring flashes above it (sheet: build/re_skills2/e018.png). So the prototype looks
exactly like Jian using the Quetzalcoatl card, on one enemy: the pose already recorded in
build/cards/card_abadon_def_down.gif with a single blue "ATK DOWN" banner. The per-target effect script is
attached to every target slot that is not -1, so one target gives one banner. No art, no table change:
entry 38's row field is 27.

**Follow-up, not designed here.** The kick-plus-icon version needs (a) a caster script of its own (a physical
script such as the single attack 0x020958C0 with the hit step's damage flags off, slot 0 forced to Jian's attack
file the way spells 10 to 13 force theirs, around 0x020686B0), (b) an effect sprite made from btldata 157's
sword icon plus a drawn down-arrow, as a new battle sprite file, and (c) a 50th effect row. The table is
followed by other data, so (c) means moving it: pool words 0x02068880 (+8), 0x02068884 (+4), 0x02068888 (+2),
0x0206888C (+0) in func_02068308 and the matching four in func_02068034 (0x020682F0 to 0x020682FC), plus
func_0207d940's use through func_020500ac. Adding a btldata entry is a new problem (archive count, and whether
the loader takes an entry number above the current last one); reusing an existing unused entry such as 16, 17,
or 29 avoids it. **[uncertain throughout]**

## 7. Test plan

Addresses: Jian level index u32 0x020B4664; field MP 0x020B4670, max 0x020B4674; battle stat records at
`[0x020B8620] + 0x6C * n` (Jian n = 0: HP +0x14, MP +0x18, max MP +0x20; a forced enemy in slot 5 is battler
and record 9: ATK stage s16 +0x40, so `[0x020B8620] + 0x3CC + 0x40`); battler objects `[0x020B8640] + 300 * i`
(command +0x84, spell +0x86, targets +0x8C); result words 0x0213B8F8; menu 0x020B8800 (page +8, spell +0x80).
The effective ATK field of the enemy record is not pinned down here: read it through func_02053880(record, 4)
or dump the record before and after and diff (**[uncertain]**).

Plans, modelled on emu/plans/test_spell_levels_*.plan and the forced battles of dsde.enemy_anims_plans:

1. `test_skill_list_8` / `test_skill_list_9`: pin u32 0x020B4664 to 7, then 8; open the first temple battle;
   Special is refused at 7 (the menu stays on the command page), opens at 8 with one entry; shot of the name
   bar ("Weapon Break", 8) and the top-screen description.
2. `test_skill_mp`: Jian's MP poked to 7: the entry is greyed and OK plays the refuse sound; at 8 it casts and
   record +0x18 goes 8 -> 0.
3. `test_skill_effect`: forced Ice Mongrel (row 20) with 30000 HP, Jian's HP not pinned. Watch the enemy's
   +0x40 short: 0 -> -1 on the cast, still -1 after a second cast. Record Jian's HP loss per enemy hit for
   three rounds before and three after (docs/re-cards.md predicts about one third less at one stage).
4. `test_skill_target`: two enemies forced (slots 5 and 6); pick the second in the grid; `battlers` shows
   Jian's +0x8C = that index, and only that record's +0x40 changes. Repeat with the picked enemy killed by
   Lucia first: the cast moves to the other.
5. `test_skill_field`: field Magic page for Jian at level 9: unchanged from vanilla (no new entry).
6. Regression: `test_spell_levels_1/5/12`, `test_mp_cast`, `tgt_grid`, `tgt_redirect_pick`, `test_kill_on_hit`,
   and a Dragon Magic cast with the Blazing Ring (enemy_dark_jian_spell.plan casts Inferno).
7. A GIF of one cast for Jeff.

## 8. Build order and risks

Steps, each testable alone:

1. Entry 38 (flags 2, cost 8, levels FF FF, row 27), the four bounds, the name bytes and offset. Test with the
   existing ring path by temporarily giving entry 38 a ring bit, or go straight to step 2.
2. cave_skill_list and cave_skill_cast with cave_skill_levels: the skill is listed and castable at level 9,
   costs MP, plays Jian's card pose with an ATK DOWN banner on a random enemy, and does nothing (tests 1, 2).
3. The description records (DataPatch append on sysmenupack 61). Until this is in, the top screen reads past
   the file for spell 38, so do it together with step 2.
4. cave_skill_fx: the stage, the cap, the recompute (test 3).
5. cave_skill_pick alone, then cave_skill_open and the mode 2 confirm (test 4).
6. Regression pass and the GIF.

Risks:

- **Page 2 to page 4** in the menu (section 4): the one part with no vanilla precedent.
- **Entry 38 as a sentinel**: nothing was found that reads it, but a reader that walks the table until a blank
  row would now run on into the growth table. None of the four loops does; an indirect reader is not excluded.
- **The grown sysmenupack entry**: both loaders size their buffer from the entry, so growth should be safe;
  the field loader's description reader was not traced, which is one reason the skill is hidden in the field.
- **Result words** for the capped case (section 5).
- **Auto battle**: Auto appears to choose Fight only (the remaining caller of func_02050a74, func_0205747c, is
  the field menu), so Auto never casts the skill; not confirmed by a run.
- **Enemy use**: enemy rows hold skill ids up to 37, so no enemy can roll 38. **[confirmed by the row table's
  range in docs/re-enemies.md, not rechecked here]**
- **Editions**: all of this is code and shared data, so it lands in both Classic and Retold unless the feature
  is left out of one.

## 9. Built (2026-11-12)

`src/dsde/feat_skills.py`, feature `skills` (optional; build with `--with skills`). What changed from the
plan above, and what the emulator showed (docs/status.md has the test list):

- **Special list for everyone.** Section 3 missed a gate: on the command page only Lucia and Flora (ids 1, 3)
  go to the spell list (0x020369E8 to 0x020369F4). Anyone else gets a one-spell panel when exactly one spell is
  listed and is refused otherwise, so Jian with a ring and Weapon Break would have been refused. The `bne` at
  0x020369F4 now goes to cave_skill_gate: it builds the list and opens the list page unless the list is empty
  (Jian with a ring he owns but does not wear passes the "has a spell" test and lists nothing), which is
  refused as before.
- **The cast's look (Jeff, 2026-11-12: a regular attack, then the ATK down).** cave_skill_anim wraps the party
  action setup (`bl func_02068308` at 0x020688B4): for spell 38 it puts Jian's attack file (character table +4)
  in slot 0 and points the battler's script at a cave copy of his combo, 0x02095AF0 for a front-row target and
  the leaping 0x02095560 for a back-row one, with the hit flags (0x40) removed and the last kick given
  0x02000000 and 0xFF00 in the second word: start the targets' effect scripts and wait for them, as the cast
  scripts do. Effect row 27 still supplies the banner sprite and its script.
- **Counters are left alone.** func_02068890 also sets up a party member's counterattack (mode bit 1 in r1,
  from 0x0202D6FC), and a countering battler keeps its queued command and spell, so the wrapper skips the
  override in counter mode; otherwise Jian countering with Weapon Break queued would lose his counter script
  and write his file into the attacking enemy's slot 0. Not reproduced in the emulator.
- **A pick follows the enemy.** The pick is a battler slot. When a front-row enemy dies the back-row enemy of
  that column is copied into its slot (func_02053918), and a pending pick of the old slot used to be treated
  as dead, so the cast went to the next enemy. cave_tgt_moved (feat_targeting_drop.py, hook 0x02053E4C, reached
  once per copied column) now moves the first target slot of party battlers 0 to 2 from 4 + column to
  8 + column. Reproduced and fixed in `test_skill_moved_target`; it covers Fight's pick as well.
- **In both editions** since 2026-11-12 (engine changes go in Classic and Retold; only story changes stay out
  of Classic).
- **Page 2 to page 4 works** as designed: the Special rows slide out the way they do for the ally picker and
  the grid slides in, with no stray frames (build/skills_t/t6.png). Cancel goes to the command page.
- **The capped cast says "No effect!"** (Jeff, 2026-11-12; design in docs/plan-skill-feedback.md A). The stage
  stays at -1 and the MP is spent. A third message bit (4) in battle work +0xDA makes the message line draw
  battle string 99, "No effect!" (cave_skill_msg, hook 0x020449C0 in func_02044990). cave_skill_anim knows at
  setup that the target is already lowered: it uses a copy of the cast script with no effect step, writes 0
  to work +0x74 so no effect helpers are set up (as for Fight), sets the bit, and opens the window for the usual
  60 frames (func_0204582c(0xD, 1, 0x3C)). So the line shows as the cast starts, not on the kick, and the
  round waits for it to close before the script's next step (0x0202D8A4), as with the game's own lines; cave_skill_fx
  keeps the same message as a fallback. Tried and dropped: a one-step effect script still showed the banner,
  and a -1 effect sprite entry hid it but left helper battler 14 with stale animation pointers.
- **One enemy alive:** cave_skill_open no longer fills the grid in that case. Filling it changed the menu's
  list under the open Special page and left the description window on screen, empty, for the rest of the
  battle (in the first commit of the feature). It now asks cave_tgt_after for the first and second living
  enemy instead.
- **Result words:** word 2 = -1 gives no number and no MISS, as the debuff cards do.
- **Records pointer:** in the first temple battle from the post-intro save the stat records are at 0x0228E860
  (the plans watch absolute addresses from it; `peek u32 0x020B8620` prints it).
- For the full kit: the field Magic list's stack buffer and the battle list's 30 entries are separate limits
  from the four loop bounds, and only string entries 74 to 76 duplicate 70 to 72 (73 is a distinct string).

## 10. Refused picks and the name bar (2026-11-12)

- **A pick that would do nothing is refused** (Jeff: "No effect" should block the attempt). In the grid's
  confirm path (feat_targeting_menu.py, disp_confirm) a Weapon Break on an enemy whose ATK stage is below 0
  sets the name bar's timed message the way func_02035128 does (menu +0xA0 = battle string 99, +0xA4 = 0x3C
  frames, +0x98 = 0, func_0204582c(0, 1, -1)), plays the refuse sound, and stays on the grid. With one enemy
  alive there is no grid, so cave_skill_open does the same from the Special list (r5 = 0 keeps the cursor
  corners, as the game's refusal at 0x02036B18 does). No MP is taken in either case. The message-line "No
  effect!" of section 9 remains for a target that changes after the pick.
- **The name bar lists the highlighted enemy's ailments** (Jeff: several must show at once). cave_skill_tag is
  called from func_02044c00 where a card name has been drawn (0x02044CF0; the grid labels its cells with card
  names). While the grid is up it builds "ATK" + glyph 1 (the font's down triangle) for an ATK stage below 0,
  "DEF" + glyph 1 for a DEF stage (+0x42) below 0, and three letters for status 1 to 7 (Slp, Bld, Cnf, Par,
  Sil, Psn, Stn; an enemy has one status at a time), with no spaces, and draws it so that it ends at text
  cell 0x1B, the last that shows (cells are 8 pixels, the name starts at cell 4). The longest case,
  "ATKvDEFvPsn", fits beside a 12-letter name. Other lowered stats are not listed; no skill lowers them.
- **Assembler trap:** keystone turns a conditional `bl` to a local label (`bllt tag_append`) into a branch to
  itself. Use a conditional branch around a plain `bl`. A conditional `bl` to a numeric address or a
  `${cave}` symbol assembles correctly.

## 11. The skills framework and Armor Break (2026-11-12)

The feature is now data-driven, so the rest of docs/plan-skills.md can be added as data where the kind of
effect already exists. Armor Break (Jian, level 14, 6 MP, one enemy, DEF down one stage, spell id 39, banner
row 28 = sprite 305 "DEF DOWN") is the second skill and the first to use it.

**Modules** (feature `skills`, put together in feat_skills.py):

| File | Role |
|---|---|
| skills_data.py | one frozen `Skill` per skill: spell id, name, description, MP, owner, learn level, target, kind, stat, delta, effect row, look |
| skills_common.py | shared addresses and record layouts, the text encoder, the one-instruction `hook` helper |
| feat_skills_table.py | spell table entries, the growth table move, names, descriptions, `cave_skill_levels`, `cave_skill_fx` |
| feat_skills_menu.py | list gate, listing by level, castable, the grid opener, the resolver, `cave_skill_idle` |
| feat_skills_tags.py | the name bar's ailment tags |
| feat_skills_fx.py | the stage effect, the cast's look, the "No effect!" message line |

**Room for spell ids 39 and up without moving the spell table.** The stat growth table starts right after
entry 38 (0x02094B4C). It has six 0x60-byte blocks, not five (0x240 bytes; the sixth, all "1, 999, 0", ends
at 0x02094D8C, where the next table with pool words of its own starts), and is read only as base + character
* 0x60 + field through the two pool words 0x020554F0 and 0x020555E4 (code at 0x0205541C and 0x02055514). A
copy of the 0x240 bytes is cave data (`cave_skill_growth`), the two pool words point at it, and the old bytes
are spell entries 39 to 86 (room for ids below 87). Only the entries of defined skills are written; the four
loop bounds are the spell count (40 now). mp-economy and spell-levels still edit the vanilla table in
place. The battle list's 30 entries and the field Magic list's stack buffer bound the spells one character
has, not the table; the largest planned list is under ten.

**Names.** Weapon Break keeps entry 91 of the battle string list. From id 39 the name comes from a pointer
table in the cave (`cave_skill_name`, called in place of `add r3, ip, r3` at 0x02044E7C in the name bar's
case 3; the spell id is read back from menu +0x94). That is the only place in battle that draws a spell
name: the only `add #0x35` in arm9 is at 0x02044E60, and the Special list's rows are icons. The field
Magic page reads the list through pool 0x0205C108 (entry 53 + spell) and is not hooked, because the
fighters' skills are not listed in the field (cave_skill_list answers only in battle); a healer skill that
should show there will need that reader hooked too.

**Per-spell cave tables.** `cave_skill_levels`: one row of learn level indices per fighter (Jian, Gabryel,
Rufus), 255 = not his or hers; only Jian's branch of func_02050c50 reads it so far (Gabryel's and Rufus's
branches are at 0x02050DA8 and 0x02050DC4). `cave_skill_fx`: four bytes per spell (kind, stat, delta as s8,
look), zeros for the game's own spells.

**One test for "would do nothing".** `cave_skill_idle(battler index, spell)` returns 0, or the battle string
to show ("No effect!", 99) when a stage skill's stat is already a stage past 0 in its direction (any stat 4
to 9, either direction: the stage is the s16 at record + 0x38 + 2 * stat). The effect hook, the cast-look
hook, the one-enemy refusal in the grid opener, and the grid's confirm all ask it; nothing tests for a
spell id any more.

**The grid's veto.** The targeting feature must build without skills, and a cave label can have only one
definition, so the grid does not call the skills code by name. The picker's state block got a fourth word,
STATE_VETO (+0xC): whoever opens the picker in spell mode leaves a routine there, and the grid's confirm
calls it (`blx`) with the highlighted battler and the menu's spell. A nonzero answer is the battle string
for the name bar; the pick is refused. cave_skill_open stores cave_skill_idle there.

**Checks.** Besides the assembler trap of section 10, every cave of the feature was assembled at its real
address and each branch target inspected (no branch to itself, no branch into the middle of another cave).
Cave space after this step: 14,516 bytes free.

## 12. Focus, Knockout Kick, War Breaker, Wall Breaker (2026-11-12)

Spell ids 40 to 43, all Jian's, as data in skills_data.py. Two new effect kinds and the all-target cases;
the "would do nothing" test and the refusal moved to feat_skills_idle.py, the cast look to
feat_skills_look.py.

- **Kind FLAG (Focus).** The Bealzebub card's effect flag 0x20000 makes func_0206a744 set bit 2 (value 4) of
  the first word of the battle work area and leave result word 2 = 4. The hit roll func_0205265c reads it at
  the party-attacker branch (`param_3 & 4`): every party member's physical attack hits. The word is zeroed
  with the battle context at battle start. The flag is party-wide, so Focus is cast on all allies (spell
  flags 0xC0000000): no picker, and the card's own row 37 plays ("HIT 100%" banner, sprite 319) on each. The
  effect hook ORs the flag in and writes the same result word. No self-target path was needed; a skill
  that affects only its caster (Feral) still needs one.
- **Kind STATUS (Knockout Kick).** The game's own status skills (func_020500dc, spells 31 to 37) decide
  immunity, then call func_0202d1d4(target battler, status), which queues the status in the battle work
  area (+0xE8, eight {status, battler} pairs) for the round to apply after the action, and leave result word
  3 = -2. The hook does the same after a success roll: func_02011424 (the game's random, state at 0x020A0238),
  modulo 100 through func_02015f80, against skills_data.STATUS_CHANCE (70). A failed roll shows the hit
  resolver's miss: func_0202bf9c(battler +0xD4, +0xD8, +0xDC + 0x20, 2) and sound 0x16. Sleep's length and the
  waking on damage are the engine's.
- **Immunity.** In func_020500dc an enemy whose row flags (enemy table 0x02097CE4, 0x54 per row, first word)
  have bit 31 never takes status 1, 3, 4, 5, or 7; rows 136 to 156 have the bit, all the boss rows. That is
  known before the cast, so cave_skill_idle counts it as "would do nothing" and the pick is refused, as it
  is on an enemy that already has any status.
- **All enemies (War Breaker, Wall Breaker).** Spell flags 0x40000000: no picker, the resolver fills the
  target list with every living enemy, and the effect hook runs per target. Before the game's action setup,
  cave_skill_anim takes the enemies the skill would do nothing to out of the caster's target list (packing
  the rest to the front), so no banner shows on them; if nobody is left the list stays and the message line
  says "No effect!". In the effect hook an idle target of an all-target spell is passed over silently.
- **Refusal with no picker.** The Special list's OK handler ends the command for all-enemy and all-ally
  spells at 0x02036D20. cave_skill_group sits there: cave_skill_idle_all (every living enemy idle for an
  all-enemy spell; the caster for anything else) and, if so, cave_skill_refuse, the shared "No effect!"
  refusal.
- **List paging.** The Special list shows six cells a page, filled by column (top, bottom). With seven
  entries (level 36 and the Blazing Ring worn: Inferno first, then the six skills) a "PAGE" tab appears and
  Right from the last column turns to a second page with the seventh entry; Left turns back. Eight entries
  cannot happen for Jian while only one ring can be worn.
- **Forcing the roll in a plan.** `execpoke 0x020503A0 u32 0x020A0238 N` sets the random state each time the
  effect hook site runs, so the next random number is fixed: N = 24 gives roll 3 (success), N = 15 gives 98
  (miss).

## 13. Gabryel's skills (2026-11-12)

Spell ids 44 to 50 as data in skills_data.py: Venom Claw, Blinding Swipe, Feral, Howl, and the all-enemy
Venom Storm, Blinding Gale, Dread Roar. The effect record grew to 8 bytes (skills_common.FX_*): a chance
byte and a self byte joined kind, argument, delta, and look.

- **Listing by level.** func_02050c50 branches on the character (r5) at 0x02050D08: Jian 0x02050D24,
  Gabryel 0x02050DA8, Rufus 0x02050DC4, each starting with `mov r0, #0xc`. Gabryel's own test is spell flag
  0x200 (Gale Cut) and Rufus's 0x400; neither has a level. cave_skill_list is now one routine for every
  fighter: it finds the fighter's row of cave_skill_levels from a small table by character id, compares the
  spell's learn level with the level index at 0x020B4664 + 0x5C * character, and for a spell with no level
  goes back into the fighter's own branch. Jian's and Gabryel's branches are hooked; Rufus's row exists but
  his branch is not hooked yet.
- **Castable.** func_02050a74 needs nothing for her: for any character but Jian a listed spell with the
  battle flag is castable (0x02050AF0: `cmp r6, #0; bne` to "yes"), and the MP test follows.
- **Self target (Feral).** The spell is a one-ally spell (flags 0x80000000) with the self byte set. The
  Special list's OK handler sends one-ally spells to the ally picker (`beq 0x02036D88` at 0x02036D10);
  cave_skill_self sits on that branch: for a self skill it asks cave_skill_idle about the member, refuses
  ("No effect!", the list stays) or stores the member's own battler index as the first target and ends the
  command through cave_skill_done, the shared copy of the list's ending (0x02036D20) that leaves the target
  alone. The resolver's one-ally case uses that target as it is.
- **Stage up.** The same stage step with delta +1: func_02054dec(record, 4, 1), the party recompute
  func_02054ebc, and result word 2 = 1 as the game's buffs leave it. Seen: stage 0 -> 1 and ATK 18 -> 22
  (one stage up is 125 percent), banner row 21 (sprite 298, "ATK UP").
- **No roll.** The chance byte is 100 for poison and blind: the effect hook then skips the random call
  altogether, so no random number is drawn. Howl and Dread Roar carry 70; each target of Dread Roar rolls
  for itself, since the effect hook runs per target.
- **The cast look by owner.** A skill with the ATTACK look takes its caster's attack file from the
  character table (0x020953D4 + 0x12 * character, +4) and one of eight scripts from a pointer table in the
  cave: Jian's combo copies, or for anyone else copies of the game's single attack, 0x020958C0 against the
  front row and 0x020954F0 (a leap) against the back row, with the hit step (flags 0xC0) made the step that
  starts the target's effect and waits for it. Gabryel can cast on the back row this way although her Fight
  reaches only the front (the spell grid lists every enemy).
- **The ROW look's pose.** The banner rows' caster script (0x02095294) and the generic cast (0x02094E84) play
  animations 0 and 1 of slot 0. For a card or an item slot 0 is the character's item pose file (table +0x0E);
  for a spell the game loads the Special file (+0x0C: Gale Cut's for Gabryel). For our skills with the ROW
  look the hook puts the item pose file back, so she raises her hand as she does for a card. For Jian both
  files are the same (18), so nothing changed for him.
- **What poison and blind do applied this way.** Both are queued with func_0202d1d4 like every status. Poison
  (6) showed 97 -> 93 HP on the enemy's own turn in the following round (5 percent of max HP), with no
  end; blind (2) and fear (4) show on the name bar as Bld and Par. A status poked into a record by hand
  (sleep) was cleared on the enemy's next turn because no duration came with it, so the plans only poke
  poison, which has none.
- **Refill and plans.** In this battle front slot 8 is empty at the start, so the back-row enemy of that
  column (battler 4) drops into it during the first round; Gabryel acts after the enemies. The plans aim at
  battler 9 (Down on the grid in round 1, Down then Right in round 2) so the target does not move.
- **Test party.** `party_gabryel.plan` puts character 2 alone in party slot 0 (pins of the three slot words
  and her HP), as party2_strong does for two members; her graphics load and the battle runs. Records are at
  0x0228E860 there too (battler 0 and record 0 are hers).

## 14. Rufus's orders, and the coverage plans (2026-11-12)

Spell ids 51 to 58 (skills_data.py): Rally, Stand Fast, Quick March, Stratagem (ATK, DEF, AGI, INT up one
stage on one ally) and Battle Cry, Shield Wall, Forced March, War Council (the same on every ally). All are
the STAGE kind with delta +1 and the ROW look; nothing new in the effect.

- **Listing.** Rufus's branch of func_02050c50 is at 0x02050DC4 (`mov r0, #0xc`, then his own test of spell
  flag 0x400 for Thunder Sword). It takes the shared cave_skill_list like Jian's and Gabryel's; his row of
  cave_skill_levels was already there. Castable needs nothing (any listed spell of a non-Jian character is).
  Rally and Stand Fast have level 1, so he has them when he joins at 15; the party versions have levels 36
  to 42, which he only reaches on his return (Retold). In Classic he is gone before then.
- **The ally picker's confirm path and the refusal** (feat_skills_allies.py). On page 6 a portrait pressed
  (button 8 + party slot, in r8) reaches 0x02037340, which reads the page it came from (menu + 0xC): 2 = a
  spell, `beq 0x02037398` at 0x02037348 (word 0x0A000012). The block at 0x02037398 stores the spell in the
  member's battler + 0x86, sets menu + 0x10 = 4, stores r8 - 8 as the target (+0x8C: the party slot is the
  battler index), and ends the command at 0x020373D0. cave_skill_ally sits on that `beq`: for a learned
  skill it refuses the pick when the ally is knocked out (BATTLER_ALIVE <= 0) or cave_skill_idle says the
  skill would do nothing, through the shared cave_skill_refuse ("No effect!" on the name bar, refuse sound,
  r5 = 0, the picker stays, no MP). r7 is 0 there, as the handler needs for "stay". The game's own spells go
  straight on. After the refusal's second is over the name bar shows the highlighted ally's name until the
  cursor moves, where it showed "Who to use it for?" before; left as it is.
- **Rufus can pick himself**: the picker lists every member, and a self pick works like any other.
- **All-ally skills.** cave_skill_idle_all now answers for an all-ally spell (target bits 0xC0000000) by
  asking about every living ally (battlers 0 to 2), so the list refuses Battle Cry when everyone is raised;
  the target-list pruning in the look hook runs for both all-target kinds, so an ally already raised gets no
  banner and no effect. Focus (all allies, FLAG kind) goes through the same code and behaves as before.
- **Look.** Rows 21 to 24 are the ATK, DEF, AGI, and INT UP banners (sprites 298 to 301, caster script
  0x02095294, effect script 0x02094E14). Rufus's item pose file is btldata 45 (character table row 4, +0x0E;
  2 animations, as the caster script needs).
- **Stat offsets.** func_02054ebc (party recompute) shows the effective stats in a stat record: ATK +0x24,
  DEF +0x28, +0x2C always 0, AGI +0x30, INT +0x34, DEX +0x38, LUK +0x3C; each is the base times the stage's
  multiplier (stage 1 = 125 percent: ATK 12 -> 15, DEF 13 -> 16, AGI 10 -> 12, INT 4 -> 5 for Jian at level
  1; Rufus ATK 99 -> 123).
- **Lifetime.** The stage stays to the end of the battle and the records are rebuilt for the next one:
  `test_skill_rally_next_battle` shows stage 1 through the won battle and stage 0, ATK 99, at the first
  prompt of a second battle.
- **Test party.** `party_rufus.plan`: Jian in slot 0 and Rufus (character 4) in slot 1, HP pinned, records
  at 0x0228E860 (battlers and records 0 and 1). Rufus acts before the enemies in these battles, so the
  banners show right after the pick. `party_jian_gabryel.plan` is the same with Gabryel in slot 1.
- **Coverage plans for the earlier steps** (no code change came out of them): Feral with Gabryel in slot 1
  (her first target slot, battler 1 + 0x8C at 0x0228EDA0 + 300 + 0x8C, holds 1); Dread Roar with unforced
  rolls (three of five scared, MISS on the others); Gabryel's leap at a back-row enemy that stays in the
  back row, and the no-effect variant of it; poison and blind on Sasquatch with Howl refused; Focus against
  an enemy whose AGI (record + 0x30) is pinned to 30000 (every blow misses before, lands after); a sleeping
  and a scared Ice Mongrel doing no damage for two of its turns and then attacking again.

## 15. The healers: schedules, no buffs, and Flora's water spells (2026-11-12)

- **Who owns what.** The healers' own spells stay with spell-levels (feat_spell_levels.py): its SCHEDULE now
  holds a level for each healer per spell (`None` = never), and Quick (7), Grand Weapon (8), and Grand Shell
  (9) are `None` for both, so nobody learns them. Nothing else reaches those three: items and cards go
  through the medicine effect table, not spell ids; Auto gives every member Attack (func_02050f1c); enemy
  rows hold skill ids 16 to 37 only. This also ends the stacking of a healer's buff on top of one of Rufus's
  orders (the game's own buff adds a stage with no one-stage cap).
- **How a healer learns a skill.** func_02050c50 lists a spell for Lucia (0x02050CA8) or Flora (0x02050CDC)
  when her level index reaches her byte of the spell's own table entry (+8 Lucia, +9 Flora); there is no
  flag or id test, which is why the enemy skills carry 0xFF in both bytes. A healer's skill therefore needs
  no hook: feat_skills_table.py writes the owner's learn level into her byte and 0xFF into the other's, and
  the fighters' rows of cave_skill_levels do not know the skill. Castable is automatic for anyone but Jian.
- **The field Magic page lists no skill.** Its loop (func_02064ff0, bound at 0x02065068) keeps the original
  0x26, so ids from 38 are never asked about there. Every skill is battle-only, the page reads names from the
  string list (no entries from id 39) and has a buffer sized for the original count. `test_skill_flora_field`:
  five rows at level 28, as before. (The fighters were already hidden there by cave_skill_list.)
- **A skill's own effect sprite.** The effect record's last two bytes (FX_SPRITE, u16) name a btldata entry
  that cave_skill_anim writes into the effect sprite slot (battle work +0x54) after the game's setup, in
  place of the effect row's sprite; 0 keeps the row's. The row's effect script then plays it. Water Bind and
  Binding Rain use row 34 (the status row: generic cast 0x02094E84, effect script 0x02094E24, one step that
  plays animation 0 and applies the effect) with sprite 313, the water ribbon nothing in the game loads, which
  has exactly one animation. No effect row was added and no script written.
- **The SPELL look.** Row 34's caster script is the generic cast, written for a character's Special file
  (two animations: raise, hold), which is what the game's setup loads for a spell. Look.SPELL leaves that
  alone, so Flora casts as she casts Healing Water; Look.ROW (item pose in slot 0) stays for the fighters.
- **Battle list.** By spell id: Healing Water, Tender Rain, Cure Squall, Divine Rain, Miracle Tears, Water
  Bind, Binding Rain (Escape is field-only), so Flora has at most seven entries, six to a page. The list's
  icon for a skill is the plain tile every id from 38 gets.
- **Auto** cannot cast them (it only Fights). The refusals are the framework's: an enemy with any status or
  a boss row is refused in the grid, Binding Rain at the list when every living enemy would be skipped, and
  the game's own "Not enough MP!" when the pool is short.
- **Plans and MP.** Pinning battle MP above a healer's max shows it snapping back to the max, so the Flora
  plans either leave MP alone (18 at level 1 stats) or pin the field MP and max MP (0x020B4784, +4) to 60
  before the battle; spending then persists in the battle record. A member whose field HP is held at 0
  starts the battle knocked out (`test_skill_miracle_tears`).
- `test_spell_levels_1/5/12` were rewritten for the new schedule with steadier key timing; `_5` now shows
  two entries (Healing Water, Cure Squall) where the pre-skills baseline in build/regress/dsde_* shows three
  (with Quick), by design.
- The skill lists are split by owner since this step: skills_types.py (the `Skill` type, kinds, looks, rows),
  skills_jian.py, skills_gabryel.py, skills_rufus.py, skills_flora.py, and skills_data.py, which gathers and
  checks them (ids with no gaps, descriptions of 30 characters at most).

## 16. Stone Throw (2026-11-18)

Jian, level 4, 3 MP, one enemy in either row, spell id 61 (the ids run in the order the skills were made, so
SKILLS is sorted by id rather than gathered by owner). Kind.HIT, Look.THROW.

- **The cast.** Flora's attack is the model (func_02068308 case 1, character 3): slot 0 her bow file, slot 2
  the arrow (btldata 10), work +0x74 = 1, every target slot's effect script 0x02094EE4. Effect mode 1 is the
  projectile mode: as each effect starts, func_02067e6c puts a helper battler (14 + slot) at the caster,
  copying its stat record index, targets, and +0x2E / +0x8A, and the helper runs the effect script: one
  16-frame step to the first target (0x00202812), then the hit step (0x80000041). Look.THROW sets the same
  after the game's Special setup, with Jian's unused throw (btldata 15) in slot 0 and a two-step caster
  script: animation 0 (he tosses the stone up and catches it, 12 frames of cells) and animation 1 (the
  swing), which starts the effects and waits for them. No run-in step and no 0x200000 position step, so he
  stays where he stands.
- **Damage.** The hit step (step flag 0x40) goes to func_02030b44 whatever the command: the hit roll
  func_0205265c (attacker's DEX against the target's AGI; the battle's sure-hit flag, Focus, makes it
  certain), then func_0205212c, the ordinary physical damage, from the attacker's record, which is Jian's.
  The spell effect step (0x400000) is not in the script, so cave_skill_effect never runs for it; Kind.HIT
  is skipped there anyway and never refused by cave_skill_idle. MP is charged by the Special path as for
  every skill.
- **The stone.** In btldata 15 the stone over his head is a piece of its own (piece 4, 16 x 16, tile unit
  49; cells 4 and 5 reuse it). The arrow file is one animation, one frame, one cell of one 16 x 16 piece,
  so the stone's file is the arrow's with those 128 bytes of tiles and the throw's 16-color palette in place
  of its own (feat_skills_stone.py). It replaces btldata 17 (in no table). DataPatch gained `whole`: the
  entry becomes the new bytes at their own size (244 bytes for 10,464); the default stays "write `new` at
  the offset", which the script inserts rely on.
- **MCE frames** (worked out here): animation records are u32 first frame, u32 0x1000, u32 frame count;
  frame records 0x18 bytes: u16 cell, u16 duration, s32 -1, u32 x scale 0x1000, u32 y scale 0x1000, two
  zero words.
- **Seen** (`test_skill_stone_throw`, `test_skill_stone_throw_hit`, first temple battle, Jian alone at
  level 4): Special lists Stone Throw alone ("Throw a stone at one monster", 3 MP); the grid picks the
  second back-row flyer; Jian tosses and swings where he stands while the camera follows the stone to it;
  MP 50 -> 47. Without help the stone missed (MISS); with the sure-hit flag set, 148 and the flyer falls
  (build/stone_hit/stone_throw.gif). Not seen: a front-row target, a target that dies before Jian acts,
  Jian's other skills' casts after this change (their path is unchanged code).

## 17. Spell lists in learn order (2026-11-18)

Jeff: every list shows its spells in the order they are learned, and learning a new one (an all-target
version included) does not reorder what is there. feat_skills_order.py sorts both lists after the game builds
them, with one stable insertion sort (cave_skill_sort) keyed by the level the member learns each spell at:

- **Battle Special list:** func_02035e00 case 2 writes halfword ids at menu 0x020B8800 + 0x44 and sets
  +0x82 to 1 (0 for the item and card lists); its shared exit loads the menu at 0x02035F6C with the count in
  r7. That load is the hook; the member is the battler at menu + 0x34, character id at battler + 4.
- **Field Magic page:** func_02064ff0 keeps 8-byte entries on its stack (r5) and the count in r7; the load
  after its loop (0x02065070) is the hook. Its sb is the **party slot**, not the character: the character is
  the s16 at 0x020B464C + slot * 4, as in func_02050c50's field branch.
- **Keys:** a healer's byte of the spell's table entry (+8 Lucia, +9 Flora: the spell-levels schedule and
  her own skills); a fighter's row of cave_skill_order (his or her skills' level indices, 0 for Gale Cut and
  Thunder Sword, which they have on joining, 254 for anything else, which for Jian is Dragon Magic from the
  rings, so ring spells come last). Ties keep id order (Thunder Sword before Rally and Stand Fast).
- **Plans.** The list cursor is a grid of columns of two, three columns a page; Down moves one entry, Right
  two, and Right from the last column turns the page. Stone Throw first shifts each of Jian's skills one
  entry, so his plans gained a press; Flora's Miracle Tears moved from the fifth entry to the seventh.

