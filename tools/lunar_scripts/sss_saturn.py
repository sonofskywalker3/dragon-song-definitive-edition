"""Lunar: Silver Star Story (Saturn, Japan) dialogue dump, both releases, via MrConan1/lsb.

    python -I sss_saturn.py TEXT_SOURCE LSB_EXE LSB_DATA_DIR WORKDIR OUT.txt [--original]
    python -I sss_saturn.py unpack BUNDLE.DAT OUTDIR
    python -I sss_saturn.py sjis AR_BOOK.TXT OUT.txt

TEXT_SOURCE  : the 1996 disc's TEXT/ folder (plain ISO9660 files), or the 1997 MPEG
               ("Complete") disc's TEXT.DAT bundle, which is unpacked first.
LSB_EXE      : lsb with lsb_file_offset.patch and lsb_unmapped_glyph.patch applied.
--original   : the 1996 release. Passes lsb's "sss" flag: its font_table.txt is the MPEG
               release's table, and the 1996 font has one extra glyph at 769.

The Saturn script is lsb's 2-byte mode (ienc 0): each u16 below 0xF000 is an index into
the 16x16 font, mapped to Unicode by lsb's font_table.txt. A code the table lacks is
printed as {XXXX}. AR_BOOK.TXT (the FMV script, Shift-JIS) is converted by "sjis".
"""

from __future__ import annotations

import argparse
import logging
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import write_dump  # noqa: E402
from sssc import TEXT_RE, decode_texts  # noqa: E402

LOG = logging.getLogger("sss_saturn")

SECTOR = 0x800
BUNDLE_ENTRY = 24
NAME_LEN = 12
TWO_BYTE = 0
SSS_FLAG = "sss"
TITLE_ORIGINAL = "Lunar: Silver Star Story (Saturn, Japan, 1996 Rev A)"
TITLE_MPEG = "Lunar: Silver Star Story Complete (Saturn MPEG, Japan, 1997)"


def unpack_bundle(bundle: Path, outdir: Path) -> list[Path]:
    """Unpack a Saturn MPEG-release X.DAT bundle (studio-lucia/lunardata X.DAT.md)."""
    data = bundle.read_bytes()
    header_sectors = struct.unpack_from(">H", data, 14)[0]
    out = []
    outdir.mkdir(parents=True, exist_ok=True)
    for pos in range(0, header_sectors * SECTOR, BUNDLE_ENTRY):
        entry = data[pos : pos + BUNDLE_ENTRY]
        if not entry[0]:
            continue
        name = entry[:NAME_LEN].split(b"\0")[0].decode("ascii")
        start = struct.unpack_from(">H", entry, 14)[0]
        size = struct.unpack_from(">I", entry, 20)[0]
        dst = outdir / Path(name).name
        dst.write_bytes(data[start * SECTOR : start * SECTOR + size])
        out.append(dst)
    LOG.info("unpacked %d files from %s", len(out), bundle.name)
    return out


def run(
    source: Path, lsb: Path, lsb_data: Path, work: Path, out: Path, original: bool
) -> int:
    files = (
        sorted(source.iterdir())
        if source.is_dir()
        else unpack_bundle(source, work / "bundle")
    )
    texts = sorted(p for p in files if TEXT_RE.search(p.name.upper()))
    extra = (SSS_FLAG,) if original else ()
    messages = decode_texts(
        texts, lsb, lsb_data, work / "lsb", TWO_BYTE, extra, encoding="utf-8"
    )
    write_dump(
        out,
        TITLE_ORIGINAL if original else TITLE_MPEG,
        f"sss_saturn.py: lsb decode ienc=0{' sss' if original else ''}",
        messages,
    )
    LOG.info("wrote %d messages to %s", len(messages), out)
    return len(messages)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) > 1 and sys.argv[1] == "unpack":
        unpack_bundle(Path(sys.argv[2]), Path(sys.argv[3]))
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "sjis":
        text = Path(sys.argv[2]).read_bytes().decode("cp932", errors="replace")
        Path(sys.argv[3]).write_text(text.replace("\r\n", "\n"), encoding="utf-8")
        return 0
    ap = argparse.ArgumentParser()
    for a in ("source", "lsb", "lsb_data", "work", "out"):
        ap.add_argument(a, type=Path)
    ap.add_argument("--original", action="store_true")
    a = ap.parse_args()
    run(a.source, a.lsb, a.lsb_data, a.work, a.out, a.original)
    return 0


if __name__ == "__main__":
    sys.exit(main())
