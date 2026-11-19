# Step 02 — Synthetic corpus v1

Ground truth written first, transcripts rendered from it second — never the
other way around. That ordering is what makes every later eval metric
(precision, recall, abstention) free and permanent instead of a weeks-long
manual labelling exercise.

Unlike steps 00–01, this step does make model calls — but only to generate
test fixtures, not as part of the running application. The master doc's
"steps 00–04 are AI-free" rule is about the app's own request path; a one-time,
offline corpus build is a different thing.

## Goal

A corpus that's actually a meaningful test of the pipeline, not a fixture that
only ever says what it's told to say. The only thing we constrain is the
*output shape* (front matter + `Speaker: text` lines, so the step 01 markdown
adapter can decode it) — the content itself, phrasing, tangents, jokes,
whether a fact gets mentioned at all, is left to the model. A templated/
deterministic generator was tried first and discarded: it was reproducible
but repetitive, and repetitive transcripts make retrieval artificially easy.

## Deliverable

- `corpus/truth/company.yaml` — a fictional 14-person engineering org (two
  teams, roles, one product).
- `corpus/truth/trail_*.yaml` — 3 decision trails as structured truth: the
  decision, who proposed it, 2–3 alternatives with rejection reasons, 2
  assumptions, and a revision for two of the three.
- `corpus/truth.py` — loads both into typed dataclasses (`Company`, `Trail`,
  `Alternative`, `Assumption`, `Revision`).
- `corpus/prompts.py` — one shared system prompt fixing the output shape, and
  per-meeting-kind user prompts that hand the model *context to dramatize*,
  explicitly telling it not to recite the ground truth verbatim.
- `corpus/llm.py` — thin OpenAI client wrapper, model/key from `Settings`.
- `corpus/generate.py` — for each trail: an exploratory meeting, a decision
  meeting, and a revision meeting where one exists; padded out with generic
  noise meetings (standups, 1:1s, retros, design reviews, incident reviews,
  planning) across six rotating kinds, to 30 meetings total.
- `corpus/out/*.md` — the 30 generated transcripts, committed. Generation is
  **not** deterministic (real model calls) — this is why the output is
  committed rather than regenerated on demand; `python -m corpus.generate`
  reruns it and overwrites `corpus/out/` if the ground truth changes.

## What's deliberately not checked here

Because content is organic, the committed tests (`tests/corpus/`) only check
structural things: file count, that every file round-trips through the step
01 adapter, that each trail has its expected meetings, and that the decision
name itself (a proper noun the model has little reason to paraphrase away)
shows up in the right meeting. They do **not** assert that alternatives,
rejection reasons, or assumptions appear verbatim — in practice the model
mostly does include them in its own words, but asserting exact phrasing would
fight the whole point of generating organic content. Whether the *pipeline*
(steps 04–08) can actually find and attribute these facts correctly, despite
paraphrasing, crosstalk, and noise, is exactly what the step 10 eval is for —
that's where real precision/recall/attribution numbers belong, not here.

## Done-when

- `python -m corpus.generate` writes 30 `.md` files to `corpus/out/`.
- Every generated file round-trips cleanly through
  `app.ingest.normalize.normalize_file` with no parse errors.
- Each trail has an exploration and decision meeting (and a revision meeting
  where planted), and the decision meeting names the decision made.
