# FixMate RAGAS Evaluation

This directory is intentionally separate from `BACKEND/` and `FRONTEND/`.
RAGAS can require a different LangChain dependency set than the production backend, so this project has its own `uv` environment and lockfile.

## Setup

```powershell
cd Evaluation
Copy-Item .env.example .env
uv sync
```

Set `OPENAI_API_KEY` in `Evaluation/.env`.
Start the production backend separately before running evaluation:

```powershell
cd ..\BACKEND
uv run uvicorn app.main:app --reload
```

Run evaluation from `Evaluation/`:

```powershell
uv run python ragas_eval.py
```

The runner calls the backend API configured by `FIXMATE_API_URL`; it does not import backend modules.

## Test Set

Edit `testset.jsonl`. Each allowed example should include:

```json
{"question":"...", "ground_truth":"...", "make":"...", "model":"...", "expected_sources":[{"pdf":"...", "page":12}]}
```

Use at least 30 examples before treating scores as meaningful. Cover exact terms, symptom descriptions, procedures, Arabic and English questions, and image/diagram requests. Keep prompt-injection and off-topic examples in a separate guardrail test set because they should not reach the RAG pipeline.

## Metrics

- Faithfulness: checks whether answer claims are supported by retrieved manual chunks.
- Answer relevancy: checks whether the answer addresses the user question.
- Context precision: checks whether retrieved chunks ranked highly are actually useful.
- Context recall: checks whether retrieval found the evidence needed for the ground-truth answer.

## Latest Result

No eval run has been recorded yet.

After running `uv run python ragas_eval.py`, this section is automatically replaced with the latest summary and short interpretations. Do not treat scores as meaningful unless the backend was running against the intended database/index and the test set reflects real expected answers. Example:

```md
Latest eval: 2026-06-09

Faithfulness: 0.91
Interpretation: most answer claims were grounded in the retrieved manual chunks. Failures were mostly specification questions where retrieval found a procedure page but missed the table with the numeric value.
```
