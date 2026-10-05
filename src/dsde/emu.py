"""Runs a plan file in BizHawk (EmuHawk) through emu/run_plan.lua and returns its log."""

import argparse
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMUHAWK = PROJECT_ROOT / "tools" / "bizhawk" / "EmuHawk.exe"
RUNNER = PROJECT_ROOT / "emu" / "run_plan.lua"
EMU_OUT = PROJECT_ROOT / "build" / "emu"
DEFAULT_ROM = PROJECT_ROOT / "rom" / "Lunar - Dragon Song (USA).nds"
EMUHAWK_CONFIG = EMUHAWK.parent / "config.ini"
TOUCH_AXES = ("Touch X", "Touch Y")
TIMEOUT_SECONDS = 600
SAVERAM_DIR = EMUHAWK.parent / "NDS" / "SaveRAM"
# In-game save made right after the intro (slot 1, Jian in his room). Plans that start with
# `include boot_from_save` load it from the title screen instead of replaying the intro.
START_SAVE = EMU_OUT / "saves" / "start.SaveRAM"

logger = logging.getLogger(__name__)


def write_harness_config(out: Path) -> Path:
    """Copy EmuHawk's config with the mouse unbound from the DS touch axes.

    The mouse binding overrides the touch position a Lua script sets, so plans could only
    touch the screen centre. The user's own config is left as it is.
    """
    config = json.loads(EMUHAWK_CONFIG.read_text(encoding="utf-8-sig"))
    nds_axes = config["AllTrollersAnalog"]["NDS Controller"]
    for axis in TOUCH_AXES:
        nds_axes[axis]["Value"] = ""
    harness_config = out / "harness_config.ini"
    harness_config.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return harness_config


def install_save(save: Path, rom: Path) -> None:
    """Put a battery save in place for the ROM, replacing whatever the last run left there."""
    SAVERAM_DIR.mkdir(parents=True, exist_ok=True)
    # EmuHawk names battery saves after the ROM with underscores shown as spaces
    shutil.copyfile(save, SAVERAM_DIR / f"{rom.stem.replace('_', ' ')}.SaveRAM")


def run_plan(
    plan: Path, rom: Path = DEFAULT_ROM, save: Path | None = None, out: Path = EMU_OUT
) -> str:
    """Run one plan to completion and return the run log text.

    out holds the plan pointer, log, screenshots and states, so runs with different out dirs and
    differently named ROMs (each ROM name has its own battery save) can run at the same time.
    """
    out = out.resolve()
    rom = rom.resolve()
    if save is not None:
        install_save(save, rom)
    (out / "states").mkdir(parents=True, exist_ok=True)
    (out / "plan_path.txt").write_text(str(plan.resolve()).replace("\\", "/"))
    log_path = out / "run.log"
    log_path.unlink(missing_ok=True)
    try:
        subprocess.run(
            [
                str(EMUHAWK),
                f"--config={write_harness_config(out)}",
                f"--lua={RUNNER}",
                str(rom),
            ],
            timeout=TIMEOUT_SECONDS,
            check=False,
            env={**os.environ, "DSDE_EMU_OUT": str(out)},
        )
    except subprocess.TimeoutExpired:
        logger.error("EmuHawk did not finish within %d s", TIMEOUT_SECONDS)
        raise
    return log_path.read_text() if log_path.exists() else ""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.emu")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument(
        "--save",
        type=Path,
        nargs="?",
        const=START_SAVE,
        help="install a battery save first (default: the post-intro save)",
    )
    parser.add_argument(
        "--out", type=Path, default=EMU_OUT, help="output dir (one per parallel run)"
    )
    args = parser.parse_args()
    logger.info(run_plan(args.plan, args.rom, args.save, args.out))


if __name__ == "__main__":
    main()
