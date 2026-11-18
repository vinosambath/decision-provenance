from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path

from app.ingest.adapters import json_transcript, markdown, srt, vtt
from app.ingest.models import NormalizedLine, NormalizedMeeting, ParsedTranscript

_PARSERS = {
    ".vtt": vtt.parse,
    ".srt": srt.parse,
    ".json": json_transcript.parse,
    ".md": markdown.parse,
}

_FILENAME_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})[-_]?(.*)$")


class UnsupportedTranscriptFormat(ValueError):
    def __init__(self, suffix: str) -> None:
        super().__init__(f"no adapter for '{suffix}' files")


def normalize_file(path: Path) -> NormalizedMeeting:
    try:
        parse = _PARSERS[path.suffix.lower()]
    except KeyError as exc:
        raise UnsupportedTranscriptFormat(path.suffix) from exc

    parsed = parse(path.read_text(encoding="utf-8"))
    return _assemble(path, parsed)


def _assemble(path: Path, parsed: ParsedTranscript) -> NormalizedMeeting:
    filename_title, filename_date = _parse_filename(path.stem)

    return NormalizedMeeting(
        id=path.stem,
        source_path=path,
        title=parsed.title or filename_title,
        date=parsed.date or filename_date,
        participants=parsed.participants or _speakers_in_order(parsed.lines),
        lines=parsed.lines,
    )


def _parse_filename(stem: str) -> tuple[str, date | None]:
    match = _FILENAME_DATE.match(stem)
    if not match:
        return _humanize(stem), None

    raw_date, remainder = match.groups()
    meeting_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    title = _humanize(remainder) if remainder else _humanize(stem)
    return title, meeting_date


def _humanize(slug: str) -> str:
    words = re.split(r"[-_]+", slug.strip("-_"))
    return " ".join(word.capitalize() for word in words if word) or slug


def _speakers_in_order(lines: Iterable[NormalizedLine]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for line in lines:
        if line.speaker and line.speaker not in seen:
            seen[line.speaker] = None
    return tuple(seen)
