# The Japanese release (Lunar Genesis)

Notes for comparing the USA text with the Japanese original (playtest feedback 5). The ROM is at
`rom/Lunar - Genesis (Japan).nds` (not tracked, SHA-1 86bb1ebcb2a10fe5df85eafce81792b63c269bfe).

## Getting at the text

- Extract: `tools/dsd.exe rom extract -r "rom/Lunar - Genesis (Japan).nds" -o build/extract_jp`.
- Archives: `dsde.archive.unpack_all` works on the Japanese .dat files too (output in `build/unpacked_jp/`).
- Encoding: one byte per character, ending at 0xFF.

| Bytes | Characters |
|---|---|
| 0x10 | ー (long vowel mark) |
| 0x15 to 0x1E | digits 0 to 9 |
| 0x1F to 0x4C | hiragana in あいうえお order |
| 0x4D to 0x55 | small hiragana |
| 0x56 to 0x83 | katakana in アイウエオ order |
| 0x84 to 0x8C | small katakana |
| 0x8D to 0xA5 | voiced and half-voiced hiragana |
| 0xA6 to 0xBE | voiced and half-voiced katakana |
| 0xBF | ヴ |
| 0xC5 | ・ |

- Scripts: in `script/NNN.bin` a speaker name sits between FB 06 and FB 07, as in the USA scripts.
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
ゲイル (Gail). Optional fixes, not decided.
