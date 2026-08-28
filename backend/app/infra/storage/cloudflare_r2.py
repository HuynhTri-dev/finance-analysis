"""
name: cloudflare_r2.py
description: Cloudflare R2 session factory and client connection management using aioboto3.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3  # type: ignore[import-untyped]

from app.core.config import Settings, get_settings


def create_r2_session() -> aioboto3.Session:
    """
    Create an aioboto3 Session instance.

    Input:
        None

    Output:
        aioboto3.Session: Configured aioboto3 session object.

    Description & Logic:
        - Instantiates a new aioboto3.Session for managing S3/R2 client lifecycle.
    """
    return aioboto3.Session()


@asynccontextmanager
async def get_r2_client(
    settings: Settings | None = None,
) -> AsyncGenerator[Any]:
    """
    Async context manager providing an aioboto3 S3 client targeted at Cloudflare R2.

    Input:
        settings (Settings | None): Configuration settings instance. Defaults to get_settings().

    Output:
        AsyncGenerator[Any, None]: Yields an active aioboto3 S3 client.

    Description & Logic:
        - Resolves configuration settings if not provided.
        - Constructs endpoint URL from r2_endpoint_url or r2_account_id if needed.
        - Yields a S3 client connected to Cloudflare R2 with region_name='auto'.
    """
    if settings is None:
        settings = get_settings()

    endpoint_url = settings.r2_endpoint_url
    if not endpoint_url and settings.r2_account_id:
        endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"

    session = create_r2_session()
    async with session.client(
        service_name="s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
        region_name="auto",
    ) as client:
        yield client
