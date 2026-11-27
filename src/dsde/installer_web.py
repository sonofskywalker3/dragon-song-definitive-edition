"""Builds the installer as one web page: installer/template.html with the pack and the engine's modules inside.

    uv run python -m dsde.installer_pack           # first, the pack
    uv run python -m dsde.installer_web            # -> build/installer/dsde-installer.html

The page runs the same Python engine (dsde.installer) in the browser with Pyodide, so the ROM never leaves the
player's computer. It works opened straight from disk; Pyodide itself loads from its CDN.
"""

import argparse
import base64
import html
import json
import logging
import re
from pathlib import Path

from dsde.installer_pack import PACK_OUT, ROM_SHA1
from dsde.installer_switches import SWITCHES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = PROJECT_ROOT / "installer" / "template.html"
PAGE_OUT = PROJECT_ROOT / "build" / "installer" / "dsde-installer.html"
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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.installer_web")
    parser.add_argument("--version", default="development build")
    parser.add_argument("--out", type=Path, default=PAGE_OUT)
    args = parser.parse_args()
    build_page(args.version, out=args.out)


if __name__ == "__main__":
    main()
