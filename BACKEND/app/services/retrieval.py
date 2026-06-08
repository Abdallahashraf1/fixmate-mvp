from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.runnables import RunnableLambda
from pymongo.errors import PyMongoError

from app.config import settings
from app.db import mongo_client, pinecone_client
from app.models import ChatRequest, SourceChunk


@dataclass
class RetrievalCandidate:
    chunk_id: str
    text: str
    source: str
    page: int
    image_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rrf_score: float = 0.0


class HybridRetriever:
    def __init__(self) -> None:
        self.chunks_col = mongo_client[settings.chunks_db][settings.chunks_collection]
        self.runnable = RunnableLambda(lambda payload: self.retrieve(**payload))

    def retrieve(
        self,
        *,
        req: ChatRequest,
        rewritten_query: str,
        query_embedding: list[float],
    ) -> list[RetrievalCandidate]:
        dense = self.dense_search(req=req, query_embedding=query_embedding, top_k=settings.dense_candidates)
        bm25 = self.bm25_search(req=req, rewritten_query=rewritten_query, top_k=settings.bm25_candidates)
        return self.rrf_fuse(dense=dense, bm25=bm25, top_k=settings.context_top_k)

    def dense_search(
        self,
        *,
        req: ChatRequest,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievalCandidate]:
        idx = pinecone_client.Index(req.make)
        response = idx.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=req.model,
            filter={"source": {"$nin": []}, "text": {"$nin": []}},
        )
        matches = list(response.matches or []) if hasattr(response, "matches") else list(response.get("matches", []))
        candidates = []
        for rank, match in enumerate(matches, start=1):
            metadata = self._match_metadata(match)
            text = metadata.get("text", "")
            if not text:
                continue
            chunk_id = str(metadata.get("chunk_id") or self._match_id(match) or f"dense-{rank}")
            candidates.append(RetrievalCandidate(
                chunk_id=chunk_id,
                text=text,
                source=metadata.get("pdf") or metadata.get("source") or "",
                page=int(metadata.get("page") or 0),
                image_ids=list(metadata.get("image_ids") or []),
                metadata={**metadata, "pinecone_id": self._match_id(match)},
                dense_rank=rank,
                dense_score=self._match_score(match),
            ))
        return candidates

    def bm25_search(
        self,
        *,
        req: ChatRequest,
        rewritten_query: str,
        top_k: int,
    ) -> list[RetrievalCandidate]:
        if not rewritten_query.strip():
            return []
        try:
            cursor = (
                self.chunks_col.find(
                    {
                        "$text": {"$search": rewritten_query},
                        "make": req.make,
                        "model": req.model,
                        "namespace": req.model,
                        "is_active": {"$ne": False},
                    },
                    {
                        "_id": 0,
                        "score": {"$meta": "textScore"},
                        "chunk_id": 1,
                        "pinecone_id": 1,
                        "text": 1,
                        "pdf": 1,
                        "page": 1,
                        "image_ids": 1,
                        "make": 1,
                        "model": 1,
                        "namespace": 1,
                        "schema_version": 1,
                    },
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(top_k)
            )
            docs = list(cursor)
        except PyMongoError:
            return []

        candidates = []
        for rank, doc in enumerate(docs, start=1):
            text = doc.get("text", "")
            if not text:
                continue
            chunk_id = str(doc.get("chunk_id") or doc.get("pinecone_id") or f"bm25-{rank}")
            candidates.append(RetrievalCandidate(
                chunk_id=chunk_id,
                text=text,
                source=doc.get("pdf", ""),
                page=int(doc.get("page") or 0),
                image_ids=list(doc.get("image_ids") or []),
                metadata={k: v for k, v in doc.items() if k not in {"text", "score"}},
                bm25_rank=rank,
                bm25_score=float(doc.get("score") or 0.0),
            ))
        return candidates

    def rrf_fuse(
        self,
        *,
        dense: list[RetrievalCandidate],
        bm25: list[RetrievalCandidate],
        top_k: int,
    ) -> list[RetrievalCandidate]:
        merged: dict[str, RetrievalCandidate] = {}

        for candidate in dense:
            existing = merged.setdefault(candidate.chunk_id, candidate)
            existing.dense_rank = candidate.dense_rank
            existing.dense_score = candidate.dense_score
            existing.rrf_score += self._rrf(candidate.dense_rank)

        for candidate in bm25:
            existing = merged.get(candidate.chunk_id)
            if existing is None:
                existing = candidate
                merged[candidate.chunk_id] = existing
            else:
                existing.bm25_rank = candidate.bm25_rank
                existing.bm25_score = candidate.bm25_score
                existing.metadata = {**candidate.metadata, **existing.metadata}
                if not existing.image_ids and candidate.image_ids:
                    existing.image_ids = candidate.image_ids
                if not existing.source and candidate.source:
                    existing.source = candidate.source
                if not existing.page and candidate.page:
                    existing.page = candidate.page
            existing.rrf_score += self._rrf(candidate.bm25_rank)

        return sorted(
            merged.values(),
            key=lambda item: (item.rrf_score, item.dense_score or 0.0, item.bm25_score or 0.0),
            reverse=True,
        )[:top_k]

    def to_source_chunks(self, candidates: list[RetrievalCandidate]) -> list[SourceChunk]:
        return [
            SourceChunk(
                chunk_id=c.chunk_id,
                text=c.text,
                source=c.source,
                page=c.page,
                rrf_score=c.rrf_score,
                dense_rank=c.dense_rank,
                bm25_rank=c.bm25_rank,
                dense_score=c.dense_score,
                bm25_score=c.bm25_score,
                metadata={**c.metadata, "image_ids": c.image_ids},
            )
            for c in candidates
        ]

    def build_context(self, candidates: list[RetrievalCandidate]) -> str:
        sections = []
        total = 0
        for idx, candidate in enumerate(candidates, start=1):
            header = (
                f"[Chunk {idx} | id={candidate.chunk_id} | pdf={candidate.source} | "
                f"page={candidate.page} | rrf={candidate.rrf_score:.6f}]"
            )
            section = f"{header}\n{candidate.text.strip()}"
            if not section.strip():
                continue
            if total + len(section) > settings.rag_context_char_limit:
                remaining = settings.rag_context_char_limit - total
                if remaining <= len(header) + 50:
                    break
                section = section[:remaining]
            sections.append(section)
            total += len(section)
            if total >= settings.rag_context_char_limit:
                break
        return "\n\n".join(sections)

    def _rrf(self, rank: Optional[int]) -> float:
        if not rank:
            return 0.0
        return 1.0 / (settings.rrf_k + rank)

    def _match_metadata(self, match) -> dict:
        if hasattr(match, "metadata"):
            return match.metadata or {}
        return match.get("metadata", {}) or {}

    def _match_score(self, match) -> Optional[float]:
        if hasattr(match, "score"):
            return match.score
        return match.get("score")

    def _match_id(self, match) -> Optional[str]:
        if hasattr(match, "id"):
            return match.id
        return match.get("id")


hybrid_retriever = HybridRetriever()
