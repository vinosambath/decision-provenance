# Step 03 — Index

Still no AI calls. This is the last of the "retrieval has to be good before a
model shows up" steps (master doc, §10 note) — segmentation and the
commitment-language score are both pure lexical passes.

## Goal

Turn a folder of transcripts into searchable, scored rows in Postgres:
`POST /corpora` registers a folder, `POST /corpora/{id}/index` reads every
supported file through the step 01 adapters, splits each into segments,
scores each segment for commitment language, and stores the result —
re-indexing is cheap and skips anything unchanged.

## Deliverable

- `app/db_models.py` — `Corpus`, `Meeting`, `Segment`, `Job`. `Segment.search_vector`
  is a Postgres `GENERATED ALWAYS AS (to_tsvector(...)) STORED` column with a
  GIN index — the direct equivalent of the original SQLite-FTS5 design, now
  on Postgres. `Meeting` uses a surrogate integer PK with `(corpus_id,
  external_id)` unique together, since a filename stem is only unique within
  one corpus, not globally.
- `app/ingest/segment.py` — fixed-size line windows (`LineSpan`), 1-indexed,
  no overlap.
- `app/ingest/lexicons.py` — commitment / alternative / objection phrase
  lists and a `score()` function: decision-density (commitment hits per
  line), `has_alternatives`, `has_objection`.
- `app/ingest/mark.py` — glues a `LineSpan` to its score as a `MarkedSegment`.
- `app/indexing.py` — `index_corpus()`: walks a corpus's folder, normalizes
  each file, skips any meeting whose content hash hasn't changed, otherwise
  re-segments, re-marks, and upserts.
- `app/routers/corpora.py`, `app/routers/jobs.py` — the four endpoints below.
- Alembic migration for the four new tables.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/corpora` | Register a folder. Idempotent by path — returns the existing `corpus_id` if already registered. |
| `POST` | `/corpora/{id}/index` | Index it. Returns `job_id`. |
| `GET` | `/corpora/{id}` | Meeting count, segment count, date range, participants. |
| `GET` | `/jobs/{id}` | Job status, structured progress, error. |

## Known simplifications

- **Segmentation is fixed-size windows, not topic-shift detection.** The
  master doc's own §12 cut-list names "fixed 150-line windows, 30-line
  overlap" as the acceptable fallback for this exact feature — here it's
  12-line windows, no overlap, sized for meetings this short (17-33 lines),
  so most meetings split into 2-3 segments rather than one. Real topic-shift
  detection (speaker-turn density, pause length) needs timing data our
  adapters don't currently carry.
- **Idempotency is content-hash only, not mtime+hash.** Mtime was always
  just a fast-path short-circuit before hashing; at this corpus size there's
  no measurable cost to always hashing, so the mtime check added complexity
  without changing behavior.
- **Indexing runs synchronously within the request**, not as a background
  task. The async-job machinery the master doc describes (§5, "Long-running
  work without Celery") is for the 30-90 second `/ask` pipeline in step 09 —
  indexing 30 small files with no model calls finishes in well under a
  second, so a `Job` row is still created and returned (keeping the contract
  stable for when `/ask` needs it for real), but there's no actual async
  dispatch yet.
- **No cleanup of meetings removed from disk.** If a file disappears from
  the corpus folder between indexing runs, its row is left in place rather
  than deleted. Acceptable for now; revisit if it matters once the eval
  corpus (step 10) starts deliberately deleting transcripts.
- **Lexicons are hand-picked, not tuned.** Step 04's retrieval test (planted
  decision meeting in the top 5) and the step 08 ablation table are where
  this actually gets measured — here the bar is just "sensible," not
  "correct."

## Done-when

- `POST /corpora` against `corpus/out` returns a `corpus_id`.
- `POST /corpora/{id}/index` indexes all 30 generated meetings in well under
  5 seconds, and re-running it indexes zero and skips 30.
- `GET /corpora/{id}` reports 30 meetings and a non-zero segment count.
- A decision meeting's segments score measurably higher on decision-density,
  on average, than a noise meeting's segments.
