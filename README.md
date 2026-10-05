# Dragon Song Definitive Edition

A ROM hack of Lunar: Dragon Song (Nintendo DS, USA) that fixes the game's systems so that play outside
of battle feels like Lunar 1 and 2. The design decisions are in [docs/design.md](docs/design.md), and
what still has to be learned about the game before building is in [docs/research.md](docs/research.md).

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

## Layout of the game

- `extract/arm9/arm9.bin`: all of the game code (about 690 KB, uncompressed, no overlays).
- `extract/files/*.dat`: packed data archives. Likely contents from the names:
  `btldata` (battle and enemy data), `script` and `evedata` (story text and events), `mapdata` (maps),
  `shoppack` (shops), `facedata` (portraits), `sound_data.sdat` (music and sound).
