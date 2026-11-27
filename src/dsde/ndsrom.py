"""Reads and rebuilds a Nintendo DS ROM: the parts the installer changes (arm9, its ITCM, and files).

Pure Python with no dependencies. Written for Lunar: Dragon Song (USA) and checked against it: an uncompressed
arm9 with two autoloads (ITCM, then DTCM), no overlays, and every file in the root directory.

The rebuilt ROM keeps the original's order and alignment: the header, arm9 (static code, then the autoloads and
their list, then the 12-byte footer), arm7, the file name table, the file allocation table, the banner, and the
files in the original's order, each on a 0x200 boundary (zeros between the parts up to the banner, 0xFF after it
and up to the original size). Read and written back unchanged, the original comes out byte for byte.

The secure area checksum (header 0x6C) covers ROM 0x4000..0x7FFF with its first 0x800 bytes encrypted, which this
dump stores decrypted. Only bytes past the encrypted part may change (the autoload list's address in the module
params, arm9 + 0xB00, does), and CRC-16 is linear, so the new checksum is the old one combined with the checksum
of the change: no key is needed. The header's own checksum is then recomputed.
"""

import struct
from dataclasses import dataclass, field

HEADER_SIZE = 0x4000
ALIGN = 0x200
GAP = 0x00  # between the parts up to the banner
FILE_GAP = (
    0xFF  # after the banner: between the files, and after them up to the ROM's size
)
ARM9_OFFSET = 0x20
ARM9_RAM = 0x28
ARM9_SIZE = 0x2C
ARM7_OFFSET = 0x30
ARM7_SIZE = 0x3C
FNT_OFFSET = 0x40
FNT_SIZE = 0x44
FAT_OFFSET = 0x48
FAT_SIZE = 0x4C
OVERLAY9_SIZE = 0x54
OVERLAY7_SIZE = 0x5C
BANNER_OFFSET = 0x68
USED_SIZE = 0x80
HEADER_CRC = 0x15E
SECURE_AREA = 0x4000  # ROM 0x4000..0x7FFF, covered by the checksum at SECURE_CRC
SECURE_AREA_END = 0x8000
ENCRYPTED_END = 0x4800  # the encrypted part, which must never change
SECURE_CRC = 0x6C
BANNER_SIZE = 0x840  # banner version 1
FOOTER_SIZE = 12
FOOTER_MAGIC = 0xDEC00621
AUTOLOAD_ENTRY = 12  # ram address, size, bss size
MODULE_PARAMS_AUTOLOAD_LIST = (
    0  # module params: list start, list end, autoload data start (RAM addresses)
)
MODULE_PARAMS_LIST_END = 4
MODULE_PARAMS_AUTOLOAD_START = 8
FILE_ENTRY = 8


class RomError(ValueError):
    """Raised when a ROM is not laid out the way this module expects."""


