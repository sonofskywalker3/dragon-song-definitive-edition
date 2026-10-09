# Character bible (draft for Jeff, 2026-10-09)

Material to think against while playing, not decisions. Every chapter keeps two things apart:

- **As written**: what the game's text says, cited the way docs/story-characters.md cites it (`004 #48` is
  script 004, message op 48 in `uv run python -m dsde.text_dump`; `018 leaf 0x5858` is a party chat line,
  row numbers from docs/re-party-chat-japanese.md section 3). Japanese is glossed in our own translation.
- **Suggested**: proposals, labeled as such. Nothing suggested here is in the game or decided.

Sources: docs/story-characters.md (the survey; read it for the full evidence), docs/story-npcs.md (what
the townsfolk say about each character, the fluff gates, and the NPC translation changes), docs/re-party-chat-japanese.md
(the chat lines and their voices), docs/story-party-timeline.md (who is in the party when), docs/design.md
section 11 (the curse decision), docs/intro-analysis.md and the shipped prologue (`PROLOGUE` in
src/dsde/feat_text.py), docs/re-opening.md and src/dsde/feat_opening.py (the shipped wake-up and run),
docs/style-rules.md (the draft voice cards this bible extends).

---

## Preface: the rewrite in one page

### The working premise

Lunar: Dragon Song has a decent plot and a cast that the text mostly tells us about instead of showing.
The rewrite keeps the plot and makes the people real, mostly through Tales-style party chat on the Y button,
plus a small number of rewritten cutscenes where the plot itself needs it. Jeff's words: "good at
handstands" is a skill, not a trait; it does not help us connect with Jian.

