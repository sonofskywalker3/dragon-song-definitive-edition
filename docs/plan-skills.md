# Plan: party skills learned by level, cards out of battle (preliminary, 2026-11-12)

Design agreed in outline with Jeff; levels, MP costs, and names are first drafts. Nothing here is built yet.
Background: docs/re-skills.md (skill tables, animations, unused assets), docs/re-cards.md (what every card
does, with numbers), docs/boss-exp.md (expected level at each boss).

## Decisions

- **Cards lose their battle use.** The Item command goes straight to the item list (no Tools / Cards choice).
  Cards stay as collectibles. No work goes into the card system itself, and boss cards get no effects.
- **Skills are learned by level**, as in Lunar 1 and 2. No consume-a-card learning, no skill levels.
- **Single target first, all targets later** as a separate spell with its own name (Lunar 2: Heal Litany /
  Calm Litany; this game: Healing Water / Tender Rain).
- **The healers lose their buffs; Rufus gets them.** Grand Weapon, Grand Shell, and Quick leave Lucia and Flora.
- **No MP recovery spell, no MP gift.** HP Walk and MP Walk become accessories (the Treant and Gloomwing
  field effects, always on while equipped).
- **Stat changes show an icon** (sword or armor with an arrow), not the "ATK DOWN!" banners. btldata 157 has
  unused sword, armor, ring, and hat icons; the arrows need drawing.
- **Flora learns Miracle Tears** (vanilla: never), late.
- Possible later: a card slot (or the planned ring slot) that grants a skill or passive while a card is
  equipped. Not scoped.

## Balance rules

- A stat-down skill moves an enemy one stage at most (the card versions stack to four stages, which takes a
  boss's hit from 42 to 1).
- Sleep, paralysis, and fear get a success roll on regular enemies (the cards never miss) and keep the boss
  immunities. Poison and blind still land on bosses.

## Expected levels (docs/boss-exp.md)

Sasquatch 7; Coliseum, Cathedral, Zethos 10; Lucia leaves 11 to 14; Elda Canyon 16 (Rufus joins at 15);
Red, White, Black Dragons 23 to 28; Blue Dragon 36; final fights 40 to 42. Late joiners arrive at Jian's EXP
(Gabryel near 10, Flora near 13).

## Kits

### Jian (street fighter)

| Skill | Lv | MP | Target | Effect | Animation |
|---|---|---|---|---|---|
| Stone Throw | 4 | 3 | one enemy, any row | physical damage at range | unused pitch (btldata 15); needs a stone projectile, Flora's arrow path is the model |
| Weapon Break | 9 | 8 | one enemy | ATK down one stage | kick + sword-down icon |
| Armor Break | 14 | 6 | one enemy | DEF down one stage | kick + armor-down icon |
| Focus | 19 | 6 | self | attacks never miss this battle | Dragon Magic pose |
| Knockout Kick | 25 | 9 | one enemy | sleep 2 to 4 turns, damage wakes | flip kick + ring |
| War Breaker | 30 | tbd | all enemies | Weapon Break on all | |
| Wall Breaker | 36 | tbd | all enemies | Armor Break on all | |
| Dragon Magic x4 | ring | 10 | all enemies | unchanged | unchanged |

### Gabryel (beast)

| Skill | Lv | MP | Target | Effect | Animation |
|---|---|---|---|---|---|
| Gale Cut | joins with | 10 | all enemies | unchanged | unchanged |
| Savage Rush | joins with | 5 | one enemy | heavy physical hit | unused double claw (btldata 33) |
| Venom Claw | 13 | 8 | one enemy | poison, 5% max HP per turn | claw + ring |
| Blinding Swipe | 17 | 7 | one enemy | blind 2 to 4 turns | claw + purple slash (318) |
| Feral | 21 | 8 | self | ATK up one stage | special pose + sword-up icon |
| Howl | 26 | 9 | one enemy | fear (the paralysis status renamed): no action 2 to 4 turns | special pose + ring |
| Venom Storm | 31 | tbd | all enemies | Venom Claw on all | |
| Blinding Gale | 35 | tbd | all enemies | Blinding Swipe on all | |
| Dread Roar | 39 | tbd | all enemies | Howl on all | |

### Rufus (knight commander; joins at 15, leaves, returns late in the Retold story)

| Skill | When | MP | Target | Effect |
|---|---|---|---|---|
| Thunder Sword | joins with | 10 | all enemies | unchanged |
| Rally | joins with | 6 | one ally | ATK up one stage |
| Guard Order | joins with | 6 | one ally | DEF up one stage |
| Quick | 17 | 5 | one ally | AGI up one stage |
| Insight | 19 | 6 | one ally | INT up one stage |
| Battle Cry | return | tbd | all allies | Rally on all (the old Grand Weapon) |
| Shield Wall | return | tbd | all allies | Guard Order on all (the old Grand Shell) |
| Tailwind | return | tbd | all allies | Quick on all (the old Quick) |
| Inspire | return | tbd | all allies | Insight on all |

### Lucia (levels 1 to about 13)

| Spell | Lv (built today) | Lv (proposed) |
|---|---|---|
| Healing Water | 1 | 1 |
| Cure Squall | 2 | 4 |
| Escape | 3 | 6 |
| Tender Rain | 6 | 8 |
| Divine Rain | 10 | 11 |
| Miracle Tears | 12 | 13 |

### Flora (joins near 13, stays to the end)

| Spell | Lv |
|---|---|
| Healing Water, Cure Squall, Escape, Tender Rain | known on joining |
| Water Bind (paralysis, one enemy; unused water ribbon, btldata 313) | 16 |
| Divine Rain | 20 |
| Binding Rain (Water Bind on all enemies) | 28 |
| Miracle Tears | 32 |

The spell table has separate level bytes for Lucia and Flora, so the two lists can differ.

## Cut (no skill, no card use)

AGI, DEX, LUK, and INT downs; DEX and LUK ups; all-stats-down; silence; stone; confusion; the damage-doubling
and damage-halving cards; the full-party heal, MP refill, and revive cards; the escape card; the four
map-enemy cards; the steal and break blockers.

## Open technical work

- Both the spell table (0x02094978, 0x26 entries) and the effect table (0x02096180, 49 rows) are full:
  relocate or extend.
- A level-learn check for Jian, Gabryel, and Rufus in func_02050c50 (only the healers have level bytes).
- Single-enemy spell targeting through the target grid (the engine's one-enemy mode exists, flags & 0xC0000000
  == 0, used by the Dagon card; how it picks is not traced).
- A hook from the spell effect code to the card effects (statuses, never-miss flag); stat stages already go
  through func_02054dec.
- Success rolls and the one-stage cap.
- How damage is computed for a party-cast physical skill (Stone Throw, Savage Rush).
- Stone projectile sprite; icon effect with arrows; whether Rufus's return exists in the story scripts.
- Removing the Tools / Cards choice from the battle Item command.

First prototype: Jian's Weapon Break end to end (table space, level check, single-enemy pick, one-stage ATK
down, icon effect, MP cost).
