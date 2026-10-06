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

Draft (speaker to confirm: whoever runs Gad's Express or owns Jian's room #203, and is met soon):

> [Gad]: JIAN! You alive up there?! / Lucia left an hour ago!
> Jian: ...Huh? An hour?!
> [Gad]: She took today's run without / you. Get moving, or she'll / take your pay too!
> Jian: I'm up! I'm up!

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
