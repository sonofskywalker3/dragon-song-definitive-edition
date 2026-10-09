# The NPC layer: what everyone else says (research 2026-10-09)

Jeff's question: do the townsfolk, shopkeepers, Gad and his offices, soldiers, priests, the Vile Tribe,
beastmen, and children add anything to the story, the way older RPGs let a stranger say "Looking for Lucia?
The way you two get on, you'd think she came to town more than three months ago"? This file answers it
town by town, then by character, by lore topic, by fluff gate, and by translation, and ends with an
assessment and ten suggested lines. It builds on docs/story-characters.md (the main cast) and does not
repeat it.

## 0. Sources, method, and citations

- **Every message of every event script was read** (scripts 001 to 026, 1,113 messages outside the party
  chat script 018). About **750 of them are NPC messages**: 733 have a speaker outside the main cast
  (Gad, Peres, Jude, and the Vile Tribe brothers included; Titus and Zethos not), plus 16 untagged
  continuations (Jacob's second box, the Lind fortune teller's results, Tovia's answers, Kirlis's second
  box). They come from about 160 named NPCs. Titus's and Zethos's cutscenes are in
  docs/story-characters.md section 7; their town lines are covered below.
- Text: `uv run python -m dsde.text_dump` (USA beside Japanese). Flag conditions: `uv run python -m
  dsde.script build/unpacked/script/NNN.bin --reach --text` (the linear listing desyncs in scripts 004,
  007, 009, and 015; `--reach` follows the code from the entry and finds nearly every message).
- **Citations:** `001 #52` is script 001, message op 52 in the text_dump output. Flags are hex. **(JP)**
  marks a reading from the Japanese line of the same op; translations are ours. **(inference)** marks a
  reading the text suggests but does not state.
- Script to place: the map table at 0x02091D18 gives each map's script in byte +2 (docs/re-opening.md 2).

