# Lunar script extractors (the other Lunar games)

Dumps the dialogue of the other Lunar games from Jeff's own discs into one plain-text
format, so lines can be compared with Dragon Song. Outputs and discs live in the
gitignored `lunar_scripts/` folder; only this code is committed.

Every dump looks like this (`common.py`):

```
=== TEXT001.DAT @0xAC0 | L38, L39, L3B ===
Hey! You're good! He WAS at
Dyne's Monument planning an
adventure with Ramus!

[L39] You were right on both counts!
```

`source file @offset | speakers`. A speaker is the portrait id the format stores
(L/R = left or right portrait, P = Lunar 2 box portrait). Ids are not mapped to
names: portraits are expression variants, and the portrait shown is not always the
speaker. A blank line is a box break.

Disc images and everything pulled out of them are untrusted. Keep these scripts
outside the data folders, pass paths as arguments, and run Python with `-I`.

## Files

| File | What it does |
|---|---|
| `discfs.py` | Lists or extracts ISO9660 files from a raw `.bin` (MODE1/2352 or MODE2/2352), a plain `.iso`, or a PSP `.cso`. No chdman or maxcso is needed for the CSO. |
| `segacd.py` | Sega CD: runs Supper's wdtools `scriptrip_tss` (The Silver Star, `C*.MAP`) or `scriptrip` (Eternal Blue, `M*.GRP`), applies a proper-noun substitution file on word boundaries, and writes the dump. `ebjp` runs `scriptrip_jp` with its Thingy table for the Japanese Eternal Blue. |
| `subs_tss.txt` | Proper-noun list for The Silver Star. The Sega CD text is upper case only, so the ripper guesses sentence case and this file restores names. |
| `sssc.py` | Silver Star Story Complete (PS1): unpacks `LUNADATA.FIL` and runs MrConan1/lsb on every `TEXTnnn.DAT`, then turns lsb's script output into the dump. |
| `lsb_file_offset.patch` | A two-line patch to lsb's `write_script.c` that adds `(file-offset X)` to each run-commands/options node, so the dump can cite offsets. |
| `l2ebc.py` | Lunar 2: Eternal Blue Complete (PS1): unpacks `DATA.IDX/PAK/UPD` (a port of wdtools `l2eb_data`) and scans `SCN/` with Supper's string reader from `l2eb_txt.cpp`. That reader is commented out upstream, so it is ported here. |
| `harmony.py` | Silver Star Harmony (PSP): unpacks `ScriptPack.dat` (FPAC of gzip members) and reads the UTF-16 dialogue in each `LTCV` script file. Written from scratch, because no tool exists. |
| `ips_text.py` | Lunar: Walking School (Game Gear): reads an IPS patch (records, merged regions, the font it draws) and dumps the Aeon Genesis English script from the patch alone, no ROM needed, in message-id order (via `gg.py`), then the strings no id reaches as "leftover". Custom one-byte table derived from the patch's font (glyph = byte - 0x10); `09 xx` is a portrait. |
| `gg.py` | Walking School (Game Gear) message engine, traced in the Japanese ROM: ids `F0nn`-`FEnn` = block, index; block table at 0x14AE; messages found by skipping 00-terminated strings with the control parameter counts at 0x149D. `jp` dumps the Japanese ROM (kana table from its font, voiced kana from context; no kanji), `pair` writes Japanese and English side by side by id. |
| `msl.py` | Mahou Gakuen Lunar! (Saturn): runs studio-lucia's `msl_script_dump` on `S00.FLD`-`S12.FLD`, turns its CSVs (Shift JIS decoded to UTF-8) into the dump, and makes the offsets file offsets using the FLD header. |
| `gba_legend.py` | Lunar Legend (GBA): `script` decompresses the 78 per-map LZSS event-script blocks and dumps the inline dialogue, narration, and choices. `strings` dumps the uncompressed menu, item, and name strings. Format below. |
| `sss_saturn.py` | Silver Star Story (Saturn, Japan), both the 1996 disc (plain `TEXT/` folder; `--original` passes lsb's `sss` flag) and the 1997 MPEG disc (`TEXT.DAT` bundle, unpacked here). Runs lsb in 2-byte mode through `sssc.decode_texts`. `sjis` converts `AR_BOOK.TXT` (the voiced FMV script, Shift-JIS) to UTF-8. |
| `lsb_unmapped_glyph.patch` | A second lsb patch: a font code missing from `font_table.txt` prints as `{XXXX}` instead of vanishing. |
| `l2eb_saturn.py` | Lunar 2: Eternal Blue (Saturn, Japan): unpacks the root files `1` and `2` (numbered like MrConan1's `l2extract`) and reads every `ES` dialogue block with a port of his `l2_txt_decode`. Corrects his v1.0 font table: 奥 was missing at 288, which put 288-333 one glyph early, and seven single entries were wrong. |

## One-time setup on Windows (what was needed)

- **chdman**: `winget install MAMEdev.MAME --location <dir>`. Without `--location`, the
  silent install fails ("This package requires an install location"). `chdman.exe` is
  in that folder.
  `chdman extractcd -i X.chd -o X.cue -ob X.bin` per disc.
- **CSO**: no tool needed; `discfs.py` reads `.cso` directly.
- **wdtools** (`git clone https://github.com/suppertails66/wdtools`): the Makefile
  needs make and libpng. Instead, compile `blackt/src/*/*.cpp` into `libblackt.a` with
  Strawberry Perl's g++ 13 (`-std=gnu++11`), then build each tool alone:
  `g++ -static -std=gnu++11 -O2 -Iblackt/src -Isrc src/<tool>.cpp -o <tool>.exe -L. -lblackt`.
  Two things to watch:
  - `scriptrip_tss` also needs `src/scriptrip_tss_utils.cpp`. The other tools must
    not link that file, or the linker reports duplicate symbols.
  - Build with `-static`. Otherwise the exe picks up Git's mingw `libstdc++-6.dll`
    and exits with code 127 without printing anything.
- **lsb** (`git clone https://github.com/MrConan1/lsb`): `git apply lsb_file_offset.patch`, then
  `gcc -static -O2 main.c snode_list.c util.c parse_script.c parse_binary.c parse_binary_psx.c parse_binary_reEng.c psx_decode.c update_script.c write_script.c bpe_compression.c -o lsb.exe`.
  lsb reads `lsss_txtcmpstr_us.bin`, `font_table.txt`, and `bpe.table` from the current
  directory. `sssc.py` copies them into its work folder.
- For the Saturn JP discs, also `git apply lsb_unmapped_glyph.patch` before building lsb, and
  `git clone https://github.com/MrConan1/lunar2_eb_sat_tools` (its `font_table/lunar2_font_table.txt`).
- Substitutions for Eternal Blue: `substitutions.txt` from
  `https://github.com/studio-lucia/lunar_eb_script`.

## Commands (as run for the USA discs)

```sh
T=tools/lunar_scripts; L=lunar_scripts
python -I $T/discfs.py extract "<disc>.bin" $L/<game>/files            # Sega CD
python -I $T/segacd.py tss $L/tss_segacd/files scriptrip_tss.exe $L/tss_segacd/script_en.txt --subs $T/subs_tss.txt
python -I $T/segacd.py eb  $L/eb_segacd/files  scriptrip.exe     $L/eb_segacd/script_en.txt  --subs lunar_eb_script/substitutions.txt
python -I $T/discfs.py extract "<SSSC disc 1>.bin" $L/sssc_ps1/disc1 "*.FIL"
python -I $T/sssc.py $L/sssc_ps1/disc1/LUNADATA.FIL lsb.exe <lsb repo dir> $L/sssc_ps1/work $L/sssc_ps1/script_en.txt
python -I $T/discfs.py extract "<L2EBC disc 1>.bin" $L/l2ebc_ps1/disc1 "DATA.*"
python -I $T/l2ebc.py $L/l2ebc_ps1/disc1/DATA.IDX $L/l2ebc_ps1/disc1/DATA.PAK $L/l2ebc_ps1/disc1/DATA.UPD $L/l2ebc_ps1/work $L/l2ebc_ps1/script_en.txt
python -I $T/discfs.py extract "<Harmony>.cso" $L/harmony_psp/files "*ScriptPack.dat"
python -I $T/harmony.py $L/harmony_psp/files/PSP_GAME/USRDIR/LUNAR/DATA/PACK/ScriptPack.dat $L/harmony_psp/work $L/harmony_psp/script_en.txt
python -I $T/ips_text.py dump "$L/roms/Lunar - Sanposuru Gakuen (Japan) [T-En by Aeon Genesis v1.00].ips" $L/walking_school_gg/script_en.txt
python -I $T/gg.py jp   "$L/roms/Lunar - Sanposuru Gakuen (Japan).gg" $L/walking_school_gg/script_jp.txt
python -I $T/gg.py pair "$L/roms/Lunar - Sanposuru Gakuen (Japan).gg" "$L/roms/Lunar - Sanposuru Gakuen (Japan) [T-En by Aeon Genesis v1.00].gg" $L/walking_school_gg/jp_en.txt
bin/mame/chdman extractcd -i "roms/Mahou Gakuen Lunar! (Japan) (1M).chd" -o discs/msl_saturn/msl.cue -ob discs/msl_saturn/msl.bin   # from $L
python -I $T/discfs.py extract $L/discs/msl_saturn/msl.bin $L/msl_saturn_jp/files "S??.FLD"
python -I $T/msl.py $L/tools/msl_script_tools/target/release/msl_script_dump.exe $L/msl_saturn_jp/files $L/msl_saturn_jp/csv $L/msl_saturn_jp/script_jp.txt
python -I $T/gba_legend.py script  "$L/roms/Lunar Legend (USA).gba" $L/legend_gba/script_en.txt
python -I $T/gba_legend.py strings "$L/roms/Lunar Legend (USA).gba" $L/legend_gba/strings_en.txt
# Saturn, Japan (track 1 of each bin is MODE1/2352 ISO9660; discfs.py reads it as is)
python -I $T/discfs.py extract "<SSS 1996>.bin" $L/sss_saturn_jp/files "TEXT/*"
python -I $T/sss_saturn.py $L/sss_saturn_jp/files/TEXT lsb.exe <lsb repo dir> $L/sss_saturn_jp/work $L/sss_saturn_jp/script_jp.txt --original
python -I $T/discfs.py extract "<SSS MPEG>.bin" $L/sssc_saturn_jp/files TEXT.DAT AR_BOOK.TXT
python -I $T/sss_saturn.py $L/sssc_saturn_jp/files/TEXT.DAT lsb.exe <lsb repo dir> $L/sssc_saturn_jp/work $L/sssc_saturn_jp/script_jp.txt
python -I $T/sss_saturn.py sjis $L/sssc_saturn_jp/files/AR_BOOK.TXT $L/sssc_saturn_jp/ar_book_jp.txt
python -I $T/discfs.py extract "<L2 disc 1>.bin" $L/l2eb_saturn_jp/disc1 1 2
python -I $T/l2eb_saturn.py $L/l2eb_saturn_jp/disc1/1 $L/l2eb_saturn_jp/disc1/2 lunar2_eb_sat_tools/font_table/lunar2_font_table.txt $L/l2eb_saturn_jp/work $L/l2eb_saturn_jp/script_jp.txt
```

Both SSSC discs and all three L2EBC discs carry the same data archive, so disc 1 is
enough.

## Running on the Japanese releases

| Game | What to do | Status |
|---|---|---|
| Eternal Blue (Mega CD) | `segacd.py ebjp FILES scriptrip_jp.exe OUT --table wdtools/src/scriptrip_jp_thingy.txt`. Text is kana bytes minus 0x20, and kanji are 16-bit (`index & 0x1FF` + 0xE0). The Thingy table converts them to Unicode. | Tool exists. Not run here (no JP disc). |
| The Silver Star (Mega CD) | No JP ripper. Supper's notes (`wdtools/notes/lunartss_notes`) give the encoding: bytes >= 0x20 minus 0x20 index a 1bpp 16x16 font at 0x1D010 of `TOMISUB.BIN`. Kanji are two bytes when the first is 0x10-0x1F (subtract 0xF20). 00 ends, 01 is a line break, 02 a box break, and 04 xx a portrait. To support it, build a Thingy table from that font, then add a JP mode to a port of `scriptrip_tss` that reads two-byte kanji. | Needs work. |
| Silver Star Story (Saturn, 1996 and MPEG 1997) | `sss_saturn.py` (lsb 2-byte mode; `--original` for the 1996 disc). No unmapped glyphs on either disc. The MPEG font reuses the unused full-width Latin slots for new kanji, so the leftover JAM debug menu in its `TEXT007.DAT` reads as garbage (the 1996 disc reads it cleanly). | Done: 8,559 and 8,604 messages. |
| Silver Star Story (PS1 JP) | `sssc.py ... --ienc 0` (lsb's 2-byte mode, using its `font_table.txt`). PS1 JP should be the same family (studio-lucia/lunardata covers both). | Untested (no disc). |
| Lunar 2 (Saturn) | `l2eb_saturn.py`. Both discs carry byte-identical `1`, `2`, and `3` (only the 49-byte `4` differs), so disc 1 is enough. Counts include duplicates: many map variants repeat the same NPC lines. The narrated prologue is subtitle pictures in data file 1234 (MrConan1 `l2_subt_extract`, 4bpp), not text; it was transcribed by eye. The Goddess Tower recording (old Luna's hologram) and Lucia's Blue Star history are voiced Cinepak movies on disc 2 (`O065`, `O064`) with no subtitles or burned-in text, and no script file holds their lines, so their Japanese exists only as audio. | Done: 8,025 messages. |
| Lunar 2 (PS1 JP) | The text encoding differs (2-byte). `l2ebc.py`'s reader is English-only. MrConan1's `l2_txt_decode` type 1 reads JP PSX `ES` blocks (Shift-JIS words 0x8000-0x9FFF); `l2eb_saturn.py` could add it. | Needs work (no disc). |
| Harmony (PSP JP) | `harmony.py` should work as is, because the text is UTF-16 (kana and kanji are just more code points). | Untested. |
| Walking School (GG JP) | `gg.py jp` (Japanese) and `gg.py pair` (side by side with the English, by the game's own message ids). | Done: 1,649 messages; 1,649 of 1,649 ids pair up. |
| Mahou Gakuen Lunar! (Saturn JP) | `msl.py` around studio-lucia/msl_script_tools (`cargo build --release`; it pulls fldtools from crates.io). | Done: 10,750 messages, no speakers. |
| Lunar Legend (GBA JP) | `gba_legend.py script ROM OUT --jp`. The decompressor, opcodes, and u16 units are engine code, and the pointer table is found by search. `--jp` accepts any glyph byte (kana probably 0x20-0xA1) and the two-byte units (high byte 0x10-0x1F = kanji, printed as `{Wxxxx}`). Names need a table drawn from the JP font; the on-demand glyph loader has not been traced. | Untested (no JP ROM). |

## Lunar Legend (GBA) script format

Found by tracing in BizHawk (mGBA core): a write callback on the EWRAM script buffer led
to the decompressor, and a read callback on its text led to the renderer.

- **Pointer table** (USA): ROM 0x7FD564, 140 u32 pointers (one per map slot) to 78 distinct
  blocks at 0x62DAE4-0x6BF042.
- **Block (LZSS)**: `u32 size, u32 data_len, data[data_len], flag bits`. Flags are LSB first,
  one per token: 0 = literal byte; 1 = u16 LE `v` from the data, copy `(v >> 12) + 3` bytes
  from `(v & 0xFFF) + 1` back. The decoder is at 0x08000D9C (state at IWRAM 0x03001990).
- **Script**: decompressed to EWRAM 0x02016000. It holds 256 u16 event offsets, then
  bytecode from 0x02016200 (80 opcodes, handler table at 0x0862D6C0). Text is inline in
  op `00 xx nnnn yyyy` (dialogue), op `17 xx xx xx nnnn` (narration), and op `33 nn ...`
  (8-byte header, a choice), followed by u16 units up to `0F00`.
- **Units** are u16 LE. High byte 0 = a glyph, using the same table as the plain strings plus
  the punctuation listed in `gba_legend.py`. Otherwise the high byte is a control and the
  low byte its parameter: 07 wait, 08 new box, 09 line break, 0A auto-advance (frames),
  0D/0E portrait, 0F end.

The USA dump has 10,144 messages: 9,984 boxes and 160 choices.

## Walking School (Game Gear) message engine

Traced in the Japanese ROM; the Aeon Genesis patch keeps it and only repoints the blocks.

- **Ids**: a 16-bit id at or above 0xF000 is `block = high byte - 0xF0`, `index = low byte`
  (0x12F7). Scripts store ids big-endian (`F2 3D`); code loads them (`LD HL,0xFE7D`).
- **Block table**: 0x14AE, 15 entries of (bank, address); the bank goes in slot 1 and the next
  bank in slot 2. Block 3 is empty. Japanese text is in banks 4-7, 0x1B, 0x1D, and 0x1F; the
  English patch points the table at 0x80000-0xAE996.
- **Lookup** (0x129E): skip `index` 00-terminated strings. Bytes below 0x10 are controls and
  skip the parameter count in the table at 0x149D (`00 00 00 01 01 01 02 02 02 01 04 00 01 03 00 00`);
  a parameter can be 00. Nothing stores a block's length, so `gg.BLOCK_LENGTHS` records where
  each block's text ends (next block, or data), cross-checked against the other ROM.
- **Text**: 01 line break, 0B wait and clear, 09 xx portrait, 03 xx word xx of the list at
  0x76B0 (English 0x96800). The English item descriptions use 07 as a one-byte line break.
- **Japanese table**: the font at 0x48200, tile = byte - 0x10: punctuation 10-1F, digits 20-29,
  A-Z 2A-43, a-z 44-5D, ー 5E, あ-ん 5F-8C, small ぁ-っ 8D-95, ア-ン 96-C3, small ァ-ッ C4-CC.
  CD-FF are the voiced kana (が-ぽ, ヴ, ガ-ポ). They have no tile of their own (tiles CD-FF are
  window borders; ゛ and ゜ at 1C/1D sit at the bottom of the tile, as if drawn on the row
  above), so they were read from context. No kanji.
- **Alignment**: of the 692 ids with portraits, 684 have the same portrait sequence in both
  ROMs; the 8 others are lines the translators moved between neighboring messages.
