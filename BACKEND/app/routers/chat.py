# routers/chat.py

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Generator
import io, base64
from PIL import Image, ImageOps
from datetime import datetime, timezone

from app.db import (
    openai_client,
    pinecone_client,
    mongo_client,
    sessions_col,
    history_col
)
from app.models import ChatRequest, ChatResponse
from app.utils import detect_language, build_system_prompt, new_session
from app.openai_client import rewrite_query, embed_text, validate_query

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    # 1️⃣ Language detection
    is_ar = detect_language(req.query)

    # 2️⃣ Rewrite to standalone
    rewrite_prompt = (
        (f"أعد صياغة سؤال المستخدم ليصبح مستقلاً وواضحاً…\n\n"
         f"سؤال المستخدم:\n{req.query}\n\n"
         "السؤال المُعاد صياغته:")
        if is_ar
        else
        (f"Rewrite the user’s query into a self-contained question…\n\n"
         f"User’s new query:\n{req.query}\n\n"
         "Standalone question:")
    )
    rewritten = rewrite_query(rewrite_prompt)

    # 3️⃣ Minimal context for relevance check
    emb = embed_text(rewritten)
    idx = pinecone_client.Index(req.make)
    pine_resp = idx.query(
        vector=emb,
        top_k=1,
        include_metadata=True,
        namespace=req.model,
        filter={"source": {"$nin": []}, "text": {"$nin": []}}
    )
    context_snip = ""
    if pine_resp.get("matches"):
        context_snip = pine_resp["matches"][0].metadata.get("text", "")[:300]

    # 4️⃣ Relevance validation (off-topic if NO)
    val_prompt = (
        (f"هل يجب الإجابة على هذا السؤال؟ يجب أن يتعلق فقط بصيانة أو تشخيص {req.make}.\n"
         f"السؤال: {req.query}\nالسياق: {context_snip}\nأجب بنعم أو لا:")
        if is_ar
        else
        (f"Should this question be answered? It must relate solely to {req.make} diagnostics/repairs. YES or NO.\n"
         f"Question: {req.query}\nContext: {context_snip}")
    )
    if "NO" in validate_query(val_prompt).upper():
        # Off-topic: no session created or stored
        fallback = (
            "أنا متخصص في تشخيص السيارات 🚗. يرجى طرح أسئلة متعلقة بالفحص أو الإصلاح."
            if is_ar else
            "I specialize in vehicle diagnostics 🚗. Please ask about components or repair steps."
        )
        return ChatResponse(assistant_text=fallback, images=[], session_id="")

    # 5️⃣ Session init or reuse
    sess = sessions_col.find_one({"session_id": req.session_id, "user_id": req.user_id})
    if not sess:
        ns = new_session()
        req.session_id = ns["session_id"]
        sessions_col.insert_one({
            "session_id": ns["session_id"],
            "created_at": ns["created_at"],
            "summary": "",
            "user_id": req.user_id
        })
        sess = {"session_id": ns["session_id"], "summary": ""}

    # 6️⃣ Retrieve full context (up to 3)
    pine_resp = idx.query(
        vector=emb,
        top_k=5,
        include_metadata=True,
        namespace=req.model,
        filter={"source": {"$nin": []}, "text": {"$nin": []}}
    )
    unique, seen = [], set()
    for m in pine_resp.get("matches", []):
        t = m.metadata.get("text", "")
        if t and t not in seen:
            seen.add(t)
            unique.append(m)
            if len(unique) == 3:
                break
    context_full = "\n\n".join(m.metadata["text"] for m in unique)[:2000]

    # 7️⃣ Build system prompt & message stack
    system_msg = build_system_prompt(req.role, is_ar, req.make, req.model, context_full)
    past = list(history_col.find({"session_id": req.session_id}).sort("timestamp", 1))
    messages = [{"role": "system", "content": system_msg}] + [
        {"role": h["role"], "content": h["content"]} for h in past
    ] + [{"role": "user", "content": req.query}]

    # 8️⃣ Call OpenAI
    chat_resp = openai_client.chat.completions.create(
        model="gpt-4o", messages=messages, temperature=0.0
    )
    assistant_text = chat_resp.choices[0].message.content

    # 9️⃣ Fetch & encode images
    images_out = []
    for match in unique:
        for img_id in match.metadata.get("image_ids", []):
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
                "data": base64.b64encode(buf.getvalue()).decode()
            })

    now = datetime.now(timezone.utc)

    # 🔟 Persist history: user
    history_col.insert_one({
        "session_id": req.session_id,
        "user_id": req.user_id,
        "role": "user",
        "content": req.query,
        "is_ar": is_ar,
        "images": [],
        "timestamp": now
    })

    # — Generate & store title on first message —
    if not sess.get("summary"):
        try:
            title_prompt = f"Generate a concise one-line chat title from this user question:\n\"{req.query}\""
            title = rewrite_query(title_prompt).strip()
            sessions_col.update_one(
                {"session_id": req.session_id},
                {"$set": {"summary": title}}
            )
        except:
            pass

    # ⓫ Persist history: assistant
    history_col.insert_one({
        "session_id": req.session_id,
        "user_id": req.user_id,
        "role": "assistant",
        "content": assistant_text,
        "is_ar": False,
        "images": images_out,
        "timestamp": now
    })

    return ChatResponse(
        assistant_text=assistant_text,
        images=images_out,
        session_id=req.session_id
    )


