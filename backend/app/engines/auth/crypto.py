"""
Cryptographic primitives for Phase 17 Authentication & Authorization.
Implements OWASP memory-hard password hashing using Python standard library hashlib.scrypt,
constant-time digest verification, and cryptographically secure token generators.
"""

import hashlib
import hmac
import secrets
from typing import Tuple


SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 32 * 1024 * 1024  # 32MB
SALT_BYTES = 16
KEY_BYTES = 64


def hash_password(password: str) -> str:
    """
    Hashes a password using OWASP-compliant memory-hard scrypt.
    Format: scrypt$<n>$<r>$<p>$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty")

    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
        dklen=KEY_BYTES,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a password against a stored scrypt hash using constant-time comparison.
    Returns False if hash is malformed or verification fails.
    """
    if not password or not password_hash:
        return False

    try:
        parts = password_hash.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False

        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected_hash = bytes.fromhex(parts[5])

        derived = hashlib.scrypt(
            password=password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=SCRYPT_MAXMEM,
            dklen=len(expected_hash),
        )
        return hmac.compare_digest(derived, expected_hash)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a URL-safe cryptographically secure random token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """
    Computes SHA-256 hash of a session or reset token.
    Only token hashes are stored server-side to prevent credential leakage.
    """
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Backward-compatible alias
hash_session_token = hash_token
