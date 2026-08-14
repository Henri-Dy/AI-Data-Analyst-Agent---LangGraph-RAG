"""Application settings, loaded from environment variables / .env."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Data Analyst Agent"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_data_analyst"

    # LLM provider selection
    llm_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    # Embeddings for RAG (Anthropic has no embeddings API, so this is
    # independent from llm_provider and defaults to OpenAI).
    embedding_provider: Literal["openai", "gemini"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # RAG retrieval
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 100
    rag_top_k: int = 5

    # Observability (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "ai-data-analyst"

    # Security / limits
    max_sql_rows: int = 10_000
    sql_timeout_seconds: int = 15
    max_upload_size_mb: int = 50
    max_sql_fix_attempts: int = 3

    # Human-in-the-loop
    confidence_threshold: float = 0.70


@lru_cache
def get_settings() -> Settings:
    return Settings()
