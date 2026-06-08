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

If deployment still requires `requirements.txt`, generate it from `pyproject.toml` instead of editing it by hand:

```powershell
cd BACKEND
uv pip compile pyproject.toml -o requirements.txt
```

## Security Note

If any API key was ever committed or shared, rotate it in the provider dashboard and update only the local environment file.
