import base64
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, Iterable, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from PIL import Image, ImageOps

from app.config import settings
from app.db import mongo_client, pinecone_client, sessions_col, history_col
from app.models import ChatRequest, ChatResponse, GuardrailResult, SourceChunk
from app.utils import build_system_prompt, detect_language, new_session


@dataclass
class PreparedChat:
    req: ChatRequest
    session: dict
    is_ar: bool
    rewritten_query: str
    messages: list[BaseMessage]
    source_chunks: list[SourceChunk]
    images: list[dict]
    guardrails: dict[str, GuardrailResult]


class RagPipeline:
    def __init__(self) -> None:
        prompt = ChatPromptTemplate.from_messages([("user", "{prompt}")])
        rewrite_llm = ChatOpenAI(
            model=settings.rewrite_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        answer_llm = ChatOpenAI(
            model=settings.answer_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )

        self.rewrite_chain = prompt | rewrite_llm | StrOutputParser()
        self.validate_chain = prompt | rewrite_llm | StrOutputParser()
        self.title_chain = prompt | rewrite_llm | StrOutputParser()
        self.answer_chain = RunnableLambda(lambda state: state["messages"]) | answer_llm | StrOutputParser()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )

    def run(self, req: ChatRequest) -> ChatResponse:
        prepared = self.prepare(req)
        if self._is_blocked(prepared):
            return self._blocked_response(prepared)

        assistant_text = self.answer_chain.invoke(
            {"messages": prepared.messages},
            config=self._chain_config(prepared, "answer"),
        )
        prepared.guardrails["output"] = GuardrailResult(allowed=True)
        self.persist_turn(prepared, assistant_text)
        return ChatResponse(
            assistant_text=assistant_text,
            images=prepared.images,
            session_id=prepared.req.session_id or "",
            sources=prepared.source_chunks,
            guardrails=prepared.guardrails,
        )

    def stream(self, req: ChatRequest) -> Generator[bytes, None, None]:
        prepared = self.prepare(req)
        if self._is_blocked(prepared):
            fallback = self._fallback_text(prepared.is_ar)
            yield fallback.encode("utf-8")
            return

        assistant_buf = ""
        for delta in self.answer_chain.stream(
            {"messages": prepared.messages},
            config=self._chain_config(prepared, "answer_stream"),
        ):
            if delta:
                assistant_buf += delta
                yield delta.encode("utf-8")

        prepared.guardrails["output"] = GuardrailResult(allowed=True)
        self.persist_turn(prepared, assistant_buf)

    def prepare(self, req: ChatRequest) -> PreparedChat:
        is_ar = detect_language(req.query)
        rewritten = self._rewrite_query(req.query, is_ar)
        query_embedding = self.embeddings.embed_query(rewritten)

        idx = pinecone_client.Index(req.make)
        validation_matches = self._query_pinecone(
            idx=idx,
            vector=query_embedding,
            namespace=req.model,
            top_k=1,
        )
        context_snip = ""
        if validation_matches:
            context_snip = self._metadata(validation_matches[0]).get("text", "")[:300]

        input_guardrail = self._validate_query(req, is_ar, context_snip)
        guardrails = {"input": input_guardrail}
        if not input_guardrail.allowed:
            return PreparedChat(
                req=req,
                session={},
                is_ar=is_ar,
                rewritten_query=rewritten,
                messages=[],
                source_chunks=[],
                images=[],
                guardrails=guardrails,
            )

        session = self._ensure_session(req)
        retrieval_matches = self._query_pinecone(
            idx=idx,
            vector=query_embedding,
            namespace=req.model,
            top_k=5,
        )
        unique_matches = self._unique_matches(retrieval_matches, limit=3)
        context_full = "\n\n".join(self._metadata(m).get("text", "") for m in unique_matches)[:2000]
        source_chunks = self._source_chunks(unique_matches)
        images = self._images_for_matches(req, unique_matches)
        messages = self._messages(req, is_ar, context_full)

        return PreparedChat(
            req=req,
            session=session,
            is_ar=is_ar,
            rewritten_query=rewritten,
            messages=messages,
            source_chunks=source_chunks,
            images=images,
            guardrails=guardrails,
        )

    def persist_turn(self, prepared: PreparedChat, assistant_text: str) -> None:
        now = datetime.now(timezone.utc)
        req = prepared.req

        history_col.insert_one({
            "session_id": req.session_id,
            "user_id": req.user_id,
            "role": "user",
            "content": req.query,
            "is_ar": prepared.is_ar,
            "images": [],
            "sources": [],
            "guardrails": {},
            "timestamp": now,
        })

        if not prepared.session.get("summary"):
            try:
                title_prompt = f"Generate a concise one-line chat title from this user question:\n\"{req.query}\""
                title = self.title_chain.invoke(
                    {"prompt": title_prompt},
                    config=self._chain_config(prepared, "title"),
                ).strip()
                sessions_col.update_one(
                    {"session_id": req.session_id},
                    {"$set": {"summary": title}},
                )
            except Exception:
                pass

        history_col.insert_one({
            "session_id": req.session_id,
            "user_id": req.user_id,
            "role": "assistant",
            "content": assistant_text,
            "is_ar": False,
            "images": prepared.images,
            "sources": [s.model_dump() for s in prepared.source_chunks],
            "guardrails": {k: v.model_dump() for k, v in prepared.guardrails.items()},
            "timestamp": now,
        })

    def _rewrite_query(self, query: str, is_ar: bool) -> str:
        rewrite_prompt = (
            (
                "أعد صياغة سؤال المستخدم ليصبح مستقلا وواضحا.\n\n"
                f"سؤال المستخدم:\n{query}\n\n"
                "السؤال المعاد صياغته:"
            )
            if is_ar
            else (
                "Rewrite the user's query into a self-contained question.\n\n"
                f"User's new query:\n{query}\n\n"
                "Standalone question:"
            )
        )
        return self.rewrite_chain.invoke({"prompt": rewrite_prompt}).strip()

    def _validate_query(self, req: ChatRequest, is_ar: bool, context_snip: str) -> GuardrailResult:
        val_prompt = (
            (
                f"هل يجب الإجابة على هذا السؤال؟ يجب أن يتعلق فقط بصيانة أو تشخيص {req.make}.\n"
                f"السؤال: {req.query}\nالسياق: {context_snip}\nأجب بنعم أو لا:"
            )
            if is_ar
            else (
                f"Should this question be answered? It must relate solely to {req.make} diagnostics/repairs. YES or NO.\n"
                f"Question: {req.query}\nContext: {context_snip}"
            )
        )
        result = self.validate_chain.invoke({"prompt": val_prompt}).strip().upper()
        if "NO" in result or "لا" in result:
            return GuardrailResult(
                allowed=False,
                reason="Question is outside supported vehicle diagnostics/repair scope.",
                flags=["out_of_scope"],
            )
        return GuardrailResult(allowed=True)

    def _ensure_session(self, req: ChatRequest) -> dict:
        sess = sessions_col.find_one({"session_id": req.session_id, "user_id": req.user_id})
        if sess:
            return sess

        ns = new_session()
        req.session_id = ns["session_id"]
        sessions_col.insert_one({
            "session_id": ns["session_id"],
            "created_at": ns["created_at"],
            "summary": "",
            "user_id": req.user_id,
        })
        return {"session_id": ns["session_id"], "summary": ""}

    def _query_pinecone(self, *, idx, vector: list[float], namespace: str, top_k: int) -> list:
        response = idx.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
            filter={"source": {"$nin": []}, "text": {"$nin": []}},
        )
        if hasattr(response, "matches"):
            return list(response.matches or [])
        return list(response.get("matches", []))

    def _unique_matches(self, matches: Iterable, limit: int) -> list:
        unique, seen = [], set()
        for match in matches:
            text = self._metadata(match).get("text", "")
            if text and text not in seen:
                seen.add(text)
                unique.append(match)
                if len(unique) == limit:
                    break
        return unique

    def _messages(self, req: ChatRequest, is_ar: bool, context: str) -> list[BaseMessage]:
        system_msg = build_system_prompt(req.role, is_ar, req.make, req.model, context)
        messages: list[BaseMessage] = [SystemMessage(content=system_msg)]
        for item in self._short_term_history(req.session_id or ""):
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=req.query))
        return messages

    def _short_term_history(self, session_id: str) -> list[dict]:
        limit = max(settings.short_term_turns, 0) * 2
        if not session_id or limit == 0:
            return []
        docs = list(
            history_col.find({"session_id": session_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        docs.reverse()
        return docs

    def _source_chunks(self, matches: Iterable) -> list[SourceChunk]:
        chunks = []
        for rank, match in enumerate(matches, start=1):
            metadata = self._metadata(match)
            text = metadata.get("text", "")
            source = metadata.get("pdf") or metadata.get("source") or ""
            page = metadata.get("page") or 0
            dense_score = self._score(match)
            chunks.append(SourceChunk(
                chunk_id=str(metadata.get("chunk_id") or self._id(match) or f"dense-{rank}"),
                text=text,
                source=source,
                page=int(page),
                rrf_score=0.0,
                dense_rank=rank,
                dense_score=dense_score,
                metadata={k: v for k, v in metadata.items() if k != "text"},
            ))
        return chunks

    def _images_for_matches(self, req: ChatRequest, matches: Iterable) -> list[dict]:
        images_out = []
        for match in matches:
            for img_id in self._metadata(match).get("image_ids", []):
                doc = mongo_client[req.make.lower()][req.model].find_one({"_id": img_id})
                if not doc or "data" not in doc:
                    continue
                img = Image.open(io.BytesIO(doc["data"]))
                if img.mode in ("1", "L", "P"):
                    img = ImageOps.invert(img.convert("RGB"))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                images_out.append({
                    "id": img_id,
                    "page": doc.get("page", 0),
                    "source": doc.get("pdf", ""),
                    "data": base64.b64encode(buf.getvalue()).decode(),
                })
        return images_out

    def _blocked_response(self, prepared: PreparedChat) -> ChatResponse:
        return ChatResponse(
            assistant_text=self._fallback_text(prepared.is_ar),
            images=[],
            session_id="",
            sources=[],
            guardrails=prepared.guardrails,
        )

    def _fallback_text(self, is_ar: bool) -> str:
        return (
            "أنا متخصص في تشخيص السيارات. يرجى طرح أسئلة متعلقة بالفحص أو الإصلاح."
            if is_ar
            else
            "I specialize in vehicle diagnostics. Please ask about components or repair steps."
        )

    def _is_blocked(self, prepared: PreparedChat) -> bool:
        input_guardrail = prepared.guardrails.get("input")
        return bool(input_guardrail and not input_guardrail.allowed)

    def _chain_config(self, prepared: PreparedChat, run_name: str) -> dict:
        return {
            "run_name": run_name,
            "tags": ["fixmate", "phase1", "dense-only"],
            "metadata": {
                "session_id": prepared.req.session_id,
                "make": prepared.req.make,
                "model": prepared.req.model,
                "rewritten_query": prepared.rewritten_query,
            },
        }

    def _metadata(self, match) -> dict:
        if hasattr(match, "metadata"):
            return match.metadata or {}
        return match.get("metadata", {}) or {}

    def _score(self, match) -> Optional[float]:
        if hasattr(match, "score"):
            return match.score
        return match.get("score")

    def _id(self, match) -> Optional[str]:
        if hasattr(match, "id"):
            return match.id
        return match.get("id")


rag_pipeline = RagPipeline()
