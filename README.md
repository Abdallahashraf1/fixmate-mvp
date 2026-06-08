# FixMate MVP

FixMate is a FastAPI and Next.js application for vehicle diagnostic assistance backed by manual content.

## Environment

Create local environment files from the examples:

```powershell
Copy-Item BACKEND/.env.example BACKEND/.env
Copy-Item FRONTEND/.env.local.example FRONTEND/.env.local
```

Required backend variables:

- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `MONGO_URI`

Optional backend variables:

- `SHORT_TERM_TURNS`, defaults to `6`
- `OPENAI_REWRITE_MODEL`, defaults to `gpt-4o-mini`
- `OPENAI_ANSWER_MODEL`, defaults to `gpt-4o`
- `OPENAI_GUARDRAIL_MODEL`, defaults to `gpt-4o-mini`
- `REVISE_UNGROUNDED_OUTPUT`, defaults to `true`
- `RRF_K`, defaults to `60`
- `DENSE_CANDIDATES`, defaults to `40`
- `BM25_CANDIDATES`, defaults to `40`
- `CONTEXT_TOP_K`, defaults to `10`
- `RAG_CONTEXT_CHAR_LIMIT`, defaults to `6000`
- `CHUNKS_DB`, defaults to `FixMate`
- `CHUNKS_COLLECTION`, defaults to `manual_chunks`

Required frontend variables:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`

Do not commit real `.env` values. The root `.gitignore` excludes `BACKEND/.env`, `FRONTEND/.env.local`, and `docs/`.

## Backend

Backend dependencies are managed with `uv`.

```powershell
cd BACKEND
uv sync
uv run uvicorn app.main:app --reload
```

The chat pipeline loads only the last configured `SHORT_TERM_TURNS` turns from MongoDB session history. This is short-term session memory only; the app does not use cross-session or vector long-term memory.

Retrieval uses hybrid search: dense Pinecone results from the selected make/model namespace plus BM25 MongoDB text search from `FixMate.manual_chunks`. The two ranked lists are merged with Reciprocal Rank Fusion using `RRF_K`.

Guardrails run in both directions. Input guardrails block prompt injection and out-of-scope questions before retrieval or answer generation. Output guardrails check grounding against retrieved chunks and redact detected PII or secret-like values before the answer is persisted or returned.

If deployment still requires `requirements.txt`, generate it from `pyproject.toml` instead of editing it by hand:

```powershell
cd BACKEND
uv pip compile pyproject.toml -o requirements.txt
```

## Security Note

If any API key was ever committed or shared, rotate it in the provider dashboard and update only the local environment file.
