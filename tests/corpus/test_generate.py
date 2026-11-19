"""Smoke tests over the committed, LLM-generated corpus in corpus/out/.

These do NOT call the LLM — generation is a one-time, non-deterministic,
paid operation (see corpus/generate.py), so tests validate the already-
generated, committed output instead of regenerating it. Checks here are
deliberately loose: content is organic, so we don't assert exact phrasing,
only that the format is decodable and that proper nouns (tech/product names,
which are unlikely to get paraphrased away) show up where expected. Stricter
semantic validation is deferred to the eval work in a later step.
"""

from pathlib import Path

from app.ingest.normalize import normalize_file
from corpus.generate import OUT_DIR, TARGET_MEETING_COUNT
from corpus.truth import load_trails


def _meeting_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _file_for(paths: list[Path], contains: str) -> Path:
    for path in paths:
        if contains in path.stem:
            return path
    raise AssertionError(f"no generated file matched '{contains}' in {[p.name for p in paths]}")


def _core_name(name: str) -> str:
    """Strips a parenthetical qualifier, e.g. 'Kafka (MSK)' -> 'Kafka'.

    Decision names are proper nouns the model has no reason to paraphrase,
    but it isn't obliged to repeat a parenthetical the way the ground truth
    phrases it.
    """
    return name.split(" (")[0]


def test_corpus_has_the_target_meeting_count() -> None:
    paths = sorted(OUT_DIR.glob("*.md"))
    assert len(paths) == TARGET_MEETING_COUNT


def test_every_generated_file_round_trips_through_normalize() -> None:
    for path in OUT_DIR.glob("*.md"):
        meeting = normalize_file(path)
        assert meeting.line_count > 0
        assert meeting.date is not None
        assert len(meeting.participants) > 0


def test_each_trail_has_an_exploration_and_decision_meeting() -> None:
    paths = list(OUT_DIR.glob("*.md"))
    for trail in load_trails():
        _file_for(paths, f"{trail.id}-exploration")
        _file_for(paths, f"{trail.id}-decision")
        if trail.revision:
            _file_for(paths, f"{trail.id}-revision")


def test_decision_meetings_mention_the_decision() -> None:
    # Only the decision name is asserted verbatim: it's the one proper noun
    # the model has no reason to paraphrase away. Alternative names and
    # rejection reasons are left to the model's own wording by design (see
    # module docstring), so they aren't asserted here.
    paths = list(OUT_DIR.glob("*.md"))
    for trail in load_trails():
        text = _meeting_text(_file_for(paths, f"{trail.id}-decision"))
        assert _core_name(trail.decision_name) in text


def test_exploratory_meetings_are_substantial() -> None:
    paths = list(OUT_DIR.glob("*.md"))
    for trail in load_trails():
        meeting = normalize_file(_file_for(paths, f"{trail.id}-exploration"))
        assert meeting.line_count >= 10
