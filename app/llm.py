from langchain_openrouter import ChatOpenRouter
from app.config import settings

llm = ChatOpenRouter(
    api_key = settings.openrouter_api_key,
    model = settings.primary_model
)

fallback_llm = ChatOpenRouter(
    api_key = settings.openrouter_api_key,
    model = settings.fallback_model
)