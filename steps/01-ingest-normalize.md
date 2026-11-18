# Step 01 — Ingest & normalize

No AI calls. No database writes. Pure parsing — turn whatever a transcript
export looks like into one consistent, line-numbered shape in memory.

## Goal

Four adapters (`.vtt`, `.srt`, `.json`, `.md`) that each read a raw transcript
file and emit the same `ParsedTranscript` contract, plus an orchestrator that
resolves the metadata any individual file is missing (date/title from the
filename, participants from the set of speakers seen) into one
`NormalizedMeeting`.

Line numbers are the citation anchor for the rest of the project — a later
step cites `m-0147:212-231`, and that span has to point at exactly the same
line both now and after re-indexing. Getting the line-numbering rule fixed
here, before anything depends on it, is the point of doing this step in
isolation.

## Deliverable

- `app/ingest/models.py` — `NormalizedLine` (speaker, text), `ParsedTranscript`
  (what one adapter can pull from a single file: lines plus whatever metadata
  that format happens to carry), `NormalizedMeeting` (the resolved result:
  id, path, title, date, participants, line-numbered `rendered()` text,
  `line_count`, `content_hash`).
- `app/ingest/adapters/vtt.py` — WebVTT cues; supports both `<v Speaker>` voice
  tags and a plain `Speaker: text` convention, since real exports use either.
- `app/ingest/adapters/srt.py` — SubRip blocks (index / timestamp / text).
- `app/ingest/adapters/json_transcript.py` — a JSON shape with explicit
  `title`, `date`, `participants`, and a `segments: [{speaker, text}]` list —
  the one format where metadata doesn't have to be inferred.
- `app/ingest/adapters/markdown.py` — YAML-ish front matter (`title`, `date`,
  `participants: [...]`) over a body of `Speaker: text` lines.
- `app/ingest/normalize.py` — `normalize_file(path) -> NormalizedMeeting`.
  Dispatches on suffix; fills in whatever the adapter didn't supply: title and
  date parsed from a `YYYY-MM-DD_slug` filename convention, participants from
  first-seen speaker order if the format has no explicit list.

## Known simplifications (acceptable for this step, revisit if real exports disagree)

- vtt/srt cue identifiers are assumed absent or purely numeric; no attempt to
  merge multi-line cues into one logical turn.
- Speaker labels are recognized by a `Name: text` prefix regex — diarization
  quality is whatever the export already encodes, this step doesn't improve it.
- Markdown front matter parsing is hand-rolled (no PyYAML dependency) and only
  understands flat scalars and one-line `[a, b, c]` lists — enough for the
  metadata fields here, not a general YAML parser.

## Done-when

A real file in each of the four formats becomes a `NormalizedMeeting` with:
clean 1-indexed numbered text, the right title, the right date, and the right
participant list — whether that metadata was embedded in the file or inferred
from the filename and the speakers who appear.
