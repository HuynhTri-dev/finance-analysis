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

    _env_file_path = Path(__file__).parent.parent.parent / ".env"
    model_config = SettingsConfigDict(
        env_file=_env_file_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Model API Keys & URLs
    google_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_fallback_model: str = "gpt-os:120b-cloud"

    qwen3_5_0_8b: str = "qwen3.5:0.8b"  # router offline
    gemma4_31b_cloud: str = "gemma4:31b-cloud"
    gpt_oss_120b_cloud: str = "gpt-oss:120b-cloud"  # Fast Expert offline
    gpt_oss_20b_cloud: str = "gpt-oss:20b-cloud"  # Think Expert offlinee
    gemma4_e4b: str = "gemma4:e4b"

    # Embedidng:
    bgem3: str = "bge-m3:latest"

    # Missing models from gateway settings
    gemini_router_model: str = "gemini-1.5-flash"
    openrouter_medical_model: str = "google/medgemma-27b"


@lru_cache
def get_ai_settings() -> AIModelSettings:
    return AIModelSettings()
