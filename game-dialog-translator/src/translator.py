from __future__ import annotations

import json
import logging

from openai import OpenAI

from .config import OPENAI_API_KEY, SYSTEM_PROMPT
from .models import TranslationPayload, TranslationResponse
from .placeholders import placeholders_preserved, protect_placeholders, restore_placeholders

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, model: str, dry_run: bool = False):
        self.model = model
        self.dry_run = dry_run
        self.client = None
        if not dry_run:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY não configurada.")
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def _fake_translate(self, text: str) -> str:
        return f"[PT-BR] {text}" if text.strip() else text

    def translate_batch(self, items: list[dict]) -> dict[int, str]:
        if self.dry_run:
            return {it["line_number"]: self._fake_translate(it["text"]) for it in items}

        pending = items[:]
        results: dict[int, str] = {}
        retries = 0
        while pending and retries < 3:
            payload_items = []
            maps = {}
            for it in pending:
                bundle = protect_placeholders(it["text"])
                payload_items.append({"line_number": it["line_number"], "text": bundle.protected_text})
                maps[it["line_number"]] = bundle.token_to_original

            payload = TranslationPayload.model_validate({"items": payload_items})
            try:
                resp = self.client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": payload.model_dump_json(ensure_ascii=False)},
                    ],
                    text={"format": {"type": "json_object"}},
                )
                text = resp.output_text
                parsed = TranslationResponse.model_validate(json.loads(text))
            except Exception as e:
                logger.error("Falha na API: %s", e)
                retries += 1
                continue

            got = {i.line_number: i.translation for i in parsed.items}
            missing = []
            for it in pending:
                ln = it["line_number"]
                if ln not in got:
                    missing.append(it)
                    continue
                restored = restore_placeholders(got[ln], maps[ln])
                if not placeholders_preserved(it["text"], restored):
                    missing.append(it)
                    continue
                results[ln] = restored
            pending = missing
            retries += 1
        if pending:
            raise RuntimeError(f"Não foi possível traduzir linhas: {[p['line_number'] for p in pending]}")
        return results
