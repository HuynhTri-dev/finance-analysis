"""
Name: app.infrastructure.gateway.langchain_utils
Description: LangChain model construction and invocation helpers for the LLM Gateway.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Any

from .types import FatalError, Platform

if TYPE_CHECKING:
    from .types import GatewaySettings, ModelConfig

logger = logging.getLogger(__name__)


def build_langchain_model(settings: GatewaySettings, cfg: ModelConfig) -> Any:
    """
    Build a LangChain chat model for the given ModelConfig.

    Input:
        settings (GatewaySettings): Global gateway settings (API keys, URLs).
        cfg (ModelConfig): Model-specific config including platform, model name, and flags.

    Output:
        Any: A LangChain chat model instance ready for invocation.

    Description & Logic:
        - Dispatches to the appropriate LangChain chat model class based on `cfg.platform`.
        - Internally delegates to `_build_langchain_model_cached` with a hashable key to
          leverage module-level LRU caching of model instances (B1 fix — connection pooling).
        - Raises `FatalError` for unknown platforms or missing credentials.
    """
    # B1: Delegate to cached factory using a hashable key tuple.
    # Cache key uses (platform, model_name, timeout_seconds, thinking_disabled) since
    # those are the only fields that affect the constructed model instance.
    return _build_langchain_model_cached(
        platform=cfg.platform,
        model_name=cfg.model_name,
        timeout_seconds=cfg.timeout_seconds,
        thinking_disabled=cfg.thinking_disabled,
        gemini_api_key=settings.gemini_api_key,
        openrouter_api_key=settings.openrouter_api_key,
        ollama_v1_base_url=settings.ollama_v1_base_url or "",
    )


@functools.lru_cache(maxsize=32)
def _build_langchain_model_cached(
    *,
    platform: Platform,
    model_name: str,
    timeout_seconds: float,
    thinking_disabled: bool,
    gemini_api_key: str,
    openrouter_api_key: str,
    ollama_v1_base_url: str,
) -> Any:
    """
    Internal cached factory for LangChain chat model instances.

    Input:
        All fields are primitive (hashable) so the function is compatible with `lru_cache`.
        They are the flat projection of `ModelConfig` and `GatewaySettings` fields that
        influence model construction.

    Output:
        Any: A LangChain chat model instance. The same instance is returned for identical
             argument combinations, preserving the model's internal HTTP connection pool
             across multiple requests.

    Description & Logic:
        - Decorated with `@functools.lru_cache(maxsize=32)` to cache up to 32 distinct
          model configurations simultaneously.
        - Raises `FatalError` for missing credentials or unsupported platforms.
    """
    if platform == Platform.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not gemini_api_key:
            raise FatalError("Gemini API key not configured.")

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=gemini_api_key,
            temperature=0.1,
            request_timeout=timeout_seconds,
            # Disable streaming for tool-bound calls: streaming=True can produce
            # AIMessageChunk where tool_calls attribute is empty, causing the ReAct
            # loop to fall back to fragile text parsing every single round.
            streaming=False,
        )

    if platform == Platform.OPENROUTER:
        from langchain_openai import ChatOpenAI

        if not openrouter_api_key:
            raise FatalError("OpenRouter API key not configured.")

        return ChatOpenAI(
            model=model_name,
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            request_timeout=timeout_seconds,
            # Disable streaming: same reasoning as Gemini above — tool_calls on
            # AIMessageChunk is unreliable across LangChain versions.
            streaming=False,
            model_kwargs={"thinking": {"type": "disabled"}} if thinking_disabled else {},
        )

    if platform == Platform.OLLAMA:
        from langchain_ollama import ChatOllama

        # Strip /v1 from the base_url for the native Ollama API.
        base_url = ollama_v1_base_url.removesuffix("/v1") or None

        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,
            timeout=timeout_seconds,
        )

    raise FatalError(f"Unknown platform for LangChain model: {platform}")


def _is_retriable_error(e: Exception) -> bool:
    """
    Determine whether an exception represents a retriable transient error.

    Input:
        e (Exception): The caught exception to inspect.

    Output:
        bool: True if the error is a rate-limit, overload, or resource-exhaustion
              signal (i.e., should trigger a fallback to the next model); False otherwise.

    Description & Logic:
        - S1 fix: Extracted from 3 duplicated inline blocks across the execution helpers.
        - First checks the exception type name for LangChain/gRPC rate-limit classes.
        - Falls back to substring matching on the string representation to catch HTTP
          status codes (429, 502, 503, 504) and semantic keywords embedded in messages.
    """
    # BR-GW-01 (Self-described): Type-name check is preferred over isinstance() to
    # avoid importing external library exception classes as hard dependencies here.
    if type(e).__name__ in ("RateLimitError", "ResourceExhausted"):
        return True
    retriable_signals = (
        "429",
        "502",
        "503",
        "504",
        "rate limit",
        "quota",
        "unavailable",
        "overloaded",
        "resourceexhausted",
        "memory",
        "oom",
        "allocate",
    )
    msg = str(e).lower()
    return any(signal in msg for signal in retriable_signals)


async def run_with_tools(
    settings: GatewaySettings,
    messages: list[Any],
    tools: list[Any],
    task_type: str = "router",
    config: dict[str, Any] | None = None,
) -> Any:
    """
    Execute a LangChain message list with tool binding.

    Input:
        settings (GatewaySettings): Global gateway settings.
        messages (list): LangChain-compatible message list.
        tools (list): List of tools to bind to the model.
        task_type (str): Key used to look up the task-specific fallback chain.
        config (dict | None): Optional LangChain runnable config.

    Output:
        Any: The AIMessage returned by the bound LangChain model.

    Description & Logic:
        - Iterates through the task's model fallback chain in order.
        - B2 fix: FatalError (e.g. missing credentials for a specific model) causes
          that model to be skipped and the next in chain to be tried.
        - S1 fix: Uses `_is_retriable_error()` helper instead of inline string matching.
        - S2 fix: Exhaustion raises with `from last_exc` to preserve stack trace.
    """
    chain = settings.task_fallback_chains.get(task_type) or settings.default_fallback_chain

    last_exc: Exception = RuntimeError("No models in chain.")

    for attempt, cfg in enumerate(chain, start=1):
        try:
            logger.info(
                "[Gateway] run_with_tools attempt %d — %s/%s (task=%s)",
                attempt,
                cfg.platform,
                cfg.model_name,
                task_type,
            )
            llm = build_langchain_model(settings, cfg)
            bound = llm.bind_tools(tools) if tools else llm

            return await asyncio.wait_for(
                bound.ainvoke(messages, config=config),
                timeout=cfg.timeout_seconds,
            )
        except FatalError as e:
            # B2: FatalError is model-scoped (e.g. key missing for this platform).
            # Log and try the next model instead of aborting the entire chain.
            logger.warning(
                "[Gateway] run_with_tools: fatal on %s/%s — %s, trying next.",
                cfg.platform,
                cfg.model_name,
                e,
            )
            last_exc = e
        except TimeoutError as e:
            logger.warning(
                "[Gateway] run_with_tools: timeout on %s/%s, trying next.",
                cfg.platform,
                cfg.model_name,
            )
            last_exc = e
        except Exception as e:
            if _is_retriable_error(e):  # S1: DRY helper
                logger.warning(
                    "[Gateway] run_with_tools: rate limit / overload on %s/%s, trying next.",
                    cfg.platform,
                    cfg.model_name,
                )
                last_exc = e
            else:
                logger.error(
                    "[Gateway] run_with_tools: unexpected error on %s/%s: %s",
                    cfg.platform,
                    cfg.model_name,
                    e,
                )
                raise

    raise RuntimeError(  # S2: preserve original stack trace
        f"run_with_tools: all models in chain for task '{task_type}' failed. Last error: {last_exc}"
    ) from last_exc


async def run_task_structured(
    settings: GatewaySettings,
    task_type: str,
    input_data: dict[str, Any],
    prompt: Any,
    schema: Any,
) -> Any:
    """
    Execute a structured extraction task.

    Input:
        settings (GatewaySettings): Global gateway settings.
        task_type (str): Key used to look up the task-specific fallback chain.
        input_data (dict): Input variables for the prompt template.
        prompt (Any): A LangChain prompt template (PromptTemplate / ChatPromptTemplate).
        schema (Any): Pydantic schema or JSON schema for structured output parsing.

    Output:
        Any: The parsed structured object returned by the model.

    Description & Logic:
        - Builds a LangChain runnable: `prompt | llm.with_structured_output(schema)`.
        - B2 fix: FatalError causes the current model to be skipped, not the whole chain.
        - S1 fix: Uses `_is_retriable_error()` helper for DRY rate-limit detection.
        - S2 fix: Chain exhaustion raises `RuntimeError` chained with `from last_exc`.
    """
    chain = settings.task_fallback_chains.get(task_type) or settings.default_fallback_chain

    last_exc: Exception = RuntimeError("No models in chain.")

    for attempt, cfg in enumerate(chain, start=1):
        try:
            logger.info(
                "[Gateway] run_task_structured attempt %d — %s/%s (task=%s)",
                attempt,
                cfg.platform,
                cfg.model_name,
                task_type,
            )
            llm = build_langchain_model(settings, cfg)
            structured_llm = llm.with_structured_output(schema)
            runnable = prompt | structured_llm

            return await asyncio.wait_for(
                runnable.ainvoke(input_data),
                timeout=cfg.timeout_seconds,
            )
        except (TimeoutError, FatalError) as e:
            # B2: FatalError is treated as model-scoped — skip and try the next.
            logger.warning(
                "[Gateway] run_task_structured: failure on %s/%s — %s, trying next.",
                cfg.platform,
                cfg.model_name,
                e,
            )
            last_exc = e
        except Exception as e:
            if _is_retriable_error(e):  # S1: DRY helper
                logger.warning(
                    "[Gateway] run_task_structured: rate limit / overload on %s/%s, trying next.",
                    cfg.platform,
                    cfg.model_name,
                )
                last_exc = e
            else:
                logger.error(
                    "[Gateway] run_task_structured: unexpected error on %s/%s: %s",
                    cfg.platform,
                    cfg.model_name,
                    e,
                )
                raise

    raise RuntimeError(  # S2: preserve original stack trace
        f"run_task_structured: all models in chain for task '{task_type}' failed. "
        f"Last error: {last_exc}"
    ) from last_exc


async def run_text_generation(
    settings: GatewaySettings,
    messages: list[Any],
    task_type: str,
    config: dict[str, Any] | None = None,
) -> str:
    """
    Execute a simple text generation task without tools or structured output.

    Input:
        settings (GatewaySettings): Global gateway settings.
        messages (list): LangChain-compatible message list.
        task_type (str): Key used to look up the task-specific fallback chain.
        config (dict | None): Optional LangChain runnable config.

    Output:
        str: The raw string content of the model's response.
             Useful for Ollama models with manual json_repair downstream.

    Description & Logic:
        - B2 fix: FatalError causes the current model to be skipped, not the whole chain.
        - S1 fix: Uses `_is_retriable_error()` helper for DRY rate-limit detection.
        - S2 fix: Chain exhaustion raises `RuntimeError` chained with `from last_exc`.
    """
    chain = settings.task_fallback_chains.get(task_type) or settings.default_fallback_chain

    last_exc: Exception = RuntimeError("No models in chain.")

    for attempt, cfg in enumerate(chain, start=1):
        try:
            logger.info(
                "[Gateway] run_text_generation attempt %d — %s/%s (task=%s)",
                attempt,
                cfg.platform,
                cfg.model_name,
                task_type,
            )
            llm = build_langchain_model(settings, cfg)

            response = await asyncio.wait_for(
                llm.ainvoke(messages, config=config),
                timeout=cfg.timeout_seconds,
            )
            return str(response.content)
        except (TimeoutError, FatalError) as e:
            # B2: FatalError is treated as model-scoped — skip and try the next.
            logger.warning(
                "[Gateway] run_text_generation: failure on %s/%s — %s, trying next.",
                cfg.platform,
                cfg.model_name,
                e,
            )
            last_exc = e
        except Exception as e:
            if _is_retriable_error(e):  # S1: DRY helper
                logger.warning(
                    "[Gateway] run_text_generation: rate limit / overload on %s/%s, trying next.",
                    cfg.platform,
                    cfg.model_name,
                )
                last_exc = e
            else:
                logger.error(
                    "[Gateway] run_text_generation: unexpected error on %s/%s: %s",
                    cfg.platform,
                    cfg.model_name,
                    e,
                )
                raise

    raise RuntimeError(  # S2: preserve original stack trace
        f"run_text_generation: all models in chain for task '{task_type}' failed. "
        f"Last error: {last_exc}"
    ) from last_exc


def get_embedder(settings: GatewaySettings, task_type: str = "embedded") -> Any:
    chain = settings.task_fallback_chains.get(task_type) or settings.default_fallback_chain
    cfg = chain[0]

    if cfg.platform == Platform.GEMINI:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        if not settings.gemini_api_key:
            raise FatalError("Gemini API key not configured for embeddings.")
        return GoogleGenerativeAIEmbeddings(
            model=f"models/{cfg.model_name}",
            google_api_key=settings.gemini_api_key,
        )

    if cfg.platform == Platform.OLLAMA:
        from langchain_ollama import OllamaEmbeddings

        base_url = (
            settings.ollama_v1_base_url.replace("/v1", "") if settings.ollama_v1_base_url else None
        )
        return OllamaEmbeddings(
            model=cfg.model_name,
            base_url=base_url,
        )

    raise FatalError(f"Unsupported embedding platform: {cfg.platform}")


# Semaphore to limit local MedGemma calls to at most 4 concurrently
# to prevent overloading local GPU/CPU resources.
_medgemma_semaphore = asyncio.Semaphore(4)


async def call_medgemma(
    settings: GatewaySettings,
    messages: list[Any],
    config: dict[str, Any] | None = None,
) -> str:
    """
    Calls local MedGemma model via health_analysis task fallback chain.
    Enforces a concurrency limit of 4 requests using a Semaphore.

    Args:
        settings: Global gateway settings.
        messages: List of LLM input messages.
        config: Optional LangChain execution configuration dictionary.

    Returns:
        The generated raw text response string.
    """
    async with _medgemma_semaphore:
        return await run_text_generation(
            settings=settings,
            messages=messages,
            task_type="health_analysis",
            config=config,
        )
