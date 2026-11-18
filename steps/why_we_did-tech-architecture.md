# Decision Provenance — Architecture

Ask *"why did we choose Kafka?"* and get back a reconstructed trail: what was decided, when, in which meeting, who was in the room, which alternatives were rejected and for what stated reason, and — the part that matters — **what was assumed at the time**, flagged where it looks checkable today.

Input: a folder of meeting transcripts. Output: `brief.md`, every sentence of which carries a `meeting:line` citation.

Design rule: **the transcripts are the entire environment.** No vector store, no embeddings, no semantic index. Plain text search plus five read tools. Storage and the API shape are in `10-tech-architecture.md`; what follows is the agent design.

---

## 1. Why this is not a search problem

The naive version — embed 200 transcripts, cosine-similarity the question, summarise the top 5 — fails on four specific things, and those four things *are* the project:

**The decision meeting often doesn't name the decision.** By the time the team commits, they've been saying "the log thing" for three weeks. Meanwhile the meeting that says "Kafka" forty times is the exploratory one from two months earlier where nothing was decided. Semantic similarity ranks the loud meeting first, every time.

**The alternatives are only named where they're rejected.** "Why Kafka" is answered in the meeting that says *Kinesis*, *RabbitMQ*, *SQS*. Retrieval that only chases the chosen option never reaches the reasoning.

**Decisions are revised quietly.** A later meeting narrows scope, adds a condition, or reverses it outright without ever restating the original. A summariser reading top-5-by-similarity produces a confident, stale answer.

**Attribution is the failure mode with teeth.** A wrong code-review finding costs a reviewer five minutes. Telling a team that Priya pushed for Kafka when she argued against it is a different category of wrong, and it is exactly what an LLM does when a transcript has crosstalk and ambiguous diarization.

So: structured extraction with typed signals, temporal ordering, blind verification of every attribution, and a system that is allowed to say *"I can't find it, and here's the shaped hole where it should be."*

---

## 2. Two phases

### Offline, once per corpus

```
transcripts/ → [normalize] → [segment] → [mark] → Postgres (segments table)
```

- **normalize** — adapters for vtt / srt / json / markdown (Granola, Otter, Fireflies exports). Everything becomes one line-numbered plaintext per meeting plus a metadata header: `id`, `date`, `title`, `participants`. Line numbers are load-bearing — they're the citation anchor, the same role `file:line` plays in a code reviewer.
- **segment** — split on topic shift, not fixed windows. Cheap heuristic first (speaker-turn density, agenda markers, long pauses); a segment is 2–15 minutes of talk.
- **mark** — pure lexical pass, no model. Tag every segment with a **decision-density score** from a commitment lexicon: *let's go with, we're committing, final call, I'll take that action, decided, locked, we're not doing, park it*. Also tag objection and alternative markers (*instead of, we looked at, my concern is, the problem with*).

This is the cheap trick that makes retrieval work. Decision-density is a *corpus-independent* prior: it is high exactly where commitments live and low in status updates, regardless of topic. One `rg` pass over 200 meetings, a few seconds, no tokens.

### Query time

```
          "why did we choose Kafka?"
                     |
               [expander]            1 cheap call
                     |                terms + likely alternatives + actors + date hints
               [retrieve]            BM25 × decision-density boost → top K segments
                     |
      +--------+--------+--------+
      |        |        |        |
   [extr]   [extr]   [extr]   [extr]   K tool-loop agents, parallel
    |↕tools  |↕tools  |↕tools  |↕tools
      +--------+--------+--------+
                     |
              [synthesizer]         1 call — order by date, build trail, mark gaps
                     |
      +--------+--------+
      |        |        |
    [ver]    [ver]    [ver]          M blind tool-loop agents, parallel
      +--------+--------+
                     |
           brief.md + traces/<run>.jsonl
```

Four roles, two of them tool loops. Structurally the same spine as the review crew — the difficulty has moved from *reading code* to *reading people*.

---

## 3. The expander earns its call

One cheap model call, and it is the highest-leverage prompt in the system. From *"why did we choose Kafka?"* it produces:

```json
{
  "direct":       ["Kafka", "MSK", "kafka cluster"],
  "paraphrase":   ["message bus", "event log", "the queue", "streaming layer"],
  "alternatives": ["Kinesis", "RabbitMQ", "SQS", "Pulsar", "Redis streams"],
  "actors":       ["platform team", "infra"],
  "date_hint":    null
}
```

