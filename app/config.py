from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    primary_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free "
    fallback_model: str = "nvidia/nemotron-3.5-lightning:free"
    gemma_model: str = "google/gemma-4-31b-it:free"
    glm_model: str = "z-ai/glm-5.2:free"
    nemotron_model: str = "nvidia/nemotron-3.5-lightning:free"

    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str
    langsmith_project: str = "resume-agent"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

@lru_cache()
def get_setting()->Settings:
    return Settings()

settings = get_setting()
    