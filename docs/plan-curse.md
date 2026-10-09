# The curse rework: items do not heal Jian, magic heals him at half (feature `curse-no-healing`, 2026-10-09)

Design (Jeff, docs/plan-two-editions.md "The curse in both editions", revised the same day): while cursed, Jian
keeps his 3-hit combo (`no-curse-penalty` stays on). Healing **items** do nothing to him. Lucia's healing
**magic** works on him at a reduced rate, `CURSE_HEAL_PERCENT` (default 50; Jeff's range 25 to 50; the unspoken
reason is that it is Althena's power, dampened). Statues heal him fully. The curse breaks on round 3 of the
Zethos fight exactly as in vanilla. No wording changes. Every number is marked **measured** (seen in the
emulator or read in the ROM) or **estimated**.

## 1. What the feature does

Code: `src/dsde/feat_curse_healing.py` (`curse_no_healing(percent)` builds the feature; `CURSE_NO_HEALING` is
the shipped one at `CURSE_HEAL_PERCENT = 50`). Four one-instruction hooks into ITCM caves (428 bytes).
Background on the curse flag: docs/re-curse-battle-speed.md part 1.

**Cursed** means, in battle, the battle's own flag (ctx 0x020B85B8 + 0x5C, set at battle start from the story
flags and cleared by Zethos's skill 21), and in the field, story flag 0x33 set and 0x79 clear (flag words behind
the pointer at 0x020B4640). The battle flag is read live, so full healing returns the moment Zethos lifts the
curse, before 0x79 is set after the fight.

| Where | Hook (vanilla instruction replaced) | Effect on cursed Jian | Item or MP |
|---|---|---|---|
| Field menu, Healing Gum / Healing Drop | 0x020636F4 `cmp r2, r0` in func_020635cc (the "HP already full" test) | refused like a full-HP target | **not used up** |
| Field menu, all-allies HP card (0xEB) | 0x020638F8 `bl func_0206a8b8` | HP restored after the effect | used up as vanilla |
| Battle, any HP item (func_0206a2f8) | 0x0206A630 `bl func_0206a8b8` | HP restored after the effect; no number shows | single-target item **put back in the bag** (the battle takes it out when the turn starts, func_020514ec); all-allies cards not refunded |
| Healing Water and Tender Rain, field and battle | 0x020509D0 `ldr r0, [sp, #0x14]` in func_02050850 (the spell heal amount, before the max-HP cap) | amount * CURSE_HEAL_PERCENT / 100, rounded down, at least 1 if the amount was not 0 | targets him and costs MP as usual |

Which paths reach the spell hook: func_02050850 computes only the INT-based heals (spell flags 0x10, Healing
Water; 0x20, Tender Rain). Items never call it (they use func_0206a8b8 via the two item hooks). Revives do not:
Miracle Tears (flags 0x80000006) sets 10% in func_020500dc's flag-4 branch, and Angel's Tears is an item.
Divine Rain (0xC0000802) has neither heal flag, so func_02050850 returns 0 for it and the hook leaves it alone.
Zethos's skill 21 is not a heal. Vanilla quirk kept: in the field func_02050850 adds the amount itself and
func_02063a94 adds it again (capped), so field Healing Water and Tender Rain heal twice the battle amount; the
hook scales before both adds, so the curse halves the field heal too.

Decisions:

- **Item not consumed, with the vanilla feedback.** The engine has no "no effect" message. Its own refusal for a
  full-HP target (field menu: the cursor stays on the target and nothing is used) is the closest thing, and the
  field hook reuses it. Vanilla checked: Healing Gum on a full-HP Jian on the vanilla ROM keeps the Gum (5 -> 5)
  and stays on the target screen (`curse_field_items_vanilla_full`), the same as our cursed refusal. Sound not
  checked. In battle the item's animation plays and no number appears; the item comes back.
- **MP items still work on Jian** (his MP only feeds the Dragon Magic rings). **Revives still work** (10%).
  **Status cures still work.** Statues are untouched (they set HP to max in the field loop).
