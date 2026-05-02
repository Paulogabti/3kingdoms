from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.exporter import export_translated_file
from src.models import ProgressRecord
from src.parser import read_dialog_file
from src.progress import load_progress, upsert_record
from src.translator import Translator
from src.utils import file_hash
from src.validator import validate_files


def run_translation(input_path: Path, output_dir: Path, batch_size: int, model: str, overwrite: bool, dry_run: bool, allow_pending: bool):
    lines = read_dialog_file(input_path)
    fh = file_hash(input_path)
    progress = {} if overwrite else load_progress(fh)
    translator = Translator(model, dry_run=dry_run)
    pending = [l for l in lines if l.has_separator and (l.line_number not in progress or progress[l.line_number].status != "translated")]
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        result = translator.translate_batch([{"line_number": b.line_number, "text": b.english_part} for b in batch])
        for b in batch:
            rec = ProgressRecord(file_hash=fh, source_file_name=input_path.name, line_number=b.line_number,
                                 chinese_part=b.chinese_part, english_original=b.english_part,
                                 portuguese_translation=result[b.line_number], status="translated")
            upsert_record(rec)
            progress[b.line_number] = rec
    return export_translated_file(input_path, output_dir, lines, progress, allow_pending=allow_pending)


def cmd_translate(args):
    out, report, _ = run_translation(Path(args.input), Path(args.output_dir), args.batch_size, args.model, args.overwrite, args.dry_run, args.allow_pending)
    print(out)
    print(report)


def cmd_resume(args):
    args.overwrite = False
    cmd_translate(args)


def cmd_validate(args):
    rep = validate_files(Path(args.original), Path(args.translated))
    print("valid:", rep.valid)
    for e in rep.errors:
        print(f"linha {e.line_number}: {e.message}")


def cmd_smoke_test(_args):
    sample = Path("samples/sample_dialog.txt")
    with tempfile.TemporaryDirectory() as td:
        out, _, _ = run_translation(sample, Path(td), 20, "dry-run", True, True, True)
        rep = validate_files(sample, out)
        if not rep.valid:
            raise SystemExit("Smoke test falhou")
    print("Smoke test OK")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("translate")
    t.add_argument("--input", required=True)
    t.add_argument("--output-dir", required=True)
    t.add_argument("--batch-size", type=int, default=20)
    t.add_argument("--model", default="gpt-4.1-mini")
    t.add_argument("--overwrite", action="store_true")
    t.add_argument("--dry-run", action="store_true")
    t.add_argument("--allow-pending", action="store_true", default=True)
    t.set_defaults(func=cmd_translate)

    r = sub.add_parser("resume")
    r.add_argument("--input", required=True)
    r.add_argument("--output-dir", required=True)
    r.add_argument("--batch-size", type=int, default=20)
    r.add_argument("--model", default="gpt-4.1-mini")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--allow-pending", action="store_true", default=True)
    r.set_defaults(func=cmd_resume)

    v = sub.add_parser("validate")
    v.add_argument("--original", required=True)
    v.add_argument("--translated", required=True)
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("smoke-test")
    s.set_defaults(func=cmd_smoke_test)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
