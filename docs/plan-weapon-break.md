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
- **Known limit:** the pick is a battler slot. When a front-row enemy dies the back-row enemy of that column
  moves into its slot (0x02053DE8), and a pending pick of the old slot is then treated as dead, so the cast
  goes to the next enemy. Fight on a back-row enemy has the same limit; the fix is to remap pending targets
  in the refill.
- **Page 2 to page 4 works** as designed: the Special rows slide out the way they do for the ally picker and
  the grid slides in, with no stray frames (build/skills_t/t6.png). Cancel goes to the command page.
- **The capped cast** still plays the banner and costs MP; the stage stays at -1 and nothing else shows.
- **Result words:** word 2 = -1 gives no number and no MISS, as the debuff cards do.
- **Records pointer:** in the first temple battle from the post-intro save the stat records are at 0x0228E860
  (the plans watch absolute addresses from it; `peek u32 0x020B8620` prints it).
- For the full kit: the field Magic list's stack buffer and the battle list's 30 entries are separate limits
  from the four loop bounds, and only string entries 74 to 76 duplicate 70 to 72 (73 is a distinct string).
