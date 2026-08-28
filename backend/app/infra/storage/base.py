"""
name: base.py
description: Abstract interface definition for cloud storage providers
             (S3, Cloudflare R2, Azure, etc.).
"""

from abc import ABC, abstractmethod


class IStorageProvider(ABC):
    """
    Abstract Base Class defining the contract for object storage implementations.
    """

    @abstractmethod
    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        """
        Upload binary file data to object storage.

        Input:
            file_data (bytes): Raw binary content of the file.
            object_name (str): Destination key/path in object storage.
            content_type (str | None): Optional MIME type of the file.

        Output:
            str: Public or internal storage location URL / object key.

        Description & Logic:
            - Asynchronously uploads bytes to storage backend under the given object_name key.
        """
        pass

    @abstractmethod
    async def delete_file(self, object_name: str) -> bool:
        """
        Delete an object from storage.

        Input:
            object_name (str): Key/path of the object to delete.

        Output:
            bool: True if deletion was successful, False otherwise.

        Description & Logic:
            - Removes the specified object key from object storage.
        """
        pass

    @abstractmethod
    async def get_file_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        Generate a pre-signed or direct public access URL for an object.

        Input:
            object_name (str): Key/path of the target object.
            expires_in (int): Expiration window in seconds for presigned links.

        Output:
            str: Pre-signed or absolute URL string.

        Description & Logic:
            - Creates a downloadable URL for client consumption.
        """
        pass

    @abstractmethod
    async def download_file(self, object_name: str) -> bytes:
        """
        Download binary object content from storage.

        Input:
            object_name (str): Key/path of the target object.

        Output:
            bytes: Raw binary file content.

        Description & Logic:
            - Fetches and returns raw bytes from the target object key.
        """
        pass
