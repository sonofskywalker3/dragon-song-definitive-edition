# The opening narration: Japanese, USA and Lunar canon

Written 2026-10-07 for Jeff. Sources:

- The Japanese text of script 026, decoded with real kanji (`uv run python -m dsde.jp_text
  build/unpacked_jp/script/026.bin`; font and encoding in docs/re-japanese.md). Every character is read from
  the game's own font, so the translation below rests on the exact text, not on guesses.
- The USA text of the same script, before our trims (docs/playtest-feedback.md items 1 and 3).
- Lunar canon from the PS1 scripts of Silver Star Story Complete (SSSC) and Eternal Blue Complete (EBC) in
  build/research/lunar_scripts/ (not tracked; line numbers given).

Only short Japanese phrases are quoted here; the translation is ours.

## 1. The Japanese opening, translated

A close translation, page by page as the game shows it. Words in brackets are the game's 【】 terms.

1. Long, long ago... This world had no grass, no trees, not even air. It was truly a world of death.
   The Goddess Althena came down to this land **together with the Dragonmaster** (竜使いとともに), leading
   the four dragons. Althena's magic gave moisture to the earth and turned the desert of death into a world
   rich with green.
2. In time... on the earth, reborn beautiful and overflowing with life, new places were built where people
   live, and the Goddess Althena blessed the people and their world.
   The Dragonmaster swore the Goddess eternal loyalty and, with the four dragons, **took up the duty of
   guarding this world**. And Althena's existence became **the wellspring of a world of magic** centred on
   her magical power (魔法世界のみなもと).
3. Splendidly built, superior in every physical ability, in stamina, quickness and endurance: the
   【Beastmen】...
4. In contrast... deft at handling tools, but small and physically frail: the 【Humans】.
   Little by little, the relationship between the two races **tilted toward a society led by the stronger
   Beastmen** (獣人しゅたいのしゃかい).
