# Dialogue tone and style rules

**Status: DRAFT, waiting for Jeff's approval.** No dialogue is written against these rules until he approves them.

Rules for every new or rewritten line of dialogue in this hack. The target is the feel of the PS1 Lunar
localizations (Silver Star Story Complete, "SSSC", 1999; Eternal Blue Complete, "EBC", 2000), applied to
Dragon Song's own cast and story. Written 2026-10-06; supersedes build/research/lunar_style_rules_draft.md.

Sources and method:

- The PS1 transcripts in build/research/lunar_scripts/ (not tracked, copyrighted; quoted here only in short
  fragments, about 15 in all). They record each speech as one paragraph, so they show what is said and how, but
  not where the PS1 boxes broke.
- Dragon Song USA text: every message in build/unpacked/script/*.bin, decoded in full (script 013 is data,
  not text). Japanese release: build/unpacked_jp/script/, read with the kana table in docs/re-japanese.md.
- Numbers below ("per 100 words") were counted over the whole transcripts; Dragon Song numbers over the
  whole USA script.
- Screenshots of the dialogue box: build/par_c/save/sg_talk1_a.png, sg_talk1_b.png, sg_talk2_b.png.

Each rule is meant to be checkable by reading the line. The checklist at the end collects them.

## 1. Voice and register

### 1.1 How people address each other

- First names between friends. No titles inside the party, except the ones below.
- Titles come from rank, and only the people below the rank use them: Rufus and priests call Gabryel
  "my lady"; everyone outside the family says "Beast King" or "King Zethos"; Gabryel says "Papa".
- Gabryel is "Gabi" to the party and to anyone she has told (she insists on it in script 005, and on no
  "Miss" either). Strangers say "Gabryel".
- Teasing nicknames have one or two owners per cast, not everyone. In EBC Ronfar names Ruby ("pink pest",
  "pretty-kitty") and Gwyn calls Hiro "m'boy"; nobody else does. In this game: Gabryel ("muscle head",
  "dunce", "bow girl" for Flora) and Gad ("lad"). New nicknames go to those two only.
- A nickname is built from something true about the person (Ruby is pink and a cat-shaped dragon; Jian is
  all muscle; Flora carries a bow).

### 1.2 Banter, teasing and sincerity

- Teasing between friends always targets an established trait (Ruby's jealousy, Ronfar's gambling, Nall's
  appetite; here Jian's oversleeping, Lucia's worrying, Flora's appetite, Rufus's "I can't be killed").
  Never invent a new flaw for a joke.
- The person teased answers in one short line, or with "..." and no answer. The exchange then moves on.
  A teasing exchange is at most 3 boxes long.
- Sincerity is plain: no irony, no joke in the same box. When the PS1 games go serious (Ronfar and Mauri,
  Luna on the night before leaving Burg) the speaker says what they feel in short, simple sentences.
- Jokes flank serious beats, never sit inside them. Rule: no joke between the start of a serious beat
  (death, capture, a reveal, a confession) and the end of that scene. The scene after may open with one to
  release the tension.
- One deflating line is allowed after a sincere speech, and it must come from a different character and
  must not mock the sincerity itself. EBC's model: Hiro's joke answer about Lucia is shut down by Ruby, and
  the sincere answer follows.

### 1.3 How jokes land (Working Designs humor)

Keep:

- Setup, punchline, reaction: one character sets it up, another lands it, a third reacts in a few words or
  with "...". The reaction is short; the joke is never explained.
- In-world idioms instead of real-world ones. Money is silver ("the million-silver question" in EBC), and
  similes use the world's own things (Nall: "She plays you like an ocarina..."). Here: silver, packages,
  deliveries, the Coliseum, beastmen and humans, Althena.
- Trait puns: a joke in the language of the target's hobby (Hiro to the gambler Ronfar: "We won't crap
  out!"). Here: delivery and courier talk for Jian and Gad, food for Flora, swordplay for Rufus.
- The literal-minded misunderstanding, used only for a character who truly does not know the custom (EBC
  Lucia, told to keep her distance from Hiro: "You mean that Hiro tends to trip people who get too close.").
  In this game the beastmen and the Vile Tribe can misread human customs and the humans can misread theirs;
  Lucia cannot, she is an ordinary local girl (see 3.2).
- Pomposity punctured: a proud or pushy character (Leo, Nash, Lemina) gets a flat one-line answer.
- Running gags pay off later. Each callback is one line, not a repeat of the whole joke (Gad's "late again
  as usual" after the oversleeping).
- Capitals for one stressed word ("I am NOT Hiro's pet, mister"): at most one capitalized word per page,
  never a whole sentence except a scream.

Avoid (these date the PS1 scripts or do not fit this game):

- Real-world references of any kind: coins ("along with a nickel, will buy you a warm cup of jack squat"),
  brands, places, people, TV, offices ("Employee of the Month"), computers.
- Period slang that marks a decade: "daddy-o", "Ladies and germs", "dude", "babe", "honey-smack".
- Slurs and cheap shots that the PS1 scripts use and that would read badly now: mocking someone as
  mentally disabled, "wench", "bimbo", jokes about weight, and broken-English accents for foreigners (the
  Nanza guards).
- Leering played for laughs (Kyle and Ronfar chasing women). Flirting is fine (Gabryel, see 3.3); the joke
  is never about a body.
- Profanity. Dragon Song's own text has none ("moron", "idiot", "dunce" among friends is its ceiling);
  keep it there, even though the PS1 scripts use "damn" and "hell".
- Fourth-wall jokes, except at most one per chapter from a comic character or an NPC, never in a serious
  scene (Dragon Song already has one: Rufus's "check the script, that's my line"). Buttons and menus are
  named only in tutorials.

### 1.4 Punctuation habits

Measured: both PS1 scripts use "?!" for shocked questions about 15 times as often as "!?" (391 to 28);
Dragon Song's USA text does the same (173 to 9).

- Shocked question: "?!" only. Never "!?", never "?!?".
- "!!" only for a shout or a scream, at most once per scene. Never "!!!".
- Ellipsis: exactly three dots, no spaces inside, attached to the word before ("Hey..." or "I... I can't").
  Never four or more dots.
- A character who says nothing gets a box with "..." alone. A long, heavy silence is "... ... ..." (the
  PS1 form: Alex answers with it 44 times in SSSC). Use the long form only at a dramatic beat.
- At most 2 ellipses per page, except a character who is hurt, dying or cursed.
- Interruptions: the cut-off line ends in "..." and the next speaker starts at once. No dashes of any kind
  (the PS1 scripts use "--"; this game's text never does, and no dash longer than the hyphen appears anywhere in it).
- Stammering uses a hyphen ("I-I hear music") at most once per scene, and only once the encoder writes
  "-" (section 5).
- "OK", not "okay" (Dragon Song uses "OK" 111 times and "okay" never).
- "Blue chest", not "blue box" (Jeff, 2026-10-08; the vanilla guidebook says "Blue Boxes").
- Oxford comma in every list of three or more: "Experience, items, and silver" (Jeff, 2026-10-08). This
  covers game text, the guidebook pages, the README, and release notes.
- Exclamation budget per page (sentences ending in "!"; a "?!" counts as a question), by character: Flora and Lucia (excited) 3; Jian, Gabryel, Gad, Cherenkov 2;
  Rufus 1; Zethos, the Dragons and priests 1. Measured for comparison, per 100 words: Ruby 11, Hiro 6 to
  7, EBC Lucia 2, Ghaleon 3.

### 1.5 Sentence and box length

- Start each sentence on a new line when it fits; this is Dragon Song's own habit and keeps boxes easy to
  read. A sentence longer than one line breaks at a comma or between phrases, never inside a name.
- A sentence is at most 2 lines (about 12 words).
- A page is at most 4 lines (hard limit 5, section 5.2). Dragon Song's median page is 13 words.
- Length follows the character. PS1 medians per speech: Alex 3 words, Hiro 7, Ruby 13, Ronfar 16, Leo 24.
  Here: Jian and Rufus short (1 to 2 lines per page usually), Lucia, Gabryel, and Flora medium, Gad and
  Cherenkov 2 to 3 lines at most.
- A long speech (a lore explanation, a confession) is split into pages of one idea each, and after 3 pages
  someone else gets a line, even if it is only "..." or a question.

## 2. Exposition

- The person who would know explains; the person who would not, asks. EBC and SSSC send lore to the
  outsider (Alex the village boy, Hiro and Lucia the strangers). Here: Gabryel on beastmen, Healriz and her
  father; Flora on the Frontier and the Vile Tribe; Gad on jobs; priests, Titus and the Dragons on Althena.
  Jian and Lucia are the outsiders who ask in beast and Frontier lands.
- No "as you know": if the speaker and the listener both already know a fact, cut it.
- One new fact per page, at most 3 new facts per conversation. A fourth goes to another scene or another
  speaker.
- Long explanations are interrupted. EBC's Leo lectures, and Ruby cuts in between pages. Rule: after 2
  pages of explanation, a reaction or a question from someone else.
- World history comes in set pieces: the opening narration, an elder, a shrine, a book, a Dragon. Party
  chatter does not deliver history.
- NPCs give news and local color, at most one lore fact per NPC line.
- Nobody recaps the opening narration. The player read it seconds before.
- Self-introductions happen only in a scene: when someone asks ("Who are you?"), or when a character meets
  someone new on screen. They give the name and at most one fact. A character never introduces themselves
  to the player, with one exception, below.

### 2.1 The one aside to the player (EBC's Hiro model)

How it works in EBC: the game opens mid-heist with no introduction. Only after the fall, while Hiro and
Ruby run from monsters, does Hiro speak to the player directly, once, as narration over the chase. It is
about 150 words in the transcript and never happens again in the game. In order, it:

1. Opens on the situation and the player ("Well, looks like you've caught us in another messy
   situation.").
2. Gives his name, offhand ("by the way").
3. Introduces his companion with a joke at her expense (Ruby says she is a dragon; he is not so sure).
4. Gives one fact about his family or mentor (Grandpa Gwyn, the archaeologist who taught him).
5. Undercuts the danger they are in, at his own expense.
6. Ends on what he wants (to prove, from ruins like these, that the past shaped the world).

It reveals nothing about the plot, only who he is and what he likes. SSSC has no aside: Alex gets one
short narrated paragraph (about 90 words) about his dream of being like Dyne, with no name and no facts,
and then Nall calls him.

Rules for this game:

- Only Jian, only once, only during the scripted run out of the inn (playtest feedback item 2).
- 2 or 3 pages, 4 lines each at most, about 40 to 60 words in all (this game's boxes are much smaller than
  the PS1's).
- Keep the order: situation, name, partner with a joke, one new fact, a self-deprecating beat. An ending
  wish is optional (Jian has no stated dream at this point of the story; do not invent one).
- Only facts that are true in this game, and only ones the opening narration does not already give. After
  the intro trims (feedback item 3) the narration gives his name, his job as a courier and Lucia as his
  friend; new are Gad's Express, the partnership being recent, the handstands, his oversleeping and the
  crush. The name may be said once, as the greeting.
- Displayed like the vanilla inner monologue (alternate text color, section 5.4), so the player can tell
  it from spoken dialogue.

### 2.2 Inner thoughts

- The PS1 games put a character's unspoken thought in parentheses mid-speech, often for a joke the
  character would not say aloud (Hiro: "I think I'm going to leave out the part about how blindingly
  beautiful she is."). This game has no parenthesis glyph; it uses the alternate text color for thoughts.
- A thought is at most one page and says something the character would not say aloud. Jian's crush on
  Lucia is the natural use.

## 3. Character voices

Each card gives the PS1 models, what Dragon Song's own text already establishes, and rules. When the USA
text and the Japanese disagree on a fact, the Japanese wins (feedback item 5).

### 3.1 Jian (hero)

- Models: Hiro first (eager, teasing, protective, impulsive, sweet on his partner, runs off alone to spare
  his friends), not Alex (who is nearly silent: median 3 words, and one speech in six is "... ... ...").
- Established: courier for Gad's Express in Port Searis, lives at Cherenkov's inn, oversleeps (a running
  gag: Cherenkov, Lucia, Gad), handstands are his trick, teases Lucia ("Your cute face will get all
  wrinkled"), wants humans and beastmen to understand each other (script 004), tries to go on alone and is
  scolded for it (019, 025). The Japanese uses the casual "ore" for "I".
- Rules: short, casual, contractions. "I have to" or "I've got to", not "I must" (the USA text overuses
  "must"; keep it for formal speakers). Resolve is one direct line, not a speech (EBC: "Leo might work for
  Althena, but he's flesh and blood, just like me"). He teases Lucia gently and gets flustered when teased
  back. He is not the main joke-teller; he reacts. Silence ("...") when hurt or ashamed.

### 3.2 Lucia (partner)

- Dragon Song's Lucia (Lucia Collins) is a different person from EBC's Lucia. EBC's Lucia is a stiff
  envoy from the Blue Star: almost no contractions (about 2 per 100 words against about 7 for everyone
  else), literal-minded, learns feeling slowly. None of that applies here. Do not copy her speech.
- Models: Luna (warm, scolds the hero fondly, keeps him out of trouble; "Alex, you're late again,
  silly."), with a flash of Jessica's temper when scared for him ("Jian, you moron! You loser...").
- Established: Jian's courier partner, punctual, a worrier, hates being outside at night, distracted by
  pretty things (flowers, lamps, a parasol), a bad cook by her own account, mothers Jian and refuses to be
  mothered. The Japanese gives her soft, girlish scolding ("mou, Jian-ttara").
- Rules: contractions, "Oh, Jian..." scolding openers, exclamations when delighted or worried. Kind to
  strangers. She is Althena reborn (script 021); nothing she says before then may hint at it.

### 3.3 Gabryel (Gabi)

- Models: Jessica (sharp tongue, takes charge, insults the hero with affection, devout underneath) and
  Jean (a hidden side she is ashamed of).
- Established: Beast King Zethos's daughter, insists on "Gabi", bossy in a crisis ("Pick yourselves up or
  I'm leaving you behind!"), calls Jian "muscle head" and "dunce", calls her father "Papa", the priests call
  her "my lady". Design 11: she joins as an impressed fan of the tournament winner and flirts with Jian
  enough to make tension with Lucia.
- Rules: confident, quick, direct; gives orders in crises. Flirting is playful and self-assured ("the
  human who fought so bravely in the Coliseum"), never crude, and never runs Lucia down. Her lines about
  her father are played straight.

### 3.4 Flora

- Models: Nall and Ruby for the comic beats (food, bravado that collapses), and the local guide role of
  Ronfar in EBC (she knows the way and the people).
- Established: grew up in the Frontier, guides the party there, archer ("bow girl"), loves food (Ghulian
  Tomatoes), hates hot places, claims she is not scared of the airship, has a brother she will not leave
  (script 010). Bright: "Oh wow!", "Hooray!", "plant power".
- Rules: the most exclamations in the cast; she explains Frontier and Vile Tribe matters; her fear is
  denied out loud and shown in the same box ("Not scared at all!").

### 3.5 Rufus

- Models: Leo's loyal-knight formality and Kyle's warrior bravado, with dry humor of his own.
- Established: a beastman soldier loyal to Zethos, calls Gabryel "my lady", boasts that he cannot be
  killed, dry and self-deprecating ("I do profess to a talent for not getting killed"), admits he looks
  down on humans and then calls Jian a friend.
- Rules: the shortest lines in the cast after Jian; few contractions, "I shall" is fine; at most one "!"
  per page; humor is understatement, never a gag. He does not explain himself.

### 3.6 Gad

- Models: the gruff elders and bosses of the PS1 games (Gwyn's "m'boy", Jessica's father Mel).
- Established: runs Gad's Express, calls Jian "lad", blunt and tactless ("It's not like Lucia is dead or
  something"), cares underneath, and ribs Jian about being "late again as usual".
- Rules: imperatives and short sentences, talk of jobs, deliveries and silver; "lad" at most once per
  page. Kindness is shown by action, rarely said.

### 3.7 Cherenkov (innkeeper)

- Model: the PS1 townsfolk who nag the hero fondly. Comic NPC, not lore.
- Established (USA): dry and sarcastic ("Finally, you grace us with your presence."), nags about the mud
  on Jian's shoes, warm when it matters (he keeps Jian's room free while he is away). The Japanese is
  rougher and folksier, an older working man's speech ("Overslept again? Honestly, you're hopeless").
- Rules: 2 or 3 lines per page; one joke per visit; addresses Jian by name; never explains the world.

## 4. Names and spelling

- Use this game's spellings: Dragonmaster (one word), Goddess Althena, beastmen and beast folk (lower
  case), Vile Tribe, Beast King Zethos, Gad's Express, Port Searis, Healriz, Gabi.
- The speaker tag shows the full display name the game already uses for that character
  ("Beast King Zethos", not "Zethos").
- Gad's Express recipients use the corrected names (docs/re-japanese.md).

## 5. Text box mechanics

### 5.1 Line width

- 30 characters per line, counting spaces and punctuation.
- Break lines yourself with the line break code. The box also wraps by itself at 30, but the stored text
  then has no space at the wrap ("Althena,her"), which makes edits error-prone.
- Do not split a place or item name across lines.

### 5.2 Lines per page

- The box shows 6 rows: the speaker tag and 5 lines. A sixth text line scrolls the tag out of view
  (sg_talk2_b.png). Rule: at most 4 lines per page, 5 at the very most.
- A page ends with the page break (waits for A). A message ends with page break then end.

### 5.3 Codes (from the vanilla text)

| Bytes | Meaning | Notes |
|---|---|---|
| FD | line break | |
| FE | page break, waits for A | FE FF ends the message |
| FE FD FD | next page in the same message | also used before a new speaker tag |
| FE FC | next page, form unknown | 598 of 1091 speaker changes use it; meaning unconfirmed. Copy the message's own pattern |
| FB 06 ... FB 07 | alternate color (yellow) | speaker tag, then FD; also inner thoughts |
| FB 04 ... FB 07 | blue | place names, every mention |
| FB 03 ... FB 07 | item color | key items and the package ("Jump Shoes", "package") |

- Speaker tag: FB 06, name, FB 07, FD, at the start of every speaker turn. A later page of the same turn
  has no tag.
- Off-screen speakers still get their real name tag (the game never uses "???").
- Inner thoughts: the vanilla monologue wraps each line in its own FB 06 ... FB 07 pair, with no speaker
  tag. Copy that.

### 5.4 Characters the encoder supports

- feat_text.py writes today: A to Z, a to z, 0 to 9, space, comma, period, apostrophe, line break, and the
  FB 06 / FB 07 pair (written "<" and ">").
- In the game's text but not in the encoder yet: "!" (0x24), "?" (0x25), "-" (0x26), the page break (FE),
  FC, and the color codes FB 03 and FB 04. Item 2 of docs/playtest-feedback.md already asks for "!", "?"
  and the speaker markup.
- Seen once or twice in vanilla, glyph not checked: 0x23 (double quote, around "Miss"), 0x5A (in "Jian"
  followed by three of it, likely a wave mark), 0x5B (in "Ta-daaaa"). Use only after an emulator check.
- Never present in the text, so treat as unavailable: parentheses, colon, semicolon, any dash other than
  the hyphen, ampersand, and the double quote until checked. Write around them.

## 6. Checklist for every new line

1. Every line is 30 characters or fewer, and the page has 4 lines or fewer (5 at most).
2. Only supported characters: letters, digits, space, . , ' ! ? and the hyphen. No parentheses, colons,
   semicolons, dashes or quotes.
3. Ellipses are exactly "..."; a silent turn is "..." alone; "?!" never "!?"; no "!!!"; "!!" only for a
   shout; within the speaker's exclamation budget (1.4).
4. At most one capitalized stressed word per page.
5. Speaker tag on the first page of each turn; place names blue, key items in the item color.
6. Every fact is true in this game and agrees with the lines around it (times, who knows what).
7. Nothing the opening narration already said; no "as you know"; no self-introduction unless asked or
   meeting someone on screen (the one Jian aside excepted).
8. One new fact per page, at most 3 per conversation.
9. Sounds like the character card: address forms, contractions, line length, nickname rights.
10. No real-world references, period slang, slurs, body jokes, accents or profanity.
11. No joke inside a serious beat.
12. Spelling and names per section 4; "OK".
13. When rewriting an existing line, check what the Japanese says first.

## Appendix: drafts for feedback item 2 (DRAFT, for Jeff's approval)

Both are checked against the rules above; every line is 30 characters or fewer. Each block is one page;
the first line of a page in a new turn is the speaker tag.

### Wake-up call (Cherenkov, off-screen)

Problems with the current draft: "an hour ago" contradicts Lucia's next scene, where she says she has been
waiting 3 hours; otherwise it already fits the rules.

DRAFT A, the current draft corrected (keeps the established USA joke):

```
Cherenkov
JIAN! You alive up there?!
Lucia left hours ago!
```
```
Jian
...Huh? Hours?!
```
```
Cherenkov
I wish I could afford to
oversleep every day!
Get moving!
```
```
Jian
I'm up! I'm up!
```

DRAFT B, closer to the Japanese (gruffer, "again" as the running gag) and setting up a payoff: in script
001 Cherenkov later promises to keep Jian's room free while he is away rescuing Lucia.

```
Cherenkov
Jian! Overslept again?!
Lucia headed out hours ago!
```
```
Jian
Wha...? She left already?!
```
```
Cherenkov
Keep this up and I'll rent
your room to someone who
actually gets up!
```
```
Jian
I'm up! I'm up!
```

Either way, Cherenkov's lobby line ("Finally, you grace us with your presence...") loses its joke and
needs a new short line or none (as the feedback item already notes).

### Jian's aside during the run

Problems with the current draft: "courier" repeats the opening narration; "Searis" should be "Port
Searis" (and blue); one line runs two sentences together. The structure and the closing joke work.

DRAFT A, the Hiro order (situation, name, partner joke, new facts, self-deprecating end), with the crush
as the last beat:

```
Oh, hey. Didn't see you there.
Name's Jian. I deliver for
Gad's Express. Fastest legs
in Port Searis...
```
```
...when I'm awake, anyway.
```
```
The girl who didn't wait?
That's Lucia, my new partner.
She's great.
Don't tell her I said that.
```

DRAFT B, shorter, built on two established traits (she hates waiting, he oversleeps), and moving the
handstands here since the intro trim drops "who loves acrobatics":

```
Oh! Hi. Bad timing, sorry.
I'm Jian. I carry packages
for Gad's Express, and I do
a mean handstand.
```
```
Lucia's my new partner.
She hates waiting.
I hate mornings.
Guess which one of us is late?
```

Notes for both: shown in the alternate color with no speaker tag (section 5.4), like the vanilla
monologue; "Port Searis" in blue. The handstand used to pay off in the curse scene (script 005, "No
standing on my head!"), which design 11 removes, so it is flavor only now.
