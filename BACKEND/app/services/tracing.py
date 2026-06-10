import hashlib
from contextlib import nullcontext
from typing import Any, Iterable

from langchain_core.messages import BaseMessage
from langsmith import traceable, tracing_context
from langsmith.run_helpers import get_current_run_tree, set_run_metadata

from app.config import settings
from app.models import ChatRequest, ChatResponse, GuardrailResult, SourceChunk


def tracing_enabled() -> bool:
    return settings.langsmith_tracing and bool(settings.langsmith_api_key)


def user_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]


def request_metadata(req: ChatRequest, operation: str) -> dict[str, Any]:
    return {
        "operation": operation,
        "session_id": req.session_id,
        "user_id_hash": user_hash(req.user_id),
        "role": req.role,
        "make": req.make,
        "model": req.model,
        "original_query": req.query,
        "retrieval_strategy": "hybrid_rrf",
        "rrf_k": settings.rrf_k,
        "dense_candidates": settings.dense_candidates,
        "bm25_candidates": settings.bm25_candidates,
        "context_top_k": settings.context_top_k,
        "rag_context_char_limit": settings.rag_context_char_limit,
        "image_candidate_top_k": settings.image_candidate_top_k,
        "max_retrieved_images": settings.max_retrieved_images,
    }


def base_tags(req: ChatRequest, operation: str) -> list[str]:
    return [
        "fixmate",
        "phase6",
        "langsmith",
        "hybrid-rrf",
        "guardrails",
        f"operation:{operation}",
        f"make:{_tag_value(req.make)}",
        f"model:{_tag_value(req.model)}",
    ]


def request_trace_context(req: ChatRequest, operation: str):
    if not tracing_enabled():
        return nullcontext()
    return tracing_context(
        project_name=settings.langsmith_project,
        tags=base_tags(req, operation),
        metadata=request_metadata(req, operation),
        enabled=True,
    )


def add_current_metadata(**metadata: Any) -> None:
    if not tracing_enabled():
        return
    set_run_metadata(**metadata)


def add_current_tags(tags: Iterable[str]) -> None:
    if not tracing_enabled():
        return
    run_tree = get_current_run_tree()
    if run_tree is not None:
        run_tree.add_tags(list(tags))


def current_trace_id() -> str | None:
    run_tree = get_current_run_tree()
    if run_tree is None:
        return None
    return str(run_tree.id)


def query_type_from_guardrails(guardrails: dict[str, GuardrailResult]) -> str:
    input_guardrail = guardrails.get("input")
    if not input_guardrail:
        return "unknown"
    return str(input_guardrail.details.get("query_type") or "unknown")


def source_chunks_for_trace(sources: list[SourceChunk]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": source.chunk_id,
            "pdf": source.source,
            "page": source.page,
            "rrf_score": source.rrf_score,
            "dense_rank": source.dense_rank,
            "bm25_rank": source.bm25_rank,
            "dense_score": source.dense_score,
            "bm25_score": source.bm25_score,
            "text_preview": _truncate(source.text, 800),
        }
        for source in sources
    ]


def messages_for_trace(messages: list[BaseMessage]) -> list[dict[str, str]]:
    return [
        {
            "type": message.type,
            "content": str(message.content),
        }
        for message in messages
    ]


def chain_config_metadata(
    *,
    req: ChatRequest,
    run_name: str,
    rewritten_query: str = "",
    query_type: str = "unknown",
    sources: list[SourceChunk] | None = None,
    messages: list[BaseMessage] | None = None,
) -> dict[str, Any]:
    metadata = {
        "run_name": run_name,
        "session_id": req.session_id,
        "user_id_hash": user_hash(req.user_id),
        "role": req.role,
        "make": req.make,
        "model": req.model,
        "original_query": req.query,
        "rewritten_query": rewritten_query,
        "query_type": query_type,
        "retrieval_strategy": "hybrid_rrf",
        "rrf_k": settings.rrf_k,
        "dense_candidates": settings.dense_candidates,
        "bm25_candidates": settings.bm25_candidates,
        "context_top_k": settings.context_top_k,
    }
    if sources is not None:
        metadata["retrieved_chunks"] = source_chunks_for_trace(sources)
    if messages is not None and settings.langsmith_capture_prompts:
        metadata["final_prompt_messages"] = messages_for_trace(messages)
    return metadata


