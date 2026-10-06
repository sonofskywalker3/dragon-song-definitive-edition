# Playtest feedback

Jeff's notes while playing the patched ROM on a 3DS (TWiLight Menu++), recorded as given. Each item
says where it is in the game data and its state: **Open** (recorded, not acted on), **Done** (with the
commit), or **Waiting** (needs something first). Act on open items only when Jeff says so.

Text references: `script NNN @ 0xOFFSET` is a message in build/unpacked/script/NNN.bin (decode with
`uv run python -m dsde.script build/unpacked/script/NNN.bin --text`). Text edits go in `TEXT_EDITS` in
`src/dsde/feat_text.py`.

## 1. Intro: "her servant the Dragonmaster" (Done, b6e4c8e)

Script 026 @ 0x08, the opening narration. Jeff: replace "her servant the dragonmaster" with "her
champion the Dragonmaster," (with the Oxford comma). Now reads "Then came the Goddess Althena, / her
champion the Dragonmaster, / and the Four Dragons." Verified in the emulator (`text_intro`).

## 2. Jian's self-introduction (Waiting: tone and style rules first)

Script 001 @ 0x1776, Jian's inner voice right after he wakes up in his room (shown in the alternate
text color, `<fb>E` ... `<fb>F` around each line). Original:

> My name is Jian Campbell. I've worked for Gad's Express as a courier for a while now, and recently I
> teamed up with this girl named Lucia Collins.
> We both love excitement and adventure. Working as couriers can sometimes land us in risky
> situations.... But that's all part of the fun! I love acrobatics and standing on my head, and I do
> have quite a soft spot for Lucia... maybe!

Jeff: some of it is redundant with the intro and some is "just cringe"; wants suggestions, but only
after there are tone and style rules built from the PS1 Lunar scripts (Silver Star Story Complete and
Eternal Blue Complete).

Jeff (follow-up): the whole thing is jarring. Unless the PS1 games have a self-introduction of their
own (Hiro talks while running around the ruins at the start of Lunar 2, but to Ruby), drop it
entirely. No "talking out loud to myself" narration or setup; rather have someone else tell Jian to
get his butt to work. Do not build yet.

Proposed (not agreed yet): replace his waking lines and the monologue with one or two text boxes from
an off-screen speaker (named, calling from downstairs or outside), plus at most one short reply from
Jian. Text only, no new actors or event scripting. Before writing it, check who the player meets next
and whether Gad's Express, the recent partnership with Lucia, standing on his head, and the crush come
up again later.

PS1 reference (scripts in build/research/lunar_scripts/, not tracked): Eternal Blue opens on Hiro and
Ruby mid-heist; Hiro only introduces himself afterwards, in a short self-aware aside to the player while
running from monsters. Silver Star gives Alex one short narrated paragraph about his dream (Dyne), then
Nall calls for him and Luna's first line is "Alex, you're late again, silly." Neither recaps the intro.

Decided (Jeff): option A. Main intro, then skip the self-introduction and go straight to an off-screen
wake-up: someone calls up to Jian that he overslept and Lucia already left, Jian answers with short,
flustered lines. It replaces his waking lines, the monologue and "Right then! I'd better go looking for
Lucia..." (script 001 from the "....It's morning...?" message through that one). Jeff's message was cut
off after "then as": the rest of the direction is still to come.

Draft wake-up (speaker: Cherenkov, see below):

> Cherenkov: JIAN! You alive up there?! / Lucia left an hour ago!
> Jian: ...Huh? An hour?!
> Cherenkov: I wish I could afford to / oversleep every day! / Get moving!
> Jian: I'm up! I'm up!

