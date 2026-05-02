from pathlib import Path

from src.exporter import export_translated_file
from src.models import ProgressRecord
from src.parser import read_dialog_file


def test_exporter_preserve(tmp_path: Path):
    src = tmp_path / "x.txt"
    src.write_text("中|Hello\nsem\n", encoding="utf-8")
    lines = read_dialog_file(src)
    rec = ProgressRecord(file_hash="h", source_file_name="x.txt", line_number=1, chinese_part="中", english_original="Hello", portuguese_translation="Olá", status="translated")
    out, _, _ = export_translated_file(src, tmp_path, lines, {1: rec})
    text = out.read_text(encoding="utf-8")
    assert "中|Olá" in text
    assert "sem" in text