`alternatives` is the point. Generated from the model's own knowledge of the option space, it reaches the rejection meeting that never says "Kafka" at all. Retrieval then scores segments against the union, with decision-density as a multiplier — so the exploratory meeting that says "Kafka" forty times but commits to nothing ranks *below* the terse segment that says "fine, we'll go with the log one, Kinesis caps us at five consumers."

Retrieval returns top K = 20–30 **segments**, not meetings, each with its meeting metadata. Date-diverse: cap how many segments one meeting can contribute, so a single long meeting can't crowd out the trail.

---

## 4. Tools

Five functions over the `segments` table and the normalized transcripts. The whole tool layer is ~100 lines.

```python
read_segment(meeting_id, seg_id)                  -> str      # line-numbered
read_window(meeting_id, around_line, n=40)        -> str      # crosstalk before/after
search(pattern, meeting_ids=None, max_hits=40)    -> list[Hit]
meeting_meta(meeting_id)                          -> Meta     # date, title, participants
list_meetings(after=None, before=None, participant=None) -> list[Meta]
```

`read_window` exists because the sentence that decides something is almost never self-contained — the reason sits ninety seconds earlier and the objection forty seconds later.

`list_meetings` is what lets an agent notice absence: *"commitment language appears on Mar 19 referring to a decision as already made; there are no transcripts between Mar 3 and Mar 19."* A system that can see its own corpus holes is the difference between a toy and something a staff engineer presents.

Every result capped and truncated.

---

## 5. Data contracts

Everything between agents is a `Signal`. Get the typology right and synthesis is plumbing.

```python
class Signal(BaseModel):
    meeting_id: str
    date: date
    speaker: str | None               # None when diarization is ambiguous — never guessed
    lines: tuple[int, int]            # exact span, the citation anchor
    kind: Literal[
        "proposal",                   # someone puts an option on the table
        "objection",                  # stated concern against an option
        "alternative_rejected",       # option + the reason it was dropped
        "assumption",                 # a claim about the world taken as true
        "commitment",                 # the decision itself
        "revision",                   # later change to a prior decision
        "context",                    # relevant but none of the above
    ]
    subject: str                      # the option/decision this is about
    claim: str                        # one sentence, paraphrased
    quote: str                        # verbatim, short, must appear in `lines`
    confidence: float
```

```python
class Assumption(BaseModel):
    claim: str
    stated_by: str | None
    meeting_id: str; date: date; lines: tuple[int, int]
    kind: Literal["capability", "forecast", "constraint", "cost", "org"]
    checkable: bool                   # is this falsifiable today?
    how_to_check: str | None          # "check Kinesis consumer limits in current docs"
```

```python
class Trail(BaseModel):
    question: str
    decision: str | None
    decided_on: date | None
    decided_in: str | None
    participants: list[str]
    alternatives: list[Alternative]   # name, rejected_because, signals
    assumptions: list[Assumption]
    revisions: list[Signal]
    contradictions: list[Contradiction]   # two signals that cannot both be true
    gaps: list[str]
    confidence: Literal["high", "medium", "low", "not-found"]
```

**Enforced in code, not in a prompt:** any field of the trail with zero backing signals is dropped before the brief is rendered. A sentence without a citation cannot reach the output. That single rule removes most of the hallucination surface, and it is a five-line function.

---

## 6. Agent roles

| Agent | Shape | Job |
|---|---|---|
| **expander** | 1 call, cheap model | Question → search terms, likely alternatives, actors, date hints. §3. |
| **extractor** | tool loop, K parallel | One candidate segment. Read it, pull surrounding window and related segments via tools, emit `list[Signal]`. Returns empty freely — most candidates are noise, and saying so is the correct answer. |
| **synthesizer** | 1 call, no tools | All signals, sorted by date. Build the trail. Resolve nothing it cannot resolve: conflicting signals become `contradictions`, missing links become `gaps`. |
| **verifier** | tool loop, M parallel, **blind** | Per claim: given only the claim text and its line refs — never the extractor's reasoning — re-read the lines and rule `keep` / `drop` / `fix_attribution`. |

The verifier is again the piece worth building, and here it has a sharper job than in the code reviewer: **attribution**. It checks three things independently — does the quote exist at those lines; does the quote support the claim; is the named speaker the one who said it. The third catches the failure that does real damage in a meeting-provenance tool, and `fix_attribution` (downgrade to `speaker: null`) is usually the right outcome rather than dropping an otherwise good signal.

