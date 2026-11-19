from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.db_models import Corpus, Job, Meeting, Segment
from app.indexing import index_corpus
from app.retrieval.search import DEFAULT_MEETING_CAP, DEFAULT_TOP_K, search
from app.schemas import (
    CorpusCreateRequest,
    CorpusCreateResponse,
    CorpusStatsResponse,
    IndexResponse,
    SearchCandidateResponse,
    SearchResponse,
)

router = APIRouter(prefix="/corpora", tags=["corpora"])


@router.post("", response_model=CorpusCreateResponse, status_code=201)
async def create_corpus(
    request: CorpusCreateRequest, session: AsyncSession = Depends(get_session)
) -> CorpusCreateResponse:
    path = Path(request.path).expanduser().resolve()
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"'{path}' is not a directory")

    existing = await session.scalar(select(Corpus).where(Corpus.path == str(path)))
    if existing:
        return CorpusCreateResponse(corpus_id=existing.id)

    corpus = Corpus(path=str(path))
    session.add(corpus)
    await session.commit()
    return CorpusCreateResponse(corpus_id=corpus.id)


@router.post("/{corpus_id}/index", response_model=IndexResponse, status_code=202)
async def start_index(corpus_id: int, session: AsyncSession = Depends(get_session)) -> IndexResponse:
    corpus = await session.get(Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status_code=404, detail="corpus not found")

    job = Job(kind="index", corpus_id=corpus_id, status="running")
    session.add(job)
    await session.commit()

    try:
        result = await index_corpus(session, corpus)
        job.status = "completed"
        job.progress = result.as_dict()
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
    finally:
        job.finished_at = datetime.now(timezone.utc)
        await session.commit()

    return IndexResponse(job_id=job.id)


@router.get("/{corpus_id}", response_model=CorpusStatsResponse)
async def get_corpus(corpus_id: int, session: AsyncSession = Depends(get_session)) -> CorpusStatsResponse:
    corpus = await session.get(Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status_code=404, detail="corpus not found")

    meeting_count = await session.scalar(
        select(func.count()).select_from(Meeting).where(Meeting.corpus_id == corpus_id)
    )
    segment_count = await session.scalar(
        select(func.count()).select_from(Segment).join(Meeting).where(Meeting.corpus_id == corpus_id)
    )
    min_date, max_date = (
        await session.execute(
            select(func.min(Meeting.date), func.max(Meeting.date)).where(Meeting.corpus_id == corpus_id)
        )
    ).one()
    participant_lists = (
        await session.execute(select(Meeting.participants).where(Meeting.corpus_id == corpus_id))
    ).scalars()
    participants = sorted({name for row in participant_lists for name in row})

    return CorpusStatsResponse(
        corpus_id=corpus_id,
        meeting_count=meeting_count or 0,
        segment_count=segment_count or 0,
        date_range=(min_date, max_date) if min_date and max_date else None,
        participants=participants,
    )


@router.get("/{corpus_id}/search", response_model=SearchResponse)
async def search_corpus(
    corpus_id: int,
    q: str,
    top_k: int = DEFAULT_TOP_K,
    meeting_cap: int = DEFAULT_MEETING_CAP,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    corpus = await session.get(Corpus, corpus_id)
    if corpus is None:
        raise HTTPException(status_code=404, detail="corpus not found")

    candidates = await search(session, corpus_id, q, top_k=top_k, meeting_cap=meeting_cap)

    return SearchResponse(
        query=q,
        candidates=[SearchCandidateResponse(**candidate.__dict__) for candidate in candidates],
    )
