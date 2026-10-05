"""Runs a plan file in BizHawk (EmuHawk) through emu/run_plan.lua and returns its log."""

import argparse
import logging
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMUHAWK = PROJECT_ROOT / "tools" / "bizhawk" / "EmuHawk.exe"
RUNNER = PROJECT_ROOT / "emu" / "run_plan.lua"
EMU_OUT = PROJECT_ROOT / "build" / "emu"
DEFAULT_ROM = PROJECT_ROOT / "rom" / "Lunar - Dragon Song (USA).nds"
TIMEOUT_SECONDS = 600

logger = logging.getLogger(__name__)


def run_plan(plan: Path, rom: Path = DEFAULT_ROM) -> str:
    """Run one plan to completion and return the run log text."""
    (EMU_OUT / "states").mkdir(parents=True, exist_ok=True)
    (EMU_OUT / "plan_path.txt").write_text(str(plan.resolve()).replace("\\", "/"))
    log_path = EMU_OUT / "run.log"
    log_path.unlink(missing_ok=True)
    try:
        subprocess.run(
            [str(EMUHAWK), f"--lua={RUNNER}", str(rom)],
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