5. The bold Beastmen, who loved a showy life, built a **royal castle** (王者城, a ruler's castle) at the
   centre of the world; the Humans, who loved a plain life, moved out to the provinces...
   Their opposite ways of life kept a moderate distance between the two races and, in a **delicate
   balance** (ぜつみょうなバランス), kept the peace.
6. Port Searis, a thriving port on the continent of **Hommel**. Here, making a living as 【couriers】, is a
   boy **who is good at handstands** (さかだちがとくいな), 【Jian Campbell】, and his **partner** (あいぼう)
   【Lucia Collins】... Both full of energy, they loved fun and adventure with a little danger in it.

## 2. Where the USA text differs

| # | Japanese | USA (original) | Kind of change |
|---|---|---|---|
| 1 | Althena comes *together with* the Dragonmaster | "her servant the Dragonmaster" | added a rank (we now say "champion") |
| 2 | Althena is the wellspring of a world of **magic** | "the source of **life**" | meaning changed |
| 2 | The Dragonmaster takes up guarding the world, with the dragons | "appointed as Master of the Four Dragons" | added an appointment |
| 2 | (nothing) | "The world became aware of life, and embraced it." | added |
| 4 | Humans: deft with tools, small, frail | "Blessed with **intellect**..." | added: makes it brains against brawn |
| 4 | Society came to be **led by** the Beastmen | "began to lean in favor of the Beastmen" | power structure blurred |
| 5 | A **royal castle** at the centre of the world | "a magnificent castle" | rule left out |
| 5 | Showy against plain **tastes** | "luxurious, rich lifestyle" against "quieter surroundings" | turned into wealth |
| 5 | A **delicate** balance | "a balance... lasting peace" | the fragility is lost |
| 6 | Continent of Hommel | Caldor | renamed (the USA uses Caldor in scripts 026 and 008 alike) |
| 6 | A boy good at **handstands** | "a youth who loves acrobatics" | softened; handstands set up Jian's headstand curse |
| 6 | His **partner** Lucia | "his friend" | weakened |

**On the "racism is bad" complaint.** The premise is the same in both versions, but the Japanese sets it up
with more edge: the Beastmen *rule* (a Beastman-led society, a ruler's castle at the centre of the world),
the Humans are physically weaker and live out in the provinces, and the peace is a *delicate* balance kept
by staying apart. That is an unequal arrangement that only works while nobody crosses the line, which gives
the story something to push against. The USA text softens each part ("lean in favor", "a magnificent castle",
"lasting peace") and adds "intellect", which turns it into a neutral brains-against-brawn contrast. The
intro is not where the flatness comes from, but the localization did remove the tension it set up. The story
scenes (scripts 004, 005, 009 for Zethos and the Beastmen) are the next place to compare.

## 3. What Lunar 1 and 2 establish

- **A dead world made green**: EB's opening calls the world "a lonely, barren place, unfit for habitation"
  until Althena transformed it (EBC 62-65). Dragon Song's first lines fit.
- **People came with Althena** from the Blue Star (EBC 65-67, 7570-7572); in EB's time most have forgotten
  why the Blue Star hangs in the sky (EBC 70-72). The USA "The world became aware of life" says the
  opposite (life arising here). Naming the Blue Star's fate or Zophar would spoil EB's late reveal.
- **The Dragonmaster is a title earned through the Four Dragons' trials** (SSSC 330-331, 6213), a protector
  of "Althena and her people" (SSSC 2285) and of "all that Althena has created" (SSSC 8411-8412). Neither PS1
  script calls the Dragonmaster a servant. Dragon Song agrees: a girl in script 008 asks Jian whether he is
  aiming to become a Dragonmaster (竜使いをめざすの？).
- **Magic is Althena's power spread through the world** (SSSC 8956-8978): "source of magic" is canon.
- **The Four Dragons** are White, Red, Blue and Black, Althena's guardians (EBC 5691, 6356-6360). In Dragon
  Song two live on Hommel/Caldor (red and white, script 008) and two on Ghulian.
- **Beastmen** do not appear in Lunar 1 or 2, so the intro must not explain where they came from.
- **Silver Star Story has no world narration**; EB's narration ends on its heroine. "Wind" is not a series
  motif, but Dragon Song's own Japanese ending is built on it ("the one who inherits the wind").

## 4. Suggested changes

Tags: **[JP]** closer to the Japanese, **[canon]** closer to Lunar 1 and 2, **[impact]** stronger as an
opening. Each is independent; the draft in section 5 applies the recommended ones.

1. **[JP][canon] "with her Dragonmaster"** instead of "her champion the Dragonmaster". "Champion" is fine
   for canon; "with" is what the Japanese says and keeps the Dragonmaster beside her rather than below her.
   Optional.
2. **[JP][canon] "the wellspring of all its magic"** instead of "the source of life". Recommended.
3. **[JP][canon] Drop "appointed as Master of the Four Dragons"**: the Dragonmaster swears loyalty and, with
   the Four Dragons, takes up guarding the world. Recommended (the title is earned in canon, and Jian is
   working toward it).
4. **[canon] Replace "The world became aware of life, and embraced it"** with people coming to the reborn
   land ("people came to build new homes upon it"). True to EB without naming the Blue Star. Recommended.
5. **[JP] Drop "intellect"** from the Humans: "deft with tools, but small and frail". Recommended.
6. **[JP][impact] Say who rules**: "Over time, the stronger Beastmen came to lead." and "a royal castle at
   the heart of the world". Recommended; this is the main fix for the flatness.
7. **[JP][impact] Keep the peace fragile**: "...and that distance kept a delicate peace." Recommended. A
   stronger option not in the Japanese: end the page with "...for now." Jeff's call.
8. **[JP] Tastes, not wealth**: Beastmen "loved a showy life", Humans "kept to simple ways". Recommended.
9. **[JP] "his partner Lucia Collins"** instead of "his friend": matches the Japanese and Jian's own run line
   ("Lucia and I haven't been partners long"). Recommended.
10. **[JP] Handstands**: the Japanese introduces Jian as a boy good at handstands, which pays off in his
    headstand curse. We cut "who loves acrobatics" as cringe; "a boy with a knack for handstands" would be
    the faithful version. Jeff's call.
11. **[canon][impact] The Blue Star in the first line**: "Long, long ago, beneath the Blue Star..." ties the
    intro to both games and to Dragon Song's own Japanese ending ("the land that looks up at the Blue
    Star"), without explaining it. Optional.
12. **[JP] Hommel instead of Caldor**: only if scripts 026 and 008 change together (the dragons talk in 008
    names the continent). Optional; low value.

The same script holds the ending. Two USA softenings there are worth undoing when the ending is reworked:
Titus's "so that this never happens **again**, we **must** fight the darkness inside ourselves" (USA: "I can
only hope... better able to fight against the evil lurking inside us"), and the closing narration's "the
one who inherits the wind will become a bridge to the future and set out on a new adventure. **That might
be you.**" (USA: "...A day when an adventurer will become... Dragonmaster.").

## 5. Draft with the recommended changes

Lines kept within 30 characters for the text box. Page breaks as `---`.

```
Long, long ago...
This was a dead world, without
grass, without trees, without
even air.

Then came the Goddess Althena,
with her Dragonmaster, leading
the Four Dragons.
---
Althena's magic gave water to
the earth, and turned the
desert of death green.

In time, life filled the
reborn land, and people came
to build new homes upon it.
Althena blessed them all.
---
The Dragonmaster swore the
Goddess eternal loyalty, and
with the Four Dragons took up
the guarding of the world.
Althena herself became the
wellspring of all its magic.
---
The Beastmen.
Powerfully built, they were
stronger, faster and hardier
in every way.
---
And in contrast, the Humans.
Deft with tools, but small of
build and frail of body.

Over time, the stronger
Beastmen came to lead.
---
The bold Beastmen raised a
royal castle at the heart of
the world, and loved a showy
life. The Humans moved out to
the countryside, and kept to
simple ways.
---
Living so differently, the two
races kept their distance, and
that distance kept a delicate
peace.
---
Turn now to Port Searis,
flourishing on the continent
of Caldor.

A youth named Jian Campbell
is making a living here as a
courier, along with his
partner Lucia Collins.
```

Built 2026-10-07 in a revised form (docs/playtest-feedback.md item 10); the draft above is the first proposal. The game wraps at 30 characters by itself and
the stored text drops the space at each wrap (feat_text.py), so the build must check every page in the
emulator.
