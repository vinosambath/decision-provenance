from __future__ import annotations

COMMITMENT_PHRASES = (
    "let's go with",
    "we're going with",
    "going with",
    "we'll go with",
    "let's do it",
    "full steam ahead",
    "lock it in",
    "locked in",
    "final call",
    "decided",
    "we've decided",
    "committing to",
    "commit to",
    "sounds like a plan",
    "we're not doing",
    "park it",
    "parked",
    "i'll take the action",
    "i'll take that action",
    "moving forward with",
)

ALTERNATIVE_MARKERS = (
    "instead of",
    "what about",
    "we looked at",
    "alternative",
    "considered",
    "ruled out",
    "is out",
)

OBJECTION_MARKERS = (
    "my concern is",
    "the problem with",
    "worried about",
    "worry",
    "concern",
    "risk",
    "doesn't make sense",
    "biggest worry",
)


def score(text: str) -> tuple[float, bool, bool]:
    """Scores one segment's text: (decision_density, has_alternatives, has_objection).

    decision_density is commitment-phrase hits per line — a corpus-independent
    prior that's high where commitments live and low in status updates,
    regardless of topic (master doc §6).
    """
    lowered = text.lower()
    line_count = text.count("\n") + 1

    commitment_hits = sum(lowered.count(phrase) for phrase in COMMITMENT_PHRASES)
    has_alternatives = any(marker in lowered for marker in ALTERNATIVE_MARKERS)
    has_objection = any(marker in lowered for marker in OBJECTION_MARKERS)

    return commitment_hits / line_count, has_alternatives, has_objection
