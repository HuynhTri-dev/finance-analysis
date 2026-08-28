"""
name: __init__.py
description: Storage infrastructure package exports.
"""

from app.infra.storage.base import IStorageProvider
from app.infra.storage.cloudflare_r2 import create_r2_session, get_r2_client
from app.infra.storage.s3_provider import S3StorageProvider

__all__ = [
    "IStorageProvider",
    "S3StorageProvider",
    "create_r2_session",
    "get_r2_client",
]
