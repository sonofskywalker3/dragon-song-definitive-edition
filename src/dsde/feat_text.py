"""Text edits in the event scripts (script.dat), in two features (docs/plan-two-editions.md):

- `text-fixes` (both editions): speaker tags matched to the names the job menu uses. No line changes what it
  says; only the name tag over it is respelled.
- `text-edits` (Retold edition): every change to what a line says: the rewritten opening narration and the
  Y-button hint's stray "Anyway..." cut.

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
PLACE_START = "{"  # stands for FB 04, the blue place-name color (closed by FB 07)
PLACE_END = "}"
NEWLINE = "\n"
TEXT_CODES = {
    " ": b"\x00",
    ",": b"\x29",
    ".": b"\x2a",
    "!": b"\x24",
    "?": b"\x25",
    ":": b"\x2d",
    "'": b"\x54",
    NEWLINE: b"\xfd",
    SPEAKER_START: b"\xfb\x06",
    SPEAKER_END: b"\xfb\x07",
    PLACE_START: b"\xfb\x04",
    PLACE_END: b"\xfb\x07",
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


TEXT_FIX_EDITS = (
    # Gad's Express recipients whose dialogue name differs from the job menu; the Japanese release uses
    # the menu's name in both places (docs/re-japanese.md)
    speaker_rename(1, "Bram", "Balam", 2, "Gad's Express recipient Balam"),
    speaker_rename(4, "Gobi", "Gobbi", 5, "Gad's Express recipient Gobbi"),
    speaker_rename(5, "Tartallia", "Tartaglia", 4, "Gad's Express recipient Tartaglia"),
    speaker_rename(7, "Raiban", "Laban", 6, "Gad's Express recipient Laban"),
    speaker_rename(11, "Davida", "Devida", 2, "Gad's Express recipient Devida"),
)
RETOLD_EDITS = (
    # The field Y-button hint (Jian thinking aloud) opened with an "Anyway..." that follows nothing
    # (Jeff, 2026-10-07; the hints are to become party chat, docs/playtest-feedback.md item 9)
    TextEdit(
        18,
        "<Jian>\nAnyway...\n",
        "<Jian>\n",
        "first Y hint without the stray 'Anyway...'",
    ),
)


def encode_text(text: str) -> bytes:
    """Encode text in the script text encoding (no terminator)."""
    unknown = set(text) - TEXT_CODES.keys()
    if unknown:
        raise ValueError(f"no text code for {sorted(unknown)}")
    return b"".join(TEXT_CODES[c] for c in text)


@dataclass(frozen=True)
class MessageRewrite:
    """Replace a whole message (the one starting at offset start in a script) with new pages.

    Each page is a tuple of lines. A line of exactly LINE_WIDTH characters fills the box, which wraps
    after it by itself, so no line break is stored after it (place-name braces do not count).
    """

    script: int
    start: int
    pages: tuple[tuple[str, ...], ...]
    note: str


LINE_WIDTH = 30
NARRATION_PAGE = b"\xfe\xfc"  # end of page, then the narration's page start (as the vanilla prologue)
NARRATION_END = b"\xfe\xff"

# The opening narration (script 026 @ 0x08), rewritten from the Japanese and Lunar 1 and 2 canon with Jeff
# (docs/intro-analysis.md, 2026-10-07).
PROLOGUE = MessageRewrite(
    26,
    0x08,
    (
        (
            "Long, long ago...",
            "Beneath the Blue Star lay a",
            "dead world, without grass,",
            "without trees, without even",
            "air.",
            "",
            "Then came the Goddess Althena,",
            "her champion the Dragonmaster,",
            "and the Four Dragons.",
        ),
        (
            "Althena's magic brought water",
            "to the earth, and the desert",
            "of death turned green.",
            "",
            "Life filled the reborn land,",
            "and people came to make their",
            "homes there, blessed by the",
            "Goddess.",
        ),
        (
            "The Dragonmaster swore eternal",
            "loyalty to the Goddess, and",
            "with the Four Dragons stood",
            "guard over the world.",
            "Althena herself became the",
            "wellspring of all its magic.",
        ),
        (
            "Two peoples came to share",
            "this world.",
            "",
            "The Beastmen: powerfully",
            "built, stronger, faster, and",
            "hardier in every way...",
        ),
        (
            "...and the Humans: deft with",
            "tools, but small and frail.",
            "",
            "In time, power settled with",
            "the stronger Beastmen.",
        ),
        (
            "The Beastmen raised a regal",
            "castle at the heart of the",
            "world and lived in splendor,",
            "while the Humans settled the",
            "countryside and kept to",
            "simple ways.",
        ),
        (
            "So different were their lives",
            "that the two races kept apart,",
            "and that distance kept a",
            "delicate peace...",
            "for now.",
        ),
        (
            "Turn now to {Port Searis},",
            "a busy harbor town on the",
            "continent of Caldor.",
            "",
            "Here Jian Campbell makes his",
            "living as a courier, with his",
            "partner, Lucia Collins.",
        ),
    ),
    "opening narration rewritten (Japanese, Lunar canon; docs/intro-analysis.md)",
)
MESSAGE_REWRITES = (PROLOGUE,)
TEXT_EDITS = TEXT_FIX_EDITS + RETOLD_EDITS


def _page_bytes(lines: tuple[str, ...]) -> bytes:
    out = b""
    for i, line in enumerate(lines):
        shown = len(line.replace(PLACE_START, "").replace(PLACE_END, ""))
        if shown > LINE_WIDTH:
            raise ValueError(f"line over {LINE_WIDTH} characters: {line!r}")
        out += encode_text(line)
        if i < len(lines) - 1 and shown < LINE_WIDTH:
            out += TEXT_CODES[NEWLINE]
    return out


def rewrite_bytes(rewrite: MessageRewrite) -> bytes:
    """The rewritten message as stored, terminator included."""
    return NARRATION_PAGE.join(_page_bytes(p) for p in rewrite.pages) + NARRATION_END


def _message_ops(data: bytes, start: int) -> list[int]:
    """Offsets of the message ops that show the text at start."""
    code = struct.unpack_from("<I", data, CODE_START)[0]
    return [
        pc
        for pc in range(code, len(data) - OP_SIZE * 2 + 1, OP_SIZE)
        if struct.unpack_from("<H", data, pc)[0] == OP_MSG
        and struct.unpack_from("<I", data, pc + OP_TARGET)[0] == start
    ]


def _message_starts(data: bytes) -> set[int]:
    """Text offsets of every message op in a script."""
    code = struct.unpack_from("<I", data, CODE_START)[0]
    return {
        struct.unpack_from("<I", data, pc + OP_TARGET)[0]
        for pc in range(code, len(data) - OP_SIZE * 2 + 1, OP_SIZE)
        if struct.unpack_from("<H", data, pc)[0] == OP_MSG
    }


def _message_start(data: bytes, at: int) -> int:
    """Start of the message containing offset at (the latest text start before it)."""
    return max(s for s in _message_starts(data) if s <= at)


def _script_patches(
    script: int,
    data: bytes,
    edits: list[TextEdit],
    rewrites: list[MessageRewrite],
) -> list[DataPatch]:
    by_message: dict[int, list[TextEdit]] = defaultdict(list)
    whole = {r.start: r for r in rewrites}
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
    for start in sorted(by_message.keys() | whole.keys()):
        message_edits = by_message.get(start, [])
        stop = data.index(TEXT_END, start) + 1
        message = data[start:stop]
        notes = [e.note for e in message_edits]
        if start in whole:
            if start not in _message_starts(data):
                raise ValueError(f"script {script}: no message starts at {start:#x}")
            message = rewrite_bytes(whole[start])
            notes.insert(0, whole[start].note)
        for edit in message_edits:
            message = message.replace(encode_text(edit.old), encode_text(edit.new))
        note = "; ".join(notes)
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


def text_patches(
    edits: tuple[TextEdit, ...] = TEXT_EDITS,
    rewrites: tuple[MessageRewrite, ...] = MESSAGE_REWRITES,
) -> tuple[DataPatch, ...]:
    entries = read_archive(VANILLA_SCRIPTS.read_bytes())
    by_script: dict[int, list[TextEdit]] = defaultdict(list)
    rewrites_by_script: dict[int, list[MessageRewrite]] = defaultdict(list)
    for edit in edits:
        by_script[edit.script].append(edit)
    for rewrite in rewrites:
        rewrites_by_script[rewrite.script].append(rewrite)
    patches: list[DataPatch] = []
    for script in sorted(by_script.keys() | rewrites_by_script.keys()):
        patches += _script_patches(
            script,
            decompress(entries[script]),
            by_script[script],
            rewrites_by_script[script],
        )
    return tuple(patches)


def _scripts(
    edits: tuple[TextEdit, ...], rewrites: tuple[MessageRewrite, ...]
) -> set[int]:
    return {e.script for e in edits} | {r.script for r in rewrites}


# Each feature moves grown messages to the end of its scripts, so the two must not share a script.
if _scripts(TEXT_FIX_EDITS, ()) & _scripts(RETOLD_EDITS, MESSAGE_REWRITES):
    raise ValueError("text-fixes and text-edits must edit different scripts")

TEXT_FIXES = Feature("text-fixes", text_patches(TEXT_FIX_EDITS, ()))
TEXT_EDITS_FEATURE = Feature("text-edits", text_patches(RETOLD_EDITS, MESSAGE_REWRITES))
