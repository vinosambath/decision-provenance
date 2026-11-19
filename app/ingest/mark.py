from __future__ import annotations

from dataclasses import dataclass

from app.ingest.lexicons import score
from app.ingest.segment import LineSpan


@dataclass(frozen=True)
class MarkedSegment:
    start_line: int
    end_line: int
    text: str
    decision_density: float
    has_alternatives: bool
    has_objection: bool


def mark(span: LineSpan) -> MarkedSegment:
    decision_density, has_alternatives, has_objection = score(span.text)
    return MarkedSegment(
        start_line=span.start_line,
        end_line=span.end_line,
        text=span.text,
        decision_density=decision_density,
        has_alternatives=has_alternatives,
        has_objection=has_objection,
    )
