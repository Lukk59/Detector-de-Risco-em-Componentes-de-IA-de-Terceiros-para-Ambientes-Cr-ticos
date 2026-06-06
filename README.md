# Detector de Risco em Componentes de IA de Terceiros

Aplicação web em Python com FastAPI para analisar risco de modelos, datasets, APIs e bibliotecas de IA.

## Como executar:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

## Testes:

```bash
pytest
```

## Observações:

- O projeto usa regras explicáveis. Não usa IA para classificar o risco.
- O banco é SQLite local.
- O protótipo não coleta dados sensíveis.
