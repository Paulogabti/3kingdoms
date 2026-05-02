from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.exporter import export_translated_file
from src.manual_batches import append_batch_event, build_next_manual_batch, import_manual_response, save_prompt_file
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


def cmd_validate(args):
    rep = validate_files(Path(args.original), Path(args.translated))
    print("valid:", rep.valid)


def cmd_smoke_test(_args):
    sample = Path("samples/sample_dialog.txt")
    with tempfile.TemporaryDirectory() as td:
        out, _, _ = run_translation(sample, Path(td), 20, "dry-run", True, True, True)
        rep = validate_files(sample, out)
        if not rep.valid:
            raise SystemExit("Smoke test falhou")
    print("Smoke test OK")


def cmd_manual_next_batch(args):
    input_path = Path(args.input)
    lines = read_dialog_file(input_path)
    fh = file_hash(input_path)
    progress = load_progress(fh)
    batch = build_next_manual_batch(lines, progress, args.batch_size, fh, input_path.name)
    if not batch:
        print("Sem linhas pendentes.")
        return
    prompt_file = save_prompt_file(input_path.name, batch)
    append_batch_event(fh, input_path.name, batch, "prompt_generated")
    print(prompt_file)


def cmd_manual_import(args):
    input_path = Path(args.input)
    lines = read_dialog_file(input_path)
    fh = file_hash(input_path)
    progress = load_progress(fh)
    batch = build_next_manual_batch(lines, progress, 200, fh, input_path.name)
    if not batch:
        print("Sem lote pendente para importar.")
        return
    response_text = Path(args.response).read_text(encoding="utf-8")
    english_map = {l.line_number: l.english_part for l in lines if l.has_separator}
    parsed = import_manual_response(response_text, batch, english_map)
    for l in lines:
        if l.line_number in parsed:
            rec = ProgressRecord(file_hash=fh, source_file_name=input_path.name, line_number=l.line_number,
                                 chinese_part=l.chinese_part, english_original=l.english_part,
                                 portuguese_translation=parsed[l.line_number], status="translated")
            upsert_record(rec)
    append_batch_event(fh, input_path.name, batch, "imported")
    print(f"Importadas {len(parsed)} linhas")


def cmd_manual_export(args):
    input_path = Path(args.input)
    lines = read_dialog_file(input_path)
    fh = file_hash(input_path)
    progress = load_progress(fh)
    out, report, _ = export_translated_file(input_path, Path(args.output_dir), lines, progress, True)
    print(out)
    print(report)


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

    v = sub.add_parser("validate")
    v.add_argument("--original", required=True)
    v.add_argument("--translated", required=True)
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("smoke-test")
    s.set_defaults(func=cmd_smoke_test)

    manual = sub.add_parser("manual")
    manual_sub = manual.add_subparsers(dest="manual_cmd", required=True)
    nb = manual_sub.add_parser("next-batch")
    nb.add_argument("--input", required=True)
    nb.add_argument("--batch-size", type=int, choices=[20, 50, 100, 200], default=100)
    nb.set_defaults(func=cmd_manual_next_batch)

    ir = manual_sub.add_parser("import-response")
    ir.add_argument("--input", required=True)
    ir.add_argument("--response", required=True)
    ir.set_defaults(func=cmd_manual_import)

    ex = manual_sub.add_parser("export")
    ex.add_argument("--input", required=True)
    ex.add_argument("--output-dir", required=True)
    ex.set_defaults(func=cmd_manual_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