@router.post("/stream")
def chat_stream(req: ChatRequest, request: Request):
    # 1️⃣ Language detection & rewrite
    is_ar = detect_language(req.query)
    rewrite_prompt = (
        (f"أعد صياغة سؤال المستخدم ليصبح مستقلاً وواضحاً…\n\n"
         f"سؤال المستخدم:\n{req.query}\n\n"
         "السؤال المُعاد صياغته:")
        if is_ar
        else
        (f"Rewrite the user’s query into a self-contained question…\n\n"
         f"User’s new query:\n{req.query}\n\n"
         "Standalone question:")
    )
    rewritten = rewrite_query(rewrite_prompt)

    # 2️⃣ Minimal context & relevance check
    emb = embed_text(rewritten)
    idx = pinecone_client.Index(req.make)
    pine_resp = idx.query(
        vector=emb,
        top_k=1,
        include_metadata=True,
        namespace=req.model,
        filter={"source": {"$nin": []}, "text": {"$nin": []}}
    )
    snip = ""
    if pine_resp.get("matches"):
        snip = pine_resp["matches"][0].metadata.get("text", "")[:300]

    val_prompt = (
        (f"هل يجب الإجابة على هذا السؤال؟ يجب أن يتعلق فقط بصيانة أو تشخيص {req.make}.\n"
         f"السؤال: {req.query}\nالسياق: {snip}\nأجب بنعم أو لا:")
        if is_ar
        else
        (f"Should this question be answered? It must relate solely to {req.make} diagnostics/repairs. YES or NO.\n"
         f"Question: {req.query}\nContext: {snip}")
    )
    if "NO" in validate_query(val_prompt).upper():
        # Off-topic: single-chunk fallback, no DB writes
        fallback = (
            "أنا متخصص في تشخيص السيارات 🚗. يرجى طرح أسئلة متعلقة بالفحص أو الإصلاح."
            if is_ar else
            "I specialize in vehicle diagnostics 🚗. Please ask about components or repair steps."
        )
        def gen() -> Generator[bytes, None, None]:
            yield fallback.encode("utf-8")
        return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")

    # 3️⃣ Session init or reuse
    sess = sessions_col.find_one({"session_id": req.session_id, "user_id": req.user_id})
    if not sess:
        ns = new_session()
        req.session_id = ns["session_id"]
        sessions_col.insert_one({
            "session_id": ns["session_id"],
            "created_at": ns["created_at"],
            "summary": "",
            "user_id": req.user_id
        })
        sess = {"session_id": ns["session_id"], "summary": ""}

    # 4️⃣ Retrieve full context (up to 3)
    pine_resp = idx.query(
        vector=emb,
        top_k=5,
        include_metadata=True,
        namespace=req.model,
        filter={"source": {"$nin": []}, "text": {"$nin": []}}
    )
    unique, seen = [], set()
    for m in pine_resp.get("matches", []):
        t = m.metadata.get("text", "")
        if t and t not in seen:
            seen.add(t)
            unique.append(m)
            if len(unique) == 3:
                break
    context_full = "\n\n".join(m.metadata["text"] for m in unique)[:2000]

    # 5️⃣ Build system msg & past messages
    system_msg = build_system_prompt(req.role, is_ar, req.make, req.model, context_full)
    past = list(history_col.find({"session_id": req.session_id}).sort("timestamp", 1))
    messages = [{"role": "system", "content": system_msg}] + [
        {"role": h["role"], "content": h["content"]} for h in past
    ] + [{"role": "user", "content": req.query}]

    # 6️⃣ Pre-fetch images
    images_out = []
    for match in unique:
        for img_id in match.metadata.get("image_ids", []):
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
                "data": base64.b64encode(buf.getvalue()).decode()
            })

    # 7️⃣ Stream GPT response
    ai_stream = openai_client.chat.completions.create(
        model="gpt-4o", messages=messages, temperature=0.0, stream=True
    )

    def event_generator() -> Generator[bytes, None, None]:
        assistant_buf = ""
        for chunk in ai_stream:
            delta = getattr(chunk.choices[0].delta, "content", None)
            if delta:
                assistant_buf += delta
                yield delta.encode("utf-8")

        now = datetime.now(timezone.utc)

        # persist user turn
        history_col.insert_one({
            "session_id": req.session_id,
            "user_id": req.user_id,
            "role": "user",
            "content": req.query,
            "is_ar": is_ar,
            "images": [],
            "timestamp": now
        })

        # generate & store title on first message
        if not sess.get("summary"):
            try:
                title_prompt = f"Generate a concise one-line chat title from this user question:\n\"{req.query}\""
                title = rewrite_query(title_prompt).strip()
                sessions_col.update_one(
                    {"session_id": req.session_id},
                    {"$set": {"summary": title}}
                )
            except:
                pass

        # persist assistant turn
        history_col.insert_one({
            "session_id": req.session_id,
            "user_id": req.user_id,
            "role": "assistant",
            "content": assistant_buf,
            "is_ar": False,
            "images": images_out,
            "timestamp": now
        })

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")
