"""The installer's linker: places pre-assembled pieces, fills in their addresses, and patches arm9 and the data.

Pure Python with no dependencies (no Keystone), so the installer can run anywhere. The pieces come from the pack
(dsde.installer_pack), which assembles every feature and glue piece ahead of time and records where each refers
to an address that depends on the layout:

- "b": a branch (b, bl, or a conditional branch) to a cave symbol plus an addend;
- "ba": a branch from cave code to a fixed address (its offset depends on where the cave lands);
- "w": a 32-bit word holding a cave symbol plus an addend;
- "s": a 32-bit word holding an address inside the same cave (the cave's address plus an addend).

Layout, ITCM image, and patch checks follow dsde.patching exactly, so a linked build equals a dsd build.
"""

import base64
import hashlib
import struct
from dataclasses import dataclass, field

from dsde.archive import compress, decompress, read_archive, write_archive
from dsde.bps import apply as bps_apply

ARM9_BASE = 0x02000000
ITCM_BASE = 0x01FF8000
ITCM_CAVE = 0x01FF8300
ITCM_END = 0x02000000
WORD = 4
ARM_PC_AHEAD = 8
BRANCH_OFFSET_MASK = 0x00FFFFFF
BRANCH_SIGN = 0x00800000
BRANCH_RANGE = 1 << 24
BRANCH_OPCODE_MASK = 0x0E000000
BRANCH_OPCODE = 0x0A000000
RELOC_BRANCH = "b"
RELOC_BRANCH_ABSOLUTE = "ba"
RELOC_WORD = "w"
RELOC_SELF = "s"


class LinkError(RuntimeError):
    """Raised when the pack, the choice of features, or the ROM does not fit together."""


@dataclass(frozen=True)
class Reloc:
    offset: int
    kind: str
    target: str | int  # a symbol, or a fixed address for RELOC_BRANCH_ABSOLUTE
    addend: int = 0


@dataclass(frozen=True)
class Cave:
    label: str
    code: bytes
    relocs: tuple[Reloc, ...]


@dataclass(frozen=True)
class Code:
    """Code written over arm9 at a fixed address; first and last are the words it expects there."""

    addr: int
    end: int
    first: int
    last: int
    code: bytes
    relocs: tuple[Reloc, ...]


@dataclass(frozen=True)
class Word:
    addr: int
    old: int
    new: int


@dataclass(frozen=True)
class Data:
    """An edit to one decompressed archive entry: the bytes at offset (old_len of them, or the whole entry) must
    hash to old_sha1; bps_apply(those bytes, delta) is then written at offset, over as many bytes as it holds."""

    archive: str
    entry: int
    offset: int
    old_len: int
    old_sha1: str
    whole: bool
    delta: bytes


@dataclass(frozen=True)
class Piece:
    """One feature, or one glue piece built only for a certain mix of features."""

    name: str
    glue: bool
    any_of: tuple[str, ...]
    all_of: tuple[str, ...] = ()
    none_of: tuple[str, ...] = ()
    caves: tuple[Cave, ...] = ()
    code: tuple[Code, ...] = ()
    words: tuple[Word, ...] = ()
    data: tuple[Data, ...] = ()

    def wanted(self, chosen: frozenset[str]) -> bool:
        return (
            any(name in chosen for name in self.any_of)
            and all(name in chosen for name in self.all_of)
            and not any(name in chosen for name in self.none_of)
        )


@dataclass
class Linked:
    pieces: list[Piece]
    symbols: dict[str, int] = field(default_factory=dict)


def _relocs(raw: list) -> tuple[Reloc, ...]:
    return tuple(Reloc(*item) for item in raw)


def pieces_from_pack(pack: dict) -> list[Piece]:
    """The pieces of a pack (the JSON object installer_pack writes)."""
    pieces = []
    for raw in pack["pieces"]:
        pieces.append(
            Piece(
                name=raw["name"],
                glue=raw["glue"],
                any_of=tuple(raw["any_of"]),
                all_of=tuple(raw["all_of"]),
                none_of=tuple(raw["none_of"]),
                caves=tuple(
                    Cave(c["label"], base64.b64decode(c["code"]), _relocs(c["relocs"]))
                    for c in raw["caves"]
                ),
                code=tuple(
                    Code(
                        c["addr"],
                        c["end"],
                        c["first"],
                        c["last"],
                        base64.b64decode(c["code"]),
                        _relocs(c["relocs"]),
                    )
                    for c in raw["code"]
                ),
                words=tuple(Word(*w) for w in raw["words"]),
                data=tuple(
                    Data(
                        d["archive"],
                        d["entry"],
                        d["offset"],
                        d["old_len"],
                        d["old_sha1"],
                        d["whole"],
                        base64.b64decode(d["delta"]),
                    )
                    for d in raw["data"]
                ),
            )
        )
    return pieces


def choose(pieces: list[Piece], names: list[str]) -> Linked:
    """The features named, in pack order, then the glue their mix calls for (as features.resolve does)."""
    chosen = frozenset(names)
    by_name = {piece.name: piece for piece in pieces if not piece.glue}
    unknown = chosen - by_name.keys()
    if unknown:
        raise LinkError(f"unknown features: {sorted(unknown)}")
    features = [by_name[name] for name in names]
    glue = [p for p in pieces if p.glue and p.wanted(chosen)]
    linked = Linked(features + glue)
    linked.symbols = layout(linked.pieces)
    return linked


