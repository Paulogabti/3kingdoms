from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DEFAULT_BATCH_SIZE, OPENAI_API_KEY, OPENAI_MODEL
from src.exporter import export_translated_file
from src.manual_batches import append_batch_event, build_next_manual_batch, import_manual_response
from src.models import ProgressRecord
from src.parser import read_dialog_file
from src.progress import load_progress, upsert_record
from src.translator import Translator
from src.utils import file_hash, setup_logging
from src.validator import validate_files

setup_logging()
st.set_page_config(page_title="Game Dialog Translator PT-BR", layout="wide")
st.title("Game Dialog Translator PT-BR")

mode = st.selectbox("Modo de tradução", ["API OpenAI", "Dry-run / teste sem API", "ChatGPT Manual"])
if mode == "API OpenAI" and not OPENAI_API_KEY:
    st.warning("OPENAI_API_KEY não configurada. Use Dry-run ou ChatGPT Manual.")

uploaded_files = st.file_uploader("Selecione arquivos .txt", type=["txt"], accept_multiple_files=True)
output_dir = st.text_input("Pasta de saída", value="output")
model = st.text_input("Modelo OpenAI", value=OPENAI_MODEL)
batch_size = st.selectbox("Tamanho do lote", [10, 20, 30, 50, 100, 200], index=1)
overwrite = st.checkbox("Sobrescrever traduções existentes", value=False)
allow_pending = st.checkbox("Permitir exportação com pendências", value=True)

if uploaded_files:
    for uf in uploaded_files:
        temp_path = Path(".tmp_") / uf.name
        temp_path.parent.mkdir(exist_ok=True)
        temp_path.write_bytes(uf.getvalue())
        lines = read_dialog_file(temp_path)
        fh = file_hash(temp_path)
        progress = {} if overwrite else load_progress(fh)
        translatable = [l for l in lines if l.has_separator]
        done_before = sum(1 for l in translatable if progress.get(l.line_number) and progress[l.line_number].status == "translated")

        st.subheader(f"Arquivo atual: {uf.name}")
        st.info(f"Progresso: {done_before}/{len(translatable)} traduzidas")

        if mode in {"API OpenAI", "Dry-run / teste sem API"} and st.button(f"Iniciar tradução ({uf.name})"):
            translator = Translator(model=model, dry_run=(mode != "API OpenAI"))
            pbar = st.progress(done_before / max(1, len(translatable)))
            start = time.time()
            pending = [l for l in translatable if progress.get(l.line_number) is None or progress[l.line_number].status != "translated"]
            for i in range(0, len(pending), batch_size):
                batch = pending[i:i + batch_size]
                items = [{"line_number": b.line_number, "text": b.english_part} for b in batch]
                result = translator.translate_batch(items)
                for b in batch:
                    rec = ProgressRecord(file_hash=fh, source_file_name=uf.name, line_number=b.line_number,
                                         chinese_part=b.chinese_part, english_original=b.english_part,
                                         portuguese_translation=result[b.line_number], status="translated")
                    upsert_record(rec)
                    progress[b.line_number] = rec
                done = sum(1 for l in translatable if progress.get(l.line_number) and progress[l.line_number].status == "translated")
                pbar.progress(done / max(1, len(translatable)))
            st.success(f"Concluído em {time.time() - start:.1f}s")

        if mode == "ChatGPT Manual":
            batch = build_next_manual_batch(lines, progress, batch_size if batch_size in {20, 50, 100, 200} else 20, fh, uf.name)
            if not batch:
                st.success("Sem pendências: tudo já traduzido para este arquivo.")
            else:
                append_batch_event(fh, uf.name, batch, "prompt_generated")
                st.write({"batch_id": batch.batch_id, "linhas": f"{batch.start_line}-{batch.end_line}", "pendentes": len([l for l in translatable if progress.get(l.line_number) is None or progress[l.line_number].status != 'translated']), "traduzidas": done_before})
                st.caption("Use a caixa abaixo para copiar manualmente o prompt.")
                st.text_area("Prompt do lote", value=batch.prompt, height=320, key=f"prompt_{uf.name}_{batch.batch_id}")
                if st.button(f"Marcar lote como enviado ({uf.name})"):
                    append_batch_event(fh, uf.name, batch, "pending")
                    st.info("Lote marcado como enviado.")

                response_text = st.text_area("Cole aqui a resposta JSON do ChatGPT", height=220, key=f"resp_{uf.name}_{batch.batch_id}")
                if st.button(f"Importar traduções deste lote ({uf.name})"):
                    try:
                        english_map = {l.line_number: l.english_part for l in translatable}
                        parsed = import_manual_response(response_text, batch, english_map)
                        for l in translatable:
                            if l.line_number in parsed:
                                rec = ProgressRecord(file_hash=fh, source_file_name=uf.name, line_number=l.line_number,
                                                     chinese_part=l.chinese_part, english_original=l.english_part,
                                                     portuguese_translation=parsed[l.line_number], status="translated")
                                upsert_record(rec)
                        append_batch_event(fh, uf.name, batch, "imported")
                        st.success("Lote importado com sucesso. Recarregue para avançar para o próximo lote.")
                    except Exception as e:
                        append_batch_event(fh, uf.name, batch, "error")
                        st.error(f"Falha ao importar lote: {e}")

        if st.button(f"Exportar ({uf.name})"):
            progress = load_progress(fh)
            out, report_file, report = export_translated_file(temp_path, Path(output_dir), lines, progress, allow_pending)
            validation = validate_files(temp_path, out)
            st.success(f"Saída: {out}")
            st.write({"Validação": "Aprovada" if validation.valid else "Falhou", "erros": report["error_lines"], "pendentes": report["pending_lines"]})
            st.download_button("Baixar relatório JSON", data=report_file.read_bytes(), file_name=report_file.name, mime="application/json")
            st.download_button("Baixar arquivo .pt-BR.txt", data=out.read_bytes(), file_name=out.name, mime="text/plain")

        recent = []
        progress = load_progress(fh)
        for l in lines[-20:]:
            rec = progress.get(l.line_number)
            recent.append({"linha": l.line_number, "chinês": l.chinese_part, "inglês": l.english_part, "português": rec.portuguese_translation if rec else "", "status": rec.status if rec else l.status})
        st.dataframe(pd.DataFrame(recent))