Jeff (continued): after the wake-up, no player control yet. A scripted run: Jian runs out of his
room, down the hall and out the front of the inn, and the real character introduction happens while
he runs (the Eternal Blue model: Hiro's aside comes mid-chase).

Speaker: Cherenkov, the innkeeper, not Gad. Gad has a counter in town but is not in the inn; Cherenkov
already has the joke (script 001: "Ah, Jian. Finally, you grace us with your presence. I wish I could
afford to oversleep every day! And if you're looking for Lucia, she already left."). His line moves
into the wake-up, so passing him in the lobby needs a new or no line. Gad's later "Hey, lad, late again
as usual, huh?" keeps the running gag.

Draft for the run (an aside to the player, as Hiro's; only facts true in this game):

> Jian: Oh, hey. Didn't see you / there. I'm Jian, courier for / Gad's Express. Fastest legs / in Searis... when I'm awake.
> Jian: The girl who left without / me? Lucia, my new partner. / She's great. She's also / going to kill me.

Feasibility, to research before promising it: script ops that move actors (026 uses 0x37, 0x39, 0x4E
near party setup), whether the room, hall, lobby and street are separate maps and how a cutscene changes
maps, whether a text box can show while Jian keeps running (otherwise alternate short runs and boxes),
and returning control at the inn door. This is event scripting, much more than a text edit.

Before building: check who is near Jian's room and at Gad's Express, add `!`, `?` and the speaker
name markup to feat_text.py, and verify the scene in the emulator.

Notes:
- Almost every fact repeats the intro's last page, which the player read seconds before (script 026:
  "A youth who loves acrobatics, named 'Jian Campbell', is making a living here as a 'courier', along
  with his friend 'Lucia Collins'. The pair of them love excitement... especially when spiced with just
  a little danger."). New here: Gad's Express, "recently teamed up", standing on his head, the crush.
- The message is 0x1B9 bytes over two pages; a rewrite can be shorter or longer (feat_text.py moves a
  message that grows). Keep each line within 30 characters.
- Text codes seen so far besides letters: 0x24 `!`, 0x25 `?`, 0x26 `-`, 0x29 `,`, 0x2A `.`, 0x54 `'`,
  0xFD line break, 0xFE page break (waits for A), 0xFC, 0xFB + letter (text color: `E` alternate, `F`
  normal, `C` blue for place names). feat_text.py does not write `!`, `?`, `-` or color codes yet.

## 3. Prologue trims (Open)

Script 026 @ 0x08 (the same opening narration as item 1). Jeff:

- Remove "who loves acrobatics": "A youth who loves acrobatics, / named 'Jian Campbell', / is making a
  living here as a / 'courier', along with his / friend 'Lucia Collins'." becomes "A youth named Jian
  Campbell is making a living here as a courier, along with his friend Lucia Collins." (rewrap to 30).
- Remove all the single quotes in the prologue unless needed: 'Beastmen', 'Humans', 'Jian Campbell',
  'courier', 'Lucia Collins'. Apostrophes that are real (Althena's) stay.
- Remove the whole last paragraph: "The pair of them love / excitement... especially when / spiced with
  just a little / danger."

Check after the edit: line wraps (30 characters, the stored text drops the space at each wrap) and that
the last page still ends cleanly with its page break before the game starts.


## 4. Lore and worldbuilding (Open)

Jeff (2026-10-06): one problem he keeps hearing is that the game has no lore. Gather everything that
can be found in the first game's scripts (Silver Star Story Complete, build/research/lunar_scripts/,
not tracked) and in any other first-party or fan sources, to strengthen the real worldbuilding. He will
invent material if he has to, but it has to feel right for Lunar.

Not started. Likely output: a tracked research doc (short quotes only, with sources) on the world before
Dragon Song: Althena, the Dragonmaster, the Four Dragons, Beastmen and humans, the Vile Tribe, places and
history, and where the new dialogue could use them.

## 5. Localization (Open)

Jeff (2026-10-06): he hears the localization is a major part of the game's problem. He downloaded the
Japanese release (Lunar Genesis, copied to `rom/Lunar - Genesis (Japan).nds`, not tracked) so the
scripts can be compared line by line with the USA text. Goes with items 2, 3 and 4: the tone rules and
any rewrite should check what the Japanese script actually says.

## 6. Walking speed (Done, `walk-speed`)

Jeff (2026-10-06): "can we increase walking speed a bit?" Field walking only (running is design 1).
To find: the player's walk step per frame (player block 0x020B6BE4, position x +0xD0, y +0xD4 in 20.12)
and whether NPC routes and scripted walks share the same speed value.

Done 2026-10-06 (Jeff: walking speed before the demo): walking is 1.25 times as fast; running is unchanged
(running is now 1.6 times walking instead of 2). Scripted walks are unchanged. See docs/status.md.

## 7. Battle cards: duplicate drops refill durability (Open)

Jeff (2026-10-06): improve the card system. A card should still drop when you already have one, and a
duplicate drop refills that card's durability instead of being lost. To find: how card drops are
skipped for owned cards, and where a card's durability (the "P" counter on the card) is kept. Cards are
items (for example 0xE8 Dagon, 0xE9 Hellbird) in the battle Item menu under Cards.

Jeff (follow-up): the "collection" cards (the ones with no battle use, only collected) should be given
real uses. To find: which cards are collection-only and what effect slots the card system supports.

## 8. Multi-hit kills die at the end of the combo (Done, `kill-on-hit`)

Jeff (2026-10-06): when Jian's 3-hit combo kills several enemies, they all die together after his last
hit. He wants each enemy to die right after the hit that kills it, while Jian moves on and hits the next
one. Asked to build it (2026-10-06).

Done 2026-10-06 on Fast and Fastest (Normal stays vanilla): each enemy dies on its killing hit, with its
halo and sparkles, then fades while Jian carries on. See docs/status.md.

## 2 (continued). Wake-up call text (decided 2026-10-06)

Jeff picked version B of the drafts in docs/style-rules.md, with his own last line:

> Cherenkov: Jian! Overslept again?! / Lucia headed out hours ago!
> Jian: Wha...? She left already?!
> Cherenkov: Keep this up and I'll rent / the room to someone / respectable!
> Jian: I'm up! I'm up!

The run aside (Jian's lines while he runs out of the inn) is still to be agreed.
