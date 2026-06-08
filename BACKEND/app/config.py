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


settings = Settings(
    openai_api_key=_required_env("OPENAI_API_KEY"),
    pinecone_api_key=_required_env("PINECONE_API_KEY"),
    mongo_uri=_required_env("MONGO_URI"),
)
