"""
name: config.py
description: Centralised application settings loaded from environment variables / .env file.
             Uses pydantic-settings for type-safe, validated configuration.
             RS256 keys are stored as multi-line PEM strings in .env (local dev).
             In production, inject them via Secret Manager at container startup.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "HRM Agent"
    app_env: str = "local"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ------------------------------------------------------------------
    # Database & Cache
    # ------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://hrm_agent:hrm_agent@localhost:5432/hrm_agent"
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # ------------------------------------------------------------------
    # JWT — RS256
    # jwt_private_key / jwt_public_key must be full PEM strings.
    # In .env, use a literal multi-line block or escape newlines as \n.
    # ------------------------------------------------------------------
    jwt_private_key: str = Field(default="", description="RS256 private key PEM string")
    jwt_public_key: str = Field(default="", description="RS256 public key PEM string")
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # ------------------------------------------------------------------
    # External integrations
    # ------------------------------------------------------------------
    hrm_provider: str = "odoo"
    hrm_base_url: str = "http://localhost:8069"
    hrm_api_key: str = "dev-hrm-token"

    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = "EMPTY"
    llm_chat_model: str = "local-chat-model"
    llm_embedding_model: str = "local-embedding-model"
    llm_timeout_seconds: float = 60.0

    embedding_dimension: int = 1536
    rate_limit_messages_per_minute: int = 5

    # ------------------------------------------------------------------
    # Cloudflare R2 / Object Storage
    # ------------------------------------------------------------------
    r2_account_id: str = Field(default="", description="Cloudflare R2 Account ID")
    r2_access_key: str = Field(default="", description="Cloudflare R2 Access Key ID")
    r2_secret_key: str = Field(default="", description="Cloudflare R2 Secret Access Key")
    r2_endpoint_url: str = Field(default="", description="Cloudflare R2 Endpoint URL")
    bucket_name: str = Field(default="", description="Cloudflare R2 Bucket Name")

    # ------------------------------------------------------------------
    # Security & Audit Log
    # ------------------------------------------------------------------
    deepeval_telemetry_opt_out: str = "YES"
    audit_log_encryption_key: str = Field(
        default="",
        description="Fernet 32-byte url-safe base64 key for encrypting sensitive HRM payload data",
    )

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    _backend_env = Path(__file__).resolve().parents[2] / ".env"
    _root_env = Path(__file__).resolve().parents[3] / ".env"
    model_config = SettingsConfigDict(
        env_file=[_root_env, _backend_env, ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Retrieve cached application settings instance.

    Input:
        None

    Output:
        Settings: Validated application configuration settings instance.

    Description & Logic:
        - Uses functools.lru_cache to load and validate environment variables once.
    """
    return Settings()
