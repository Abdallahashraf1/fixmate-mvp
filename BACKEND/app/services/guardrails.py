import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models import ChatRequest, GuardrailResult, SourceChunk


@dataclass
class OutputGuardrailDecision:
    text: str
    result: GuardrailResult
    should_revise: bool = False


class Guardrails:
    def __init__(self) -> None:
        prompt = ChatPromptTemplate.from_messages([("user", "{prompt}")])
        llm = ChatOpenAI(
            model=settings.guardrail_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        self.classifier_chain = prompt | llm | StrOutputParser()

    def check_input(self, req: ChatRequest) -> GuardrailResult:
        injection = self._detect_prompt_injection(req.query)
        if injection:
            return GuardrailResult(
                allowed=False,
                reason="Prompt injection attempt detected.",
                flags=["prompt_injection"],
                details={"query_type": "prompt_injection", "matches": injection},
            )

        prompt = f"""
Classify this FixMate user query.

Allowed scope:
- vehicle diagnostics
- repair procedures
- maintenance procedures
- vehicle components, symptoms, trouble codes, wiring, fluids, parts, diagrams, or manual summaries
- questions about the selected vehicle make/model

Block if unrelated to vehicle diagnostics, repair, maintenance, or manual content.

Selected vehicle:
make: {req.make}
model: {req.model}

Return only valid JSON with this schema:
{{
  "allowed": true,
  "query_type": "factual | diagnostic | procedure | summarization | image_or_diagram | out_of_scope",
  "reason": "short reason"
}}

Query:
{req.query}
""".strip()
        try:
            data = self._load_json(self.classifier_chain.invoke({"prompt": prompt}))
        except Exception:
            return GuardrailResult(
                allowed=True,
                reason="Input classifier failed open.",
                flags=["classifier_error"],
                details={"query_type": "unknown"},
            )

        allowed = bool(data.get("allowed"))
        query_type = str(data.get("query_type") or "unknown")
        flags = [] if allowed else ["out_of_scope"]
        return GuardrailResult(
            allowed=allowed,
            reason=str(data.get("reason") or ""),
            flags=flags,
            details={"query_type": query_type},
        )

    def check_output(
        self,
        *,
        question: str,
        answer: str,
        sources: list[SourceChunk],
    ) -> OutputGuardrailDecision:
        pii_text, pii_flags, pii_details = self._redact_pii(answer)
        grounding = self._check_grounding(question=question, answer=pii_text, sources=sources)

        flags = []
        if pii_flags:
            flags.extend(pii_flags)
        if not grounding.allowed:
            flags.extend(grounding.flags)

        allowed = grounding.allowed
        reason_parts = []
        if pii_flags:
            reason_parts.append("PII or secret-like data was redacted.")
        if not grounding.allowed:
            reason_parts.append(grounding.reason or "Answer may contain unsupported claims.")

        return OutputGuardrailDecision(
            text=pii_text,
            result=GuardrailResult(
                allowed=allowed,
                reason=" ".join(reason_parts) or "Output passed guardrails.",
                flags=flags,
                details={
                    "pii": pii_details,
                    "grounding": grounding.details,
                },
            ),
            should_revise=not grounding.allowed,
        )

    def _check_grounding(
        self,
        *,
        question: str,
        answer: str,
        sources: list[SourceChunk],
    ) -> GuardrailResult:
        if not answer.strip():
            return GuardrailResult(allowed=True, reason="Empty answer.", details={"grounded": True})
        if not sources:
            insufficient_context_markers = [
                "no retrieved manual context",
                "cannot be confirmed",
                "insufficient context",
                "not enough context",
                "لا يمكن تأكيد",
                "السياق غير كاف",
            ]
            if any(marker in answer.lower() for marker in insufficient_context_markers):
                return GuardrailResult(
                    allowed=True,
                    reason="Answer is a grounded insufficient-context fallback.",
                    details={"grounded": True, "unsupported_claims": [], "source_chunk_ids": []},
                )
            return GuardrailResult(
                allowed=False,
                reason="No retrieved context was available to ground the answer.",
                flags=["ungrounded"],
                details={"grounded": False, "unsupported_claims": [], "source_chunk_ids": []},
            )

        context = "\n\n".join(
            f"[{source.chunk_id} | {source.source} p.{source.page}]\n{source.text}"
            for source in sources
        )
        prompt = f"""
You are a grounding evaluator for a retrieval-augmented vehicle repair assistant.

Decide whether the answer is supported by the retrieved context. Ignore style and wording. Focus on factual claims, procedures, specifications, part references, and safety claims.

Return only valid JSON:
{{
  "grounded": true,
  "unsupported_claims": ["claim not supported by context"],
  "source_chunk_ids": ["chunk id used as evidence"],
  "reason": "short explanation"
}}

Question:
{question}

Retrieved context:
{context}

Answer:
{answer}
""".strip()
        try:
            data = self._load_json(self.classifier_chain.invoke({"prompt": prompt}))
        except Exception:
            return GuardrailResult(
                allowed=True,
                reason="Grounding classifier failed open.",
                flags=["grounding_classifier_error"],
                details={"grounded": True, "unsupported_claims": [], "source_chunk_ids": []},
            )

        grounded = bool(data.get("grounded"))
        unsupported = data.get("unsupported_claims") or []
        source_ids = data.get("source_chunk_ids") or []
        return GuardrailResult(
            allowed=grounded,
            reason=str(data.get("reason") or ""),
            flags=[] if grounded else ["ungrounded"],
            details={
                "grounded": grounded,
                "unsupported_claims": unsupported,
                "source_chunk_ids": source_ids,
            },
        )

    def _redact_pii(self, text: str) -> tuple[str, list[str], dict[str, Any]]:
        redacted = text
        detected: dict[str, int] = {}

        patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "credit_card": r"\b(?:\d[ -]*?){13,19}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "api_key": r"\b(?:sk-[A-Za-z0-9_-]{20,}|pcsk_[A-Za-z0-9_-]{20,})\b",
            "mongodb_uri": r"mongodb(?:\+srv)?://[^\s)]+",
            "phone": r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
            "address": r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,5}\s+(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b",
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, redacted, flags=re.IGNORECASE)
            if matches:
                detected[pii_type] = len(matches)
                redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted, flags=re.IGNORECASE)

        flags = ["pii_redacted"] if detected else []
        return redacted, flags, {"detected": detected}

    def _detect_prompt_injection(self, text: str) -> list[str]:
        patterns = [
            r"ignore (?:all )?(?:previous|prior|above) instructions",
            r"disregard (?:all )?(?:previous|prior|above) instructions",
            r"reveal (?:the )?(?:system|developer) prompt",
            r"show (?:me )?(?:the )?(?:system|developer) prompt",
            r"print (?:the )?(?:system|developer) prompt",
            r"developer message",
            r"system message",
            r"hidden instructions",
            r"jailbreak",
            r"\bdan\b",
            r"act as",
            r"pretend to be",
            r"override (?:your|the) instructions",
            r"bypass (?:the )?(?:safety|guardrails|instructions)",
            r"repeat (?:your|the) instructions",
            r"prompt injection",
        ]
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                matches.append(pattern)
        return matches

    def _load_json(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned)


guardrails = Guardrails()
