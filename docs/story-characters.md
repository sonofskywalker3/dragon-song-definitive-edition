# The cast as the game writes it (research 2026-10-09)

What characterization already exists in Lunar: Dragon Song's text, character by character, so Jeff can
decide what to keep, sharpen, or create for the Tales-style skits and the story rewrite
(story direction: keep the plot, cut fluff and the curse, give a real final fight with Ignatius).
The one-page assessment is at the end (section 11).

## 0. Sources and how to read the citations

- **Every English message** of every event script (USA script.dat, scripts 001 to 026), read in full,
  with the Japanese of the same message op beside it. Dump them with the new tool:
  `uv run python -m dsde.text_dump` (writes `build/text/script_NNN.txt`, USA then JP per message), or
  `uv run python -m dsde.text_dump --grep "Ignatius"` to search. Source: src/dsde/text_dump.py. Needs
  `build/unpacked/script/` and `build/unpacked_jp/script/` (docs/re-japanese.md, "Getting at the text").
  The USA and Japanese scripts have the same message ops in the same order (op counts match in every
  script but 018), so the pairing is exact outside 018.
- **Party chat** (script 018, the Y button): `uv run python -m dsde.jp_hint_pairs`, already compared line by
  line in docs/re-party-chat-japanese.md.
- **Item and menu text** (sysmenupack 057/058, arm9 string tables): checked for character content. There is
  no battle dialogue in the game's text at all (the cast's names occur only in script.dat, the sound test
  list in sysmenupack 060, and status screen titles), so "battle lines" contribute nothing.
- Background: docs/story-party-timeline.md (who is in the party when), docs/intro-analysis.md (script 026),
  docs/design.md section 11 (the curse decision), docs/re-enemies.md (boss list).

**Citations.** `004 #81` means script 004, message op 81 in the text_dump output (one op can hold several
speakers and pages). Party chat lines are cited by their USA leaf offset, `018 leaf 0x5858`, which is the
key both jp_hint_pairs and docs/re-party-chat-japanese.md use. Japanese is quoted in the game's own
spelling (mostly kana) with a gloss; translations are ours. **(inference)** marks a reading that the text
suggests but does not state.

### Volume, as a first impression

Speaker turns across all scripts (a turn is one speaker tag; repeated messages counted once):

| Jian | Gabryel | Flora | Lucia | Zethos | Ignatius | Titus | Rufus | Althena | Gad | Peres |
|---|---|---|---|---|---|---|---|---|---|---|
| 561 | 292 | 166 | 153 | 59 | 47 | 45 | 32 | 21 | 15 | 15 |

Gabryel speaks twice as much as Lucia, the heroine, and Ignatius has fewer turns than Zethos. All but one of
Lucia's 153 turns fall in the first third (she leaves the party at Sungrid Bridge; the last is in
the ending).

---

## 1. Jian Campbell

### 1.1 What the text establishes

**Shown by action (cutscenes):**

