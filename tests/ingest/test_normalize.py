from datetime import date
from pathlib import Path

import pytest

from app.ingest.normalize import UnsupportedTranscriptFormat, normalize_file

VTT_SAMPLE = """WEBVTT

00:00:00.000 --> 00:00:04.000
Priya: Let's go with Kafka.

00:00:04.000 --> 00:00:08.000
<v Daniel>Sounds good to me.</v>
"""

SRT_SAMPLE = """1
00:00:00,000 --> 00:00:05,000
Wei Lin: Kinesis caps us at five consumers per shard.

2
00:00:05,000 --> 00:00:09,000
Daniel: Backfill has to replay 30 days.
"""

JSON_SAMPLE = """{
  "title": "Platform Sync",
  "date": "2025-03-19",
  "participants": ["Priya", "Daniel", "Wei Lin", "Ana"],
  "segments": [
    {"speaker": "Priya", "text": "Let's go with Kafka."},
    {"speaker": "Daniel", "text": "Sounds good."}
  ]
}
"""

MARKDOWN_SAMPLE = """---
title: Platform Sync
date: 2025-03-19
participants: [Priya, Daniel]
---

Priya: Let's go with Kafka.
Daniel: Sounds good.
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_vtt_resolves_metadata_from_filename_and_speakers(tmp_path: Path) -> None:
    path = _write(tmp_path, "2025-03-19_platform-sync.vtt", VTT_SAMPLE)

    meeting = normalize_file(path)

    assert meeting.title == "Platform Sync"
    assert meeting.date == date(2025, 3, 19)
    assert meeting.participants == ("Priya", "Daniel")
    assert [line.text for line in meeting.lines] == [
        "Let's go with Kafka.",
        "Sounds good to me.",
    ]


def test_srt_resolves_speakers_with_multi_word_names(tmp_path: Path) -> None:
    path = _write(tmp_path, "2025-03-12_kafka-options.srt", SRT_SAMPLE)

    meeting = normalize_file(path)

    assert meeting.title == "Kafka Options"
    assert meeting.date == date(2025, 3, 12)
    assert meeting.participants == ("Wei Lin", "Daniel")


def test_json_uses_embedded_metadata_over_filename(tmp_path: Path) -> None:
    path = _write(tmp_path, "m-0147.json", JSON_SAMPLE)

    meeting = normalize_file(path)

    assert meeting.title == "Platform Sync"
    assert meeting.date == date(2025, 3, 19)
    assert meeting.participants == ("Priya", "Daniel", "Wei Lin", "Ana")
    assert len(meeting.lines) == 2


def test_markdown_parses_front_matter(tmp_path: Path) -> None:
    path = _write(tmp_path, "notes.md", MARKDOWN_SAMPLE)

    meeting = normalize_file(path)

    assert meeting.title == "Platform Sync"
    assert meeting.date == date(2025, 3, 19)
    assert meeting.participants == ("Priya", "Daniel")


def test_rendered_output_is_one_indexed_and_numbered(tmp_path: Path) -> None:
    path = _write(tmp_path, "2025-03-19_platform-sync.vtt", VTT_SAMPLE)

    rendered = normalize_file(path).rendered()
    lines = rendered.split("\n")

    assert lines[0].startswith("1 | Priya: Let's go with Kafka.")
    assert lines[1].startswith("2 | Daniel: Sounds good to me.")


def test_content_hash_is_stable_and_sensitive_to_text(tmp_path: Path) -> None:
    path_a = _write(tmp_path, "2025-03-19_platform-sync.vtt", VTT_SAMPLE)
    path_b = _write(tmp_path, "copy.vtt", VTT_SAMPLE)
    changed = VTT_SAMPLE.replace("Kafka", "Kinesis")
    path_c = _write(tmp_path, "changed.vtt", changed)

    hash_a = normalize_file(path_a).content_hash
    hash_b = normalize_file(path_b).content_hash
    hash_c = normalize_file(path_c).content_hash

    assert hash_a == hash_b
    assert hash_a != hash_c


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "transcript.txt", "whatever")

    with pytest.raises(UnsupportedTranscriptFormat):
        normalize_file(path)
