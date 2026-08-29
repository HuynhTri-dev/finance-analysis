from __future__ import annotations

"""
name: s3_provider.py
description: Physical storage provider implementation using aioboto3
             for S3-compatible systems like Cloudflare R2.
"""

import logging
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from app.core.config import Settings, get_settings
from app.infra.storage.base import IStorageProvider
from app.infra.storage.cloudflare_r2 import get_r2_client

logger = logging.getLogger(__name__)


class S3StorageProvider(IStorageProvider):
    """
    S3 / Cloudflare R2 storage provider implementation of IStorageProvider.
    Handles physical byte read, write, and delete operations against cloud object storage.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize S3StorageProvider.

        Input:
            settings (Settings | None): Config settings instance. Defaults to get_settings().

        Output:
            None

        Description & Logic:
            - Stores settings and bucket name for async storage operations.
        """
        self.settings = settings or get_settings()
        self.bucket_name = self.settings.bucket_name

    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        """
        Upload raw bytes to S3/R2 storage.

        Input:
            file_data (bytes): Raw binary content.
            object_name (str): Destination key/path in storage.
            content_type (str | None): Optional HTTP Content-Type.

        Output:
            str: Object key / storage path after successful upload.

        Description & Logic:
            - Connects async S3 client via get_r2_client context manager.
            - Prepares put_object parameters including Body, Bucket, Key, and optional ContentType.
            - Executes put_object and returns object_name key.
        """
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type

        async with get_r2_client(self.settings) as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                **extra_args,
            )
        return object_name

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete an object from S3/R2 storage.

        Input:
            object_name (str): Target key to delete.

        Output:
            bool: True if deleted successfully, False if error occurs.

        Description & Logic:
            - Calls delete_object on S3 client.
            - Catches ClientError and returns False if deletion fails.
        """
        try:
            async with get_r2_client(self.settings) as client:
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False

    async def get_file_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        Generate presigned download URL for an S3/R2 object key.

        Input:
            object_name (str): Storage object key.
            expires_in (int): Expiration duration in seconds.

        Output:
            str: Generated presigned URL.

        Description & Logic:
            - Calls client.generate_presigned_url for get_object action.
        """
        async with get_r2_client(self.settings) as client:
            url: str = await client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expires_in,
            )
            return url

    async def download_file(self, object_name: str) -> bytes:
        """
        Download object content from S3/R2 storage.

        Input:
            object_name (str): Key of object to download.

        Output:
            bytes: Raw downloaded binary bytes.

        Description & Logic:
            - Issues get_object request to S3 client.
            - Reads Body stream asynchronously into bytes.
        """
        async with get_r2_client(self.settings) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
            async with response["Body"] as stream:
                data: bytes = await stream.read()
                return data

    async def list_files(self, prefix: str = "reports/") -> list[dict]:
        """
        List objects from S3/R2 storage under a specific prefix.

        Input:
            prefix (str): Storage key prefix (e.g. 'reports/').

        Output:
            list[dict]: List of object metadata dictionaries.

        Description & Logic:
            - Calls list_objects_v2 on the S3/R2 client.
            - Generates presigned URLs for each found object.
            - Returns list of objects sorted by last modified date descending.
        """
        results: list[dict] = []
        try:
            async with get_r2_client(self.settings) as client:
                response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                )
                contents = response.get("Contents", [])
                # Sort newest first
                sorted_contents = sorted(
                    contents,
                    key=lambda x: x.get("LastModified", ""),
                    reverse=True,
                )
                for item in sorted_contents:
                    key = item.get("Key", "")
                    if not key or key.endswith("/"):
                        continue
                    size_bytes = item.get("Size", 0)
                    last_modified = item.get("LastModified")
                    iso_time = last_modified.isoformat() if last_modified else ""

                    url = await client.generate_presigned_url(
                        ClientMethod="get_object",
                        Params={"Bucket": self.bucket_name, "Key": key},
                        ExpiresIn=604800,  # 7 days
                    )
                    filename = key.split("/")[-1]
                    results.append({
                        "filename": filename,
                        "url": url,
                        "size_kb": round(size_bytes / 1024, 1),
                        "created_at": iso_time,
                    })
        except Exception as e:
            logger.warning("Failed to list files from S3/R2: %s", e)
        return results
