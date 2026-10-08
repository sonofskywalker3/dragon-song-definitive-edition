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

## 3. Prologue trims (Done)

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

Cherenkov's lobby line (decided 2026-10-06), from his Japanese line (script 001 JP @ 0x642) in place of the
USA "grace us with your presence" joke, which the wake-up now replaces:

> Cherenkov: Jian, what are you doing?! / Get to the fountain plaza! / Don't keep Lucia waiting!

Jian's run lines: still being worked on. Source is his Japanese self-introduction (JP script 001 @ 0xC16),
minus what the trimmed prologue already says.

## 2 and 3. Opening built (2026-10-06)

Jeff approved Jian's run lines (inner voice, no name tag, one box per map):

> Room: I'm Jian. I'm a courier for / Gad's Express. Lucia and I / haven't been partners long.
> Hall: It gets risky sometimes. / Honestly? That's what I / love about it.
> Lobby: Lucia? She's great. / Just don't tell her / I said so.

`opening-run` is in the default build with the decided wake-up, run lines and Cherenkov's lobby line
("Fountain Square" in the place-name color, as the USA text names it). Prologue trims done (Jeff,
2026-10-06: "'humans' and 'beastmen' need to have the ' removed still"): no quotes around Beastmen,
Humans, Jian Campbell, courier and Lucia Collins; no "who loves acrobatics"; no "pair of them love
excitement" paragraph. Checked in the emulator from a New Game (`text_intro`, `opening_run`).

## 2. Opening lines revised (2026-10-07)

Jeff rewrote Cherenkov's wake-up and Jian's run lines:

> Cherenkov: Jian, get your lazy bones / out of bed! Lucia's gonna / skin you alive!
> Jian: Wha...? She left already?!
> Cherenkov: Keep this up and I'll rent / your room to someone useful!
> Jian: I'm up! I'm up!
>
> Room: I'm Jian. I'm a courier for / Gad's Express. Lucia and I / haven't been partners long, / but she's great. / (blank line) / Except for her temper.
> Hall: The job gets risky sometimes, / but honestly, that's why I / love it.
> Lobby: Well, that and getting to / work with Lucia every day. / If only we started later, / I'd have it made!

Checked from a New Game in the emulator (`opening_run`): every box fits, the run reaches the street and
hands back control. The room line is one page (Jeff: no A press mid-run), the punchline after a blank line.

## 9. Y button "thinking out loud" becomes party chat (Open, 2026-10-07)

In the field the DS Y button shows a line of Jian thinking aloud about what to do next (script 018, e.g.
"Anyway... I'd better find Lucia, quick! She's probably about ready to boil over!"; Japanese とにかく…). Jeff:
co-opt it for the story and turn it into **party chat**: it can still give the hint, but other party
members talk too, Tales-style. Not started. First steps when it is: map how script 018 picks its line (story
flags), whether a message there can show several speakers, and list every line with its trigger.

Also on the list for that work: the first hint no longer fits the new opening (Cherenkov already says
Fountain Square, and a later hint has Jian "remember" it). Suggested: "I'd better get to Fountain Square,
quick! Lucia's probably about ready to boil over!"

## 2. Opening run asides rebalanced (2026-10-07)

Jian walks the run now (diagonal routes, see feat_opening.py), so the room is short (about 2 s) and the
hall long (about 6 s). Jeff: move the whole Lucia part into the hall. Room: "I'm Jian. I'm a courier for /
Gad's Express." Hall: "Lucia and I haven't been / partners long, but she's / great. Except for her temper.
/ (blank) / The job gets risky sometimes, / but honestly, that's why I / love it." Lobby unchanged. Seen in
`opening_run`: all seven hall lines fit one box.

## 10. Opening narration rewritten (Done, 2026-10-07)

From the Japanese and Lunar 1 and 2 canon (docs/intro-analysis.md), revised with Jeff: "her champion the
Dragonmaster" kept, no handstands, "beneath the Blue Star" and "a delicate peace... for now." added, a
transition into the two races ("Two peoples came to share this world."), Caldor kept (Lunar 1 has Caldor
Isle). The final text is `PROLOGUE` in feat_text.py (a whole-message rewrite, 8 pages, replacing the
earlier piecemeal prologue edits). Seen page by page in `text_intro`: every line fits, the colon (code
0x2D) shows, and the game goes on to the wake-up call.

## 11. Lucia missing at Fountain Square (Fixed, 2026-10-07)

