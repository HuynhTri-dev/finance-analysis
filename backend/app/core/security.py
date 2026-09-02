"""
name: security.py
description: Password hashing and verification utilities using PBKDF2-HMAC-SHA256
             with cryptographically secure random salts.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using PBKDF2-HMAC-SHA256 with 100,000 iterations.

    Args:
        password (str): Plain-text password to hash.

    Returns:
        str: Formatted string 'salt$hash' in hexadecimal representation.
    """
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return f"{salt}${hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored 'salt$hash' string.

    Args:
        plain_password (str): Plain-text password provided by user.
        hashed_password (str): Stored 'salt$hash' string.

    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()
        return hmac.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False
