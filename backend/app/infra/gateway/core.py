"""
name: core.py
description: Core LLMGateway orchestrator providing raw HTTP-based LLM dispatch
             with retry/fallback, and LangChainFacade for high-level LangChain operations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from . import langchain_utils
from .adapters import call_gemini, call_ollama, call_openrouter
from .types import (
    FatalError,
    GatewaySettings,
    LLMResult,
    ModelConfig,
    Platform,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Centralized LLM routing with configurable fallback chains.
    """

    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, settings: GatewaySettings):
        self.settings = settings
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> LLMGateway:
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("LLMGateway must be used as an async context manager.")
        return self._session

    async def run(
        self,
        prompt: str,
        *,
        chain: list[ModelConfig] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        chain = chain or self.settings.default_fallback_chain
        last_exc: Exception | None = None

        for attempt, cfg in enumerate(chain, start=1):
            try:
                logger.info(
                    "[Gateway] Attempt %d — %s / %s",
                    attempt,
                    cfg.platform,
                    cfg.model_name,
                )
                content = await self._call_with_retry(
                    prompt,
                    cfg,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return LLMResult(
                    content=content,
                    platform=cfg.platform,
                    model_name=cfg.model_name,
                    attempts=attempt,
                )
            except RateLimitError as e:
                logger.warning("[Gateway] Rate limit on %s/%s: %s", cfg.platform, cfg.model_name, e)
                last_exc = e
            except FatalError as e:
                # B2 fix: FatalError is treated as model-scoped (e.g., bad API key for
                # this specific platform). Skip and try the next model in the chain
                # instead of aborting immediately — consistent with LangChain helpers.
                logger.warning(
                    "[Gateway] Fatal error on %s/%s (skipping): %s",
                    cfg.platform,
                    cfg.model_name,
                    e,
                )
                last_exc = e
            except Exception as e:
                logger.error(
                    "[Gateway] Unexpected error on %s/%s: %s",
                    cfg.platform,
                    cfg.model_name,
                    e,
                )
                last_exc = e

        error_msg = f"All models in the fallback chain failed. Last error: {last_exc}"
        logger.error("[Gateway] %s", error_msg)
        last = chain[-1]
        return LLMResult(
            content="",
            platform=last.platform,
            model_name=last.model_name,
            attempts=len(chain),
            error=error_msg,
        )

    async def run_task(
        self,
        task_type: str,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        chain = (
            self.settings.task_fallback_chains.get(task_type)
            or self.settings.default_fallback_chain
        )
        return await self.run(
            prompt,
            chain=chain,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def get_embedder(self, task_type: str = "embedded") -> Any:
        return langchain_utils.get_embedder(self.settings, task_type)

    async def _call_with_retry(
        self,
        prompt: str,
        cfg: ModelConfig,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(1, cfg.max_retries + 2):
            try:
                return await asyncio.wait_for(
                    self._dispatch(
                        prompt,
                        cfg,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=cfg.timeout_seconds,
                )
            except (RateLimitError, FatalError):
                raise
            except TimeoutError as e:
                last_exc = e
            except Exception as e:
                last_exc = e

            if attempt <= cfg.max_retries:
                wait = cfg.retry_delay_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(wait)

        raise last_exc

    async def _dispatch(
        self,
        prompt: str,
        cfg: ModelConfig,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if cfg.platform == Platform.GEMINI:
            return await call_gemini(
                self.session,
                self.settings,
                prompt,
                cfg.model_name,
                self.GEMINI_URL,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif cfg.platform == Platform.OPENROUTER:
            return await call_openrouter(
                self.session,
                self.settings,
                prompt,
                cfg.model_name,
                self.OPENROUTER_URL,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif cfg.platform == Platform.OLLAMA:
            return await call_ollama(
                self.session,
                self.settings,
                prompt,
                cfg.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_disabled=cfg.thinking_disabled,
            )
        else:
            raise FatalError(f"Unknown platform: {cfg.platform}")

    # -- LangChain methods: REMOVED — use LangChainFacade instead ---------------
    # All LangChain proxy methods have been moved to LangChainFacade (SRP fix).
    # LLMGateway is now solely responsible for raw HTTP dispatch + retry/fallback.


class GatewayRegistry:
    """
    Module-level singleton that holds the shared LLMGateway instance.
    """

    _instance: LLMGateway | None = None

    @classmethod
    def set(cls, gateway: LLMGateway) -> None:
        """
        Register the application-wide LLMGateway instance.

        Input:
            gateway (LLMGateway): The fully-initialized gateway to register.
        Output:
            None
        Description & Logic:
            - Called once during application startup (e.g., in lifespan handler).
            - Stores the instance at class level for later retrieval via `get()`.
        """
        cls._instance = gateway
        logger.info("[GatewayRegistry] LLMGateway registered.")

    @classmethod
    def get(cls) -> LLMGateway:
        """
        Retrieve the registered LLMGateway instance.

        Output:
            LLMGateway: The shared gateway instance.
        Description & Logic:
            - Raises RuntimeError if called before `set()` during startup.
        """
        if cls._instance is None:
            raise RuntimeError(
                "GatewayRegistry has no LLMGateway. "
                "Ensure GatewayRegistry.set(gateway) is called during app startup."
            )
        return cls._instance


class LangChainFacade:
    """
    High-level LangChain operations facade.

    SRP fix: Separates LangChain-based invocations (tool binding, structured output,
    text generation) from `LLMGateway`, which is solely responsible for raw HTTP
    dispatch with retry/fallback. Callers that need LangChain features should use
    this class instead of `LLMGateway`.
    """

    def __init__(self, settings: GatewaySettings) -> None:
        """
        Initialize with the shared gateway settings.

        Input:
            settings (GatewaySettings): Runtime configuration (API keys, fallback chains).
        """
        self.settings = settings

    async def run_with_tools(
        self,
        messages: list[Any],
        tools: list[Any],
        task_type: str = "router",
        config: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute a LangChain message list with tool binding.

        Input:
            messages (list): LangChain-compatible message list.
            tools (list): Tools to bind to the model.
            task_type (str): Fallback chain key.
            config (dict | None): Optional LangChain runnable config.
        Output:
            Any: The AIMessage returned by the bound model.
        """
        return await langchain_utils.run_with_tools(
            self.settings, messages, tools, task_type, config=config
        )

    async def run_task_structured(
        self,
        task_type: str,
        input_data: dict[str, Any],
        prompt: Any,
        schema: Any,
    ) -> Any:
        """
        Execute a structured extraction task.

        Input:
            task_type (str): Fallback chain key.
            input_data (dict): Template input variables.
            prompt (Any): LangChain prompt template.
            schema (Any): Pydantic or JSON schema for structured output.
        Output:
            Any: Parsed structured object from the model.
        """
        return await langchain_utils.run_task_structured(
            self.settings, task_type, input_data, prompt, schema
        )

    async def run_text_generation(
        self,
        messages: list[Any],
        task_type: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        """
        Execute a simple text generation task.

        Input:
            messages (list): LangChain-compatible message list.
            task_type (str): Fallback chain key.
            config (dict | None): Optional LangChain runnable config.
        Output:
            str: Raw text content of the model response.
        """
        return await langchain_utils.run_text_generation(
            self.settings, messages, task_type, config=config
        )

    async def call_medgemma(
        self,
        messages: list[Any],
        config: dict[str, Any] | None = None,
    ) -> str:
        """
        Call the local MedGemma model with concurrency limiting.

        Input:
            messages (list): LangChain-compatible message list.
            config (dict | None): Optional LangChain runnable config.
        Output:
            str: Raw text content of the model response.
        Description & Logic:
            - Internally enforces a Semaphore(4) concurrency cap to prevent GPU/CPU saturation.
        """
        return await langchain_utils.call_medgemma(self.settings, messages, config=config)

    def get_embedder(self, task_type: str = "embedded") -> Any:
        """
        Build and return a LangChain embedder for the given task type.

        Input:
            task_type (str): Fallback chain key for embeddings (default: "embedded").
        Output:
            Any: A LangChain embeddings instance (e.g., GoogleGenerativeAIEmbeddings).
        """
        return langchain_utils.get_embedder(self.settings, task_type)
