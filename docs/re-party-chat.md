# Party chat: the Y button, script 018, and place-aware chats (research 2026-10-09)

The field Y button (or a tap on the two figures of the bottom-screen party chat icon) shows a "thinking
out loud" hint: USA script 018. Jeff wants it to become party chat (docs/playtest-feedback.md item 9 and
section 21): lines that know where you are and what has happened, two-way talks with a hint in each, and
an icon that bounces only when there is something new. This file is the research (sections 1 to 4) and
the engine built from it, the `party-chat` feature (sections 5 to 8).

Static analysis: USA ARM9 (build/arm9_decomp_annot.c), script 018 via `dsde.script` and
`dsde.party_chat`. Emulator: vanilla runs `emu/plans/chat_vanilla_y.plan` (Jian's room from
build/emu/saves/start.SaveRAM, and Thieves' Woods from a copy of Jeff's save), screenshots in
build/chat/v_room/ and build/chat/v_woods/ (strip: build/chat/v_room_strip.png).

## 1. How Y starts script 018 (confirmed)

- Field state 0x14 (docs/re-field-hud.md, touch input at 0x0201F088): Y (0x800) or a tap on HUD button 6
  (the figures, rect 48x48 around (82, 123)) sets id 6, which goes to state 0x20.
- State 0x20 (code ending at 0x02020194): allocates a fresh 0x2B4-byte script context, stores it at
  0x020B4644 (the main context stays at 0x020B4640), copies the main context's first 0x5C bytes into it
  (`func_020419e0(dst, src)` = MI_CpuCopy, 0x02020160: story flags 0..0x2DF), loads script 0x12
  (`func_02041a68(ctx, 6, 0x12)`, 0x02020170), sets ctx +0x29A = 0, and starts it at the file's first op
  (`bl func_02041988` at **0x02020188**: pc +0xE0 = file base +0xDC). Then state 0x21.
- State 0x21 (0x0201E6A0 switch, decomp line ~26681): runs the script every frame (`func_020418ac`);
  when it stops, copies the flags back (`func_020419e0(main, hint)`) plus `func_02041828`, frees the
  context, and returns to the field. So a flag 018 sets (op 0x19) is kept.
- The System menu (func_02059f84) can start 018 too, the same way with ctx +0x29A = 1: copy at
  0x0205F340, load at 0x0205F350, `bl func_02041988` at **0x0205F368**, state 0x2A copies the flags back.
- The fresh context's vars are not set: unlike a map entry event (field state 3 sets var 0 =
  1, var 1 = map id), 018 starts with whatever the allocation left in ctx +0x204.
- Vanilla run (chat_vanilla_y.plan): room (map 163, only flag 0x1 set) shows Jian, "Anyway... I'd
  better find Lucia, quick! ..."; woods (map 1, flags 0x1, 0x2, 0xB, 0xC, 0xD, 0x14, 0x1C, ...) shows
  Jian, "Well, he ran off toward Perit Village ...". The hint context was at 0x02281940 / 0x022881A0 and
  is freed (0x020B4644 = 0) after the box closes. No story flag changed. The box holds the speaker's name
  and 5 lines of 30 characters ("us." is the 5th line of the woods hint); a portrait band sits above it
  with a background picture for the place.

## 2. Script 018 (confirmed)

25,620 bytes: text from 0x08, code from 0x5124 (the first op jumps there), 104 paths to 99 different
pieces of line code. Ops used (linear count): 0x4F portrait 253, 0x0F message 106, 0x00 stop 99, 0x13
"all set" 98, 0x14 "any set" 4, 0x15 "none set" 2, 0x02 jump 7, 0x19 set flag 8, 0x04 return 4, and 0x32
(6), 0x33 (4), 0x36 (4) inside a few long talks (not needed here).

- 0x13/0x14/0x15 `u16 op, u16 count, u32 target, u32 flags[count]`: jump if all / any / none of the flags
  are set (docs/re-opening.md). Flags are bits at the start of the context (flag n in word n >> 5).
