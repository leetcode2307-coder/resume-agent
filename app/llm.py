from __future__ import annotations

from typing import Any

from langchain_openrouter import ChatOpenRouter

from app.config import settings

import logging
from langchain_core.callbacks.base import BaseCallbackHandler

logger = logging.getLogger(__name__)

class TokenLoggingCallback(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        try:
            for generation_group in response.generations:
                for generation in generation_group:
                    if hasattr(generation, 'message') and hasattr(generation.message, 'response_metadata'):
                        meta = generation.message.response_metadata
                        token_usage = meta.get("token_usage", {})
                        model_name = meta.get("model_name", "unknown")
                        if token_usage:
                            logger.info(f"LLM [{model_name}] Token Usage: {token_usage} | Other Details: {meta}")
        except Exception as e:
            logger.warning(f"Failed to log token usage: {e}")

_MODEL_ALIASES = {
    "primary": settings.primary_model,
    "fallback": settings.fallback_model,
    "gemma": settings.gemma_model,
    "glm": settings.glm_model,
    "nemotron": settings.nemotron_model,
}


def _get_model_name(model_name: str) -> str:
    return _MODEL_ALIASES.get(model_name, model_name)


def _build_model(model_name: str) -> ChatOpenRouter:
    return ChatOpenRouter(
        api_key=settings.openrouter_api_key,
        model=_get_model_name(model_name),
        timeout=900000, # ChatOpenRouter expects timeout in milliseconds (900000ms = 900s)
        max_retries=3,
        callbacks=[TokenLoggingCallback()]
    )


class _ModelChain:
    """Attempt each configured LLM in order until one succeeds."""

    def __init__(self, *models: Any):
        self.models = list(models)
        if not self.models:
            raise ValueError("At least one model is required to build a model chain.")

    def invoke(self, messages):
        import time
        last_error = None
        for attempt in range(3):
            for model in self.models:
                try:
                    return model.invoke(messages)
                except Exception as exc:  # pragma: no cover - fallback path
                    last_error = exc
                    logger.warning(f"Model invoke failed: {exc}")
            if attempt < 2:
                sleep_time = 2 ** attempt
                logger.warning(f"All models failed on attempt {attempt+1}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
        if last_error is not None:
            raise last_error
        raise RuntimeError("No models were configured for invocation.")

    async def ainvoke(self, messages):
        import asyncio
        last_error = None
        for attempt in range(3):
            for model in self.models:
                try:
                    if hasattr(model, "ainvoke"):
                        return await model.ainvoke(messages)
                    return model.invoke(messages)
                except Exception as exc:  # pragma: no cover - fallback path
                    last_error = exc
                    logger.warning(f"Model ainvoke failed: {exc}")
            if attempt < 2:
                sleep_time = 2 ** attempt
                logger.warning(f"All models failed on attempt {attempt+1}. Retrying in {sleep_time}s...")
                await asyncio.sleep(sleep_time)
        if last_error is not None:
            raise last_error
        raise RuntimeError("No models were configured for async invocation.")

    def with_structured_output(self, schema: Any):
        structured_models = [model.with_structured_output(schema) for model in self.models]

        class _StructuredInvoker:
            def invoke(self_inner, messages):
                import time
                last_error = None
                for attempt in range(3):
                    for structured_model in structured_models:
                        try:
                            res = structured_model.invoke(messages)
                            if res is not None:
                                return res
                        except Exception as exc:  # pragma: no cover - fallback path
                            last_error = exc
                            logger.warning(f"Structured model invoke failed: {exc}")
                    if attempt < 2:
                        sleep_time = 2 ** attempt
                        logger.warning(f"All structured models failed on attempt {attempt+1}. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                if last_error is not None:
                    raise last_error
                return None

            async def ainvoke(self_inner, messages):
                import asyncio
                last_error = None
                for attempt in range(3):
                    for structured_model in structured_models:
                        try:
                            if hasattr(structured_model, "ainvoke"):
                                res = await structured_model.ainvoke(messages)
                            else:
                                res = structured_model.invoke(messages)
                            if res is not None:
                                return res
                        except Exception as exc:  # pragma: no cover - fallback path
                            last_error = exc
                            logger.warning(f"Structured model ainvoke failed: {exc}")
                    if attempt < 2:
                        sleep_time = 2 ** attempt
                        logger.warning(f"All structured models failed on attempt {attempt+1}. Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                if last_error is not None:
                    raise last_error
                return None

        return _StructuredInvoker()


def get_llm(*model_names: str) -> _ModelChain:
    """Build a fallthrough LLM chain from model aliases or explicit model names."""
    if not model_names:
        raise ValueError("get_llm() requires at least one model name or alias.")

    models = [_build_model(model_name) for model_name in model_names]
    return _ModelChain(*models)


llm = get_llm("primary", "fallback")
fallback_llm = get_llm("fallback")