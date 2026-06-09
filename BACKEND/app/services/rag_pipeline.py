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
from app.db import mongo_client, sessions_col, history_col
from app.models import ChatRequest, ChatResponse, GuardrailResult, SourceChunk
from app.services.guardrails import guardrails
from app.services.retrieval import RetrievalCandidate, hybrid_retriever
from app.utils import build_system_prompt, detect_language, new_session


@dataclass
class PreparedChat:
    req: ChatRequest
    session: dict
    is_ar: bool
    rewritten_query: str
    messages: list[BaseMessage]
    retrieval_candidates: list[RetrievalCandidate]
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
        self.title_chain = prompt | rewrite_llm | StrOutputParser()
        self.answer_chain = RunnableLambda(lambda state: state["messages"]) | answer_llm | StrOutputParser()
        self.revision_chain = prompt | answer_llm | StrOutputParser()
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
        assistant_text = self._apply_output_guardrails(prepared, assistant_text)
        self.persist_turn(prepared, assistant_text)
        return ChatResponse(
            assistant_text=assistant_text,
            images=prepared.images,
            session_id=prepared.req.session_id or "",
            sources=prepared.source_chunks,
            guardrails=prepared.guardrails,
        )

    def stream(self, req: ChatRequest) -> Generator[bytes, None, None]:
        prepared = self.prepare(req, include_images=False)
        if self._is_blocked(prepared):
            fallback = self._fallback_text(prepared.is_ar)
            yield fallback.encode("utf-8")
            try:
                self.persist_turn(prepared, fallback)
            except Exception:
                pass
            return

        chunks: list[str] = []
        for chunk in self.answer_chain.stream(
            {"messages": prepared.messages},
            config=self._chain_config(prepared, "answer_stream"),
        ):
            if not chunk:
                continue
            chunks.append(chunk)
            yield chunk.encode("utf-8")

        assistant_text = "".join(chunks)
        assistant_text = self._apply_output_guardrails(prepared, assistant_text)
        prepared.images = self._images_for_candidates(
            prepared.req,
            prepared.retrieval_candidates,
        )
        self.persist_turn(prepared, assistant_text)

    def prepare(self, req: ChatRequest, *, include_images: bool = True) -> PreparedChat:
        is_ar = detect_language(req.query)
        input_guardrail = guardrails.check_input(req)
        guardrails_map = {"input": input_guardrail}
        if not input_guardrail.allowed:
            return PreparedChat(
                req=req,
                session={},
                is_ar=is_ar,
                rewritten_query="",
                messages=[],
                retrieval_candidates=[],
                source_chunks=[],
                images=[],
                guardrails=guardrails_map,
            )

        rewritten = self._rewrite_query(req.query, is_ar)
        query_embedding = self.embeddings.embed_query(rewritten)

        session = self._ensure_session(req)
        retrieval_candidates = hybrid_retriever.runnable.invoke(
            {
                "req": req,
                "rewritten_query": rewritten,
                "query_embedding": query_embedding,
            },
            config=self._chain_config_for_req(req, rewritten, "hybrid_retrieval"),
        )
        context_full = hybrid_retriever.build_context(retrieval_candidates)
        source_chunks = hybrid_retriever.to_source_chunks(retrieval_candidates)
        images = self._images_for_candidates(req, retrieval_candidates) if include_images else []
        messages = self._messages(req, is_ar, context_full)

        return PreparedChat(
            req=req,
            session=session,
            is_ar=is_ar,
            rewritten_query=rewritten,
            messages=messages,
            retrieval_candidates=retrieval_candidates,
            source_chunks=source_chunks,
            images=images,
            guardrails=guardrails_map,
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

    def _apply_output_guardrails(self, prepared: PreparedChat, assistant_text: str) -> str:
        first = guardrails.check_output(
            question=prepared.req.query,
            answer=assistant_text,
            sources=prepared.source_chunks,
        )
        if first.should_revise and settings.revise_ungrounded_output:
            revised_text = self.revision_chain.invoke(
                {
                    "prompt": self._revision_prompt(
                        question=prepared.req.query,
                        draft=first.text,
                        sources=prepared.source_chunks,
                    )
                },
                config=self._chain_config(prepared, "revise_ungrounded_answer"),
            ).strip()
            second = guardrails.check_output(
                question=prepared.req.query,
                answer=revised_text,
                sources=prepared.source_chunks,
            )
            second.result.flags = list(dict.fromkeys(["revised_for_grounding", *second.result.flags]))
            second.result.details["initial_output_guardrail"] = first.result.model_dump()
            prepared.guardrails["output"] = second.result
            return second.text

        prepared.guardrails["output"] = first.result
        return first.text

    def _revision_prompt(self, *, question: str, draft: str, sources: list[SourceChunk]) -> str:
        if not sources:
            return (
                "Rewrite the draft answer as a concise refusal because no retrieved manual context is available. "
                "Do not add facts, procedures, specs, part numbers, or external references.\n\n"
                f"Question:\n{question}\n\nDraft answer:\n{draft}"
            )
        context = "\n\n".join(
            f"[{source.chunk_id} | {source.source} p.{source.page}]\n{source.text}"
            for source in sources
        )
        return f"""
Revise the draft answer so every factual claim is grounded only in the retrieved context.

Rules:
- Use only the retrieved context.
- Remove unsupported claims, specifications, steps, or part references.
- If the context is insufficient, say what cannot be confirmed from the retrieved manual context.
- Do not include emails, phone numbers, addresses, API keys, database URIs, or other PII/secrets.

Question:
{question}

Retrieved context:
{context}

Draft answer:
{draft}
""".strip()

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

    def _images_for_candidates(self, req: ChatRequest, candidates: Iterable[RetrievalCandidate]) -> list[dict]:
        images_out = []
        seen = set()
        for candidate in list(candidates)[: settings.image_candidate_top_k]:
            for img_id in candidate.image_ids:
                if len(images_out) >= settings.max_retrieved_images:
                    return images_out
                if img_id in seen:
                    continue
                seen.add(img_id)
                doc = mongo_client[req.make.lower()][req.model].find_one({"_id": img_id})
                if not doc or "data" not in doc:
                    continue
                try:
                    img = Image.open(io.BytesIO(doc["data"]))
                    if img.mode in ("1", "L", "P"):
                        img = ImageOps.invert(img.convert("RGB"))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                except Exception:
                    continue
                images_out.append({
                    "id": img_id,
                    "page": doc.get("page", 0),
                    "source": doc.get("pdf", ""),
                    "data": base64.b64encode(buf.getvalue()).decode(),
                })
        return images_out

    def _blocked_response(self, prepared: PreparedChat) -> ChatResponse:
        fallback = self._fallback_text(prepared.is_ar)
        self.persist_turn(prepared, fallback)
        return ChatResponse(
            assistant_text=fallback,
            images=[],
            session_id=prepared.req.session_id or "",
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
            "tags": ["fixmate", "phase3", "hybrid-rrf", "guardrails"],
            "metadata": {
                "session_id": prepared.req.session_id,
                "make": prepared.req.make,
                "model": prepared.req.model,
                "rewritten_query": prepared.rewritten_query,
                "rrf_k": settings.rrf_k,
                "dense_candidates": settings.dense_candidates,
                "bm25_candidates": settings.bm25_candidates,
                "context_top_k": settings.context_top_k,
            },
        }

    def _chain_config_for_req(self, req: ChatRequest, rewritten_query: str, run_name: str) -> dict:
        return {
            "run_name": run_name,
            "tags": ["fixmate", "phase3", "hybrid-rrf", "guardrails"],
            "metadata": {
                "session_id": req.session_id,
                "make": req.make,
                "model": req.model,
                "rewritten_query": rewritten_query,
                "rrf_k": settings.rrf_k,
                "dense_candidates": settings.dense_candidates,
                "bm25_candidates": settings.bm25_candidates,
                "context_top_k": settings.context_top_k,
            },
        }


rag_pipeline = RagPipeline()
