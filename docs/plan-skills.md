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
- **Stat changes keep the game's banners** ("ATK DOWN!"). Jeff first wanted an icon, then was fine with the
  banner once he saw it in place (2026-11-12). What an enemy is suffering from is shown on the name bar when
  it is highlighted in the enemy grid ("Thanatos ATKvDEFvPsn"); with that, no always-on icon beside the
  monster is needed.
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

| Skill | Id / built | Lv | MP | Target | Effect | Animation |
|---|---|---|---|---|---|---|
| Stone Throw | not built | 4 | 3 | one enemy, any row | physical damage at range | unused pitch (btldata 15); needs a stone projectile, Flora's arrow path is the model |
| Weapon Break | 38, built | 9 | 8 | one enemy | ATK down one stage | his attack with no hits, then the ATK DOWN banner |
| Armor Break | 39, built | 14 | 6 | one enemy | DEF down one stage | his attack with no hits, then the DEF DOWN banner |
| Focus | 40, built | 19 | 6 | all allies (the engine's flag is party-wide) | physical attacks never miss this battle | fist raise, HIT banner on each ally |
| Knockout Kick | 41, built | 25 | 9 | one enemy | sleep 2 to 4 turns, damage wakes; 70 percent; bosses immune | his attack with no hits, then the green ring |
| War Breaker | 42, built | 30 | 12 | all enemies | Weapon Break on all, skipping those already lowered | fist raise, ATK DOWN banner on each |
| Wall Breaker | 43, built | 36 | 9 | all enemies | Armor Break on all, skipping those already lowered | fist raise, DEF DOWN banner on each |
| Dragon Magic x4 | game's own | ring | 10 | all enemies | unchanged | unchanged |

### Gabryel (beast)

| Skill | Id / built | Lv | MP | Target | Effect | Animation |
|---|---|---|---|---|---|---|
| Gale Cut | game's own | joins with | 10 | all enemies | unchanged | unchanged |
| Savage Rush | not built | joins with | 5 | one enemy | heavy physical hit | unused double claw (btldata 33) |
| Venom Claw | 44, built | 13 | 8 | one enemy | poison, 5% max HP per turn; always lands, bosses too | her attack with no hit, then the green ring |
| Blinding Swipe | 45, built | 17 | 7 | one enemy | blind 2 to 4 turns; always lands, bosses too | her attack with no hit, then the green ring |
| Feral | 46, built | 21 | 8 | self, no picker | ATK up one stage | item pose, ATK UP banner on her |
| Howl | 47, built | 26 | 9 | one enemy | fear (the paralysis status): no action 2 to 4 turns; 70 percent; bosses immune | her attack with no hit, then the green ring |
| Venom Storm | 48, built | 31 | 12 | all enemies | Venom Claw on all, skipping those with a status | item pose, green ring on each |
| Blinding Gale | 49, built | 35 | 10 | all enemies | Blinding Swipe on all, skipping those with a status | item pose, green ring on each |
| Dread Roar | 50, built | 39 | 13 | all enemies | Howl on all, each with its own roll | item pose, green ring on each |

### Rufus (leader of the beastmen's strike force; joins at 15, leaves, returns late in the Retold story)

His skills are a commander's orders to the troops. All built 2026-11-12 (docs/plan-weapon-break.md 14). The
party versions are learned at levels 36 to 42, so they only exist once he returns; in Classic he is gone
before then. The healers still have Quick, Grand Weapon, and Grand Shell until their step.

| Skill | Id / built | Lv | MP | Target | Effect |
|---|---|---|---|---|---|
| Thunder Sword | game's own | joins with | 10 | all enemies | unchanged |
| Rally | 51, built | 1 | 6 | one ally (the game's ally picker) | ATK up one stage |
| Stand Fast | 52, built | 1 | 6 | one ally | DEF up one stage |
| Quick March | 53, built | 17 | 5 | one ally | AGI up one stage |
| Stratagem | 54, built | 19 | 6 | one ally | INT up one stage |
| Battle Cry | 55, built | 36 | 12 | all allies | Rally on everyone not yet raised |
| Shield Wall | 56, built | 38 | 12 | all allies | Stand Fast on everyone not yet raised |
| Forced March | 57, built | 40 | 10 | all allies | Quick March on everyone not yet raised |
| War Council | 58, built | 42 | 12 | all allies | Stratagem on everyone not yet raised |

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
- Stone projectile sprite; whether Rufus's return exists in the story scripts.
- Removing the Tools / Cards choice from the battle Item command.

First prototype: Jian's Weapon Break end to end. Built 2026-11-12 (docs/plan-weapon-break.md): in both
editions, with the pick on the enemy grid, the refusal of a wasted cast, and the name bar tags.
