import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Calculate absolute path to .env file (assuming it's in project root, one level up from src)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding='utf-8', extra='ignore')

    # LLM Settings
    OPENAI_API_KEY: str = Field(..., description="API Key for OpenAI or compatible provider.")
    MODEL_NAME: str = Field("gpt-4o-mini", description="Model to use for extraction (e.g., gpt-4o, claude-3-opus).")
    
    # App Settings
    LOG_LEVEL: str = "INFO"

settings = Settings()

# Ensure litellm/openai libraries can see the key in env vars
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Configure LiteLLM (Optional global configs)
import litellm
# litellm.drop_params = True # Example: auto-drop unsupported params
