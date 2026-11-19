from pathlib import Path

from app.ingest.models import NormalizedLine, NormalizedMeeting
from app.ingest.segment import segment_meeting


def _meeting(line_count: int) -> NormalizedMeeting:
    lines = tuple(NormalizedLine(speaker="Speaker", text=f"line {i}") for i in range(line_count))
    return NormalizedMeeting(
        id="m", source_path=Path("m.vtt"), title="t", date=None, participants=(), lines=lines
    )


def test_short_meeting_is_a_single_segment() -> None:
    spans = segment_meeting(_meeting(5), max_lines=12)

    assert len(spans) == 1
    assert spans[0].start_line == 1
    assert spans[0].end_line == 5


def test_meeting_splits_into_fixed_windows() -> None:
    spans = segment_meeting(_meeting(25), max_lines=12)

    assert len(spans) == 3
    assert [(s.start_line, s.end_line) for s in spans] == [(1, 12), (13, 24), (25, 25)]


def test_windows_do_not_overlap() -> None:
    spans = segment_meeting(_meeting(24), max_lines=12)

    all_lines = [line for span in spans for line in range(span.start_line, span.end_line + 1)]
    assert all_lines == list(range(1, 25))


def test_span_text_includes_speaker_prefix() -> None:
    spans = segment_meeting(_meeting(2), max_lines=12)

    assert spans[0].text == "Speaker: line 0\nSpeaker: line 1"
