"""Factory for the configured embedding provider.

Anthropic has no embeddings API, so embeddings are configured independently
from LLM_PROVIDER via EMBEDDING_PROVIDER (openai | gemini | local).
"""
from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.core.config import Settings, get_settings


@lru_cache
def get_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()

    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.embedding_model, api_key=settings.openai_api_key
        )

    if settings.embedding_provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model, google_api_key=settings.google_api_key
        )

    if settings.embedding_provider == "local":
        # Runs entirely on-device via sentence-transformers: no API key,
        # no per-call cost. Model weights are downloaded once from the
        # Hugging Face Hub and cached locally.
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