def layout(pieces: list[Piece]) -> dict[str, int]:
    """Give every cave an ITCM address, 4-byte aligned, in piece order (patching.layout_cave)."""
    symbols: dict[str, int] = {}
    addr = ITCM_CAVE
    for piece in pieces:
        for cave in piece.caves:
            if cave.label in symbols:
                raise LinkError(f"cave label {cave.label} is used twice")
            symbols[cave.label] = addr
            addr += len(cave.code)
            addr = (addr + WORD - 1) & ~(WORD - 1)
    if addr > ITCM_END:
        raise LinkError(
            f"These changes do not all fit: together they need {addr - ITCM_END} bytes more of the DS's fast "
            "code memory than there is. Switch one or more of the larger ones off (Retold party chat, the card "
            "system, skills, or the bestiary)."
        )
    return symbols


def _branch(word: int, place: int, target: int) -> int:
    distance = target - (place + ARM_PC_AHEAD)
    if distance % WORD or not -BRANCH_RANGE * 2 <= distance < BRANCH_RANGE * 2:
        raise LinkError(f"branch at {place:#x} cannot reach {target:#x}")
    return (word & ~BRANCH_OFFSET_MASK) | ((distance >> 2) & BRANCH_OFFSET_MASK)


def relocate(
    code: bytes, base: int, relocs: tuple[Reloc, ...], symbols: dict[str, int]
) -> bytes:
    """code placed at base, with every address reference filled in."""
    out = bytearray(code)
    for reloc in relocs:
        (word,) = struct.unpack_from("<I", out, reloc.offset)
        place = base + reloc.offset
        if reloc.kind == RELOC_BRANCH:
            if (word & BRANCH_OPCODE_MASK) != BRANCH_OPCODE:
                raise LinkError(f"no branch at {place:#x}")
            word = _branch(word, place, symbols[reloc.target] + reloc.addend)
        elif reloc.kind == RELOC_BRANCH_ABSOLUTE:
            word = _branch(word, place, int(reloc.target))
        elif reloc.kind == RELOC_WORD:
            word = (symbols[reloc.target] + reloc.addend) & 0xFFFFFFFF
        elif reloc.kind == RELOC_SELF:
            word = (base + reloc.addend) & 0xFFFFFFFF
        else:
            raise LinkError(f"unknown relocation {reloc.kind}")
        struct.pack_into("<I", out, reloc.offset, word)
    return bytes(out)


def _check_word(arm9: bytearray, name: str, addr: int, expected: int) -> None:
    (current,) = struct.unpack_from("<I", arm9, addr - ARM9_BASE)
    if current != expected:
        raise LinkError(
            f"{name} @ {addr:#010x}: expected {expected:#010x}, found {current:#010x}"
        )


def patch_arm9(arm9: bytearray, linked: Linked) -> None:
    """Apply every piece's code and word patches, in order (patching.apply_arm9)."""
    for piece in linked.pieces:
        for code in piece.code:
            _check_word(arm9, piece.name, code.addr, code.first)
            _check_word(arm9, piece.name, code.end - WORD, code.last)
            placed = relocate(code.code, code.addr, code.relocs, linked.symbols)
            if len(placed) > code.end - code.addr:
                raise LinkError(f"{piece.name}: code at {code.addr:#x} does not fit")
            at = code.addr - ARM9_BASE
            arm9[at : at + len(placed)] = placed
        for word in piece.words:
            _check_word(arm9, piece.name, word.addr, word.old)
            struct.pack_into("<I", arm9, word.addr - ARM9_BASE, word.new)


def build_itcm(itcm: bytes, linked: Linked) -> bytes:
    """itcm.bin with every cave placed at its address (patching.build_itcm)."""
    caves = [cave for piece in linked.pieces for cave in piece.caves]
    if not caves:
        return itcm
    image = bytearray(itcm) + bytearray(ITCM_CAVE - ITCM_BASE - len(itcm))
    for cave in caves:
        addr = linked.symbols[cave.label]
        code = relocate(cave.code, addr, cave.relocs, linked.symbols)
        offset = addr - ITCM_BASE
        image += bytearray(offset - len(image))
        image[offset : offset + len(code)] = code
    return bytes(image + bytearray(-len(image) % WORD))


def patch_archives(files: dict[str, bytes], linked: Linked) -> dict[str, bytes]:
    """The archives the pieces edit, rebuilt (patching.apply_data); files maps an archive name to its bytes."""
    edits: dict[str, list[tuple[str, Data]]] = {}
    for piece in linked.pieces:
        for data in piece.data:
            edits.setdefault(data.archive, []).append((piece.name, data))
    rebuilt = {}
    for archive, patches in edits.items():
        entries = read_archive(files[archive])
        decoded: dict[int, bytearray] = {}
        for name, data in patches:
            current = decoded.setdefault(
                data.entry, bytearray(decompress(entries[data.entry]))
            )
            old_end = len(current) if data.whole else data.offset + data.old_len
            old = bytes(current[data.offset : old_end])
            if hashlib.sha1(old).hexdigest() != data.old_sha1:
                raise LinkError(
                    f"{name} {archive}/{data.entry:03d}+{data.offset:#x}: not the expected bytes"
                )
            new = bps_apply(old, data.delta)
            # As patching.apply_data: the new bytes are written over as many bytes as they hold (the rest of a
            # whole entry is cut), so a longer edit overwrites what follows the old bytes.
            end = len(current) if data.whole else data.offset + len(new)
            current[data.offset : end] = new
        for index, data in decoded.items():
            entries[index] = compress(bytes(data))
        rebuilt[archive] = write_archive(entries)
    return rebuilt
