"""BPS patches: build one from the original ROM to a patched ROM, and apply one.

A release ships a patch, never a ROM: players apply it to their own copy of the game. Data that only moved
(files after a grown file shift in the ROM) is encoded as copies from the player's ROM (SourceCopy), so the
patch holds only our own bytes. Format: https://www.romhacking.net/documents/746/ (BPS1).

Usage:
    uv run python -m dsde.bps create <original.nds> <patched.nds> <out.bps>
    uv run python -m dsde.bps apply <original.nds> <patch.bps> <out.nds>
"""

import argparse
import logging
import struct
import zlib
from pathlib import Path

MAGIC = b"BPS1"
SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)
ACTION_BITS = 2
VARINT_BITS = 7
VARINT_LOW = 0x7F
VARINT_END = 0x80
FOOTER = 12  # three CRC32s: source, target, patch
BLOCK = 4096  # chunk for fast equality runs
KEY = 32  # bytes per index key
STRIDE = 64  # source positions indexed: one every STRIDE bytes
MIN_SAME = 8  # shortest same-offset run worth its own action
MIN_COPY = KEY  # shortest moved run worth a copy

logger = logging.getLogger(__name__)


class BpsError(ValueError):
    """Raised when a patch does not fit the file or fails its checksums."""


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        low = value & VARINT_LOW
        value >>= VARINT_BITS
        if value == 0:
            out.append(VARINT_END | low)
            return bytes(out)
        out.append(low)
        value -= 1


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    value, shift = 0, 1
    while True:
        byte = data[pos]
        pos += 1
        value += (byte & VARINT_LOW) * shift
        if byte & VARINT_END:
            return value, pos
        shift <<= VARINT_BITS
        value += shift


def _run(a: bytes, a_at: int, b: bytes, b_at: int) -> int:
    """Length of the run where a[a_at:] equals b[b_at:]."""
    length = 0
    limit = min(len(a) - a_at, len(b) - b_at)
    while length + BLOCK <= limit and (
        a[a_at + length : a_at + length + BLOCK]
        == b[b_at + length : b_at + length + BLOCK]
    ):
        length += BLOCK
    while length < limit and a[a_at + length] == b[b_at + length]:
        length += 1
    return length


def create(source: bytes, target: bytes) -> bytes:
    """Return a BPS patch turning source into target."""
    index: dict[bytes, int] = {}
    for pos in range(0, len(source) - KEY + 1, STRIDE):
        index.setdefault(source[pos : pos + KEY], pos)
    out = bytearray(MAGIC + _varint(len(source)) + _varint(len(target)) + _varint(0))
    literal = bytearray()
    source_rel = 0
    t = 0

    def flush() -> None:
        if literal:
            out.extend(_varint((len(literal) - 1) << ACTION_BITS | TARGET_READ))
            out.extend(literal)
            literal.clear()

    while t < len(target):
        same = _run(source, t, target, t) if t < len(source) else 0
        if same >= MIN_SAME:
            flush()
            out.extend(_varint((same - 1) << ACTION_BITS | SOURCE_READ))
            t += same
            continue
        found = None
        for k in range(min(STRIDE, len(target) - t - KEY + 1)):
            s = index.get(target[t + k : t + k + KEY])
            if s is not None and s >= k and source[s - k : s] == target[t : t + k]:
                found = s - k
                break
        if found is not None:
            length = _run(source, found, target, t)
            if length >= MIN_COPY:
                flush()
                out.extend(_varint((length - 1) << ACTION_BITS | SOURCE_COPY))
                delta = found - source_rel
                out.extend(_varint(abs(delta) << 1 | (delta < 0)))
                source_rel = found + length
                t += length
                continue
        literal.append(target[t])
        t += 1
    flush()
    out.extend(struct.pack("<II", zlib.crc32(source), zlib.crc32(target)))
    out.extend(struct.pack("<I", zlib.crc32(out)))
    return bytes(out)


def apply(source: bytes, patch: bytes) -> bytes:
    """Apply a BPS patch to source and return the target, checking all three CRC32s."""
    if patch[: len(MAGIC)] != MAGIC:
        raise BpsError("not a BPS1 patch")
    source_crc, target_crc, patch_crc = struct.unpack_from(
        "<III", patch, len(patch) - FOOTER
    )
    if zlib.crc32(patch[:-4]) != patch_crc:
        raise BpsError("patch is damaged")
    if zlib.crc32(source) != source_crc:
        raise BpsError("this is not the ROM the patch was made for")
    pos = len(MAGIC)
    source_size, pos = _read_varint(patch, pos)
    target_size, pos = _read_varint(patch, pos)
    meta_size, pos = _read_varint(patch, pos)
    pos += meta_size
    if source_size != len(source):
        raise BpsError("source size does not match")
    target = bytearray()
    source_rel = target_rel = 0
    end = len(patch) - FOOTER
    while pos < end:
        word, pos = _read_varint(patch, pos)
        action, length = word & ((1 << ACTION_BITS) - 1), (word >> ACTION_BITS) + 1
        if action == SOURCE_READ:
            target += source[len(target) : len(target) + length]
        elif action == TARGET_READ:
            target += patch[pos : pos + length]
            pos += length
        else:
            offset, pos = _read_varint(patch, pos)
            delta = -(offset >> 1) if offset & 1 else offset >> 1
            if action == SOURCE_COPY:
                source_rel += delta
                target += source[source_rel : source_rel + length]
                source_rel += length
            else:
                target_rel += delta
                for _ in range(length):
                    target.append(target[target_rel])
                    target_rel += 1
    if len(target) != target_size or zlib.crc32(target) != target_crc:
        raise BpsError("result does not match the patched ROM")
    return bytes(target)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.bps")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, second in (("create", "patched"), ("apply", "patch")):
        cmd = sub.add_parser(name)
        cmd.add_argument("original", type=Path)
        cmd.add_argument(second, type=Path)
        cmd.add_argument("out", type=Path)
    args = parser.parse_args()
    source = args.original.read_bytes()
    if args.command == "create":
        target = args.patched.read_bytes()
        patch = create(source, target)
        if apply(source, patch) != target:
            raise BpsError("round trip failed")
        args.out.write_bytes(patch)
        logger.info("wrote %s (%d bytes), round trip checked", args.out, len(patch))
    else:
        args.out.write_bytes(apply(source, args.patch.read_bytes()))
        logger.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
