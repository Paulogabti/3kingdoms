from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DEFAULT_BATCH_SIZE, OPENAI_API_KEY, OPENAI_MODEL
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

if not OPENAI_API_KEY:
    st.warning("OPENAI_API_KEY não configurada. Você ainda pode usar o modo dry-run sem API.")

uploaded_files = st.file_uploader("Selecione arquivos .txt", type=["txt"], accept_multiple_files=True)
output_dir = st.text_input("Pasta de saída", value="output")
model = st.text_input("Modelo OpenAI", value=OPENAI_MODEL)
batch_size = st.selectbox("Tamanho do lote", [10, 20, 30, 50], index=[10,20,30,50].index(DEFAULT_BATCH_SIZE) if DEFAULT_BATCH_SIZE in [10,20,30,50] else 1)
overwrite = st.checkbox("Sobrescrever traduções existentes", value=False)
allow_pending = st.checkbox("Permitir exportação com pendências (mantém inglês original nas pendentes)", value=True)
dry_run = st.checkbox("Modo teste sem API / dry-run", value=False)

if st.button("Iniciar tradução") and uploaded_files:
    for uf in uploaded_files:
        temp_path = Path(".tmp_") / uf.name
        temp_path.parent.mkdir(exist_ok=True)
        temp_path.write_bytes(uf.getvalue())
        lines = read_dialog_file(temp_path)
        fh = file_hash(temp_path)
        progress = {} if overwrite else load_progress(fh)
        translatable = [l for l in lines if l.has_separator]
        done_before = sum(1 for l in translatable if progress.get(l.line_number) and progress[l.line_number].status == "translated")
        st.info(f"Progresso encontrado para este arquivo: {done_before}/{len(translatable)} linhas traduzidas")

        translator = Translator(model=model, dry_run=dry_run)
        st.subheader(f"Arquivo atual: {uf.name}")
        pbar = st.progress(done_before / max(1, len(translatable)))
        start = time.time()

        pending = [l for l in translatable if progress.get(l.line_number) is None or progress[l.line_number].status != "translated"]

        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            items = [{"line_number": b.line_number, "text": b.english_part} for b in batch]
            try:
                result = translator.translate_batch(items)
                for b in batch:
                    rec = ProgressRecord(file_hash=fh, source_file_name=uf.name, line_number=b.line_number,
                                         chinese_part=b.chinese_part, english_original=b.english_part,
                                         portuguese_translation=result[b.line_number], status="translated")
                    upsert_record(rec)
                    progress[b.line_number] = rec
            except Exception as e:
                for b in batch:
                    rec = ProgressRecord(file_hash=fh, source_file_name=uf.name, line_number=b.line_number,
                                         chinese_part=b.chinese_part, english_original=b.english_part,
                                         status="error", error_message=str(e))
                    upsert_record(rec)
                    progress[b.line_number] = rec
            done = sum(1 for l in translatable if progress.get(l.line_number) and progress[l.line_number].status == "translated")
            pbar.progress(done / max(1, len(translatable)))

        out, report_file, report = export_translated_file(temp_path, Path(output_dir), lines, progress, allow_pending)
        elapsed = time.time() - start
        validation = validate_files(temp_path, out)
        placeholders_ok = report["translated_lines"]
        st.success(f"Concluído em {elapsed:.1f}s. Saída: {out}")
        st.write({
            "Validação": "Aprovada" if validation.valid else "Falhou",
            "Total de linhas original": len(lines),
            "Total de linhas final": len(out.read_text(encoding='utf-8', errors='replace').splitlines()),
            "Placeholders preservados (linhas traduzidas)": placeholders_ok,
            "Quantidade de linhas com erro": report["error_lines"],
        })
        st.download_button("Baixar relatório JSON", data=report_file.read_bytes(), file_name=report_file.name, mime="application/json")
        st.download_button("Baixar arquivo .pt-BR.txt", data=out.read_bytes(), file_name=out.name, mime="text/plain")

        if not validation.valid:
            rows = [{"linha": e.line_number, "tipo do erro": e.message, "texto original": "", "tradução gerada": "", "sugestão": "Revise a linha e reprocese."} for e in validation.errors]
            st.dataframe(pd.DataFrame(rows))

        recent = []
        for l in lines[-20:]:
            rec = progress.get(l.line_number)
            recent.append({"linha": l.line_number, "chinês": l.chinese_part, "inglês": l.english_part, "português": rec.portuguese_translation if rec else "", "status": rec.status if rec else l.status})
        st.dataframe(pd.DataFrame(recent))
        st.caption("A amostra mostra apenas as últimas 20 linhas para evitar travamento com arquivos grandes.")
