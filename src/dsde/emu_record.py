"""Opens EmuHawk for a person to play while emu/record_path.lua logs where the player walks.

Uses the normal EmuHawk config (keyboard and mouse as you set them up) and the post-intro battery
save, so Load Game, slot 1 starts in Jian's room. Close the emulator when done; the log is
<out>/path.log.

    uv run python -m dsde.emu_record --rom build/par_a/dsde_a.nds
"""

import argparse
import logging
import os
import subprocess
from pathlib import Path

from dsde.emu import (
    DEFAULT_ROM,
    EMU_OUT,
    EMUHAWK,
    PROJECT_ROOT,
    START_SAVE,
    install_save,
)

RECORDER = PROJECT_ROOT / "emu" / "record_path.lua"

logger = logging.getLogger(__name__)


def record(rom: Path, save: Path | None, out: Path) -> Path:
    """Run EmuHawk with the recorder until it is closed; return the path log."""
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rom = rom.resolve()
    if save is not None:
        install_save(save, rom)
    subprocess.run(
        [str(EMUHAWK), f"--lua={RECORDER}", str(rom)],
        check=False,
        env={**os.environ, "DSDE_EMU_OUT": str(out)},
    )
    return out / "path.log"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.emu_record")
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--save", type=Path, default=START_SAVE)
    parser.add_argument("--out", type=Path, default=EMU_OUT / "record")
    args = parser.parse_args()
    logger.info("path log: %s", record(args.rom, args.save, args.out))


if __name__ == "__main__":
    main()
