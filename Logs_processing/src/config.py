"""Configuration management using pydantic-settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Calculate paths
BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    OPENAI_API_KEY: str = Field(
        ...,
        description="API Key for OpenAI or compatible provider.",
    )
    MODEL_NAME: str = Field(
        "gpt-4o-mini",
        description="Model to use for extraction (e.g., gpt-4o, claude-3-opus).",
    )
    
    # App Settings
    LOG_LEVEL: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR).")
    
    # Paths
    DATA_DIR: Path = Field(default=BASE_DIR / "data", description="Data directory path.")
    

settings = Settings()

# Export API key to environment for litellm/openai
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
