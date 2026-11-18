# Step 00 — Foundations

Self-contained. No AI calls in this step — see the master doc, §10: retrieval and
plumbing have to be solid before a model enters the picture.

## Goal

A booting FastAPI service with a real Postgres connection, migrations, and the
two cross-cutting primitives every later step depends on: a budget guard and a
trace writer. Nothing domain-specific yet (no `meetings`, `segments`, agents).

## Deliverable

- `pyproject.toml` — Python 3.12, FastAPI, SQLAlchemy 2.x (async) + `asyncpg`,
  Alembic, `pydantic-settings`, `uvicorn`, pytest + pytest-asyncio for dev.
- `docker-compose.yml` — single `postgres:16` service. `docker compose up -d`
  is the entire "install a database" step.
- `app/config.py` — `Settings(BaseSettings)`: `database_url`, model names,
  per-run budget defaults, trace directory. Loaded from `.env`.
- `app/db.py` — async engine, async session factory, a `Base` for future
  declarative models, and a FastAPI dependency (`get_session`) that yields one
  session per request.
- `migrations/` — Alembic wired to the async engine via `Settings`, one
  baseline revision (no tables yet; proves the migration path end to end).
- `app/budget.py` — `RunBudget`: tracks tokens and calls spent against a
  ceiling, raises `BudgetExceeded` the instant either is crossed. No agent
  exists yet to spend from it, but every later agent takes one as a
  constructor argument, so the contract is fixed now.
- `app/trace.py` — `TraceWriter`: appends one JSON object per line to
  `traces/<run_id>.jsonl`. Every later agent call writes through this; fixing
  its shape now means the trace format never has to migrate.
- `app/main.py` — FastAPI app, lifespan context manages the engine's lifecycle
  (dispose on shutdown), routers mounted.
- `app/routers/health.py` — `GET /health` round-trips `SELECT 1` through the
  real session dependency, so a true DB outage shows up as a failed health
  check, not just a missing route.
- `tests/test_health.py` — hits `/health` against a real Postgres (the compose
  service), asserts 200 and a healthy DB status.

## Non-goals (explicitly deferred)

- No `meetings` / `segments` tables — that's step 03 (Index).
- No ingest adapters, no retrieval, no agents, no CLI.
- No auth, no rate limiting — out of scope for the whole project per the
  master doc.

## Done-when

1. `docker compose up -d` starts Postgres with no manual config.
2. `alembic upgrade head` runs clean against a fresh database.
3. `uvicorn app.main:app` boots with no errors.
4. `GET /health` returns `200 {"status": "ok", "database": "ok"}`.
5. Killing the DB container and re-hitting `/health` returns a `503` with
   `{"status": "degraded", "database": "unreachable"}` — the check is real,
   not decorative.
6. `pytest` passes.
