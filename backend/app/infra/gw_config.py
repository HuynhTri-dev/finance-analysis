"""
gw_config.py — Configuration showing per-task fallback chains.

Load GatewaySettings from environment variables using Pydantic v2.
"""

from __future__ import annotations

from functools import lru_cache

from app.core import get_ai_settings

from .gateway import GatewaySettings, ModelConfig, Platform


@lru_cache
def build_gateway_settings() -> GatewaySettings:
    """
    Construct GatewaySettings with per-task fallback chains.
    Using centralized settings from core configuration.

    Fallback chain logic:
      - router          : gemini-flash → llama3-instruct (light tasks, low latency)
      - general_logic   : gemini-pro   → llama3-instruct
      - medical         : openrouter-medgemma → gemini-pro
      - offline_local   : ollama only (no cloud)
      - default         : gemini-flash → llama3
    """
    settings = get_ai_settings()
    gw_settings = GatewaySettings(
        gemini_api_key=settings.google_api_key,
        openrouter_api_key=settings.openrouter_api_key,
        ollama_base_url=settings.ollama_url,
        gemini_default_model=settings.gemini_router_model,
        openrouter_default_model=settings.openrouter_medical_model,
        ollama_default_model=settings.ollama_fallback_model,
        # ---- Default chain (general tasks) --------------------------------
        default_fallback_chain=[
            ModelConfig(Platform.GEMINI, settings.gemini_router_model, timeout_seconds=30),
            ModelConfig(Platform.OLLAMA, settings.ollama_fallback_model, timeout_seconds=120),
        ],
        # ---- Per-task chains ----------------------------------------------
        task_fallback_chains={
            "router": [
                ModelConfig(
                    Platform.OLLAMA,
                    settings.gemma4_31b_cloud,
                    timeout_seconds=30,
                    thinking_disabled=True,
                ),
                ModelConfig(
                    Platform.OLLAMA,
                    settings.qwen3_5_0_8b,
                    timeout_seconds=30,
                    thinking_disabled=True,
                ),
            ],
            "generate_answer": [
                ModelConfig(Platform.OLLAMA, settings.gemma4_31b_cloud, timeout_seconds=60),
                ModelConfig(Platform.OLLAMA, settings.gpt_oss_20b_cloud, timeout_seconds=60),
            ],
            "extract": [
                ModelConfig(
                    Platform.OLLAMA,
                    settings.gpt_oss_20b_cloud,
                    timeout_seconds=120,
                ),
            ],
            "embedded": [ModelConfig(Platform.OLLAMA, settings.bgem3, timeout_seconds=120)],
        },
    )
    return gw_settings
