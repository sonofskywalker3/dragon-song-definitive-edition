# Dragon Song Definitive Edition

A ROM hack of Lunar: Dragon Song (Nintendo DS, USA) that fixes the game's systems so that play outside
of battle feels like Lunar 1 and 2. The design decisions are in [docs/design.md](docs/design.md), and
what still has to be learned about the game before building is in [docs/research.md](docs/research.md).

## Credits and origin

This project started after watching i am a dot's video
[My Brief Obsession with the Worst RPG Ever Made](https://www.youtube.com/watch?v=g3ZHiycAYeQ) (2026),
whose closing list of fixes for Lunar: Dragon Song lines up closely with what this hack sets out to do.
Thanks for the reminder that this game deserved another look.

Lunar: Dragon Song was developed by Japan Art Media with Game Arts and published by Marvelous Interactive
(Japan), Ubisoft (North America) and Rising Star Games (Europe). This repository contains no game data;
you need your own copy of the game.

## Setup

You need your own copy of the game. This repo never contains the ROM or anything extracted from it.

1. Put the USA ROM at `rom/Lunar - Dragon Song (USA).nds`.
   Expected SHA-1: `e5ac472b2a5de04215e54ab098c94247a88e1c08`.
2. Download `dsd-windows-x86_64.exe` from [ds-decomp v0.12.1](https://github.com/AetiasHax/ds-decomp/releases)
   to `tools/dsd.exe`.
3. Extract the ROM:

   ```
   tools/dsd.exe rom extract -r "rom/Lunar - Dragon Song (USA).nds" -o extract
   ```

4. Rebuild a ROM from `extract/`:

   ```
   tools/dsd.exe rom build -c extract/config.yaml -o build/dsde.nds
   ```

An unmodified rebuild matches the original byte for byte except the secure area checksum at header
offset 0x6C and the header CRC at 0x15E, which need an ARM7 BIOS (`-7`) to recompute. Emulators ignore them.

For real hardware, put your own DS ARM7 BIOS dump (16 KB, for example from a DSi with dumpTool) at
`tools/bios7.bin` before running `uv run python -m dsde.patches` (or pass `--arm7-bios <path>`). The build
then passes it to dsd, which writes the secure area checksum. Our patched ROMs need this because the new
ITCM code makes the arm9 autoload table at 0x02000B00, inside the secure area, differ from the original.
Without it the checksum stays 0 (dsd recomputes the header CRC either way).
Checked 2026-10-06: with a good dump (CRC32 1280F0D5) an unmodified rebuild is byte-identical to the
original ROM, secure area checksum 0x1413 included.

Hardware notes (2026-10-06, from the nds-bootstrap source, not yet tested on a device): nds-bootstrap
(TWiLight Menu++ on a DSi or 3DS) only puts code in ITCM for a few DSiWare titles and has no fix patch
for this game (ALNE), so our ITCM cave at 0x01FF8300 should not collide with it.

## Layout of the game

- `extract/arm9/arm9.bin`: all of the game code (about 690 KB, uncompressed, no overlays).
- `extract/files/*.dat`: packed data archives. Likely contents from the names:
  `btldata` (battle and enemy data), `script` and `evedata` (story text and events), `mapdata` (maps),
  `shoppack` (shops), `facedata` (portraits), `sound_data.sdat` (music and sound).