### Budget

- **6 tool calls** / **12k tokens** per extractor, then it must emit or return empty
- **3 tool calls** per verifier
- run-level `RunBudget(max_tokens, max_calls)`; `llm.py` decrements and raises `BudgetExceeded`

K = 25 parallel extractors with no ceiling is one bad expansion away from an expensive afternoon.

---

## 7. The brief

```markdown
## Why Kafka?

**Decided** 2025-03-19, platform sync — Kafka (MSK) as the event backbone.
Confidence: medium. [m-0147:212-231]

**In the room:** Priya (proposed), Daniel, Wei Lin, Ana. [m-0147:1-8]

**Alternatives rejected**
- **Kinesis** — consumer-group limit too low for the fan-out they projected. [m-0141:88-96]
- **RabbitMQ** — no replay; Daniel's requirement for backfill killed it. [m-0141:140-151]
- **SQS** — ordering. Considered briefly, dropped same meeting. [m-0141:160-164]

**Assumptions stated at the time**
- ⚠ *"Kinesis caps at 5 consumers per shard"* — Wei Lin, 2025-03-12. [m-0141:91]
  Capability claim, checkable. **Verify against current limits.**
- ⚠ *"We'll have two platform engineers on this through Q3"* — Priya, 2025-03-19. [m-0147:240]
  Org forecast, checkable. **No longer true?**
- *"Backfill has to replay 30 days"* — Daniel, 2025-03-12. [m-0141:145]

**Revisions**
- 2025-06-04: scope narrowed to the orders topic only; the user-events migration was parked. [m-0203:55-70]

**Contradictions**
- Mar 19 records the decision as final; Apr 02 refers to it as "still being evaluated". [m-0147:228] vs [m-0158:41]

**Gaps**
- No transcript between Mar 03 and Mar 12; the shortlist appears already formed on Mar 12.
```

The ⚠ assumptions block is the feature people remember. Half the time the team's reaction is *"wait, is that still true?"* — which is the entire value proposition, and it falls straight out of typing `assumption` as a first-class signal kind.

---

## 8. Files

```
decision-provenance/
  cli.py                  # provenance index ./meetings
                          # provenance ask "why did we choose Kafka?" --out brief.md
  # file layout: see 10-tech-architecture.md §7
  adapters/               # vtt.py srt.py json.py markdown.py (granola, otter, fireflies)
  retrieve.py             # BM25 + decision-density boost + meeting diversity cap
  tools.py                # the five functions
  llm.py                  # call_agent(prompt, schema, tools). retries, budget, trace.
  models.py               # Signal, Assumption, Trail, Meta, RunBudget
  agents/
    expander.py  extractor.py  synthesizer.py  verifier.py
  prompts/
    expander.md  extractor.md  synthesizer.md  verifier.md
  corpus/
    generate.py           # ground truth → transcripts
    truth/trail_*.yaml    # planted decision trails
    out/                  # 200 generated transcripts, committed
  evals/
    run_eval.py
  traces/                 # one jsonl per run, gitignored
```

Prompts in files. The extractor prompt alone will see thirty revisions.

---

## 9. The synthetic corpus — generate truth first

This is a genuine piece of the engineering, not a fixture, and it's what makes the eval possible at all.

**Order matters: write the ground truth, then render transcripts from it.** The reverse — generate transcripts then label them — is weeks of manual work and the labels are wrong.

1. **Company** — fictional 14-person eng org: names, roles, two teams, a product. One YAML.
2. **Trails** — 12–15 decision trails as structured truth: the decision, the date, who proposed it, 2–4 alternatives with rejection reasons, 2–4 assumptions (some marked checkable), optional later revision, optional deliberate contradiction.
3. **Render** — each trail is spread across 2–4 meetings in sequence: an exploratory one that names everything and decides nothing, a decision one that commits in half a sentence, sometimes a later one that revises. Generate the transcripts with a model, with realistic damage: crosstalk, one person dominating, "sorry, you cut out", partial sentences, someone joining late.
4. **Noise** — ~150 meetings with no planted decision: standups, retros, 1:1s, incident reviews, and critically **near-miss meetings** that discuss a planted topic at length without deciding anything.
5. **Holes** — delete 2–3 transcripts that the truth says exist. Those are the gap-detection cases.

