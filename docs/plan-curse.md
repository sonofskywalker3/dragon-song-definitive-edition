# The curse rework: only statues heal Jian (feature `curse-no-healing`, 2026-10-09)

Design (Jeff, docs/plan-two-editions.md "The curse in both editions"): while cursed, Jian keeps his 3-hit combo
(`no-curse-penalty` stays on) but nothing heals him except the Goddess's statues. The curse breaks on round 3 of
the Zethos fight exactly as in vanilla. No wording changes. This doc records the hooks, the tests, and the
viability study. Every number is marked **measured** (seen in the emulator or read in the ROM) or **estimated**.

## 1. What the feature does

Code: `src/dsde/feat_curse_healing.py`. Six one-instruction hooks into ITCM caves (about 480 bytes). Background on
the curse flag: docs/re-curse-battle-speed.md part 1.

**Cursed** means, in battle, the battle's own flag (ctx 0x020B85B8 + 0x5C, set at battle start from the story
flags and cleared by Zethos's skill 21), and in the field, story flag 0x33 set and 0x79 clear (flag words behind
the pointer at 0x020B4640). The battle flag is read live, so healing works again the moment Zethos lifts the
curse, before 0x79 is set after the fight.

| Where | Hook (vanilla instruction replaced) | Effect on cursed Jian | Item or MP |
|---|---|---|---|
| Field menu, Healing Gum / Healing Drop | 0x020636F4 `cmp r2, r0` in func_020635cc (the "HP already full" test) | refused like a full-HP target | **not used up** |
| Field menu, Healing Water | 0x02063AFC `cmp r1, r0` in func_02063a94 (same full-HP test) | refused | **no MP spent** |
| Field menu, Tender Rain | 0x02063BC0 `cmp r1, r0` (per-member full-HP test) | skipped; the others heal; refused if only Jian was hurt | MP as vanilla |
| Field menu, all-allies HP card (0xEB) | 0x020638F8 `bl func_0206a8b8` | HP restored after the effect | used up as vanilla |
| Battle, any HP item (func_0206a2f8) | 0x0206A630 `bl func_0206a8b8` | HP restored after the effect; no number shows | single-target item **put back in the bag** (the battle takes it out when the turn starts, func_020514ec); all-allies cards not refunded |
| Battle (and field), healing spells | 0x020509D0 `ldr r0, [sp, #0x14]` in func_02050850 (the heal amount) | amount 0; no number shows | MP and turn spent |

Decisions:

- **Item not consumed, with the vanilla feedback.** The engine has no "no effect" message. Its own refusal for a
  full-HP target (field menu: the cursor stays on the target and nothing is used) is the closest thing, and the
  field hooks reuse it. Vanilla checked: Healing Gum on a full-HP Jian on the vanilla ROM keeps the Gum (5 -> 5)
  and stays on the target screen (`curse_field_items_vanilla_full`), the same as our cursed refusal. Sound not
  checked. In battle the item's animation plays and no number appears; the item comes back.
- **MP items still work on Jian** (Mental Gum, Mental Drop, the MP cards). The curse is about healing; his MP
  only feeds the Dragon Magic rings.
