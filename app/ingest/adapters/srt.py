from __future__ import annotations

from app.ingest.adapters._shared import split_speaker_prefix
from app.ingest.models import NormalizedLine, ParsedTranscript


def parse(raw: str) -> ParsedTranscript:
    lines: list[NormalizedLine] = []
    for block in raw.replace("\r\n", "\n").split("\n\n"):
        for raw_line in (l.strip() for l in block.split("\n")):
            if not raw_line or raw_line.isdigit() or "-->" in raw_line:
                continue
            speaker, text = split_speaker_prefix(raw_line)
            lines.append(NormalizedLine(speaker=speaker, text=text))
    return ParsedTranscript(lines=tuple(lines))