Jeff: after the new opening Lucia was not at Fountain Square. Vanilla sets flag 0xC (Lucia waits at the
fountain) after Cherenkov's first lobby line (script 001, `19:C` at 0x5F94); Jack tests it (0x6764). The run
takes Jian past Cherenkov without talking, so the flag was never set. Now the run sets it with the wake-up
flags, and both Cherenkov lines it selects between (first talk 0xBD2, after the flag 0xC78 "Impressive! You
know where to go!") show "Jian, what are you doing?! Get to Fountain Square! Don't keep Lucia waiting!", so a
save made before the fix gets the flag by talking to him once. Seen: flag word 0x1002 after `opening_run`;
`test_cherenkov_lobby` shows the line.

Follow-up (same day): talking to Cherenkov was not enough either. Map 164 (Fountain Square) keeps the Lucia
meeting (object 200) only with flag 0xD, which only Jack sets ("I just saw Lucia in Fountain Square", 0x6788,
after Cherenkov's 0xC). The entry check (script 001 0x56E8) now tests 0xC instead, and the run sets both, so
neither Jack nor Cherenkov is needed and a save with Cherenkov talked to works as is.

## 12. Faster field movement and the run cooldown (Done, 2026-10-07)

Jeff: walking 1.5 times, running 3 times vanilla walking (walking 1.25 made running feel little better), and
the run should be ready on entering a new area (running through a door carried the 3 s cooldown into the next
map). `walk-speed` scales every field step by 1.5 (a running frame's two steps make 3); measured 45 px in 30
frames walking and 90 running (`diag_speed_field`). `timed-run` resets the run state when the map id changes
(`diag_run_counter2`: state 0 on the first frame of the new map, running again at once on B).

Why vanilla gated Lucia behind Jack (Jeff asked, 2026-10-07): nothing in the original script points to Jack. Cherenkov
only says "she already left" (sets 0xC); Jian's Y hint then is "Oh, Lucia! Where have you been?" (script 018, a
mistranslation of JP ルシアのヤツ…いったいどこに行ったんだ？ "Where the heck did Lucia go?"); the player has to
knock on doors until Jack, in his own house (map 159), says he saw her at Fountain Square (sets 0xD); only then
does the hint become "Now I remember! We were going to meet up at Fountain Square!" and Lucia appear. The
Japanese works the same way, so it is the original design, not a localization loss; the only thing our opening
removed is Jian's "Right then! I'd better go looking for Lucia...". Decision: override it, as built (the run
sets 0xC and 0xD, map 164 checks 0xC): in our opening Jian is late to meet her, so he knows where.

## 13. Healing statue without the camera pan (Done, 2026-10-07)

Jeff: A on a statue panned the camera to centre it, sparkled, then panned back. Field state 0x3C calls the
camera move func_0201d878 (statue - (0x80, 0x50), 60 frames) and 0x3D waits for it; after the sparkle 0x40
pans back to Jian the same way and waits. Both calls are NOPs now (feat_mp STATUE_CAMERA_CALLS), in the code
every statue shares. `test_statue_fountain` (Fountain Square, map 164): vanilla 193 frames from A to control
(3C, 3D +60, 3E, 3F, 40 +60), ours 73 (3C, 3E, 3F); the sparkle plays on Jian and the camera stays put.

## 14. Opening asides close by themselves (Done, 2026-10-07)

Jeff: the walks are timed to the text, so close each aside when Jian reaches the door instead of waiting for A.
`feat_opening_asides.py` hooks the message op's per-frame window update (0x02040B54): while the run flag 0x1DF is
set and the player's route is done (0x020B6CEC = 0), a page waiting for A (window +0x2E = 1) is cleared as A
would, so the box closes. Text still typing finishes first; other messages are untouched. `test_aside_autoclose`:
from the bedroom state with no input at all, Jian goes hall (26), lobby (428), town map (766).

## 15. Town map menu with the D-pad (Done, 2026-10-07)

Jeff: tapping tabs to see the place lists is not intuitive. `feat_town_menu.py` (feature `town-menu-dpad`): in
towns, Up/Down move through the rows, Left/Right switch tabs (keeping the row where it exists), A goes; touch is
unchanged; the overworld hubs keep their free D-pad cursor. (The DS has no stick; the 3DS Circle Pad reaches DS
games as the D-pad, so the map cursor stays on the stylus in towns.) `test_town_dpad`: Down, Down, Right, Right,
Left, Up give Inn 1F -> Restaurant -> Jose's house -> Loto Pier -> Item Shop -> Loto Pier -> Fountain Square,
holding Down moves one row, A goes to the place (map 165); `test_town_touch`: a row tap and YES still work.

## 16. Gad and the first package (Open, after v0.1.3; Jeff 2026-10-07)

Gad should be properly angry that Jian is hours late. Compare his lines with the Japanese (`python -m dsde.jp_text`)
and rewrite the package pickup scene. Drop the Gad's Express job-picking interface for this first delivery: Gad just
hands over the package.

## 17. Slow enemy attack animations (Open, Jeff 2026-10-07)

On the 3DS, Jian's attacks feel good but being attacked is slow. The Ice Mongrel (Thieves' Woods) hops forward four
times, attacks, then hops back four times. The battle-pace work sped up the party's moves, kills and camera, not
the enemies' own action scripts. To do: survey every enemy's attack animation (action script steps: hops, approach,
return) and speed up or shorten the slow ones on Fast/Fastest, e.g. faster movement steps or fewer hops.

Also from the same session: in Thieves' Woods (one enemy front, one back) Fight attacked at once without the picker.
That is by design: Jian and Lucia reach the front row only, and with one valid target the attack confirms. Jeff may
prefer the picker to show anyway.

Follow-up (same day): Jeff found going from the D-pad town menus to the world map's free cursor jarring, so the
list controls now apply to every hub, the world map included (the selected place moves the icon, and the view with
it); the D-pad no longer drags the icon anywhere. `test_worldmap_dpad`: Leave town (flag 0x1E1 poked) picked with
Left + Up + A, world map 260 loads, a held Down does not move the icon.
