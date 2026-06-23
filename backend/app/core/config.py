import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    groq_api_key: str
    hf_token: str | None
    qdrant_url: str
    qdrant_collection: str
    embedding_model: str
    cors_origins: tuple[str, ...]
    max_pdf_bytes: int
    max_request_bytes: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
    auth_rate_limit_attempts: int
    auth_rate_limit_window_seconds: int
    max_sessions: int
    session_ttl_seconds: int


def _required_env(name: str, *fallbacks: str) -> str:
    for candidate in (name, *fallbacks):
        value = os.getenv(candidate)
        if value:
            return value
    raise ValueError(f"La variable de entorno {name} es requerida")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        supabase_url=_required_env("SUPABASE_URL"),
        supabase_anon_key=_required_env("SUPABASE_ANON_KEY"),
        supabase_service_key=_required_env("SUPABASE_SERVICE_KEY"),
        groq_api_key=_required_env("GROQ_API_KEY"),
        hf_token=os.getenv("HF_TOKEN"),
        qdrant_url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
        qdrant_collection=os.getenv(
            "QDRANT_COLLECTION",
            "leyes_peru",
        ),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL",
            "paraphrase-multilingual-mpnet-base-v2",
        ),
        cors_origins=tuple(
            origin.strip()
            for origin in origins.split(",")
            if origin.strip()
        ),
        max_pdf_bytes=int(os.getenv("MAX_PDF_BYTES", 10 * 1024 * 1024)),
        max_request_bytes=int(
            os.getenv("MAX_REQUEST_BYTES", 12 * 1024 * 1024)
        ),
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "120")),
        rate_limit_window_seconds=int(
            os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
        ),
        auth_rate_limit_attempts=int(
            os.getenv("AUTH_RATE_LIMIT_ATTEMPTS", "5")
        ),
        auth_rate_limit_window_seconds=int(
            os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", str(15 * 60))
        ),
        max_sessions=int(os.getenv("MAX_SESSIONS", "100")),
        session_ttl_seconds=int(
            os.getenv("SESSION_TTL_SECONDS", str(2 * 60 * 60))
        ),
    )
