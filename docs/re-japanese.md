# The Japanese release (Lunar Genesis)

Notes for comparing the USA text with the Japanese original (playtest feedback 5). The ROM is at
`rom/Lunar - Genesis (Japan).nds` (not tracked, SHA-1 86bb1ebcb2a10fe5df85eafce81792b63c269bfe).

## Getting at the text

- Extract: `tools/dsd.exe rom extract -r "rom/Lunar - Genesis (Japan).nds" -o build/extract_jp`.
- Archives: `dsde.archive.unpack_all` works on the Japanese .dat files too (output in `build/unpacked_jp/`).
- Encoding: one byte per character, ending at 0xFF. **The byte is the index of a cell in the one dialogue
  font**, `build/unpacked_jp/pack/005.bin` (0x30-byte NTC4 header, then 4bpp 8x8 tiles; cell c is tiles 2c
  and 2c + 1, an 8x16 glyph at 0x30 + c * 64). There is no lookup table and nothing per script: a code means
  the same character in every file. Checked 2026-10-07 by dumping the bottom-screen BG VRAM during the JP
  opening: its font area equals pack/005 for all 256 cells. (`wmpack/046.bin` is the world-map copy, with
  Latin capitals in 0xC9..0xDF.)
- Decoder: `uv run python -m dsde.jp_text build/unpacked_jp/script/NNN.bin` (`--all` for unreferenced strings,
  `--sheet out.png` with `uv run --with pillow` to render the cells a script uses for checking by eye).

| Bytes | Characters |
|---|---|
| 0x00 | full-width space (0xF9 too) |
| 0x01 | ▼ |
| 0x02 to 0x08 | H L M P S V Z |
| 0x09 0x0A | 「」 |
| 0x0B 0x0C | ( ) |
| 0x0D to 0x14 | & ！ ？ ー 。 、 ： / |
| 0x15 to 0x1E | digits 0 to 9 |
| 0x1F to 0x4C | hiragana in あいうえお order |
| 0x4D to 0x55 | small hiragana |
| 0x56 to 0x83 | katakana in アイウエオ order |
| 0x84 to 0x8C | small katakana |
| 0x8D to 0xA5 | voiced and half-voiced hiragana |
| 0xA6 to 0xBE | voiced and half-voiced katakana |
| 0xBF | ヴ |
| 0xC0 to 0xC6 | 〜 … × ↑ ↓ ・ © |
| 0xC7 0xC8 | 【】 (the brackets the USA text turned into single quotes) |
| 0xC9 | F |
| 0xCA to 0xF8 | the game's only 47 kanji: 必要世界女神竜使赤白青黒気来見行人間王言村町魔族法手中大陸心配地方天転呪生本当出存在入死剣悪獣 |

There is no 力 glyph: the text writes 魔法カ with katakana カ for 魔法力. Control codes: FB xx (06 speaker,
04 place-name colour, 03 item colour; FB 07 ends any of them), FC (one byte, mostly right after a page
break), FD new line, FE page break, FF end.
- Scripts: in `script/NNN.bin` a speaker name sits between FB 06 and FB 07, as in the USA scripts.
- Whole-script dump, USA and Japanese side by side per message op: `uv run python -m dsde.text_dump`
  (`build/text/script_NNN.txt`; `--grep REGEX` to search, `--usa-only`). Used for docs/story-characters.md.