| Script | Maps | Place |
|---|---|---|
| 001 | 151..165, 259 | Port Searis (Gad's Express head office, Cherenkov's inn, Fountain Square) |
| 002 | 0..4 | Thieves' Woods (Hagar, Micah, signposts) |
| 003 | 166..175 | Perit Village |
| 013 | 5..19 | Delrich Temple (no NPCs; statue puzzle, package found) |
| 004 | 176..185 | Healriz (town) |
| 005 | 186..198 | San Coliseum district of Healriz (inn, restaurant, Sandro's office) |
| 014 | 31..34 | Roland cave (Armored Boar) |
| 007 | 199..212 | Port Olbeage |
| 015 | 140..150 | Cathedral of Althena and its School of Magic |
| 008 | 213..222 | Leephon City |
| 009 | 223..225 | Zethos Castle (Peace Hall, guards, Phoenix Knights) |
| 016, 010 | 20..30; 50..52, 226..232 | Sungrid Bridge; Underground Tunnel and Lind Village (Frontier) |
| 019, 020, 021 | 53..57, 58..60, 61..84 | Sandra Desert, Elda Canyon, Vile Castle and the endgame |
| 006, 017, 022, 023 | 100..105, 94..99, 106..111, 112..120 | White, Red, Black, Blue Dragon caves |
| 011, 012, 025, 024 | 233..248, 249..256, 121..128, 129..139 | Noapeace, Rebric Village, Tower of Kirlis, Negri Ocean Lab |
| 026 | 257, 258 | Opening narration and ending |

### Story stages (the flags NPC lines test)

Almost every NPC handler is a first-match chain of the same few flags, so a town has four to six "moods".

| Flag | Set at | Stage |
|---|---|---|
| (none) | | first visit |
| 0x1, 0xC, 0xD, 0xB | 001 | woke up, Cherenkov said Lucia left, Jack saw her, met her at the fountain |
| 0x14 | 002 #1 | package stolen in Thieves' Woods |
| 0x15 | 003 #57 | Enos asks you to fight the Sasquatch |
| 0x28 | 013 #17 | package recovered at Delrich Temple |
| 0x29 | 003 #59 | package delivered, road to Healriz open |
| 0x34 | 005 #71 | after the Coliseum: curse, Gabryel joins |
| 0x6F | 015 (after the Gronk fight) | Cathedral saved |
| 0x79 | 009 (Zethos fight won) | curse lifted, Sungrid Bridge next |
| 0xCB, 0xCC, 0xCA | 010, 019, 020 | Frontier with Flora; Jian alone; Rufus joins at Elda Canyon |
| 0xC9 | 021 (after the Ignatius fight) | lost to Ignatius, Lucia is Althena, Rufus dead |
| 0x80, 0x63 | 009 #21, 004 #88 | sent to Titus; the Dragon Trials begin (Flora back) |
| 0x61, 0x62, 0x12E, 0x132 | 006, 017, 022, 023 | White, Red, Black, Blue Dragon passed |
| 0x18F | 025 (Kirlis) | airship finished |

Nothing after 0x18F changes an NPC line: no townsperson reacts to the final battle, and nobody is
written for the ending except Titus, Peres, and Lucia (026 #1 to #3).

---

## 1. Place by place, in story order

Each town has one "delivery" line per Gad's Express recipient (talking to them with a package, script
event 77): about 55 such receipts in all, pure filler with a few jokes (Moses realizes he has been dumped,
003 #3; Ira's package is from her mother, 007 #5). They are skipped below.

### 1.1 Port Searis (001), the home town

The most heavily staged town: twelve NPCs, each with five or six moods. It is the only place where people
know Jian and Lucia personally.

- **Cherenkov** (innkeeper; Jian lives at his inn, 001 #57, 011 #16): the oversleeping joke, "I wish I
  could afford to oversleep every day! And if you're looking for Lucia, she already left." (001 #52, sets
  0xC). Then "Get over to the Fountain Square, on the double! Lucia will be thinking you've stood her up!"
  (#54). After Ignatius: "Don't you worry about your room. I'll keep it free until you get back." (#57).
  **(JP)** #53, after 0xC: いつものところに行ってやんな ("go to the usual place"); the English "Impressive!
  You know where to go!" loses that the fountain is their daily meeting spot.
- **Jack** (Jack's house; Lila lives there too): the gate NPC of the opening (section 4.1). Later, gossip
  that tracks the plot: "is it true that the Cathedral of Althena was attacked by a Vile Tribe?" (#115),
  "Is it true that Lucia has been kidnapped?" (#116), and at the trials stage he repeats his opening line as
  a joke, "I just saw Lucia in Fountain Square", and Gabryel stops him (#117).
- **Gad**: only the opening and the post-Ignatius scene. Before 0xB: "Aren't you with Lucia? ... what's one
  team member without the other?" (#14). With 0x14: Thieves' Woods is blocked, "no work for us for a
  while" (#15). After the gift scene (0x42) his only line is "Are you sure you want to work, at a time like
  this?" (#30). He has nothing for the Coliseum, the curse, the Frontier, or the trials.
- **Isabella** (old woman): "Where is pretty young Lucia today, then?" (#102); with Lucia present: "So
  young, and yet shouldering such responsibility! What with having to look after Lucia and all..." and
  Lucia: "I'm no trouble to Jian, I promise. You make it sound as if... as if I were a child!" (#103).
  After Ignatius: "Failing to keep such a pretty girl safe! ... Do you even have a brain in that massive
  body?" (#106). Trials: "Bring that pretty young Lucia back safe! I'm sure she's waiting for you!" (#107).
- **Caren** (restaurant cook; flirts): "How about spending a little time with me instead?" (#60), "One
  partner is all I need." (#63), "If you need my help, I could...?" / Jian: "..." (#65). **(JP)** #63:
  わたしも　つれてってくれるって言ったじゃない？ ("You said you'd take me along too, didn't you?"): in
  Japanese Jian once promised her, a hint of a past the English drops.
- **Jacob** (restaurant owner): "So, where's Lucia?" (#32); with Gabryel: "Slacking off work again, are we?
  Or did you actually come to eat something this time?" (#34), which implies the couriers loaf in his
  restaurant (inference).
- **Hiram**: the human anti-beastman voice. "No warm welcome for humans there! Those beast folk like to keep
  to themselves." (#91), "Messing with beast folk brings trouble!" (#92), "What did I tell you?" (#93),
  "Stay away from the Frontier!" (#94); after Ignatius: "You just picked a fight with the wrong guy" (#95);
  trials: "You always ignore my advice, you always come back alive" (#96; **added in English**, see 5).
- **Ikey**: "You two sure work hard!" (#97), the ferry hint (#98), "Do something against the teachings of the
  Goddess Althena and you might get sent there" (#99, about the Frontier), "Your recklessness is your
  biggest flaw. If you really want to save Lucia, you need to grow up a little first." (#101).
- **Adah** (a beastwoman tourist in the restaurant): the full prejudice arc in five lines: "Eating alongside a
  human?! One of my worst nightmares come true!" (#41), "It is this obtrusive nature of all humans that has
  purchased the anger of King Zethos." (#42), "A measly human?!" (#43), "I might have been too hasty in
  judging you." (#44), "For yours is the dream that all wish to see fulfilled!" (#45).
- **Malachi** (from Healriz, condescending): "Met with the anger of King Zethos ... You're obviously not as
  strong as you thought." (#48), then "I'm backing you all the way!" (#51).
- **Jose (JP ホセア, Hosea)** and his servant **Joseph**: Jose objects to a world "controlled by beastmen"
  (#126), then to Gabryel (#127), comes round ("beastmen and humans have to, well... Work together?", #128),
  and at the end fears a world "controlled by the Vile Tribe" (#130). His diary is titled "Dragonmaster
  Jose" (#132); Joseph: "The master has been recording your exploits in his diary, every day without fail
  ... a shining example of the bravery and valor of man and beast." (#134).
- **Adina** (from Perit), **Lila** (her boyfriend "got lost in Thieves' Woods", #121, then "wants to move out
  into the sticks, just because a Vile Tribe might attack!", #124), **Timothy** (inventor; gives the Jump
  Shoes, #76), **Hyman** (ferryman; the ferry sails only after the Coliseum, flag 0x33, #135 to #137).
  Adina: "The Frontier... Isn't that where those who hate and oppose the Goddess Althena live?" (#88).

### 1.2 Thieves' Woods (002)

Hagar and Micah, two Perit men at the rockfall. Hagar: "Huge rocks have been scattered everywhere. Who would
do such a thing?" (002 #4); Micah: "Troubles come in threes, they say... the bridge to Healriz is out!"
(#8), "You planning on going to Healriz ...? They don't exactly welcome humans." (#9). Talking to either
is the Perit gate (4.2). Signposts name the region (#12 to #16).

### 1.3 Perit Village (003)

Farming village; people treat Jian and Lucia as kids. Stages: default, 0x15 (job taken), 0x28, 0x29, 0xC9,
0x63, 0x61.

- **Enos** (village head): refuses to talk (#53), then explains the Sasquatch and the Four Dragons (#54,
  #55), and Jian volunteers before he can ask ("It was obviously going to happen. I was just speeding the
  process up a bit.", #56). Later: "So long as we have you, there is hope!" (#63).
- **Simon** (old man): "Stay away from the White Dragon Cave! ... That cave is a sacred place" (#25), gives
  an item (#27), and later prophesies: "you're standing on the verge of doing something great! Something so
  big that the very world will change!" (#30).
- **Moses**, **Mae** (the "legendary giant" theory, #21, #22; "that shining blue star... the people who live
  there", #24), **Hester**, **Hanna** ("I thought you were out of control, but... You're actually really
  good kids.", #43; **(JP)** あんたたち　たんなる　いたずらっこじゃなかったんだねぇ, "so you weren't just
  little troublemakers"), **Ezra** (the hints: "Hagar and Micah went off to check out the trouble", #46),
  **Beulah** and **Debora** (gossips), **Abednego** (senile joke).
- **Lilith** (Gad's Express office): no work while the woods are blocked (#8), back to work (#9).
- Rumor drumbeat: Beulah: "The Vile Tribe has been expanding their influence!" and "this Vile Tribe... Just
  who exactly are they?" (#70, #71). Debora: "they say that, actually, Goddess Althena has been absent for
  who-knows-how-many years! ... Gone! Vanished!" (#80).

### 1.4 Healriz and the San Coliseum (004, 005)

The beast town. Every NPC runs the same four-stage arc: contempt (default), surprise (0x34, with Gabryel),
pity (0xC9), respect (0x63). The town is the best-built piece of the NPC layer.

- **Contempt:** Alvera "humans coming to pay our town a visit!" (004 #7); Balbo "I ain't got nothing for the
  likes of you!" (#12); Cara "How weak and... pathetic you look. You... humans." (#18); Gobi "I ain't gonna
  apologize. I hate humans!" (#31); Tracy "Oh look, humans! How ugly!" (#107; the Japanese differs, 5);
  Carlotta "Totally lame, humans" (#117); Toscanini "There's no food here I want humans eating." (005 #13);
  Marietta "Can those pasty limbs of yours really handle the stuff I'm selling?" (005 #5).
- **How the town works for humans:** "Othello is the Mayor of our town, in name at least. Leoncavallo is
  really in charge" (004 #36); "In the Western region, you can enjoy shopping! ... Even humans are allowed
  to shop there!" (Nita, #63); Othello: "I already have one human maid." (#97); Aaron, a human merchant:
  "We humans need the permission of Leoncavallo in order to get into the Coliseum. Which means I need to
  find a bribe!" (005 #29); Rosa, a human who lives there: "Humans have a rough time spending even just a few
  hours here, trust me." (004 #103).
- **Respect:** Alvera "Beastman, human, it doesn't matter any more!" (#10); Gobi "I'm impressed that a human
  has done so much" (#34); Vianca "Beastmen and humans, working together, can achieve anything!" (#114);
  Orland "Humans are strongest in heart and mind." (005 #45); Pacini apologizes for calling the Coliseum
  win luck (005 #38); Manzoni keeps asking what crime got Jian sent to the Frontier (005 #47, #48).
- **Leoncavallo, Marcella, Evelina, Aaron**: the tournament gate (4.3). Marcella: "Your little boyfriend
  doesn't shape up, does he?" (004 #56).
- **Titus** (living quietly in Healriz before the reveal): "No beastman will talk to a human unless they
  have to. ... That makes this town great for a quiet life." (004 #69). Elmo: "There is one called Titus
  living here, but... I think he is a bit too odd to learn much from." (#123). Titus's own pre-reveal lines
  carry the best foreshadowing in the NPC layer (2.2).
- **Side quest:** Balbo's juice and who drank it (#16, #27 to #30), comic.

### 1.5 Port Olbeage (007)

Beastman-run bay town (Claudio: "This town is controlled by us beastmen, you see.", 007 #70) with School of
Magic students lodging there (Absalom, #44). Stages: default (Cathedral attacked, Jian cursed), 0x6F (Gronk
beaten), 0x79, 0xC9, 0x63.

- **The Cathedral crisis:** Dayan (Gad's office) "Big trouble at Cathedral of Althena... Bigger things than
  work going down right now." (#14); Absalom "They've sent reinforcements from Leephon City" (#43); Monica
  was to start "at the Cathedral of Althena School of Magic, starting in the spring" (#28); Ira, a student,
  passes on the absent-goddess rumor (#54).
- **Rufus as the beastmen's hero:** Berio "The invincible warrior Rufus!" (#40), "Our hero, Rufus,
  defeated?!" (#41), "Avenge Rufus for us!" (#42); Carducci "Our hero Rufus shall save us all!" (#83), "Vile
  Tribe propaganda, that's all!" (#84), "You give them one for Rufus too" (#85); Belinda "Is it true that Rufus
  was defeated? ... Tell me it's a mistake!" / Jian: "....I wish I could..." (#68).
- **The skeptic:** Absalom: "Win or lose, nothing good will come of it!" (#46) and "You're perpetuating the
  circle of violence, that's all! So long as you resort to combat there will never be a peaceful solution!"
  (#47), the line Jian repeats to Ignatius (021 #28).
- **Gabryel's cover:** the bay guards call her "My Lady... that is... Princess...!" after she uses the royal
  emblem (#97 to #112); the checkpoint scene is the gate in 4.4.
- **Lil** (bar): "Load those buns of yours on the next ferry out of here" (#23), and later "You're doing this
  for that girly, huh? ... Go get her, then, sugar rump!" (#26). The innuendo is English only (5).
- **Carmen:** "The Curse of Lost Equilibrium? ... you're going to be stuck like that for a long time." (#33),
  and the final turn: "No matter what anyone else says, I'm on your side, Jian!" (#37).

### 1.6 Cathedral of Althena and the School of Magic (015)

Priests and students. Stages: default (during the Gronk crisis the petrified ones say nothing; these are the
lines after), 0xC9, 0x63.

- **The open secret:** "I shouldn't really tell you this, but... the Goddess Althena has not appeared before
  us for a number of years, now." (priest, 015 #17); "The rumor that the Goddess Althena has been captured by
  the Vile Tribe is gathering momentum." (#20); "Our magical world is growing weaker! ... Goddess Althena may
  indeed no longer be here..." (#32). Amalia: "the Vile Tribe was trying to get into the Chamber of Rebirth"
  (#54), the only NPC who guesses the target.
- **Priest aphorisms (0xC9, 0x63):** ten lines of advice that read as quiet foreshadowing: "We are born twice
  into this world. The first time, simply to exist... And the second time, to live!" (#21); "The idea that
  they alone are right and everyone else is wrong is the greatest obstacle to any who aim to become a
  Dragonmaster." (#31); "If you do not part, how can you meet again?" (#36); "Two of you can go, and indeed
  three of you can go... But I am sure that you will have to take the final step alone." (#40).
- **Students:** Bolyai wants to join Zethos's knights (#47); Dorati vows "to take revenge for Rufus" (#52);
  Lena studies Black Magic, "magic so dangerous that it can wound or kill" (#68), and asks why the
  Dragonmaster is causing trouble (#67); Principal Zeeman: "If you are aiming to become a Dragonmaster, you'll
  have to master Black Magic ... Just be careful that you don't lose sight of yourself" (#76).

### 1.7 Leephon City (008) and Zethos Castle (009)

"This town is the biggest in the world! ... And Garcia is the richest beastman in this town!" (Marco, 008
#44). First visited as a prisoner; stages: default, 0xC9, 0x63. No line changes between the Zethos fight and
the Frontier.

- **Beastmen who have never met a human:** "I thought humans were a myth or something!" (Francesca, #19);
  "How many years has it been since I last saw a human?" (Angelica, #9); "you are not welcome in this town"
  (Pasolini, #52); the Phoenix Knights "are for beastmen only" (Valencia, #57; Knight Captain, 009 #43).
- **Zethos as seen by his people:** "our Beast King Zethos has been acting a little odd recently..." (Guzman,
  #23); after the Ignatius defeat: "Beast King Zethos has made a proclamation that there is to be no more
  discrimination against humans. I wonder what happened to spark that off?" (Palestrina, #64), the political
  result of his apology (009 #20). Posters of the king (Jian, #40).
- **Peace Hall** (009): Quasimodo sets Zethos against Ignatius: "Beast King Zethos created a kingdom and laws
  in order to allow people to live peacefully. ... However, Ignatius believes that he is the law, that he is
  a God himself" (009 #2); "Of the three, only Ignatius has evil in his heart" (#3).
- **Lore and color:** Bruno recites the creation story (008 #13, the same as the opening narration 026 #0);
  Pisarno Square is named for "Pisarno, founder of the School of Magic", who "received the teachings of
  Althena" and is "still a hero to all beast people" (Jian reading a plaque, #65); Silone and Tasso's
  Fountain of Truth joke (#67, #68, #71); Enrica: "A beast girl only truly falls in love once in their entire
  life! And that's with their first love!" (#16), said in Gabryel's home city (inference: a seed for her).
- **Ezekiel:** "You can probably find her in Pisarno Square. That's where she goes when things get too much
  for her..." (009 #24), the one personal fact anyone outside the cast gives about Gabryel.

### 1.8 Sungrid Bridge to Vile Castle: the Underground Tunnel and Lind (010, 016, 019 to 021)

The Frontier's NPCs are the richest lore source in the game. Stages: 0xCB (first visit), 0xCC (Jian alone),
0xCA (Rufus with him), 0xC9, 0x63, 0x18F.

- **The hidden humans:** Dan: "long, long ago... Humans where captured by the Vile Tribe and forced to work in
  the mines of the Frontier. But some of them escaped and made this Underground Tunnel their home. Our boss at
  the moment is Peres." (010 #38). His running gag, a secret tunnel to Sungrid Bridge that floods with sea
  water (#39 to #42). Asher: "We do what we can when Zethos' men come through here ... none have made it
  through Elda Canyon. Not a single one of them has come back alive..." (#33), and on Rufus: "He could have
  just run off ... Getting a bad name beats having to fight the Vile Tribe!" (#34). Paul tells Jian to go
  home five times, then "Results follow determination, I guess." (#47). Huldah: "Just what I'd expect from
  Peres' sister." (#52).
- **Lind, the Vile Tribe village** (shops, an inn, and a fortune teller; they serve the party, who carry
  the Ignatic Stones, 010 #65, so (inference) the Stones let them pass): the "Nameless" villager: "We don't believe in Althena, so our village doesn't need
  an Althena statue. The only thing we believe in is... Ignatius, and Ignatius alone." (#14); "For a long, long
  time now we have suffered as a race forgotten by the rest of the world. I have no trouble believing that even
  the Goddess Althena, the very one who sent us here, has long since forgotten that we exist. You could never
  understand the pain that comes with simply existing... The pain of having no purpose." (#15); "Our Lord is
  making his stand, to save every living creature in the Frontier!" (#16); "You're not the only ones trying to
  get back something you've lost, you know!" (#17). Others: "will the Goddess Althena save us Vile Tribe, too?
  After all, she was the one who put us all the way out here in the first place..." (#21); "We kept many humans
  here in order to work the mines" (#20); "some humans are living here, hidden away" (#22).
- The shopkeepers address Jian as a buyer "going after Zethos' minions" (#0, #1): the Stones make the party
  pass for Vile Tribe (inference).

### 1.9 Ghulian: Noapeace, Rebric, Tower of Kirlis (011, 012, 025)

A human continent visited only with Gabryel and Flora. Stages: default, 0x18F; no 0xC9 or 0x63 split
because the party first arrives during the trials.

- **Noapeace**, "built as a symbol of peace" (Marilyn, 011 #23), booming since the new ferry (#10, #13, #15,
  #41). Luke: "What happened to change his mind? Why has Beast King Zethos suddenly taken such an interest in
  our town? ... Beastmen have always thought humans small and weak... Is it actually possible for man and
  Beastman to get along?" (#17), and "I just don't think I'll ever grow to like beastmen." (#18). Rebecca and
  Nannette argue about whether the Vile Tribe will come (#30, #32, #33). Gail's bell was rung at the Cathedral
  "on special events and festival days. But since the rumors of the Goddess being absent have started to
  circulate, my chances to ring the bell have decreased sharply." (#38). Solomon gets Jian's most honest
  answer: "I'm not capable of anything so grand. I just want to save Lucia! That's all." (#35).
- **Rebric**: Blue Dragon worship ("worshipped here in the village as the master of all water", Tovia,
  012 #25); Zachariah: "Ignatius... A Dragonmaster turned tyrant. Goddess Althena is missing, and now her
  Dragonmaster has gone off the rails..." (#28); Raphael's city-versus-nature joke (#11). Saul, Tovia, and
  Roxane are the Ghulian gates (4.6).
- **Kirlis**: eccentric collector; at 0x18F: "what's this I hear about you fighting for sake of the world and
  the sake of its people, eh? Impressive!" (025 #12).

### 1.10 The dragons' caves and the endgame

No townspeople. The Delrich legend (Jian, 006 #2: the giant who would rule the world, the missing hundredth
step, "the giant was packed off to the Frontier") is folk religion the White Dragon then debunks (006 #7).
Caucus, Orcus, and Morus taunt (020 #0); Jude reveals the rumor campaign (016 #7, section 3.1).

---

## 2. What others say about the main cast

### 2.1 Jian

- **Lives at Cherenkov's inn**, not with family: "Don't you worry about your room. I'll keep it free until you
  get back." (001 #57); "Reminds me of my room back at Cherenkov's..." (011 #16). No NPC mentions his parents,
  his childhood, or where he grew up. (inference: an orphan or a newcomer himself; the text does not say.)
- **Reputation at home:** oversleeper ("I wish I could afford to oversleep every day!", 001 #52; Gad's "late
  again as usual", #17), tracks mud in (#4, #55), hard worker ("You two sure work hard!", Ikey #97; "Hard little
  workers, aren't you?", Lilith 003 #10), reckless ("Your recklessness is your biggest flaw.", Ikey #101).
  Physically big: "Do you even have a brain in that massive body?" (Isabella #106; **(JP)** ずうたいばかり
  でかくなって, "all you did was grow big").
- **Seen as a kid outside Searis:** Hester calls him "sonny" (003 #35), Hanna thought they were "out of
  control" (#43), Leoncavallo calls him "kid" throughout (004 #45 to #53), Lil "sugar rump" (007 #26).
- **A legend in the making:** Jose writes "Dragonmaster Jose" about him (001 #132, #134); Simon foresees
  "something so big that the very world will change" (003 #30); Tartallia wants to charge extra for "the room
  used by the mighty hero" (005 #26); Asher: "you've got a chance to forge a legend, kid" (010 #35).
- **Romance, as others see it:** Caren flirts and is turned down (001 #60 to #68); Marcella "your little
  boyfriend" to Lucia (004 #56) and "a girl on each arm" (#60); Tracy "falling in love makes a person weak.
  ... Feeling weak recently?" (004 #109).

### 2.2 Lucia

- **Nobody says when she arrived, where she came from, or where she lives.** The only dating is Jian's: "This
  is the umbrella Lucia was using when we first met. ... it's been over a year already..." (001 #83, the same in
  Japanese); the gift is for "the day we first met" (#21); his intro says he "recently teamed up" with her
  (#81; **(JP)** ちょっとまえから, "since a little while ago"). So: met over a year ago, couriers together for
  less.
- **The town treats her as a local girl under Jian's wing**: "Where is pretty young Lucia today, then?"
  (Isabella #102); "What with having to look after Lucia and all..." and her protest that she is not a child
  (#103); "So, where's Lucia?" (Jacob #32); "what's one team member without the other?" (Gad #14; **(JP)**
  あいぼうってぇのは　そういうもんだろう, "that's what partners are"); "Lucia will be thinking you've stood her
  up!" (Cherenkov #54); Jack: "I thought she was waiting for you...?" (#110).
- **Strangers:** Moses: "You're quite a... lively girl, aren't you?" (003 #13); Lil: "She was a cute little
  thing" (007 #26); Angelica in Leephon: "where's that pretty girl who was with you before? Did she dump you?"
  (008 #10).
- **The goddess under the girl (all foreshadowing, much of it flattened in English):**
  - Titus, meeting her in Healriz: "Hold on a moment...? You there, human girl!" / Lucia: "have we met before
    somewhere?" (004 #67). **(JP)** あ　あなたは…！？ ("You... you are...!?"): he recognizes her.
  - Titus, after Sungrid Bridge: "I'm sure she is fine." (#73). **(JP)** あの方なら　きっと　だいじょうぶですよ:
    he calls her あの方, the honorific "that person" (a deity's or noble's register).
  - Titus's album: Lucia: "This album looks like...?" (#95); Jian alone: "Lucia's got one that looks exactly
    the same. Just a coincidence, I guess..." (#96).
  - Jian at the Healriz window: "those Althena Statues actually look a little like Lucia..." (#11; the English
    adds a joke, 5).
  - In the ending Titus says "This is not the first time that our Goddess has been reborn in such a way."
    (026 #1).

### 2.3 Gabryel

- **"A beast girl with humans" is the standard reaction everywhere:** Adina "Isn't she a beast girl? Why is
  she with you, then?" (001 #87), Jose (#127), Cara (004 #19, Gabryel: "You make me ashamed to be a
  beastwoman"), Tracy (#108), Vianca (#112), Mantegna of Flora (008 #28), Gamariel in Noapeace "We don't get
  beasts visiting here very often!" (011 #11).
- Royal identity: the Olbeage guards' "My Lady" (007 #97 to #112), the Cathedral priest (015 #92).
- Ezekiel on where she hides (009 #24); Enrica on beast girls' one true love (008 #16).

### 2.4 Flora

Peres: "she is naive and prone to being reckless" (010 #27) and the farewell scenes (#24, #31); Huldah:
"Just what I'd expect from Peres' sister. Everyone's counting on you, Flora!" (#52); Moses's "friends" and her
"Friends?" (003 #19). Nothing about her parents or how the tunnel chose Peres as boss.

### 2.5 Rufus

The beastmen's hero, in four towns: "The invincible warrior Rufus!" (Berio, 007 #40); "Rufus is our hero! He
always has been... And he always will be!" (Torricelli, 008 #61); "I'll be able to take revenge for Rufus"
(Dorati, 015 #52); Carducci calls his death "Vile Tribe propaganda" (007 #84). The Frontier humans are
colder: Asher assumes he ran (010 #34); Peres: "I'm sure that he had no regrets." (#29). No Port Searis NPC
mentions him.

### 2.6 Ignatius

Seen as a tyrant by humans and beastmen (Quasimodo 009 #2, #3; Zachariah 012 #28; Solomon 011 #35, "the tyrant
Ignatius"; Garcia "This Ignatius problem is all about money. I'll just buy up the entire Frontier!", 008 #30)
and as a savior by the Vile Tribe (010 #14, #16, #17, #19, #23). Two NPCs ask the obvious question: "Isn't the
Dragonmaster meant to protect the world, along with the Four Dragons? So what's he playing at?" (Francesca,
008 #21) and "Ignatius is a loser... sorry, Dragonmaster, right? The guardian of the Goddess? So why's he
causing all this trouble?" (Lena, 015 #67). Nobody answers them, and no NPC knows anything about his past.

### 2.7 Zethos, Gad, Titus

- Zethos: feared and adored at home (Evelina "Oh, the honor!", 004 #22); "acting a little odd" (008 #23); the
  anti-discrimination proclamation (008 #64); his outreach to human Noapeace (011 #17); his laws (009 #2).
- Gad: no NPC mentions him by name beyond "Please take your business to Gad's Express!" (Gabryel, 001 #122);
  his branch managers (Lilith, Sandro, Dayan, Eliff, Jody) are interchangeable "get to work" lines. Balbo
  knows the Healriz branch as "Sandro's" (004 #12).
- Titus: "a bit too odd to learn much from" (Elmo, 004 #123).

---

## 3. World and lore

### 3.1 Althena: the absent goddess

- **Creation:** "The Goddess Althena turned this dead world, that had no grass, no trees, not even air, into a
  beautiful, green planet" (Bruno, 008 #13), matching the opening narration (026 #0).
- **Absence is common knowledge before the plot says so:** Debora in Perit (003 #80), Ira in Olbeage "she has
  not shown herself for a number of years now" (007 #54), the Cathedral priest (015 #17), Gail's silent bell
  (011 #38). **Capture is a rumor that Jude says he planted:** "While Althena has been gone, I've been spreading
  lies among beasts and humans, whispering that we have captured Althena." (016 #7); it reaches Leephon (Bruno
  #14, Enrica #18), the castle (Maria 009 #6), and the Cathedral (#20, Amalia #55). The player can connect
  the two; no NPC does.
- **Magic is weakening:** Enrica "our world is at peace only due to the magical power of the Goddess Althena"
  (008 #17); priests (015 #32); Lucia's healing fails at Sungrid Bridge (016 #2 to #4).
- **The Frontier is exile for the disobedient**, as folk belief: Ikey (001 #99), Adina (#88), Manzoni ("That's
  where those who disobey the Goddess are sent, right? ...So, what did you do?", 005 #47), the giant legend
  (006 #2). The Vile Tribe agree they were sent there by her (010 #15, #21). Titus's version is harsher: the
  Frontier "existed to confine those evildoers for whom there was no other hope" until Ignatius made them an
  army (004 #78).

### 3.2 The Vile Tribe

Two accounts that the game never reconciles: Titus's "fiends of the Frontier" molded by Black Magic (004 #78),
and Lind's forgotten, exiled people who want "the green, lush lands" back (010 #15 to #17, #21). Lind also
records their crime: they enslaved humans in the mines (010 #20, #38). Townsfolk elsewhere do not know who
they are (Beulah 003 #71; Francesca 008 #20). Althena's last words, that the Vile Tribe "must all live
together, side by side" with humans and beastmen (021 #32), rest on the Lind lines alone.

### 3.3 Beastmen, humans, and the Frontier humans

- Beastmen run Healriz (Leoncavallo over a figurehead mayor), Olbeage, and Leephon; humans there shop in one
  quarter, work as maids, and need permits (1.4). The Phoenix Knights bar humans (008 #57). Leephon beastmen
  have never seen a human (008 #19).
- Human prejudice exists too: Hiram, Micah, Jose, Enos ("unlikely to get a warm welcome", 003 #59), Luke in
  Noapeace (011 #17, #18), and Peres, who blames "the Vile Tribe... and you beasts" (010 #64).
- Every town's chorus ends in apology (Alvera, Gobi, Evelina, Belinda, Carmen, Pacini, Agostini 008 #7: "We
  have been too hasty... Arbitrarily deciding what humans cannot do."). This chorus carries the theme more than
  the cast (docs/story-characters.md 7).
- The Frontier humans: escaped mine slaves (010 #38), led by Peres, helpers to Zethos's doomed strike forces
  (#33), hidden from Lind by a secret passage (#48).

### 3.4 Dragons and Dragonmasters

- Two dragons per continent: "Two dragons live in the Caldor continent and two dragons live in the Ghulian, so
  I'm told." (Angelica 008 #11; Marco #46). Enos gives the compass points (003 #54), wrongly in English (5).
- Local worship: Delrich Temple, "Once a place of worship of the Four Dragons" (003 #54), now a monster's
  nest; the Blue Dragon as Rebric's "master of all water" (012 #25).
- Ochoa: "Those dragons... Why do they all live in caves?" (008 #50), the only joke at the dragons' expense.

### 3.5 Places, economies, and institutions

- **Gad's Express** spans three continents with branch offices in Perit (Lilith), Healriz (Sandro), Olbeage
  (Dayan), Noapeace (Eliff), and Rebric (Jody); couriers' code: "never examine the delivery, never ask any
  questions of the client and resist any personal interest in the packages!" (Gabryel, 001 #145).
- **School of Magic** at the Cathedral, founded by Pisarno (008 #65); girls take a spell or two before
  marriage (Ochoa, 008 #48); students lodge in Olbeage (007 #44).
- **Leephon:** biggest town, Garcia the richest beastman (008 #44), servants hunting rare wine and food for him
  (#22, #26); Peace Hall (009 #1).
- **Ghulian:** human villages "in the middle of a forest" (Miranda 008 #43), reached only through the Meryod
  Cave until a ferry started (Rosita #34, Rachel 011 #27). The Blue Star appears in Mae's daydream (003 #24),
  Rebecca's "the Blue Star is the limit!" (011 #29), and the last line of the game (026 #4).

---

## 4. Fluff gates (the story waits on a talk)

Every place where a required step is "talk to this NPC first", with the flags (all checked in the scripts).

### 4.1 Port Searis opening: Cherenkov, then Jack (checked in the emulator)

1. Cherenkov in the lobby: "if you're looking for Lucia, she already left." (001 #52) **sets 0xC**.
2. Jack in Jack's house: with 0xC, "I just saw Lucia in Fountain Square. I thought she was waiting for
   you...?" (#110) **sets 0xD**. Without 0xC: "Sorry, I haven't seen her. ... Try asking Cherenkov, maybe?"
   (#111), no flag.
3. Fountain Square (map 164): the entry code keeps the Lucia object 0xC8 only with 0xD (001 0x56E0); the
   parasol scene (#138 to #140) sets 0xB. Gad blocks with "Aren't you with Lucia?" (#14) until 0xB.

Emulator, vanilla ROM, from the post-intro save (`emu/plans/npc_gate_searis.plan` to `npc_gate_searis4.plan`,
`--save --out build/npc_emu`): flags word 0 starts at 0x00000002 (0x1 woken); after Cherenkov's "Ah, Jian.
Finally, you grace us with your presence." it is 0x00001002 (0xC); Jack with 0xC shows #110 and the word
becomes 0x00003002 (0xD); Jack with 0xC cleared shows #111 and nothing is set (shots gate_cher1,
gate_jack1, gate_jack_noc1). This matches docs/re-field-battle.md ("Port Searis maps"); DSDE already patches
the fountain test to 0xC, which cuts Jack out of the chain.

### 4.2 Perit and Thieves' Woods: Enos waits on Hagar or Micah

- Enos (village head) refuses: "I do not have time to talk with visitors now!" (003 #53, sets 0x1D, used only
  by the party chat) **until 0x16 or 0x17 is set**, i.e. until you have talked to Hagar (002 #4, sets 0x16) or
  Micah (#7, sets 0x17) at the rockfall in Thieves' Woods. Then he tells the Sasquatch story (#54 to #57) and
  **sets 0x15**, which opens the road to Delrich Temple.
- Pointers: Moses sends you to "the village head ... the biggest house in the village" (#13, sets 0x20, used
  only by Adina's line in Searis); Ezra: "Hagar and Micah went off to check out the trouble in Thieves' Woods"
  (#46); Hanna and Ezra change lines after 0x16/0x17. The player is told where to go, but not that Enos will
  stonewall until the woodsmen have been visited.
- After the Sasquatch, delivering the package to Enos (#59) sets 0x29 and opens Healriz (bridge repaired).

### 4.3 Healriz: the tournament chain (seven steps, three NPCs before any action)

1. Evelina: "They say that the Beast King Zethos may well come to this very town... today!" (004 #22) sets
   **0x36**.
2. Leoncavallo, without honey: "Don't tell me you waltzed in here empty-handed? ... So get out." (#41) sets
   **0x37**.
3. Aaron (005 #29), **only with both 0x36 and 0x37** (else his merchant line #28): humans need Leoncavallo's
   permission, he has a sweet tooth, "His girlfriend, Marcella, should know." Sets **0x38**.
4. Marcella, **only with 0x38** (else her boyfriend line #56): honey from "the Insector that lives in Roland
   Forest" (#57). Sets **0x39**.
5. Honey to Leoncavallo (#42, #43) sets **0x3A**; he then sends Jian after the Armored Boar (#45, #46),
   **0x3B**.
6. The Boar (014 #3, **0x3C**), then the entry pass (004 #48, **0x3D**).

Uncertain: whether the honey can be found before Marcella names it (the Insector drop was not traced).

### 4.4 Port Olbeage: four checkpoint talks

Carducci asks you to "Go over to the checkpoint and see if things are OK" (007 #75, **0x75**); the three
guards each turn you back: the bay gate guard (#94, **0x72**), the Gronk-duty guard (#101, **0x73**), and the
guard reporting "Gronk has attacked, with four Deuce in tow!" (#107, **0x74**). Only with all four of
0x72..0x75 does Carducci start Gabryel's royal-emblem scene (#76 to #80, **0x76**), which opens the road to the
Cathedral. The player is told to check "the checkpoint", singular.

### 4.5 Leephon: not a gate

Ezekiel says where Gabryel is (009 #24), but the reunion in Pisarno Square (map 222) needs only 0x7C (Zethos
audience) and not 0x7D (008 0x31E8); talking to Ezekiel is optional.

### 4.6 Ghulian: Roxane, Tovia, Saul (and a trick question)

- **Kirlis waits on Roxane.** Kirlis's first talk (025 #0, #1, **0x137**); without **0x138** he only says "you
  young punks nowadays have no manners!" (#2). Roxane in Rebric (012 #17) says he wants "rare but useless
  stuff" and sets **0x138**; only then does Kirlis ask for a stone flower (#3, **0x139**).
- **The anthodites wait on Tovia, behind a yes/no.** Tovia asks "Do you know of the Blue Dragon Cave?"
  (012 #19). **Yes** ends the talk: "Really... That's a real shame. I did so want to talk to someone..."
  (#20). Only **No** gives the stone-flower lore (#21, sets **0x133**). Without 0x133, the flowers in the Blue
  Dragon Lake are Flora "seeing things again" (023 #1); with it, they can be picked (#2, #3, **0x135**).
- **The Blue Dragon treasures wait on Saul.** Without **0x140** (Saul, 012 #13) each treasure is only "What's
  this...? It kinda looks important..." (023 #5, #9, #13); after Saul they can be taken (#4, #8, #12).
- Marion's Photon Plant tip (011 #20, 0x130) is not required: the plant's pickup in the Black Dragon Cave
  tests only 0x12F (022 0xE00). (Checked in the script; not played.)

### 4.7 Smaller ones

- Port Searis ferry: Hyman sails only after the Coliseum (0x33, 001 #135 to #137); not a talk gate.
- Gad's Express offices (Lilith, Dayan) gate only side jobs.
- Cathedral of Althena: examining the petrified people sets 0x81 (015 #3 and others); this is a search, not an
  NPC talk, and not traced further.

---

## 5. Japanese against English, for NPCs

Checked: every NPC line quoted above against its Japanese (text_dump pairs them exactly; op counts match in
every script but 018).

**Patterns**

1. **Foreshadowing flattened.** Titus recognizes Lucia (004 #67 あ　あなたは…！？) and calls her あの方
   (#73); Cherenkov's "the usual place" (001 #53 いつものところ); Jian's statue line ends on a question in
   Japanese, どうしてだろう？ ("I wonder why?", 004 #11), where English adds "She's going to be hot when she
   hits twenty!".
2. **Added innuendo and insults.** Lil's "buns", "sweet little butt", "sugar rump" (007 #23, #24, #26; the
   Japanese is a plain warning and "as a girl, I'm a little jealous"); Isabella's "Do you even have a brain in
   that massive body?" (001 #106); Carmen's "tell me how great humans are again" (007 #36; Japanese: "this
   isn't like you, Jian, cheer up!"); Carmen's "the boy who cried blob" pun (#34); Tracy's "Oh look, humans!
   How ugly!" (004 #107; Japanese: ここは　あなたたちが来るような町じゃないわ。悪いことは言わないから
   おかえりなさい, "This isn't a town for people like you. I'm telling you for your own good: go home.").
3. **Added history.** Hiram's "You always ignore my advice, you always come back alive" (001 #96) is not in
   the Japanese ("Jian, you're a surprise. Going to rescue Lucia? I'll cheer you on from the sidelines.").
   docs/story-characters.md 1.1 cites it for Jian's reputation; it is the localizer's. Jian's "Lucia's famous
   'Charcoal Surprise'" (001 #69) is ルシアは　りょうりなんてしないから ("Lucia doesn't cook at all"); the
   burnt-food running joke is English (Lucia's own #39 is おりょうり　にがてだもん, "I'm bad at cooking").
4. **Dropped facts.** Juanita (004 #127): わたし　人間は… ローザと　トレーシーしかしらないの ("the only
   humans I know are Rosa and Tracy"): Rosa and Tracy are humans living in Healriz, which the English loses
   (and turns Tracy into a bigot). Caren's "you said you'd take me along" (001 #63). Huldah (010 #50): Flora
   came back えらく　ごきげんななめだった ("in a foul mood"); English says "excited about something".
5. **Changed facts.** Enos's compass (003 #54): Japanese white north, blue south, **black east, red west**
   (matching Titus, 004 #81); English swaps red and black. Jose's proverb (001 #129): ななころびやおき, "fall
   seven times, get up eight", becomes a muddled "An eye for an eye". Evelina drinks Balbo's **wine**, with a
   drunk joke, in Japanese (004 #27); "Termite juice" in English. Carmen's curse lasts いっしょう ("for life",
   007 #33), "a long time" in English. Debora's "I'm not allowed to comment." (003 #78) is Jian's silence
   (…………。) in Japanese.
6. **Names.** ホセア (Hosea) is "Jose"; イーノク (Enoch) is "Paul"; ピサーノ (Pisano) is "Pisarno"; the
   continent ホンメル (Honmel) is "Caldor" everywhere (consistent). The ending's speaker "Peles" (026 #1) is
   ペレス, Peres.
7. **Typos worth fixing:** "Gpddess" (007 #54), "Due you know" (008 #41), "Well them" (025 #9), "Humans where
   captured" (010 #38), and Marietta's garbled duplicate "pasty limbs of yoursreally ha ndle" (005 #64).

Lore lines are otherwise faithful: the Lind villagers (010 #14 to #23), Dan (#38), Quasimodo (009 #2), the
priests (015), and the absent-goddess rumors match the Japanese closely. Mantegna's "some humans live in the
Frontier" (008 #27) is slightly sharper in Japanese: とりのこされた人びと, "people who were left behind".

---

## 6. Assessment

### What the NPC layer already does well

- **Stage-aware choruses.** Nearly every NPC in Searis, Perit, Healriz, Olbeage, and Leephon has four to six
  lines keyed to the plot, and they move in step: contempt, surprise, pity, respect. Healriz and Olbeage carry
  the human/beastman theme better than any cutscene.
- **Lind.** Five or six Vile Tribe lines give Ignatius's followers a grievance, a faith, and a point ("You're
  not the only ones trying to get back something you've lost"). The final boss's people are better written
  than the final boss.
- **The absent-goddess drumbeat.** From Perit onward the world quietly knows Althena is gone, and Jude says he
  turned that into a capture rumor. The reveal is earned by the townsfolk, not the plot.
- **Rufus's fame.** Four towns call him a hero before and after his "defeat", which gives his death weight.

### What it does not do

- **Nothing about Jian's or Lucia's past.** No NPC dates Lucia's arrival, knows her family, or remembers Jian
  as a boy. Port Searis knows them only as partners and as Jian looking after her.
- **Gad and his offices are mute** after the opening; Searis has no lines for Rufus's death, Gideon, or the end.
- **Ignatius has no past in anyone's mouth.** Francesca and Lena ask why the guardian turned; nobody answers.
- **Nothing after the airship.** No NPC line changes for the endgame or the ending.

### What it could do for the rewrite

- **Carry the Jian and Lucia history in Port Searis** (Cherenkov, Isabella, Jacob, Caren), where townsfolk
  would know it: when she arrived, the umbrella, the daily fountain meeting.
- **Restore the Titus foreshadowing** (the recognition, the honorific, the album) and the statue line.
- **Give Ignatius a reputation**: in Lind (what he did for them), in Leephon (what the old knights remember),
  and at the Cathedral (what he was before).
- **Keep the beastman tension honest on both sides**: the Frontier humans resent Zethos's strike forces
  (Asher, Peres), Noapeace distrusts Zethos's sudden interest (Luke).
- **Cut the fluff gates** (section 4): let Cherenkov send Jian straight to the fountain (done), let Enos act on
  the first talk, merge Evelina, Aaron, and Marcella into one conversation, make Carducci one talk, drop
  Tovia's yes/no trap, and let Kirlis name his price on the first visit.

### Ten suggested NPC lines

Plain, modern, American, serial comma; each needs wrapping to the 30-character box (feat_text.py). Facts the
game does not state are marked **new**.

1. **Port Searis, Cherenkov, the opening** (replaces 001 #52 and #53; with the fountain patch, also replaces
   the Jack gate): "Lucia left an hour ago. Fountain Square, same as every morning. You'd think after a year
   you'd learn to get up on time." (restores いつものところ; the year is from 001 #83)
2. **Port Searis, Isabella, day one with Lucia** (replaces #102): "Looking for Lucia? The way you two bicker,
   you'd think you grew up together. It's only been a year since she turned up at Gad's with that umbrella."
   (**new**: she arrived through Gad's)
3. **Port Searis, Jacob, after Ignatius** (replaces #36): "Her stool's still by the window. I haven't let
   anyone sit there. Bring her back, and the first meal's on me." (**new** detail; Lucia as a regular)
4. **Healriz, Titus, first meeting** (replaces 004 #67, #68 opening): Titus: "...You." / Lucia: "Have we
   met?" / Titus: "No. Forgive me. You look like someone I knew a long time ago." (restores the Japanese
   recognition)
5. **Healriz, Jian at the window** (replaces 004 #11): "Those Althena statues look a little like Lucia. ...
   Huh. Why would that be?" (restores the Japanese question, drops the joke)
6. **Port Olbeage, Lil, after Zethos** (replaces 007 #26): "You're crossing into the Frontier for her? Lucky
   girl. Go get her, sweetheart." (keeps her flirt, drops the innuendo)
7. **Lind, a Vile Tribe villager, first visit** (new line or replaces 010 #19): "When Althena threw us out
   here, Lord Ignatius came after us. He dug our wells, he gave us a name, and he stayed. What did your
   goddess ever give us?" (**new**: Ignatius's past; sets up the final fight's argument)
8. **Leephon, Guzman, after Ignatius** (replaces 008 #23): "The king hasn't been himself since the news from
   the Frontier. The old guards say he and Ignatius knew each other once, before the Frontier." (**new**;
   seeds Ignatius's "matters to settle" with Zethos, 016 #7)
9. **Underground Tunnel, Asher, first visit** (replaces 010 #33): "Zethos sends his beastmen through every
   few months. They eat our food, they never learn our names, and none of them come back. Excuse us if we
   don't throw you a party." (sharpens the human side of the tension, matches Peres 010 #64)
10. **Port Searis, Gad, after Ignatius** (replaces 001 #30): "You've been late every morning since the day I
    hired you, lad. Don't you dare be late for her." (callback to "late again as usual"; **new**: how long Jian
    has worked for Gad is left open)

Corrections to make regardless: Enos's compass (003 #54: white north, blue south, black east, red west), the
"Peles" speaker name (026 #1), and the typos in section 5.7.
