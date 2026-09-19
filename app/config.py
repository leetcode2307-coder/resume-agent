from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    xkiro_api_key: str = ""
    primary_model: str = "openai/gpt-oss-120b"
    fallback_model: str = "deepseek/deepseek-v4-flash-0731:free"
    gemma_model: str = "google/gemma-4-31b-it:free"
    glm_model: str = "z-ai/glm-5.2:free"
    nemotron_model: str = "nvidia/nemotron-3.5-lightning:free"

    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None
    langsmith_project: str = "resume-agent"

    use_s3_storage: bool = False
    aws_s3_bucket_name: str | None  = None    
    aws_region: str | None  = None 
    aws_access_key_id: str | None  = None 
    aws_secret_access_key: str | None  = None  

    supabase_jwt_secret: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache()
def get_setting()->Settings:
    return Settings()

settings = get_setting()
    