- Not handled (none seen in this stretch): HP regeneration from gear (none found: the Refresh and other rings
  feed the status-resistance table in func_0206ab6c). Level-ups rescale current HP to the new maximum (measured:
  93 -> 97 at Jian's level 11), as vanilla.

**Composition with `no-curse-penalty`:** they compose; both are on in both editions (features.py, ef19fc7).
This feature does not touch Jian's attack checks.

## 2. Tests (build/curse/dsde.nds = the default edition, which includes the feature at 50; screenshots in build/curse/)

Built with `uv run python -m dsde.patches --output build/curse/dsde.nds`; the 25% ROM with the scratch
`build/curse/build_pct.py 25 build/curse/g25.nds`. Plans in emu/plans/curse_*.plan, run with `--save` (the
post-intro save, flag 0x33 poked into the flag word 0x02204624). Results of the second round of tests (v2_*):

| Test | Plan | Result (measured) | Shots |
|---|---|---|---|
| Field, Healing Gum on cursed Jian, then Lucia | curse_field_items | Jian 5 -> 5 HP, Gums 5 -> 5; Lucia 5 -> 11, Gums 5 -> 4 | v2_field_items/strip.png |
| Same, no curse flag / 0x79 also set | curse_field_items_uncursed, _lifted | Jian 5 -> 13, Gums 5 -> 4 | v2_field_items_uncursed/, v2_field_items_lifted/ |
| Vanilla ROM: Gum on full-HP Jian | curse_field_items_vanilla_full (on build/curse/vcurse.nds) | Gums 5 -> 5, same screen as ours | field_items_vanilla/ |
| Field, Healing Water on cursed Jian (5 of 999 HP), then Lucia | curse_field_spell | Jian 5 -> 29 (+24), MP 18 -> 14; Lucia 5 -> 21, MP -> 10 | v2_field_spell/strip.png |
| Same, uncursed / lifted (same rolls) | curse_field_spell_uncursed, _lifted | Jian 5 -> 53 (+48), MP 18 -> 14 | v2_field_spell_uncursed/, v2_field_spell_lifted/ |
| Field, Tender Rain (Lucia 10), all at 20 HP, Jian max 999 | curse_field_tender | Jian 20 -> 66 (+46), Lucia 20 -> 74 and Gabryel 20 -> 55 (full), MP 43 -> 37 | v2_field_tender/strip.png |
| Same, uncursed | curse_field_tender_uncursed | Jian 20 -> 114 (+94), the others the same | v2_field_tender_uncursed/ |
| Statue, cursed | curse_statue | Jian 5 -> 28 HP, 1 -> 10 MP | v2_statue/st_after.png |
| Battle, cursed: Gum on Jian, Healing Water on Jian; next round Gum and Healing Water on Lucia | curse_battle | Gum: Jian 100 -> 100, Gums 5 -> 4 -> 5 (taken at turn start, returned); Water: Jian 100 -> 109 (+9), MP 300 -> 296; round 2 Lucia +299 (Gum), +19 (Water), Gums 5 -> 4 | v2_battle/strip.png |
| Battle, uncursed (same rolls) | curse_battle_uncursed | Gum 100 -> 399, Water 399 -> 417 (+18), Gums 5 -> 4 | v2_battle_uncursed/ |
| Zethos (event battle 6, Jian alone, forced from Delrich Temple) | curse_zethos | Gum on Jian in rounds 1, 2, 3: taken and returned, HP 399 stays; the curse flag clears in round 3 (frame 8281, after Jian's turn); round 4 Gum 399 -> 698, round 5 696 -> 995 | v2_zethos/strip.png |

The Zethos fight was forced (not reached by story), so its pre- and post-fight scripts and the vanilla
"The Curse of Lost Equilibrium has been broken!" line were not seen; the feature does not touch scripts.

## 3. Viability study: the cursed stretch on Fast with the hack's rules

### 3.1 The route

From the end of the San Coliseum (flag 0x33, script 005 0x3E3C) to the Zethos fight (0x79 after it). Map ids,
scripts, and groups: docs/re-curse-battle-speed.md 1.3, docs/re-enemies.md. Map contents **measured** by pin-warping
to every map with the flag on and dumping the object table (`curse_route_maps`, `curse_route_cathedral`;
build/curse/parse_route.py; shots build/curse/route*/).

| Place | Maps | Statues | Encounters | Chests | Notes |
|---|---|---|---|---|---|
| Healriz, San Coliseum aftermath | 176 to 198 | map 185 | none (town) | | inn: none in the game |
| Port Olbeage | 199 to 212 | map 208 | none (town) | | best gear before the Cathedral sold here |
| Overworld to the Cathedral | world map | | none found | | **uncertain**: no field map between Olbeage and the Cathedral was found in the map table range |
| Cathedral of Althena | 140 to 150 (area group 18, enemy level from 10, up to 30 by the clamp) | map 145, the main hall (152, 200) | map 141 (the long hall): 8 spawn points, 5 symbols (5 to 7 per map); other maps **unknown** (146 to 149 did not load by warp) | maps 144 and 145 one chest each, **not blue**; no blue chest found | four Deuces (towers either side) and Gronk; the LP (lparchive Update 05) also says "there's no blue chests" and the player "running back to the statue all the time" |
| Capture, Leephon, Zethos Castle | 213 to 225 | map 222 | none (towns) | | saving disabled after Gronk until Zethos; Zethos is Jian alone |

Regular encounters on the whole stretch are therefore the Cathedral's (group 18: Comet, Phantom, Enigma, Ghoula,
Thanatos, Asmodee, Duager, Druid). Its one statue is in the main hall between the two towers, so every Deuce
trip starts and ends next to it.

### 3.2 Jian's level and HP

- **Estimated** level at the curse: 9 to 11. Jeff's save is level 5 in Thieves' Woods; with one-battle-mode
  every win pays EXP, and `boss-exp` makes each Coliseum boss pay a pool of about 653, doubled to about 1306 EXP
  for Jian (docs/boss-exp.md), so the three Coliseum fights alone add about 3900 (level 10 needs 6100).
- **Measured** from the ROM's growth table: max HP 97 at level 8, 117 at 10, 136 at 12, 156 at 14. Lucia 74 at
  10, Gabryel 30 at 1 (joins at level 1), 63 at 5.
- Gabryel catches up fast: from level 4 she reached level 7 in five Cathedral fights (**measured**).

### 3.3 What a fight costs (measured)

Party Jian 10, Lucia 10, Gabryel 4 with the best Port Olbeage gear (curse_party_l10.plan), cursed, warped into
the Cathedral hall and put onto its five enemy symbols in turn, battles on Auto (`curse_cathedral_fights`):

| Fight | Enemies | Jian HP after (of 117, then 136 at level 11) |
|---|---|---|
| 1 | Comet x2, Enigma, Druid | 117 -> 96 (-21) |
| 2 | Asmodee, Thanatos x3 | 96 -> 93 (-3) |
| 3 | Phantom x2, Enigma, Thanatos x3 | 93 -> 97 (level-up rescale; no damage) |
| 4 | Enigma x2, Ghoula | 97 -> 97 |
| 5 | Enigma x2, Thanatos x2 | 97 -> 95 (-2) |

Five fights cost Jian 26 HP in all, 21 of it in one fight (the Comets' and Druid's magic); Lucia and Gabryel took
about as much and could heal each other. The hall cleared in five fights. (Measured under the first rule, when
magic did not heal Jian either; with magic at 50% these are an upper bound.)

Bosses, forced from the hall, from full HP, Gronk at level index 10 (975 HP) in every run:

- **Deuce** (event battle 4, `curse_boss_4`, everyone on Fight): won in 4 rounds; Jian took no damage (one run).
- **Gronk** (event battle 5), three ways (measured; Jian 117 HP, Lucia 74, Gabryel 55):

| Run | Lucia | Jian's HP, round by round | Outcome |
|---|---|---|---|
| `curse_boss_5`, first rule (no heal on Jian) | Fight | 117 -> 78 -> 38 -> 0 by round 3 | party wiped in 3 rounds, Gronk barely scratched |
| `curse_gronk_heal` at **50%** | Healing Water on Jian every round | Gronk's party spell (about 38 to Jian, every other round) then Lucia's heal: 85 -> 117 (+32, capped), 79 -> 114 (+35) -> 117 | Jian stays topped up while Lucia lives; Gabryel petrified round 1 and died round 4, Lucia (never healed) died round 6; Jian alone took Gronk to **42 HP** and fell in round 11 |
| same at **25%** | same | 85 -> 102 (+17) -> 117, 79 -> 96 (+17) -> 115, then 76 -> 36 -> 0 | Lucia died round 6, Jian round 8, Gronk at 249 HP |

Shots: build/curse/gronk50/strip.png, build/curse/gronk25/strip.png (inputs each round); earlier wipe:
build/curse/boss5/s.png.

**Can Lucia keep him up?** At 50%, yes: one Healing Water (about 33 at Lucia's level 10, INT 49) undoes one of
Gronk's party spells on Jian, and the spell comes every other round, so she has every other turn free for
herself or Gabryel. At 25% she heals about 17, half a spell, so keeping Jian up takes her every turn and nothing
is left for the other two. In both runs the loss came from Lucia and Gabryel going unhealed (the scripted Lucia
only ever healed Jian), not from the curse; Tender Rain (full on the others, half on Jian) is the better play and
was not scripted.

### 3.4 Fights between statues (estimated from 3.3)

On Fast with kill-on-hit, regular fights are short and cost Jian about 5 HP on average and up to about 21. With
117 to 136 HP that is about 5 fights in the worst case and 20 or more on average without any healing, and Lucia's
magic now tops him up at half rate in between (a field Healing Water healed him +24 at Lucia's level 1,
measured; about 60 to 85 at level 10 with the field double-add, estimated). The Cathedral's statue is central, so the hall-to-tower trips are short.
Running from a fight costs nothing and the maps restock on entry.

### 3.5 Verdict

**Viable at 50%; tight but workable at 25%.**

- Regular encounters: fine. The statue is in the middle of the only dungeon, there are no blue chests in the
  Cathedral (so no return trips for chests), and the towns at both ends have statues.
- Deuces: fine from a statue (one walk back between towers, which the LP's vanilla player already does).
- **Gronk** is still the hardest fight of the stretch, but the curse is no longer what decides it: at 50% one
  Healing Water per Gronk spell keeps Jian up; at 25% it costs Lucia every turn. Gronk's fight level can roll
  between 10 and 30 (area clamp, docs/re-enemies.md); these runs rolled 10. Items still do nothing on Jian, so
  the curse stays felt: Healing Gums and Drops are for the other two, and Lucia's MP becomes Jian's lifeline.
- Zethos: no pinch. Jian is alone, the HP floor and the round-3 lift are vanilla, and from round 3 items heal
  him fully again (measured).

### 3.6 Tuning knobs that remain (in order of cost)

1. **`CURSE_HEAL_PERCENT`** (feat_curse_healing.py; 50 ships, 25 measured above). Anything from 1 to 100 works;
   a heal that was not 0 never rounds below 1.
2. **Items at a fraction too** instead of 0 (the two item caves restore the old HP; they could restore part of
   the gain instead). Would soften the field between statues; Jeff chose 0.
3. **The curse yields in boss fights**: skip the block when the battle is an event battle (ctx +0x06 boss type
   non-zero).
4. **A statue nearer the towers or before Gronk's room**: a map object change (DataPatch); needs the Cathedral's
   map data located.
5. **Revive at more than 10%** for cursed Jian, or a cheaper revive item in the Olbeage shop.
6. Lower Gronk's level clamp (area_min override for battle 5) so the fight does not roll up to 30.

Open (needs a playtest): the real levels at Gronk on this hack, the Cathedral towers' encounters (maps 146 to
149), Gronk with Tender Rain played well, and whether the item refusal sound is the vanilla buzzer.