- 0x4F `u16 op, u16 face, u32 slot` (handler 0x0203C330): shows a portrait. Slot 0 is the center, 1 the
  left, 2 the right; three portraits at once happen (Gabryel left, Jian center, Flora right). Faces come
  in fours per character: Jian 1 to 4, Lucia 5 to 8, Gabryel 9 to 12, Flora 13 to 16, Rufus 17 to 20 (18
  seen). Bit 3 of the slot word takes another path (func_0206df18; unused in 018).
- 0x0F `u16 op, u16 0, u32 text`: a message box; text is the file offset. Message text: FB 06 name FB 07
  FD (speaker), FD new line, FE wait for A, FC new page, FE FF end; FB 04 place color, FB 03 item color,
  FB 07 back to white.
- 0x19 `u16 op, s16 flag`: set a flag. 018 sets 0x2C, 0xDA, 0x2B, 0x13E, 0x13F, 0xDB, 0xDC, and 0xDD
  ("said once" marks that move the tree on to the next line).

The tree is first-match: the first branch whose flags hold wins, so each line's real condition is its own
branch plus "not" every branch checked before it. Full table in section 4 (`uv run python -m
dsde.party_chat tree` prints it). Story order runs bottom to top: flags 0xC/0xD/0xB/0x1C/0x14/0x193 (the
Port Searis to Perit opening), 0x15/0x194/0x22..0x25/0x28/0x1F (Sasquatch, Delrich Temple, package back),
0x195 then 0x38..0x3D/0x34 (Healriz, the Coliseum), 0x66 (Leephon to the Frontier), 0xCB, 0xC9, 0x61,
0x133 (dragon trials to the end). Temp flags 0x26A..0x26F (Delrich's statue puzzle) live in the
0x260..0x2DF block that `func_020419fc` clears (when it runs was not traced).

No map is tested anywhere, so a line that says "here" plays everywhere at that stage: with flag 0x193 (the
party has reached Perit Village) Lucia's "That's why we came here to Perit Village" also plays in Thieves'
Woods (Jeff's report).

## 3. Is there a map test? (confirmed: no)

- No script op reads the map id (s16 0x020B6BE4). 0x0D/0x0E compare two operands, each an immediate, the
  s8 at ctx +0x1F4, an s16 var at ctx +0x204, or an s32 at ctx +0x224 (docs/re-opening.md). Map scripts
  branch on the map only because the field puts the map id in var 1 before an entry event; the Y context
  never gets it.
- Cheapest addition: hook the `bl func_02041988` that starts 018 (two sites, 0x02020188 and 0x0205F368) and
  write var 1 = map id there, after which `if_cmp_goto var1 == map` (op 0x0D, mode 0x0002, as
  feat_opening's `if_map_goto`) works in 018 exactly as in entry handlers. The `party-chat` feature does
  this, but the chats themselves do not need it: the same hook picks the chat in ARM code from a table of
  map ranges and flags (section 5), because the icon has to know every frame whether a new chat exists,
  without running the script.


## 4. The 018 tree (condition -> line)

Every path in vanilla's first-match order with its full condition (flag numbers in hex). "Set": all set;
"Clear": none set; "Any set": at least one; "Not all set": at least one clear. Some lines are reached by
two paths (same leaf twice). The DSDE note marks lines the `party-chat` seed restricts to a place.

| # | Leaf | Set | Clear | Any set | Not all set | Line (first words) |
|---|---|---|---|---|---|---|
| 1 | 0x6334 | 195 66 CB C9 61 133 D0 DD |  |  |  | Jian: Lucia... |
| 2 | 0x630c | 195 66 CB C9 61 133 D0 | DD |  |  | Jian: I wonder... was this really for the best...? |
| 3 | 0x6250 | 195 66 CB C9 61 133 CF DC | D0 |  |  | Jian: We have to hurry... Hurry before it's too late! I must stop Ignati... |
| 4 | 0x62d8 | 195 66 CB C9 61 133 CF | D0 DC |  |  | Jian: This doesn't feel right... Where's Lucia? Where?! / Gabryel: Calm ... |
| 5 | 0x6358 | 195 66 CB C9 61 133 1B8 1B9 1BA 1BB | D0 CF |  |  | Jian: ...!? Ignatius... / Gabryel: What? What's wrong, Jian? / Jian: I c... |
| 6 | 0x6274 | 195 66 CB C9 61 133 1A9 | D0 CF |  | 1B8 1B9 1BA 1BB | Jian: Face it with a smile or tear in your eye, for this is the final ba... |
| 7 | 0x6250 | 195 66 CB C9 61 133 CE DB | D0 CF 1A9 |  | 1B8 1B9 1BA 1BB | Jian: We have to hurry... Hurry before it's too late! I must stop Ignati... |
| 8 | 0x62a4 | 195 66 CB C9 61 133 CE | D0 CF 1A9 DB |  | 1B8 1B9 1BA 1BB | Gabryel: Jian... You kept Rufus' sword, all this time? / Jian: ...Yes. /... |
| 9 | 0x6250 | 195 66 CB C9 61 133 18E | D0 CF 1A9 CE |  | 1B8 1B9 1BA 1BB | Jian: We have to hurry... Hurry before it's too late! I must stop Ignati... |
| 10 | 0x622c | 195 66 CB C9 61 133 18F | D0 CF 1A9 CE 18E |  | 1B8 1B9 1BA 1BB | Jian: ... Gabryel: What's up, Jian? You look kinda down. |
| 11 | 0x6208 | 195 66 CB C9 61 133 78 | D0 CF 1A9 CE 18E 18F |  | 1B8 1B9 1BA 1BB | Flora: What?! You think I'm scared? You think a trip in that airship sca... |
| 12 | 0x61e4 | 195 66 CB C9 61 133 13B | D0 CF 1A9 CE 18E 18F 78 |  | 1B8 1B9 1BA 1BB | Flora: Now he wants a Levitation Stone! Kirlis is a little odd, too, isn... |
| 13 | 0x61c0 | 195 66 CB C9 61 133 13A | D0 CF 1A9 CE 18E 18F 78 13B |  | 1B8 1B9 1BA 1BB | Jian: Incredible... If the XR45 Sakura really doesfly, we can get straig... |
| 14 | 0x619c | 195 66 CB C9 61 133 14A | D0 CF 1A9 CE 18E 18F 78 13B 13A |  | 1B8 1B9 1BA 1BB | Flora: Hey look, a note says... We should go up to the roof! |
| 15 | 0x6178 | 195 66 CB C9 61 133 135 | D0 CF 1A9 CE 18E 18F 78 13B 13A 14A |  | 1B8 1B9 1BA 1BB | Jian: OK! We've got our hands on an Anthodite! / Flora: Excellent! Now w... |
| 16 | 0x6134 | 195 66 CB C9 61 133 139 134 | D0 CF 1A9 CE 18E 18F 78 13B 13A 14A 135 |  | 1B8 1B9 1BA 1BB | Gabryel: Anthodites...? Jian: Flowers said to grow in Blue Dragon Lake. ... |
| 17 | 0x60f0 | 195 66 CB C9 61 133 139 | D0 CF 1A9 CE 18E 18F 78 13B 13A 14A 135 134 |  | 1B8 1B9 1BA 1BB | Gabryel: Anthodites...? Jian: Flowers said to grow in Blue Dragon Lake. ... |
| 18 | 0x60c0 | 195 66 CB C9 61 133 | D0 CF 1A9 CE 18E 18F 78 13B 13A 14A 135 139 |  | 1B8 1B9 1BA 1BB | Gabryel: Anthodites...? Jian: Flowers said to grow in Blue Dragon Lake. ... |
| 19 | 0x5fec | 195 66 CB C9 61 132 | 133 |  |  | Flora: What are we going to do?! We'll never get there in time! / Jian: ... |
| 20 | 0x5fc8 | 195 66 CB C9 61 141 142 143 | 133 132 |  |  | Flora: Hooray! That's all of the stones removed. Now we can meet the Dra... |
| 21 | 0x5fa4 | 195 66 CB C9 61 | 133 132 | 141 142 143 | 141 142 143 | Jian: Well then, now we're here, let's start searching for the stones Sa... |
| 22 | 0x5f80 | 195 66 CB C9 61 140 1B1 | 133 132 141 142 143 |  | 141 142 143 | Flora: We'd better start looking for these treasures then! / I don't kno... |
| 23 | 0x5f80 | 195 66 CB C9 61 140 13F 1B0 1B1 | 133 132 141 142 143 1B1 |  | 141 142 143 | Flora: We'd better start looking for these treasures then! / I don't kno... |
| 24 | 0x5f5c | 195 66 CB C9 61 140 13F 1B0 | 133 132 141 142 143 1B1 |  | 141 142 143 | Jian: ... Flora: What's the frown for, Jian? Something weighing on your ... |
| 25 | 0x5f2c | 195 66 CB C9 61 140 13F | 133 132 141 142 143 1B1 1B0 |  | 141 142 143 | Gabryel: Right... to get to the Blue Dragon Cave, we have to pass throug... |
| 26 | 0x5ef8 | 195 66 CB C9 61 140 | 133 132 141 142 143 1B1 13F |  | 141 142 143 | Gabryel: So, to get to the Blue Dragon Cave, we have to pass through the... |
| 27 | 0x5ebc | 195 66 CB C9 61 1AF 1B1 | 133 132 141 142 143 140 |  | 141 142 143 | Flora: Say... Can the Blue Dragon really be found just by wandering arou... |
| 28 | 0x5e98 | 195 66 CB C9 61 1AF | 133 132 141 142 143 140 1B1 |  | 141 142 143 | Flora: Say... Don't you think Rebric Villageis a beautiful place? So dif... |
| 29 | 0x5e68 | 195 66 CB C9 61 1AE | 133 132 141 142 143 140 1AF |  | 141 142 143 | Flora: I just had a thought... If we're going into the East Moto Rainfor... |
| 30 | 0x5e44 | 195 66 CB C9 61 13E | 133 132 141 142 143 140 1AF 1AE |  | 141 142 143 | Flora: Right, this one's easy... We're headed for the East MotoRainfores... |
| 31 | 0x5ddc | 195 66 CB C9 61 12E | 133 132 141 142 143 140 1AF 1AE 13E |  | 141 142 143 | Flora: Congratulations, Jian! The Black Dragon's Trial is over with! / G... |
| 32 | 0x5db8 | 195 66 CB C9 61 12F | 133 132 141 142 143 140 1AF 1AE 13E 12E |  | 141 142 143 | Gabryel: I see... A Photon Plant can light our way! / Flora: Great! That... |
| 33 | 0x5d94 | 195 66 CB C9 61 1AD | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F |  | 141 142 143 | Flora: Are we going to be able to make it though...? This Black Dragon C... |
| 34 | 0x5d70 | 195 66 CB C9 61 1AC | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD |  | 141 142 143 | Flora: Let me get this straight, then. The Black Dragon Cave isbeyond Va... |
| 35 | 0x5d4c | 195 66 CB C9 61 130 | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC |  | 141 142 143 | Flora: Photon Plant, huh? Gabryel: Apparently found in the Black Dragon ... |
| 36 | 0x5d28 | 195 66 CB C9 61 1AB | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC 130 |  | 141 142 143 | Flora: Noapeace... what an odd name! I'm getting even more excited now! ... |
| 37 | 0x5d04 | 195 66 CB C9 61 1AA | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC 130 1AB |  | 141 142 143 | Flora: So, once we get through the East Meryod Cave, we'll be on the con... |
| 38 | 0x5ce0 | 195 66 CB C9 61 19B | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC 130 1AB 1AA |  | 141 142 143 | Flora: Right, I know this! After the West Meryod Cave comes the East Mer... |
| 39 | 0x5cbc | 195 66 CB C9 61 2B | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC 130 1AB 1AA 19B |  | 141 142 143 | Flora: The Meryod Cave... It actually sounds like fun! Hurry up, then! /... |
| 40 | 0x5c94 | 195 66 CB C9 61 | 133 132 141 142 143 140 1AF 1AE 13E 12E 12F 1AD 1AC 130 1AB 1AA 19B 2B |  | 141 142 143 | Flora: The Meryod Cave... It actually sounds like fun! Hurry up, then! /... |
| 41 | 0x5b8c | 195 66 CB C9 12 | 61 |  |  | Jian: This is it! Found it! / Gabryel: Finally, we're going to meet the ... |
| 42 | 0x5b68 | 195 66 CB C9 10 | 61 12 |  |  | Gabryel: Of course! How dumb have we been! If anything has happened, I'm... |
| 43 | 0x5b44 | 195 66 CB C9 11 | 61 12 10 |  |  | Jian: I'm sure the key to finding the White Dragon Cave is somewhere at ... |
| 44 | 0x5b20 | 195 66 CB C9 62 | 61 12 10 11 |  |  | Flora: These Dragon Trials are actually a lot harder than I thought they... |
| 45 | 0x5afc | 195 66 CB C9 199 3E | 61 12 10 11 62 |  |  | Gabryel: Jian, maybe it's too early to say this, but... Do you really th... |
| 46 | 0x5ad8 | 195 66 CB C9 199 | 61 12 10 11 62 3E |  |  | Flora: I guess I already know the answer, but... Are we really going to ... |
| 47 | 0x5aa8 | 195 66 CB C9 198 | 61 12 10 11 62 199 |  |  | Flora: Oh! I just remembered something else! I was told to watch out for... |
| 48 | 0x5a84 | 195 66 CB C9 13 | 61 12 10 11 62 199 198 |  |  | Flora: No need to over-think this... Just leave it to me! Everything wil... |
| 49 | 0x5a60 | 195 66 CB C9 63 | 61 12 10 11 62 199 198 13 |  |  | Flora: Let's get down to business! We need to pass through Roland Forest... |
| 50 | 0x5a44 | 195 66 CB C9 80 | 61 12 10 11 62 199 198 13 63 |  |  | Gabryel: Titus Lauren, living in Healriz, huh... Jian, do you know this ... |
| 51 | 0x5a28 | 195 66 CB C9 42 | 61 12 10 11 62 199 198 13 63 80 |  |  | Jian: Gabi...! We need to meet with the BeastKing, right away! / Gabryel... |
| 52 | 0x5a0c | 195 66 CB C9 | 61 12 10 11 62 199 198 13 63 80 42 |  |  | Gabryel: Well then, let's get this package delivered! Gad is waiting! Ji... |
| 53 | 0x5964 | 195 66 CB CD | C9 |  |  | Gabryel: Say, Jian... Do you think Rufus is OK all alone? / Jian: I'm wo... |
| 54 | 0x5940 | 195 66 CB 1A8 | C9 CD |  |  | Rufus: Vile Castle... Jian: I just hope Lucia is really in there! I'm co... |
| 55 | 0x591c | 195 66 CB CA | C9 CD 1A8 |  |  | Rufus: Well then, easy enough. Pass through Elda Canyon and there's Vile... |
| 56 | 0x5908 | 195 66 CB CC | C9 CD 1A8 CA |  |  | Jian: I'll bet Gabi is fuming... And I guess I was unfair to Flora, afte... |
| 57 | 0x58e4 | 195 66 CB 1A6 | C9 CD 1A8 CA CC |  |  | Flora: Just a little further! Once we cross the Sandra Desert, we will b... |
| 58 | 0x58c0 | 195 66 CB DA | C9 CD 1A8 CA CC 1A6 |  |  | Flora: OK! No need to waste any more timearound here. Let's hurry on toS... |
| 59 | 0x5858 | 195 66 CB 1A5 | C9 CD 1A8 CA CC 1A6 DA |  |  | Flora: But still, I can't quite get over you two! Gabryel: Huh? What do ... |
| 60 | 0x5834 | 195 66 CB 1A3 | C9 CD 1A8 CA CC 1A6 DA 1A5 |  |  | Flora: I don't know what's happening in the Frontier... / We'd better st... |
| 61 | 0x5810 | 195 66 CB | C9 CD 1A8 CA CC 1A6 DA 1A5 1A3 |  |  | Flora: Once we get back above ground,we'll be in Lind Village. It's the ... |
| 62 | 0x5778 | 195 66 1A1 | CB |  |  | Jian: Here we go! Once we cross Sungrid Bridge we'll be in the Frontier!... |
| 63 | 0x5754 | 195 66 7D | CB 1A1 |  |  | Gabryel: Pick up your feet, slow poke! We're headed for Sungrid Bridge, ... |
| 64 | 0x5738 | 195 66 7C | CB 1A1 7D |  |  | Jian: OK! First, let's find Gabi. Lucia: Right! Good idea! |
| 65 | 0x571c | 195 66 79 | CB 1A1 7D 7C |  |  | Lucia: Jian... What should we do now? Jian: I was just about to ask you ... |
| 66 | 0x56f8 | 195 66 6F | CB 1A1 7D 7C 79 |  |  | Jian: And there we have it... As tough as the rumors made him out to be.... |
| 67 | 0x56e4 | 195 66 83 | CB 1A1 7D 7C 79 6F |  |  | Jian: OK, big trouble ahead! We'd better be ready for this! |
| 68 | 0x56c0 | 195 66 77 | CB 1A1 7D 7C 79 6F 83 |  |  | Gabryel: I just hope things continue togo smoothly. Lucia: Yeah, me too.... |
| 69 | 0x56ac | 195 66 | CB 1A1 7D 7C 79 6F 83 77 | 6B 6C 6D 6E |  | Jian: Looks like it fits! So now we need to defeat the Deuce and recover... |
| 70 | 0x5698 | 195 66 82 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E |  |  | Jian: Right, of course! We need to fit something into that massive Althe... |
| 71 | 0x5684 | 195 66 81 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 |  |  | Jian: It's worse then we thought! All the people at Cathedral ofAlthenah... |
| 72 | 0x5670 | 195 66 19D | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 81 |  |  | Jian: Cathedral of Althena... I'm starting to get a bad feeling about th... |
| 73 | 0x564c | 195 66 76 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 81 19D |  |  | Jian: The Vile Tribe at Cathedral ofAlthena... / Sounds nasty! I don't k... |
| 74 | 0x5638 | 195 66 72 73 74 75 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 81 19D 76 |  |  | Gabryel: Say, I've an idea... Why don't we try talking to Carducci again... |
| 75 | 0x5624 | 195 66 75 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 81 19D 76 |  | 72 73 74 75 | Jian: Something is definitely up... Let's go to the checkpoint and, eh..... |
| 76 | 0x5610 | 195 66 | CB 1A1 7D 7C 79 6F 83 77 6B 6C 6D 6E 82 81 19D 76 75 |  | 72 73 74 75 | Lucia: I wonder what all the fuss is about? Sounds like something's happ... |
| 77 | 0x5528 | 195 34 | 66 |  |  | Gabriel: If we're headed for Leephon City, we have to take the ferry fro... |
| 78 | 0x54f4 | 195 3D | 66 34 |  |  | Lucia: Jian... I do understand how you feel, but... are you really going... |
| 79 | 0x54d8 | 195 3C | 66 34 3D |  |  | Lucia: Good work, Jian! We've beaten the Armored Boar! / Jian: Yep, piec... |
| 80 | 0x54bc | 195 2C | 66 34 3D 3C |  |  | Jian: That Armored Boar is somewherearound this area, no doubt about it.... |
| 81 | 0x549c | 195 3B | 66 34 3D 3C 2C |  |  | Lucia: No way, Jian! No way! Just what was all that about? I'm not letti... |
| 82 | 0x5488 | 195 3A | 66 34 3D 3C 2C 3B |  |  | Lucia: Oh Jian, honey... You found the honey! Great! |
| 83 | 0x546c | 195 39 | 66 34 3D 3C 2C 3B 3A |  |  | Lucia: Quite funny if you think aboutit! Honey, honey! Doesn't really su... |
| 84 | 0x5450 | 195 38 | 66 34 3D 3C 2C 3B 3A 39 |  |  | Lucia: Marcella, wasn't it? What do you think, Jian? Jian: Let's go and ... |
| 85 | 0x5434 | 195 | 66 34 3D 3C 2C 3B 3A 39 38 |  |  | Lucia: So, Jian... What is it you want to do in Healriz? / Jian: OK, I g... |
| 86 | 0x5384 | 1F | 195 29 |  |  | Lucia: Oh, hold on...! We'd better go and tell Enos how things worked ou... |
| 87 | 0x53a4 | 1F 29 | 195 |  |  | Lucia: So, Jian... You really want to go to Healriz? / Jian: Yep! I've m... |
| 88 | 0x535c | 28 | 195 1F |  |  | Lucia: Thank the Goddess! We've got the package back safely! / Jian: I d... |
| 89 | 0x5348 | 26F | 195 1F 28 | 22 23 24 25 |  | Jian: That Sasquatch must have hidden our package around here somewhere!... |
| 90 | 0x5334 | 26A 26B 26C 26D | 195 1F 28 26F | 22 23 24 25 |  | Jian: I think maybe that did the trick... All right then! Sasquatch, I'm... |
| 91 | 0x5320 |  | 195 1F 28 26F | 22 23 24 25 | 26A 26B 26C 26D | Jian: There's something here at Delrich Temple, something we have to sol... (DSDE: only in Delrich Temple) |
| 92 | 0x5348 | 194 26F | 195 1F 28 22 23 24 25 |  |  | Jian: That Sasquatch must have hidden our package around here somewhere!... |
| 93 | 0x5334 | 194 26A 26B 26C 26D | 195 1F 28 22 23 24 25 26F |  |  | Jian: I think maybe that did the trick... All right then! Sasquatch, I'm... |
| 94 | 0x52e0 | 194 | 195 1F 28 22 23 24 25 26F |  | 26A 26B 26C 26D | Lucia: Hey, Jian, I've been thinking... Did you notice those four dragon... |
| 95 | 0x52a0 | 15 | 195 1F 28 22 23 24 25 194 |  |  | Lucia: A Sasquatch? Jian, could that be the thief? / Jian: Yeah, I think... |
| 96 | 0x5284 | 193 | 195 1F 28 22 23 24 25 194 15 | 16 17 |  | Jian: I'm starting to get this, now... Everyone is upset because it'stoo... |
| 97 | 0x5270 | 193 1D | 195 1F 28 22 23 24 25 194 15 16 17 |  |  | Lucia: Enos looked pretty wound up, didn't he! Something is going on in ... |
| 98 | 0x525c | 193 | 195 1F 28 22 23 24 25 194 15 16 17 1D |  |  | Lucia: We're looking for information,right? / That's why we came here to... (DSDE: only in Perit Village) |
| 99 | 0x522c | 14 | 195 1F 28 22 23 24 25 194 15 193 |  |  | Jian: Well, he ran off toward Perit Village. So let's go there first, OK... |
| 100 | 0x5218 | 1C | 195 1F 28 22 23 24 25 194 15 193 14 |  |  | Lucia: Right, so all we need to do istake this package to Gad's Express ... |
| 101 | 0x5204 | B | 195 1F 28 22 23 24 25 194 15 193 14 1C |  |  | Lucia: Jian, come on... We'd better get this package to Gad's Express ri... |
| 102 | 0x51f0 | D | 195 1F 28 22 23 24 25 194 15 193 14 1C B |  |  | Jian: Hold on...! Now I remember! We were going to meet up at Fountain S... |
| 103 | 0x51dc | C | 195 1F 28 22 23 24 25 194 15 193 14 1C B D |  |  | Jian: Oh, Lucia! Where have you been? |
| 104 | 0x51c8 |  | 195 1F 28 22 23 24 25 194 15 193 14 1C B D C |  |  | Jian: Anyway... I'd better find Lucia, quick! She's probably about ready... |

## 5. Design: place-aware party chat (`party-chat`, src/dsde/feat_party_chat.py)

- **Entries.** A table of entries replaces the tree as the thing that decides. Each entry has a place
  (map id ranges, or anywhere), a flag condition (set / clear / any set / not all set), the script 018 code
  to run, a read flag, and optionally a chain. New chats (src/dsde/party_chat_lines.py) come first, then
  the vanilla lines (src/dsde/party_chat_hints.py), in vanilla's order.
- **Vanilla lines keep their own code.** A `Hint(leaf, ...)` runs vanilla's code at that offset of 018
  (portraits, all pages, its flag sets, its text-edits fixes); nothing in vanilla's code moves. New chats
  are compiled to 0x4F/0x0F/0x00 code plus text and appended to 018 after the messages text-edits moves
  there (the same bytes are written too, as feat_opening does, so the layout holds with or without
  text-edits).
- **Chains keep the tree's first-match rule cheap.** All vanilla lines are in chain "hint": the first one
  whose place and flags match claims the chain and every later one is out, so their conditions need only
  the flags on their own path (2.4 KB of table instead of 4.5 KB with every negation). A place-restricted
  line that does not match the map does not claim the chain, so the entry after it (same flags, anywhere)
  plays instead: this is how "came here to Perit Village" stays in Perit Village.
- **Which entry plays.** Walk the table: the first matching entry whose read flag is clear plays; if all
  matching entries are read, the first matching one plays again. Several new chats at one place and stage
  therefore play one per press, then the first repeats.
- **Read flags** are story flags (saved with the game: the flag words are at 0x850 in a save file), taken
  from ranges no script op tests or sets and engine code does not read: 0x84..0xC8, 0xDE..0x12C,
  0x14B..0x18D, 0x221..0x242, 0x244..0x25F (279 in all). Vanilla lines get them by leaf offset (stable),
  new chats in table order. The build fails if a script ever uses one. 0x1E0..0x220 is avoided (the engine
  sets 0x1E0 + n per place visited).
- **Start hook** (`cave_chat_start`, at 0x02020188 and 0x0205F368 instead of `bl func_02041988`): start the
  script, set var 1 = map id, pick the entry from the hint context's flag copy, set pc = file base + the
  entry's code offset, set its read flag (in the hint context, which state 0x21 copies back, and in the
  main context).
- **Icon cue** (`cave_chat_frame`, at 0x02022108 instead of `bl func_0206f7c4`, the per-frame HUD pulse):
  after the vanilla pulse, if HUD button 6 is the figures (type 2, cell 14), pick the entry for the main
  context's flags and the current map; unread -> give button 6 OAM flags 0xA026 (affine matrix 6, ours)
  and set matrix 6 to vanilla's pulse (scale 0x1000 + sin(phase) / 8, phase += 0x800 per frame:
  func_0201ace4(*0x020AFF50, 6, scale, 0, 0)); otherwise flags 0x8000 (no matrix: still) and phase 0.
  The Menu note and the portrait keep matrix 5, which still-hud holds at scale 1, so only the figures
  move. The pick runs every field frame (about 110 table rows; ITCM code).
- **Cost:** ITCM 3.2 KB (code 0.7 KB, table 2.5 KB), of the about 17 KB free; script 018 grows by the
  new chats' code and text.