- **He fights to prove humans are equal, and stakes his life on it.** He demands to enter the beastmen's
  tournament instead of watching it: "I don't intend to sit in the stands. I want to fight..." (004 #45).
  When Leoncavallo asks why: "If I can display the bravery and strength of a human in front of so many
  beastmen... You may rethink your ideas about humans. We may even come to understand each other!"
  (004 #48). At the Coliseum: "I'm gonna show them all that humans are no different from beastmen!"
  (005 #57). This is his only self-chosen goal before Lucia is taken.
- **He carries a grudge against beastmen that he does not see in himself.** To Zethos: "Unlike humans,
  beastmen don't seem to be able to believe in themselves, do they? You're really making me glad that I
  wasn't born a beastmen!" (009 #13, the same in Japanese). To Gabryel: "You beasts do little but mock us
  humans, I know... But you are the exception, Gabi... Most beasts, well..." (009 #19). Rufus names it:
  "I know you don't think much of us beastmen. I can live with that." (020 #6). Jian never answers him.
- **He goes it alone, again and again.** He tells the girls to stay behind at the Cathedral (018 leaf
  0x564c), tries to leave Gabryel and Flora at Titus's house (004 #88, Gabryel: "The brave knight protecting
  the poor defenseless princesses, is it?"), sends them both away before Elda Canyon ("you'll only get in my
  way. I have to carry on alone.", 019 #0), and tries once more before the airship (025 #15, Gabryel:
  "This act is getting old! How many times are you going to try and ditch us?"). His private reason,
  in the party chat: "I can't put either of them in any further danger..." (018 leaf 0x5908).
- **He refuses help from a beastman and picks a human guide**, cutting Rufus off in front of everyone:
  "Sorry, but no thanks!... I would like our guide to be... you, Flora" (010 #62).
- **He gives up power for Lucia at the climax.** He hands Althena the four Dragon Rings: "I don't want to
  be a Dragonmaster. I just want to go back to Searis, with Lucia." (021 #26) and faces Ignatius unarmed.
- **He tries to save his enemy.** He grabs the falling Ignatius: "No! Don't let go! Ignatius!" (021 #38),
  then: "Ignatius... I couldn't save him... In the end, who did I save? No one..." (021 #40).

**Only told (by others, or by Jian about himself):**

- "My name is Jian Campbell... I love acrobatics and standing on my head, and I do have quite a soft spot
  for Lucia... maybe!" (001 #81, the opening monologue). The Japanese lists it as a skill outright:
  とくいワザは　さかだち！ ("My special skill: handstands!") and たいせつなものは　やっぱり　ルシアかなぁ？
  ("The thing that matters most to me is... Lucia, I guess?"). This is Jeff's "skill, not trait" line,
  and it is literally labeled a skill.
- Reckless, by town consensus: "Your recklessness is your biggest flaw." (Ikey, 001 #101); "You always
  ignore my advice, you always come back alive" (Hiram, 001 #96).
- Lazy and late: "late again as usual" (Gad, 001 #17), "I wish I could afford to oversleep every day!"
  (Cherenkov, 001 #52), "She's always angry when I oversleep!" (Jian, 001 #82).
- He has promised to protect Lucia: "I promised that I would protect her." (004 #81; again 010 #62). The
  promise is never shown (section 1.4).
- Knows odd things: "It burns with oil from a plant called the Goatweed." / Lucia: "You sure do know a lot,
  don't you Jian!" (003 #32). Books make his head hurt (001 #79, 007 #60). These do not add up to anything.

**Wants and fears.** Wants: first, to make beastmen respect humans (004 #48); after Sungrid Bridge, only
Lucia ("I just want to save Lucia! That's all.", 011 #35; "Althena this... Althena that...! I want to save
Lucia! That's all!", 004 #81). Dragonmaster is a means: "I desperately need that power to save Lucia!"
(001 #67); "I haven't decided that yet..." (018 leaf 0x5f5c). Fears: failing to protect her ("I failed to
protect her, Gad! I'm not worthy of her gifts...", 001 #22). No fear for himself is ever voiced.

**Relationships.** Lucia (partner, the axis of everything, section 1.4); Gabryel (121 shared messages, the
most of any pair: she manages him, scolds him, and pulls him out of despair); Flora (79; she teases, he
apologizes to her twice, 023 #3, 024 #1); Rufus (11; distrust, then debt); Gad (boss, tough love).

### 1.2 Voice

- **English:** an eager, slightly cocky young man who swings between bravado ("I'd expect no less! Now
  shut up and fight!", 009 #54) and stiff formality ("Then we will head straight over there.", 003 #56;
  "You are... madam...?" to the Red Dragon, 017 #3). He fills silences with agreement ("...That's right.",
  "...Yes.").
- **Japanese:** rough boy's speech with オレ (87 times), sentence-final ぜ (心して　行こうぜ！, 018 leaf
  0x5778), きさま for enemies, and ちくしょう-type curses (くそっ). He switches to polite です/ます with elders:
  見たいんじゃありません。出たいんです ("I don't want to watch. I want to fight", to Leoncavallo, 004 #45);
  he calls Lucia and Flora きみ. Above all, **his silences are written as silences**: …………。 where the English
  gives him a line (018 leaves 0x5f5c, 0x62a4, 0x5858, 0x5a0c, 0x62d8; docs/re-party-chat-japanese.md 1.2).
- **What the English changed** (all checked against the Japanese):
  - Added romance. "Unlike him, I have someone to protect... Someone I love!" (006 #8) is
    まもるべきもの…　あいすべきものが　あるかないかのちがい ("the difference is having something to protect...
    something to love"), abstract and impersonal. "Lucia means more to me than a sister! She means...
    everything to me!" (010 #62) is 本当のきょうだい　いじょうに　たいせつな存在 ("more precious than a real
    sibling"). The final "I love you! Lucia!" (021 #32) **is not in the Japanese**, which has only "Lucia,
    answer me! Luciaaa!". The English turns an ambiguous, family-like bond into a declared romance.
  - Added vengeance. Jian's battle cry "Revenge!" against Gideon (021 #15) is a wordless ぬおぉぉぉ〜っ!
    "I swore to protect her... which means every last one of you is going to pay" (020 #0) is "I won't
    forgive you! I'll never forgive you!". The English then contradicts itself in the chat, where Jian
    insists "This is not merely about revenge" (018 leaf 0x62a4).
  - Added crudeness. "She's going to be hot when she hits twenty!" (004 #11) is only "Althena statues look
    a bit like Lucia... why is that?" in Japanese: the English trades the foreshadowing for a leer.
  - Added a running joke at Lucia's expense: "Nothing like your famous 'Charcoal Surprise', Lucia." (001
    #69, Japanese: "Lucia doesn't cook, so... I'm a little envious") and "Plenty of room for Lucia to burn
    things in here!" (007 #93, Japanese: "Lucia would be amazed to see this").

### 1.3 Arc as written (story order)

1. Port Searis: carefree, oversleeps, teases Lucia ("Your cute face will get all wrinkled", 001 #140).
2. Perit / Healriz: volunteers before he is asked ("It was obviously going to happen. I was just speeding
   the process up a bit.", 003 #56); decides on his own to fight in the tournament for human dignity
   (004 #45, 004 #48). **This is the most active, self-motivated Jian in the game.**
3. Coliseum and curse (005 #57 to #71); Zethos: righteous anger, and the "glad I wasn't born a beastman"
   speech (009 #13).
4. Sungrid Bridge: Lucia taken. From here his want narrows to her alone ("I don't care about this Ignatius
   guy. But I must save Lucia, no matter what!", 010 #63).
5. Ignatius crushes him (021 #4 to #12). Back home he breaks down (001 #17 to #29): "I failed to protect
   her". Gad's tough love and Gabryel's plan restart him; Gad: "Depressed one minute, hyper the next"
   (001 #29).
6. The four trials, each a lesson **told by a dragon**: perceive truth (White, 006 #7, #9), willpower and
   the cost of winning (Red, 017 #5, #6), the evil inside oneself (Black, 022 #6; the boss list has a "Dark
   Jian", docs/re-enemies.md, which fits this trial, inference), listen to companions (Blue, 023 #21: "To
   be open to what others have to say... A pure heart, always valuing the opinions of companions.").
7. Airship: tries to go alone again (025 #15). **The Blue Dragon lesson is undone one scene later.**
8. Climax: gives up the rings (021 #26), preaches against "the circle of hatred" (021 #28), then breaks
   ("This is unforgivable!", 021 #31) until Althena asks him to forgive; he reaches for the falling
   Ignatius (021 #38).

**Growth asserted but not shown.** The dragons and Titus declare him pure-hearted and chosen ("You really
are the chosen one", 004 #90; "all four Dragons are with you, always!", 004 #93); Peres says "He appears
to have a dream... A dream that may save the future for us all" (010 #64) while Jian has just said his
only dream is Lucia. The "listen to companions" lesson is stated, not earned, and broken at once. His
prejudice against beastmen is never reflected on by him: Zethos apologizes for the beastmen (009 #20),
Gabryel lectures (020 #6), and Jian's only answer is the later chat speech about Rufus's sword (018 leaf
0x62a4, "He was our comrade... our friend").

### 1.4 Contradictions and gaps

- **Why does Jian go along at the start?** Nothing drives him in Port Searis but the delivery and, later,
  the tournament. Before Sungrid Bridge, his reason for following Gabryel is the curse (005 #71: "You'll have
  to meet with him if you want the curse to be lifted"). Remove the curse and Jian has no reason of his own
  to go to Leephon (section 9).
- **The promise.** "I promised that I would protect her" (004 #81, 010 #62) is the stated core of his
  motive; there is no scene of it, no account of when, and no reason given why Lucia would need protecting
  before her secret is known.
- **How long have they been partners?** "This is the umbrella Lucia was using when we first met... it's
  been over a year already" (001 #83, same in Japanese) against "recently I teamed up with this girl"
  (001 #81, Japanese ちょっとまえから, "for a little while") and "Today is the day we first met!" (001 #21,
  the gift scene, so at least a year).
- **No past.** No family, no hometown, no reason he is a courier; he lives in a room at Cherenkov's inn
  (001 #57, 011 #16). A search of the whole script for parents, family, or siblings finds none for him.
- **Skill, not trait.** Handstands are his introduction (001 #81, 026 #0), the curse's target ("No standing
  on my head!", 005 #71), and the Japanese curse name, 天地転とうの呪ばく ("curse of turning heaven and earth
  over"), is a pun on them. None of it says who he is.
- **"Humans are no different" vs his own contempt for beastmen** (009 #13, #19) is the most interesting
  contradiction in him, and the game treats it as a non-issue.
- **Is he a Dragonmaster at the end?** Ignatius says giving up the rings changes nothing (021 #26); the
  closing narration ends on "A day when an adventurer will become... Dragonmaster." (026 #4). Unresolved.

### 1.5 Raw material worth keeping

- The tournament motive and Leoncavallo's "You're staking your life on it, kid... I don't really
  understand it. But I have to say, I've grown to like you." (004 #48). Jian at his best: a reason bigger
  than himself.
- "Unlike humans, beastmen don't seem to be able to believe in themselves... glad that I wasn't born a
  beastmen!" (009 #13): a real flaw spoken in anger. Worth keeping *as a flaw*, then paying off with Rufus.
- The breakdown at Gad's: "No... I can't. I don't deserve it. I failed to protect her, Gad!" (001 #22).
- Giving back the rings: "I don't want to be a Dragonmaster. I just want to go back to Searis, with
  Lucia." (021 #26), and "...And yet you still fear something, don't you. Not me! Yourself!" (021 #28).
- Reaching for Ignatius, and "In the end, who did I save? No one..." (021 #40); Flora's answer "you
  protected us, didn't you? I'm still in one piece" is a ready-made skit seed.
- The Japanese silences (…………。) after "You and Lucia are a couple?" (018 leaf 0x5858) and after Flora
  finishes his sentence "...want to save Lucia. ...Right?" (018 leaf 0x5f5c).

---

## 2. Lucia Collins (and Althena)

### 2.1 What the text establishes

**Shown:**

- **She worries and keeps things on track.** Waited three hours and is still mostly worried about the
  schedule: "If we don't get going soon, we won't make it back before sunset!" (001 #140). When the package
  is stolen: "If Gad finds out about this... Our careers are finished!... We can't let anyone know"
  (002 #1), and she covers it up mid-sentence when Jian starts to tell Moses (003 #13).
- **She tries to stop Jian, then stands by him.** "No way, Jian! No way!... You'll get hurt for sure!
  Maimed, even!" (018 leaf 0x549c); at the Coliseum "Please, oh please, stop this! You've done enough."
  (005 #61), then "Jian, you moron! You loser, you idiot, you fool! You're making me worry so much!"
  (005 #63).
- **She is fierce when he is wronged.** She marches up to the Beast King: "You'd better put my poor Jian
  back to normal right away, or I swear I'll...!... Prepare yourself! I won't hold back!" (009 #48, #50)
  and challenges him to fight. This is the strongest Lucia scene in the game, and it is a curse scene.
- **She turns on Gabryel when she feels deceived, then apologizes first.** "Gabi! If that's even your real
  name?!" (009 #60), then "It was cruel to say those things. I'm sorry." (008 #72).
- **As Althena she acts decisively twice:** she stops Ignatius from killing Jian and Gabryel and sends them
  away (021 #12), and in the Chamber she gives up her power: "This world should be ruled by... all
  peoples... together... The beastmen... and humans... and even the Vile Tribe... must all live together"
  (021 #32).

**Told:** she is lively ("You're quite a... lively girl, aren't you?" / "I shall take that as a
compliment.", 003 #13), not a child ("You make it sound as if... Well, as if I were a child!", 001 #103),
dislikes being out at night (001 #140), loves flowers (001 #109, 003 #44), parasols (004 #101), fireplaces
("They're so romantic", 001 #118), and fountain wishes (004 #115). She is bad at cooking (001 #39).

**Wants and fears.** As Lucia: none stated beyond doing the job well and keeping Jian safe. As Althena:
Titus says she doubted her own position and believed the future should be entrusted "to all the people in
the world" (004 #78), and hid as a human to keep her power from Ignatius (004 #80). Why she chose *this*
life, a courier in Port Searis with Jian, is never said; Jian begs her to remember it: "Remember why you
chose to become Lucia!" (021 #24), and the game never answers.

### 2.2 Voice

- **English:** a bossy, proper girl ("I think that's perfectly reasonable!", 001 #140; "We must not delay
  this delivery any longer!"), with sudden outbursts and puns ("Oh Jian, honey... You found the [honey]!",
  018 leaf 0x5488, an English-only joke).
- **Japanese:** わたし and soft, girlish speech: もう　ジアンったら… (a fond "honestly, Jian..."), sulky
  elongations (ジアンのいじわるぅ！, "Jian, you meanie!", 006 #0; ジアンのバカァ！　もう　バカっ　バカっ　バカ〜っ！,
  005 #63), and a playful sing-song challenge to Zethos (こたえは　ひとォつ！, "There's only one answer!",
  009 #50). As Althena: formal ありません/なのです.
- **What the English changed:** the night line "Girls are all like that" (女のコは　みんな　そうよ, 001
  #140) became "I think that's perfectly reasonable!", losing the joke-hint that she is not quite what she
  seems (inference). The "burnt food" and "Charcoal Surprise" running gag (001 #39, #69; 007 #93) is
  English-only: the Japanese just says she is not good at cooking. Japanese Lucia is softer and more
  childlike; English Lucia is more of a scold.

### 2.3 Arc as written

Lucia has no arc as Lucia. She worries (Port Searis to Coliseum), defends Jian (Zethos), is hurt by and
reconciles with Gabryel (Leephon), and is taken. Althena's arc is told in one block of exposition (004
#78 to #82) and resolved in one speech (021 #31, #32). The ending puts her back as Lucia, traveling with
Titus: "Come on, Titus, you slow-poke! Let's get going!" (026 #3). **Jian is not in the ending text at
all.** Whether she remembers him is not said.

### 2.4 Contradictions and gaps

- **What does Lucia want from Jian?** Nothing in the text. She scolds, worries, and calls him "my Jian"
  (009 #49, Japanese わたしのジアン too), but never says what he is to her. Jeff's question has no answer
  in the game.
- **Why did a goddess pick this life?** Unanswered (2.1).
- **The ending does not reunite them.** Titus explains her rebirth to Peles (026 #1, #2); Lucia appears for
  one line; Jian is absent.
- **Althena's "promise" with Ignatius:** "Did you not make me a promise, Dragonmaster? A promise that you
  would cease your killing...?" (021 #12; Japanese: "Didn't you promise you would no longer hurt anyone?").
  When and why she struck a bargain with her captor, and why he keeps it, is never shown.
- **Her magic fails near Rufus** ("I'm trying! I am! But... it's not working?!", 016 #2) because Althena's
  power is weak in the Frontier (016 #3, #4); nobody connects this to her being Althena.

### 2.5 Raw material worth keeping

- The Zethos confrontation: "Hey, get your paws off me, OK? Is this any way to treat a lady?!" (009 #47)
  and the challenge (009 #48 to #52). Lucia's bravery is real here and should survive without the curse.
- The Gabryel apology: "I didn't wait to hear what you had to say... It was cruel to say those things.
  I'm sorry... And fight back next time, OK?" (008 #72).
- The fireplace, the flowers, the parasol, the coin fountain: small wants that a skit can turn into a
  person (what she would do with a life of her own).
- Althena's thesis: "Each of you are already, in your own way, just as powerful as I ever could be."
  (021 #32). This is the answer to Ignatius and should be Lucia's own conviction, not a goddess's farewell.
- The gift: Lucia left a present with Gad for the anniversary of the day they met (001 #19 to #24); the
  item is most likely the **Bell Shoes**, whose description is "Gift from Lucia, but details are unknown"
  (sysmenupack 058 @ 0x697; the name, arm9 @ 0xA7CC6, is the 14th footwear name and that is the 14th
  footwear description, so the pairing is an inference from list order). Footwear for an acrobat: a tiny,
  real piece of affection.

---

## 3. Gabryel Ryan ("Gabi")

### 3.1 What the text establishes

**Shown:**

- **She opens with a conviction.** Rescuing Lucia from Zethos's blast: "...A beast? Is that what you want
  to say? But aren't humans and beastmen the same? Both blessed by Goddess Althena" (005 #68).
- **She is a princess traveling in secret, and handles authority with style.** She flashes the royal emblem
  at the Olbeage checkpoint and sweeps through: "Does it really matter? So, what's it to be... Am I allowed
  through, or not?" (007 #78), then "What do you think, muscle head?... What do you think of me now?"
  (007 #80).
- **She recruited Jian for her father, hid it, and it breaks her.** "Papa, I can't do this any more!
  Please, no more... I'm so sorry!" (009 #61).
- **She chooses her own path.** "I'm not going to do my father's bidding any longer. It's time I decided my
  future for myself!" (008 #73), and leaves without telling him.
- **She is the one who restarts Jian.** After Ignatius: "There could be a hundred of us, an army, and we
  could still never defeat Ignatius!... Let's try asking my father." (001 #26); "Get down off the fence! I
  want a decision! Yes or no?!" (001 #143).
- **She refuses to be left behind**, every time (004 #88, 019 #0, 025 #15), and at Elda Canyon she comes
  back with Rufus: "He's not stupid enough to turn us down this time. Right, moron boy?" (020 #4).
- **She is the team's voice on race:** "We're friends now! Comrades! Does human this or beast that really
  make any difference? No!" (020 #6).
- **She works out the White Dragon puzzle** (013 #22) and the Blue Dragon's answer ("Jian, don't think too
  hard!", 023 #19).

**Told:** Zethos and Lucia explain her battle strictness: "Every other second she would be shouting 'Don't
let your guard down...'" (Lucia); "she has seen how those she herself has selected, fail and fall... fears
letting your guard down more than anything" (Jian, 009 #13). Zethos: "Each time, I have watched my
daughter fall into a deeper depression at the loss of those she has helped gather." (009 #64). Ezekiel:
"You can probably find her in Pisarno Square. That's where she goes when things get too much for her..."
(009 #24).

**Wants and fears.** Wants: no more of her recruits to die ("from the moment she declared that she would
allow no more casualties, she went looking for truly strong warriors", 009 #13); to save Lucia, "my first
friend... And my first true comrade!" (025 #16); to decide her own future (008 #73). Fears: losing
companions (009 #13). **This is the only cast member whose wants, fear, and wound are all on the page.**

### 3.2 Voice

- **English:** brisk, bossy, sarcastic, with American tough-girl slang added ("bub", "muscle head",
  "moron boy", "What do you think this claw is for, bub? Trimming the verge?", 018 leaf 0x564c).
- **Japanese:** あたし (41 times), feminine particles わ, わよ, かしら, and a prim, upper-class streak:
  ごめんあそばせ〜 ("pardon me~", the mock-aristocratic sign-off at the Cathedral, 018 leaf 0x564c),
  なによォ, and a schoolgirl's ジアンのバ〜カ！　もう　しらないんだから！ ("Jian, you dummy! I don't care anymore!",
  019 #0, English "Jian, you utter moron! This is it between us!"). She is a princess pretending to be a
  commoner, and the Japanese lets that show.
- **What the English lost or changed:**
  - **Her jealousy.** When Jian says he will save Lucia whatever she is, the Japanese gives Gabryel:
    ルシアは女神さまなのよ！　はこびやのジアンとは　つりあわないんじゃない？ ("Lucia is a goddess! Isn't she out
    of a courier's league?") and then ふ〜ん…　ちょっとやけるなァ　それって！ ("Hmm... that makes me a little
    jealous!", 004 #81). The English gives that last line to Titus as "Sounds like you've got it bad."
    With 018 leaf 0x5858 (Flora: "you make a lovely couple", Gabryel's flustered denial, protective of
    Lucia in Japanese), the Japanese quietly gives Gabryel feelings for Jian. The English erased them.
  - Her teasing turns into cruelty in the chat ("your quiver is a few arrows short", 018 leaf 0x5cbc;
    Japanese: "honestly... how much does she actually understand?").
  - The wobble before the airship: Japanese Gabryel notices Flora is near tears (なみだめに　なってる,
    024 #2); English "You're doing a good job of convincing me otherwise".

### 3.3 Arc as written

1. Healriz: mysterious rescuer with a creed (005 #68 to #71).
2. Olbeage: competent, secretive (007 #76 to #80).
3. Zethos Castle: exposed, collapses (009 #58 to #64).
4. Pisarno Square: forgiven, decides for herself (008 #72, #73). **A complete mini-arc, shown.**
5. Sungrid to Frontier: suspicious of Lucia's secret ("Have you been... hiding anything from me?",
   010 #60), sticks with Jian.
6. Post-Ignatius: becomes Jian's minder ("We're going to have to handle him carefully for a while", 009
   #70); Zethos: "You have grown up so much, in such a short time!" (009 #69).
7. Trials to the end: the steady one; "Lucia is special to me, too" (025 #16).

Asserted without showing: Zethos's "grown up so much" comes right after she flees home (009 #71: "I don't
want to meet Papa yet, OK?"). Her relationship with her father is told in two scenes and then dropped.

### 3.4 Contradictions and gaps

- She "declared that she would allow no more casualties" (009 #13) yet recruits a human she knows is weaker
  than the beastmen who died; the Japanese is the same. The text implies she saw something in Jian at the
  Coliseum (009 #58, Zethos: "I can see where your initial interest in these two must have come from")
  but never lets her say what.
- Her mother is never mentioned; nor is what being Zethos's daughter means to ordinary beastmen beyond the
  guards' "My Lady".
- The jealousy thread (Japanese 004 #81, 018 leaf 0x5858) is set up and never touched again.

### 3.5 Raw material worth keeping

- "But aren't humans and beastmen the same?" (005 #68) against Jian's "glad I wasn't born a beastman"
  (009 #13): the two of them disagree about the game's theme, which is a skit engine.
- The recruiter's guilt (009 #13, #64) and Pisarno Square as "where she goes when things get too much"
  (009 #24): a place for a quiet skit.
- "Lucia is special to me, too, you know! She was my first... my first friend... And my first true
  comrade!" (025 #16).
- The checkpoint scene (007 #78 to #80): her charm and authority in one beat.
- The Japanese ちょっとやけるなァ (004 #81).

---

## 4. Flora Banks

### 4.1 What the text establishes

**Shown:**

- **First appearance: brisk, mocking, and practical.** "You're a little crazy, aren't you?... Sungrid
  Bridge is hardly the place for you and your two girlfriends to be dating... You're lucky to still have
  all your limbs attached." (010 #59).
- **She has no patience for superstition**: "Come on, Gabi, don't tell me you're actually buying into this
  superstitious nonsense?" (006 #2); she cracks the backwards inscription (014 #1).
- **She pushes into the party** ("You're going off on a journey again... In which case, you'll need my
  help.", 004 #87; "We'll let you tag along with us, OK?", 004 #88).
- **She is brave despite real fear.** She is afraid of heights and the airship ("I don't really care if it
  flies or not... because I won't! Sorry, but... I don't like heights.", 025 #13; "Don't let me near it!
  I think I want to smash it!", 024 #0) and goes anyway ("If it looks like it's going to break up, I'll
  hold it together with my teeth!", 025 #17). As Ignatius's hostage: "Jian! Forget about me!" (021 #34).
- **She is hurt when dropped**: "That's just too much! I did my best as a guide, and then I just get cast
  aside! Lovely!" (010 #54).

**Told:** reckless and naive, by her brother: "But she is naive and prone to being reckless, hardly the best
combination!" (Peres, 010 #27; "Look before you leap", 010 #24). She loves food (Ghulian tomatoes "My
Favorite!", 011 #12; meat, 011 #37; a glowing salad she won't eat, 011 #22), hates hot places (018 leaf
0x5ad8), wants fireflies (022 #1, #2), and finds Rebric "So different from the Frontier where I grew up"
(018 leaf 0x5e98).

**Wants and fears.** Wants: to see new places ("I just want to see new places!", 018 leaf 0x5d28), to be
useful ("I'm sure I can help you out!", 010 #55). Fears: heights, heat, the mystical. Nothing larger.

**Relationships.** Peres (her brother and the tunnel's leader; the only sibling bond in the game, 010 #24,
#31); Gabryel (87 shared messages, a bickering big-sister dynamic); Jian (79, she teases him, he
apologizes); Lucia **never** (they are never in the party together; 0 shared messages).

### 4.2 Voice

- **English:** a sassy, upbeat tomboy ("Blah blah blah... let's get going already!", 018 leaf 0x5ddc;
  "jumped up lizard", 017 #4), sometimes dim ("Explain it again, OK?", 013 #22) and sometimes the sharpest
  in the room (014 #1). The English adds put-downs (calling Kirlis an "old crackpot", 018 leaf 0x6134;
  "could depress a clown" to the grieving Jian, 018 leaf 0x5e68).
- **Japanese:** あたい (39 times), the rustic, tomboyish "I" of a country girl; おにいちゃん for Peres;
  drawn-out vowels and childish endings (ちょっとォ, だモン, しゅっぱぁ〜つしんこうッ！！ "Full speed ahead!",
  018 leaf 0x5ef8); she calls Jian あなた, a little grown-up and bossy. Sheepish backdowns in Japanese
  (わ　わかってるよォ…　ちょっと　言ってみただけだもん！ "I-I know... I was just saying!", 018 leaf 0x5d28)
  become defiance in English ("I'm not an idiot, Gabi, OK!").
- **What the English lost:** the dialect (her Frontier upbringing in her mouth), her shy praise of Jian
  (ジアン…　ちょっと　カッコいいかも？ "Jian... that's kinda cool?", 006 #8 and 018 leaf 0x62a4; English
  "You really pick your moment" and "way cooler than I expected from you"), and her tears on the airship
  (024 #2). Japanese Flora is warmer and more of a kid; English Flora is snarkier.

### 4.3 Arc as written

Joins as guide (010 #63), admits on the road she has never been past the tunnel ("Actually, I asked someone
in that town back there. I've never been here before in my life!", 018 leaf 0x5a60; "this is all new to
me, too!", 018 leaf 0x58e4), is sent home (019 #0), returns via Zethos (004 #87), faces the airship
(024, 025), is held hostage (021 #34). Peres: "To be honest, I didn't think you would achieve quite so
much... You have really grown up!" / Flora: "I'm just me, the same old me!" (010 #31). That exchange
asserts growth and has her deny it; nothing between shows the change.

### 4.4 Contradictions and gaps

- **Why is she a guide at all?** Jian picks her over Rufus to spite him (010 #62); she admits she does not
  know the way. Her own reason to come is Peres's push ("Even you think I should go...?", 010 #63).
- **Her people.** The Underground Tunnel humans descend from slaves of the Vile Tribe's mines (Dan, 010
  #38), and Flora hands out Ignatic Stones to walk among the Vile Tribe (010 #65). She calls Ignatius "a
  tyrant, nothing more!" (010 #61). She never speaks of her parents, of living hidden, or of what the
  Vile Tribe did to her family. The richest backstory in the cast is unused.
- **Clever or dim?** She solves the backwards inscription (014 #1) and the stone-step logic (006 #2), then
  needs the hundred-steps reasoning explained (013 #22). The English "dim" jokes (018 leaf 0x5cbc) push
  her toward comic relief.
- **Skill, not trait** in her case: food, heat, heights, fireflies are quirks. Her one real trait,
  recklessness (by Peres), is never shown in a choice.

### 4.5 Raw material worth keeping

- The airship fear and "I'll hold it together with my teeth!" (025 #17), with the Japanese tears (024 #2).
- "That's just too much! I did my best as a guide, and then I just get cast aside!" (010 #54).
- "So different from the Frontier where I grew up..." (018 leaf 0x5e98): the door to her past.
- Peres and Flora (010 #24, #31): the only family warmth in the game.
- "Jian! Forget about me!" (021 #34) and "you protected us, didn't you?" (021 #40).
- The Japanese あたい and おにいちゃん: a voice worth restoring in English as a dialect or a country turn
  of phrase.

---

## 5. Rufus Crow

### 5.1 What the text establishes

**Shown:**

- **He arrests the heroes, reluctantly, for his standing.** "I'm not a big fan of such methods, but... A
  human acting so heroically would disrupt our way of life here, if the public were to ever find out about
  it." (015 #90). Japanese: オレも　こんなやり方は　スキじゃないんだが…　あまりにも　人間に　めだつ　かつやくを
  されては　オレのたちばもあるし ("I don't like doing it this way either... but with a human stealing the
  spotlight, there's my position to think of, and order here couldn't be kept").
- **Found wounded at Sungrid Bridge, used as bait**, he warns them: "R... run... away... Th... is... a
  trap...!" (016 #5).
- **He offers atonement and is refused.** "It is also partly my fault that your companion was taken. I
  must atone for this, if I can. Allow me to lead you." / Jian: "Sorry, but no thanks!" (010 #62).
- **He listens to Peres's rebuke and changes course.** Peres: "Long ago, all humans had a dream... Taken by
  the Vile Tribe... and you beasts." / Rufus: "Dreams and... hope..." (010 #64). Next time we see him, he
  saves Jian at Elda Canyon: "Jian... I don't want to be a burden, but perhaps I could join in?" (020 #3).
- **He dies holding the line.** "Are you forgetting? I can't be killed! I'll be fine! I always am... He
  killed many of my comrades, don't forget. This is a good chance to avenge them, too!" (021 #1).

**Told:** the hero of all beastmen, by an NPC chorus: "He is the hero of all us beastmen. The invincible
warrior Rufus!" (Berio, 007 #40), "Our hero Rufus shall save us all!" (Carducci, 007 #83), then disbelief at
his defeat (007 #41, #84; 008 #61; 015 #51, #52). Zethos hired him as "a beast mercenary" to lead the new
strike force (009 #13). Ezekiel: "Rufus said as much" (009 #46).

**Wants and fears.** Wants: to keep his standing and order (015 #90), then to atone (010 #62), then to
avenge his comrades (021 #1). Fears: none spoken. The English adds one: "You see, I don't want to die."
(020 #5) is not in the Japanese, where he says さあ　どうかな？　かえりうちにしてやるぞ！ ("We'll see. You'll be the one
who falls!").

### 5.2 Voice

- **English:** dry, gallant, gently ironic ("You always did have a way with words.", to the mute Gideon,
  021 #2; "I do profess to a talent for not getting killed.", 020 #5), formal with Gabryel ("my lady").
- **Japanese:** オレ (12 times), rough-cool; あんた or きみ to Jian, おじょうさま / おじょうさん ("young miss")
  to Gabryel; the catchphrase ふじみ ("unkillable"): どうやら　オレは　ふじみのようだ ("looks like I can't
  die", 020 #5) and オレは　ふじみのオトコだからな ("I'm the man who can't die", 021 #1). The repetition sets
  up his death; the English keeps it once ("I can't be killed!").
- **What the English broke:** at the Cathedral, Jian asks who he is and Rufus answers ざんねんだが　そいつは
  こっちのセリフだ ("Sorry, but that's my line", meaning "I should be asking you that"). The English
  rendered it as a fourth-wall joke, "I think you need to check the script. That's my line..." (015 #86).

### 5.3 Arc as written

Antagonist (015) → bait (016) → guilty volunteer, rejected (010 #62) → rebuked by Peres (010 #64) →
rescuer and comrade (020) → sacrifice (021 #1) → his sword returned as Ignatius's "toothpick" (021 #5) →
carried and used by Jian against Gideon (021 #13 to #15) → mourned (018 leaf 0x62a4; Zethos, 009 #20: "I
think I understand, now, why Rufus was willing to lay his life on the line to protect you."). The arc is
complete in outline and fast: 32 turns of dialogue across seven scenes. The turn from "my standing" to
self-sacrifice happens off screen between 010 #64 and 020 #3.

### 5.4 Contradictions and gaps

- **Why did he change?** Peres's speech is the only bridge, and Rufus answers it with two words.
- **"Placed there to stall us."** Gabryel says Rufus "was placed there to stall us" at Sungrid Bridge
  (010 #60); whether he was a prisoner used as bait or sent there is unclear (inference: bait, since he
  warns them).
- **Hero of the beastmen, mercenary, or Zethos's man?** All three are said; none is explored. No past.
- **Jian's prejudice toward him** (010 #62, 020 #6) is never resolved between them before he dies; the
  apology comes only afterward, to Gabryel, in the chat.

### 5.5 Raw material worth keeping

- "I know you don't think much of us beastmen. I can live with that. But..." (020 #6), cut off by Gabryel.
  The unfinished sentence is a skit waiting to be written.
- The ふじみ ("unkillable") catchphrase and its payoff (020 #5, 021 #1).
- Peres to Rufus: "He has gone to take back all that we have lost. Dreams and hopes, enough for us all."
  / "Dreams and... hope..." (010 #64).
- The sword's whole journey (021 #5, #13 to #15; 009 #19, #20; 018 leaf 0x62a4).

---

## 6. Ignatius

### 6.1 Every appearance

| # | Where | What happens | Source |
|---|---|---|---|
| 1 | Vile Castle, after Lucia's capture | With his servant Jude: confirms Lucia is Althena, plans to wake her in the Chamber of Rebirth, notes the Four Dragons guard it, "I think there might be a better way..." | 016 #7 |
| 2 | Vile Castle, Grand Hall | Meets Jian, mocks him, returns Rufus's sword as a "toothpick", the unwinnable battle (battle type 0x11, HP refills, docs/re-enemies.md), Althena stops him and sends the party away | 021 #4 to #12 |
| 3 | Chamber of Rebirth (Cathedral of Althena) | Thanks Jian for killing the dragons, presents the awakened Althena, "Love steals everything", Jian's "circle of hatred" speech, Althena gives up her power, Ignatius takes Flora hostage, falls, refuses Jian's hand | 021 #20 to #38 |
| (4) | Party chat, USA only | Jian senses Ignatius in the Chamber, "Luciaaaaaaaaaaa!!!" (no Japanese counterpart) | 018 leaf 0x6358 |

That is all: three on-screen scenes and 47 speaker turns. Everything else about him is said by others:
Titus (004 #78 to #82), Quasimodo in Peace Hall (009 #2, #3), Zethos (009 #18), the Vile Tribe of Lind (010
#14 to #23), the dragons (006 #5, 017 #3, 022 #6, 023 #19, #21, #23), and townsfolk (008 #21, 008 #30, 012
#28, 015 #67).

### 6.2 What he wants, as the text gives it

- **An ideology, stated by others:** Althena came to doubt that one all-powerful being should rule; she
  wanted the future "entrusted... to all the people in the world" (004 #78). Ignatius "believes the
  opposite... That the only way to lead this world into true paradise is for it to be controlled by a
  single, all powerful, omnipotent being" and "desires to take the seat of Goddess Althena... even the
  Goddess herself under his control" (004 #80). Quasimodo: "Ignatius believes that he is the law, that he
  is a God himself" (009 #2).
- **In his own words:** "The fate of the Goddess, and of this world, now rest in the palm of my hand.
  Finally, both where they belong!" (021 #9); "I have become all powerful! Indeed, I am a God!" (021 #28);
  "this world only needs one all-powerful being. Which looks like me, on both counts." (021 #31); "The
  ruler of this world! The all powerful being to command all! That... is I!" (021 #34).
- **A people who believe in him.** The Vile Tribe were exiles: the Frontier "existed to confine those
  evildoers for whom there was no other hope" until Ignatius used Black Magic to mold them into an army
  (Titus, 004 #78). Their side: "For a long, long time now we have suffered as a race forgotten by the
  rest of the world... even the Goddess Althena, the very one who sent us here, has long since forgotten
  that we exist... The pain of having no purpose." (010 #15); "Our Lord! Ignatius! The final ray of light
  piercing the dismal clouds of our fate!" (010 #16); "All he is trying to do is lead us... in transforming
  the Frontier into a green and verdant paradise!... You're not the only ones trying to get back something
  you've lost, you know!" (010 #17).
- **A plan with some intelligence.** His servant Jude spread the rumor that Althena was captured while she
  was missing ("Now these rumors shall finally become reality!", 016 #7). He needs the dragons gone to
  reach the Chamber, and lets the would-be Dragonmaster kill them for him: "Due to your kindly releasing
  the Four Dragons, I can finally achieve my goal." (021 #22). The dragons themselves "cannot turn against
  Ignatius" while he is their master (017 #3).
- **A grudge with Zethos:** "The Beast King, is it. I still have... matters to settle with him, too."
  (016 #7; Japanese いつかは　ケリを　つけなくては　ならぬあいてだ, "an opponent I must settle with someday").
  Never explained.

### 6.3 Voice

- **English:** a camp aristocrat: "Welcome to my humble abode. But you are quite the barbarian, aren't you?"
  (021 #4); "Lucia, Lucia, Lucia. Learn some new lyrics!" (021 #9); "Oh, a kidnapping here or there. So
  what?" (021 #7, English-only); "whelp".
- **Japanese:** the royal first person 余 (よ, "We"), classical copula なり (よは　イグナティウスなり, "I am
  Ignatius", 021 #4), archaic negatives (ぬ, ん, ならぬ), contemptuous suffix めっ (アルテナめ, "that Althena"),
  こぞう ("brat") for Jian, and stage laughs (ククク, フフフフ, ハッハッハッハッ). He lectures more than he
  sneers: いせいが　いいだけじゃ　世の中はわたれん。れいぎというものも　わきまえんとな？ ("Spirit alone won't carry
  you through the world. You must also mind your manners.", 021 #7).
- **What the English lost:** the literary allusion at the heart of his only real argument. "Love steals
  everything... You may believe that you are giving that single-minded love of yours, but in truth you are
  stealing everything with it!" (021 #24) is あいは　おしみなく　うばう ("Love takes, unsparingly"), the title
  of Arishima Takeo's well-known essay 『惜みなく愛は奪う』 (1920). The Japanese Ignatius is a man who quotes
  philosophy to wound; the English one is a pantomime villain.

### 6.4 How the game ends him

In the Chamber, after Althena gives her power away, Ignatius grabs Flora: "All who oppose me face death!...
Starting with this pretty little thing right here!" (021 #34). Something interrupts him ("...What the?!
What is this?!", 021 #35; Gabryel: "Flora!"; Ignatius: "What...?! No!", 021 #36), and he falls. Jian
catches him: "Hah! I don't need your help, whelp. Release me!" / "No! Don't let go! Ignatius!" (021 #38).
He lets go. Gabryel: "With the release of Goddess Althena's power, this Cathedral is rapidly becoming
unsafe!" (021 #40). The text does not say what interrupted him (inference: the collapse as Althena's
power is released). **There is no battle**: Ignatius has a single battle type (0x11, HP refilled every hit,
docs/re-enemies.md), the unwinnable Grand Hall fight; whether "Another taste of my power" in the Chamber
(021 #26, #27) reuses it is unchecked. The last boss fights of the game are against Gideon (Gideon 2 and 3
in script 021; docs/story-party-timeline.md row 22). Before the fall, Jian says "Ignatius! Raise your
sword, defend yourself! I'm going to finish you!" (021 #31) and Althena talks him down. The fight the player is promised is
explicitly refused.

### 6.5 Contradictions and gaps

- **Why does he do any of it?** "He wants to be God" is stated three ways but never rooted in a person.
  What made Althena's own champion turn? When did she start doubting, and did she tell him? The White
  Dragon says "He took my trial, received by Black Magic, and went on to become a Dragonmaster" (006 #5):
  he was once where Jian is. The text never says what happened between.
- **Why does he obey Althena?** He spares Jian on her word ("As you wish, Goddess!", 021 #12) and keeps a
  promise to her to "cease your killing". A usurper who keeps faith with the goddess he usurps is the most
  human thing about him, and nobody remarks on it.
- **Liberator or tyrant?** The Vile Tribe see him as the one who remembered them (010 #15 to #17); Flora
  calls him "a tyrant, nothing more" (010 #61); the Underground Tunnel exists because the Vile Tribe
  enslaved humans (010 #38). The game has a real moral knot here and never ties it to him.
- **Titus says Ignatius fears another Dragonmaster** (004 #81), yet Ignatius lets Jian pass every trial and
  uses it (021 #22). Either Titus was wrong or Ignatius played everyone (inference: the second fits 016 #7).
- **"You fear yourself"** (021 #28) is Jian's best line and goes nowhere: Ignatius roars and attacks.
- **The cliff.** He falls in a hostage gambit that the text leaves unexplained, and the game's last
  boss is his mute pet.

### 6.6 What the text gives a real final confrontation

1. **The argument.** One ruler (Ignatius) against everyone (Althena's "Each of you are already... just as
   powerful as I ever could be", 021 #32). A final battle can be that argument with swords.
2. **The mirror.** Every dragon frames Jian as a possible Ignatius: White ("what proof can you offer me that
   you will not follow the same path of rebellion that he has?", 006 #5), Blue ("like Ignatius, you may
   pass this Trial and receive great wisdom, but forget your purity", 023 #19), Black ("You must not
   submit, as Ignatius has!", 022 #6). Ignatius: "There cannot be two Dragon Masters in the world" (021 #25).
   Dark Jian (the Black Dragon trial boss) already exists as a fight against one's own shadow.
3. **The manipulation.** He used the trials to break the barrier (016 #7, 021 #22). A confrontation where
   Jian learns he was the tool is ready-made.
4. **His people.** The Vile Tribe's grievance (010 #15 to #17) gives him a cause that is not madness.
5. **His one argument that lands.** "Love takes, unsparingly" (021 #24): he accuses Jian's devotion of
   being possession. A rewrite that lets Jian answer it, rather than Althena, finishes Jian's arc.
6. **His fear.** "You fear yourself" (021 #28).
7. **The hand.** Jian reaching for him (021 #38) can stay as the ending of a fight Jian wins, rather than
   the end of a fight he never has.

---

## 7. The other figures who matter to the plot

- **Gad** (15 turns): the gruff boss ("lad", "late again as usual"). His one scene has real heart: he
  bullies the grieving Jian into opening Lucia's gift by pretending to throw it out (001 #17 to #29).
  English adds sarcasm ("It would certainly have suited you, Jian. Shame.", 001 #24; Japanese: "This is
  great... it really suits you, Jian!"). Japanese Gad is rough Edo speech (じゃねえか, だらしねえな). Verdict:
  thin, and that is fine for his role; his gift scene is worth keeping as is.
- **Beast King Zethos** (59 turns): proud, theatrical ("Oh, who requested the clown?", 005 #57), a worried
  father who jokes ("Perhaps we should chain her down now, before she gets away again, eh?", 009 #69), and
  the one beastman who apologizes for his people: "I am ashamed... How we have mocked and oppressed humans!"
  (009 #20). His curse reasoning (009 #13) is the clearest motivated decision in the plot (section 9).
  Japanese: わたし, きみ to Jian, あのコ ("that girl") for Gabryel. A good side character.
- **Titus Lauren** (45 turns): Althena's priest hiding in Healriz; the exposition engine (004 #74 to #94) and
  the ending's speaker (026 #1, #2). No personality beyond kindness.
- **Peres** (15 turns): Flora's brother, leader of the hidden humans; gentle with her, cold to Rufus, and
  the author of the game's best speech about loss (010 #64).
- **Gideon** (9 turns, all single words spelled out: "..D...i...e..."): Ignatius's demon ("my Gideon",
  021 #5). Takes Lucia at Sungrid Bridge (Jian fights him alone and forgets it: "I'm supposed to have fought
  him myself, but... I don't really remember it...", 021 #1), kills Rufus, and is fought twice more as the last bosses (021 #13 to #19).
- **Jude** (5 turns): Ignatius's servant and rumor-monger (016 #7). Unique source of Ignatius's plan.
- **Leoncavallo**: the gruff Healriz boss who gives Jian his own tournament slot (004 #45, #48); a model of a
  beastman won over by deeds.
- **The NPC chorus.** Every town has an arc of opinion about Jian (contempt, surprise, apology, cheering):
  Adah (001 #41 to #45), Gobi (004 #31 to #34), Carmen (007 #33 to #37), Belinda (007 #64 to #69), Pacini
  (005 #36 to #38). One NPC argues against the whole quest: Absalom, "You're perpetuating the circle of
  violence, that's all!" (007 #47), which Jian echoes word for word at the climax (021 #28). This chorus
  carries the human/beastman theme more than the cast does.

---

## 8. Relationships as written (cross-cast)

Shared messages (a message where both speak), from the dump:

| Pair | Messages | What they are about |
|---|---|---|
| Jian and Gabryel | 121 | She steers him: tactics, grief, decisions, puzzles, race. The real partnership of the game |
| Gabryel and Flora | 87 | Bickering sisters: Gabryel scolds, Flora clowns; almost all party chat route talk |
| Jian and Flora | 79 | Teasing and apology; she is the one who praises him (in Japanese) |
| Jian and Lucia | 55 | Worry and scolding (Port Searis to Coliseum), the curse at Zethos, one Gabryel scene |
| Gabryel and Lucia | 18 | Rescue, deception and apology; "my first friend" is said only after Lucia is gone |
| Jian and Ignatius | 17 | All in script 021 |
| Jian and Zethos | 13 | Coliseum taunt, the curse argument, the apology |
| Gabryel and Zethos | 13 | Father and daughter |
| Jian and Rufus | 11 | Arrest, refusal, rescue, farewell |
| Gabryel and Rufus | 5 | "My lady" |
| Lucia and Flora | 0 | Never together |
| Lucia and Rufus | 2 | Only the arrest and the bridge |

Observations:

- **The Jian and Lucia bond is the plot's engine and has the least intimate material.** Of their 55
  messages, most are about the job or his recklessness. There is no conversation about each other, the
  past, or the future. Everything romantic is said by others (Marcella "Your little boyfriend", 004 #56;
  Flora "you and your two girlfriends", 010 #59) or added by the English (section 1.2).
- **Gabryel is the de facto second lead.** She has the most scenes with Jian and with everyone else.
- **Two triangles are seeded and dropped:** Gabryel's jealousy (Japanese 004 #81, 018 leaf 0x5858) and
  Caren's flirting with Jian in Port Searis (001 #60 to #68: "One partner is all I need.", 001 #63).
- **Nobody but Jian talks to Ignatius**, and only in the last chapter.

---

## 9. The curse: what it does in the story, and what removing it leaves

Where it appears (every message): Coliseum aftermath, Gabryel names it and offers to take them to Zethos
(005 #71); Carmen in Olbeage (007 #33); Zethos Castle: Lucia's demand and challenge (009 #48 to #52),
Zethos's explanation and apology (009 #13), the "cursed knight and his sweet little princess" taunt (009
#52), the cure (009 #55); "You look all better now" (009 #17). No party chat line mentions it. Its battle
effect is one flag (docs/re-curse-battle-speed.md part 1).

**The game does explain it.** docs/design.md section 11 says "The story never explains why Zethos cursed
Jian"; the text does, in 009 #13 (same in Japanese): Zethos guessed Gabryel would recruit Jian after the
Coliseum, "including a human in the strike force would stir up unwanted animosity across the world", so he
crippled Jian's fighting so "she would surely just give up on you". She did not, because "from the moment
she declared that she would allow no more casualties, she went looking for truly strong warriors". The
English adds that the curse "will lose its power naturally, in only, oh... a few more days time?"; the
Japanese has no expiry, only "it is no longer necessary" (Rufus's force had been hired instead).

What it carries, and what goes with it:

1. **The reason to go to Leephon.** Jian follows Gabryel to have the curse lifted (005 #71). Without it,
   Jian and Lucia need another reason to travel with a stranger to the Beast King (design.md's
   "challenge" idea supplies one).
2. **Jian's grievance with Zethos** and through him with beastmen ("the high-and-mighty Beast King, who
   still shows no remorse over the terrible curse he himself placed on me", 009 #13). This anger is what
   makes Jian's "glad I wasn't born a beastman" speech land. Without the curse, his anti-beastman edge
   needs another source (the Coliseum taunts and town insults are already there: 005 #57, 004 #18, #31).
3. **Lucia's best scene** (009 #47 to #52): she fights a king for Jian's sake. Keep the scene; give her a
   different cause.
4. **The Gabryel reveal.** Zethos's explanation of the curse is how the player learns Gabryel's secret job
   (009 #13, #58 to #64). The reveal needs a new trigger.
5. **The handstand joke.** The Japanese curse name is a pun on Jian's handstands; dropping the curse frees
   the handstand to be cut or kept as a flourish, not a plot point.
6. **The Olbeage rumor** (Carmen, 007 #33) and "You look all better now" (009 #17): small lines to rewrite.

Nothing after Zethos Castle depends on the curse.

---

## 10. Story-wide gaps a rewrite has to fill

- **The first meeting and the promise.** Jian and Lucia met over a year ago (001 #83) under her umbrella;
  he promised to protect her (004 #81). Neither is shown. A skit or flashback here pays for the whole plot.
- **Ignatius's history** with Althena, with the dragons, and with Zethos (016 #7).
- **Why Althena chose to live as Lucia, and as Jian's partner.**
- **The ending.** Lucia is reborn and leaves with Titus (026 #3); there is no reunion with Jian and no word
  on what became of Gabryel, Flora, Zethos, or the Vile Tribe.
- **Flora's people and family.**
- **Rufus's turn** from "my standing" to self-sacrifice.
- **The Vile Tribe after Ignatius.** Althena says they "must all live together, side by side" (021 #32);
  the game then shows none of them again.

---

## 11. Assessment for Jeff (one page)

### Does usable characterization exist?

| Character | Verdict | Why |
|---|---|---|
| Jian | **Yes** | A real early motive (prove humans equal, 004 #48), a real flaw (contempt for beastmen, 009 #13; go-it-alone, 019 #0), and real climax beats (gives up the rings, reaches for Ignatius). Missing: a past, the promise, and an arc that is shown rather than lectured by dragons. |
| Lucia | **Thin** | Worry, scolding, small likes, one brave scene (Zethos, a curse scene). No want of her own, no voice on the bond, no ending with Jian. Althena's thesis is good but belongs to the goddess, not the girl. |
| Gabryel | **Yes** | Wants, fear, and wound on the page: the recruiter whose fighters all died, the princess choosing her own path, "my first friend". The Japanese adds jealousy. The best-written cast member. |
| Flora | **Thin** | Quirks (food, heat, heights, fireflies) and sass; one real fear faced (the airship). Her Frontier upbringing and her people's history are set up by others and never used. |
| Rufus | **Thin** | A complete arc in outline (arrest, guilt, rescue, death) in 32 turns, with a good catchphrase (ふじみ, "unkillable"). The turn happens off screen. |
| Ignatius | **Thin** (ideology yes, person no) | His cause, his people's grievance, his manipulation of the trials, and one sharp argument ("love takes, unsparingly") are all in the text. His past, his reasons, and a fight are not. |
| Zethos | Yes (for a side role) | Proud king, worried father, the one who apologizes. |
| Gad, Titus, Peres | Thin, fit for their roles | Gad's gift scene and Peres's speech are keepers. |

### The three highest-value things to create

1. **Ignatius as a person, and the fight.** Give him a history (Althena's champion who heard her doubt
   and could not accept it; the one who went to the forgotten exiles; an old score with Zethos) and end the
   game with the battle his ideas deserve. Build it from 016 #7, 021 #22, #24, #28, 010 #15 to #17, and the
   dragons' mirror lines (6.6). Restore the Arishima line in spirit and let Jian answer it.
2. **The Jian and Lucia bond, shown.** The day they met, the promise, what each wants from the
   partnership, and a closing scene where they meet again. Lucia needs one want of her own (inference from
   the text: an ordinary life among people, her small likes and Althena's thesis) so the rescue rescues
   someone. Skits in the Lucia stretch (Port Searis to Sungrid Bridge) are the cheapest place to do this.
3. **Jian's flaw as a trait, with a cost.** Replace "good at handstands" with the two flaws the text already
   gives him (he goes it alone to protect people; he resents beastmen while claiming everyone is equal),
   and let the cast, not the dragons, change him: Gabryel on race, Rufus's unfinished sentence (020 #6),
   Flora's "you protected us" (021 #40), and the Blue Dragon lesson actually holding at the airship.

Next after these: Flora's past (one skit from "where I grew up", 018 leaf 0x5e98), Rufus's turn (one skit
after Peres's speech, 010 #64), and a voice pass that brings back the Japanese registers (Flora's あたい,
Gabryel's prim streak, Ignatius's 余, Jian's silences).

Branching is available for skits: party chats can now ask a yes/no question and remember the answer
(docs/re-party-chat.md section 9, commit df9a1df).
