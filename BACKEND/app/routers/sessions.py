# backend/app/routers/sessions.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.db import sessions_col, history_col
from app.models import SessionCreate, SessionOut
from app.utils import new_session

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionOut)
def create_session(payload: SessionCreate):
    sess = new_session()
    sessions_col.insert_one({
        "session_id": sess["session_id"],
        "created_at": sess["created_at"],
        "summary": "",           # start empty
        "user_id": payload.user_id
    })
    return SessionOut(
        session_id=sess["session_id"],
        created_at=sess["created_at"],
        summary="",
        user_id=payload.user_id
    )

@router.get("/", response_model=List[SessionOut])
def list_sessions(user_id: str = Query(..., description="Clerk userId")):
    """
    List all sessions with at least one message, returning the stored summary,
    which we now generated and persisted on first message.
    """
    valid_ids = history_col.distinct("session_id", {"user_id": user_id})
    docs = sessions_col.find(
        {"user_id": user_id, "session_id": {"$in": valid_ids}}
    ).sort("created_at", -1)

    out: List[SessionOut] = []
    for d in docs:
        # we're trusting the stored summary here; fallback to ID slice
        summary = d.get("summary") or d["session_id"][:8]
        out.append(SessionOut(
            session_id=d["session_id"],
            created_at=d["created_at"],
            summary=summary,
            user_id=d["user_id"]
        ))
    return out

@router.get("/{session_id}/history", response_model=List[dict])
def get_history(
    session_id: str,
    user_id: str = Query(..., description="Clerk userId")
):
    sess = sessions_col.find_one({"session_id": session_id, "user_id": user_id})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found for this user")

    docs = history_col.find({"session_id": session_id}).sort("timestamp", 1)
    history = []
    for d in docs:
        history.append({
            "role": d["role"],
            "content": d["content"],
            "is_ar": d.get("is_ar", False),
            "images": d.get("images", []),
            "sources": d.get("sources", []),
            "guardrails": d.get("guardrails", {}),
            "timestamp": d["timestamp"]
        })
    return history
