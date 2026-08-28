"""
Platform-specific adapters for LLM Gateway.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .types import FatalError, RateLimitError

if TYPE_CHECKING:
    import aiohttp

    from .types import GatewaySettings

logger = logging.getLogger(__name__)


async def call_gemini(
    session: aiohttp.ClientSession,
    settings: GatewaySettings,
    prompt: str,
    model_name: str,
    gemini_url_template: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    if not settings.gemini_api_key:
        raise FatalError("Gemini API key not configured.")

    url = gemini_url_template.format(model=model_name)
    headers = {
        "x-goog-api-key": settings.gemini_api_key,
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if temperature is not None or max_tokens is not None:
        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = generation_config

    async with session.post(url, headers=headers, json=payload) as resp:
        if resp.status == 429:
            raise RateLimitError(f"Gemini 429: {await resp.text()}")
        if resp.status in (401, 403):
            raise FatalError(f"Gemini auth error {resp.status}: {await resp.text()}")
        resp.raise_for_status()
        data = await resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return str(text)
    except (KeyError, IndexError) as e:
        raise FatalError(f"Unexpected Gemini response format: {data}") from e


async def call_openrouter(
    session: aiohttp.ClientSession,
    settings: GatewaySettings,
    prompt: str,
    model_name: str,
    openrouter_url: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    if not settings.openrouter_api_key:
        raise FatalError("OpenRouter API key not configured.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_base_url,
    }
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    async with session.post(openrouter_url, headers=headers, json=payload) as resp:
        if resp.status == 429:
            raise RateLimitError(f"OpenRouter 429: {await resp.text()}")
        if resp.status in (401, 403):
            raise FatalError(f"OpenRouter auth error {resp.status}")
        resp.raise_for_status()
        data = await resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
        return str(content)
    except (KeyError, IndexError) as e:
        raise FatalError(f"Unexpected OpenRouter response format: {data}") from e


async def call_ollama(
    session: aiohttp.ClientSession,
    settings: GatewaySettings,
    prompt: str,
    model_name: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    thinking_disabled: bool = False,
) -> str:
    """
    Call the local Ollama /api/generate endpoint.

    Args:
        session: Shared aiohttp client session.
        settings: Gateway settings containing the Ollama base URL.
        prompt: The text prompt to send.
        model_name: Ollama model tag (e.g. "qwen3:0.6b").
        temperature: Sampling temperature override.
        max_tokens: Maximum tokens to generate (maps to num_predict).
        thinking_disabled: When True, attempts to set "think": false to
            suppress <think> token generation on models that support it
            (e.g. qwen3, Ollama >=0.6.0). Saves ~200-400ms on small tasks.
            Falls back gracefully if the Ollama version does not support it.

    Returns:
        The generated text response from Ollama.
    """
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens

    async def _post(use_think_param: bool) -> str:
        payload: dict[str, Any] = {"model": model_name, "prompt": prompt, "stream": False}
        if use_think_param:
            payload["think"] = False
        if options:
            payload["options"] = options
        async with session.post(settings.ollama_base_url, json=payload) as resp:
            if resp.status == 429:
                raise RateLimitError("Ollama 429")
            if resp.status == 400 and use_think_param:
                # Older Ollama versions (<0.6.0) return HTTP 400 when 'think'
                # is an unrecognised field — raise a sentinel to trigger retry
                raise _ThinkParamUnsupported()
            resp.raise_for_status()
            data = await resp.json()
            response_text = data.get("response", "")
            return str(response_text)

    try:
        return await _post(use_think_param=thinking_disabled)
    except _ThinkParamUnsupported:
        # Retry without 'think' param for backward-compatibility with Ollama <0.6.0
        logger.warning(
            "[Ollama] 'think' param not supported by this Ollama version — retrying without it. "
            "Upgrade to Ollama >=0.6.0 to suppress <think> tokens and save latency."
        )
        return await _post(use_think_param=False)


class _ThinkParamUnsupported(Exception):
    """Internal sentinel: Ollama returned 400 because 'think' field is unknown."""
