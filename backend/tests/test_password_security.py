"""
Unit tests for Phase 17 Password Security & Cryptography.
"""

import pytest
from backend.app.engines.auth.crypto import (
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_scrypt_password_hashing():
    pwd = "SecurePassword123!"
    h = hash_password(pwd)
    assert h.startswith("scrypt$16384$8$1$")
    assert verify_password(pwd, h) is True
    assert verify_password("WrongPassword123!", h) is False


def test_salt_uniqueness():
    pwd = "IdenticalPassword123!"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)
    assert h1 != h2, "Salts must be uniquely generated per hash call"
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True


def test_malformed_hash_verification():
    assert verify_password("pass", "malformed") is False
    assert verify_password("pass", "scrypt$invalid$format") is False
    assert verify_password("pass", "") is False
    assert verify_password("", "scrypt$16384$8$1$abc$def") is False


def test_empty_password_rejection():
    with pytest.raises(ValueError):
        hash_password("")


def test_secure_token_and_hashing():
    token1 = generate_secure_token(32)
    token2 = generate_secure_token(32)
    assert token1 != token2
    assert len(token1) >= 40

    th1 = hash_token(token1)
    th2 = hash_token(token2)
    assert len(th1) == 64  # SHA-256 hex length
    assert th1 != th2
    # Deterministic token hashing
    assert hash_token(token1) == th1
