# Step 04 — Retrieval

Last of the AI-free steps. The query here is the user's raw question text —
no query expansion yet. The expander is an AI call (master doc §4.1 / agent-
design doc §3), so it belongs with the rest of the agent pipeline from step
05 onward, not here. Retrieval has to work on the literal question first;
if it can't, no amount of query expansion will save it.

## Goal

Given a corpus_id and a question, return the segments most likely to matter
— ranked by text relevance *multiplied by* commitment-language density, so a
terse decisive segment can outrank a long chatty one that merely mentions the
same words more often (master doc §6, point 1). Capped per meeting so one
long meeting can't fill the whole result list.

## Deliverable

- `app/retrieval/search.py` — `search(session, corpus_id, query, top_k=25,
  meeting_cap=3) -> list[Candidate]`.
  - Relevance: Postgres `websearch_to_tsquery('english', query)` matched
    against `segments.search_vector`, scored with `ts_rank_cd` — this is our
    equivalent of the original design's SQLite-FTS5-BM25 call, swapped onto
    Postgres per `steps/why_we_did-tech-architecture.md` §5's own note that
    this swap should leave everything above the storage layer unchanged.
  - **AND rewritten to OR.** `websearch_to_tsquery` ANDs every term by
    default. Segments are only ~12 lines, so a question's words routinely
    land in *different* segments of the same meeting (e.g. "why did we move
    off **Jenkins**?" → "move" and "jenkins" never co-occur in one segment,
    even though the meeting is exactly the right one) — found this by
    actually running the three planted questions and watching one return
    zero results. Fixed by rewriting the query's top-level `&` into `|`
    before matching (phrase sequences, `<->`, are left alone). This is the
    same recall-over-precision tradeoff the master doc makes deliberately at
    this stage: retrieval casts a wide net, later agents narrow it down.
  - Boost: `score = relevance * (1 + decision_density * DENSITY_BOOST_FACTOR)`.
    Multiplying straight by density (as the prose design doc literally says)
    would zero out every segment with zero commitment language — including
    the alternative-rejection segments that matter just as much as the
    commitment itself. `1 + density * k` amplifies decisive segments without
    discarding merely-relevant ones. `k = 10` is a hand-picked constant, not
    tuned; real tuning is the step 10 ablation's job.
  - Diversity cap: after sorting by score, greedily keep results but skip any
    segment once its meeting has already contributed `meeting_cap` segments.
- `GET /corpora/{id}/search?q=...&top_k=...` — the debug endpoint. Returns
  every candidate with its relevance, density, and final score visible —
  this is what you'd screenshot to show the boost is actually doing
  something, not just asserted in prose.

## Known simplifications

- No query expansion — see above. A query that doesn't share any words with
  the relevant segments (e.g. the alternatives, which the master doc notes
  are "only ever spoken where they're rejected") won't be found yet. That's
  expected; it's exactly what the expander (later) exists to fix.
- The diversity cap is per-meeting, not per-date. Since every meeting in this
  corpus has its own date, capping per meeting already gets most of the
  date-diversity benefit without a separate mechanism.
- `DENSITY_BOOST_FACTOR` is a guess, not a measured constant.

## Done-when

For each of the three planted trail questions (`corpus/truth/trail_*.yaml`'s
`question` field, e.g. "why did we choose Kafka?"), run `search()` against
the indexed corpus — a segment from that trail's `*-decision` meeting is
among the top 5 results.
