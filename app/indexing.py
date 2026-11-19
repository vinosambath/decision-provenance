from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Corpus, Meeting, Segment
from app.ingest.mark import mark
from app.ingest.normalize import normalize_file
from app.ingest.segment import segment_meeting

SUPPORTED_SUFFIXES = {".vtt", ".srt", ".json", ".md"}


@dataclass
class IndexResult:
    meetings_indexed: int = 0
    meetings_skipped: int = 0
    segments_created: int = 0

    def as_dict(self) -> dict:
        return {
            "meetings_indexed": self.meetings_indexed,
            "meetings_skipped": self.meetings_skipped,
            "segments_created": self.segments_created,
        }


async def index_corpus(session: AsyncSession, corpus: Corpus) -> IndexResult:
    """Normalizes every supported file in corpus.path, scores it, and upserts it.

    Idempotent by content hash: a meeting whose hash hasn't changed since the
    last index is skipped entirely, no re-segmentation or re-marking.
    """
    result = IndexResult()
    root = Path(corpus.path)

    existing_hashes = {
        meeting.external_id: meeting.content_hash
        for meeting in (
            await session.execute(select(Meeting).where(Meeting.corpus_id == corpus.id))
        ).scalars()
    }

    for file_path in sorted(root.glob("*")):
        if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        normalized = normalize_file(file_path)

        if existing_hashes.get(normalized.id) == normalized.content_hash:
            result.meetings_skipped += 1
            continue

        await session.execute(
            delete(Meeting).where(Meeting.corpus_id == corpus.id, Meeting.external_id == normalized.id)
        )

        meeting = Meeting(
            corpus_id=corpus.id,
            external_id=normalized.id,
            path=str(normalized.source_path),
            title=normalized.title,
            date=normalized.date,
            participants=list(normalized.participants),
            line_count=normalized.line_count,
            content_hash=normalized.content_hash,
        )
        session.add(meeting)
        await session.flush()

        for span in segment_meeting(normalized):
            marked = mark(span)
            session.add(
                Segment(
                    meeting_id=meeting.id,
                    start_line=marked.start_line,
                    end_line=marked.end_line,
                    text=marked.text,
                    decision_density=marked.decision_density,
                    has_alternatives=marked.has_alternatives,
                    has_objection=marked.has_objection,
                )
            )
            result.segments_created += 1

        result.meetings_indexed += 1

    await session.commit()
    return result
