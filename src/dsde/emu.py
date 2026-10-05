"""Runs a plan file in BizHawk (EmuHawk) through emu/run_plan.lua and returns its log."""

import argparse
import json
import logging
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMUHAWK = PROJECT_ROOT / "tools" / "bizhawk" / "EmuHawk.exe"
RUNNER = PROJECT_ROOT / "emu" / "run_plan.lua"
EMU_OUT = PROJECT_ROOT / "build" / "emu"
DEFAULT_ROM = PROJECT_ROOT / "rom" / "Lunar - Dragon Song (USA).nds"
EMUHAWK_CONFIG = EMUHAWK.parent / "config.ini"
HARNESS_CONFIG = EMU_OUT / "harness_config.ini"
TOUCH_AXES = ("Touch X", "Touch Y")
TIMEOUT_SECONDS = 600

logger = logging.getLogger(__name__)


def write_harness_config() -> Path:
    """Copy EmuHawk's config with the mouse unbound from the DS touch axes.

    The mouse binding overrides the touch position a Lua script sets, so plans could only
    touch the screen centre. The user's own config is left as it is.
    """
    config = json.loads(EMUHAWK_CONFIG.read_text(encoding="utf-8-sig"))
    nds_axes = config["AllTrollersAnalog"]["NDS Controller"]
    for axis in TOUCH_AXES:
        nds_axes[axis]["Value"] = ""
    HARNESS_CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return HARNESS_CONFIG


def run_plan(plan: Path, rom: Path = DEFAULT_ROM) -> str:
    """Run one plan to completion and return the run log text."""
    (EMU_OUT / "states").mkdir(parents=True, exist_ok=True)
    (EMU_OUT / "plan_path.txt").write_text(str(plan.resolve()).replace("\\", "/"))
    log_path = EMU_OUT / "run.log"
    log_path.unlink(missing_ok=True)
    try:
        subprocess.run(
            [
                str(EMUHAWK),
                f"--config={write_harness_config()}",
                f"--lua={RUNNER}",
                str(rom),
            ],
            timeout=TIMEOUT_SECONDS,
            check=False,
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
    args = parser.parse_args()
    logger.info(run_plan(args.plan, args.rom))


if __name__ == "__main__":
    main()
