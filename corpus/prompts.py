"""Prompt construction for the LLM-generated synthetic corpus.

The only thing we constrain is the output shape, so the ingest adapters from
step 01 can decode it. Everything else — phrasing, tangents, interruptions,
who dominates the conversation, whether anyone even mentions the thing we
expect them to — is left to the model. That's deliberate: a corpus that only
ever says exactly what the ground truth says is a worse test of the search
and extraction pipeline than one that behaves like a real meeting.
"""

from __future__ import annotations

from corpus.truth import Company, Trail

SYSTEM_PROMPT = """\
You write realistic synthetic transcripts of internal engineering meetings, \
used as test data for a decision-search tool. Write natural, organic \
dialogue: interruptions, tangents, hedging, disagreement, personality, \
realistic workplace banter. Do not sound scripted or like a recitation of \
bullet points — real engineers go on tangents, crack jokes, talk over each \
other, and don't always land exactly where you'd expect.

Output ONLY the transcript, in exactly this shape and nothing else:

---
title: <short meeting title>
date: <YYYY-MM-DD>
participants: [<Full Name>, <Full Name>, ...]
---

<Full Name>: <line of dialogue>
<Full Name>: <line of dialogue>
...

Rules:
- Every dialogue line starts with a participant's full name, then a colon.
- No stage directions, no timestamps, no section headers beyond the front
  matter shown above.
- 15-30 dialogue lines.
- `participants` should list everyone who actually speaks."""


def trail_exploratory_prompt(company: Company, trail: Trail) -> str:
    alt_lines = "\n".join(f"- {a.name}: a possible concern is \"{a.rejected_because}\"" for a in trail.alternatives)
    assumption_hint = (
        f'Someone might mention, in passing, something like: "{trail.assumptions[0].claim}" '
        f"(attributed to {trail.assumptions[0].stated_by}, if it comes up naturally)."
        if trail.assumptions
        else ""
    )
    return f"""\
Company: {company.name}, which builds {company.product}.
Meeting date: {trail.exploratory_date}
Likely attendees: {", ".join(trail.participants)} — feel free to have one \
person dominate the conversation, someone join a few minutes late, or a line \
get cut off and repeated.

Context for you to dramatize (don't recite this, have the team actually \
discuss it in their own words): the team is early in exploring options for \
{trail.topic}. They're actively weighing {trail.decision_name} against a \
few alternatives:
{alt_lines}

{assumption_hint}

Nothing is decided yet — the meeting should end without a clear commitment, \
more like "let's keep digging" than a final call."""


def trail_decision_prompt(company: Company, trail: Trail) -> str:
    alt_lines = "\n".join(f"- {a.name} was ruled out: {a.rejected_because}" for a in trail.alternatives)
    assumption_hint = ""
    if len(trail.assumptions) > 1:
        a = trail.assumptions[1]
        assumption_hint = f'Near the end, {a.stated_by} raises a caveat along the lines of: "{a.claim}".'

    return f"""\
Company: {company.name}, which builds {company.product}.
Meeting date: {trail.decision_date}
Attendees: {", ".join(trail.participants)}

Context for you to dramatize: the team is wrapping up a decision about \
{trail.topic}. Over the course of this meeting they rule out the \
alternatives below and land on {trail.decision_name}:
{alt_lines}

{assumption_hint}

The meeting should end with an unambiguous commitment to {trail.decision_name} \
— in the team's own words, not necessarily the exact phrasing above."""


def trail_revision_prompt(company: Company, trail: Trail) -> str:
    assert trail.revision is not None
    return f"""\
Company: {company.name}, which builds {company.product}.
Meeting date: {trail.revision.date}
Attendees: {", ".join(trail.participants)}

Context for you to dramatize: weeks or months after committing to \
{trail.decision_name} for {trail.topic}, the team revisits it. By the end of \
the meeting, they land on an update along these lines (in their own words, \
not verbatim): "{trail.revision.text}\""""


def noise_prompt(company: Company, kind: str, attendees: list[str], meeting_date: str) -> str:
    return f"""\
Company: {company.name}, which builds {company.product}.
Meeting type: {kind}
Date: {meeting_date}
Attendees: {", ".join(attendees)}

Context: this is a completely ordinary {kind}, unrelated to any major \
company decision. Make it feel like a real, slightly messy {kind} — status \
updates, small complaints, a tangent or two, nothing momentous."""
