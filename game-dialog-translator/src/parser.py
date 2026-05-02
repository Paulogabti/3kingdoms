from __future__ import annotations

import logging
from pathlib import Path

from .models import ParsedLine

logger = logging.getLogger(__name__)


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""


def read_dialog_file(path: Path) -> list[ParsedLine]:
    content = None
    for enc in ("utf-8-sig", "utf-8"):
        try:
            content = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if content is None:
        content = path.read_text(encoding="utf-8", errors="replace")
        logger.warning("Fallback errors=replace usado para %s", path)

    lines = content.splitlines(keepends=True)
    parsed: list[ParsedLine] = []
    for idx, raw in enumerate(lines, start=1):
        body, ending = _split_line_ending(raw)
        if "|" in body:
            chinese, english = body.split("|", 1)
            parsed.append(
                ParsedLine(
                    line_number=idx,
                    raw_line=raw,
                    chinese_part=chinese,
                    english_part=english,
                    separator="|",
                    line_ending=ending,
                    has_separator=True,
                    status="pending",
                )
            )
        else:
            parsed.append(
                ParsedLine(
                    line_number=idx,
                    raw_line=raw,
                    chinese_part="",
                    english_part=body,
                    separator="",
                    line_ending=ending,
                    has_separator=False,
                    status="skipped_no_separator",
                )
            )
    return parsed
