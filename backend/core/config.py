import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

# Search for .env in backend directory, then fallback to root directory
_backend_env = Path(__file__).parent.parent / ".env"
_root_env = Path(__file__).parent.parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(dotenv_path=_backend_env)
elif _root_env.exists():
    load_dotenv(dotenv_path=_root_env)
else:
    load_dotenv()


class Settings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    APP_NAME: str = "Mahindra Automotive OEM Conversational Agent"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # LLM Provider Configuration: 'openrouter', 'gemini', or 'ollama'
    LLM_PROVIDER: Literal["openrouter", "gemini", "ollama", "groq"] = os.getenv("LLM_PROVIDER", "openrouter")  # type: ignore

    # OpenRouter Config (Free models supported)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Groq Free Tier Config (https://console.groq.com/keys)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Google Gemini Config
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    # Ollama Local Config
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Zoho CRM OAuth 2.0 Settings
    USE_MOCK_ZOHO: bool = os.getenv("USE_MOCK_ZOHO", "true").lower() in ("true", "1", "yes")
    ZOHO_CLIENT_ID: Optional[str] = os.getenv("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET: Optional[str] = os.getenv("ZOHO_CLIENT_SECRET")
    ZOHO_REFRESH_TOKEN: Optional[str] = os.getenv("ZOHO_REFRESH_TOKEN")

    # Data Center Specific Domains (Accounts & API must match the registered DC)
    # Options for DC: in (India), com (US), eu (Europe), com.au (Australia)
    ZOHO_DC: str = os.getenv("ZOHO_DC", "in")
    ZOHO_ACCOUNTS_URL: str = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
    ZOHO_API_BASE_URL: str = os.getenv("ZOHO_API_BASE_URL", "https://www.zohoapis.in/crm/v8")


settings = Settings()
