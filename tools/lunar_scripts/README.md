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
| `ips_text.py` | Lunar: Walking School (Game Gear): reads an IPS patch (records, merged regions, the font it draws) and dumps the Aeon Genesis English script from the patch alone, no ROM needed. Custom one-byte table derived from the patch's font (glyph = byte - 0x10); `09 xx` is a portrait. |
| `gba_legend.py` | Lunar Legend (GBA): **partial**. It dumps only the uncompressed strings (item descriptions, names, and menus). The dialogue is compressed with a scheme that has not been found. |

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
python -I $T/gba_legend.py "Lunar Legend (USA).gba" $L/legend_gba/strings_en.txt
```

Both SSSC discs and all three L2EBC discs carry the same data archive, so disc 1 is
enough.

## Running on the Japanese releases

| Game | What to do | Status |
|---|---|---|
| Eternal Blue (Mega CD) | `segacd.py ebjp FILES scriptrip_jp.exe OUT --table wdtools/src/scriptrip_jp_thingy.txt`. Text is kana bytes minus 0x20, and kanji are 16-bit (`index & 0x1FF` + 0xE0). The Thingy table converts them to Unicode. | Tool exists. Not run here (no JP disc). |
| The Silver Star (Mega CD) | No JP ripper. Supper's notes (`wdtools/notes/lunartss_notes`) give the encoding: bytes >= 0x20 minus 0x20 index a 1bpp 16x16 font at 0x1D010 of `TOMISUB.BIN`. Kanji are two bytes when the first is 0x10-0x1F (subtract 0xF20). 00 ends, 01 is a line break, 02 a box break, and 04 xx a portrait. To support it, build a Thingy table from that font, then add a JP mode to a port of `scriptrip_tss` that reads two-byte kanji. | Needs work. |
| Silver Star Story (PS1 JP / Saturn) | `sssc.py ... --ienc 0` (lsb's 2-byte mode, using its `font_table.txt`). lsb's 2-byte path is proven on Saturn; PS1 JP should be the same family (studio-lucia/lunardata covers both). | Untested. |
| Lunar 2 (PS1 JP) | The text encoding differs (2-byte). `l2ebc.py`'s reader is English-only. Use studio-lucia/eternaldata notes and MrConan1/lunar2_eb_sat_tools (Saturn) as the reference. | Needs work. |
| Harmony (PSP JP) | `harmony.py` should work as is, because the text is UTF-16 (kana and kanji are just more code points). | Untested. |
| Walking School (GG JP) | `ips_text.py` reads only the English patch. The Japanese ROM's text is untouched by it; ripping it needs the ROM, its kana table, and its pointer tables. | Needs the ROM. |
| Lunar Legend (GBA JP) | Same block as the English: the dialogue compression is unknown. | Blocked. |
