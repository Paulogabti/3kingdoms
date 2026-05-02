from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import PROGRESS_DIR
from .models import ProgressRecord


def _progress_file(file_hash: str) -> Path:
    return PROGRESS_DIR / f"{file_hash}.jsonl"


def load_progress(file_hash: str) -> dict[int, ProgressRecord]:
    p = _progress_file(file_hash)
    if not p.exists():
        return {}
    records = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = ProgressRecord.model_validate_json(line)
        records[rec.line_number] = rec
    return records


def upsert_record(record: ProgressRecord) -> None:
    records = load_progress(record.file_hash)
    records[record.line_number] = record
    p = _progress_file(record.file_hash)
    with p.open("w", encoding="utf-8") as f:
        for _, rec in sorted(records.items()):
            rec.updated_at = datetime.utcnow()
            f.write(json.dumps(rec.model_dump(mode="json"), ensure_ascii=False) + "\n")
