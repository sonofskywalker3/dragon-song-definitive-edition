"""Builds the installer as one web page: installer/template.html with the pack and the engine's modules inside.

    uv run python -m dsde.installer_pack           # first, the pack
    uv run python -m dsde.installer_web            # -> build/installer/dsde-installer.html
    uv run python -m dsde.installer_web --release 0.1.7    # a release: see `release`

The page runs the same Python engine (dsde.installer) in the browser with Pyodide, so the ROM never leaves the
player's computer. It works opened straight from disk; Pyodide itself loads from its CDN.
"""

import argparse
import base64
import hashlib
import html
import json
import logging
import re
from pathlib import Path

from dsde.edition_check import changes, is_fix
from dsde.feat_text import VANILLA_SCRIPTS
from dsde.installer import install, load_pack
from dsde.installer_pack import PACK_OUT, ROM_SHA1, write_pack
from dsde.installer_switches import (
    RETOLD_REPORT,
    SWITCHES,
    edition_switches,
    feature_names,
)
from dsde.ndsrom import file, read_rom

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = PROJECT_ROOT / "installer" / "template.html"
PAGE_OUT = PROJECT_ROOT / "build" / "installer" / "dsde-installer.html"
ORIGINAL_ROM = PROJECT_ROOT / "rom" / "Lunar - Dragon Song (USA).nds"
RELEASE_DIR = PROJECT_ROOT / "build" / "release"
RELEASE_NAME = "Dragon Song Definitive Edition v{version} installer.html"
EDITIONS = ("classic", "retold")
PYODIDE_VERSION = "0.29.4"
ENGINE = (
    "__init__.py",
    "archive.py",
    "bps.py",
    "linker.py",
    "ndsrom.py",
    "installer.py",
    "installer_switches.py",
)
SOURCE_DIR = Path(__file__).resolve().parent
PLACEHOLDER = re.compile(r"@@([A-Z0-9_]+)@@")

logger = logging.getLogger(__name__)


def _script_json(value: object) -> str:
    """JSON safe inside a <script> element: no "<" at all, so no tag or comment can open or close."""
    return json.dumps(value).replace("<", "\\u003c")


def build_page(version: str, pack: Path = PACK_OUT, out: Path = PAGE_OUT) -> Path:
    modules = {name: (SOURCE_DIR / name).read_text(encoding="utf-8") for name in ENGINE}
    switches = [
        {
            "number": s.number,
            "group": s.group,
            "label": s.label,
            "tooltip": s.tooltip,
            "needs": list(s.needs),
            "default": s.default,
            "details": s.details,
        }
        for s in SWITCHES
    ]
    values = {
        "PACK": base64.b64encode(pack.read_bytes()).decode("ascii"),
        "MODULES": _script_json(modules),
        "SWITCHES": _script_json(switches),
        "EDITIONS": _script_json(
            {e: sorted(edition_switches(e)) for e in ("classic", "retold")}
        ),
        "REPORT": _script_json([[head, list(items)] for head, items in RETOLD_REPORT]),
        "ROM_SHA1": ROM_SHA1,
        "PYODIDE": PYODIDE_VERSION,
        "VERSION": html.escape(version),
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    missing = set(values) - set(PLACEHOLDER.findall(template))
    if missing:
        raise ValueError(f"{sorted(missing)} missing from {TEMPLATE}")
    # One pass over the template, so nothing inside an inserted value is ever replaced.
    page = PLACEHOLDER.sub(lambda m: values[m.group(1)], template)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    logger.info("wrote %s (%d bytes)", out, out.stat().st_size)
    return out


class ReleaseError(RuntimeError):
    """Raised when a release would ship something it must not."""


def release(version: str, original: Path = ORIGINAL_ROM) -> Path:
    """The release file: a fresh pack, the page named for the version, and its Classic and Retold results checked.

    Releases ship this page only, no patches (Jeff, 2026-11-28). Classic must change no dialogue beyond the
    name-tag fixes (dsde.edition_check); the SHA-1 of each edition's ROM is logged for the release notes.
    """
    pack_path = write_pack()
    page = build_page(
        version, pack_path, RELEASE_DIR / RELEASE_NAME.format(version=version)
    )
    pack = load_pack(pack_path)
    source = original.read_bytes()
    for edition in EDITIONS:
        names = feature_names(edition_switches(edition), tuple(pack["order"]))
        rom = install(source, names, pack)
        logger.info("%s ROM SHA-1 %s", edition.title(), hashlib.sha1(rom).hexdigest())
        if edition == "classic":
            script = file(read_rom(rom), "script.dat")
            bad = [
                c
                for c in changes(VANILLA_SCRIPTS.read_bytes(), script)
                if not is_fix(c)
            ]
            if bad:
                raise ReleaseError(
                    f"Classic changes {len(bad)} messages beyond the name tags"
                )
    logger.info("release file: %s", page)
    return page


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.installer_web")
    parser.add_argument("--version", default="development build")
    parser.add_argument("--out", type=Path, default=PAGE_OUT)
    parser.add_argument(
        "--release", metavar="X.Y.Z", help="write the release file for this version"
    )
    args = parser.parse_args()
    if args.release:
        release(args.release)
    else:
        build_page(args.version, out=args.out)


if __name__ == "__main__":
    main()
