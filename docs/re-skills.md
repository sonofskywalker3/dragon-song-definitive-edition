# Player skills, their animations, and unused battle assets (reverse engineering notes)

Static analysis of the vanilla USA ARM9 and btldata.dat (2026-11-12). Nothing here was run in the emulator;
"unused" means "no table or loader found that reaches it", and each candidate needs one forced load in a battle
before anything is built on it. Sheets of every file named here: `build/re_skills/` (renderer:
`build/re_skills/render_mce.py <out dir> <btldata entry> ...`, needs pillow).

## 1. The skill list is one table, and it is full

Spell table 0x02094978, 0x26 entries of 0xC bytes (format: docs/re-mp-jobs-rings.md 1.1; the u16 at +0x0A is
the **effect row**, section 2). The loops that list and cast (func_02050e74, func_02050ec8) stop at 0x26.

| Entries | What | Who |
|---|---|---|
| 0 | blank | |
| 1 to 9 | Healing Water, Tender Rain, Cure Squall, Divine Rain, Miracle Tears, Escape, Quick, Grand Weapon, Grand Shell | Lucia (id 1) by level byte +8, Flora (id 3) by level byte +9 |
| 10 to 13 | Inferno, Loud Call, Wind Cutter, Lunar Quake | Jian (id 0), ring flags 0x100000 to 0x800000 |
| 14 | Gale Cut | Gabryel (id 2), flag 0x200 |
| 15 | Thunder Sword | Rufus (id 4), flag 0x400 |
| 16 to 37 | enemy skills; every one is used by at least one enemy row | enemies |

So Jian has four (one animation, section 3), Gabryel one, Rufus one, and only the two healers have a list.
There is **no spare entry**: 0 is the blank, and index 38 onward is other data. The name list at 0x020A4480
has exactly the 15 player names, none extra. Who may learn what is hard-coded per character in func_02050c50
(level bytes exist only for Lucia and Flora; Gabryel and Rufus are flag tests with no level).

## 2. Skill to animation

Effect table **0x02096180**, 49 rows of 0x10 (row 49 is the terminator):
`u16 0, u16 slot count (2 or 3), s32 effect sprite (btldata entry, -1 none), u32 caster script, u32 per-target
effect script`. Read by func_02068034 (enemies) and func_02068308 (party; items go through
func_0206aa3c: item table 0x0209B06A -> medicine table 0x0209D124, u16 at +0x0A = row).

For a party cast (func_02068308 case 2) the three animation slots (battle work +0x50, +0x52, +0x54, loaded
from btldata by entry number around 0x0202E1xx) are: the caster's special file (character table 0x020953D4 +
0x12 * id, +0x0C), the caster's move file (+0x02), and the row's effect sprite. Jian is the exception: skills
10 to 13 put btldata 0x13, 0x15, 0x14, 0x16 in slot 0 instead. A script step is 16 bytes: flags, u16 0 / u16
sound at +6, s16 slot at +8, s16 animation index inside that slot's file at +0xA, s16 frames at +0xC.

Every one of the 49 rows is used:

