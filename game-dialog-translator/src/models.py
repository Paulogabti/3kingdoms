from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LineStatus = Literal["pending", "translated", "skipped_no_separator", "error", "validated"]


class ParsedLine(BaseModel):
    line_number: int
    raw_line: str
    chinese_part: str = ""
    english_part: str = ""
    separator: str = ""
    line_ending: str = ""
    has_separator: bool = False
    status: LineStatus = "pending"


class ProgressRecord(BaseModel):
    file_hash: str
    source_file_name: str
    line_number: int
    chinese_part: str
    english_original: str
    portuguese_translation: str = ""
    status: LineStatus
    error_message: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TranslationItemIn(BaseModel):
    line_number: int
    text: str


class TranslationPayload(BaseModel):
    items: list[TranslationItemIn]


class TranslationItemOut(BaseModel):
    line_number: int
    translation: str


class TranslationResponse(BaseModel):
    items: list[TranslationItemOut]


class ValidationErrorItem(BaseModel):
    line_number: int
    message: str


class ValidationReport(BaseModel):
    valid: bool
    errors: list[ValidationErrorItem]
