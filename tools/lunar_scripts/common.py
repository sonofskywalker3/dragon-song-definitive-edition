"""Shared output format for the Lunar script dumps.

Every dump is a plain UTF-8 text file:

    # <game title>
    # produced by <tool>; <n> messages
    === <source file> @0x<offset> | <speaker or -> ===
    <message text, line breaks kept, box breaks as a blank line>

Speaker is the portrait/attribution the format stores (e.g. "L39" = left portrait 0x39,
"P705" = Lunar 2 box portrait 705); ids are not mapped to names. A portrait change in
the middle of a message is marked inline as "[L39] ".
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


BLANK_RUN_RE = re.compile(r"\n{3,}")


@dataclass
class Message:
    source: str
    offset: int
    text: str
    speakers: list[str] = field(default_factory=list)


def write_dump(path: Path, title: str, tool: str, messages: list[Message]) -> None:
    lines = [f"# {title}", f"# produced by {tool}; {len(messages)} messages", ""]
    for m in messages:
        who = ", ".join(dict.fromkeys(m.speakers)) if m.speakers else "-"
        lines.append(f"=== {m.source} @0x{m.offset:X} | {who} ===")
        lines.append(BLANK_RUN_RE.sub("\n\n", m.text).strip("\n"))
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_subs(path: Path) -> list[tuple[re.Pattern[str], str]]:
    """Read a wdtools-style substitution file ("orig | Replacement;") into word-bounded regexes."""
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or " | " not in line:
            continue
        orig, rest = line.split(" | ", 1)
        repl = rest.split(";", 1)[0]
        orig = orig.strip()
        if not orig:
            continue
        words = [re.escape(w) for w in orig.split()]
        pat = re.compile(
            r"(?<![A-Za-z])" + r"\s+".join(words) + r"(?![A-Za-z])", re.IGNORECASE
        )
        rules.append((pat, repl.strip()))
    return rules


def apply_subs(text: str, rules: list[tuple[re.Pattern[str], str]]) -> str:
    """Apply proper-noun rules, keeping the original whitespace (line breaks) between words."""

    def fix(rep: str) -> Callable[[re.Match[str]], str]:
        def inner(m: re.Match[str]) -> str:
            gaps = re.findall(r"\s+", m.group(0))
            words = rep.split(" ")
            out = words[0]
            for i, w in enumerate(words[1:]):
                out += (gaps[i] if i < len(gaps) else " ") + w
            if m.group(0)[:1].isupper():
                out = out[:1].upper() + out[1:]
            return out

        return inner

    for pat, rep in rules:
        text = pat.sub(fix(rep), text)
    return text


TAG_RE = re.compile(r"\[[^\]]*\]")
PLAIN_CHARS = frozenset(" .,!?'\"\n-")
TEXTY_RATIO = 0.85
WORD_RE = re.compile(r"\b[A-Za-z][a-z]{3,}\b")
SILENCE_RE = re.compile(r"[.\s_!?]+")


def looks_like_text(text: str) -> bool:
    """Heuristic filter for scanners that can lock onto binary data."""
    bare = TAG_RE.sub("", text).strip()
    if not bare:
        return False
    if SILENCE_RE.fullmatch(bare):
        return True
    ratio = sum(c.isalpha() or c in PLAIN_CHARS for c in bare) / len(bare)
    return ratio >= TEXTY_RATIO or bool(WORD_RE.search(bare))
