"""Read files out of a CD/UMD image: raw .bin (MODE1/2352, MODE2/2352), plain .iso, or .cso.

Usage:
    python -I discfs.py list  IMAGE
    python -I discfs.py extract IMAGE OUTDIR [GLOB ...]

The image is untrusted data; this only parses ISO9660 structures and writes files under OUTDIR.
"""

from __future__ import annotations

import fnmatch
import logging
import struct
import sys
import zlib
from pathlib import Path

LOG = logging.getLogger("discfs")

SECTOR = 2048
RAW_SECTOR = 2352
SYNC = b"\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00"
MODE1 = 1
MODE2 = 2
PVD_LBA = 16
CSO_MAGIC = b"CISO"
CSO_PLAIN_BIT = 0x80000000
DIR_FLAG = 0x02


class Image:
    """Sector reader giving 2048-byte user data for any supported image type."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.fh = open(path, "rb")
        head = self.fh.read(16)
        self.cso: tuple[int, int, list[int]] | None = None
        self.raw = False
        if head[:4] == CSO_MAGIC:
            _hdr, total, block, _ver, align = struct.unpack(
                "<IQIBB", head[4:22] if len(head) >= 22 else self._reread(22)[4:22]
            )
            nblocks = total // block
            self.fh.seek(24)
            index = list(
                struct.unpack(f"<{nblocks + 1}I", self.fh.read(4 * (nblocks + 1)))
            )
            self.cso = (block, align, index)
        elif head[:12] == SYNC:
            self.raw = True

    def _reread(self, n: int) -> bytes:
        self.fh.seek(0)
        return self.fh.read(n)

    def sector(self, lba: int) -> bytes:
        if self.cso is not None:
            block, align, index = self.cso
            if block != SECTOR:
                raise ValueError(f"unsupported CSO block size {block}")
            a, b = index[lba], index[lba + 1]
            pos = (a & ~CSO_PLAIN_BIT) << align
            end = (b & ~CSO_PLAIN_BIT) << align
            self.fh.seek(pos)
            data = self.fh.read(end - pos)
            if a & CSO_PLAIN_BIT:
                return data[:SECTOR]
            return zlib.decompress(data, -15)[:SECTOR]
        if self.raw:
            self.fh.seek(lba * RAW_SECTOR)
            raw = self.fh.read(RAW_SECTOR)
            mode = raw[15]
            if mode == MODE1:
                return raw[16 : 16 + SECTOR]
            if mode == MODE2:
                return raw[24 : 24 + SECTOR]
            raise ValueError(f"sector {lba}: unknown mode {mode}")
        self.fh.seek(lba * SECTOR)
        return self.fh.read(SECTOR)

    def read(self, lba: int, size: int) -> bytes:
        n = (size + SECTOR - 1) // SECTOR
        return b"".join(self.sector(lba + i) for i in range(n))[:size]


def walk(img: Image) -> list[tuple[str, int, int]]:
    """Return (path, lba, size) for every file in the ISO9660 tree."""
    pvd = img.sector(PVD_LBA)
    if pvd[1:6] != b"CD001":
        raise ValueError("no ISO9660 primary volume descriptor")
    root = pvd[156:190]
    out: list[tuple[str, int, int]] = []
    seen: set[int] = set()

    def recurse(lba: int, size: int, prefix: str) -> None:
        if lba in seen:
            return
        seen.add(lba)
        data = img.read(lba, size)
        pos = 0
        while pos < len(data):
            ln = data[pos]
            if ln == 0:
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            rec = data[pos : pos + ln]
            elba = struct.unpack_from("<I", rec, 2)[0]
            esize = struct.unpack_from("<I", rec, 10)[0]
            flags = rec[25]
            nlen = rec[32]
            name = rec[33 : 33 + nlen]
            pos += ln
            if name in (b"\x00", b"\x01"):
                continue
            sname = name.decode("ascii", "replace").split(";")[0]
            if flags & DIR_FLAG:
                recurse(elba, esize, f"{prefix}{sname}/")
            else:
                out.append((f"{prefix}{sname}", elba, esize))

    recurse(
        struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], ""
    )
    return out


def extract(image: Path, outdir: Path, globs: list[str]) -> int:
    img = Image(image)
    count = 0
    for name, lba, size in walk(img):
        if globs and not any(fnmatch.fnmatch(name.upper(), g.upper()) for g in globs):
            continue
        dst = outdir / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(img.read(lba, size))
        count += 1
    LOG.info("extracted %d files to %s", count, outdir)
    return count


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(argv) < 2:
        sys.stderr.write(__doc__ or "")
        return 2
    cmd, image = argv[0], Path(argv[1])
    if cmd == "list":
        for name, lba, size in walk(Image(image)):
            sys.stdout.write(f"{lba:8d} {size:10d} {name}\n")
        return 0
    if cmd == "extract":
        extract(image, Path(argv[2]), argv[3:])
        return 0
    sys.stderr.write(__doc__ or "")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
