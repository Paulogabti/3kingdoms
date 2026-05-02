from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DEFAULT_BATCH_SIZE, OPENAI_MODEL
from src.exporter import export_translated_file
from src.models import ProgressRecord
from src.parser import read_dialog_file
from src.progress import load_progress, upsert_record
from src.translator import Translator
from src.utils import file_hash, setup_logging
from src.validator import validate_files

setup_logging()
st.set_page_config(page_title="Game Dialog Translator PT-BR", layout="wide")
st.title("Game Dialog Translator PT-BR")

uploaded_files = st.file_uploader("Selecione arquivos .txt", type=["txt"], accept_multiple_files=True)
output_dir = st.text_input("Pasta de saída", value="output")
model = st.text_input("Modelo OpenAI", value=OPENAI_MODEL)
batch_size = st.selectbox("Tamanho do lote", [10, 20, 30, 50], index=[10,20,30,50].index(DEFAULT_BATCH_SIZE) if DEFAULT_BATCH_SIZE in [10,20,30,50] else 1)
overwrite = st.checkbox("Sobrescrever traduções existentes", value=False)
allow_pending = st.checkbox("Permitir exportação com pendências", value=True)

if st.button("Iniciar tradução") and uploaded_files:
    for uf in uploaded_files:
        temp_path = Path(".tmp_") / uf.name
        temp_path.parent.mkdir(exist_ok=True)
        temp_path.write_bytes(uf.getvalue())
        lines = read_dialog_file(temp_path)
        fh = file_hash(temp_path)
        progress = {} if overwrite else load_progress(fh)
        translator = Translator(model=model)
        st.subheader(f"Arquivo atual: {uf.name}")
        pbar = st.progress(0)
        start = time.time()

        translatable = [l for l in lines if l.has_separator]
        pending = [l for l in translatable if progress.get(l.line_number, None) is None or progress[l.line_number].status != "translated"]

        for i in range(0, len(pending), batch_size):
            batch = pending[i:i+batch_size]
            items = [{"line_number": b.line_number, "text": b.english_part} for b in batch]
            try:
                result = translator.translate_batch(items)
                for b in batch:
                    rec = ProgressRecord(
                        file_hash=fh, source_file_name=uf.name, line_number=b.line_number,
                        chinese_part=b.chinese_part, english_original=b.english_part,
                        portuguese_translation=result[b.line_number], status="translated",
                    )
                    upsert_record(rec)
                    progress[b.line_number] = rec
            except Exception as e:
                for b in batch:
                    rec = ProgressRecord(file_hash=fh, source_file_name=uf.name, line_number=b.line_number,
                        chinese_part=b.chinese_part, english_original=b.english_part, status="error", error_message=str(e))
                    upsert_record(rec)
                    progress[b.line_number] = rec
            done = sum(1 for l in translatable if progress.get(l.line_number) and progress[l.line_number].status == "translated")
            pbar.progress(done / max(1, len(translatable)))

        out, report_file, report = export_translated_file(temp_path, Path(output_dir), lines, progress, allow_pending)
        elapsed = time.time() - start
        st.success(f"Concluído em {elapsed:.1f}s. Saída: {out}")
        st.json(report)
        recent = []
        for l in lines[-15:]:
            rec = progress.get(l.line_number)
            recent.append({"linha": l.line_number, "chinês": l.chinese_part, "inglês": l.english_part, "português": rec.portuguese_translation if rec else "", "status": rec.status if rec else l.status})
        st.dataframe(pd.DataFrame(recent))

if st.button("Validar arquivo traduzido"):
    orig = st.text_input("Original", value="samples/sample_dialog.txt")
    tr = st.text_input("Traduzido", value="output/sample_dialog.pt-BR.txt")
    if orig and tr:
        rep = validate_files(Path(orig), Path(tr))
        st.write("Válido:" , rep.valid)
        st.write([e.model_dump() for e in rep.errors])
