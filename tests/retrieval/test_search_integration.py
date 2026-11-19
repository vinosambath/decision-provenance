from sqlalchemy import delete

from app.db import get_session
from app.db_models import Corpus
from app.indexing import index_corpus
from app.retrieval.search import search
from corpus.generate import OUT_DIR
from corpus.truth import load_trails


async def _indexed_corpus_id() -> int:
    async for session in get_session():
        corpus = Corpus(path=str(OUT_DIR))
        session.add(corpus)
        await session.commit()
        await index_corpus(session, corpus)
        return corpus.id
    raise AssertionError("no session yielded")


async def _delete_corpus(corpus_id: int) -> None:
    async for session in get_session():
        await session.execute(delete(Corpus).where(Corpus.id == corpus_id))
        await session.commit()


async def test_planted_decision_meeting_is_in_top_5_for_its_real_question() -> None:
    corpus_id = await _indexed_corpus_id()
    try:
        for trail in load_trails():
            async for session in get_session():
                results = await search(session, corpus_id, trail.question, top_k=5)

            decision_meetings = {c.meeting_external_id for c in results if "-decision" in c.meeting_external_id}
            assert any(trail.id in m for m in decision_meetings), (
                f"trail '{trail.id}': question {trail.question!r} did not surface its decision "
                f"meeting in the top 5. Got: {[c.meeting_external_id for c in results]}"
            )
    finally:
        await _delete_corpus(corpus_id)


async def test_search_with_no_lexical_overlap_returns_nothing() -> None:
    # OR semantics (see search.py) mean a query matches if ANY term does —
    # so a coincidental single-word overlap (e.g. "budget" showing up in an
    # unrelated pricing discussion) legitimately surfaces a result. That's
    # the intended wide-net behavior, not a bug. What should still hold:
    # a query with zero lexical overlap with the corpus at all returns nothing.
    corpus_id = await _indexed_corpus_id()
    try:
        async for session in get_session():
            results = await search(session, corpus_id, "xyzzyplugh zorbnaxqix", top_k=5)
        assert results == []
    finally:
        await _delete_corpus(corpus_id)


async def test_meeting_cap_is_respected_for_a_broad_query() -> None:
    corpus_id = await _indexed_corpus_id()
    try:
        async for session in get_session():
            results = await search(session, corpus_id, "team meeting update", top_k=25, meeting_cap=2)

        counts: dict[int, int] = {}
        for candidate in results:
            counts[candidate.meeting_id] = counts.get(candidate.meeting_id, 0) + 1
        assert all(count <= 2 for count in counts.values())
    finally:
        await _delete_corpus(corpus_id)
