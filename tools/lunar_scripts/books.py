"""Fetch openly hosted Lunar manuals, guides, and art books, and OCR them.

Everything lands in the gitignored lunar_scripts/books/<item>/ folder, one folder per
item, with a SOURCE.txt. Downloads are untrusted data: this script only reads them
(images, PDFs, zip/rar archives via 7-Zip) and never executes anything from them.

    uv run --with pymupdf --with pillow python -I tools/lunar_scripts/books.py fetch [item ...]
    uv run --with pymupdf --with pillow python -I tools/lunar_scripts/books.py pages [item ...]
    uv run --with pymupdf --with pillow python -I tools/lunar_scripts/books.py ocr [item ...]

`pages` renders every page (PDF pages at OCR_DPI, archive images as they are) to
<item>/pages/NNNN.png; `ocr` runs Tesseract over them and writes <item>/text.txt with
"=== page NNNN (<source name>) ===" markers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "lunar_scripts" / "books"
TESSDATA = ROOT / "lunar_scripts" / "bin" / "tessdata"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
SEVEN_ZIP = Path(r"C:\Program Files\7-Zip\7z.exe")
IA_DOWNLOAD = "https://archive.org/download/"
IA_DETAILS = "https://archive.org/details/"
OCR_DPI = 300
IMAGE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
)
ARCHIVE_SUFFIXES = frozenset({".zip", ".cbz", ".cbr", ".rar", ".7z"})
MAX_PIXELS = 24_000_000  # downscale huge scans before OCR
MAX_SOURCE_PIXELS = 400_000_000  # Pillow bomb guard, raised for 600 dpi scans
POINTS_PER_INCH = 72
MIN_TEXT_LAYER = 40  # a PDF page with this much embedded text is not OCRed
OCR_WORKERS = 6
CHUNK = 1 << 20
HTTP_PREFIX = "https://"
UA_HEADERS = {"User-Agent": "Mozilla/5.0 (research fetch; lunar books)"}
FETCH_TRIES = 5
FETCH_BACKOFF_S = 10
# Tesseract jpn puts a space between every Japanese token; drop spaces between CJK chars.
CJK = r"[　-ヿ㐀-鿿＀-￯]"
CJK_SPACE_RE = re.compile(rf"(?<={CJK}) +(?={CJK})")

log = logging.getLogger("books")


@dataclass(frozen=True)
class Item:
    folder: str
    ia_id: str
    files: tuple[str, ...]
    lang: str  # tesseract language string
    note: str


ITEMS: tuple[Item, ...] = (
    Item(
        "mcd_tss_jp_manual",
        "lunar-the-silver-star-t-45014-mcd-jp-manual-600-dpi",
        (
            "Lunar - The Silver Star [T-45014](MCD)(JP) -Manual(600DPI).pdf",
            "Lunar - The Silver Star [T-45014](MCD)(JP) -BoxBack(600DPI).png",
        ),
        "jpn+eng",
        "LUNAR ザ・シルバースター, Mega-CD, Game Arts, 1992-06-26, T-45014: manual and box back.",
    ),
    Item(
        "mcd_eb_jp_manual",
        "lunar-eternal-blue-t-45074-mcd-jp-manual-600-dpi",
        (
            "Lunar - Eternal Blue [T-45074](MCD)(JP) -Manual(600DPI).pdf",
            "Lunar - Eternal Blue [T-45074](MCD)(JP) -Map(600DPI).pdf",
            "Lunar - Eternal Blue [T-45074](MCD)(JP) -BoxBack(600DPI).png",
        ),
        "jpn+eng",
        "LUNAR エターナルブルー, Mega-CD, Game Arts, 1994-12-22, T-45074: manual, map sheet, box back.",
    ),
    Item(
        "saturn_sss_jp_manual",
        "Lunar_Silver_Star_Story_1996_J_color",
        ("Lunar_Silver_Star_Story_1996_J_color.cbr",),
        "jpn+eng",
        "LUNAR シルバースターストーリー, Sega Saturn, Kadokawa Shoten, 1996: manual.",
    ),
    Item(
        "saturn_sss_jp_extra_card",
        "Lunar_Silver_Star_Story_Extra_Card_1996_J_color",
        ("Lunar_Silver_Star_Story_Extra_Card_1996_J_color.cbr",),
        "jpn+eng",
        "LUNAR シルバースターストーリー, Sega Saturn, 1996: extra card insert.",
    ),
    Item(
        "saturn_l2eb_jp_manual",
        "Lunar_2_Eternal_Blue_1998_J_color",
        ("Lunar_2_Eternal_Blue_1998_J_color.cbr",),
        "jpn+eng",
        "LUNAR2 エターナルブルー, Sega Saturn, Kadokawa Shoten, 1998: manual.",
    ),
    Item(
        "saturn_l2eb_jp_poster",
        "Lunar_2_Eternal_Blue_Poster_1998_J_color",
        ("Lunar_2_Eternal_Blue_Poster_1998_J_color.cbr",),
        "jpn+eng",
        "LUNAR2 エターナルブルー, Sega Saturn, 1998: poster insert.",
    ),
    Item(
        "saturn_mgl_jp_manual",
        "Mahou_Gakuen_Lunar_1997_J_color",
        ("Mahou_Gakuen_Lunar_1997_J_color.cbr",),
        "jpn+eng",
        "魔法学園LUNAR!, Sega Saturn, ESP, 1997: manual.",
    ),
    Item(
        "saturn_sssc_jp_scans",
        "sega-sarturn-lunar-silver-star-story-complate",
        tuple(f"Page{n}.jpg" for n in range(392, 410)),
        "jpn+eng",
        "LUNAR シルバースターストーリー MPEG版 (Saturn, Kadokawa, 1997, T-27904G): manual scans "
        "(uploader titled them Silver Star Story Complete, files Page392-409).",
    ),
    Item(
        "jp_world_guide_vol1",
        "lunarworldguide",
        ("lunarworldguide_images.zip",),
        "jpn+eng",
        "LUNAR ザ・シルバースター ワールドガイド Vol.1 (Japanese), scanned book images.",
    ),
    Item(
        "jp_artbook_1995",
        "lunariiithesilverstareternalblue",
        ("LunarI-ii-TheSilverStarEternalBlue1995.pdf",),
        "jpn+eng",
        "'Lunar I & II: The Silver Star & Eternal Blue' art book (1995 per file name), Japanese.",
    ),
    Item(
        "ps1_sssc_us_manual",
        "img-20221007-0007",
        (),  # file list read from the item metadata
        "eng",
        "Lunar: Silver Star Story Complete (PS1, Working Designs, 1999): box, hardcover manual, disc scans.",
    ),
    Item(
        "ps1_l2ebc_us_manual",
        "img-20221009-0007",
        (),  # file list read from the item metadata (names mix two scan dates)
        "eng",
        "Lunar 2: Eternal Blue Complete (PS1, Working Designs, 2000): box, hardcover manual, disc scans.",
    ),
    Item(
        "segacd_tss_us_guide",
        "lunari-thesilverstar-theofficialguide",
        ("lunari-thesilverstar-theofficialguide.pdf",),
        "eng",
        "Lunar: The Silver Star, The Official Guide (Sega CD, Working Designs, 1993/1994).",
    ),
    Item(
        "ps1_sssc_wd_guide",
        "LunarSilverStarStoryCompleteWorkingDesignsOfficialGuide",
        ("Lunar - Silver Star Story Complete Working Designs Official Guide.pdf",),
        "eng",
        "Lunar: Silver Star Story Complete Official Strategy Guide (Working Designs, 1999).",
    ),
    Item(
        "ps1_l2ebc_wd_guide",
        "lunar-2-eternal-blue-working-designs-strategy-guide_202603",
        ("Lunar 2 Eternal Blue Working Designs Strategy Guide.pdf",),
        "eng",
        "Lunar 2: Eternal Blue Complete Official Strategy Guide (Working Designs, 2000).",
    ),
    Item(
        "psp_harmony_prima_guide",
        "lunar-silver-star-harmony-prima-strategy-guide",
        ("Lunar Silver Star Harmony Prima Strategy Guide.pdf",),
        "eng",
        "Lunar: Silver Star Harmony, Prima Official Game Guide (2010).",
    ),
    Item(
        "gba_legend_jp_manual",
        "lunar-legend-gba-jpn-manual",
        ("3.5 Manual Scan.pdf",),
        "jpn+eng",
        "ルナ レジェンド (GBA, Media Rings, 2002), AGB-ALNJ-JPN: manual.",
    ),
    Item(
        "gba_legend_jp_guide",
        "LunarLegendGBAJapanGuide",
        ("Lunar Legend (GBA Japan Guide).pdf",),
        "jpn+eng",
        "ルナ レジェンド Japanese strategy guide (2002).",
    ),
    Item(
        "segacd_tss_us_manual",
        "SEGACDManuals",
        ("Lunar - The Silver Star (USA).pdf",),
        "eng",
        "Lunar: The Silver Star (Sega CD, Working Designs, 1993): US instruction manual.",
    ),
    Item(
        "segacd_eb_us_manual",
        "",
        (
            "https://www.gamesdatabase.org/Media/SYSTEM/Sega_CD//Manual/formated/"
            "Lunar_-_Eternal_Blue_-_1994_-_Working_Designs.pdf",
        ),
        "eng",
        "Lunar: Eternal Blue (Sega CD, Working Designs, 1995): US instruction manual "
        "(gamesdatabase.org copy; archive.org's SEGACDManuals copy is the Silver Star manual).",
    ),
    Item(
        "psp_harmony_us_manual",
        "psp_rpg_manuals",
        ("Lunar - Silver Star Harmony.pdf",),
        "eng",
        "Lunar: Silver Star Harmony (PSP, XSEED, 2010): US instruction manual.",
    ),
)
BY_FOLDER = {i.folder: i for i in ITEMS}


def ia_files(item: Item) -> tuple[str, ...]:
    if item.files:
        return item.files
    import json

    with urllib.request.urlopen(
        f"https://archive.org/metadata/{item.ia_id}", timeout=60
    ) as r:
        meta = json.load(r)
    return tuple(
        f["name"]
        for f in meta["files"]
        if f.get("source") == "original"
        and Path(f["name"]).suffix.lower() in IMAGE_SUFFIXES
        and not f["name"].startswith("__")
    )


def fetch(item: Item) -> None:
    dest = BOOKS / item.folder / "download"
    dest.mkdir(parents=True, exist_ok=True)
    names = ia_files(item)
    for name in names:
        out = dest / urllib.parse.unquote(Path(name).name)
        if out.exists() and out.stat().st_size > 0:
            continue
        if name.startswith(HTTP_PREFIX):  # a direct link off the Internet Archive
            url = name
        else:
            url = IA_DOWNLOAD + item.ia_id + "/" + urllib.parse.quote(name)
        log.info("GET %s", url)
        tmp = out.with_suffix(out.suffix + ".part")
        for attempt in range(1, FETCH_TRIES + 1):
            try:
                with (
                    urllib.request.urlopen(
                        urllib.request.Request(url, headers=UA_HEADERS), timeout=120
                    ) as r,
                    tmp.open("wb") as fh,
                ):
                    shutil.copyfileobj(r, fh, CHUNK)
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                log.warning("%s: attempt %d failed: %s", name, attempt, exc)
                if attempt == FETCH_TRIES:
                    raise
                time.sleep(FETCH_BACKOFF_S * attempt)
        tmp.replace(out)
    src = BOOKS / item.folder / "SOURCE.txt"
    src.write_text(
        f"Item: {item.note}\n"
        f"Source: {IA_DETAILS}{item.ia_id}\n"
        f"Files: {', '.join(names) if len(names) < 6 else f'{len(names)} files'}\n"
        f"Fetched: {dt.date.today().isoformat()} by tools/lunar_scripts/books.py\n"
        "License/notes: hosted openly on the Internet Archive by its uploader; copyrighted "
        "printed matter (publisher named above), kept local for private research only.\n",
        encoding="utf-8",
    )


def render_pages(item: Item) -> None:
    import fitz  # pymupdf
    from PIL import Image

    base = BOOKS / item.folder
    pages = base / "pages"
    if pages.exists():
        shutil.rmtree(pages)
    pages.mkdir()
    index: list[str] = []
    n = 0
    for src in sorted((base / "download").iterdir()):
        suf = src.suffix.lower()
        if suf == ".pdf":
            doc = fitz.open(src)
            for pno, page in enumerate(doc, 1):
                n += 1
                area_in2 = page.rect.width * page.rect.height / POINTS_PER_INCH**2
                dpi = min(OCR_DPI, int((MAX_PIXELS / area_in2) ** 0.5))
                page.get_pixmap(dpi=dpi).save(pages / f"{n:04d}.png")
                layer = page.get_text().strip()
                if len(layer) >= MIN_TEXT_LAYER:
                    (pages / f"{n:04d}.txt").write_text(layer, encoding="utf-8")
                index.append(f"{n:04d}\t{src.name} p{pno}")
        elif suf in ARCHIVE_SUFFIXES:
            unpack = base / "unpacked" / src.stem
            if not unpack.exists():
                unpack.mkdir(parents=True)
                subprocess.run(
                    [str(SEVEN_ZIP), "x", "-y", f"-o{unpack}", str(src)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
            for img in sorted(
                p for p in unpack.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES
            ):
                n += 1
                _save_image(img, pages / f"{n:04d}.png", Image)
                index.append(
                    f"{n:04d}\t{src.name}/{img.relative_to(unpack).as_posix()}"
                )
        elif suf in IMAGE_SUFFIXES:
            n += 1
            _save_image(src, pages / f"{n:04d}.png", Image)
            index.append(f"{n:04d}\t{src.name}")
    (base / "pages.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
    log.info("%s: %d pages", item.folder, n)


def _save_image(src: Path, out: Path, image_mod) -> None:  # noqa: ANN001
    image_mod.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS
    im = image_mod.open(src)
    im.load()
    if im.width * im.height > MAX_PIXELS:
        scale = (MAX_PIXELS / (im.width * im.height)) ** 0.5
        im = im.resize((int(im.width * scale), int(im.height * scale)))
    im.convert("RGB").save(out)


def _ocr_page(png: Path, lang: str) -> str:
    layer = png.with_suffix(".txt")
    if layer.exists():
        return "[text layer]\n" + layer.read_text(encoding="utf-8")
    env = {**os.environ, "TESSDATA_PREFIX": str(TESSDATA)}
    res = subprocess.run(
        [str(TESSERACT), str(png), "stdout", "-l", lang, "--psm", "3"],
        capture_output=True,
        env=env,
        check=False,
    )
    if res.returncode != 0:
        log.warning(
            "%s: tesseract failed: %s",
            png.name,
            res.stderr.decode(errors="replace")[:200],
        )
    return join_cjk(res.stdout.decode("utf-8", errors="replace").strip())


def join_cjk(text: str) -> str:
    return CJK_SPACE_RE.sub("", text)


def tidy(item: Item) -> None:
    path = BOOKS / item.folder / "text.txt"
    path.write_text(join_cjk(path.read_text(encoding="utf-8")), encoding="utf-8")


def ocr(item: Item) -> None:
    from concurrent.futures import ThreadPoolExecutor

    base = BOOKS / item.folder
    index = dict(
        line.split("\t", 1)
        for line in (base / "pages.tsv").read_text(encoding="utf-8").splitlines()
        if line
    )
    pngs = sorted((base / "pages").glob("*.png"))
    with ThreadPoolExecutor(OCR_WORKERS) as pool:
        texts = list(pool.map(lambda p: _ocr_page(p, item.lang), pngs))
    out: list[str] = [
        f"# {item.note}",
        f"# OCR: Tesseract 5, lang {item.lang}, psm 3",
        "",
    ]
    for png, text in zip(pngs, texts, strict=True):
        out.append(f"=== page {png.stem} ({index.get(png.stem, '?')}) ===")
        out.append(text)
        out.append("")
    (base / "text.txt").write_text("\n".join(out), encoding="utf-8")
    log.info("%s: OCR done, %d pages", item.folder, len(pngs))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("fetch", "pages", "ocr", "tidy", "list"))
    ap.add_argument("items", nargs="*")
    args = ap.parse_args()
    chosen = [BY_FOLDER[f] for f in args.items] if args.items else list(ITEMS)
    for item in chosen:
        if args.action == "list":
            log.info("%s\t%s", item.folder, item.ia_id)
        elif args.action == "fetch":
            fetch(item)
        elif args.action == "pages":
            render_pages(item)
        elif args.action == "tidy":
            tidy(item)
        else:
            ocr(item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
