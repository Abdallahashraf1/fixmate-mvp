from typing import Generator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models import ChatRequest, ChatResponse
from app.services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    return rag_pipeline.run(req)


@router.post("/stream")
def chat_stream(req: ChatRequest, request: Request):
    def event_generator() -> Generator[bytes, None, None]:
        yield from rag_pipeline.stream(req)

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")