- The shop string table (Gad's Express recipient names are entries 75 to 128) has its u16 offsets at 0x020A3DC0
  (129 entries, same layout as the USA table at 0x020A4D28) and its text at 0x020A3EC4.

## Gad's Express recipient names

In the Japanese release the job menu and the NPC's own dialogue use the same name for all 10 recipients whose USA
spellings disagree (docs/re-mp-jobs-rings.md 2.2), so each USA mismatch is a translation error with a clear answer.
Found 2026-10-06 by pairing each Japanese speaker name with the USA one through the `if_cmp_call` value before
the message.

| USA menu / dialogue | Japanese (menu and dialogue) | Reading | Correct spelling |
|---|---|---|---|
| Balam / Bram (001) | バラム | Baramu | Balam (Bram would be ブラム) |
| Timathy / Timothy (001) | ティモシー | Timoshii | Timothy |
| Gobbi / Gobi (004) | ゴッビ | Gobbi | Gobbi |
| Paoro / Paolo (005) | パオロ | Paoro | Paolo (kana do not tell r from l; the Italian name) |
| Tartaglia / Tartallia (005) | タルターリア | Tarutaaria | Tartaglia |
| Laban / Raiban (007) | レイバン | Reiban | Laban |
| eva / Eva (007) | エヴァ | Eva | Eva |
| Pazolini / Pasolini (008) | パゾリーニ | Pazoriini | Pasolini |
| Devida / Davida (011) | デヴィーダ | Deviida | Devida (Davida would be ダヴィーダ) |
| Esthel / Esther (012) | エステル | Esuteru | Esther |

Three names that agree in English differ from the Japanese: Jose is ホセア (Hosea), Ira is アイエラ, Hagar is
ゲイル (Gail). Jeff (2026-10-06): keep the English names for these three.

## The opening narration, Japanese against USA (script 026)

Compared 2026-10-07 for Jeff's question whether the flat "racism is bad" story comes from the localization.
Script 026 holds the opening narration (JP @ 0x8, USA @ 0x8) and the ending (Titus and Peles, the closing
narration). First read with the kanji guessed from context; every guess was later confirmed from the font (above).
The full decoded text and a line-by-line translation are in docs/intro-analysis.md.

Close translation of the Japanese, page by page, with what the USA text does differently:

1. "Long, long ago... this world had no grass, no trees, not even air: truly a world of death. The Goddess
   Althena came down to this land **together with** the Dragonmaster, leading the four dragons." The
   Dragonmaster is 竜使い ("dragon handler") who comes with her; the USA "her servant" is not in it.
2. "Life overflowed, the land was reborn, people built new homes, and Althena blessed them. The Dragonmaster
   swore her eternal loyalty and with the four dragons took on the guarding of this world. Althena became the
   source of a world of magic built on her power." Same as the USA text.
3. "The Beastmen: splendid builds, and better in every physical way, strength, quickness, stamina." Same.
4. "**In contrast**, the Humans: **skilled at handling tools**, but small and physically feeble. The relationship
   of the two races gradually **tilted toward a society led by the stronger Beastmen**." The USA text adds
   "Blessed with **intellect**", which the Japanese does not say, and turns "a Beastman-led society" into the
   vaguer "began to lean in favor of the Beastmen".
5. "The bold Beastmen, who liked a showy life, built a castle at the centre of the world; the Humans, who
   liked a plain life, moved out to the country. These opposite ways of life kept a moderate distance between
   the races and, in a delicate balance, kept the peace." The USA "luxurious, rich lifestyle" against
   "quieter surroundings" is close; the Japanese frames it as taste (showy against plain), not wealth.
6. "Port Searis, thriving on the continent of **Hommel**. Here the boy who is **good at handstands**, Jian
   Campbell, makes a living as a courier, with his partner Lucia Collins. Both lively, they loved play and
   adventure with a little danger in it." The USA text names the continent Caldor and turns handstands into
   "loves acrobatics".

Verdict on the question: **the premise is the same in both.** The Japanese prologue also sets up two races
by body (strong Beastmen, weak Humans), a society tilted toward the Beastmen, and a peace kept by distance.
The localization adds "intellect" to the Humans, which sharpens it into brains against brawn, and blurs who
held power, but it does not invent the theme. Whether the story's handling of it lost nuance can only be
judged from the story scenes themselves (to do: the Beastman/Human dialogue in the town and castle scripts).

The ending in the same script is close too, with two softenings in English: Titus's "so that this never
happens **again**, we **must** fight the darkness inside ourselves" becomes "I can only hope that from now on
we shall all be better able to fight against the evil lurking inside us"; and the closing narration's "the
one who inherits the wind will become a bridge to the future and set out on a new adventure. **That might be
you.**" became "...time for valor shall return. A day when an adventurer will become... Dragonmaster."
