from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import ParsedLine, ProgressRecord


def export_translated_file(
    source_file: Path,
    output_dir: Path,
    lines: list[ParsedLine],
    progress_map: dict[int, ProgressRecord],
    allow_pending: bool = True,
) -> tuple[Path, Path, dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_txt = output_dir / f"{source_file.stem}.pt-BR.txt"
    out_report = output_dir / f"{source_file.stem}.translation_report.json"

    report = {
        "total_lines": len(lines), "translated_lines": 0, "pending_lines": 0,
        "error_lines": 0, "skipped_lines": 0, "validation_passed": False,
        "list_of_errors": [], "created_at": datetime.utcnow().isoformat(),
    }

    out_lines = []
    for pl in lines:
        rec = progress_map.get(pl.line_number)
        if not pl.has_separator:
            report["skipped_lines"] += 1
            out_lines.append(pl.raw_line)
            continue
        if rec and rec.status == "translated" and rec.portuguese_translation:
            report["translated_lines"] += 1
            translated = rec.portuguese_translation
        elif rec and rec.status == "error":
            report["error_lines"] += 1
            report["list_of_errors"].append({"line": pl.line_number, "message": rec.error_message})
            translated = pl.english_part
        else:
            report["pending_lines"] += 1
            translated = pl.english_part
        if (report["pending_lines"] or report["error_lines"]) and not allow_pending:
            raise RuntimeError("Há linhas pendentes/erro, exportação bloqueada.")
        out_lines.append(f"{pl.chinese_part}|{translated}{pl.line_ending}")

    out_txt.write_text("".join(out_lines), encoding="utf-8")
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_txt, out_report, report
