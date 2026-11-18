from __future__ import annotations

import re

_SPEAKER_PREFIX = re.compile(r"^([A-Za-z][\w .'\-]{0,40}):\s+(.*)$")


def split_speaker_prefix(line: str) -> tuple[str | None, str]:
    """Pull a leading 'Speaker: text' label off a transcript line, if present."""
    match = _SPEAKER_PREFIX.match(line)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, line
