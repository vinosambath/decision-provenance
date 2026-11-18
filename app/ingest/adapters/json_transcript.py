from __future__ import annotations

import json
from datetime import date

from app.ingest.models import NormalizedLine, ParsedTranscript


def parse(raw: str) -> ParsedTranscript:
    payload = json.loads(raw)

    lines = tuple(
        NormalizedLine(speaker=segment.get("speaker"), text=segment["text"].strip())
        for segment in payload.get("segments", [])
        if segment.get("text", "").strip()
    )

    raw_date = payload.get("date")
    participants = payload.get("participants")

    return ParsedTranscript(
        lines=lines,
        title=payload.get("title"),
        date=date.fromisoformat(raw_date) if raw_date else None,
        participants=tuple(participants) if participants else None,
    )
