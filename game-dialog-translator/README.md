# Game Dialog Translator PT-BR

Ferramenta local para traduzir arquivos `chinês|inglês` para `chinês|português`, preservando estrutura e progresso.

## Requisitos
- Python 3.11+
- (Opcional) OPENAI_API_KEY para tradução real

## COMO USAR NO WINDOWS
1. Baixe/extraia o projeto.
2. Abra a pasta `game-dialog-translator`.
3. Dê duplo clique em `scripts/setup_windows.bat`.
4. Edite `.env` e preencha `OPENAI_API_KEY`.
5. Dê duplo clique em `scripts/run_windows.bat`.
6. Selecione os arquivos `.txt` na interface.
7. Clique em traduzir.
8. Revise o bloco de validação.
9. Baixe o `.pt-BR.txt` e o relatório JSON.

> O arquivo original nunca é sobrescrito.

## COMO TESTAR SEM GASTAR API
- CLI smoke test offline:
```bash
python cli.py smoke-test
```
- Tradução em dry-run:
```bash
python cli.py translate --input samples/sample_dialog.txt --output-dir saida --dry-run
```
- Na interface Streamlit, marque **Modo teste sem API / dry-run**.

## COMO COMPILAR / GERAR PACOTE WINDOWS
1. Rode `scripts/setup_windows.bat`.
2. Rode `scripts/build_windows.bat`.
3. O pacote sai em `dist/GameDialogTranslatorPTBR/` com executável/launcher e arquivos necessários.

## Testes
```bash
pytest -q
```

## CLI
```bash
python cli.py translate --input "arquivo.txt" --output-dir "saida" --batch-size 20 --model gpt-4.1-mini
python cli.py resume --input "arquivo.txt" --output-dir "saida"
python cli.py validate --original "arquivo.txt" --translated "arquivo.pt-BR.txt"
```

## Progresso
- Salvo em `.progress/<hash>.jsonl`.
- Ao reabrir o mesmo arquivo, a ferramenta reaproveita traduções já concluídas (se overwrite desmarcado).
