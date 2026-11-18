import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceWriter:
    """Appends one JSON object per line to traces/<run_id>.jsonl.

    Every model and tool call in a run writes through this writer so the
    jsonl file is a complete, replayable record of that run.
    """

    def __init__(self, trace_dir: Path, run_id: str) -> None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        self._path = trace_dir / f"{run_id}.jsonl"

    def write(self, event: str, **payload: Any) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **payload,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    @property
    def path(self) -> Path:
        return self._path
