# Decision Provenance

Ask a plain-English question about a past decision — "why did we choose
Kafka?" — and get back a cited trail reconstructed from your meeting
transcripts: what was decided, who was in the room, which alternatives were
rejected and why, and what was assumed at the time.

Design docs: `why_we_did-tech-architecture.md`. Build steps: `steps/`.

## Quickstart

Requires Python 3.12 and Docker.

```bash
# 1. Start Postgres
docker compose up -d

# 2. Create a virtualenv and install dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env

# 4. Apply database migrations
alembic upgrade head

# 5. Run the API
uvicorn app.main:app --reload --port 8000
```

Check it's up:

```bash
curl http://localhost:8000/health
# {"status":"ok","database":"ok"}
```

API docs: http://localhost:8000/docs

## Tests

```bash
pytest -q
```

## Status

Currently at step 00 (Foundations) of the build — see `steps/00-foundations.md`.
The `/ask` pipeline (ingest, retrieval, agents, brief rendering) is not built
yet.
