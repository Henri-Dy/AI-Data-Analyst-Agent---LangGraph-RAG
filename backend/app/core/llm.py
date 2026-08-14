"""Factory for the configured chat LLM provider (OpenAI, Anthropic, or Gemini)."""
from langchain_core.language_models import BaseChatModel

from app.core.config import Settings, get_settings


def get_chat_model(settings: Settings | None = None, temperature: float = 0.0) -> BaseChatModel:
    settings = settings or get_settings()

    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key, temperature=temperature)

    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-3-5-sonnet-latest", api_key=settings.anthropic_api_key, temperature=temperature
        )

    if settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=settings.google_api_key, temperature=temperature
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
