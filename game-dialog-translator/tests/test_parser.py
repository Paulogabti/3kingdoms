from pathlib import Path

from src.parser import read_dialog_file


def test_normal_line(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("测试物品获得|Test Items Acquired\n", encoding="utf-8")
    line = read_dialog_file(p)[0]
    assert line.chinese_part == "测试物品获得"
    assert line.english_part == "Test Items Acquired"


def test_multi_separator(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("中文|Text with | inside\n", encoding="utf-8")
    line = read_dialog_file(p)[0]
    assert line.chinese_part == "中文"
    assert line.english_part == "Text with | inside"


def test_no_separator(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("apenas texto\n", encoding="utf-8")
    line = read_dialog_file(p)[0]
    assert line.status == "skipped_no_separator"
