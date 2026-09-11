"""
AnalyzaX — Phase 24: Enterprise Cryptographic Key Management & AEAD Encryption.
Implements authenticated symmetric encryption (AES-256-GCM) with key versioning,
deterministic HKDF key derivation, and seamless key rotation support.
"""

import base64
import os
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from backend.app.core.config import settings


class KeyManager:
    """
    Coordinates application-level authenticated encryption using standard AES-256-GCM.
    Supports versioned encryption keys to enable key rotation without data loss.
    """

    CURRENT_KEY_VERSION = "v1"

    def __init__(self, master_secret: Optional[str] = None) -> None:
        self._master_secret = (master_secret or settings.SECRET_KEY).encode("utf-8")
        self._keys: Dict[str, bytes] = {}
        # Derive default v1 key
        self._keys["v1"] = self._derive_key("analyzax_data_key_v1")
        # Derive v2 key for rotation readiness
        self._keys["v2"] = self._derive_key("analyzax_data_key_v2")

    def _derive_key(self, info_tag: str) -> bytes:
        """Derives a 256-bit key from the master secret via HKDF-SHA256."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=b"analyzax_hkdf_salt_2026",
            info=info_tag.encode("utf-8"),
        )
        return hkdf.derive(self._master_secret)

    def register_key(self, key_version: str, key_material: bytes) -> None:
        """Allows registering a specific key version."""
        if len(key_material) != 32:
            raise ValueError("Key material must be exactly 32 bytes (256 bits) for AES-256.")
        self._keys[key_version] = key_material

    def encrypt(self, plaintext: str, key_version: Optional[str] = None) -> str:
        """
        Encrypts plaintext string using AES-256-GCM.
        Envelope format: '{key_version}:{nonce_b64}:{ciphertext_b64}'
        """
        if not plaintext:
            return ""

        ver = key_version or self.CURRENT_KEY_VERSION
        key = self._keys.get(ver)
        if not key:
            raise ValueError(f"Unknown encryption key version: '{ver}'")

        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), ver.encode("utf-8"))

        nonce_b64 = base64.urlsafe_b64encode(nonce).decode("ascii")
        ct_b64 = base64.urlsafe_b64encode(ciphertext).decode("ascii")

        return f"{ver}:{nonce_b64}:{ct_b64}"

    def decrypt(self, envelope: str) -> str:
        """
        Decrypts an envelope encrypted with AES-256-GCM.
        Automatically resolves the appropriate key version.
        """
        if not envelope:
            return ""

        parts = envelope.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid encrypted envelope format. Expected 'version:nonce:ciphertext'.")

        ver, nonce_b64, ct_b64 = parts
        key = self._keys.get(ver)
        if not key:
            raise ValueError(f"Encryption key version '{ver}' not found for decryption.")

        try:
            nonce = base64.urlsafe_b64decode(nonce_b64.encode("ascii"))
            ciphertext = base64.urlsafe_b64decode(ct_b64.encode("ascii"))
            aesgcm = AESGCM(key)
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, ver.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: cryptographic integrity check or tag mismatch ({e})")

    def rotate(self, envelope: str, target_version: str = "v2") -> str:
        """Re-encrypts ciphertext envelope with target key version."""
        plaintext = self.decrypt(envelope)
        return self.encrypt(plaintext, key_version=target_version)


key_manager = KeyManager()
