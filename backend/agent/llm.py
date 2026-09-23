import os
from core.config import settings


def get_llm(custom_key: str = None, custom_model: str = None):
    """Returns the configured Chat model with tool-calling capabilities.
    If custom_key is provided (BYOK), instantiates ChatOpenAI with user's key and model.
    """
    if custom_key and custom_key.strip():
        from langchain_openai import ChatOpenAI
        model_name = custom_model.strip() if custom_model and custom_model.strip() else settings.OPENROUTER_MODEL
        return ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=custom_key.strip(),
            base_url="https://openrouter.ai/api/v1",
            max_retries=2,
        )

    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1,
            )
        except ImportError:
            pass

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.1,
            )
        except ImportError:
            pass

    if provider == "groq" and settings.GROQ_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.1,
            max_retries=2,
        )

    # Default to OpenRouter (compatible with OpenAI interface and free models)
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.1,
        api_key=settings.OPENROUTER_API_KEY or "free_key",
        base_url=settings.OPENROUTER_BASE_URL,
        max_retries=2,
    )
