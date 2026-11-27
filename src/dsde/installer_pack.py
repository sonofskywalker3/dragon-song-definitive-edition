"""Builds the installer's pack: every feature and glue piece assembled ahead of time, its address references marked.

The installer (dsde.installer, dsde.linker) then needs no assembler: it only places the pieces, fills in the
addresses, and patches the player's ROM. Run on our side, where Keystone is available:

    uv run python -m dsde.installer_pack            # -> build/installer/pack.json.gz

Address references are found by assembling each piece three times: at two addresses with the same symbols, and
at one address with every symbol moved by a different amount. A word that changes with the address is a branch
(to a symbol, or to a fixed address) or a word holding an address in the same cave; a word that changes only
with the symbols holds a symbol plus an addend. Each kind is checked against its own encoding.

Data patches are shipped as BPS deltas from the bytes they replace (which the installer checks by SHA-1), so the
pack carries no game data beyond what the release patches already do.
"""

import argparse
import base64
import gzip
import hashlib
import itertools
import json
import logging
import re
import struct
from collections.abc import Callable
from pathlib import Path

from dsde.bps import create as bps_create
from dsde.features import FEATURES, GLUE, REQUIRES
from dsde.installer_switches import ALWAYS, SWITCHES
from dsde.linker import (
    ARM_PC_AHEAD,
    BRANCH_OFFSET_MASK,
    BRANCH_OPCODE,
    BRANCH_OPCODE_MASK,
    BRANCH_SIGN,
    ITCM_CAVE,
    RELOC_BRANCH,
    RELOC_BRANCH_ABSOLUTE,
    RELOC_SELF,
    RELOC_WORD,
    WORD,
)
from dsde.patching import (
    AsmPatch,
    CaveCode,
    DataPatch,
    Feature,
    Glue,
    Patch,
    assemble,
    substitute,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACK_OUT = PROJECT_ROOT / "build" / "installer" / "pack.json.gz"
ROM_SHA1 = (
    "e5ac472b2a5de04215e54ab098c94247a88e1c08"  # Lunar - Dragon Song (USA), README
)
PACK_VERSION = 1
SYMBOL_REF = re.compile(r"\$\{(\w+)\}")
BASE_A = ITCM_CAVE + 0x1000
BASE_B = ITCM_CAVE + 0x2000
SYMBOL_START = ITCM_CAVE + 0x4000
SYMBOL_STEP = 0x1000
# Symbol i moves by SHIFT_STEP * (2i + 1) in the second assembly: an odd multiple of 4, so a data word that merely
# looks like a branch (its offset field moving by the shift moves its "target" by 4 times the shift, a multiple of
# 16) can never pass for a branch to a moved symbol.
SHIFT_STEP = 4
MAX_ALIGN_POWER = 2  # caves are only 4-byte aligned, so no directive may ask for more
ALIGN_DIRECTIVE = re.compile(r"\.(p2align|align|balign)\s+(\d+)")

logger = logging.getLogger(__name__)


class PackError(RuntimeError):
    """Raised when a piece's address references cannot be told apart."""


def _symbols(asm: str) -> tuple[dict[str, int], dict[str, int]]:
    """Two symbol tables for the references in asm: the second moves each symbol by a different amount."""
    names = sorted(set(SYMBOL_REF.findall(asm)))
    first = {name: SYMBOL_START + i * SYMBOL_STEP for i, name in enumerate(names)}
    second = {
        name: first[name] + SHIFT_STEP * (2 * i + 1) for i, name in enumerate(names)
    }
    return first, second


def _words(code: bytes) -> list[int]:
    return list(struct.unpack(f"<{len(code) // WORD}I", code))


def _branch_target(word: int, place: int) -> int:
    offset = word & BRANCH_OFFSET_MASK
    if offset & BRANCH_SIGN:
        offset -= BRANCH_OFFSET_MASK + 1
    return place + ARM_PC_AHEAD + offset * WORD


def _check_align(asm: str) -> None:
    for kind, amount in ALIGN_DIRECTIVE.findall(asm):
        power = (
            int(amount) if kind != "balign" else max(int(amount) - 1, 0).bit_length()
        )
        if power > MAX_ALIGN_POWER:
            raise PackError(
                f".{kind} {amount}: caves are only {1 << MAX_ALIGN_POWER}-byte aligned"
            )


def _is_branch(*words: int) -> bool:
    top = words[0] & ~BRANCH_OFFSET_MASK
    return all(
        (w & BRANCH_OPCODE_MASK) == BRANCH_OPCODE and w & ~BRANCH_OFFSET_MASK == top
        for w in words
    )


def find_relocs(asm: str, fixed: int | None) -> tuple[bytes, list[list]]:
    """asm assembled (at `fixed`, or at BASE_A for cave code) and its address references."""
    _check_align(asm)
    first, second = _symbols(asm)
    base = BASE_A if fixed is None else fixed
    code = assemble(substitute(asm, first), base)
    moved = assemble(substitute(asm, second), base)
    elsewhere = code if fixed is not None else assemble(substitute(asm, first), BASE_B)
    if not (len(code) == len(moved) == len(elsewhere)):
        raise PackError("the code's size depends on its addresses")
    size = len(code)
    pad = bytes(-size % WORD)
    by_shift = {second[name] - first[name]: name for name in first}
    relocs: list[list] = []
    words = zip(
        _words(code + pad), _words(moved + pad), _words(elsewhere + pad), strict=True
    )
    for i, (a, b, c) in enumerate(words):
        if a == b == c:
            continue
        offset = i * WORD
        if offset + WORD > size:
            raise PackError(f"a reference in the last {size % WORD} bytes")
        place = base + offset
        if _is_branch(a, b, c):
            target = _branch_target(a, place)
            if _branch_target(c, BASE_B + offset if fixed is None else place) == target:
                shift = _branch_target(b, place) - target
                if shift == 0:
                    relocs.append([offset, RELOC_BRANCH_ABSOLUTE, target, 0])
                    continue
                name = by_shift.get(shift)
                if name is not None:
                    relocs.append([offset, RELOC_BRANCH, name, target - first[name]])
                    continue
        if a == b and c - a == BASE_B - BASE_A:
            relocs.append([offset, RELOC_SELF, "", a - base])
        elif a == c and (b - a) & 0xFFFFFFFF in by_shift:
            name = by_shift[(b - a) & 0xFFFFFFFF]
            relocs.append([offset, RELOC_WORD, name, (a - first[name]) & 0xFFFFFFFF])
        else:
            raise PackError(
                f"the word at +{offset:#x} refers to an address in no known way"
            )
    return code, relocs


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def piece(feature: Feature, glue: Glue | None, any_of, all_of=(), none_of=()) -> dict:
    """One pack entry for a feature or a glue piece."""
    caves, code, words, data = [], [], [], []
    for patch in feature.patches:
        if isinstance(patch, CaveCode):
            assembled, relocs = find_relocs(patch.asm, None)
            caves.append(
                {"label": patch.label, "code": _b64(assembled), "relocs": relocs}
            )
        elif isinstance(patch, AsmPatch):
            assembled, relocs = find_relocs(patch.asm, patch.addr)
            if any(r[1] in (RELOC_BRANCH_ABSOLUTE, RELOC_SELF) for r in relocs):
                raise PackError(
                    f"{feature.name} @ {patch.addr:#x}: fixed code needs no layout"
                )
            code.append(
                {
                    "addr": patch.addr,
                    "end": patch.end,
                    "first": patch.first,
                    "last": patch.last,
                    "code": _b64(assembled),
                    "relocs": relocs,
                }
            )
        elif isinstance(patch, Patch):
            words.append([patch.addr, patch.old, patch.new])
        elif isinstance(patch, DataPatch):
            data.append(
                {
                    "archive": patch.archive,
                    "entry": patch.entry,
                    "offset": patch.offset,
                    "old_len": len(patch.old),
                    "old_sha1": hashlib.sha1(patch.old).hexdigest(),
                    "whole": patch.whole,
                    "delta": _b64(bps_create(patch.old, patch.new)),
                }
            )
    return {
        "name": feature.name,
        "glue": glue is not None,
        "any_of": list(any_of),
        "all_of": list(all_of),
        "none_of": list(none_of),
        "caves": caves,
        "code": code,
        "words": words,
        "data": data,
    }


def _glue_variants(
    glue: Glue,
) -> list[tuple[Feature, tuple[str, ...], tuple[str, ...]]]:
    """A glue's pieces: one, or one per mix of its `uses` with the conditions that pick it."""
    if isinstance(glue.feature, Feature):
        return [(glue.feature, glue.all_of, glue.none_of)]
    make: Callable[[frozenset[str]], Feature] = glue.feature
    variants = []
    for bits in itertools.product((False, True), repeat=len(glue.uses)):
        mix = tuple(name for name, on in zip(glue.uses, bits, strict=True) if on)
        rest = tuple(name for name in glue.uses if name not in mix)
        feature = make(frozenset(mix))
        if feature.patches:
            variants.append((feature, glue.all_of + mix, glue.none_of + rest))
    return variants


def build_pack() -> dict:
    pieces = [piece(feature, None, (feature.name,)) for feature in FEATURES]
    for glue in GLUE:
        for feature, all_of, none_of in _glue_variants(glue):
            pieces.append(piece(feature, glue, glue.any_of, all_of, none_of))
    return {
        "version": PACK_VERSION,
        "rom_sha1": ROM_SHA1,
        "order": [feature.name for feature in FEATURES],
        "requires": {name: list(needs) for name, needs in REQUIRES.items()},
        "always": list(ALWAYS),
        "switches": [
            {
                "number": s.number,
                "group": s.group,
                "label": s.label,
                "tooltip": s.tooltip,
                "features": list(s.features),
                "needs": list(s.needs),
                "default": s.default,
                "details": s.details,
            }
            for s in SWITCHES
        ],
        "pieces": pieces,
    }


def write_pack(out: Path = PACK_OUT) -> Path:
    pack = build_pack()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(
        gzip.compress(json.dumps(pack, separators=(",", ":")).encode("utf-8"))
    )
    logger.info(
        "wrote %s: %d pieces, %d bytes", out, len(pack["pieces"]), out.stat().st_size
    )
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.installer_pack")
    parser.add_argument("--out", type=Path, default=PACK_OUT)
    write_pack(parser.parse_args().out)


if __name__ == "__main__":
    main()
