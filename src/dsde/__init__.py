"""Dragon Song Definitive Edition tooling."""

import argparse
import logging
from pathlib import Path

from dsde.archive import unpack_all

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTRACT_FILES = PROJECT_ROOT / "extract" / "files"
UNPACKED = PROJECT_ROOT / "build" / "unpacked"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("unpack", help="decompress every archive entry into build/unpacked")
    args = parser.parse_args()
    if args.command == "unpack":
        unpack_all(EXTRACT_FILES, UNPACKED)
        logging.info("unpacked to %s", UNPACKED)
