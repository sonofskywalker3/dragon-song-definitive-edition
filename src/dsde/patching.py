"""Patch types and the code that applies them to arm9.bin and the .dat archives.

Every patch states the bytes it expects to replace, so a patch applied to the wrong
build or the wrong address fails loudly instead of corrupting the game.
"""

import logging
import string
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

from dsde.archive import compress_stored, decompress, read_archive, write_archive

ARM9_BASE = 0x02000000
ARM_NOP = 0xE1A00000
# New code goes in ITCM after the game's own 0x2E0 bytes. The game sets up an ITCM arena there
# but never allocates from it (only arena 0 is used, see func_02004c18 callers).
ITCM_BASE = 0x01FF8000
ITCM_CAVE = 0x01FF8300
ITCM_END = 0x02000000
LAYOUT_PLACEHOLDER = ITCM_CAVE

logger = logging.getLogger(__name__)


class PatchError(RuntimeError):
    """Raised when the bytes at a patch site are not what the patch expects."""


@dataclass(frozen=True)
class Patch:
    """Replace one 32-bit ARM instruction in arm9.bin."""

    addr: int
    old: int
    new: int
    note: str


@dataclass(frozen=True)
class AsmPatch:
    """Overwrite the dead code block addr..end (exclusive) with new ARM code.

    first and last are the original words at addr and end - 4, checked before writing.
    """

    addr: int
    end: int
    first: int
    last: int
    asm: str
    note: str


@dataclass(frozen=True)
class DataPatch:
    """Replace bytes inside one decompressed entry of a .dat archive."""

    archive: str
    entry: int
    offset: int
    old: bytes
    new: bytes
    note: str


@dataclass(frozen=True)
class CaveCode:
    """New ARM code placed in ITCM. Other asm refers to it as ${label}."""

    label: str
    asm: str
    note: str


@dataclass(frozen=True)
class Feature:
    """A named group of patches that together make one design change."""

    name: str
    patches: tuple[Patch | AsmPatch | DataPatch | CaveCode, ...]


def _caves(features: list[Feature]) -> list[CaveCode]:
    return [p for f in features for p in f.patches if isinstance(p, CaveCode)]


def substitute(asm: str, symbols: dict[str, int]) -> str:
    """Replace ${label} references to cave code with addresses."""
    return string.Template(asm).substitute({k: f"{v:#x}" for k, v in symbols.items()})


def layout_cave(features: list[Feature]) -> dict[str, int]:
    """Give every CaveCode block an ITCM address (4-byte aligned, in feature order)."""
    caves = _caves(features)
    placeholder = {c.label: LAYOUT_PLACEHOLDER for c in caves}
    symbols: dict[str, int] = {}
    addr = ITCM_CAVE
    for cave in caves:
        symbols[cave.label] = addr
        addr += len(assemble(substitute(cave.asm, placeholder), addr))
        addr = (addr + 3) & ~3
    if addr > ITCM_END:
        raise PatchError(f"cave code overflows ITCM by {addr - ITCM_END} bytes")
    return symbols


def build_itcm(itcm: bytes, features: list[Feature], symbols: dict[str, int]) -> bytes:
    """Return itcm.bin with every CaveCode block assembled at its address."""
    caves = _caves(features)
    if not caves:
        return itcm
    image = bytearray(itcm) + bytearray(ITCM_CAVE - ITCM_BASE - len(itcm))
    for cave in caves:
        addr = symbols[cave.label]
        code = assemble(substitute(cave.asm, symbols), addr)
        offset = addr - ITCM_BASE
        image += bytearray(offset - len(image))
        image[offset : offset + len(code)] = code
        logger.info(
            "cave %s @ %#010x: %s (%d bytes)", cave.label, addr, cave.note, len(code)
        )
    return bytes(image + bytearray(-len(image) % 4))


def assemble(asm: str, addr: int) -> bytes:
    """Assemble ARM code for the given load address."""
    encoding, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(asm, addr)
    return bytes(encoding)


def _check_word(arm9: bytearray, feature: Feature, addr: int, expected: int) -> None:
    (current,) = struct.unpack_from("<I", arm9, addr - ARM9_BASE)
    if current != expected:
        raise PatchError(
            f"{feature.name} @ {addr:#010x}: expected {expected:#010x}, found {current:#010x}"
        )


def apply_arm9(arm9: bytearray, feature: Feature, symbols: dict[str, int]) -> None:
    """Apply the code patches of a feature to an arm9.bin image in place."""
    for patch in feature.patches:
        if isinstance(patch, AsmPatch):
            _check_word(arm9, feature, patch.addr, patch.first)
            _check_word(arm9, feature, patch.end - 4, patch.last)
            code = assemble(substitute(patch.asm, symbols), patch.addr)
            if len(code) > patch.end - patch.addr:
                raise PatchError(
                    f"{feature.name}: {len(code)} bytes do not fit in {patch.end - patch.addr}"
                )
            arm9[patch.addr - ARM9_BASE : patch.addr - ARM9_BASE + len(code)] = code
            logger.info(
                "%s @ %#010x: %s (%d bytes)",
                feature.name,
                patch.addr,
                patch.note,
                len(code),
            )
        elif isinstance(patch, Patch):
            _check_word(arm9, feature, patch.addr, patch.old)
            struct.pack_into("<I", arm9, patch.addr - ARM9_BASE, patch.new)
            logger.info("%s @ %#010x: %s", feature.name, patch.addr, patch.note)


def apply_data(files_dir: Path, features: list[Feature]) -> None:
    """Apply the archive patches of all features, rewriting each touched archive once."""
    by_archive: dict[str, list[tuple[Feature, DataPatch]]] = defaultdict(list)
    for feature in features:
        for patch in feature.patches:
            if isinstance(patch, DataPatch):
                by_archive[patch.archive].append((feature, patch))
    for archive, patches in by_archive.items():
        path = files_dir / f"{archive}.dat"
        entries = read_archive(path.read_bytes())
        decoded: dict[int, bytearray] = {}
        for feature, patch in patches:
            data = decoded.setdefault(
                patch.entry, bytearray(decompress(entries[patch.entry]))
            )
            current = bytes(data[patch.offset : patch.offset + len(patch.old)])
            if current != patch.old:
                raise PatchError(
                    f"{feature.name} {archive}/{patch.entry:03d}+{patch.offset:#x}: "
                    f"expected {patch.old.hex()}, found {current.hex()}"
                )
            data[patch.offset : patch.offset + len(patch.new)] = patch.new
            logger.info(
                "%s %s/%03d+%#x: %s",
                feature.name,
                archive,
                patch.entry,
                patch.offset,
                patch.note,
            )
        for index, data in decoded.items():
            entries[index] = compress_stored(bytes(data))
        path.write_bytes(write_archive(entries))
