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