def crc16(data: bytes) -> int:
    """The DS header checksum (CRC-16/MODBUS)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _align(value: int) -> int:
    return (value + ALIGN - 1) & ~(ALIGN - 1)


@dataclass
class Rom:
    header: bytearray
    arm9: bytes  # static code: up to the first autoload's data
    autoloads: list[tuple[int, bytes, int]]  # (ram address, data, bss size), ITCM first
    footer: bytes
    module_params: int  # offset of the module params in arm9
    arm7: bytes
    fnt: bytes
    banner: bytes
    files: list[bytes]
    names: dict[str, int] = field(default_factory=dict)  # root file name -> file id
    order: list[int] = field(default_factory=list)  # file ids in stored order
    size: int = 0
    secure_area: bytes = b""  # ROM 0x4000..0x7FFF as read


def _u32(data: bytes, at: int) -> int:
    return struct.unpack_from("<I", data, at)[0]


def _root_names(fnt: bytes) -> dict[str, int]:
    """File name -> id for the files in the root directory (sub-directories are not read)."""
    sub_table = _u32(fnt, 0)
    first_id = struct.unpack_from("<H", fnt, 4)[0]
    names = {}
    at, file_id = sub_table, first_id
    while True:
        kind = fnt[at]
        if kind == 0:
            return names
        length = kind & 0x7F
        name = fnt[at + 1 : at + 1 + length].decode("ascii")
        at += 1 + length
        if kind & 0x80:
            at += 2  # a sub-directory's id; its files are not needed here
            continue
        names[name] = file_id
        file_id += 1


def read_rom(data: bytes) -> Rom:
    header = bytearray(data[:HEADER_SIZE])
    if _u32(header, OVERLAY9_SIZE) or _u32(header, OVERLAY7_SIZE):
        raise RomError("overlays are not supported")
    arm9_at, arm9_size = _u32(header, ARM9_OFFSET), _u32(header, ARM9_SIZE)
    ram = _u32(header, ARM9_RAM)
    full = data[arm9_at : arm9_at + arm9_size]
    footer = data[arm9_at + arm9_size : arm9_at + arm9_size + FOOTER_SIZE]
    if _u32(footer, 0) != FOOTER_MAGIC:
        raise RomError("no arm9 footer")
    params = _u32(footer, 4)
    list_start = _u32(full, params + MODULE_PARAMS_AUTOLOAD_LIST) - ram
    list_end = _u32(full, params + MODULE_PARAMS_LIST_END) - ram
    data_start = _u32(full, params + MODULE_PARAMS_AUTOLOAD_START) - ram
    if list_end != arm9_size:
        raise RomError("the autoload list does not end arm9")
    autoloads = []
    at = data_start
    for entry in range(list_start, list_end, AUTOLOAD_ENTRY):
        address, size, bss = struct.unpack_from("<III", full, entry)
        autoloads.append((address, full[at : at + size], bss))
        at += size
    if at != list_start:
        raise RomError("the autoloads do not fill arm9 up to their list")
    fat_at, fat_size = _u32(header, FAT_OFFSET), _u32(header, FAT_SIZE)
    files, starts = [], []
    for i in range(fat_size // FILE_ENTRY):
        start, end = struct.unpack_from("<II", data, fat_at + i * FILE_ENTRY)
        files.append(data[start:end])
        starts.append(start)
    fnt = data[
        _u32(header, FNT_OFFSET) : _u32(header, FNT_OFFSET) + _u32(header, FNT_SIZE)
    ]
    rom = Rom(
        header=header,
        arm9=full[:data_start],
        autoloads=autoloads,
        footer=footer,
        module_params=params,
        arm7=data[
            _u32(header, ARM7_OFFSET) : _u32(header, ARM7_OFFSET)
            + _u32(header, ARM7_SIZE)
        ],
        fnt=fnt,
        banner=data[
            _u32(header, BANNER_OFFSET) : _u32(header, BANNER_OFFSET) + BANNER_SIZE
        ],
        files=files,
        size=len(data),
        secure_area=data[SECURE_AREA:SECURE_AREA_END],
    )
    rom.names = _root_names(fnt)
    rom.order = sorted(range(len(files)), key=starts.__getitem__)
    return rom


def file(rom: Rom, name: str) -> bytes:
    return rom.files[rom.names[name]]


def set_file(rom: Rom, name: str, data: bytes) -> None:
    rom.files[rom.names[name]] = data


def write_rom(rom: Rom) -> bytes:
    """The ROM with its current parts, laid out as the original is."""
    header = bytearray(rom.header)
    ram = _u32(header, ARM9_RAM)
    arm9 = bytearray(rom.arm9)
    for _, data, _ in rom.autoloads:
        arm9 += data
    list_start = len(arm9)
    for address, data, bss in rom.autoloads:
        arm9 += struct.pack("<III", address, len(data), bss)
    struct.pack_into(
        "<I", arm9, rom.module_params + MODULE_PARAMS_AUTOLOAD_LIST, ram + list_start
    )
    struct.pack_into(
        "<I", arm9, rom.module_params + MODULE_PARAMS_LIST_END, ram + len(arm9)
    )
    out = bytearray(header)
    arm9_at = _u32(header, ARM9_OFFSET)
    out += bytes([GAP]) * (arm9_at - len(out))
    out += arm9 + rom.footer
    struct.pack_into("<I", header, ARM9_SIZE, len(arm9))

    def place(blob: bytes, gap: int = GAP) -> int:
        at = _align(len(out))
        out.extend(bytes([gap]) * (at - len(out)))
        out.extend(blob)
        return at

    struct.pack_into("<I", header, ARM7_OFFSET, place(rom.arm7))
    struct.pack_into("<I", header, FNT_OFFSET, place(rom.fnt))
    fat_at = place(bytes(FILE_ENTRY * len(rom.files)))
    struct.pack_into("<I", header, FAT_OFFSET, fat_at)
    struct.pack_into("<I", header, BANNER_OFFSET, place(rom.banner))
    for i in rom.order:
        start = place(rom.files[i], FILE_GAP)
        end = start + len(rom.files[i])
        struct.pack_into("<II", out, fat_at + i * FILE_ENTRY, start, end)
    struct.pack_into("<I", header, USED_SIZE, len(out))
    if len(out) > rom.size:
        raise RomError(f"the ROM grew past {rom.size:#x} bytes")
    out.extend(bytes([FILE_GAP]) * (rom.size - len(out)))
    area = bytes(out[SECURE_AREA:SECURE_AREA_END])
    change = bytes(a ^ b for a, b in zip(area, rom.secure_area, strict=True))
    if any(change[: ENCRYPTED_END - SECURE_AREA]):
        raise RomError("the encrypted part of the secure area changed")
    (crc,) = struct.unpack_from("<H", header, SECURE_CRC)
    crc ^= crc16(change) ^ crc16(bytes(len(change)))
    struct.pack_into("<H", header, SECURE_CRC, crc)
    struct.pack_into("<H", header, HEADER_CRC, crc16(header[:HEADER_CRC]))
    out[: len(header)] = header
    return bytes(out)