Ground truth gives recall, precision, attribution and abstention metrics for free, forever.

---

## 10. Eval

| Metric | What it answers |
|---|---|
| **decision-point precision** | Of the meetings named as the decision point, how many are the planted one? The near-miss meetings are the whole test. |
| **attribution precision** | Of statements attributed to a named person, how many are right? ← **headline** |
| **alternative recall** | Planted rejected alternatives surfaced, with the right reason. |
| **assumption recall** | Planted assumptions surfaced; checkable ones correctly flagged. |
| **abstention rate** | On questions with no planted trail, does it say *not-found* instead of inventing one? ← **the number that separates this from a summariser** |
| **gap detection** | On the deleted-transcript cases, does it report the hole? |
| ablations | verifier off/on; decision-density boost off/on; expander alternatives off/on |
| cost | tokens and $ per question |

Target README claims, with real numbers: *"blind verification raised attribution precision from 0.6x to 0.9x at +15% tokens"*, *"decision-density boosting raised decision-point precision from 0.4x to 0.7x at zero model cost"*, *"abstains correctly on 8/10 unanswerable questions."*

That middle claim is the one engineers will respect — it's a retrieval win with no LLM in it.

---

## 11. Known limits — put these in the README

- Decisions made in DMs, hallways, doc comments or PR threads are invisible. The corpus is the ceiling.
- Diarization errors propagate; `speaker: null` is the honest output and the system uses it.
- Tentative language is genuinely ambiguous — "yeah let's probably do Kafka then" is or isn't a commitment depending on who said it and what happened after.
- Many decisions have no moment. They accrete. The trail will show a smear rather than a point, and it should say so.
- Sarcasm, in-jokes and shorthand defeat it. So do meetings conducted in two languages.

Saying this plainly reads as senior. Omitting it reads as a demo.

---

## 12. Two-week slice

| Days | Build |
|---|---|
| 1 | `models.py`, adapters, indexing (normalize + segment + mark). Index a folder, inspect the `segments` rows by hand. |
| 2 | `corpus/generate.py`: 3 trails, 20 meetings. Enough to develop against. |
| 3 | `tools.py`, `llm.py`, **one** extractor as a tool loop on one hand-picked segment. End to end, no retrieval. |
| 4 | Expander + BM25 retrieval + density boost. Now it answers a real question. |
| 5–6 | Parallel fan-out, synthesizer, trail rendering. First usable `brief.md`. |
| 7 | Blind verifier, including `fix_attribution`. |
| 8 | Full corpus: 15 trails, 200 meetings, noise, near-misses, holes. |
| 9–10 | `run_eval.py`, first numbers, ablations. |
| 11 | Budgets, partial-failure handling, traces. |
| 12 | Assumption staleness pass + ⚠ rendering. |
| 13 | README: diagram, numbers, sample brief, 60-second quickstart, §11 limits. |
| 14 | Slack-export adapter, or `--since` incremental indexing. |

Day 4 already answers a question out loud. If the fortnight compresses to ten days, cut from §13 upward and there is still something to push.

---

## 13. Stack

**The stack lives in `10-tech-architecture.md` §9. Short version:**

- Python 3.12, FastAPI, Postgres 16 (text search via `tsvector` + GIN), async SQLAlchemy + asyncpg, Alembic.
- `pydantic` models double as the structured-output schemas for every agent call.
- `claude-agent-sdk` or `openai-agents` for model calls and the tool loop; orchestration written by hand. Not LangGraph, not CrewAI — the loop, the parallel reads and the failure handling are the three things this project exists to demonstrate, and a framework hides exactly those.
- `typer` + `rich` for the CLI, which is a thin client over the same functions the API calls.

> **Note on this document.** It was written for a CLI-only design with a flat file index. The agent design below is unchanged and still correct. Where it mentions a file-based index or a local BM25 library, read `10-tech-architecture.md` instead — that doc is the authority on storage, the API and the build order.

---

## 14. What to cut if time runs short

Cut in this order: the Slack adapter; the contradiction detector (log conflicting signals verbatim instead of reasoning about them); the segmenter (fixed 150-line windows with 30-line overlap); the expander (search the question's own nouns).

Never cut: the blind verifier, the assumption extraction, the abstention path, the eval numbers, the budget ceiling. Those five are the entire differentiation — and the abstention path is the one a staff-level interviewer will push on hardest.
