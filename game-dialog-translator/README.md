# Game Dialog Translator PT-BR

Ferramenta local para traduzir arquivos de diálogo no formato `chinês|inglês` para `chinês|português`, preservando estrutura, número de linhas e parte chinesa.

## Requisitos
- Python 3.11+
- Chave de API OpenAI

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Configuração
```bash
cp .env.example .env
```
Edite `.env` e configure `OPENAI_API_KEY`.

## Interface principal (Streamlit)
```bash
streamlit run app.py
```

### Fluxo
1. Selecione um ou mais `.txt`.
2. Defina pasta de saída.
3. Escolha modelo e batch size.
4. Clique em **Iniciar tradução**.
5. Acompanhe progresso, erros e tabela comparativa.
6. Valide arquivo traduzido.

## CLI
```bash
python cli.py translate --input "arquivo.txt" --output-dir "saida" --batch-size 20 --model gpt-4.1-mini
python cli.py resume --input "arquivo.txt" --output-dir "saida"
python cli.py validate --original "arquivo.txt" --translated "arquivo.pt-BR.txt"
```

## Continuação de progresso
- O progresso fica em `.progress/<hash>.jsonl`.
- A ferramenta calcula hash do arquivo original e retoma linhas pendentes.

## Segurança e preservação
- Não altera a parte chinesa.
- Não altera número de linhas.
- Traduz somente após o primeiro `|`.
- Preserva placeholders/variáveis com proteção por tokens internos.
- Nunca sobrescreve arquivo original.

## Solução de problemas
- **OPENAI_API_KEY não configurada**: preencha `.env`.
- **Falha de API**: lote é marcado como erro para tentativa posterior.
- **Validação falhou**: consulte `translation_report.json` e erros por linha.

## Integração futura com GPT personalizado
No futuro, é possível expor esta ferramenta via FastAPI com schema OpenAPI para acoplamento a um GPT personalizado (GPT Actions), sem alterar o núcleo de parsing/tradução/validação.
