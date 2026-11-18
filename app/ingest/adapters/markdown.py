from __future__ import annotations

from datetime import date

from app.ingest.adapters._shared import split_speaker_prefix
from app.ingest.models import NormalizedLine, ParsedTranscript


def parse(raw: str) -> ParsedTranscript:
    front_matter, body = _split_front_matter(raw)

    lines = tuple(
        NormalizedLine(*split_speaker_prefix(stripped))
        for raw_line in body.split("\n")
        if (stripped := raw_line.strip()) and not stripped.startswith("#")
    )

    raw_date = front_matter.get("date")
    participants = front_matter.get("participants")

    return ParsedTranscript(
        lines=lines,
        title=front_matter.get("title"),
        date=date.fromisoformat(raw_date) if raw_date else None,
        participants=tuple(participants) if participants else None,
    )


def _split_front_matter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw

    _, _, rest = raw.partition("---\n")
    block, _, body = rest.partition("\n---")
    return _parse_front_matter(block), body.lstrip("\n")


def _parse_front_matter(block: str) -> dict:
    fields: dict = {}
    for raw_line in block.split("\n"):
        if ":" not in raw_line:
            continue
        key, _, value = raw_line.partition(":")
        fields[key.strip()] = _parse_value(value.strip())
    return fields


def _parse_value(value: str) -> str | list[str]:
    if value.startswith("[") and value.endswith("]"):
        return [item.strip() for item in value[1:-1].split(",") if item.strip()]
    return value
