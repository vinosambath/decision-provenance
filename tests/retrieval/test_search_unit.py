from app.retrieval.search import Candidate, _apply_meeting_cap


def _candidate(segment_id: int, meeting_id: int, score: float) -> Candidate:
    return Candidate(
        segment_id=segment_id,
        meeting_id=meeting_id,
        meeting_external_id=f"meeting-{meeting_id}",
        meeting_title="t",
        meeting_date=None,
        start_line=1,
        end_line=1,
        text="text",
        relevance=score,
        decision_density=0.0,
        score=score,
    )


def test_cap_limits_segments_per_meeting() -> None:
    candidates = [
        _candidate(1, meeting_id=1, score=0.9),
        _candidate(2, meeting_id=1, score=0.8),
        _candidate(3, meeting_id=1, score=0.7),
        _candidate(4, meeting_id=1, score=0.6),
        _candidate(5, meeting_id=2, score=0.5),
    ]

    selected = _apply_meeting_cap(candidates, top_k=25, meeting_cap=2)

    assert [c.segment_id for c in selected] == [1, 2, 5]


def test_cap_respects_top_k() -> None:
    candidates = [_candidate(i, meeting_id=i, score=1.0 - i * 0.01) for i in range(10)]

    selected = _apply_meeting_cap(candidates, top_k=3, meeting_cap=5)

    assert len(selected) == 3
    assert [c.segment_id for c in selected] == [0, 1, 2]


def test_cap_preserves_score_order() -> None:
    candidates = [
        _candidate(1, meeting_id=1, score=0.5),
        _candidate(2, meeting_id=2, score=0.9),
        _candidate(3, meeting_id=3, score=0.7),
    ]

    selected = _apply_meeting_cap(candidates, top_k=25, meeting_cap=5)

    assert [c.segment_id for c in selected] == [1, 2, 3]
