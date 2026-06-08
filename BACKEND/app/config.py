import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in BACKEND/.env or the deployment environment."
        )
    return value


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    pinecone_api_key: str
    mongo_uri: str
    short_term_turns: int
    rewrite_model: str
    answer_model: str


settings = Settings(
    openai_api_key=_required_env("OPENAI_API_KEY"),
    pinecone_api_key=_required_env("PINECONE_API_KEY"),
    mongo_uri=_required_env("MONGO_URI"),
    short_term_turns=int(os.getenv("SHORT_TERM_TURNS", "6")),
    rewrite_model=os.getenv("OPENAI_REWRITE_MODEL", "gpt-4o-mini"),
    answer_model=os.getenv("OPENAI_ANSWER_MODEL", "gpt-4o"),
)
