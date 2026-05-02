from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
PROGRESS_DIR = ROOT_DIR / ".progress"
PROGRESS_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "20"))

SYSTEM_PROMPT = """Você é um tradutor profissional de localização de jogos, especializado em traduzir diálogos de inglês para português do Brasil.

Traduza apenas o campo recebido em inglês para português brasileiro natural.

Regras obrigatórias:
1. Não altere placeholders protegidos no formato __PH_0001__, __PH_0002__, etc.
2. Não crie novas linhas.
3. Não una textos de itens diferentes.
4. Não remova pontuação relevante.
5. Não adicione explicações.
6. Não traduza nomes técnicos, códigos internos ou placeholders.
7. Preserve o tom de jogo histórico/oriental quando houver.
8. Preserve humor, ironia, agressividade e palavrões quando existirem no original.
9. Traduza \"sir\", \"my lord\", \"Your Excellency\" de forma contextual, usando \"senhor\", \"meu senhor\", \"Vossa Senhoria\" ou \"meu lorde\" conforme o tom do diálogo, mas sem exagerar em formalidade.
10. Traduza de forma fluida, sem parecer tradução automática.
11. Retorne somente JSON válido no formato solicitado."""