def chain_config_tags(req: ChatRequest, run_name: str, query_type: str = "unknown") -> list[str]:
    return [
        "fixmate",
        "phase6",
        "hybrid-rrf",
        "guardrails",
        f"run:{_tag_value(run_name)}",
        f"query_type:{_tag_value(query_type)}",
        f"make:{_tag_value(req.make)}",
        f"model:{_tag_value(req.model)}",
    ]


def chat_request_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    req = inputs.get("req")
    if not isinstance(req, ChatRequest):
        return {}
    return {"request": request_metadata(req, "chat")}


def chat_response_trace_outputs(output: Any) -> dict[str, Any]:
    if not isinstance(output, ChatResponse):
        return {"output_type": type(output).__name__}
    return {
        "session_id": output.session_id,
        "trace_id": output.trace_id,
        "answer_chars": len(output.assistant_text or ""),
        "images_count": len(output.images or []),
        "source_chunks": source_chunks_for_trace(output.sources or []),
        "guardrails": {
            key: value.model_dump()
            for key, value in (output.guardrails or {}).items()
        },
    }


def stream_trace_reduce(chunks: list[bytes]) -> dict[str, Any]:
    return {
        "chunks": len(chunks),
        "bytes": sum(len(chunk) for chunk in chunks),
    }


def guardrail_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    req = inputs.get("req")
    if isinstance(req, ChatRequest):
        return {"request": request_metadata(req, "input_guardrails")}
    return {
        "question": _truncate(str(inputs.get("question", "")), 1000),
        "answer_preview": _truncate(str(inputs.get("answer", "")), 1000),
        "sources_count": len(inputs.get("sources") or []),
    }


def guardrail_trace_outputs(output: Any) -> dict[str, Any]:
    if isinstance(output, GuardrailResult):
        return output.model_dump()
    result = getattr(output, "result", None)
    if isinstance(result, GuardrailResult):
        return {
            "text_preview": _truncate(str(getattr(output, "text", "")), 1000),
            "should_revise": bool(getattr(output, "should_revise", False)),
            "result": result.model_dump(),
        }
    return {"output_type": type(output).__name__}


def retrieval_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    req = inputs.get("req")
    payload = {}
    if isinstance(req, ChatRequest):
        payload.update(request_metadata(req, "retrieval"))
    if "rewritten_query" in inputs:
        payload["rewritten_query"] = inputs["rewritten_query"]
    if "top_k" in inputs:
        payload["top_k"] = inputs["top_k"]
    return payload


def retrieval_trace_outputs(output: Any) -> dict[str, Any]:
    if not isinstance(output, list):
        return {"output_type": type(output).__name__}
    return {
        "count": len(output),
        "chunks": [
            {
                "chunk_id": getattr(item, "chunk_id", None),
                "pdf": getattr(item, "source", None),
                "page": getattr(item, "page", None),
                "rrf_score": getattr(item, "rrf_score", None),
                "dense_rank": getattr(item, "dense_rank", None),
                "bm25_rank": getattr(item, "bm25_rank", None),
                "dense_score": getattr(item, "dense_score", None),
                "bm25_score": getattr(item, "bm25_score", None),
                "text_preview": _truncate(str(getattr(item, "text", "")), 800),
            }
            for item in output
        ],
    }


def prompt_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    req = inputs.get("req")
    payload: dict[str, Any] = {}
    if isinstance(req, ChatRequest):
        payload.update(request_metadata(req, "prompt_build"))
    payload["context_chars"] = len(str(inputs.get("context", "")))
    return payload


def prompt_trace_outputs(output: Any) -> dict[str, Any]:
    if not isinstance(output, list):
        return {"output_type": type(output).__name__}
    return {"messages": messages_for_trace(output) if settings.langsmith_capture_prompts else []}


def persistence_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    prepared = inputs.get("prepared")
    req = getattr(prepared, "req", None)
    payload: dict[str, Any] = {}
    if isinstance(req, ChatRequest):
        payload.update(request_metadata(req, "history_persistence"))
    payload["answer_chars"] = len(str(inputs.get("assistant_text", "")))
    payload["trace_id"] = getattr(prepared, "trace_id", None)
    payload["source_count"] = len(getattr(prepared, "source_chunks", []) or [])
    return payload


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "...[truncated]"


def _tag_value(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_") or "unknown"
