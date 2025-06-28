# models.py :
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class SessionCreate(BaseModel):
    user_id: str

class SessionOut(BaseModel):
    session_id: str
    created_at: datetime
    summary: Optional[str] = ""
    user_id: str

class Message(BaseModel):
    role: str
    content: str
    is_ar: Optional[bool] = False

class HistoryMessage(Message):
    timestamp: datetime
    images: Optional[List[dict]] = []

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

class ImageRequest(BaseModel):
    make: str
    model: str
    image_ids: List[str]
