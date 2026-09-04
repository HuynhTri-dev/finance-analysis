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
    Call the Ollama or remote OpenAI-compatible endpoint.

    Args:
        session: Shared aiohttp client session.
        settings: Gateway settings containing the Ollama base URL and optional API key.
        prompt: The text prompt to send.
        model_name: Model tag or identifier.
        temperature: Sampling temperature override.
        max_tokens: Maximum tokens to generate.
        thinking_disabled: When True, attempts to suppress thinking tokens on supported models.

    Returns:
        The generated text response.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    if getattr(settings, "ollama_api_key", None) and settings.ollama_api_key.strip():
        headers["Authorization"] = f"Bearer {settings.ollama_api_key.strip()}"

    options: dict[str, Any] = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens

    # Detect if the target URL is an OpenAI-compatible /chat/completions endpoint
    is_openai_compat = any(
        sub in settings.ollama_base_url.lower()
        for sub in ["/chat/completions", "/paas/", "/v1/"]
    )

    async def _post(use_think_param: bool) -> str:
        if is_openai_compat:
            payload: dict[str, Any] = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if temperature is not None:
                payload["temperature"] = temperature
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
        else:
            payload: dict[str, Any] = {"model": model_name, "prompt": prompt, "stream": False}
            if use_think_param:
                payload["think"] = False
            if options:
                payload["options"] = options

        async with session.post(settings.ollama_base_url, headers=headers, json=payload) as resp:
            if resp.status == 429:
                raise RateLimitError("Ollama/LLM 429 Rate Limit")
            if resp.status in (401, 403):
                raise FatalError(f"Ollama/LLM Auth Error {resp.status}: {await resp.text()}")
            if resp.status == 400 and use_think_param and not is_openai_compat:
                raise _ThinkParamUnsupported()
            resp.raise_for_status()
            data = await resp.json()

            # Handle OpenAI-compatible response format
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                message = choice.get("message", {})
                return str(message.get("content", ""))

            # Handle native Ollama response format
            response_text = data.get("response", "")
            return str(response_text)

    try:
        return await _post(use_think_param=thinking_disabled)
    except _ThinkParamUnsupported:
        # Retry without 'think' param for backward-compatibility with Ollama <0.6.0
        logger.warning(
            "[Ollama] 'think' param not supported by this endpoint — retrying without it."
        )
        return await _post(use_think_param=False)


class _ThinkParamUnsupported(Exception):
    """Internal sentinel: Ollama returned 400 because 'think' field is unknown."""
