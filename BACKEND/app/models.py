from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    user_id: str

class SessionOut(BaseModel):
    session_id: str
    created_at: datetime
    summary: Optional[str] = ""
    user_id: str

class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    source: str
    page: int
    rrf_score: float
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class GuardrailResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    flags: List[str] = Field(default_factory=list)

class Message(BaseModel):
    role: str
    content: str
    is_ar: Optional[bool] = False
    sources: List[SourceChunk] = Field(default_factory=list)
    guardrails: dict[str, GuardrailResult] = Field(default_factory=dict)

class HistoryMessage(Message):
    timestamp: datetime
    images: Optional[List[dict]] = Field(default_factory=list)

class ChatRequest(BaseModel):
    session_id: Optional[str]  # may be empty or wrong, we'll handle on server
    user_id: str
    role: str           # "Car Owner" or "Car Specialist"
    make: str
    model: str
    query: str

class ChatResponse(BaseModel):
    assistant_text: str
    images: List[dict]  # { "id": str, "page": int, "source": str, "data": str(base64) }
    session_id: str
    sources: List[SourceChunk] = Field(default_factory=list)
    guardrails: dict[str, GuardrailResult] = Field(default_factory=dict)

class ImageRequest(BaseModel):
    make: str
    model: str
    image_ids: List[str]
