"""
Name: app.infrastructure.gateway.types
Description: Dataclasses, enums, and exceptions for the LLM Gateway.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)


class Platform(StrEnum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class ModelConfig:
    """Single model endpoint configuration."""

    platform: Platform
    model_name: str
    # Optional per-model overrides
    timeout_seconds: float = 60.0
    max_retries: int = 1  # retries on transient errors (not rate limits)
    retry_delay_seconds: float = 2.0
    # When True, the gateway will explicitly disable extended thinking for
    # models that support it (e.g. Claude Sonnet with thinking mode).
    # Set this on any fast/low-latency task where thinking is wasteful.
    thinking_disabled: bool = False


@dataclass
class GatewaySettings:
    """
    All runtime settings for the gateway.
    Load from env / Pydantic Settings in production.
    """

    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/api/generate"

    # Default model for each platform (overridable per-request)
    gemini_default_model: str = "gemini-2.0-flash"
    openrouter_default_model: str = "google/gemma-7b-it"
    ollama_default_model: str = "llama3"

    # Runtime computed base url for Ollama LangChain compatibility
    ollama_v1_base_url: str = ""

    # App base URL for OpenRouter Referer header
    app_base_url: str = "https://your-app.com"

    # Default fallback chain: list of ModelConfig tried in order
    default_fallback_chain: list[ModelConfig] = field(default_factory=list)

    # Per task-type fallback chains (task_type -> ordered list)
    task_fallback_chains: dict[str, list[ModelConfig]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ollama_v1_base_url:
            self.ollama_v1_base_url = (
                self.ollama_base_url.removesuffix("/api/generate").rstrip("/") + "/v1"
            )

        # Provide a sensible default chain if none supplied
        if not self.default_fallback_chain:
            self.default_fallback_chain = [
                ModelConfig(Platform.GEMINI, self.gemini_default_model),
                ModelConfig(Platform.OLLAMA, self.ollama_default_model),
            ]


@dataclass
class LLMResult:
    content: str
    platform: Platform
    model_name: str
    attempts: int  # how many models were tried before success
    error: str | None = None  # set if all fallbacks failed


class RateLimitError(Exception):
    """Raised when a platform returns 429 / ResourceExhausted."""


class FatalError(Exception):
    """Raised for non-retryable errors (bad auth, malformed request, etc.)."""
