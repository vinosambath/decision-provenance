"""LLM-generated synthetic meeting corpus.

Ground truth is authored by hand in corpus/truth/*.yaml; this script turns it
into transcripts. Unlike a templated generator, the model is only told the
output shape (see prompts.SYSTEM_PROMPT) — the dialogue itself, including
whether it mentions what we expect it to, is left organic on purpose. That
makes this a real test of the search and extraction pipeline rather than a
fixture that only ever says what it's told to say. It also means output is
not reproducible run to run, so we generate once and commit corpus/out/.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from corpus import llm, prompts
from corpus.truth import Company, Trail, load_company, load_trails

OUT_DIR = Path(__file__).parent / "out"
TARGET_MEETING_COUNT = 30
_NOISE_PADDING_DAYS = 14
_NOISE_KINDS = ["standup", "one-on-one", "retro", "design review", "incident review", "planning"]


def generate(out_dir: Path = OUT_DIR, seed: int = 42) -> list[Path]:
    rng = random.Random(seed)
    company = load_company()
    trails = load_trails()

    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.glob("*.md"):
        existing.unlink()

    written: list[Path] = []
    for trail in trails:
        written += _write_trail_meetings(company, trail, out_dir)

    noise_count = max(0, TARGET_MEETING_COUNT - len(written))
    written += _write_noise_meetings(company, noise_count, trails, rng, out_dir)

    return written


def _write_trail_meetings(company: Company, trail: Trail, out_dir: Path) -> list[Path]:
    paths = [
        _generate_meeting(
            out_dir, trail.exploratory_date, f"{trail.id}-exploration",
            prompts.trail_exploratory_prompt(company, trail),
        ),
        _generate_meeting(
            out_dir, trail.decision_date, f"{trail.id}-decision",
            prompts.trail_decision_prompt(company, trail),
        ),
    ]
    if trail.revision:
        paths.append(
            _generate_meeting(
                out_dir, trail.revision.date, f"{trail.id}-revision",
                prompts.trail_revision_prompt(company, trail),
            )
        )
    return paths


def _write_noise_meetings(
    company: Company, count: int, trails: tuple[Trail, ...], rng: random.Random, out_dir: Path
) -> list[Path]:
    teams: dict[str, list[str]] = {}
    for person in company.people:
        teams.setdefault(person.team, []).append(person.name)

    start, end = _noise_date_range(trails)
    used_dates: set[date] = set()
    current = start

    paths: list[Path] = []
    for i in range(count):
        current += timedelta(days=rng.randint(2, 7))
        if current > end:
            current = start + timedelta(days=rng.randint(1, 3))
        while current in used_dates:
            current += timedelta(days=1)
        used_dates.add(current)

        kind = _NOISE_KINDS[i % len(_NOISE_KINDS)]
        team_name = rng.choice(list(teams))
        roster = teams[team_name]
        attendee_count = 2 if kind == "one-on-one" else min(len(roster), rng.randint(3, 6))
        attendees = rng.sample(roster, k=attendee_count)

        slug = f"{team_name.lower()}-{kind.replace(' ', '-')}"
        prompt = prompts.noise_prompt(company, kind, attendees, current.isoformat())
        paths.append(_generate_meeting(out_dir, current, slug, prompt))

    return paths


def _generate_meeting(out_dir: Path, meeting_date: date, slug: str, user_prompt: str) -> Path:
    raw = llm.complete(prompts.SYSTEM_PROMPT, user_prompt)
    text = _strip_code_fence(raw)
    path = out_dir / f"{meeting_date.isoformat()}_{slug}.md"
    path.write_text(text, encoding="utf-8")
    return path


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _noise_date_range(trails: tuple[Trail, ...]) -> tuple[date, date]:
    all_dates = [t.exploratory_date for t in trails] + [t.decision_date for t in trails]
    all_dates += [t.revision.date for t in trails if t.revision]
    padding = timedelta(days=_NOISE_PADDING_DAYS)
    return min(all_dates) - padding, max(all_dates) + padding


if __name__ == "__main__":
    paths = generate()
    print(f"wrote {len(paths)} meetings to {OUT_DIR}")
