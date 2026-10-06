"""Text edits in the event scripts (script.dat).

A script file starts with a jump over its text block to its code; each message op (0x0F) holds the
file offset of its text, which ends with 0xFF. Text boxes wrap by themselves at 30 characters and
the stored text leaves out the space at each wrap ("Althena,her"), so keep an edited line within
30 characters or check the layout in the emulator.

An edit that keeps its message's length is patched in place. One that changes it gets a copy of the
whole message at the end of the script file, and every message op that showed the old one points at
the copy; nothing else in the file moves.
"""

import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from dsde.archive import decompress, read_archive
from dsde.patching import DataPatch, Feature

VANILLA_SCRIPTS = (
    Path(__file__).resolve().parents[2] / "extract" / "files" / "script.dat"
)
ARCHIVE = "script"

OP_MSG = 0x0F
OP_SIZE = 4  # ops are 4-byte aligned
OP_TARGET = 4  # u32 file offset of the message text
CODE_START = 4  # the file's first op jumps to its code at this u32
TEXT_END = 0xFF
SPEAKER_START = "<"  # stands for FB 06, which opens a speaker name
SPEAKER_END = ">"  # FB 07 closes it
TEXT_CODES = {
    " ": b"\x00",
    ",": b"\x29",
    ".": b"\x2a",
    "'": b"\x54",
    "\n": b"\xfd",
    SPEAKER_START: b"\xfb\x06",
    SPEAKER_END: b"\xfb\x07",
    **{chr(ord("A") + i): bytes([0x02 + i]) for i in range(26)},
    **{chr(ord("a") + i): bytes([0x3A + i]) for i in range(26)},
    **{chr(ord("0") + i): bytes([0x30 + i]) for i in range(10)},
}


@dataclass(frozen=True)
class TextEdit:
    """Replace text in one script file. old must occur exactly count times in it; all are replaced."""

    script: int
    old: str
    new: str
    note: str
    count: int = 1


def speaker_rename(script: int, old: str, new: str, count: int, note: str) -> TextEdit:
    """Rename every speaker tag old in a script (only the tags, not the name in running text)."""
    return TextEdit(
        script,
        SPEAKER_START + old + SPEAKER_END,
        SPEAKER_START + new + SPEAKER_END,
        note,
        count,
    )


TEXT_EDITS = (
    TextEdit(
        26,
        "her servant the Dragonmaster\n",
        # exactly 30 characters: the box wraps after it, so the line break goes
        "her champion the Dragonmaster,",
        "intro: the Dragonmaster is Althena's champion, not her servant",
    ),
    # Gad's Express recipients whose dialogue name differs from the job menu; the Japanese release uses
    # the menu's name in both places (docs/re-japanese.md)
    speaker_rename(1, "Bram", "Balam", 2, "Gad's Express recipient Balam"),
    speaker_rename(4, "Gobi", "Gobbi", 5, "Gad's Express recipient Gobbi"),
    speaker_rename(5, "Tartallia", "Tartaglia", 4, "Gad's Express recipient Tartaglia"),
    speaker_rename(7, "Raiban", "Laban", 6, "Gad's Express recipient Laban"),
    speaker_rename(11, "Davida", "Devida", 2, "Gad's Express recipient Devida"),
)


def encode_text(text: str) -> bytes:
    """Encode text in the script text encoding (no terminator)."""
    unknown = set(text) - TEXT_CODES.keys()
    if unknown:
        raise ValueError(f"no text code for {sorted(unknown)}")
    return b"".join(TEXT_CODES[c] for c in text)


def _message_ops(data: bytes, start: int) -> list[int]:
    """Offsets of the message ops that show the text at start."""
    code = struct.unpack_from("<I", data, CODE_START)[0]
    return [
        pc
        for pc in range(code, len(data) - OP_SIZE * 2 + 1, OP_SIZE)
        if struct.unpack_from("<H", data, pc)[0] == OP_MSG
        and struct.unpack_from("<I", data, pc + OP_TARGET)[0] == start
    ]


def _message_start(data: bytes, at: int) -> int:
    """Start of the message containing offset at (the latest text start before it)."""
    code = struct.unpack_from("<I", data, CODE_START)[0]
    starts = {
        struct.unpack_from("<I", data, pc + OP_TARGET)[0]
        for pc in range(code, len(data) - OP_SIZE * 2 + 1, OP_SIZE)
        if struct.unpack_from("<H", data, pc)[0] == OP_MSG
    }
    return max(s for s in starts if s <= at)


def _script_patches(script: int, data: bytes, edits: list[TextEdit]) -> list[DataPatch]:
    by_message: dict[int, list[TextEdit]] = defaultdict(list)
    for edit in edits:
        old = encode_text(edit.old)
        if data.count(old) != edit.count:
            raise ValueError(
                f"script {script}: {edit.old!r} found {data.count(old)} times,"
                f" expected {edit.count}"
            )
        at = data.find(old)
        while at != -1:
            message_edits = by_message[_message_start(data, at)]
            if edit not in message_edits:
                message_edits.append(edit)
            at = data.find(old, at + len(old))
    patches = []
    end = len(data)
    for start, message_edits in sorted(by_message.items()):
        stop = data.index(TEXT_END, start) + 1
        message = data[start:stop]
        for edit in message_edits:
            message = message.replace(encode_text(edit.old), encode_text(edit.new))
        note = "; ".join(e.note for e in message_edits)
        if len(message) == stop - start:
            patches.append(
                DataPatch(ARCHIVE, script, start, data[start:stop], message, note)
            )
            continue
        ops = _message_ops(data, start)
        if not ops:
            raise ValueError(f"script {script}: no message op shows text {start:#x}")
        patches.append(DataPatch(ARCHIVE, script, end, b"", message, note))
        for pc in ops:
            patches.append(
                DataPatch(
                    ARCHIVE,
                    script,
                    pc + OP_TARGET,
                    struct.pack("<I", start),
                    struct.pack("<I", end),
                    f"{note} (message moved to {end:#x})",
                )
            )
        end += len(message)
    return patches


def text_patches(edits: tuple[TextEdit, ...] = TEXT_EDITS) -> tuple[DataPatch, ...]:
    entries = read_archive(VANILLA_SCRIPTS.read_bytes())
    by_script: dict[int, list[TextEdit]] = defaultdict(list)
    for edit in edits:
        by_script[edit.script].append(edit)
    patches: list[DataPatch] = []
    for script, script_edits in sorted(by_script.items()):
        patches += _script_patches(script, decompress(entries[script]), script_edits)
    return tuple(patches)


TEXT_FIXES = Feature("text-edits", text_patches())
