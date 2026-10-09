"""Builds a patched ROM: copy extract/, apply the chosen features, run dsd.

uv run python -m dsde.patches                      # Classic edition -> build/dsde.nds
uv run python -m dsde.patches --edition retold     # Retold edition -> build/dsde-retold.nds
uv run python -m dsde.patches --with party-chat    # an edition plus extra features
uv run python -m dsde.patches timed-run walk-speed # exactly these features
"""

import argparse
import logging
import re
import shutil
import subprocess
from pathlib import Path
from types import MappingProxyType

from dsde.features import EDITION_ALIASES, EDITIONS, FEATURES, REQUIRES
from dsde.patching import PatchError, apply_arm9, apply_data, build_itcm, layout_cave

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTRACT = PROJECT_ROOT / "extract"
DSD = PROJECT_ROOT / "tools" / "dsd.exe"
OUTPUT_ROM = PROJECT_ROOT / "build" / "dsde.nds"
DEFAULT_EDITION = "classic"
EDITION_OUTPUTS = MappingProxyType(
    {
        "classic": OUTPUT_ROM,
        "retold": PROJECT_ROOT / "build" / "dsde-retold.nds",
    }
)
# Your own DS ARM7 BIOS dump (16 KB). With it dsd encrypts the secure area and writes its checksum
# (header 0x6C); without it the checksum stays 0, which emulators ignore and real hardware may not.
ARM7_BIOS = PROJECT_ROOT / "tools" / "bios7.bin"

logger = logging.getLogger(__name__)


def build(
    feature_names: list[str], output: Path = OUTPUT_ROM, arm7_bios: Path = ARM7_BIOS
) -> Path:
    """Copy extract/, apply the named features, and build a ROM."""
    wanted = {f.name: f for f in FEATURES}
    unknown = set(feature_names) - wanted.keys()
    if unknown:
        raise PatchError(f"unknown features: {sorted(unknown)}")
    for name, needs in REQUIRES.items():
        for needed in needs:
            if name in feature_names and (
                needed not in feature_names
                or feature_names.index(needed) > feature_names.index(name)
            ):
                raise PatchError(f"{name} needs {needed} built before it")
    chosen = [wanted[name] for name in feature_names]
    mod_extract = output.parent / f"{output.stem}_extract"
    if mod_extract.exists():
        shutil.rmtree(mod_extract)
    shutil.copytree(EXTRACT, mod_extract)
    symbols = layout_cave(chosen)
    arm9_path = mod_extract / "arm9" / "arm9.bin"
    arm9 = bytearray(arm9_path.read_bytes())
    for feature in chosen:
        apply_arm9(arm9, feature, symbols)
    arm9_path.write_bytes(arm9)
    itcm_path = mod_extract / "arm9" / "itcm.bin"
    itcm = build_itcm(itcm_path.read_bytes(), chosen, symbols)
    itcm_path.write_bytes(itcm)
    itcm_yaml = mod_extract / "arm9" / "itcm.yaml"
    itcm_yaml.write_text(
        re.sub(r"code_size: \d+", f"code_size: {len(itcm)}", itcm_yaml.read_text())
    )
    apply_data(mod_extract / "files", chosen)
    config = mod_extract / "config.yaml"
    command = [str(DSD), "rom", "build", "-c", str(config), "-o", str(output)]
    if arm7_bios.is_file():
        command += ["-7", str(arm7_bios)]
    else:
        logger.warning(
            "no ARM7 BIOS at %s: secure area checksum left at 0 (fine for emulators)",
            arm7_bios,
        )
    subprocess.run(command, check=True)
    logger.info("built %s with %s", output, ", ".join(feature_names) or "no features")
    return output


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.patches")
    parser.add_argument(
        "features", nargs="*", help="feature names; default is the edition's set"
    )
    parser.add_argument(
        "--edition",
        choices=[*sorted(EDITIONS), *sorted(EDITION_ALIASES)],
        default=DEFAULT_EDITION,
        help="classic (mechanics only, vanilla wording) or retold (classic plus the rewrite);"
        " engine and story are the old names",
    )
    parser.add_argument(
        "--with",
        dest="extra",
        nargs="+",
        default=[],
        help="features to build on top of the edition's set (ignored with explicit features)",
    )
    parser.add_argument(
        "--output", type=Path, help="default build/dsde.nds, or build/dsde-retold.nds"
    )
    parser.add_argument("--arm7-bios", type=Path, default=ARM7_BIOS)
    args = parser.parse_args()
    edition = args.edition
    if edition in EDITION_ALIASES:
        edition = EDITION_ALIASES[edition]
        logger.warning("--edition %s is now %s", args.edition, edition)
    names = args.features or [*EDITIONS[edition], *args.extra]
    build(names, args.output or EDITION_OUTPUTS[edition], args.arm7_bios)


if __name__ == "__main__":
    main()
