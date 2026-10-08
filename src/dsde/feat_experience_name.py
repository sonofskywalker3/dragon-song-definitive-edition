""" "Althena Conduct" is called "Experience" (Jeff, 2026-10-08).

The name appears twice in arm9's indexed string lists (0xFF-terminated, game charset): the battle result banner
(hidden by result-screens, kept consistent) and the status screen label. The lists are reached through u16
offset tables, so each copy keeps its length: "Experience" and spaces to the old 15 characters.
"""

from pathlib import Path

from dsde.feat_text import encode_text
from dsde.patching import ARM9_BASE, Feature, Patch, byte_patches

VANILLA_ARM9 = Path(__file__).resolve().parents[2] / "extract" / "arm9" / "arm9.bin"
OLD_NAME = "Althena Conduct"
NEW_NAME = "Experience"
NAME_COPIES = (
    0x020A4377,  # battle result strings
    0x020A665E,  # status screen labels
)


def _rename_patches() -> tuple[Patch, ...]:
    arm9 = VANILLA_ARM9.read_bytes()
    old = encode_text(OLD_NAME)
    new = encode_text(NEW_NAME.ljust(len(OLD_NAME)))
    edits = {}
    for addr in NAME_COPIES:
        offset = addr - ARM9_BASE
        if arm9[offset : offset + len(old)] != old:
            raise ValueError(f"{OLD_NAME!r} not found at {addr:#x}")
        edits.update({addr + i: byte for i, byte in enumerate(new)})
    return byte_patches(arm9, edits, f"{OLD_NAME} is called {NEW_NAME}")


EXPERIENCE_NAME = Feature("experience-name", _rename_patches())
