import time

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select

from app.db import get_session
from app.db_models import Corpus, Meeting, Segment
from app.main import app
from corpus.generate import OUT_DIR, TARGET_MEETING_COUNT


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _delete_corpus(corpus_id: int) -> None:
    async for session in get_session():
        await session.execute(delete(Corpus).where(Corpus.id == corpus_id))
        await session.commit()


async def _average_density(meeting_substring: str) -> float:
    async for session in get_session():
        avg = await session.scalar(
            select(func.avg(Segment.decision_density))
            .join(Meeting)
            .where(Meeting.external_id.contains(meeting_substring))
        )
        return float(avg) if avg is not None else 0.0
    raise AssertionError("no session yielded")


async def test_index_corpus_end_to_end() -> None:
    async with await _client() as client:
        create_response = await client.post("/corpora", json={"path": str(OUT_DIR)})
        assert create_response.status_code == 201
        corpus_id = create_response.json()["corpus_id"]

        try:
            start = time.perf_counter()
            index_response = await client.post(f"/corpora/{corpus_id}/index")
            elapsed = time.perf_counter() - start

            assert index_response.status_code == 202
            assert elapsed < 5.0
            job_id = index_response.json()["job_id"]

            job = (await client.get(f"/jobs/{job_id}")).json()
            assert job["status"] == "completed"
            assert job["progress"]["meetings_indexed"] == TARGET_MEETING_COUNT
            assert job["progress"]["meetings_skipped"] == 0
            assert job["progress"]["segments_created"] > 0

            stats = (await client.get(f"/corpora/{corpus_id}")).json()
            assert stats["meeting_count"] == TARGET_MEETING_COUNT
            assert stats["segment_count"] == job["progress"]["segments_created"]
            assert stats["date_range"] is not None
            assert "Priya Nair" in stats["participants"]

            reindex_response = await client.post(f"/corpora/{corpus_id}/index")
            reindex_job = (await client.get(f"/jobs/{reindex_response.json()['job_id']}")).json()
            assert reindex_job["progress"]["meetings_indexed"] == 0
            assert reindex_job["progress"]["meetings_skipped"] == TARGET_MEETING_COUNT

            decision_density = await _average_density("-decision")
            noise_density = await _average_density("standup")
            assert decision_density > noise_density
        finally:
            await _delete_corpus(corpus_id)


async def test_create_corpus_rejects_nonexistent_path() -> None:
    async with await _client() as client:
        response = await client.post("/corpora", json={"path": "/no/such/directory"})
        assert response.status_code == 400


async def test_create_corpus_is_idempotent_by_path() -> None:
    async with await _client() as client:
        first = await client.post("/corpora", json={"path": str(OUT_DIR)})
        second = await client.post("/corpora", json={"path": str(OUT_DIR)})

        corpus_id = first.json()["corpus_id"]
        try:
            assert second.json()["corpus_id"] == corpus_id
        finally:
            await _delete_corpus(corpus_id)


async def test_get_job_404_for_unknown_id() -> None:
    async with await _client() as client:
        response = await client.get("/jobs/999999")
        assert response.status_code == 404
