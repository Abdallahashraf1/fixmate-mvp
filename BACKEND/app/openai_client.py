# openai_client.py:
from app.db import openai_client

def rewrite_query(prompt: str) -> str:
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return resp.choices[0].message.content.strip()

def validate_query(prompt: str) -> str:
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return resp.choices[0].message.content.strip().upper()

def embed_text(text: str):
    emb = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    ).data[0].embedding
    return emb

def chat_completion(messages: list):
    resp = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0
    )
    return resp.choices[0].message.content