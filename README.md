# FixMate

FixMate is a full-stack RAG vehicle diagnostics chatbot that answers make/model-specific repair questions from service-manual content. It combines a Next.js chat interface with a FastAPI/LangChain backend, hybrid retrieval, source explainability, guardrails, LangSmith tracing, and a separate RAGAS evaluation environment.

The project is designed as a portfolio-grade applied AI system: users select a vehicle make and model, ask a diagnostic or repair question, receive a streamed answer grounded in retrieved manual chunks, and can inspect the exact source references and relevant diagrams used by the assistant.

## Technical Highlights

| Area | Implementation |
| --- | --- |
| RAG orchestration | LangChain-based backend pipeline for input guardrails, query rewriting, retrieval, prompt construction, answer generation, output guardrails, and persistence. |
| Query rewriting | User questions are rewritten into standalone retrieval queries before embedding and search. |
| Hybrid retrieval | Pinecone dense vector search is combined with MongoDB BM25 text search over `FixMate.manual_chunks`. |
| Reciprocal Rank Fusion | Dense and BM25 ranked lists are merged with configurable RRF using `RRF_K=60` by default. |
| Make/model filtering | Frontend dropdowns select the make and model; Pinecone searches the selected model namespace and Mongo filters by make/model. |
| Short-term memory | The chatbot loads only the last `SHORT_TERM_TURNS` messages from MongoDB session history. No cross-session or vector long-term memory is used. |
| Input guardrails | Prompt injection and out-of-scope questions are blocked before retrieval or answer generation. |
| Output guardrails | Answers are checked for grounding against retrieved chunks and scanned for PII or secret-like leakage before persistence. |
| Source explainability | Assistant answers expose a reference popover with exact chunk text, PDF filename, page number, RRF score, and dense/BM25 ranks. |
| Streaming UX | Text streams first, then retrieved diagrams appear below the answer. |
| Observability | LangSmith traces capture query type, original query, rewritten query, retrieved chunks, prompt metadata, response, and guardrail decisions. |
| Evaluation | A separate `Evaluation/` project runs RAGAS metrics against the live backend API without changing backend dependencies. |

## Architecture

![FixMate system architecture](Fixmate-Architecture-Diagram.png)

### Frontend

- Next.js app in `FRONTEND/my-app/`.
- React chat UI with make/model dropdowns, streamed responses, modern message composer, session sidebar, and image gallery.
- Source reference popover shows the chunks that grounded the assistant response.
- Clerk-ready user identity via `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`.

### Backend

- FastAPI app in `BACKEND/`.
- Dependencies managed with `uv`.
- LangChain pipeline shared by normal chat and streaming chat endpoints.
- MongoDB Atlas stores sessions, chat history, searchable manual chunks, and image data.
- Pinecone stores dense vectors by vehicle make/model namespace.
- LangSmith tracing can be enabled through environment variables.

### Ingestion

- `upsertion_script_2_databases` extracts manual text chunks and diagrams/images from PDFs.
- Text chunks are embedded and upserted into Pinecone.
- The same chunks are stored in MongoDB `FixMate.manual_chunks` for BM25 retrieval.
- Stable chunk IDs connect Pinecone vectors, Mongo text chunks, source references, and image metadata.

### Evaluation

- `Evaluation/` is an isolated `uv` project for RAGAS.
- It calls the running backend API instead of importing backend modules.
- Results are written under `Evaluation/results/`.
- Metrics include faithfulness, answer relevancy, context precision, and context recall.

## Retrieval Flow

1. The user selects a vehicle make and model in the frontend.
2. The backend runs input guardrails to block prompt injection and off-topic requests.
3. The user query is rewritten into a standalone retrieval query.
4. Dense retrieval searches Pinecone using the selected make index and model namespace.
5. BM25 retrieval searches MongoDB `FixMate.manual_chunks` filtered by make/model.
6. Reciprocal Rank Fusion merges dense and BM25 ranked lists.
7. The top context chunks are formatted into the final prompt.
8. The LLM generates a streamed answer.
9. Output guardrails check grounding and redact PII or secret-like values.
10. The assistant response, source chunks, guardrail decisions, trace ID, and retrieved images are persisted to MongoDB.
11. The frontend shows the answer, relevant diagrams, and a source reference popover.

## API Surface

Primary backend endpoints:

| Endpoint | Purpose |
| --- | --- |
| `POST /chat/` | Non-streaming chat response with answer, images, sources, guardrails, and trace ID. |
| `POST /chat/stream` | Streaming chat response used by the frontend. |
| `GET /sessions/?user_id=...` | List a user's previous chat sessions. |
| `GET /sessions/{session_id}/history?user_id=...` | Load session history, including images, sources, guardrails, and trace IDs. |
| `GET /meta/makes` | List available vehicle makes. |
| `GET /meta/models?make=...` | List available models for a make. |

## Deployment

The portfolio deployment used a split full-stack deployment:

```text
FastAPI backend
  -> Dockerfile
  -> GitHub Actions CI/CD
  -> Amazon ECR
  -> AWS App Runner
  -> Live HTTPS API endpoint

Next.js frontend
  -> Vercel
  -> Connected to backend through NEXT_PUBLIC_API_URL
```

Managed services:

- MongoDB Atlas for sessions, history, manual chunks, and image data.
- Pinecone for vector retrieval.
- OpenAI for embeddings and LLM responses.
- LangSmith for traceability and debugging.

This deployment story demonstrates containerization, AWS image registry usage, CI/CD automation, managed backend deployment, and a production-style split between frontend hosting and backend API infrastructure.

## Local Setup

### 1. Clone and Create Environment Files