| Rows | Effect sprite (btldata) | Used by |
|---|---|---|
| 0 | 158 sparkle trail | Healing Water, Escape, most medicines |
| 1 to 4 | 224 burst, 225 ground geyser, 226 flame column, 227 boulder that shatters (one-color silhouettes, tinted at run time) | enemy skills 16 to 19 and their all-target twins 26 to 29 |
| 5 | 318 purple demon slash | Gideon 2 (skill 20) |
| 6 | 228 star swirl | Zethos (skill 21) |
| 7 to 10 | none (Jian's own files 19 to 22) | Dragon Magic |
| 11, 12 | none (in the character's special file 34 / 44) | Gale Cut, Thunder Sword |
| 13 | none | two cards (items 233, 235) |
| 14, 15 | 158, 322 blue star shower | Tender Rain, Divine Rain |
| 16 | none (breath is in the sprite) | Red Dragon (22) |
| 17, 20 | 315 ice crystals | White Dragon (23), Gideon 3 (30) |
| 18 | 317 rolling boulder | Black Dragon (24) |
| 19 | 316 dead-tree spikes | Black Dragon (25) |
| 21 to 33 | 298 to 310 "ATK UP" style banners with streaks | Grand Weapon / Shell / Quick, buff cards |
| 34, 39 to 45 | 314 green rings | status skills 31 to 37, status cards |
| 35 to 37 | 312 silver medallion, 319 / 320 banners | cards |
| 38 | 311 gold ring with rising light | Miracle Tears, revive items |
| 46 | 321 white flash | Cure Squall |
| 47, 48 | 323, 324 ring of blue dots | two cards |

## 3. What is unused

**Found by data (no table entry, no constant loader):**

| btldata | What it is | Notes |
|---|---|---|
| **313 (0x139)** | blue water ribbon that coils and splashes, 8 cells, 68 x 72, one animation | sits between two used effect sprites (0x138, 0x13A); no effect row names it. The only orphaned spell effect. |
| **15** | Jian: tosses something up, then a rising slash with a long arc, 16 cells, 64 x 116, 2 animations | character table column +8. Only Flora's +8 is ever read (her bow), so Jian's is never loaded. |
| **33** | Gabryel: leap and double claw with white arcs, 13 cells, 2 animations | same column +8. Close to her normal attack (file 32, red streaks), so less new than it sounds. |
| 26 | the same Gabryel animation in an orange palette, in Lucia's +8 column | placeholder |
| 16 | Jian standing, 2 cells, 8-bit color | column +0xA, never read for anyone |
| 17, 29 | Lucia idle and turn, 8 cells each (4-bit and 8-bit copies) | in no table at all |
| 157 | four 16 x 16 icons (sword, armor, ring, hat) | in no table |

**Not unused, but worth knowing:** Jian's four Dragon Magic files (19 to 22) are the same 15 cells and 6
animations with different palettes and one shared script (0x02095EC0). That is the "same spell four times"
complaint.

**Second tier, never seen from the party's side** (effect sprites are not tied to the caster, so a party
skill can point at them): 315 ice crystals, 316 dead-tree spikes, 317 boulder, 318 demon slash, 228 star
swirl, and the four tinted element effects 224 to 227.

**Not found:** cut skill entries, spare effect rows, extra skill names. Not checked: sound effects with no
caller, description text in the archives, Japanese leftovers, animations inside the 10-animation idle files.
The Cutting Room Floor page for the game is a stub that lists unused areas only.

## 4. What a new learnable skill takes

1. **A table entry.** None is free, so either move the spell table (and every pointer to it: the literal
   pools of func_02050094 / 020500ac / 020500c4 / 02050a74 / 02050c50, the +0x0A reads at 0x02094982, and
   the two 0x26 loop bounds), or take over an entry. A new entry also needs the name list (15 names, in
   table order) extended, and a description wherever the menu reads one (not located).
2. **Who learns it and when.** Lucia and Flora: the two level bytes. Jian, Gabryel, Rufus: func_02050c50
   needs a new test (a level compare like the healers', or a story flag).
3. **An effect row.** The table is full and is followed by other data, so a new row means moving that table
   too (pointers at 0x020682F0..FC and 0x02068880..8C), unless the new skill reuses a row.
4. **The animation.** Lowest cost first:
   - an existing row with the generic cast script 0x02094E84 (rows 1 to 4, 19, 34 to 48): data only; the
     caster plays its own special file while the effect runs on each target. Fits the healers, whose
     special files are cast poses; Jian, Gabryel and Rufus have attack-style special files and need their
     own script.
   - a row with no effect sprite and a physical script (as Gale Cut): a new script plus a sprite file in
     slot 0. This is how btldata 15 (Jian) or 33 (Gabryel) would come back; the slot-0 override that
     Dragon Magic uses (func_02068308, skills 10 to 13) is the place to add it.
   - effect 313 needs a row and an effect script; the heal script 0x02094EA4 (two steps) is the model.
5. **Damage.** What the enemy skill flags (0x1000 to 0x8000 elements, 0x20000) do when a party member is
   the caster is not traced.

## 5. Forced in a battle (2026-11-12)

Both main candidates load and play in the emulator, by memory pokes only (no patch code yet):

- **btldata 15 (Jian):** vanilla ROM, Jian's attack-file columns (0x020953D8, 0x020953DA) pinned to 15 and
  his attack scripts (0x02095AF0, 0x020958C0) overwritten with a ten-step copy of the single attack: run in,
  slot 0 animation 0 (the toss), slot 0 animation 1 with the hit flags 0xC1 (the flip kick with the arc), run
  back. Against a forced Ice Mongrel the kick lands and the damage number shows on the kick frame.
- **btldata 313 (water ribbon):** effect row 0's sprite (0x02096184) poked from 158 to 313 and the heal effect
  script's second step (0x02094EBE) set to animation 0, since the file has only one. Lucia's Healing Water
  then coils the ribbon around the target and the heal applies as usual.

GIFs: build/force_anims/jian_unused_attack.gif and water_unused_effect.gif (build/ is not committed).
