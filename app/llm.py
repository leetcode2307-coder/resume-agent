from langchain_openrouter import ChatOpenRouter
from app.config import settings
from typing import Any


# Create primary and fallback raw clients
_primary_client = ChatOpenRouter(
    api_key=settings.openrouter_api_key,
    model=settings.primary_model,
)

_fallback_client = ChatOpenRouter(
    api_key=settings.openrouter_api_key,
    model=settings.fallback_model,
)


class _LLMInvoker:
    """Small wrapper that attempts the primary client first then falls back."""

    def __init__(self, primary: Any, fallback: Any):
        self.primary = primary
        self.fallback = fallback

    def with_structured_output(self, schema: Any):
        # Return an object that exposes invoke(messages)
        primary_struct = getattr(self.primary, "with_structured_output")(schema)
        fallback_struct = getattr(self.fallback, "with_structured_output")(schema)

        class _Invoker:
            def invoke(self_inner, messages):
                try:
                    return primary_struct.invoke(messages)
                except Exception:
                    # Try fallback LLM and propagate its exception if it fails
                    return fallback_struct.invoke(messages)

        return _Invoker()

    def invoke(self, messages):
        try:
            return self.primary.invoke(messages)
        except Exception:
            return self.fallback.invoke(messages)


# Export a safe wrapper named `llm` for the rest of the codebase to use
llm = _LLMInvoker(_primary_client, _fallback_client)

# Also keep a reference to the raw fallback client for direct use in main.py
fallback_llm = _fallback_client