"""
LLM Gateway — Multi-platform with configurable fallback chains.

Supports: Google AI Studio (Gemini), OpenRouter, Ollama
"""

from .core import GatewayRegistry, LLMGateway
from .types import (
    FatalError,
    GatewaySettings,
    LLMResult,
    ModelConfig,
    Platform,
    RateLimitError,
)

__all__ = [
    "Platform",
    "ModelConfig",
    "GatewaySettings",
    "LLMResult",
    "RateLimitError",
    "FatalError",
    "LLMGateway",
    "GatewayRegistry",
]
