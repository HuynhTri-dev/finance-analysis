# name: model_config.py
# description: AI Model configuration settings, separated to keep the main config clean.

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AIModelSettings(BaseSettings):
    """
    Tách riêng danh sách cấu hình và tên các model ra khỏi file config chính
    để dễ quản lý khi có quá nhiều models.
    """

    _env_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(".env"),
    ]
    model_config = SettingsConfigDict(
        env_file=_env_paths,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Model API Keys & URLs
    google_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_api_key: str = ""
    ollama_url: str = "https://ollama.com/api/generate"
    ollama_fallback_model: str = "gpt-oss:120b"

    # Ollama Cloud Free Tier Models
    gpt_oss_120b: str = "gpt-oss:120b"            # Flagship 120B — Comprehensive financial reports
    gpt_oss_20b: str = "gpt-oss:20b"              # Fast 20B — Structured BCTC extraction & routing
    gemma4_31b: str = "gemma4:31b"                # Google Gemma 4 31B — Interactive conversational Q&A (~250ms)
    nemotron_3_nano: str = "nemotron-3-nano:30b"  # NVIDIA Nemotron 30B — Low latency fallback
    nemotron_3_super: str = "nemotron-3-super"    # NVIDIA Nemotron Super — Synthesis fallback
    nemotron_3_ultra: str = "nemotron-3-ultra"    # NVIDIA Nemotron Ultra — Deep reasoning fallback

    # Aliases for backward compatibility
    gemma4_31b_cloud: str = "gemma4:31b"
    gpt_oss_120b_cloud: str = "gpt-oss:120b"
    gpt_oss_20b_cloud: str = "gpt-oss:20b"
    qwen3_5_0_8b: str = "gpt-oss:20b"
    gemma4_e4b: str = "gemma4:31b"

    # Embedding model
    bgem3: str = "bge-m3:latest"

    # Cloud fallback models
    gemini_router_model: str = "gemini-1.5-flash"
    openrouter_medical_model: str = "google/medgemma-27b"


@lru_cache
def get_ai_settings() -> AIModelSettings:
    return AIModelSettings()
