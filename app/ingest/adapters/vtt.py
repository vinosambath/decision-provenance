from __future__ import annotations

from app.ingest.adapters._shared import split_speaker_prefix
from app.ingest.models import NormalizedLine, ParsedTranscript

_VOICE_TAG_OPEN = "<v "


def parse(raw: str) -> ParsedTranscript:
    lines: list[NormalizedLine] = []
    for block in raw.replace("\r\n", "\n").split("\n\n"):
        for raw_line in (l.strip() for l in block.split("\n")):
            if not raw_line or raw_line.isdigit() or raw_line.upper() == "WEBVTT" or "-->" in raw_line:
                continue
            lines.append(_parse_line(raw_line))
    return ParsedTranscript(lines=tuple(lines))


def _parse_line(raw_line: str) -> NormalizedLine:
    if raw_line.startswith(_VOICE_TAG_OPEN):
        end = raw_line.index(">")
        speaker = raw_line[len(_VOICE_TAG_OPEN) : end].strip()
        text = raw_line[end + 1 :].removesuffix("</v>").strip()
        return NormalizedLine(speaker=speaker, text=text)

    speaker, text = split_speaker_prefix(raw_line)
    return NormalizedLine(speaker=speaker, text=text)
