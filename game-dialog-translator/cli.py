from __future__ import annotations

import argparse
from pathlib import Path

from src.exporter import export_translated_file
from src.models import ProgressRecord
from src.parser import read_dialog_file
from src.progress import load_progress, upsert_record
from src.translator import Translator
from src.utils import file_hash
from src.validator import validate_files


def cmd_translate(args):
    path = Path(args.input)
    lines = read_dialog_file(path)
    fh = file_hash(path)
    progress = {} if args.overwrite else load_progress(fh)
    translator = Translator(args.model)
    pending = [l for l in lines if l.has_separator and (l.line_number not in progress or progress[l.line_number].status != "translated")]
    for i in range(0, len(pending), args.batch_size):
        batch = pending[i:i+args.batch_size]
        result = translator.translate_batch([{"line_number": b.line_number, "text": b.english_part} for b in batch])
        for b in batch:
            rec = ProgressRecord(file_hash=fh, source_file_name=path.name, line_number=b.line_number,
                                 chinese_part=b.chinese_part, english_original=b.english_part,
                                 portuguese_translation=result[b.line_number], status="translated")
            upsert_record(rec)
            progress[b.line_number] = rec
    out, report, _ = export_translated_file(path, Path(args.output_dir), lines, progress, allow_pending=True)
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


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("translate")
    t.add_argument("--input", required=True)
    t.add_argument("--output-dir", required=True)
    t.add_argument("--batch-size", type=int, default=20)
    t.add_argument("--model", default="gpt-4.1-mini")
    t.add_argument("--overwrite", action="store_true")
    t.set_defaults(func=cmd_translate)

    r = sub.add_parser("resume")
    r.add_argument("--input", required=True)
    r.add_argument("--output-dir", required=True)
    r.add_argument("--batch-size", type=int, default=20)
    r.add_argument("--model", default="gpt-4.1-mini")
    r.set_defaults(func=cmd_resume)

    v = sub.add_parser("validate")
    v.add_argument("--original", required=True)
    v.add_argument("--translated", required=True)
    v.set_defaults(func=cmd_validate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
