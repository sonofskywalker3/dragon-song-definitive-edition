"""Gad's Express delivery jobs (design 9). Research: docs/re-mp-jobs-rings.md section 2.

Recipient names: 10 recipients have one name in the job menu and another in their own dialogue. The Japanese
release uses one name for both (docs/re-japanese.md). Five menu names are wrong and are fixed here, in place (each
fix keeps its length, so the string table's offsets stay); the five wrong dialogue names are speaker tag edits
in feat_text.py.
"""

import struct
from pathlib import Path

from dsde.feat_gad_jobs import job_patches
from dsde.feat_text import encode_text
from dsde.patching import ARM9_BASE, Feature, Patch

VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"
STRING_END = b"\xff"
WORD = 4
MENU_NAME_FIXES = {  # job menu name (shop string block 0x020A4E2C): correct name
    "Timathy": "Timothy",
    "Paoro": "Paolo",
    "eva": "Eva",
    "Pazolini": "Pasolini",
    "Esthel": "Esther",
}


def _menu_name_patches() -> tuple[Patch, ...]:
    data = VANILLA_ARM9.read_bytes()
    patches = []
    for old, new in MENU_NAME_FIXES.items():
        old_bytes = STRING_END + encode_text(old) + STRING_END
        new_bytes = STRING_END + encode_text(new) + STRING_END
        if len(old_bytes) != len(new_bytes) or data.count(old_bytes) != 1:
            raise ValueError(f"menu name {old!r} is not a unique same-length fix")
        at = data.index(old_bytes)
        first = next(i for i, (a, b) in enumerate(zip(old_bytes, new_bytes)) if a != b)
        last = max(i for i, (a, b) in enumerate(zip(old_bytes, new_bytes)) if a != b)
        for offset in range(first, last + 1, WORD):
            word_at = at + offset
            window = bytearray(data[word_at : word_at + WORD])
            for i in range(WORD):
                if offset + i < len(new_bytes):
                    window[i] = new_bytes[offset + i]
            patches.append(
                Patch(
                    ARM9_BASE + word_at,
                    struct.unpack_from("<I", data, word_at)[0],
                    struct.unpack("<I", bytes(window))[0],
                    f"job menu name {old} -> {new}",
                )
            )
    return tuple(patches)


GAD_NAME_PATCHES = _menu_name_patches()

GAD_EXPRESS = Feature("gad-express", GAD_NAME_PATCHES + job_patches())