- **Revives still work** (Angel's Tears, Miracle Tears, the 10% revive): a knocked-out Jian comes back at 10%,
  so a KO never strands him until the next statue. The hooks only undo an HP rise from above 0.
- **Status cures still work.** Statues are untouched (they set HP to max in the field loop).
- **Healing spells cost MP in battle.** Refunding MP would need another hook in the turn start; the player chose
  the target. In the field the full-HP refusal already spends nothing.
- Not handled (none seen in this stretch): Divine Rain (battle-only, flag 0x800, effect unknown, Lucia learns it at
  level 10 with `spell-levels`); HP regeneration from gear (none found: the Refresh and other rings feed the
  status-resistance table in func_0206ab6c). Level-ups rescale current HP to the new maximum (measured: 93 -> 97 at
  Jian's level 11), as vanilla.

**Composition with `no-curse-penalty`:** they compose; both are meant to be on. This feature does not touch
Jian's attack checks (0x020684F8, 0x02068628, 0x02068370), so on its own it would leave the vanilla one-swing
penalty in place. Built and tested with the full default list plus `curse-no-healing`.

## 2. Tests (all on build/curse/dsde.nds = default features + curse-no-healing; screenshots in build/curse/)

Built with `build/curse/build_curse.py` (scratch: appends the feature to FEATURES without editing features.py).
Plans in emu/plans/curse_*.plan, run with `--save` (the post-intro save, flag 0x33 poked into the flag word
0x02204624).

| Test | Plan | Result (measured) | Shots |
|---|---|---|---|
| Field, Healing Gum on cursed Jian, then Lucia | curse_field_items | Jian 5 -> 5 HP, Gums 5 -> 5; Lucia 5 -> 11, Gums 5 -> 4 | field_items/strip.png |
| Same, no curse flag | curse_field_items_uncursed | Jian 5 -> 13, Gums 5 -> 4 | field_items_uncursed/ |
| Same, 0x33 and 0x79 set (after Zethos) | curse_field_items_lifted | Jian 5 -> 13, Gums 5 -> 4 | field_items_lifted/ |
| Vanilla ROM: Gum on full-HP Jian | curse_field_items_vanilla_full (on build/curse/vcurse.nds) | Gums 5 -> 5, same screen as ours | field_items_vanilla/ |
| Field, Healing Water on cursed Jian, then Lucia | curse_field_spell | Jian 5 -> 5, Lucia MP 18 -> 18; Lucia 5 -> 21, MP 18 -> 14 | field_spell/strip.png |
| Same, uncursed / lifted | curse_field_spell_uncursed, _lifted | Jian 5 -> 28, MP 18 -> 14 | field_spell_uncursed/, field_spell_lifted/ |
| Statue, cursed | curse_statue | Jian 5 -> 28 HP, 1 -> 10 MP | statue/st_after.png |
| Battle, cursed: Gum on Jian, Healing Water on Jian; next round Gum on Lucia, Healing Water on Lucia | curse_battle | Jian 100 -> 100 through both; Gums 5 -> 4 -> 5 (taken at turn start, returned); Lucia MP 300 -> 296; round 2 Lucia 99 -> 116 (Water) -> 415 (Gum), Gums 5 -> 4 | battle/strip1.png, strip2.png |
| Battle, uncursed | curse_battle_uncursed | Gum 100 -> 399 (30% of 999), Water -> 417, Gums 5 -> 4 | battle_uncursed/ |
| Zethos (event battle 6, Jian alone, forced from Delrich Temple) | curse_zethos | Gum on Jian in rounds 1, 2, 3: taken and returned, HP 399 stays; the curse flag clears in round 3 (frame 8281, after Jian's turn); round 4 Gum 399 -> 698, round 5 696 -> 995 (Gums used up) | zethos/strip.png |

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
about as much and could heal each other. The hall cleared in five fights.

Bosses (`curse_boss_4`, `curse_boss_5`, forced from the hall, everyone on Fight, from full HP):

- **Deuce** (event battle 4): won in 4 rounds; Jian took no damage in this run (one run).
- **Gronk** (event battle 5): the party was wiped in 3 rounds. His all-party spell hit Jian about 40 a round
  (117 -> 78 -> 38 -> 0) and petrified Gabryel; Jian did about 50 a hit to Gronk's 1030 HP. This party loses to
  Gronk with or without the curse; with the curse, Lucia's heals between rounds cannot keep Jian up.

### 3.4 Fights between statues (estimated from 3.3)

On Fast with kill-on-hit, regular fights are short and cost Jian about 5 HP on average and up to about 21. With
117 to 136 HP that is about 5 fights in the worst case and 20 or more on average before he is in danger, and the
Cathedral's statue is central, so the hall-to-tower trips are short. Running from a fight costs nothing and the
maps restock on entry.

### 3.5 Verdict

**Viable for the regular fights and the Deuces; Gronk is the pinch.**

- Regular encounters: fine. The statue is in the middle of the only dungeon, there are no blue chests in the
  Cathedral (so no return trips for chests), and the towns at both ends have statues.
- Deuces: fine from a statue (one walk back between towers, which the LP's vanilla player already does).
- **Gronk**: his party spell is the one place where in-fight healing of Jian matters. With the curse Jian has
  about three rounds of Gronk at level 10; after that he falls and only a revive (Angel's Tears, 300 S, or
  Miracle Tears) brings him back at 10%. The party then fights mostly as Lucia and Gabryel. Gronk's fight level
  rolls between 10 and 30 (area clamp, docs/re-enemies.md), so some attempts will be much harder. Needs a real
  playtest at the levels players actually reach (the measurement used a forced fight at level 10).
- Zethos: no pinch. Jian is alone, the HP floor and the round-3 lift are vanilla, and from round 3 items and
  heals work again (measured).

### 3.6 Tuning knobs (in order of cost)

1. **Partial heal instead of none**: items heal 25% of what they would on cursed Jian (one shift in the two
   item caves and the spell cave instead of zeroing). Keeps the curse felt everywhere, softens Gronk.
2. **The curse yields in boss fights**: skip the block when the battle is an event battle (ctx +0x06 boss type
   non-zero). Gronk and the Deuces play as vanilla; regular fights keep the curse.
3. **A statue nearer the towers or before Gronk's room**: a map object change (DataPatch); needs the Cathedral's
   map data located.
4. **Revive at more than 10%** for cursed Jian, or a cheaper revive item in the Olbeage shop.
5. Lower Gronk's level clamp (area_min override for battle 5) so the fight does not roll up to 30.

Open (needs a playtest): the real levels at Gronk on this hack, the Cathedral towers' encounters (maps 146 to
149), and whether the item refusal sound is the vanilla buzzer.
