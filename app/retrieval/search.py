from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import String, cast, func, select
from sqlalchemy.dialects.postgresql import TSQUERY
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Meeting, Segment

DEFAULT_TOP_K = 25
DEFAULT_MEETING_CAP = 3

# Multiplying relevance straight by decision_density (as the design doc's
# prose literally says) would zero out every segment with no commitment
# language at all — including alternative-rejection segments, which matter
# just as much as the commitment itself. `1 + density * k` amplifies
# decisive segments instead of discarding merely-relevant ones.
DENSITY_BOOST_FACTOR = 10.0


@dataclass(frozen=True)
class Candidate:
    segment_id: int
    meeting_id: int
    meeting_external_id: str
    meeting_title: str
    meeting_date: date | None
    start_line: int
    end_line: int
    text: str
    relevance: float
    decision_density: float
    score: float


async def search(
    session: AsyncSession,
    corpus_id: int,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    meeting_cap: int = DEFAULT_MEETING_CAP,
) -> list[Candidate]:
    # websearch_to_tsquery ANDs every term by default. Segments are short
    # (~12 lines), so a question's words easily land in different segments
    # of the same meeting and match nothing despite the meeting being
    # relevant. Retrieval's job here is to cast a wide net — precision is a
    # later agent's problem — so we rewrite the AND query into an OR query.
    # This leaves quoted-phrase sequences (the '<->' operator) untouched;
    # only top-level term boundaries (' & ') become OR (' | ').
    and_query = func.websearch_to_tsquery("english", query)
    tsquery = cast(func.replace(cast(and_query, String), " & ", " | "), TSQUERY)
    relevance = func.ts_rank_cd(Segment.search_vector, tsquery)
    boosted_score = relevance * (1 + Segment.decision_density * DENSITY_BOOST_FACTOR)

    statement = (
        select(
            Segment.id,
            Segment.meeting_id,
            Meeting.external_id,
            Meeting.title,
            Meeting.date,
            Segment.start_line,
            Segment.end_line,
            Segment.text,
            relevance.label("relevance"),
            Segment.decision_density,
            boosted_score.label("score"),
        )
        .join(Meeting, Meeting.id == Segment.meeting_id)
        .where(Meeting.corpus_id == corpus_id)
        .where(Segment.search_vector.op("@@")(tsquery))
        .order_by(boosted_score.desc())
    )

    rows = (await session.execute(statement)).all()

    candidates = [
        Candidate(
            segment_id=row.id,
            meeting_id=row.meeting_id,
            meeting_external_id=row.external_id,
            meeting_title=row.title,
            meeting_date=row.date,
            start_line=row.start_line,
            end_line=row.end_line,
            text=row.text,
            relevance=row.relevance,
            decision_density=row.decision_density,
            score=row.score,
        )
        for row in rows
    ]

    return _apply_meeting_cap(candidates, top_k=top_k, meeting_cap=meeting_cap)


def _apply_meeting_cap(
    candidates: list[Candidate], top_k: int, meeting_cap: int
) -> list[Candidate]:
    """Keeps candidates in score order, skipping any once its meeting has
    already contributed meeting_cap segments — so one long meeting can't
    crowd out the result list."""
    selected: list[Candidate] = []
    contributions: dict[int, int] = {}

    for candidate in candidates:
        if contributions.get(candidate.meeting_id, 0) >= meeting_cap:
            continue
        selected.append(candidate)
        contributions[candidate.meeting_id] = contributions.get(candidate.meeting_id, 0) + 1
        if len(selected) >= top_k:
            break

    return selected
