"""The custom installer's engine: the player's ROM and a choice of switches in, a patched ROM out.

Pure Python with no dependencies beyond this package's linker, archive, bps, and ndsrom modules; the front ends
(a window or a web page) call `install`. From the command line, for testing:

    uv run python -m dsde.installer ROM OUT                     # the defaults (the full release)
    uv run python -m dsde.installer ROM OUT --off 47 48         # these switches off
    uv run python -m dsde.installer ROM OUT --features a b c    # exactly these features (and ALWAYS)
    uv run python -m dsde.installer ROM OUT --bps out.bps       # also write a patch of the result
"""

import argparse
import gzip
import hashlib
import json
import logging
from pathlib import Path

from dsde.bps import create as bps_create
from dsde.installer_switches import ALWAYS, defaults, feature_names
from dsde.linker import (
    ITCM_BASE,
    LinkError,
    build_itcm,
    choose,
    patch_archives,
    patch_arm9,
    pieces_from_pack,
)
from dsde.ndsrom import file, read_rom, set_file, write_rom

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACK = PROJECT_ROOT / "build" / "installer" / "pack.json.gz"
ARCHIVE_SUFFIX = ".dat"

logger = logging.getLogger(__name__)


def load_pack(path: Path = PACK) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def check_requires(pack: dict, names: list[str]) -> None:
    """Every feature's prerequisites are chosen and come before it (patches.build's check)."""
    for name, needs in pack["requires"].items():
        for needed in needs:
            if name in names and (
                needed not in names or names.index(needed) > names.index(name)
            ):
                raise LinkError(f"{name} needs {needed} built before it")


def install(rom_bytes: bytes, names: list[str], pack: dict) -> bytes:
    """rom_bytes (the original game, checked by SHA-1) patched with the features named, in pack order."""
    if hashlib.sha1(rom_bytes).hexdigest() != pack["rom_sha1"]:
        raise LinkError(
            "this is not Lunar: Dragon Song (USA), or not a clean dump of it"
        )
    order = pack["order"]
    names = sorted(dict.fromkeys(names), key=order.index)
    check_requires(pack, names)
    linked = choose(pieces_from_pack(pack), names)
    rom = read_rom(rom_bytes)
    arm9 = bytearray(rom.arm9)
    patch_arm9(arm9, linked)
    rom.arm9 = bytes(arm9)
    address, itcm, bss = rom.autoloads[0]
    if address != ITCM_BASE:
        raise LinkError("the first autoload is not the ITCM")
    rom.autoloads[0] = (address, build_itcm(itcm, linked), bss)
    archives = {
        name[: -len(ARCHIVE_SUFFIX)]: file(rom, name)
        for name in rom.names
        if name.endswith(ARCHIVE_SUFFIX)
    }
    for archive, data in patch_archives(archives, linked).items():
        set_file(rom, archive + ARCHIVE_SUFFIX, data)
    return write_rom(rom)


def switch_features(pack: dict, off: set[int]) -> list[str]:
    on = frozenset(defaults() - off)
    return feature_names(on, tuple(pack["order"]))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.installer")
    parser.add_argument("rom", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument(
        "--off", type=int, nargs="+", default=[], help="switches to turn off"
    )
    parser.add_argument(
        "--features", nargs="+", help="exactly these features (plus ALWAYS)"
    )
    parser.add_argument(
        "--bps", type=Path, help="also write a .bps patch of the result"
    )
    args = parser.parse_args()
    pack = load_pack(args.pack)
    if args.features:
        names = [*ALWAYS, *args.features]
    else:
        names = switch_features(pack, set(args.off))
    source = args.rom.read_bytes()
    patched = install(source, names, pack)
    args.out.write_bytes(patched)
    logger.info("wrote %s with %s", args.out, ", ".join(names))
    if args.bps:
        args.bps.write_bytes(bps_create(source, patched))
        logger.info("wrote %s", args.bps)


if __name__ == "__main__":
    main()
