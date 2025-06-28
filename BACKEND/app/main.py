# main.py:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sessions, meta, chat, images

app = FastAPI(title="FixMate API")

# 1️⃣ Add CORS middleware so your Next.js frontend (localhost:3000) can call the API
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # add any other origins you need (e.g. your deployed frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(meta.router)
app.include_router(chat.router)
app.include_router(images.router)