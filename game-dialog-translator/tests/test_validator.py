from pathlib import Path

from src.validator import validate_files


def test_validator_chinese_changed(tmp_path: Path):
    orig = tmp_path / "o.txt"
    tra = tmp_path / "t.txt"
    orig.write_text("中|Hello\n", encoding="utf-8")
    tra.write_text("文|Olá\n", encoding="utf-8")
    rep = validate_files(orig, tra)
    assert not rep.valid


def test_validator_line_count(tmp_path: Path):
    orig = tmp_path / "o.txt"
    tra = tmp_path / "t.txt"
    orig.write_text("中|Hello\nA|B\n", encoding="utf-8")
    tra.write_text("中|Olá\n", encoding="utf-8")
    rep = validate_files(orig, tra)
    assert not rep.valid


def test_validator_internal_break(tmp_path: Path):
    orig = tmp_path / "o.txt"
    tra = tmp_path / "t.txt"
    orig.write_text("中|Hello\n", encoding="utf-8")
    tra.write_text("中|Olá\\nquebra\n", encoding="utf-8")
    rep = validate_files(orig, tra)
    assert not rep.valid
