from __future__ import annotations

import re
from pathlib import Path

from .models import ValidationErrorItem, ValidationReport
from .parser import _split_line_ending, read_dialog_file
from .placeholders import protect_placeholders


def validate_files(original: Path, translated: Path) -> ValidationReport:
    orig_lines = read_dialog_file(original)
    traw = translated.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    errors: list[ValidationErrorItem] = []
    if len(orig_lines) != len(traw):
        errors.append(ValidationErrorItem(line_number=0, message="Número de linhas diferente."))
        return ValidationReport(valid=False, errors=errors)

    for i, (o, tline) in enumerate(zip(orig_lines, traw), start=1):
        tbody, ending = _split_line_ending(tline)
        if o.has_separator:
            if "|" not in tbody:
                errors.append(ValidationErrorItem(line_number=i, message="Separador ausente."))
                continue
            tch, tpt = tbody.split("|", 1)
            if tch != o.chinese_part:
                errors.append(ValidationErrorItem(line_number=i, message="Parte chinesa alterada."))
            if "__PH_" in tpt:
                errors.append(ValidationErrorItem(line_number=i, message="Token interno __PH_ encontrado."))
            for ph in set(protect_placeholders(o.english_part).token_to_original.values()):
                if ph not in tpt and re.search(r"[A-Z]{2,}|\{|%|<|\[", ph):
                    errors.append(ValidationErrorItem(line_number=i, message=f"Placeholder ausente: {ph}"))
            if o.english_part.strip() and not tpt.strip():
                errors.append(ValidationErrorItem(line_number=i, message="Tradução vazia."))
            if "\n" in tpt or "\r" in tpt:
                errors.append(ValidationErrorItem(line_number=i, message="Quebra de linha interna na tradução."))
            if o.line_ending == "\r" and ending != "\r":
                errors.append(ValidationErrorItem(line_number=i, message="Quebra \r não preservada."))
    return ValidationReport(valid=not errors, errors=errors)
