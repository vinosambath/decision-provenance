from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

TRUTH_DIR = Path(__file__).parent / "truth"


@dataclass(frozen=True)
class Person:
    name: str
    role: str
    team: str


@dataclass(frozen=True)
class Company:
    name: str
    product: str
    people: tuple[Person, ...]


@dataclass(frozen=True)
class Alternative:
    name: str
    rejected_because: str


@dataclass(frozen=True)
class Assumption:
    claim: str
    stated_by: str
    kind: str
    checkable: bool
    how_to_check: str | None = None


@dataclass(frozen=True)
class Revision:
    date: date
    text: str


@dataclass(frozen=True)
class Trail:
    id: str
    question: str
    topic: str
    decision_name: str
    decision: str
    proposed_by: str
    participants: tuple[str, ...]
    alternatives: tuple[Alternative, ...]
    assumptions: tuple[Assumption, ...]
    exploratory_date: date
    decision_date: date
    revision: Revision | None


def load_company(truth_dir: Path = TRUTH_DIR) -> Company:
    data = yaml.safe_load((truth_dir / "company.yaml").read_text(encoding="utf-8"))
    return Company(
        name=data["name"],
        product=data["product"],
        people=tuple(Person(**person) for person in data["people"]),
    )


def load_trails(truth_dir: Path = TRUTH_DIR) -> tuple[Trail, ...]:
    return tuple(
        _trail_from_dict(yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in sorted(truth_dir.glob("trail_*.yaml"))
    )


def _trail_from_dict(data: dict) -> Trail:
    revision = data.get("revision")
    return Trail(
        id=data["id"],
        question=data["question"],
        topic=data["topic"],
        decision_name=data["decision_name"],
        decision=data["decision"],
        proposed_by=data["proposed_by"],
        participants=tuple(data["participants"]),
        alternatives=tuple(Alternative(**a) for a in data["alternatives"]),
        assumptions=tuple(Assumption(**a) for a in data["assumptions"]),
        exploratory_date=data["exploratory_date"],
        decision_date=data["decision_date"],
        revision=Revision(**revision) if revision else None,
    )
