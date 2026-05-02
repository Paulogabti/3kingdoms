from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import ROOT_DIR
from .models import ParsedLine, ProgressRecord
from .placeholders import placeholders_preserved, protect_placeholders, restore_placeholders

MANUAL_BATCHES_DIR = ROOT_DIR / "manual_batches"
MANUAL_BATCHES_DIR.mkdir(exist_ok=True)

PROMPT_TEMPLATE = """Você é um tradutor profissional de localização de jogos.

Traduza do inglês para português do Brasil apenas o campo \"english_text\".

Regras obrigatórias:
1. Não altere placeholders protegidos no formato __PH_0001__, __PH_0002__, etc.
2. Não crie novas linhas.
3. Não una itens diferentes.
4. Não remova pontuação relevante.
5. Não adicione explicações.
6. Não traduza nomes técnicos, códigos internos ou placeholders.
7. Preserve o tom de jogo histórico/oriental quando houver.
8. Preserve humor, ironia, agressividade e palavrões quando existirem no original.
9. Retorne somente JSON válido.
10. Não use markdown.
11. Não coloque comentários antes ou depois do JSON.

Formato obrigatório da resposta:

{
  \"items\": [
    {
      \"line_number\": 1,
      \"translation\": \"Tradução em português\"
    }
  ]
}

Agora traduza este lote:

__BATCH_JSON__
"""


@dataclass
class ManualBatch:
    batch_id: str
    index: int
    start_line: int
    end_line: int
    items: list[dict]
    prompt: str
    token_maps: dict[int, dict[str, str]]


def _history_file(file_hash: str) -> Path:
    return MANUAL_BATCHES_DIR / f"{file_hash}.batches.jsonl"


def _base_name(source_name: str) -> str:
    return Path(source_name).stem


def append_batch_event(file_hash: str, source_name: str, batch: ManualBatch, status: str) -> None:
    now = datetime.utcnow().isoformat()
    event = {
        "batch_id": batch.batch_id,
        "file_hash": file_hash,
        "start_line": batch.start_line,
        "end_line": batch.end_line,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    with _history_file(file_hash).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def next_batch_index(file_hash: str) -> int:
    hf = _history_file(file_hash)
    if not hf.exists():
        return 1
    count = 0
    for line in hf.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count + 1


def build_next_manual_batch(lines: list[ParsedLine], progress: dict[int, ProgressRecord], batch_size: int, file_hash: str, source_name: str) -> ManualBatch | None:
    pending = [l for l in lines if l.has_separator and (l.line_number not in progress or progress[l.line_number].status != "translated")]
    if not pending:
        return None
    chosen = pending[:batch_size]
    idx = next_batch_index(file_hash)
    items = []
    token_maps: dict[int, dict[str, str]] = {}
    for line in chosen:
        bundle = protect_placeholders(line.english_part)
        token_maps[line.line_number] = bundle.token_to_original
        items.append({"line_number": line.line_number, "english_text": bundle.protected_text})
    batch_json = json.dumps(items, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.replace("__BATCH_JSON__", batch_json)
    batch_id = f"batch-{idx:03d}"
    return ManualBatch(batch_id=batch_id, index=idx, start_line=chosen[0].line_number, end_line=chosen[-1].line_number, items=items, prompt=prompt, token_maps=token_maps)


def save_prompt_file(source_name: str, batch: ManualBatch) -> Path:
    path = MANUAL_BATCHES_DIR / f"{_base_name(source_name)}.{batch.batch_id}.prompt.txt"
    path.write_text(batch.prompt, encoding="utf-8")
    return path


def import_manual_response(response_text: str, batch: ManualBatch, english_by_line: dict[int, str]) -> dict[int, str]:
    data = json.loads(response_text)
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("JSON inválido: campo 'items' ausente ou inválido.")
    expected = {it["line_number"] for it in batch.items}
    parsed: dict[int, str] = {}
    errors = []
    for it in items:
        ln = it.get("line_number")
        tr = it.get("translation", "")
        if ln not in expected:
            errors.append(f"linha {ln} não pertence ao lote atual")
            continue
        restored = restore_placeholders(tr, batch.token_maps.get(ln, {}))
        if "\n" in restored or "\r" in restored:
            errors.append(f"linha {ln} contém quebra de linha interna")
            continue
        if not placeholders_preserved(english_by_line[ln], restored):
            errors.append(f"linha {ln} perdeu placeholders")
            continue
        parsed[ln] = restored
    missing = expected - set(parsed.keys())
    for ln in sorted(missing):
        errors.append(f"linha {ln} ausente na resposta")
    if errors:
        raise ValueError("; ".join(errors))
    return parsed
