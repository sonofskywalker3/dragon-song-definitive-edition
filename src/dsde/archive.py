"""Reader and writer for the game's .dat archives and their CMDS-compressed entries.

Archive layout (all little-endian):
    u32 count
    u32 offsets[count + 1]   in units of BLOCK_SIZE bytes; entry i spans offsets[i]..offsets[i + 1]
    entries, each starting on a BLOCK_SIZE boundary

Entry layout (decoded by the game at 0x0201a404):
    "CMDS"
    u32 decompressed size
    u32 length of the token stream (the flag bits start right after it)
    token stream: literal bytes and u16 back-references
    flag bits: one per token, LSB first; 0 = literal byte, 1 = back-reference
Back-reference u16: length = (v >> 12) + 3, distance = (v & 0xfff) + 1.
"""

import struct
from pathlib import Path

BLOCK_SIZE = 0x20
MAGIC = b"CMDS"
HEADER_SIZE = 12
LENGTH_SHIFT = 12
MIN_MATCH = 3
DISTANCE_MASK = 0xFFF


class ArchiveError(ValueError):
    """Raised when an archive or entry does not match the expected format."""


def read_archive(data: bytes) -> list[bytes]:
    """Split an archive into its raw (still compressed) entries."""
    (count,) = struct.unpack_from("<I", data, 0)
    offsets = struct.unpack_from(f"<{count + 1}I", data, 4)
    return [
        data[offsets[i] * BLOCK_SIZE : offsets[i + 1] * BLOCK_SIZE]
        for i in range(count)
    ]


def write_archive(entries: list[bytes]) -> bytes:
    """Build an archive from raw entries, padding each to a block boundary."""
    table_size = 4 + 4 * (len(entries) + 1)
    first = _align(table_size, 0x800) // BLOCK_SIZE
    offsets = [first]
    body = bytearray()
    for entry in entries:
        body += entry + b"\0" * (_align(len(entry), BLOCK_SIZE) - len(entry))
        offsets.append(first + len(body) // BLOCK_SIZE)
    header = struct.pack(f"<I{len(offsets)}I", len(entries), *offsets)
    return header + b"\0" * (first * BLOCK_SIZE - len(header)) + bytes(body)


def decompress(entry: bytes) -> bytes:
    """Decompress one CMDS entry."""
    if entry[:4] != MAGIC:
        raise ArchiveError(f"bad magic {entry[:4]!r}")
    size, stream_len = struct.unpack_from("<II", entry, 4)
    stream = entry[HEADER_SIZE : HEADER_SIZE + stream_len]
    flags = entry[HEADER_SIZE + stream_len :]
    out = bytearray()
    pos = 0
    token = 0
    while len(out) < size:
        if flags[token >> 3] & (1 << (token & 7)):
            (value,) = struct.unpack_from("<H", stream, pos)
            pos += 2
            distance = (value & DISTANCE_MASK) + 1
            for _ in range((value >> LENGTH_SHIFT) + MIN_MATCH):
                out.append(out[-distance])
        else:
            out.append(stream[pos])
            pos += 1
        token += 1
    return bytes(out[:size])


def compress_stored(data: bytes) -> bytes:
    """Encode data as a CMDS entry using literals only. Valid for the game, just not smaller."""
    flags = bytes(_align(len(data), 8) // 8)
    return MAGIC + struct.pack("<II", len(data), len(data)) + data + flags


def unpack_all(extract_files: Path, out_dir: Path) -> None:
    """Decompress every entry of every archive into out_dir/<archive>/<index>.bin."""
    for archive in sorted(extract_files.glob("*.dat")):
        target = out_dir / archive.stem
        target.mkdir(parents=True, exist_ok=True)
        for index, entry in enumerate(read_archive(archive.read_bytes())):
            (target / f"{index:03d}.bin").write_bytes(decompress(entry))


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment
