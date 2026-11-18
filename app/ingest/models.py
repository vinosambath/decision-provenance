from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path


@dataclass(frozen=True)
class NormalizedLine:
    speaker: str | None
    text: str


@dataclass(frozen=True)
class ParsedTranscript:
    """What a single adapter can pull out of one file's own contents.

    Any field an adapter can't determine (most formats have no explicit
    title/date/participants) is left None/empty for normalize.py to resolve.
    """

    lines: tuple[NormalizedLine, ...]
    title: str | None = None
    date: Date | None = None
    participants: tuple[str, ...] | None = None


@dataclass(frozen=True)
class NormalizedMeeting:
    """A transcript once every adapter- and filename-derived field is resolved."""

    id: str
    source_path: Path
    title: str
    date: Date | None
    participants: tuple[str, ...]
    lines: tuple[NormalizedLine, ...]

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def content_hash(self) -> str:
        body = "\n".join(f"{line.speaker or ''}\t{line.text}" for line in self.lines)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def rendered(self) -> str:
        """Line-numbered plaintext, 1-indexed. This numbering is the citation anchor."""
        width = max(len(str(self.line_count)), 1)
        rows = []
        for line_number, line in enumerate(self.lines, start=1):
            speaker_prefix = f"{line.speaker}: " if line.speaker else ""
            rows.append(f"{line_number:>{width}} | {speaker_prefix}{line.text}")
        return "\n".join(rows)
