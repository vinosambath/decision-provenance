from __future__ import annotations

from dataclasses import dataclass

from app.ingest.models import NormalizedLine, NormalizedMeeting

MAX_SEGMENT_LINES = 12


@dataclass(frozen=True)
class LineSpan:
    start_line: int
    end_line: int
    lines: tuple[NormalizedLine, ...]

    @property
    def text(self) -> str:
        return "\n".join(
            f"{line.speaker}: {line.text}" if line.speaker else line.text for line in self.lines
        )


def segment_meeting(meeting: NormalizedMeeting, max_lines: int = MAX_SEGMENT_LINES) -> list[LineSpan]:
    """Splits a meeting into fixed-size, non-overlapping, 1-indexed line windows.

    Real topic-shift segmentation (speaker-turn density, pause length) needs
    timing data our adapters don't carry. Fixed windows are the master doc's
    own named fallback for this feature — see steps/03-index.md.
    """
    total = len(meeting.lines)
    spans = []
    for start in range(0, total, max_lines):
        end = min(start + max_lines, total)
        spans.append(LineSpan(start_line=start + 1, end_line=end, lines=meeting.lines[start:end]))
    return spans
