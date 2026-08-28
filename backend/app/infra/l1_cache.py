"""
name: l1_cache.py
description: Lightweight, thread-safe in-memory cache helper (L1 cache) with TTL expiration.
"""

import time
from typing import Any


class L1Cache:
    """
    In-memory key-value cache with expiration.
    """

    def __init__(self, default_ttl: float = 5.0) -> None:
        """
        Initialise cache container.

        Input:
            default_ttl (float): Default duration in seconds to keep items in cache.

        Output:
            None

        Description & Logic:
            - Set internal dictionary and default TTL limit.
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """
        Retrieve value from cache if it exists and has not expired.

        Input:
            key (str): Unique cache key identifier.

        Output:
            Any | None: Cached value, or None if missing or expired.

        Description & Logic:
            - Check if key exists. If not, return None.
            - Compare current time with item expiration time.
            - If expired, delete item from dictionary and return None.
            - Return cached value.
        """
        if key not in self._cache:
            return None
        val, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        return val

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """
        Save value to cache with a specified or default TTL.

        Input:
            key (str): Unique cache key identifier.
            value (Any): Payload to store.
            ttl (float | None): Expiration time in seconds. Defaults to default_ttl.

        Output:
            None

        Description & Logic:
            - Compute expiration timestamp.
            - Write tuple of (value, expiration_timestamp) to dictionary.
        """
        ttl_val = ttl if ttl is not None else self._default_ttl
        self._cache[key] = (value, time.time() + ttl_val)

    def delete(self, key: str) -> None:
        """
        Remove key from cache manually.

        Input:
            key (str): Unique cache key identifier.

        Output:
            None

        Description & Logic:
            - Pop key from internal dictionary safely.
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """
        Clear all cached records.

        Input:
            None

        Output:
            None

        Description & Logic:
            - Clear the internal dictionary.
        """
        self._cache.clear()


# Global L1 Cache instance
l1_cache = L1Cache(default_ttl=5.0)
