from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class CorpusCreateRequest(BaseModel):
    path: str


class CorpusCreateResponse(BaseModel):
    corpus_id: int


class CorpusStatsResponse(BaseModel):
    corpus_id: int
    meeting_count: int
    segment_count: int
    date_range: tuple[date, date] | None
    participants: list[str]


class IndexResponse(BaseModel):
    job_id: int


class JobResponse(BaseModel):
    id: int
    kind: str
    status: str
    progress: dict | None
    error: str | None


class SearchCandidateResponse(BaseModel):
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


class SearchResponse(BaseModel):
    query: str
    candidates: list[SearchCandidateResponse]