```powershell
Copy-Item BACKEND/.env.example BACKEND/.env
Copy-Item FRONTEND/.env.local.example FRONTEND/.env.local
Copy-Item FRONTEND/.env.local.example FRONTEND/my-app/.env.local
Copy-Item Evaluation/.env.example Evaluation/.env
```

Fill in only local secrets in the generated `.env` files. Do not commit real environment values.

### 2. Backend

```powershell
cd BACKEND
uv sync
uv run uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

### 3. Frontend

```powershell
cd FRONTEND/my-app
pnpm install
pnpm run dev
```

The frontend usually runs at:

```text
http://localhost:3000
```

### 4. Evaluation

Start the backend first, then run:

```powershell
cd Evaluation
uv sync
uv run python ragas_eval.py
```

RAGAS result files are written to:

```text
Evaluation/results/
```

## Environment Variables

### Backend Required

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI embeddings, chat generation, query rewriting, and guardrail classifiers. |
| `PINECONE_API_KEY` | Pinecone vector search. |
| `MONGO_URI` | MongoDB Atlas connection string. |

### Backend Optional

| Variable | Default | Purpose |
| --- | --- | --- |
| `SHORT_TERM_TURNS` | `6` | Number of recent chat messages loaded as short-term memory. |
| `OPENAI_REWRITE_MODEL` | `gpt-4o-mini` | Model used for query rewriting and chat title generation. |
| `OPENAI_ANSWER_MODEL` | `gpt-4o` | Model used for final answer generation. |
| `OPENAI_GUARDRAIL_MODEL` | `gpt-4o-mini` | Model used for guardrail classification. |
| `REVISE_UNGROUNDED_OUTPUT` | `true` | Whether to revise answers flagged as insufficiently grounded. |
| `RRF_K` | `60` | Reciprocal Rank Fusion smoothing constant. |
| `DENSE_CANDIDATES` | `25` | Dense vector candidates retrieved from Pinecone. |
| `BM25_CANDIDATES` | `25` | BM25 candidates retrieved from MongoDB. |
| `CONTEXT_TOP_K` | `1` | Number of fused chunks passed into the LLM context. |
| `RAG_CONTEXT_CHAR_LIMIT` | `1200` | Maximum context characters sent to the LLM. |
| `IMAGE_CANDIDATE_TOP_K` | `2` | Number of top retrieval candidates used for image lookup. |
| `MAX_RETRIEVED_IMAGES` | `4` | Maximum diagrams/images returned with an answer. |
| `CHUNKS_DB` | `FixMate` | MongoDB database for searchable chunks. |
| `CHUNKS_COLLECTION` | `manual_chunks` | MongoDB collection for searchable chunks. |
| `FRONTEND_ORIGINS` | localhost origins | Allowed CORS origins for frontend clients. |
| `LANGSMITH_TRACING` | `false` | Enables LangSmith tracing when set to `true`. |
| `LANGSMITH_API_KEY` | empty | LangSmith API key. |
| `LANGSMITH_PROJECT` | `fixmate-rag` | LangSmith project name. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | LangSmith endpoint. |
| `LANGSMITH_CAPTURE_PROMPTS` | `true` | Captures final prompt messages in trace metadata. |

### Frontend Required

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend API base URL, for example `http://localhost:8000`. |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key for frontend identity integration. |

### Evaluation Required

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required by RAGAS/OpenAI evaluation models. |
| `FIXMATE_API_URL` | Running backend API URL, usually `http://127.0.0.1:8000`. |

## RAGAS Evaluation

The evaluation environment is separate from the backend because RAGAS can require a different LangChain dependency set than the production API.

The test runner:

1. Loads examples from `Evaluation/testset.jsonl`.
2. Calls `POST /chat/` on the running backend.
3. Collects the answer, retrieved contexts, source metadata, and ground truth.
4. Runs RAGAS metrics:
   - Faithfulness
   - Answer relevancy
   - Context precision
   - Context recall
5. Writes timestamped JSON and CSV results under `Evaluation/results/`.
6. Updates `Evaluation/README.md` with the latest score interpretation.

## LangSmith Traceability

When enabled, LangSmith traces are tagged and annotated with:

- Original user query.
- Rewritten query.
- Query type, such as `diagnostic`, `procedure`, `factual`, `summarization`, or `out_of_scope`.
- Make and model.
- Dense/BM25/RRF retrieval metadata.
- Retrieved chunks with PDF filename, page number, and RRF score.
- Final prompt messages.
- Final response.
- Input and output guardrail decisions.
- Session ID and trace ID.

This makes it possible to inspect why a response was produced, which chunks were used, and whether guardrails or retrieval affected the result.

## Testing

Backend tests:

```powershell
cd BACKEND
uv run pytest
```

Current tests cover guardrail behavior, including prompt injection blocking, off-topic classification, PII redaction, missing-source grounding failures, and unsupported-claim detection.

Useful manual checks:

1. Ask an exact service-manual term query and confirm BM25 helps retrieval.
2. Ask a symptom-style question and confirm dense retrieval finds semantic matches.
3. Ask an off-topic question and confirm it is blocked before retrieval.
4. Ask a prompt-injection question and confirm it is blocked.
5. Hover over `Reference` at the end of an assistant answer and confirm chunk text, PDF, page, and RRF score appear.
6. Confirm LangSmith trace metadata includes query type, retrieved chunks, prompt, response, and guardrail decisions.

## Security Notes

- Never commit real `.env` values.
- Rotate any API key that was ever committed, pasted, or shared.
- Keep `BACKEND/.env`, `FRONTEND/.env.local`, `FRONTEND/my-app/.env.local`, `Evaluation/.env`, and evaluation result files out of git.