In one sentence: **a courier who wants to prove humans are worth as much as beastmen, while privately
holding beastmen in contempt, chases the partner he promised to protect across a world that a fallen
Dragonmaster wants to rule alone, and learns from the friends he keeps trying to leave behind that nobody
has to carry the world by themselves.** That last clause is already the game's own thesis: Althena's
"Each of you are already, in your own way, just as powerful as I ever could be" (021 #32) and Titus's
"Happiness does not lie in control by an all-powerful, all-seeing being" (026 #2). The rewrite's job is to
make Jian, not the goddess, the one who arrives there.

### The rules

0. **Canon (Jeff, 2026-10-09).** Only Lunar 1 and Lunar 2 are canon, Japanese preferred over English. Every
   other release (Silver Star Story, Eternal Blue Complete, Legend, Harmony, Walking School, Magic School
   Lunar, and Dragon Song itself) is judged by its fidelity to the world of those two: where it contradicts
   them, canon wins; what does not contradict them is flavor we may borrow. Working timeline: Althena brought
   humans about 1,000 years before Lunar 1; Dragon Song is about 500 years before Lunar 1 and is the Vile
   Tribe exile Lunar 1 remembers (docs/research-lunar-lore.md).
1. **Keep the plot.** The route, the dungeons, the bosses, Lucia's capture, Rufus's death, the four trials,
   the airship, the Chamber of Rebirth. Nothing in this bible needs a new dungeon.
2. **Cut the fluff.** Errand chains that send you to the innkeeper, then a random NPC, before the story
   moves are shortened; a skit's hint should send the player straight to the next real step.
3. **Cut the curse** (docs/design.md section 11). The chapter "The curse" below lists what it carried and
   what can carry it instead.
4. **One hint per skit**, concrete, naming the place or person. A skit is character first and errand last:
   the hint is the closing line, never the subject. A skit that has nothing to hint still ends on the
   current goal.
5. **The party changes Jian.** Dragons and priests may state lessons; only the cast may teach them. Every
   change in Jian should come from a skit or scene with Gabryel, Lucia, Flora, or Rufus first, and a dragon
   second (if at all).
6. **The Japanese silences stay silences** unless there is a reason. Where the Japanese gives Jian
   "…………。" and the English filled it with "...That's right." or "...Yes." (rows 4, 7, 21, 49, and 56 of the
   chat comparison), the silence is the point. A rewrite may break one only to land a beat the silence was
   holding back, and then only once.
7. **The Japanese is a baseline, not a target**: what each hint must say, and how each person sounds
   (Jian's rough オレ, Gabryel's prim あたし, Flora's country あたい, Ignatius's royal 余). Where the English
   added a joke at someone's expense, assume it goes.
8. **Mechanical limits** (docs/re-party-chat.md sections 6 and 9): up to 3 speakers per skit, and only
   party members who are in the party at that moment (Jian, Lucia, Gabryel, Flora, Rufus; nobody else can
   speak in a skit); up to 5 lines of 30 characters per box; YES/NO is the only choice, A or B, and both
   answers rejoin at the hint; **28 choice flags, so 14 two-sided choices in the whole game**. A choice
   that only changes a later skit is cheap; one that changes a cutscene needs a script edit. The choice
   ledger at the end counts every choice proposed here.

### How each chapter is laid out

1. In one line. 2. Want, need, wound, lie. 3. Voice: rules and three new sample lines. 4. Arc, beat by beat
in story order, each marked **exists**, **told not shown**, or **to create**. 5. Relationships. 6. Skit
ideas. 7. Open questions for Jeff, each with a recommendation.

Story order is not script order. For reference: Port Searis (001), Thieves' Woods and Perit (002, 003),
Delrich Temple and Healriz (003, 004), San Coliseum (005), Port Olbeage (007), Cathedral of Althena and the
arrest (015), Zethos Castle (009), Leephon and Pisarno Square (008), Sungrid Bridge (016), Underground Tunnel
and Lind (010), Sandra Desert (019), Elda Canyon (020), Vile Castle and the Grand Hall (021), home to Port
Searis (001), Zethos (009), Titus (004), the Red, White, Black, and Blue Dragons (017, 006, 022, 023), the
airship (024, 025), the return to Vile Castle and the Chamber of Rebirth (021), the ending (026).

---

## 1. Jian Campbell

### 1.1 In one line

**As written:** a cocky, kind courier who wants beastmen to respect humans (004 #48), then wants only
Lucia back (010 #63), and keeps trying to do both alone (019 #0, 025 #15).

**Suggested:** the player's stand-in, who thinks he has to earn his place by winning, and learns from the
friends he keeps sending home that he never had to.

### 1.2 Want, need, wound, lie

**As written.**

- **Want:** first, to prove humans are no less than beastmen ("If I can display the bravery and strength
  of a human in front of so many beastmen... You may rethink your ideas about humans", 004 #48; "I'm gonna
  show them all that humans are no different from beastmen!", 005 #57). After Sungrid Bridge, Lucia and
  nothing else ("I don't care about this Ignatius guy. But I must save Lucia, no matter what!", 010 #63).
  Becoming a Dragonmaster is only a means ("I haven't decided that yet...", 018 leaf 0x5f5c).
- **Fear:** failing to protect her ("I failed to protect her, Gad! I'm not worthy of her gifts...",
  001 #22). Nothing for himself.
- **Need, wound, lie:** not on the page. The text gives him no family, no hometown, and no reason he is a
  courier (story-characters.md 1.4).

**Suggested.**

- **Need:** to let other people carry part of the weight, and to see the beastmen he resents as people.
  These are one lesson, not two: both are "you are not the only one who counts".
- **The lie:** "Humans are worth something only if they win." He says humans and beastmen are equal, but he
  sets out to *prove* it in a beastman arena by beastman rules (004 #45, #48), which concedes the beastmen's
  measure. The same lie makes him go it alone: if worth is earned by winning, nobody can win it for you.
  Gabryel holds the truth from her first line, "But aren't humans and beastmen the same? Both blessed by
  Goddess Althena" (005 #68): no proof required.
- **Wound** (Jeff's choice; each is one or two told lines in a skit, never a flashback):
  - **A. The kid the beastmen laughed at.** He grew up in Port Searis running errands for beastman traders
    who called humans frail (the shipped prologue's own word: "small and frail"). Explains the contempt
    (009 #13, #19) and the need to prove himself in the Coliseum. *Cost:* almost none; it fits every
    existing line. It makes beastmen look like bullies until Gabryel and Rufus correct it, which is the
    point.
  - **B. Nobody's son.** No family; Cherenkov's room and Gad's job are the only home he has (001 #57,
    011 #16). He protects people because being needed is the only belonging he knows. *Cost:* none, and
    it explains why the ending must bring him home to someone. It does not explain the beastman edge.
  - **C. A partner he lost.** Before Lucia, a delivery went wrong and someone got hurt because he ran
    ahead. *Cost:* invents an offscreen victim and duplicates Gabryel's wound (her dead recruits, 009 #13);
    two characters with the same wound weaken each other.
  - **Recommendation:** A and B together, one line each (skits 1.6.2 and 2.6.3). Skip C: Gabryel owns
    that wound.

### 1.3 Voice

**As written** (story-characters.md 1.2; style-rules.md 3.1): eager and cocky, short lines, stiff
formality with elders and kings ("Then we will head straight over there.", 003 #56). Japanese: rough オレ,
sentence-final ぜ, くそっ when thwarted, polite です/ます to elders ("I don't want to watch. I want to fight",
004 #45), and silences written as silences.

**Suggested rules.**

1. One or two lines a box. Resolve is one sentence, never a speech.
2. Contractions always; "I've got to", never "I must" (the English overuses it).
3. Polite with elders, kings, and dragons, rough with everyone else, and the switch is audible: "sir",
   full sentences, no slang. The Japanese does this; it says he was raised to know his place.
4. His metaphors come from the job: packages, routes, schedules, being late, signing for things.
5. Hurt or ashamed, he says "..." and nothing else. He never fills a silence with agreement.
6. He never says out loud what Lucia is to him before the Chamber of Rebirth. He teases her, worries about
   her, and goes quiet; other people say the rest (Marcella, Flora, Gabryel).
7. Early on, "you beasts" slips out under pressure (009 #19). After Rufus he says "beastmen", and then
   names: "Rufus", "Leoncavallo". The change in his nouns is his arc in miniature.
8. He is not the joke-teller; he reacts. His own jokes are at his own expense (the oversleeping).

**Three sample lines** (new, not in the game):

- To Lucia in Thieves' Woods: "Relax. I've outrun Cherenkov with a breakfast tray. A thief's nothing."
- To Zethos: "I'm not asking you to like humans, sir. I'm asking you to watch."
- To Gabryel, back home after the Grand Hall: "She told me to run. ...And I ran."

### 1.4 Arc

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | Carefree, late, sweet on his partner | exists (001 #140; the shipped wake-up and run) | Port Searis |
| 2 | Volunteers before he is asked; the thief chase | exists (003 #56) | Thieves' Woods, Perit |
| 3 | Why he wants the tournament: humans are no less | exists, but said to Leoncavallo (004 #48); Lucia gets only a hint line (row 82) | Healriz; skit 1.6.2 |
| 4 | Wins, and is jeered anyway | exists (005 #57) | San Coliseum |
| 5 | Why he goes to Leephon | **to create** (was the curse, 005 #71) | Healriz, after the Coliseum; chapter "The curse" |
| 6 | Contempt for beastmen spoken in anger ("glad I wasn't born a beastman") | exists (009 #13) | Zethos Castle |
| 7 | Lucia taken; his want narrows to her | exists (016, 010 #62, #63) | Sungrid Bridge, Underground Tunnel |
| 8 | Refuses Rufus in front of everyone | exists (010 #62) | Underground Tunnel |
| 9 | Sends the girls away, goes on alone | exists (019 #0) | End of Sandra Desert |
| 10 | Saved by Rufus and Gabryel; Rufus's unfinished sentence | exists, cut off (020 #6) | Elda Canyon |
| 11 | Hears Rufus out, before Rufus dies | **to create** | Vile Castle; skit 5.6.5 |
| 12 | Crushed by Ignatius; saved by Lucia's word | exists (021 #4 to #12) | Grand Hall |
| 13 | Breakdown, and Lucia's gift | exists (001 #17 to #29) | Gad's Express |
| 14 | Zethos apologizes for the beastmen; Jian answers with "most beasts, well..." | exists (009 #19, #20) | Zethos Castle |
| 15 | Jian's own reckoning with his contempt | **to create** | skit 1.6.5, and one line to Zethos |
| 16 | The four trials, each a lesson | told, not shown (006, 017, 022, 023: each dragon states it) | after each trial, a skit where the party shows it |
| 17 | Dark Jian: the boss who is him | exists as a fight, no words around it | Black Dragon Cave; skit 6.6.4 |
| 18 | The Blue Dragon's lesson: listen to companions | told, then broken one scene later (023 #21, 025 #15) | **to create**: the airship scene honors it (skit 1.6.7) |
| 19 | Gives up the rings; "circle of hatred" | exists (021 #26, #28) | Chamber of Rebirth |
| 20 | Answers Ignatius's "love takes" himself | **to create** (Althena answers instead, 021 #32) | Chamber; chapter "Ignatius and the final fight" |
| 21 | Fights Ignatius, with everyone | **to create** | Chamber |
| 22 | Reaches for Ignatius; "who did I save?" | exists (021 #38, #40) | Chamber |
| 23 | Comes home and meets Lucia again | **to create** (Jian is absent from the ending, 026 #3) | Port Searis; chapter "Jian and Lucia" |

### 1.5 Relationships

**Lucia.** As written: 55 shared messages, almost all about the job or his recklessness; the promise is
stated twice (004 #81, 010 #62) and never shown; everything romantic is said by others or added by the
English (story-characters.md 1.2 and 8). To build: see the chapter "Jian and Lucia".

**Gabryel.** As written: the real partnership, 121 shared messages; she manages him and pulls him out of
despair (001 #26, #143), and they disagree about the game's theme without either noticing (005 #68 against
009 #13). To build: let them notice. Gabryel is the one who names his contempt to his face, once, kindly,
and the one he apologizes to first. After Lucia is gone, she is the person he talks to at night. The
Japanese jealousy (004 #81, ちょっとやけるなァ) stays small and turns into friendship with Lucia, not
rivalry (3.5).

**Flora.** As written: she teases, he apologizes (023 #3, 024 #1), and in Japanese she alone praises him
("Jian... that's kinda cool?", 006 #8, 018 leaf 0x62a4). To build: he picked her as guide to spite Rufus
(010 #62); his arc with her is learning that she came because she wanted to see the world ("I just want to
see new places!", 018 leaf 0x5d28), not because he chose her, and that she does not need his protecting.

**Rufus.** As written: distrust, refusal, rescue, and farewell in 11 messages; the apology comes after
Rufus is dead, and to Gabryel (018 leaf 0x62a4). To build: one conversation before 021 #1 where Rufus
finishes his sentence and Jian answers it (skit 5.6.5). This is the single most valuable skit for Jian in
the game.

**Ignatius.** As written: 17 shared messages, all in script 021. Titus says they "resonate" (004 #82), and
every dragon calls Jian a possible Ignatius (006 #5, 022 #6, 023 #19). To build: the resonance, felt on
screen, early and often (chapter "Ignatius and the final fight").

**Zethos** (short). As written: taunt, contempt, apology (005 #57, 009 #13, #20). To build: Jian answers
the apology with one line in the post-Grand-Hall scene, owning his half instead of "most beasts, well...".

### 1.6 Skit ideas

Speakers are only party members present at that point (docs/story-party-timeline.md). Flags are the vanilla
stage flags from the chat table (docs/re-party-chat-japanese.md section 3); "replaces row N" means the skit
takes that vanilla hint's slot (`chain=HINT`).

1. **Fountain Square, met Lucia (flag 0xB; replaces row 96).** Lucia will not say where she was this
   morning. She was at Gad's, leaving his anniversary gift (001 #20: exists, never shown). Jian guesses
   wrong three times. *Beat:* she has a secret, and a happy one; it plants the gift. *Hint:* "We have to
   pick up the [package] at Gad's Express, or the delivery will be late!" (the corrected row 96).
2. **Healriz, why the tournament (0x195; replaces row 82).** Jian tells Lucia about the beastman traders
   who laughed him off a job when he was a kid (wound A). Lucia: "So this isn't about the prize." *Beat:*
   his want and its crooked root. *Hint:* Leoncavallo runs the tournament; find him.
3. **Healriz, after the Coliseum (the stage after the tournament).** He won, and the crowd jeered anyway
   (005 #57). Lucia: "You wanted them to cheer." Jian: "...". *Beat:* winning did not buy what he wanted.
   *Hint:* the next step toward Leephon (whatever replaces the curse; chapter "The curse").
4. **Thieves' Woods at night (on 0x1C, off 0x14).** Lucia hates being out after dark (001 #140). Jian walks
   on the side of the path nearer the trees without saying so. *Beat:* the protecting instinct, shown small.
   *Hint:* the thief ran toward {Perit Village}. **Choice (cheap):** Lucia: "Are you walking on that side
   on purpose?" YES: he admits it; she says nothing and takes his sleeve. NO: he claims it is shorter; she
   lets him have it. *Later:* one line of skit 2.6.8 at Sungrid Bridge differs. Choice 1 in the ledger.
5. **Underground Tunnel, after Rufus is refused (0xCB).** Gabryel: "That was about him being a beastman."
   Jian: "It was about Lucia." Flora, quietly: "It was a little about him being a beastman." Jian: "...".
   *Beat:* the contempt named by two people at once, and he has no answer yet. *Hint:* through
   {Guystole Mine} to {Lind Village}.
6. **Elda Canyon area 1, alone (0xCC; replaces row 53).** Jian's inner voice only. He rehearses what he
   will say to Gabi when he sees her again and gets it wrong three times. *Beat:* he already knows leaving
   them was wrong, which makes the rescue in 020 land as relief, not surprise. *Hint:* {Vile Castle} lies
   past {Elda Canyon}.
7. **Before the airship (0x13A).** Jian, to Gabryel and Flora: "The Blue Dragon said to listen. So... I'm
   asking. Not telling." *Beat:* the lesson holds. The airship cutscene then drops its fourth ditching
   attempt (025 #15) and keeps Flora's fear and "I'll hold it together with my teeth!" (025 #17).
   *Hint:* "If the XR45 Sakura flies, we can get straight to {Vile Castle}" (row 11). Not a choice: the
   player should not be able to choose the old flaw back.
8. **Back from the Frontier, Gad waiting (0xC9; replaces row 49).** Gabryel: "Come on. Gad's holding a
   [package] for you." Jian: "......" (the Japanese silence, kept). Gabryel says nothing more. *Beat:*
   grief without words. *Hint:* the package is waiting at Gad's Express.
9. **Final dungeon, the last fight ahead (0x1A9; replaces row 6, "Face it with a smile or tear").** Jian
   thanks each of them by name, badly. Flora: "You're doing the thing where you say goodbye." Jian: "I'm
   not. ...I'm saying I'm glad you came." *Beat:* the go-it-alone flaw, finished. *Hint:* Ignatius is in
   the {Chamber of Rebirth}.

### 1.7 Open questions for Jeff

1. **The shipped run says "Lucia and I haven't been partners long"; the game says they met over a year ago
   (001 #83) and stages the anniversary (001 #21).** Both can be true: they met a year ago and have worked
   together only a few months ("recently teamed up", 001 #81). *Recommendation:* keep the run line and make
   the first meeting predate the partnership (12.1 A). Change it only if you pick a first meeting where
   they were partners from day one (12.1 B).
2. **Which wound: A, B, or C?** *Recommendation:* A and B, one told line each.
3. **Is Jian a Dragonmaster at the end?** The text leaves it open (021 #26, 026 #4). *Recommendation:* no.
   He gives the rings away and the party wins together; the closing narration's "one day... Dragonmaster"
   stays about the future.
4. **Handstands: cut them, or keep one?** With the curse gone they carry nothing. *Recommendation:* keep
   one. On the airship, Flora asks him to do a handstand on the deck to take her mind off the height, and he
   does. A skill used for someone else becomes a trait.
5. **Does Jian ever say "I love you"?** The English adds it at 021 #32; the Japanese has only her name.
   *Recommendation:* never in those words. He says it in the reunion by what he does (chapter "Jian and
   Lucia").

---

## 2. Lucia Collins (and Althena)

### 2.1 In one line

**As written:** Jian's worried, punctual partner who scolds him, defends him once like a lion (009 #47 to
#52), is taken at Sungrid Bridge, and turns out to be the Goddess Althena in hiding (004 #80).

**Suggested:** a goddess who put the world down for a year to find out what one ordinary life is worth, and
who decides, at the end, that it is worth choosing again.

### 2.2 Want, need, wound, lie

**As written.**

- **As Lucia:** no want beyond doing the job well and keeping Jian in one piece ("If we don't get going
  soon, we won't make it back before sunset!", 001 #140; "Our careers are finished!", 002 #1). Small
  likes: flowers (001 #109, 003 #44), a parasol (004 #101), fireplaces ("They're so romantic", 001 #118),
  fountain wishes (004 #115). A fear: being out at night (001 #140). Bad at cooking by her own account
  (001 #39; the "Charcoal Surprise" running joke is English-only, story-characters.md 2.2).
- **As Althena:** she doubted that one all-powerful being should rule and wanted the future entrusted "to
  all the people in the world" (004 #78); she hid as a human, sealing her power and memories, to keep them
  from Ignatius (004 #80). Her thesis: "Each of you are already, in your own way, just as powerful as I ever
  could be" (021 #32). Titus: "This is not the first time that our Goddess has been reborn in such a way"
  (026 #1).
- **What the town knows** (docs/story-npcs.md 2.2): nothing about when she arrived, where she came from, or
  where she lives. The only dates are Jian's: met "over a year" ago (001 #83, the same in Japanese),
  partners "recently" (001 #81). Port Searis treats her as a local girl Jian looks after ("What with having
  to look after Lucia and all...", Isabella, 001 #103). In Japanese, Cherenkov sends Jian to "the usual
  place" (いつものところ, 001 #53): the fountain is their daily meeting spot. The English drops it.
- **The only person who sees the goddess** is Titus, and only in Japanese: he recognizes her on sight
  (あ　あなたは…！？, "You... you are...!?", 004 #67; English "You there, human girl!"), calls her あの方, the
  honorific "that person" (004 #73), and owns an album identical to hers (004 #95, #96)
  (docs/story-npcs.md 2.2 and 5).
- **Missing:** why she chose *this* life, a courier in Port Searis beside Jian. Jian begs her to remember
  it ("Remember why you chose to become Lucia!", 021 #24), and the game never answers.

**Suggested.**

- **Want** (Jeff's choice):
  - **A. One ordinary life, chosen.** Althena wanted to know whether the people she would hand the world
    to could carry it, and the only way to find out was to be one of them. Lucia's small wants (the
    parasol, the fireplace, the coin in the fountain) are that experiment from the inside: a person who
    wants things for herself, which a goddess never did. *Cost:* none; it turns her trivia into
    character, and gives 021 #24 its answer.
  - **B. To belong somewhere.** With her memory sealed, Lucia arrived in Port Searis a year ago with no
    past (the umbrella day, 001 #83). Her love of schedules and her fear of the dark are a girl holding on
    to the one routine she has. *Cost:* the text never says she has no past; it reframes her
    punctuality as anxiety, which is touching but heavier, and a sharp player may guess the secret early.
  - **C. To be needed by one person instead of everyone.** Simpler, more romantic, and narrows her to Jian.
    *Cost:* makes her want Jian's want, which is the problem the rewrite is fixing.
  - **Recommendation:** A as her want, with a light touch of B (she does not talk about before Port
    Searis, and nobody pushes).
- **Need:** for the ordinary life to be a choice and not a hiding place. In the Chamber, Althena chooses
  to become Lucia again knowing what it costs (her power, given away). That is her arc, and it already
  exists in outline (021 #32, 026 #2, #3); it only needs Lucia's half to have been built.
- **The lie (Althena's, before the game):** "The world needs me to carry it." She had stopped believing it
  (004 #78), which is why she left. **Suggested link:** this is Jian's flaw at the scale of a world, and
  Ignatius's creed. Lucia is the one of the three who already put the weight down. Jian learns it from his
  friends; Ignatius never does.
- **Wound (Althena):** the champion who turned on her when she said it out loud (chapter "Ignatius and the
  final fight"). Lucia herself needs no wound.

### 2.3 Voice

**As written:** English Lucia is a bossy, proper scold with sudden outbursts ("Jian, you moron! You loser,
you idiot, you fool!", 005 #63). Japanese Lucia is softer and more girlish: わたし, もう　ジアンったら… (a
fond "honestly, Jian..."), sulky elongations (ジアンのいじわるぅ！, 006 #0), a sing-song challenge to a king
(こたえは　ひとォつ！, 009 #50), and calls him わたしのジアン ("my Jian", 009 #49). Althena speaks formally
(ありません, なのです). Style card: Luna's warmth with a flash of temper (style-rules.md 3.2).

**Suggested rules.**

1. "Oh, Jian..." is her scolding opener, and it is fond, not sharp: the Japanese ったら, not the English
   "moron".
2. She worries in schedules: sunset, late, the delivery, the ferry. Worry is how she says she cares.
3. She notices pretty, small things out loud (a lamp, a flower box, a parasol) and then talks herself out
   of wanting them. That habit is the whole character in one tic.
4. Kind to strangers first, suspicious never. She asks people's names.
5. Up to three exclamations a page when delighted or frightened; none when she is serious.
6. Fierce for someone else, never for herself: she will challenge a king for Jian (009 #48) and never
   raise her voice for her own sake.
7. Nothing she says before the Grand Hall may confirm she is Althena. One unease is allowed, and vanilla
   already has it (the dragon statues, 018 leaf 0x52e0, row 89).
8. **Althena** speaks without contractions, in short, plain sentences: a person very old and very tired,
   not a priestess performing.

**Three sample lines** (new):

- In Perit: "Oh, Jian... You can't save the whole village before lunch. One thief. Then the package."
- At the Healriz fountain: "It's a silly thing to wish for. ...I wished for it anyway."
- As Althena, to Jian in the Chamber: "I carried this world alone for longer than it has had names. I am
  tired, Jian. Let me be one of you."

### 2.4 Arc

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | The first meeting under her umbrella, a year ago; the fountain as "the usual place" | told (001 #83; 001 #53 in Japanese only), never shown | skit or ending echo; chapter "Jian and Lucia" |
| 2 | She left early to drop off his anniversary gift | exists, hidden (001 #20) | the opening day; skit 1.6.1 plants it |
| 3 | Waits three hours, scolds, worries about sunset | exists (001 #140) | Fountain Square |
| 4 | Covers up the stolen package | exists (002 #1, 003 #13) | Thieves' Woods, Perit |
| 5 | Wants things for herself (parasol, fountain) | exists as trivia (004 #101, #115) | Healriz; skit 2.6.4 makes it a want |
| 6 | Tries to stop the tournament, then stands by him | exists (018 leaf 0x549c, 005 #61, #63) | Healriz, Coliseum; skit 2.6.5 |
| 7 | Befriends Gabryel | told after the fact ("my first friend", 025 #16) | **to create**: skits 2.6.6, 2.6.7 |
| 8 | Challenges the Beast King for Jian | exists, but its cause is the curse (009 #47 to #52) | Zethos Castle; new cause in "The curse" |
| 9 | Turns on Gabryel, then apologizes first | exists (009 #60, 008 #72) | Zethos Castle, Pisarno Square |
| 10 | Crosses Sungrid Bridge of her own accord | exists, from the villain's side (016 #7, "she crossed Sungrid Bridge of her own accord!") | skit 2.6.8: why she chose to go |
| 11 | Taken | exists (016) | Sungrid Bridge |
| 12 | Stops Ignatius killing Jian; her promise with him | exists, unexplained (021 #12) | Grand Hall; "Ignatius and the final fight" |
| 13 | Awakened as Althena; gives her power to everyone | exists (021 #24 to #32) | Chamber of Rebirth |
| 14 | Remembers something of Lucia in the Chamber | **to create** | Chamber (needs a 021 edit) |
| 15 | Reborn as Lucia, leaves with Titus | exists (026 #3), one line, no Jian | **to create**: the reunion |

### 2.5 Relationships

**Jian.** See the chapter "Jian and Lucia". In short: as written she worries and scolds; to build, she
wants something for herself and lets him see it, and the bond is shown in what each does for the other
without saying so.

**Gabryel.** As written: 18 shared messages. Gabryel saves her (005 #68), deceives her, is accused ("Gabi!
If that's even your real name?!", 009 #60), and is forgiven first ("It was cruel to say those things. I'm
sorry... And fight back next time, OK?", 008 #72). "My first friend" is said only after Lucia is gone
(025 #16). To build: the friendship before Sungrid Bridge, so the line lands. Two skits (2.6.6, 2.6.7):
Lucia is the first person who treats the princess as a girl her age, and Gabryel, who has only ever
recruited people, does not know what to do with that. The Japanese jealousy (004 #81) belongs to this
pair as much as to Jian: Gabryel likes them both and envies what they have.

**Flora.** As written: never in the party together, 0 shared messages. To build: one moment. Flora meets
Lucia only as Althena in the Chamber, and in the reunion. Suggested: in the ending, Flora is the one who
says the plain thing ("So you're Lucia. He talked about you every night.").

**Rufus.** As written: 2 shared messages, the arrest (015) and Sungrid Bridge, where her healing fails on
him (016 #2: "I'm trying! I am! But... it's not working?!"). To build: nothing new is needed. Lucia
kneeling to heal the beastman who arrested her, and failing, is already a good beat; one added line from
Rufus ("Why would you...") is enough.

**Ignatius.** As written: she made him promise to stop killing (021 #12) and he keeps it. To build: the
history between them (chapter "Ignatius and the final fight"). Lucia never meets him; Althena has known
him for an age.

**Titus** (short). As written: he explains her (004 #78 to #82) and walks with her in the ending (026 #1 to
#3). To build: nothing; he is her escort, not her friend.

### 2.6 Skit ideas

Lucia is in the party from Fountain Square (0xB) to Sungrid Bridge (0x1A1), with Gabryel from Healriz on
(0x34), except the arrest stretch (Jian and Lucia only). That is the only window.

1. **Package in hand (0x1C; replaces row 95).** Lucia plans the route out loud, sunset included. Jian:
   "You've planned this since breakfast." Lucia: "Since last night." *Beat:* the schedule is how she cares.
   *Hint:* through {Thieves' Woods} to Gad's Express in {Perit Village}.
2. **Perit Village, Enos busy (0x193 and 0x1D; replaces row 92).** Lucia asks a frightened villager's
   name before she asks what happened; Jian notices. *Beat:* kind to strangers first. *Hint:* something is
   wrong in {Thieves' Woods}; go look.
3. **Delrich Temple, the dragon statues (0x194; keeps row 89's hint).** Lucia: "Something about those four
   statues... I feel like I should know them." Jian: "You've never been here." Lucia: "I know." Jian, to
   change the subject, says the one thing about himself he never says: that Cherenkov's room is the only
   home he has had (wound B). *Beat:* her unease (allowed, vanilla has it) and his trust. *Hint:* the
   statues are a puzzle; turn them.
4. **Healriz, the parasol (0x38, Marcella named; replaces row 81).** Lucia admires the parasol (004 #101)
   and adds up what a courier earns in a month. **Choice 2 (needs the ending edit):** Lucia: "Should I buy
   it?" YES: she does, and is giddy and guilty. NO: "Someday, then." *Later:* in the reunion, YES means
   she is carrying it when Jian finds her; NO means Jian brings it. *Hint:* go and see what Marcella
   has to say (row 81).
5. **Leoncavallo's offer (0x3B; replaces row 78).** Keep her "No way, Jian!" and add the turn: when he
   will not budge, she makes him promise to come back in one piece. Jian: "That's my line." Lucia: "Not
   today." *Beat:* the promise runs both ways (chapter "Jian and Lucia"). *Hint:* the [Armored Boar] is
   somewhere in {Roland Forest} (the corrected row 77 wording).
6. **Gabryel joins, the ferry (0x34; replaces row 74).** Gabryel gushes about the champion; Lucia, too
   polite to be rude, asks Gabi what *she* fights for. Gabryel has no answer ready. *Beat:* Lucia is the
   first to ask Gabi about Gabi. *Hint:* to {Leephon City}, take the ferry from {Port Searis} (the
   corrected row 74).
7. **Leephon, the fuss (0x66; replaces row 73).** Lucia and Gabryel gang up on Jian for the first time
   (his table manners at the ferry). Gabryel laughs, surprised at herself. *Beat:* the start of "my first
   friend". *Hint:* something has happened at {Port Olbeage}.
8. **Sungrid Bridge (0x1A1; replaces row 59).** The last skit with Lucia. Gabryel scouts ahead; Lucia and
   Jian stop at the rail. She tells him she has something waiting for him at home and will not say what
   (the gift). If choice 1 was YES, she adds: "Walk on my side on the bridge, OK?" **Choice 3 (needs a
   021 edit):** Lucia: "Jian... are you scared?" YES: "Me too. Good. Then we'll be careful." NO: "Liar."
   *Later:* in the Chamber, before giving her power away, Althena says the matching line back, which is
   how Jian (and the player) know Lucia is still in there. *Hint:* past the bridge is the {Frontier}; keep
   your guard up. *Why she crosses:* she chose to (016 #7); this skit is where she says so ("Gabi needs us.
   And you'd go without me.").
9. **Zethos Castle aftermath, find Gabi (0x7C; replaces row 61).** Lucia rehearses her apology to Gabryel
   with Jian, and it is terrible. Jian: "Just say sorry. And mean it." *Beat:* she apologizes first because
   she wants Gabi back, not because she was wrong. *Hint:* Gabi goes to {Pisarno Square} when things get
   too much (009 #24).

### 2.7 Open questions for Jeff

1. **What does Lucia want: A (one ordinary life, chosen), B (to belong), or C (to be needed)?**
   *Recommendation:* A, with a light touch of B.
2. **Does the reborn Lucia remember Jian?** The text does not say (026 #3). *Recommendation:* not at
   first. She remembers the city and the job and not him, and the reunion is her choosing him again
   anyway. Remembering at once is warmer; not remembering lets the ending repeat the first meeting.
   Your call; it decides the ending scene.
3. **Can Lucia hint at what she is before Sungrid Bridge?** The style rules say no (style-rules.md 3.2);
   vanilla already does once (row 89), and the Japanese Titus does it for her (004 #67, #73, the album at
   #95). *Recommendation:* one unease of her own in Delrich Temple (skit 2.6.3), plus the Titus
   foreshadowing restored (9.2); nothing else.
4. **The cooking gag:** her own admission (001 #39) is in both versions; Jian's "Charcoal Surprise" jabs
   are English-only. *Recommendation:* keep her admission, drop his jabs.
5. **Why does Lucia go to the Frontier?** The game never says; Ignatius notes she chose to (016 #7).
   *Recommendation:* she goes because Gabi needs them and Jian would go without her (skit 2.6.8).

---

## 3. Gabryel Ryan ("Gabi")

### 3.1 In one line

**As written:** the Beast King's daughter, traveling as a commoner, who recruits fighters for her father's
war, has watched every one of them die, and decides for herself at last (008 #73).

**Suggested:** the second lead. The one who believes humans and beastmen are equal without needing it
proved, and who has to learn that believing in people does not make her responsible for their deaths.

### 3.2 Want, need, wound, lie

**As written** (the only cast member with all of it on the page, story-characters.md 3.1):

- **Want:** no more of her recruits to die ("from the moment she declared that she would allow no more
  casualties, she went looking for truly strong warriors", 009 #13); to decide her own future ("I'm not
  going to do my father's bidding any longer", 008 #73); to save Lucia, "my first friend... And my first
  true comrade!" (025 #16).
- **Fear:** losing companions ("fears letting your guard down more than anything... Because she knows what
  may happen if you don't", 009 #13).
- **Wound:** "Each time, I have watched my daughter fall into a deeper depression at the loss of those she
  has helped gather" (Zethos, 009 #64). Pisarno Square is "where she goes when things get too much"
  (009 #24).
- **Conviction:** "But aren't humans and beastmen the same? Both blessed by Goddess Althena" (005 #68).

**Suggested.**

- **Need:** to stop counting people as losses she caused. She chose them; they chose to go.
- **The lie:** "If I pick well enough, nobody dies." It is why she is strict in battle (009 #13), why she
  looked for "truly strong warriors", and why Rufus's death (021 #1) should hit her hardest of anyone: he
  is the one fighter she did not recruit, and he died anyway, by choice.
- **The gap the text leaves** (story-characters.md 3.4): why recruit a human, weaker by her own world's
  rules, after promising no more deaths? **Suggested answer** (Jeff's choice):
  - **A. She saw him get up.** At the Coliseum, Jian was knocked down and got up again, every round.
    Her strong beastmen never got up. She is not recruiting strength; she is recruiting stubbornness. (A Port Searis NPC already has the
    proverb in Japanese, ななころびやおき, "fall seven times, get up eight", 001 #129, mistranslated as "An eye
    for an eye", docs/story-npcs.md 5; it could come back in Gabryel's mouth.)
    *Cost:* none; fits Zethos's "I can see where your initial interest in these two must have come from"
    (009 #58) and design 11's fan act.
  - **B. She wanted to be wrong about her father.** She half wants a human to prove Zethos's world wrong.
    *Cost:* makes her more political; slightly undercuts her fan act being sincere.
  - **Recommendation:** A, said once, late (skit 3.6.5), when she finally tells Jian why it was him.

### 3.3 Voice

**As written:** English: brisk, bossy, sarcastic, with American tough-girl slang added ("bub", "muscle
head", "moron boy"). Japanese: あたし, feminine わ, わよ, かしら, a prim upper-class streak (ごめんあそばせ〜,
"pardon me~", 018 leaf 0x564c), and a schoolgirl's ジアンのバ〜カ！ (019 #0). She is a princess pretending to
be a commoner, and the Japanese lets it show. Style card: Jessica's tongue, Jean's hidden side
(style-rules.md 3.3).

**Suggested rules.**

1. Quick, confident, direct. Gives orders in a crisis without raising her voice.
2. She owns the nicknames ("muscle head", "dunce", "bow girl"); nobody else in the party invents them.
3. The princess leaks: under stress or when showing off, a mock-grand phrase slips in ("Toodle-oo!",
   "Do try to keep up"). Replace the English "bub" with this, which is what the Japanese does.
4. Flirting is playful and self-assured, never crude, and never runs Lucia down.
5. "Papa" always, played straight. When she talks about her father she stops joking.
6. About her dead recruits she is brief and specific: a name, one detail, then a change of subject.
7. No cruelty to Flora. Teasing targets an established trait (Flora's appetite, her bravado), and Gabryel
   cares more than she says (the Japanese notices Flora's tears, 024 #2).
8. She says sorry rarely and fully, once, then is done.

**Three sample lines** (new):

- To Jian at the Olbeage checkpoint: "Watch and learn, muscle head. Royalty is mostly posture."
- About her recruits, at Pisarno Square: "Benno. He laughed at everything. He laughed at the bridge."
- To Flora on the airship: "Hold my hand, bow girl. Not because you're scared. Because I am."

### 3.4 Arc

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | Rescuer with a creed ("aren't humans and beastmen the same?") | exists (005 #68) | Healriz, after the Coliseum (the blast is cut with the curse: needs a new staging) |
| 2 | Fan of the champion; the challenge as her reason to bring him | **to create** (design 11) | Healriz; chapter "The curse" |
| 3 | Charm and authority at the checkpoint | exists (007 #78 to #80) | Port Olbeage |
| 4 | Separated at the arrest | exists (015) | Cathedral of Althena |
| 5 | Exposed by her father; collapses ("Papa, I can't do this any more!") | exists (009 #61) | Zethos Castle |
| 6 | Forgiven; "decide my future for myself" | exists (008 #72, #73) | Pisarno Square |
| 7 | Friendship with Lucia, before it is lost | told after (025 #16) | **to create**: skits 2.6.6, 2.6.7 |
| 8 | Suspects Lucia's secret | exists (010 #60) | Underground Tunnel |
| 9 | Refuses to be left; comes back with Rufus | exists (019 #0, 020 #4) | Sandra Desert, Elda Canyon |
| 10 | The race speech ("We're friends now! Comrades!") | exists (020 #6) | Elda Canyon |
| 11 | Rufus dies holding the line; her wound reopens | exists as event (021 #1), her grief unshown | **to create**: skit 3.6.6 |
| 12 | Restarts Jian after the Grand Hall | exists (001 #26, #143) | Port Searis |
| 13 | Father and daughter, with honesty this time | exists in part (009 #17 to #20, #69 to #71) | Zethos Castle; skit 3.6.7 |
| 14 | Tells Jian why it was him | **to create** | skit 3.6.5 |
| 15 | The steady one through the trials | exists (013 #22, 023 #19) | Dragon caves |
| 16 | "My first friend" | exists (025 #16) | Before the airship |
| 17 | What she does after | **to create** (no word in the ending, story-characters.md 10) | Ending: one line |

### 3.5 Relationships

**Jian.** As written: 121 shared messages; she scolds, steers, and restarts him. They disagree about the
theme (005 #68 against 009 #13) without knowing it. To build: the disagreement, spoken. Gabryel names his
contempt once (skit 1.6.5) and does not repeat it; he comes to her when he has worked it out (skit 3.6.6).
The Japanese jealousy (004 #81, and her protectiveness of Lucia in 018 leaf 0x5858) is real but small:
she likes him, she sees what he has with Lucia, and she chooses to guard it. Design 11's flirting
supplies the first half; the second half is the Lind skit (3.6.4).

**Lucia.** See 2.5. To build: two skits of friendship before Sungrid Bridge, so that "my first friend"
(025 #16) is something the player watched happen.

**Flora.** As written: 87 shared messages, bickering sisters; the English adds cruelty ("your quiver is a
few arrows short", 018 leaf 0x5cbc). To build: big sister, not bully. Gabryel teases Flora's bravado and
quietly makes room for her fear (the airship, 024 #2). The English jabs go.

**Rufus.** As written: 5 shared messages, "my lady". To build: he is the kind of fighter she used to
recruit and lose, and the one who chose to come on his own. One exchange at Elda Canyon where she tries to
send him back and he refuses, which is exactly what she does to Jian (skit 5.6.3).

**Zethos.** As written: father and daughter in two scenes, then dropped (009 #17 to #20, #58 to #71). To
build: one honest scene after the Grand Hall, where she tells him she left without a word and he tells her
he knew (skit 3.6.7).

**Ignatius.** As written: none beyond being in the room. To build: she has buried his victims for years;
she has a right to hate him and the party should hear her say so once.

### 3.6 Skit ideas

1. **Healriz, after she joins (the stage replacing the curse).** Gabryel lists Jian's Coliseum fights from
   memory, round by round. Lucia: "You were watching closely." Gabryel: "I watch everyone closely."
   *Beat:* the fan act, and the recruiter underneath it. *Hint:* the Beast King's challenge is answered in
   {Leephon City}; the ferry leaves from {Port Searis}.
2. **Port Olbeage, the checkpoint (0x75; replaces row 72).** Gabryel, before she sweeps through: "Let me
   handle this. And don't look surprised." *Beat:* the princess she is hiding. *Hint:* check the
   checkpoint.
3. **Cathedral of Althena, Vile Tribe (0x76; replaces row 70).** Jian offers to let "you two" wait outside.
   Gabryel, in the Japanese register: "If you mean me, you've got the wrong girl. I wasn't raised that
   soft. Toodle-oo!" (the corrected row 70). *Beat:* she will not be protected. *Hint:* into the
   {Cathedral of Althena}.
4. **Lind Village, Flora's question (0x1A5; replaces row 56).** Flora: "You two are a couple?" Gabryel's
   denial is fast and then careful: "Think how that would make Lucia feel. Jian and Lucia are..." Jian:
   "......" (the Japanese silence). Gabryel, after a beat, to Flora: "We're getting her back. Both of us."
   *Beat:* the jealousy acknowledged and put away for a friend. *Hint:* stock up in {Lind Village} before
   the {Sandra Desert}.
5. **The Red Dragon's trial passed (0x62; replaces row 41).** Flora asks Gabi why she picked a human of all
   people. Gabryel answers honestly for the first time: "He kept getting up." (2.2 option A). Jian is not
   in the conversation; he is listening. *Hint:* the {White Dragon Cave}: start at {Delrich Temple}.
6. **After Lucia's gift, on the way to Leephon (0x42; replaces row 48).** Gabryel, alone with Jian, says Rufus's name and one thing about him she learned too late.
   Then: "I didn't recruit him. He came anyway." *Beat:* her lie cracks: you cannot pick well enough.
   *Hint:* "Papa will be in {Zethos Castle}" (row 48). **Choice 4 (cheap):** Gabryel: "Do you hate them?
   Beastmen, I mean." YES: Jian: "I did. I think I did." NO: Jian: "...Not the ones I know." *Later:* the
   Zethos scene's new Jian line (1.5, Zethos) can come in two versions keyed on this flag (a 009 edit), or,
   cheaper, a skit at Zethos Castle (3.6.7) differs by one line.
7. **After the audience with Zethos, Titus named (0x80; replaces row 47).** Gabryel tells Jian she never
   told her father she left. "He knew. He always knows. He let me." *Beat:* the father, seen fairly.
   *Hint:* Titus Lauren, in {Healriz}. If choice 4 was YES, Jian adds: "I said something to him I should
   have said months ago."
8. **Before the Blue Dragon (0x13F and 0x1B0; replaces row 21).** Keep the Japanese shape: Gabryel asks if
   he will be a Dragonmaster, Jian: "That's not decided yet... I just...", Flora: "...want to save Lucia.
   ...Right?", Jian: "......" (story-characters.md 1.5). *Beat:* the two of them know him. *Hint:* the
   Blue Dragon is beyond the three jewels.
9. **Before the airship (0x78 or 0x13A).** "Lucia is special to me, too, you know" exists as cutscene text
   (025 #16); the skit before it is Gabryel and Flora alone, Gabi admitting she is scared of the airship
   too. *Beat:* big sister, finally soft. *Hint:* to the roof of the lab (row 12) or {Vile Castle} by air
   (row 11), by stage.

### 3.7 Open questions for Jeff

1. **Why did she pick Jian: A (he kept getting up) or B (to prove her father wrong)?** *Recommendation:* A.
2. **How far does the jealousy go?** Design 11 has her flirt to set up tension with Lucia; the Japanese
   has a quiet "that makes me a little jealous" (004 #81). *Recommendation:* flirting before the reveal, a
   real but unspoken feeling after Lucia is taken, resolved in the Lind skit (3.6.4) into loyalty to
   Lucia. No triangle that the ending has to resolve.
3. **Where does Gabryel end up?** The ending is silent. *Recommendation:* she goes home to Leephon and
   takes her father's place at the table, not his throne: the strike force becomes an envoy to the
   Frontier. One line in the ending.
4. **Her mother.** Never mentioned. *Recommendation:* leave it. One unexplained absence is fine.
5. **The English slang ("bub", "moron boy").** *Recommendation:* replace with the Japanese prim streak,
   keep "muscle head" and "dunce" as her two names for Jian.

---

## 4. Flora Banks

### 4.1 In one line

**As written:** a brash, food-loving archer from the human hideout in the Frontier who talks her way into
the party as guide (010 #63), admits she has never been where she is guiding (018 leaf 0x5a60, 0x58e4), and
is afraid of heights and goes up anyway (025 #13, #17).

**Suggested:** the girl who grew up underground and wants to see everything, and who has to learn that the
people who enslaved her ancestors are people too, the same lesson Jian has to learn about beastmen.

### 4.2 Want, need, wound, lie

**As written.**

- **Want:** "I just want to see new places!" (018 leaf 0x5d28); to be useful ("I'm sure I can help you
  out!", 010 #55).
- **Fears:** heights (025 #13; 024 #0), heat (018 leaf 0x5ad8), the mystical (006 #2).
- **What she has and never uses** (story-characters.md 4.4): the Underground Tunnel humans descend from
  slaves who escaped the Vile Tribe's mines (Dan, 010 #38); she hands out Ignatic Stones so the party can
  walk among the Vile Tribe (010 #65); she calls Ignatius "a tyrant, nothing more!" (010 #61). Her brother
  Peres calls her "naive and prone to being reckless" (010 #27). She never speaks of her parents.
- **Hurt:** "I did my best as a guide, and then I just get cast aside! Lovely!" (010 #54).

**Suggested.**

- **Need:** to see the Vile Tribe as people. They are her people's old masters, and they are also exiles
  "forgotten by the rest of the world" (010 #15). She is to the Vile Tribe what Jian is to beastmen: the
  same flaw, on the other side of the bridge. That gives the Frontier stretch a theme instead of a route.
- **The lie:** "If I act like I'm not scared, I'm not a kid." Her bravado (style-rules.md 3.4: the fear
  denied out loud and shown in the same box) is how a little sister gets taken seriously by a big brother
  who runs everything.
- **Wound** (Jeff's choice):
  - **A. Raised underground.** She grew up in the tunnel and has hardly seen the sky. The fear of heights
    is a tunnel girl's, the fireflies she wants (022 #1, #2) are something she has heard of and never seen,
    and "I just want to see new places" is literal. *Cost:* none; it turns three quirks into one person.
  - **B. Parents lost.** The Vile Tribe or the mines took her parents; Peres raised her. *Cost:* darker,
    and it gives her a reason to hate the Vile Tribe that the Lind skits then have to answer. Makes the
    mirror with Jian sharper.
  - **C. Peres's shadow.** She is the leader's little sister and nobody lets her do anything. *Cost:*
    small; explains why she grabs the guide job, but makes Peres the obstacle, and he is the warmest
    person in the game.
  - **Recommendation:** A, with B as one quiet fact ("Big Brother raised me") and no details.

### 4.3 Voice

**As written:** English: a sassy, upbeat tomboy ("Blah blah blah... let's get going already!", 018 leaf
0x5ddc), with added put-downs ("old crackpot" for Kirlis, 018 leaf 0x6134; "could depress a clown" to the
grieving Jian, 018 leaf 0x5e68). Japanese: あたい (39 times), a rustic, tomboyish country "I"; おにいちゃん
for Peres; drawn-out vowels; sheepish backdowns ("I-I know... I was just saying!", 018 leaf 0x5d28); shy
praise of Jian ("Jian... that's kinda cool?", 006 #8); tears on the airship (024 #2).

**Suggested rules.**

1. Light country turns, never an accent: "reckon" (vanilla already has "I reckon he is!", 018 leaf
   0x5afc), "Big Brother" for Peres, plain words. No dropped letters or broken grammar (style-rules.md 1.3
   bans accents).
2. The most exclamations in the cast, up to three a page, and they collapse into a small, honest line
   when the bravado runs out.
3. Fear is denied out loud and shown in the same box: "Not scared. My knees are, a little."
4. Food is her measuring stick for everything ("bigger than a Ghulian tomato").
5. Backs down sheepishly, not defiantly (the Japanese, not the English "I'm not an idiot, Gabi, OK!").
6. She praises Jian shyly and only when he is not looking for it.
7. No put-downs of elders, and no jokes while someone is grieving (style-rules.md 1.2): the English
   "old crackpot" and "depress a clown" go.
8. She knows the Frontier and explains it (style-rules.md 2: the person who would know explains), in
   short facts, never history lessons.

**Three sample lines** (new):

- In Rebric: "The sky's bigger out here than I reckoned. Does it just keep going?"
- On the airship: "I'm not scared. My knees are scared. I'm just standing on them."
- In Lind: "Big Brother says look before you leap. I looked. ...I'm still leaping."

### 4.4 Arc

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | Mocks the "daters" on the bridge, then helps | exists (010 #59) | Sungrid Bridge |
| 2 | Picked as guide to spite Rufus; Peres pushes her | exists (010 #62, #63) | Underground Tunnel |
| 3 | Her people's history, in her own mouth | told by Dan (010 #38), never by her | **to create**: skit 4.6.1 |
| 4 | The Vile Tribe as people | the Lind villagers say it (010 #15 to #17); she never reacts | **to create**: skit 4.6.2 |
| 5 | Admits she has never been this far | exists (018 leaf 0x58e4, 0x5a60) | Sandra Desert, Roland Forest |
| 6 | Cast aside by Jian; goes home in a foul mood | exists (019 #0, 010 #54; Huldah, 010 #50: "in a foul mood" in Japanese, "excited" in English, docs/story-npcs.md 5) | End of Sandra Desert, Underground Tunnel |
| 7 | Comes back on her own | told as "Zethos sent her" (004 #87, #88) | Titus's house; skit 4.6.4 makes it her choice |
| 8 | Fear of heat, the mystical, the dark caves | exists as hints (rows 30, 43, 20) | Dragon caves |
| 9 | Sees the world (Noapeace, Rebric) | exists (rows 25, 33) | Ghulian; skit 4.6.6 |
| 10 | Peres's "You have really grown up!" and her denial | exists (010 #31), growth asserted, not shown | **to create**: earned by beats 3, 4, and 11 |
| 11 | Faces the airship; tears in Japanese | exists (024 #2, 025 #13, #17) | Negri Ocean Lab, airship |
| 12 | Hostage: "Jian! Forget about me!" | exists (021 #34) | Chamber of Rebirth |
| 13 | "You protected us, didn't you?" | exists (021 #40) | Chamber |
| 14 | What she does after | **to create** | Ending: back to the tunnel, with the sky |

### 4.5 Relationships

**Jian.** As written: 79 shared messages; she teases, he apologizes, and in Japanese she praises him. To
build: she is the one person Jian protects who tells him plainly she did not need it, and the one who
tells him, after the Chamber, that he did save someone (021 #40). The shy praise (006 #8, 018 leaf 0x62a4)
comes back in English.

**Gabryel.** See 3.5. As written: bickering sisters, with English cruelty added. To build: Gabryel teases
the bravado and makes room for the fear; Flora gives Gabi someone to look after who is not a recruit.

**Lucia.** As written: never together. To build: one line in the ending (2.5).

**Rufus.** As written: they are never in the party together; she is present, silent ("..."), when Jian
refuses him (010 #62). To build: her "..." there is the right reaction. After Rufus's death, Flora is
the one who did not know him, and says so, and asks what he was like (skit 5.6.7).

**Peres.** As written: the only family warmth in the game (010 #24, #31), "Look before you leap" (010 #24).
To build: he is offstage for most of the game, so he lives in her mouth: "Big Brother says..." as a
running habit that pays off when she stops saying it.

**Ignatius.** As written: "a tyrant, nothing more!" (010 #61); he takes her hostage (021 #34). To build:
Flora is the one who has to hear the Vile Tribe's side (010 #15 to #17) and still call him a tyrant, now
knowing why they followed him. The hostage scene is her chapter's last test of the bravado.

### 4.6 Skit ideas

Flora is in the party from the Underground Tunnel (0xCB) to the end of Sandra Desert (0xCC), then from
Titus's house to the end.

1. **Under Guystole Mine (0xCB; replaces row 58).** Flora says, flatly, that the mine they are walking
   through is where her great-grandparents were worked by the Vile Tribe, and then talks about lunch.
   Gabryel does not let it go: "Flora." Flora: "It was a long time ago. I've got an [Ignatic] [Stone]."
   *Beat:* the history in her mouth, and the deflection. *Hint:* above ground is {Lind Village}, the
   only Vile Tribe village in the {Frontier}; the stone keeps us safe.
2. **Lind Village, stock up (0x1A3; replaces row 57).** A Vile Tribe child stares at Flora's bow. Flora,
   after: "They're... just kids. I thought they'd be..." Jian: "Bigger?" Flora: "Worse." *Beat:* the
   mirror of Jian's lesson, started. *Hint:* stock up here; past {Guystole Mine} there is nothing.
3. **Sandra Desert (0x1A6; replaces row 54).** "I said I knew the region. I know it from the map on Big
   Brother's wall." *Beat:* she came to see the world, and she admits it. *Hint:* past the {Sandra
   Desert} is {Elda Canyon}.
4. **Titus's house, rejoined (0x63; replaces row 46).** Jian: "Zethos sent you?" Flora: "Nobody sends me.
   I asked him for a ride." **Choice 5 (cheap):** Flora: "Did you miss me? Be honest." YES: Jian: "...A
   little." Flora is unbearable for a page. NO: Jian: "No." Gabryel: "He did." *Later:* on the airship
   (4.6.8), Flora calls back to it. *Hint:* through {Roland Forest} and across {Barrel Desert} to the {Red
   Dragon Cave}.
5. **Red Dragon Cave (0x199; replaces row 43).** Keep her hatred of hot places and her "could I sit this
   one out?", and let Gabryel answer it with a bargain about dinner. *Beat:* comic, kind. *Hint:* the Red
   Dragon is deeper in.
6. **Rebric Village (0x1AF; replaces row 25).** "So different from the Frontier where I grew up..."
   (exists) becomes the door: the tunnel had no sky, and she has never seen fireflies. **Choice 6 (needs
   the ending edit, one line):** Flora: "When this is over... would you come and see the tunnel? Big
   Brother won't believe me about the sky." YES / NO. *Later:* in the ending, Flora's one line differs. 
   *Hint:* the Blue Dragon will not be found by wandering; ask in {Rebric Village}.
7. **Black Dragon Cave is dark (0x1AD; replaces row 30).** Gabryel hates it; Flora does not. "Dark? I grew
   up in a tunnel. This is home." For once she leads and Gabi holds on. *Beat:* the tunnel girl's one
   strength, and a reversal of who is brave. *Hint:* we need a light: the [Photon Plant] grows in the {Black
   Dragon Cave} (row 32). Her line about Dark Jian is in skit 6.6.4.
8. **After the airship flight (0x78; replaces row 9).** Keep the bravado ("You think I'm scared?") and let
   the Japanese tears through: she was. If choice 5 was YES: "You missed me. You'd have missed me more
   splattered." *Beat:* the lie admitted. *Hint:* {Vile Castle}, by air.
9. **After Rufus's sword saves them (0xCE; with row 7).** The Japanese ending of that exchange, restored:
   "Huh... Jian, that was kind of cool?" *Beat:* shy praise. *Hint:* deeper into {Vile Castle}.

### 4.7 Open questions for Jeff

1. **Which wound: A (raised underground), B (parents lost), or C (Peres's shadow)?** *Recommendation:* A,
   with one quiet line of B.
2. **Does Flora come to see the Vile Tribe as people?** *Recommendation:* yes, and it is her arc (skits
   4.6.1 and 4.6.2, paid off in the ending where the Vile Tribe "must all live together", 021 #32, gets a
   face through her).
3. **How country should she sound?** *Recommendation:* light: "reckon", "Big Brother", plain words. No
   phonetic accent.
4. **Her place in the ending.** *Recommendation:* home to the tunnel, with the sky open above it; one line.

---

## 5. Rufus Crow

### 5.1 In one line

**As written:** the beastmen's "invincible" hero who arrests the party to protect his standing (015 #90),
is used as bait at Sungrid Bridge (016 #5), is refused by Jian (010 #62), saves him anyway (020 #3), and
dies holding off Gideon (021 #1).

**Suggested:** the legend who has outlived everyone who followed him, and who finally spends the one thing
the legend says he cannot lose.

### 5.2 Want, need, wound, lie

**As written.**

- **Wants, in order:** his standing and order ("A human acting so heroically would disrupt our way of life
  here, if the public were to ever find out about it", 015 #90; Japanese: "there's my position to think
  of"); atonement ("It is also partly my fault that your companion was taken. I must atone for this",
  010 #62); revenge ("He killed many of my comrades, don't forget. This is a good chance to avenge them,
  too!", 021 #1).
- **Told:** the beastmen's hero in four towns (docs/story-npcs.md 2.5): "The invincible warrior Rufus!"
  (Berio, 007 #40), "Rufus is our hero! He always has been..." (Torricelli, 008 #61); Carducci calls news of
  his defeat "Vile Tribe propaganda" (007 #84). The Frontier humans are colder: Asher assumes he ran
  (010 #34), Peres: "I'm sure that he had no regrets." (010 #29); hired by Zethos as "a beast mercenary" to
  lead the new strike force (009 #13). The enemy at Elda Canyon: "For a while, I really thought you were
  dead." (Caucus, 020 #5).
- **The turn:** Peres's rebuke ("Long ago, all humans had a dream... Taken by the Vile Tribe... and you
  beasts.") and his two-word answer, "Dreams and... hope..." (010 #64). Everything between that and Elda
  Canyon is offscreen.
- **The catchphrase:** ふじみ, "unkillable" (020 #5, 021 #1; story-characters.md 5.2). The English "You
  see, I don't want to die." (020 #5) is not in the Japanese.

**Suggested.**

- **Wound** (built from the text, inference marked): he led the strike force that set out the day after
  the Zethos audience (009 #13). At Sungrid Bridge it was destroyed, and he was left alive as bait (016 #5;
  "placed there to stall us", 010 #60; "I really thought you were dead", 020 #5). **(inference)** "He killed
  many of my comrades" (021 #1) is that strike force. The unkillable man survives; his men do not.
  This is Gabryel's wound from the other side: she chose the dead, he led them.
- **The lie:** "My worth is my legend." He arrests heroes to keep it (015 #90), and the catchphrase is the
  legend talking. The truth he dies into: a legend is something other people believe; a choice is his own.
- **Need:** to be thanked as Rufus, not cheered as the invincible warrior. Jian is the one who can give
  that, which is why the unfinished sentence (020 #6) has to be finished before 021 #1.
- **Why he changed** (Jeff's choice; the text gives only 010 #64):
  - **A. Peres and Lucia.** Peres's speech names what the beastmen took, and the human he arrested is the
    one who knelt to heal him at the bridge, and failed (016 #2). Both are on screen already; one added
    line ("The girl I arrested tried to heal me.") ties them. *Cost:* one line. 
  - **B. His dead men.** He goes to Elda Canyon for revenge, and finds Jian alone there. *Cost:* none, but
    it makes the rescue an accident.
  - **C. Zethos sent him.** *Cost:* removes his choice, which is the whole character.
  - **Recommendation:** A, with B as his own excuse ("I was going that way anyway.").

### 5.3 Voice

**As written:** English: dry, gallant, gently ironic ("You always did have a way with words.", to the mute
Gideon, 021 #2; "I do profess to a talent for not getting killed.", 020 #5), formal with Gabryel ("my
lady"). Japanese: rough-cool オレ, あんた or きみ to Jian, おじょうさま to Gabryel, the repeated ふじみ. The
English broke one line: "I think you need to check the script. That's my line..." (015 #86) is, in
Japanese, "Sorry, but that's my line", meaning "I should be asking you that". Style card: Leo's formality,
Kyle's bravado, dry humor of his own (style-rules.md 3.5).

**Suggested rules.**

1. The shortest lines in the cast after Jian. Few contractions; "I shall" is fine.
2. At most one "!" a page. Understatement, never a gag.
3. "Unkillable" (or "I can't be killed") is his phrase, and it changes meaning each time: a boast (Elda
   Canyon), a joke (Vile Castle), a lie told kindly (021 #1).
4. "My lady" to Gabryel, always. "Jian" to Jian, never "human", from Elda Canyon on.
5. He does not explain himself. Others explain him, and he lets them be wrong.
6. Swordplay is his idiom: guard, opening, reach, footing.
7. He thanks no one aloud, except once.
8. The fourth-wall "check the script" goes (style-rules.md 1.3 allows one per chapter, but this one is a
   mistranslation); use the Japanese meaning.

**Three sample lines** (new):

- To Gabryel at Elda Canyon: "I am not one of your recruits, my lady. Nobody brought me."
- To Jian, on the road: "Unkillable is not the same as unhurt."
- About his strike force: "Eleven of us crossed the bridge. I am the one who was too stubborn to die."

### 5.4 Arc

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | The legend, by NPC chorus | told (007 #40, #83; 008 #61; 015 #51, #52) | Olbeage, Leephon |
| 2 | Arrests the heroes for his standing | exists (015 #86 to #90) | Cathedral of Althena |
| 3 | Leads the strike force out | told (009 #13) | offscreen |
| 4 | His men die at Sungrid; he is left as bait | **told only by implication** (016 #5, 010 #60, 020 #5, 021 #1) | skit 5.6.4 says it |
| 5 | Lucia tries to heal him | exists (016 #2) | Sungrid Bridge |
| 6 | Offers to atone; refused | exists (010 #62) | Underground Tunnel |
| 7 | Peres's rebuke | exists (010 #64) | Underground Tunnel |
| 8 | Why he changed | **to create** (A, above) | skit 5.6.4 |
| 9 | Rescues Jian; joins | exists (020 #3 to #5) | Elda Canyon |
| 10 | The unfinished sentence | exists, cut off (020 #6) | Elda Canyon |
| 11 | The sentence finished, and Jian's answer | **to create** | Vile Castle; skit 5.6.5 |
| 12 | Holds off Gideon; "I'll catch up" | exists (021 #1) | Vile Castle 4F |
| 13 | His sword returned as a "toothpick" | exists (021 #5) | Grand Hall |
| 14 | Zethos understands him through the sword | exists (009 #20) | Zethos Castle |
| 15 | The sword saves them | exists (021 #13 to #15; 018 leaf 0x62a4) | Vile Castle, return |

### 5.5 Relationships

**Jian.** As written: arrest, refusal, rescue, farewell; the apology is to Gabryel after Rufus is dead
(018 leaf 0x62a4: "He was our comrade... our friend"). To build: one honest exchange before 021 #1, with
Rufus finishing "I know you don't think much of us beastmen... But..." and Jian answering him to his face.
Without it, Rufus dies for someone who never said thank you.

**Gabryel.** As written: "my lady", 5 shared messages, "Be careful, Rufus!" / "I'm always careful. The
same to you, my lady." (021 #1). To build: she tries to send him back at Elda Canyon, as Jian tries with
her, and he refuses in the same words she uses (skit 5.6.3). His death is her wound reopened (3.6.6).

**Lucia.** As written: he arrests her (015 #88); she tries to heal him (016 #2). To build: one line, in his
mouth, that he remembers the second (A, above).

**Flora.** As written: never in the party together; she is silent when Jian refuses him (010 #62). To build:
after his death she asks what he was like (skit 5.6.7).

**Zethos.** As written: his employer (009 #13); Zethos reads his death correctly (009 #20). To build:
nothing more; Zethos's line is the eulogy.

**Gideon.** As written: killed his comrades, kills him (021 #1, #5). To build: nothing; Gideon is a force,
not a person.

### 5.6 Skit ideas

Rufus is in the party only from the Elda Canyon boss to Vile Castle 4F (story-party-timeline.md rows 14
to 16). Vanilla has two stage flags there: 0xCA (Elda Canyon) and 0x1A8 (Vile Castle in sight); more skits
in that stretch need place restrictions (Elda Canyon area 2, area 3, Vile Castle floors) at the same flags.
Skits before and after are about him, without him.

1. **After the arrest (Jian and Lucia only; stage flag to confirm).** Lucia: "He didn't want to do it. You
   could hear it." Jian: "He did it anyway." *Beat:* plants the man inside the legend. *Hint:* the current
   escape step (to check against the arrest stretch's vanilla lines).
2. **Elda Canyon, area 2 (0xCA).** **Choice 7 (cheap):** Rufus: "Do you still not want me here?" YES:
   Jian: "...I don't know yet." Rufus: "Honest. Good." NO: Jian: "I was wrong at the tunnel." Rufus: "We
   shall see." *Later:* one line of skit 5.6.5 differs. *Hint:* through {Elda Canyon} to {Vile Castle}
   (row 52).
3. **Elda Canyon, area 3 (0xCA).** Gabryel tries to send him back to Leephon: he is the last of her
   father's men out here. Rufus: "I am not one of your recruits, my lady. Nobody brought me." Gabryel has
   said exactly this to Jian three times. *Beat:* mirror; she hears herself. *Hint:* {Vile Castle} lies
   just past the canyon.
4. **Elda Canyon, camp (0xCA, the last canyon map).** Jian asks how he survived Sungrid Bridge. Rufus tells
   it in four short lines: eleven crossed, Gideon came, he woke up tied to a post as bait, and a human girl
   tried to heal him. *Beat:* the wound and the turn (5.2 A) in one skit. *Hint:* rest here; {Vile
   Castle} is next.
5. **Vile Castle in sight (0x1A8; replaces row 51).** The sentence finished. Rufus: "At the canyon I said
   you don't think much of us beastmen. I can live with that. But I would rather not die with it." Jian:
   "...I was wrong about you. About more than you." If choice 7 was NO, Rufus: "You said so at the canyon.
   Twice is a habit." *Beat:* the most important skit for Jian in the game; it has to play before Vile
   Castle 4F. *Hint:* "I'm coming, Lucia" stays as the closing beat, with {Vile Castle} named.
6. **Rufus left alone (0xCD; replaces row 50).** Gabryel: "Do you think Rufus is OK alone?" Jian: "He said
   he'd catch up. He always does." Gabryel: "......" *Beat:* both know. *Hint:* stick close; up to the
   Grand Hall.
7. **Barrel Desert ahead, Flora back (0x13; replaces row 45).** Flora: "What was he like? Rufus." Gabryel:
   "Proud. Polite. Impossible." Jian: "He was kind about it. About me." *Beat:* Flora gets him secondhand,
   and so does the player, one more time. *Hint:* cross {Barrel Desert} to the {Red Dragon Cave}; watch
   for ant lions (row 44).
8. **Rufus's sword saves them (0xCE; replaces row 7).** The Japanese version (re-party-chat-japanese.md
   1.1 item 8): Jian's silence when Gabryel asks if he kept the sword, then "That's not it! Rufus fought
   for us. He was one of us." *Beat:* the apology, now a follow-up to 5.6.5 instead of a substitute for it.
   *Hint:* deeper into {Vile Castle}.

### 5.7 Open questions for Jeff

1. **Why did Rufus change: A (Peres and Lucia), B (revenge), or C (orders)?** *Recommendation:* A, with B
   as his excuse.
2. **Was he bait or sent to stall them at Sungrid Bridge?** The text is unclear (010 #60, 016 #5).
   *Recommendation:* bait, the survivor of his own strike force.
3. **Hero, mercenary, or Zethos's man?** All three are said. *Recommendation:* a mercenary the beastmen
   made into a hero; he took the legend because it paid, and dies out of it.
4. **The English-only "You see, I don't want to die." (020 #5).** *Recommendation:* replace with the
   Japanese "We'll see. You'll be the one who falls!", so "unkillable" is never fear.
5. **Does his death scene change?** *Recommendation:* no. 021 #1 works once 5.6.5 has played; keep "I'm
   always careful. The same to you, my lady."

---

## 6. Ignatius

This chapter is the person. His history options, his earlier appearances, the fight, and the ending are in
chapter 11, "Ignatius and the final fight".

### 6.1 In one line

**As written:** a Dragonmaster who turned on Althena, leads the Vile Tribe, wants to rule the world as its
one all-powerful being (004 #80, 021 #28), uses Jian's trials to break the Chamber's barrier (016 #7,
021 #22), and falls off a ledge in a hostage gambit (021 #34 to #38). Three scenes, 47 turns.

**Suggested:** what Jian becomes if he never lets anyone help him: the champion who decided that only he
could be trusted to carry the world.

### 6.2 Want, need, wound, lie

**As written.**

- **Want:** Althena's seat and the Goddess herself "under his control" (004 #80); "this world only needs
  one all-powerful being. Which looks like me, on both counts." (021 #31). The Vile Tribe believe he wants
  to make the Frontier "a green and verdant paradise" for them (010 #17) and call him "the final ray of
  light piercing the dismal clouds of our fate" (010 #16).
- **Plan:** let the would-be Dragonmaster kill the Four Dragons for him (016 #7; "Due to your kindly
  releasing the Four Dragons, I can finally achieve my goal.", 021 #22).
- **Past:** he took the White Dragon's trial "and went on to become a Dragonmaster" (006 #5); Zethos: "currently,
  Ignatius is the Dragonmaster of the Goddess" (009 #18). He turned when "the Goddess Althena began to have
  doubts in her position" (004 #78). An old score with Zethos (016 #7). A promise to Althena to stop
  killing, kept (021 #12).
- **His one real argument:** "Love steals everything" (021 #24), in Japanese あいは　おしみなく　うばう
  ("Love takes, unsparingly"), the title of Arishima Takeo's 1920 essay (story-characters.md 6.3).
- **Fear:** Jian names it: "...And yet you still fear something, don't you. Not me! Yourself!" (021 #28).
  Titus: he fears another Dragonmaster (004 #81).

**Suggested.**

- **The lie:** "Only one hand can hold the world still." It is Althena's old belief, which she dropped
  (004 #78), and he could not. It is also Jian's go-it-alone flaw at the scale of a god.
- **Need:** none he will meet. He is the character who does not change; his last act (letting go of Jian's
  hand, 021 #38) should be a choice, not an accident.
- **Wound:** the day Althena said the future belongs to everyone, he heard "you are no longer needed".
  Three versions of who he was, with costs, in 11.1.
- **The human crack:** he keeps his promise to her (021 #12). A usurper who will not break his word to the
  goddess he usurps still loves her, or the oath, or both. That is the thread the fight pulls.

### 6.3 Voice

**As written:** English: a camp aristocrat ("Lucia, Lucia, Lucia. Learn some new lyrics!", 021 #9; "Oh, a
kidnapping here or there. So what?", 021 #7, English-only; "whelp"). Japanese: the royal 余, classical なり
("I am Ignatius", 021 #4), archaic negatives, こぞう ("brat") for Jian, stage laughs (ククク), and a lecturer
more than a sneerer: "Spirit alone won't carry you through the world. You must also mind your manners."
(021 #7).

**Suggested rules.**

1. Formal and slightly old: no contractions, full sentences, an older word where a plain one would do
   ("cease", "whelp" or "boy", "the Goddess", never "Althena" bare until the end).
2. He lectures; he does not taunt. Every insult is a lesson he thinks Jian needs.
3. He argues from a real idea (one hand, one will) and quotes it like scripture. The Arishima line comes
   back in English as something with weight: "Love takes. It does not ask."
4. He never lies. He misleads by telling the truth at the wrong time (016 #7: the rumors become reality).
5. No camp. Drop "Learn some new lyrics" and "a kidnapping here or there". One dry joke per scene at most,
   at Jian's expense, never at his own.
6. He speaks of the Vile Tribe as "my people" and means it.
7. He laughs once in the game, and it is not a stage laugh.
8. He calls himself "I". The Japanese royal 余 reads as a plural in English "we"; use rank in his manner,
   not his pronoun.

**Three sample lines** (new):

- To Jian in the Grand Hall: "You call it a promise, boy. I called it that once. Then she changed her mind."
- To the party in the Chamber: "One hand on the world, and it holds still. A thousand hands, and it is torn
  apart."
- His last line, refusing the hand: "Let go, boy. One of us should learn how."

### 6.4 Arc (appearances)

| # | Beat | Status | Where |
|---|---|---|---|
| 1 | Named by Titus as the Dragonmaster who turned | told (004 #78 to #82) | Healriz |
| 2 | Felt by Jian ("resonance", 004 #82) | told by Titus and the White Dragon (006 #5), never felt | **to create**: skits 6.6.2, 6.6.8 |
| 3 | First seen, earlier than the Grand Hall | **to create** | 11.2 |
| 4 | Plans with Jude; uses the trials | exists (016 #7) | Vile Castle (cutscene) |
| 5 | His people's case | told by the Lind villagers (010 #15 to #17) | Lind; skit 6.6.5 |
| 6 | Crushes Jian; keeps his promise to Althena | exists (021 #4 to #12) | Grand Hall |
| 7 | The dragons call Jian his mirror | told (006 #5, 022 #6, 023 #19) | each trial |
| 8 | Thanks Jian for the dragons; "love takes" | exists (021 #20 to #24) | Chamber of Rebirth |
| 9 | Jian answers him | **to create** | Chamber; 11.3 |
| 10 | The fight | **to create** | Chamber; 11.3 |
| 11 | Refuses the hand | exists (021 #38) | Chamber; 11.4 |

### 6.5 Relationships

**Jian.** As written: 17 shared messages, all in 021. To build: the mirror. Ignatius is the only person in
the game who takes Jian completely seriously, as a rival Dragonmaster (021 #25, "There cannot be two Dragon
Masters in the world"), and he is right about Jian's flaw (love that holds on, 021 #24). Jian's answer has
to be his own.

**Althena / Lucia.** As written: he pursued her (004 #80), keeps his promise to her (021 #12), and calls
her "Cursed Althena" in private (016 #7). To build: the history (11.1). He never meets Lucia; he only knows
the goddess, which is his blindness.

**Gabryel.** As written: no exchange. To build: one line from her in the Chamber, for her dead.

**Flora.** As written: she calls him a tyrant (010 #61); he takes her hostage (021 #34). To build: if he
holds anyone in the Chamber, let it be the human whose ancestors his people enslaved, and let her answer
him (4.5).

**Rufus.** As written: Gideon, his creature, kills Rufus; Ignatius hands back the sword as a "toothpick"
(021 #5). To build: nothing; the sword's later journey answers him.

**Zethos.** As written: "I still have... matters to settle with him" (016 #7); "That mewling pup Zethos
shall kneel before me!" (016 #7). To build: 11.1 offers a history.

### 6.6 Skit ideas

Ignatius cannot speak in a skit (only party members can). Every skit here is the party about him, and
each carries a piece of him forward so the Chamber is not the first time the player meets a person.

1. **After Titus, on the road (0x63, a second chat after 4.6.4).** Gabryel: "Ignatius was the Goddess's
   own Dragonmaster." Jian: "Then he knew her. Before." *Beat:* the first time he is a person, not a
   title. *Hint:* {Roland Forest}, then {Barrel Desert}.
2. **White Dragon Cave key (0x11; replaces row 40).** The first resonance: after the Red Dragon, Jian
   felt something look at him "from far off". He says it lightly and does not sleep. *Beat:* Titus's
   "resonance" (004 #82), felt. *Hint:* the key to the {White Dragon Cave} is at {Delrich Temple}: the
   stone steps.
3. **Two trials done (0x61; replaces row 37).** The White Dragon said "Just like Ignatius before you"
   (006 #5). Jian: "He stood where I stood. Same cave, same question." Gabryel: "Different answer." Jian:
   "...You hope." *Beat:* the mirror, named by Jian himself. *Hint:* Titus said four dragons; next is
   through the {Meryod Cave} to Ghulian.
4. **Black Dragon's trial passed (0x12E; replaces row 28).** Dark Jian (docs/re-enemies.md). Gabryel: "The
   Black Dragon said Ignatius submitted. To what?" Jian: "To being the only one who could do it." Flora:
   "That thing wasn't you. It was what you'd be without us." *Beat:* the theme, said by Flora. *Hint:*
   only the Blue Dragon's trial remains; it is on {Ghulian}.
5. **Leaving Lind (0xDA; replaces row 55).** The villager said "You're not the only ones trying to get back
   something you've lost" (010 #17). Flora: "They think he's going to give them the sky." Gabryel: "Maybe
   he is." Flora: "...". *Beat:* his cause, taken seriously by the party for one page. *Hint:* on to the
   {Sandra Desert}.
6. **The note at the lab (0x14A; replaces row 12).** Gabryel: "He let us live. In the Grand Hall. Why?"
   Jian: "Lucia told him to. And he listened." *Beat:* the promise (021 #12) noticed; the crack in him.
   *Hint:* the note says go up to the roof.
7. **Final dungeon, Jian quiet (0x18F; replaces row 8).** Keep the Japanese silence, then: Jian: "He's
   scared. I can feel it. Not of us." Gabryel: "Of what, then?" Jian: "Of not being needed." *Beat:* sets
   up 021 #28 ("You fear yourself") as something Jian has worked out, not shouted. *Hint:* find the way to
   the {Chamber of Rebirth}.
8. **The USA-only resonance scene (0x1B8..0x1BB; row 5).** The English added "Luciaaaaaaaaaaa!!!" with no
   Japanese counterpart. Keep the flags and the idea (he feels Ignatius in the Chamber); replace the scream
   with one quiet line. *Hint:* the Chamber is close.
9. **Chamber of Rebirth empty (0xCF; replaces row 4).** **Choice 8 (needs a 021 edit):** Gabryel: "When
   we find him... are you going to finish him?" YES: Jian: "...He took everything." Gabryel puts her hand
   on his sword arm and says nothing. NO: Jian: "I want him stopped. Not dead." *Later:* the fight's end
   (11.4): with YES, Gabryel's hand on his arm is what stops the killing blow before he reaches for
   Ignatius; with NO, he lowers the sword himself. Both reach. *Hint:* if Lucia is not in the Chamber,
   look further in (row 4).

### 6.7 Open questions for Jeff

1. **His history** (11.1). *Recommendation:* option B there.
2. **How human?** *Recommendation:* human enough that his promise to Althena means something, and never
   pitiable. He does not get a redemption; he gets understood.
3. **Camp or menace?** *Recommendation:* menace with a teacher's manner (the Japanese). Drop the camp.
4. **Does he die?** *Recommendation:* yes, by his own choice, refusing the hand (11.4).

---

## 7. Beast King Zethos

### 7.1 In one line

**As written:** a proud, theatrical king and worried father ("Oh, who requested the clown?", 005 #57;
"Perhaps we should chain her down now, before she gets away again, eh?", 009 #69) who cursed Jian to make
his daughter give up on a human recruit (009 #13) and is the one beastman who apologizes for his people
(009 #20).

**Suggested:** a good king of an unfair arrangement, who learns it is unfair from his daughter and a human
courier, and says so out loud.

### 7.2 Want, need, wound, lie

- **As written** (NPCs, docs/story-npcs.md 2.7): he has proclaimed an end to discrimination against humans
  ("I wonder what happened to spark that off?", Palestrina, 008 #64), and he reaches out to human Noapeace
  (Luke: "Why has Beast King Zethos suddenly taken such an interest in...", 011 #17). The world notices him
  changing before the party does.
- **As written. Want:** to win the war in the Frontier without a human in the strike force ("including a
  human in the strike force would stir up unwanted animosity across the world", 009 #13), and to keep his
  daughter safe. **Lie:** "humans are not made for combat" (009 #13). **Turn:** "I am ashamed... How we
  have mocked and oppressed humans!" (009 #20). **Grudge:** Ignatius has "matters to settle with him"
  (016 #7), never explained.
- **Suggested. Wound** (Jeff's choice):
  - **A. He turned the exiles away.** When the Vile Tribe first sent envoys out of the Frontier asking to
    come home, the beastmen's throne refused them. Ignatius was there, and remembers. *Cost:* makes the
    beastmen complicit in the Frontier's misery, which deepens the theme (the Vile Tribe were "forgotten
    by the rest of the world", 010 #15) and gives 016 #7 its meaning. It costs Zethos some innocence.
  - **B. Gabryel's mother.** She died in the first Vile Tribe war. *Cost:* explains the grudge and
    Gabryel's war, but makes the war personal for both and puts a death behind every scene of theirs.
  - **C. The dead strike forces.** He has sent his best beastmen over the bridge again and again (009 #13,
    #64), and every loss is his. *Cost:* none, and it is already true; it simply needs saying.
  - **Recommendation:** C as written, plus A as his secret, told to Jian after the Grand Hall in one line.

### 7.3 Voice

**As written:** Japanese わたし, きみ to Jian, あのコ ("that girl") for his daughter; English proud and
mock-theatrical, sincere when it counts.

**Suggested rules.** 1. Grand, but never camp: he enjoys being a king. 2. A joke at his own expense after
every serious line about Gabryel. 3. "My daughter" to others, never "Gabryel" until he is apologizing. 4.
One "!" a page at most.

**Sample lines** (new): "A human, in my Coliseum, refusing to stay down. I have not been this annoyed in
years." / To Jian, after the Grand Hall: "We turned them away once. The ones who became the Vile Tribe. I
was young, and I agreed."

### 7.4 Arc and suggested changes

1. Watches the Coliseum and issues the challenge (design 11; **to create**, replacing the curse blast,
   005 #71). 2. The fight and the reveal (009 #53 to #64; exists, with the curse lines rewritten). 3. Sends
   Jian over Sungrid Bridge ("try and cross the Sungrid Bridge", 009 #13; exists). 4. After the Grand Hall,
   tells them about the Dragonmaster (009 #17 to #19; exists), apologizes (009 #20; exists), and, suggested,
   hears Jian apologize back (1.5). 5. Sends Flora to Titus's house (004 #87; exists). 6. The ending: one
   line, or Gabryel's line about him (3.7).

**Skits about him:** Gabryel's "He knew. He let me." (3.6.7); the post-curse skit after the challenge,
where Lucia asks what kind of king throws a challenge at commoners and Gabryel answers too quickly
(chapter 10).

**Open questions:** **Which wound?** *Recommendation:* C plus A. **When does the proclamation happen?**
The NPC lines (008 #64, 011 #17) fit best after the Grand Hall apology (009 #20). *Recommendation:* make
it the visible result of that scene, so the world changes because Jian and Gabryel changed him.

---

## 8. Gad

### 8.1 In one line

**As written:** the gruff boss of Gad's Express ("lad", "late again as usual", 001 #17) who bullies the
grieving Jian into opening Lucia's gift by pretending to throw it out (001 #17 to #29).

**Suggested:** the closest thing Jian has to a father, who would rather die than say it.

### 8.2 Want, need, wound, lie

- **As written:** wants the jobs done and the deliveries on time; cares underneath (style-rules.md 3.6).
  The gift scene is his one real scene, and it is good (story-characters.md 7: "worth keeping as is").
- **Suggested:** no arc. His job in the story is to be the place Jian comes back to. One fact worth making
  explicit: Lucia trusted *him* with the anniversary gift, booked as a Gad's Express delivery "to be
  delivered to you today" (001 #20). That makes the gift scene a delivery, and Gad is honoring a job.

### 8.3 Voice

**As written:** Japanese rough, old-Edo working man's speech (じゃねえか, だらしねえな); English adds
sarcasm ("It would certainly have suited you, Jian. Shame.", 001 #24; Japanese: "This is great... it really
suits you, Jian!").

**Suggested rules.** 1. Imperatives and short sentences. 2. "Lad", once a page at most. 3. Kindness is done,
not said. 4. Restore the Japanese warmth at 001 #24: the sarcasm undercuts the one moment he lets it show.

**Sample lines** (new): "Signed for, delivered, and you're crying on my counter. Out." / In the ending:
"Got a job for you, lad. Pickup at Fountain Square. Don't be late. ...Again."

### 8.4 Arc and suggested changes

1. Opening: off screen (the shipped wake-up uses Cherenkov). 2. The gift scene (001 #17 to #29; exists,
keep, restore 001 #24). 3. **To create:** the ending. Gad sends Jian to Fountain Square on a made-up job
the day Lucia comes back to Port Searis (chapter 12). He knew she was back and said nothing.

**Skits about him:** the Fountain Square skit (1.6.1, the gift planted) and the Gad's Express skit (1.6.8)
are already his. No more needed.

**Open question:** **Does Gad know who Lucia is, at the end?** *Recommendation:* no, and he does not ask.
He just knows his two couriers belong together on the schedule.

---

## 9. Titus Lauren

### 9.1 In one line

**As written:** Althena's priest, hiding in Healriz because he "perceived a threat to the Goddess Althena"
(004 #78); the story's exposition (004 #74 to #94) and the ending's speaker (026 #1, #2). "No personality
beyond kindness" (story-characters.md 7).

**Suggested:** the man who knew where the goddess was hiding, and let her have her year.

### 9.2 Want, need, wound, lie

- **As written:** wants Althena safe and Ignatius stopped; sends Jian to the Four Dragons (004 #81).
- **Suggested** (Jeff's choice):
  - **A. He knew.** Titus came to Healriz because it is near Port Searis, and he has watched Lucia from a
    distance for a year without telling her, because she asked to forget. The Japanese already leans this
    way: he recognizes her (004 #67), calls her あの方 (004 #73), and owns an album just like hers (004 #95,
    #96; docs/story-npcs.md 2.2). *Cost:* one line to Jian ("I should have warned you. She asked me not
    to.") and restoring the flattened Japanese. It gives him guilt and a reason to help.
  - **B. He did not know,** as written. *Cost:* none; he stays a guide.
  - **Recommendation:** A. It costs one line and makes him a person.

### 9.3 Voice

**As written:** kind, formal, explanatory. The English softened his ending lines (docs/intro-analysis.md
section 4): the Japanese has "so that this never happens again, we must fight the darkness inside
ourselves", where the English "can only hope".

**Suggested rules.** 1. Explains, but in one idea a page, and lets Gabryel interrupt (style-rules.md 2).
2. Calls her "the Goddess" until the ending, then "Lucia". 3. Restore the Japanese firmness in 026 #2.

**Sample line** (new): "She asked to forget. I am a priest. I do what the Goddess asks, even when it is
foolish. Especially then."

### 9.4 Arc and suggested changes

1. The exposition at his house (004 #78 to #94; exists, trim to one fact a page). 2. Sends Flora back in
(exists). 3. The ending: he walks with the reborn Lucia (026 #1 to #3). **Suggested:** shorten the
Titus and Peles exchange (026 #1, #2) to its one idea (she chose to live among us) and give the last scene
to Lucia and Jian (chapter 12). The closing narration takes the Japanese "the one who inherits the wind...
That might be you." (docs/intro-analysis.md section 4).

**Skits about him:** the road out of Healriz (6.6.1) carries what he said about Ignatius. No more needed.

**Open question:** **Did he know?** *Recommendation:* A, yes.

---

## 10. The curse: what removing it leaves, and what can carry it

**Decided (Jeff, 2026-10-09): the curse stays in the Story edition.** It is redefined: Jian cannot be healed
except by the Goddess's power at statues (no items, no healing spells on him) while cursed; he keeps his
attack. It still keeps any beastman army from recruiting him, which is why Zethos cursed him. It breaks on
round 3 of the Zethos fight: Zethos, "I may have been wrong about you. Let's make this a fair fight," then the
flash; Jian can use items again from that turn. The options below about removing the curse are superseded;
what remains useful here is the list of scenes the curse touches. See docs/plan-two-editions.md.

Decided: the curse goes, and so does Zethos's blast at the end of the San Coliseum (docs/design.md section
11). Design 11 also gives Gabryel's new reason to bring Jian: she plays the impressed fan of the human
champion and points him at a bigger fight, the Beast King's open challenge, which turns out to be a ploy to
find fighters for the Frontier. What follows takes each piece the curse carried (story-characters.md
section 9) and offers ways to carry it without the curse. **Everything in this chapter is suggested.**

**As written, the curse is explained** (009 #13, the same in Japanese): Zethos guessed Gabryel would
recruit Jian, a human in the strike force "would stir up unwanted animosity across the world", so he
crippled Jian's fighting so "she would surely just give up on you". Nothing after Zethos Castle depends on
it.

### 10.1 Jian's reason to go to Leephon (was: lift the curse, 005 #71)

- **A. The challenge, as Jian's own want** (design 11). Beating the Coliseum did not make the crowd cheer
  (005 #57); beating the Beast King in his own castle might. Jian goes for exactly the reason he entered
  the tournament (004 #48), and Lucia goes because the purse is a year's wages and because he would go
  alone. *Cost:* none; it is already decided, and it makes 1.6.3 ("You wanted them to cheer") pay off.
- **B. A delivery.** Gabryel hires Gad's Express, through Jian and Lucia, to carry a sealed letter to
  Zethos Castle. The letter is her recommendation of Jian. They are delivering him. *Cost:* a new prop;
  in exchange the courier job finally matters to the plot, and the reveal gets a sting ("You read it?" "We
  don't read the mail.").
- **C. Both.** The challenge is the reason; the letter is how Gabryel gets them past the gate.
- **Recommendation:** A, with B's letter if the Olbeage checkpoint (007 #78) needs a reason Gabryel
  handles it herself.

### 10.2 Gabryel's creed, which answered Zethos's blast (005 #68)

The blast is gone, and with it the moment Gabryel saves Lucia and says "But aren't humans and beastmen the
same?". The line is too good to lose.

- **A. A sore loser.** Moran, the last tournament opponent, goes for Jian after the bell; Gabryel stops him
  and says the line to him. *Cost:* a short new cutscene in 005 with existing sprites.
- **B. The crowd.** A beastman in the stands shouts that the human cheated; Gabryel answers him. *Cost:*
  smaller, but she is answering a nobody.
- **C. To Lucia, as the opening of the fan act.** She says it in admiration of Jian, not in a fight.
  *Cost:* loses the rescue, which is her introduction as a fighter.
- **Recommendation:** A.

### 10.3 Jian's grievance with Zethos and the beastmen (was: "no remorse over the terrible curse", 009 #13)

- **A. What is already there.** The Coliseum jeers (005 #57), the town insults (004 #18, #31), Zethos's
  "Oh, who requested the clown?" (005 #57), and his "humans are not made for combat" (009 #13). Delete the
  curse clause from Jian's 009 #13 speech and his anger stands on the rest: "I'm not about to forgive
  anyone who puts humans down so easily, even if he is a king!" *Cost:* none.
- **B. Plus the wound** (Jian 1.2 A): the beastman traders of his childhood. *Cost:* one skit line.
- **C. Plus the arrest.** Jian and Lucia arrive as challengers and are arrested at the Cathedral instead
  (015 #86 to #90, kept). The king who invited all comers had his hero drag in the human who answered.
  *Cost:* none; the arrest exists, and it is a better insult than a curse.
- **Recommendation:** all three; they do not conflict.

### 10.4 Lucia's best scene (009 #47 to #52; was: "put my poor Jian back to normal")

- **A. She demands the fair fight they were promised.** Arrested instead of received, Lucia marches up to
  the throne: the challenge said anyone, and Jian is anyone. Keep "Hey, get your paws off me, OK? Is this
  any way to treat a lady?!" (009 #47) and the sing-song "There's only one answer!" (009 #50, the
  Japanese). *Cost:* rewrite of 009 #48 and #52.
- **B. She demands their release** and offers to fight him herself if he will not let them go. *Cost:*
  makes the scene about her and less about Jian, which is arguably better for Lucia.
- **C. Both, in that order:** release first, then "and you owe him a fight".
- **Recommendation:** C. The "cursed knight and his sweet little princess" taunt (009 #52) becomes "the
  courier and his sweet little bodyguard".

### 10.5 The Gabryel reveal (was: Zethos explaining the curse, 009 #13, #58 to #64)

- **A. The ploy, confessed** (design 11). After the fight, Zethos: the challenge was never about prize
  money; it was how his daughter finds him fighters. Keep "I guessed that Gabryel would set her sights on
  you, and end up bringing you to me" (009 #13) word for word: it works without the curse.
- **B. Ezekiel's slip.** "My lady" in front of Jian and Lucia, before Zethos says anything. *Cost:* the
  priests at the Cathedral already call her that; a third slip is a joke, not a reveal.
- **Recommendation:** A, with B as the half-second before it.

### 10.6 The handstand

The Japanese curse name, 天地転とうの呪ばく ("curse of turning heaven and earth over"), is a pun on Jian's
handstands. Without the curse the handstand means nothing. **Recommendation:** one use, for someone else
(1.7 question 4: Flora on the airship).

### 10.7 Small lines to rewrite

- **Carmen in Olbeage (007 #33):** the curse rumor becomes the challenge rumor ("A human won at the
  Coliseum? Next he'll want the king.").
- **"You look all better now" (009 #17):** this scene is after the Grand Hall, so it becomes Zethos seeing
  what Ignatius did to him: "You are still standing, I see."
- **The Zethos fight** keeps its HP floor and round-3 real hit (design 11); only the curse text goes.
- **Jian's thanks at 009 #55** ("Thank you, Lucia... And you, Gabi") moves to after the fight, for having
  come at all.

### 10.8 Recommended replacement, in story order

San Coliseum final (Moran attacks after the bell, Gabryel's creed, 10.2 A) → Gabryel the fan, and the
Beast King's challenge (design 11; skit 3.6.1) → ferry and Olbeage (skits 2.6.6, 2.6.7, 3.6.2) → the
Cathedral, the arrest (015, kept: 10.3 C) → Zethos Castle: Lucia's demand (10.4 C), the fight, the ploy
(10.5 A), Jian's anger without the curse clause (10.3 A) → Pisarno Square, unchanged.

---

## 11. Ignatius and the final fight

**As written**, in one paragraph (story-characters.md section 6): three scenes and 47 turns. He plans with
Jude (016 #7), crushes Jian in an unwinnable fight and keeps his promise to Althena to spare him (021 #4 to
#12; battle type 0x11, HP refilled, docs/re-enemies.md), and in the Chamber of Rebirth thanks Jian for
killing the dragons (021 #22), argues that "love takes" (021 #24), is refused a duel ("Raise your sword,
defend yourself!", 021 #31; Althena talks Jian down), takes Flora hostage (021 #34), is interrupted by
something the text never names, falls, and refuses Jian's hand (021 #38). The last bosses are Gideon. Two
NPCs ask the question the game never answers: "Isn't the Dragonmaster meant to protect the world, along
with the Four Dragons? So what's he playing at?" (Francesca, 008 #21) and "Ignatius is a loser... sorry,
Dragonmaster, right? The guardian of the Goddess? So why's he causing all this trouble?" (Lena, 015 #67)
(docs/story-npcs.md 2.6). Everything below is **suggested**.

### 11.1 His history: three options

What any version must fit: he took the White Dragon's trial and became a Dragonmaster (006 #5); he is "the
Dragonmaster of the Goddess" now (009 #18); he turned when Althena "began to have doubts in her position"
(004 #78); he used "Black Magic", which in this game is the Dragonmaster's own power (Jian's ring spells;
006 #5, "received by Black Magic"), to make the Frontier's exiles into an army (004 #78); he has a score to
settle with Zethos and calls him "that mewling pup" (016 #7), so he is older; and he keeps a promise to
Althena (021 #12). The shipped prologue also has "her champion the Dragonmaster" swearing her eternal
loyalty at the dawn of the world.

- **A. The first champion.** Ignatius *is* the Dragonmaster of the prologue, ancient, who swore eternal
  loyalty and served for an age. When she said the world should belong to everyone, his oath had nothing
  left to serve. *Gives:* tragedy on the scale of the prologue; "I kept faith with her longer than any of
  you have been alive". *Costs:* Lunar canon makes Dragonmaster a title earned by many people across time
  (docs/intro-analysis.md section 3), and the White Dragon speaks of his trial as an event in its own
  memory, not the dawn of time (006 #5). An immortal champion also makes Jian's victory harder to believe.
- **B. The exile's son.** Born in the Frontier, among the descendants of the people Althena sent there
  (004 #78; the villagers: "even the Goddess Althena, the very one who sent us here, has long since
  forgotten that we exist", 010 #15). The only one of them ever to cross back, he passed the trials and
  became her champion. When she said the future belongs "to all the people in the world" (004 #78), he
  asked whether "all" included his people, and she had no answer ready. He went home and made them an army
  with her own magic. The beastmen's throne once turned his people's envoys away (Zethos 7.2 A), so he
  despises Zethos. *Gives:* a cause that is not madness, ties to every existing Vile Tribe line (010 #15 to
  #23), a real moral knot for Flora (her ancestors were their slaves, 010 #38), and an answer to Francesca
  and Lena. *Costs:* Titus's "fiends of the Frontier" (004 #78) becomes one side's story, not the truth,
  and the Vile Tribe become partly victims, which the ending must then address (021 #32: "the Vile
  Tribe... must all live together").
- **C. The human champion.** A human who became Dragonmaster in a beastman-led world (the shipped prologue:
  "power settled with the stronger Beastmen"), mocked by a beastman court where young Zethos laughed at
  him. He concluded that no race would ever treat another fairly, so one will must stand above them all.
  *Gives:* the sharpest mirror for Jian, who starts the game wanting exactly what Ignatius wanted (to make
  beastmen respect humans, 004 #48). *Costs:* nothing in the text says what race Ignatius is, and it turns
  the Vile Tribe into his tools rather than his people, losing 010 #15 to #17.
- **Recommendation: B**, with C's mirror carried by the dragons' lines instead (006 #5, 022 #6, 023 #19).
  B is the only option that uses the Vile Tribe text the game already has, and it gives Flora's arc (4.2)
  its other half.

**The promise (021 #12).** "Did you not make me a promise, Dragonmaster? A promise that you would cease
your killing...?" When was it made? **Suggested:** at Sungrid Bridge. Ignatius came for the goddess
himself, recognized her in the human girl, and would have killed Jian; Lucia, who did not know what she
was, offered to go quietly if he let Jian live and stopped the killing. He agreed, and kept it. That one
change fills three gaps at once: the promise's origin, why Jian "fought Gideon" at the bridge and remembers
nothing (021 #1: Ignatius put him down), and why Lucia "crossed Sungrid Bridge of her own accord" matters
(016 #7). It also makes the Grand Hall Lucia's second rescue of Jian, and his promise to protect her
(004 #81) the debt he is paying back. *Cost:* a new beat in the Sungrid Bridge cutscene (016) with Ignatius
present for a few lines, and a rewrite of the Jude scene after it: as written, Ignatius hears from Jude
that "that girl is the one" (016 #7), so he was not at the bridge. A cheaper variant keeps Gideon taking
her and has the bargain made by Gideon's prisoner at Vile Castle (she trades going quietly for the lives
Gideon has been taking); it explains the promise but not Jian's lost memory.

### 11.2 When he should appear earlier

Today the player meets Ignatius in person in the last act. Four places to bring him forward, cheapest
first:

1. **The resonance, in skits** (cheap). Titus says Jian and Ignatius feel each other (004 #82); the White
   Dragon confirms it (006 #5). Jian says so in skits 6.6.2 (after the Red Dragon), 6.6.7 (the final
   dungeon), and 6.6.8 (the Chamber). No cutscene work.
2. **Sungrid Bridge** (a 016 edit). He takes Lucia himself and makes the promise (11.1). The player sees
   his face, his manner, and his one virtue, before the Grand Hall.
3. **The Cathedral of Althena** (a 015 edit). He planned to occupy the Cathedral to draw her out (016 #7),
   and the people there are turned to stone (rows 68 to 71). A few lines from him over the petrified
   congregation, gone before the party arrives, would put a person behind the stone. *Cost:* he would be
   in Caldor while Lucia is in the party; he must not notice her (or the bridge scene loses its surprise).
   Optional.
4. **After each dragon** (a small cutscene addition each, or skits). The resonance runs both ways: as each
   dragon falls, Jian hears him, once, briefly: "Thank you, boy." The player understands the manipulation
   (021 #22) before Jian does. *Cost:* four short additions; the payoff is that 021 #22 lands as dread,
   not exposition.

**Recommendation:** 1 and 2 for certain, 4 if the dragon cutscenes are touched anyway, 3 only if it reads
well in play.

### 11.3 What the fight is about

Two arguments, both already in the text:

- **One hand or many.** Ignatius: "this world only needs one all-powerful being" (021 #31). Althena: "Each
  of you are already, in your own way, just as powerful as I ever could be" (021 #32). This is Jian's
  go-it-alone flaw and Ignatius's creed, and the fight is where it is settled.
- **Love that takes, or love that lets go.** Ignatius: "Love takes, unsparingly" (021 #24, the Arishima
  title). He is half right about Jian: Jian's whole quest has been getting Lucia *back*. Today Althena
  answers him. **Suggested:** Jian answers. "You're right. I came to take her back. ...So she chooses.
  Not me. Not you." Then he gives the rings away (021 #26, kept) and Althena gives her power to everyone
  (021 #32, kept). His answer is what lets her choose.

**The shape of the fight (suggested).** Ignatius, refused a duel by a boy who has just given up his power,
reaches for the power Althena is releasing ("If no one will hold it, I will"). He becomes the final boss:
one man trying to hold what was meant for everyone. The party fights him **together, each with a dragon**:
Althena returns the four rings, not to Jian alone but to all of them, and design 10 already lets every
character wear one in their own ring slot. No Dragonmaster wins the last fight; three people with a dragon
each do. The gameplay says the theme.

**What has to be built** (not now; noted for later): a winnable Ignatius battle (today he has only battle
type 0x11, docs/re-enemies.md), new boss stats, and the Chamber cutscene (021 #24 to #40) rewritten around
it. Gideon 2 and 3 stay as the gates before the Chamber.

### 11.4 The ending: the fall replaced

Today: the hostage gambit, an unexplained interruption, the fall, the refused hand (021 #34 to #38).

- **Option 1. Beaten, he refuses the hand.** The power he grabbed is too much for one: it burns out of him,
  the Chamber breaks, and he hangs over the drop. Jian reaches (021 #38, kept: "No! Don't let go!").
  Ignatius chooses to let go, with a last line that is his creed turned on himself ("Let go, boy. One of us
  should learn how."). Then "In the end, who did I save? No one..." and Flora's "you protected us, didn't
  you? I'm still in one piece" (021 #40), kept. *Cost:* least change to 021; keeps every good existing line.
  The hostage beat can stay before the fight, as Flora's test (4.5).
- **Option 2. Beaten, he takes the hand.** He lives, powerless, and walks back to the Frontier to his
  people. *Gives:* the Vile Tribe an ending with a face. *Costs:* no reckoning for Rufus or Gabryel's dead;
  a villain with four scenes gets a redemption he has not earned.
- **Option 3. He lets the power go himself.** At the end he does the thing he could not do: opens his hand.
  It costs him his life. *Gives:* the theme completed by the villain. *Costs:* the same as 2, and it takes
  the last choice from Jian.
- **Recommendation: 1.** With choice 8 (6.6.9) deciding only whether Gabryel's hand or Jian's own will
  lowers the sword before he reaches.

After the Chamber: Gabryel's "this Cathedral is rapidly becoming unsafe!" (021 #40), the escape, and the
ending (chapter 12), with one line each for Gabryel (3.7), Flora (4.7), and Zethos (7.4), and the Vile
Tribe given one image: Lind under a green sky.

### 11.5 Open questions for Jeff

1. **History A, B, or C?** *Recommendation:* B.
2. **Does Ignatius take Lucia at Sungrid Bridge himself, and is that where the promise is made?**
   *Recommendation:* yes; it is the cheapest change with the most payoff in the game.
3. **Who fights the final battle: Jian alone, or the party with a ring each?** *Recommendation:* the party.
4. **The fall: option 1, 2, or 3?** *Recommendation:* 1.
5. **Should the Cathedral appearance (11.2 item 3) happen?** *Recommendation:* only if the bridge scene
   alone feels too late in play.

---

## 11a. The ending as decided (Jeff, 2026-10-09)

These are decisions, not suggestions. They replace the options in chapter 11 and the ending notes in chapter 12
where they overlap.

- **Althena stays.** When Ignatius wakes her inside Lucia, she says she had hoped this rebirth could be her
  last: that she could find happiness as a human, die, and pass her power on. This conflict has proved the
  world is not ready for that yet, so she must stay. **She never releases her power.** (This keeps the
  Japanese Lunar 1 and 2: she is still the goddess until Dyne, and Luna is her last rebirth; the hope she
  voices here is the one Lunar 1 finally grants her 500 years later.)
- **The final battle is the party's.** Jian and whoever else is in the party at that point, and the player
  chooses who fights, against Ignatius himself. He is a real, winnable boss. (Vanilla: an unwinnable fight
  in the Grand Hall, battle id 0x11, enemy row 155, HP refilled every hit by func_02053384; the last bosses
  are Gideon. The engine already has his battle sprite and a boss-battle path.)
- **The fall follows the fight.** After Ignatius is beaten, the walkway crumbles under him as a result of the
  battle, not of any power release. Jian reaches out; Ignatius refuses the hand (keep 021 #38 as written).
- **No power release, so no collapsing Cathedral from it.** Any escape sequence is the walkway or the battle
  damage, not Althena's magic leaving the world.
- **The epilogue with Titus is gone.** Lucia does not leave "with some other guy." The ending belongs to
  Jian and Lucia (chapter 12 has the fountain reunion options; Althena staying means Lucia is Althena-aware
  from here on, so the reunion is a goddess choosing to keep her ordinary life beside him for now).
- **Althena's nature, decided (Jeff, 2026-10-09):** her vessel wears out, so she must be reborn, grow up, and be
  strong enough to take the power up again; she has no memory of being Althena until she is awakened, then
  remembers everything (including the human life), and keeps that memory even after releasing the power
  (this is Lunar 1's Luna and Lunar 2's Goddess Tower recording). The villain's control can suppress her
  awakened self for a while (Ghaleon in Lunar 1, Ignatius here). She confesses to Jian's party, privately,
  what the Japanese Lunar 2 actually says (first-hand transcript, docs/research-lunar-lore.md correction):
  the people of the Blue Star begged her for salvation, she and Lucia "barely" sealed Zophar, the star she
  was entrusted with went into its long sleep, and she brought the few survivors to a dead moon and has
  spent every life since managing its magic to wake it. The wound is a world she could not save and a seal
  that barely held, not a destruction by her hand (the "destroyed it as the price of the seal" line is a
  Wikipedia claim the game does not contain). The cost she admits only in private is the one Lunar 2's Blue
  Dragon starts to say and Lucia silences: what using her power to seal Zophar means for this world. **Being the goddess is her self-inflicted penance** for the Blue Star she could not save: each rebirth is
  another term served, the power is the weight she chose to carry, and "the world is not ready" is also "I
  have not finished paying." Lucia's rebirth was meant to be the one where the debt was paid and she could
  set it down; Ignatius proves it is not, and she takes it up again. Lunar 1 then becomes her release, not
  her retirement: Dyne is the one who finally lets her forgive herself. Her lesson to Jian ("the bravery to
  forgive") comes from someone who has never forgiven herself; Ignatius wants the power as a crown, she
  carries it as a sentence. Write the rest ("I still must rest sometimes") as weariness under that sentence,
  never as mere fatigue.
- **What binds her (Jeff, 2026-10-09, from the Japanese Lunar 2):** her power is committed to restoring the
  Blue Star, not to Lunar. Canon: the Goddess Tower / the magic city Althena exists "to send all of this
  world's magic to the Blue Star... everything is for the regeneration of the frozen Blue Star; that is the
  purpose this world was created for" (Saturn Lunar 2, 1506 @0x9E6, @0xAE0); the Blue Dragon starts to say
  what sealing Zophar with her power means "for this world" and Lucia silences him in front of the humans
  (1483 @0xB8E); old Luna's last-rebirth reason is realizing "Lunar does not exist only for the Blue Star"
  (O065). So in Dragon Song she cannot release her power into Lunar because most of it is owed elsewhere,
  and she has not yet let herself see Lunar as a home rather than a waiting room. The line to aim at: Lunar
  is something new, its people would not go back if they could, and she is the last one to believe it. Dyne,
  500 years later, is the one who frees her of it; Dragon Song plants the seed and leaves it.
- **Jian plants the seed (Jeff, 2026-10-09):** in the Chamber of Rebirth Jian is the first to say it to her
  (Lunar is a home, not a waiting room; its people would not go back if they could; her work today is her
  guilt, not what is best for them now). She almost hears it and cannot accept it, because accepting it means
  forgiving herself; she takes the power back up. Dyne gets the second try, 500 years later.
- **Lucia's human mirror (Jeff, 2026-10-09, shape decided; the event is his to pick):** Lucia the human has
  something of her own she cannot forgive herself for, and Jian's relationship with her, which never asks her
  to earn it, pushes her toward forgiving herself as a human before the Chamber of Rebirth shows the same
  wound at the goddess's scale. Write the human beat first (Port Searis to Sungrid Bridge, in skits and one
  scene), so the goddess scene is a recognition, not an explanation. Candidates, cheapest rhyme first:
  (1) **a late delivery**: before Searis something she carried arrived too late and someone paid for it;
  hence never late, hence the courier job, hence "You're late, Jian. Again" cuts deeper than a joke; this is
  "they begged me and I barely made it" at the size of one village (recommended); (2) **someone she left
  behind** to have a life of her own (her want becomes her guilt); (3) **someone hurt because she froze**,
  which is why Jian's recklessness, which she scolds all game, is what she wishes she had.
- **Dragon Song is the exile (decided):** the Frontier is already the rebels' prison (004 #78), Ignatius leads
  the Vile Tribe out across the world, and the ending seals the Frontier; from 500 years later that is the
  Japanese Lunar 1 line "the Vile Tribe that tormented people lived in this world; Althena exiled them to the
  Frontier and sealed them" (Mega CD C021 @0x265D). No plot change needed; the seal is the thing Lunar 1
  remembers.
- **The Dragonmasters, named in the Story edition (decided):** Louie (ルイ), who came with Althena from the
  Blue Star and turned the dead world green, is named in the intro. The later line (Zeon, Loka, the gold and
  silver sisters Asti and Liza [Mega CD names; the Saturn calls them Alicia and Rina], Dyne, Alex) is future
  history relative to Dragon Song and may be seeded as prophecy or left for Lunar 2 players to recognize.
  Jian is not on that list because he gives the rings back and says "I don't want to be a Dragonmaster"
  (021 #26); keep that line. Ignatius is not on it because he fell. The first Dragonmaster came with
  Althena long before this story (do not use "greened the world" in our text); Ignatius is only the latest.
- **Keepers from the vanilla climax:** Jian giving back the Dragon Rings (021 #26), "You fear yourself"
  (021 #28), the reached hand (021 #38), Althena's "the future must come from each one of you" as the thing
  she wants and is not yet allowed to do.

## 12. Jian and Lucia

**As written** (story-characters.md 1.4, 2.4, 8; docs/story-npcs.md 2.2): the bond is the plot's engine
and has the least intimate material in the game. 55 shared messages, mostly about the job or his
recklessness. They met over a year ago, when she was carrying an umbrella (001 #83); they have been
couriers together "recently" (001 #81); the fountain is "the usual place" (001 #53, Japanese only). He
promised to protect her (004 #81, 010 #62), never shown. She left him an anniversary gift with Gad the
morning the game starts (001 #20, #21), very likely the Bell Shoes, "Gift from Lucia, but details are
unknown" (inference from list order, story-characters.md 2.5). The English added the romance ("I love
you! Lucia!", 021 #32, is not in the Japanese, which has only her name); the Japanese gives a family-like
bond ("more precious than a real sibling", 010 #62). The ending does not reunite them: Jian is absent
(026 #3). The shipped opening run says "Lucia and I haven't been partners long" (feat_opening.py), which
fits "recently teamed up" and not "over a year" unless they knew each other before they worked together.

Everything below is **suggested**.

### 12.1 The first meeting

The text has: an umbrella, over a year ago, and Lucia's habit of leaving her umbrella (or parasol) as a
sign of where she is (001 #138: "if she left this behind... she can't have gone far. I'll just wait
here").

- **A. Rain at the fountain.** A year ago, a girl stood in Fountain Square in the rain under an umbrella,
  with nowhere to go and not much to say about where she came from (the goddess, newly human, her memory
  sealed, 004 #80). Jian, late for something as usual, stopped. He found her a room and walked her to
  Gad's. Months later, when Gad needed a second courier, he vouched for her. *Fits:* the umbrella, "over a
  year" since meeting and "recently" partners (both true), "the usual place", the town treating her as a
  girl Jian looks after (001 #103), her fear of the dark, and why a goddess hiding would end up beside him.
  *Cost:* a sharp player will guess she is not ordinary. That is fine; the game tells you at Titus's
  anyway.
- **B. A new courier, lost.** Gad hired her and paired her with Jian; on her first job she got lost in
  Thieves' Woods after dark and he found her. *Fits:* her fear of the night (001 #140). *Cost:* makes them
  partners from day one, against "recently" (001 #81) and the shipped run line.
- **C. She found him.** He was doing handstands at the fountain for tips and fell; she held her umbrella
  over him. *Fits:* uses the handstand once, warmly. *Cost:* the least weight; the protecting runs the
  wrong way for the promise.
- **Recommendation: A.** It reconciles every date in the text with the shipped opening line.

**Where it is told:** never as a flashback. Jian tells part in a skit (2.6.3 or a Fountain Square chat on
the return home after the Grand Hall, 0xC9), and the ending shows it again (12.4).

### 12.2 The promise

- **A. His, the day they met.** "I'll look out for you." Said lightly, to a stranger in the rain, and he
  has meant it every day since. *Fits:* 004 #81 and 010 #62 exactly, and why she "needed protecting"
  before anyone knew her secret: she had no one.
- **B. Hers, turned around.** She made him promise to stop running ahead, and he made it "I'll protect
  you" because that is the only kind of promise he knows how to make. *Fits:* his recklessness; skit 2.6.5
  ("That's my line." "Not today.").
- **C. Both, and a third.** His promise (A), her small one before the tournament (2.6.5), and her real one
  at Sungrid Bridge, made to Ignatius for Jian's life (11.1). The game then turns on the fact that she
  kept hers first.
- **Recommendation: C.** A is the root, 2.6.5 is the echo, and the bridge bargain is the twist that the
  Grand Hall reveals ("Did you not make me a promise?", 021 #12).

### 12.3 Her want, and how he sees it

Lucia wants one ordinary life she chose (2.2 A). Jian's flaw is that he loves her by holding on (Ignatius
is right about that, 021 #24). The bond grows when he notices what she wants and lets her have it:

- the parasol she talks herself out of (2.6.4, choice 2);
- the coin in the Healriz fountain (004 #115): she will not tell him the wish; in the ending, she does;
- the fireplace she calls romantic (001 #118): Cherenkov's lobby;
- the gift she arranged for him as a delivery (001 #20): she plans happiness on a schedule.

### 12.4 The reunion (the new last scene)

**Suggested**, replacing the one-line Lucia of 026 #3 and Jian's absence:

1. Some time later, Gad gives Jian a pickup at Fountain Square (8.4). He knows; Jian does not.
2. A girl stands at the fountain under an umbrella, or, if choice 2 was YES, the parasol. It is not raining.
3. She does not know him (2.7 question 2). "Are you from Gad's Express? I was told to wait here." He has
   every line ready and says none of them ("......", the Japanese silence, used once more).
4. If choice 3 (Sungrid Bridge, "are you scared?") was YES: she says, without knowing why, "You look
   scared." If NO: "You look like you're about to lie to me." Either way she smiles, as if at something she
   almost remembers.
5. He says the line from the day they met (12.2 A), lightly, as then.
6. Lucia, borrowing her own line from the ending as written (026 #3, "Come on, Titus, you slow-poke!"):
   "Come on, Jian, you slowpoke! We'll be late!" The closing narration follows (9.4).

*Cost:* a new ending cutscene in 026 (the Titus and Peles exchange shortened to set it up). *Alternative:*
she remembers him at once and runs to him. Warmer, shorter, and it skips the repeat of the first meeting;
Jeff's call (2.7 question 2).

### 12.5 Scene placements, in story order

| Beat | Where | Status | Section |
|---|---|---|---|
| The wake-up, "she left already" (she is at Gad's with the gift) | Jian's room, Inn | exists (shipped); the reason is hidden | 1.6.1 |
| "The usual place": the fountain, her umbrella | Fountain Square | exists (001 #53 Japanese, #83, #138) | restore #53 |
| She will not say where she was | Fountain Square skit | to create | 1.6.1 |
| Walking on the dark side of the path | Thieves' Woods | to create | 1.6.4, choice 1 |
| His home is a rented room | Delrich Temple | to create | 2.6.3 |
| The parasol | Healriz | exists as trivia (004 #101) | 2.6.4, choice 2 |
| Her promise before the tournament | Healriz | to create | 2.6.5 |
| She fights a king for him | Zethos Castle | exists, needs a new cause | 10.4 |
| "Are you scared?" and why she crosses | Sungrid Bridge | to create | 2.6.8, choice 3 |
| Her bargain for his life | Sungrid Bridge | to create | 11.1 |
| Her second rescue: "Did you not make me a promise?" | Grand Hall | exists (021 #12) | 11.1 |
| The gift, delivered | Gad's Express | exists (001 #17 to #29) | 8.4 |
| Gabryel and Flora carry her in his absence | skits | to create | 3.6.4, 3.6.8 |
| "Love takes", answered by Jian | Chamber of Rebirth | to create | 11.3 |
| Lucia still in there: the line from the bridge | Chamber | to create | 2.6.8, choice 3 |
| The reunion | Fountain Square | to create | 12.4 |

### 12.6 Open questions for Jeff

1. **Romance, family, or undefined?** The English made it romance; the Japanese keeps it family-like and
   unspoken. *Recommendation:* unspoken and unmistakable. Nobody in the pair says "love"; everyone around
   them can see it (Marcella's "Your little boyfriend", 004 #56; Flora's "you and your two girlfriends",
   010 #59).
2. **First meeting A, B, or C?** *Recommendation:* A.
3. **Does she remember him at the reunion?** *Recommendation:* not at first (12.4).
4. **The shipped run line** "haven't been partners long": keep it (true under 12.1 A) or change it to "a
   year" (1.7 question 1)? *Recommendation:* with 12.1 A it can stay as is: they met a year ago and have
   been partners only a few months. This supersedes 1.7 question 1 if you pick A.

---

## 13. Appendix

### 13.1 Choice ledger

28 choice flags (0x244..0x25F) make 14 two-sided choices (docs/re-party-chat.md section 9). Proposed here:

| # | Skit | Question | Later effect | Cost |
|---|---|---|---|---|
| 1 | 1.6.4, Thieves' Woods | "Are you walking on that side on purpose?" | one line in 2.6.8 | cheap (chats only) |
| 2 | 2.6.4, Healriz | "Should I buy it?" (the parasol) | the reunion (12.4) | ending edit |
| 3 | 2.6.8, Sungrid Bridge | "Are you scared?" | Althena's line in the Chamber; the reunion | 021 and ending edits |
| 4 | 3.6.6, road to Leephon | "Do you hate them? Beastmen." | one line in 3.6.7 (or the Zethos scene) | cheap (or a 009 edit) |
| 5 | 4.6.4, Titus's house | "Did you miss me?" | one line in 4.6.8 | cheap |
| 6 | 4.6.6, Rebric | "Would you come and see the tunnel?" | Flora's ending line | ending edit |
| 7 | 5.6.2, Elda Canyon | "Do you still not want me here?" | one line in 5.6.5 | cheap |
| 8 | 6.6.9, Chamber empty | "Are you going to finish him?" | the end of the fight (11.4) | 021 edit |

Eight of fourteen; six left for Jeff's own. No choice lets the player pick the old flaw back (1.6.7).

### 13.2 Fluff gates that touch a character beat

From docs/story-npcs.md section 4. Where a talk-to-this-NPC-first gate sits on a character beat, the skit
can carry the information instead and the gate can go:

- **Port Searis: Cherenkov, then Jack, then Lucia** (4.1). Already cut (the run sets the flags). The
  Japanese "usual place" (001 #53) should come back in Cherenkov's line, since it is the first fact about
  Jian and Lucia.
- **Perit: Enos waits until Hagar or Micah has been seen** (4.2). Skit 2.6.2 (Lucia and the frightened
  villager) can name the woodsmen; better, let Enos talk at once.
- **Healriz: the seven-step tournament chain** (4.3). The beat it delays is Jian's reason for the tournament
  (1.6.2). Suggest: Leoncavallo asks for honey directly, Marcella's step goes, and skit 2.6.4 carries the
  Marcella hint only if the step stays.
- **Port Olbeage: Carducci plus three guards before Gabryel's emblem scene** (4.4). The emblem scene is
  Gabryel's best early beat (007 #78 to #80); one guard is enough (skit 3.6.2).
- **Ghulian: Roxane before Kirlis; Tovia's trick question (YES ends the talk, only NO gives the anthodite
  lore); Saul before the treasures** (4.6). Flip Tovia's answers, and let the anthodite skit (rows 14 to
  16) name Tovia.

### 13.3 If you read nothing else: the five that matter most

1. **Ignatius takes Lucia at Sungrid Bridge, and she bargains for Jian's life** (11.1). It explains the
   promise of 021 #12, Jian's lost memory of the bridge (021 #1), and makes the Grand Hall her second
   rescue of him. One cutscene.
2. **The final fight is the party, each with a dragon ring** (11.3), after Jian answers "love takes"
   himself. The rings already work this way in design 10; the theme and the gameplay say the same thing.
3. **Rufus finishes his sentence before he dies** (skit 5.6.5). The cheapest, most important skit for Jian
   in the game.
4. **Lucia wants one ordinary life she chose** (2.2 A), met in the rain at the fountain a year ago (12.1 A),
   and the ending repeats that meeting (12.4) with "Come on, Jian, you slowpoke!".
5. **Ignatius is the exile's son** (11.1 B), so the Vile Tribe's grievance (010 #15 to #17) is real, Flora's
   arc has its other half (4.2), and the two NPCs who ask why the Dragonmaster turned (008 #21, 015 #67) get
   an answer.
