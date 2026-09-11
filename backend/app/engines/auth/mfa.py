"""
AnalyzaX — Phase 24: RFC 6238 TOTP Multi-Factor Authentication Engine.
Standard, deterministic implementation of Time-based One-Time Passwords (RFC 6238 / RFC 4226)
and single-use hashed recovery codes with zero external dependencies.
"""

import base64
import hashlib
import hmac
import math
import secrets
import struct
import time
from typing import List, Optional, Tuple
from urllib.parse import quote

from backend.app.core.config import settings


class TOTPEngine:
    """
    Implements RFC 6238 TOTP (Time-Based One-Time Password Algorithm).
    - Uses HMAC-SHA1 by default per RFC 6238 specification for universal authenticator compatibility.
    - Standard 30-second time steps.
    - 6-digit decimal tokens.
    - Supports clock drift tolerance (default: ±1 step, i.e., ±30 seconds).
    """

    TIME_STEP_SECONDS = 30
    DIGITS = 6

    @classmethod
    def generate_secret(cls) -> str:
        """Generates a cryptographically secure 160-bit Base32 secret key."""
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode("ascii").rstrip("=")

    @classmethod
    def _get_time_counter(cls, timestamp: Optional[float] = None) -> int:
        ts = timestamp if timestamp is not None else time.time()
        return int(math.floor(ts / cls.TIME_STEP_SECONDS))

    @classmethod
    def generate_totp(cls, secret: str, timestamp: Optional[float] = None) -> str:
        """Generates the 6-digit TOTP string for a given secret and timestamp."""
        counter = cls._get_time_counter(timestamp)
        return cls._generate_hotp(secret, counter)

    @classmethod
    def _generate_hotp(cls, secret: str, counter: int) -> str:
        """RFC 4226 HOTP core computation."""
        # Pad secret to base32 multiple of 8 if needed
        secret_clean = secret.strip().replace(" ", "").upper()
        missing_padding = len(secret_clean) % 8
        if missing_padding != 0:
            secret_clean += "=" * (8 - missing_padding)

        key = base64.b32decode(secret_clean, casefold=True)
        counter_bytes = struct.pack(">Q", counter)

        # HMAC-SHA1
        hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation (RFC 4226 Section 5.3)
        offset = hmac_digest[-1] & 0x0F
        binary_code = (
            ((hmac_digest[offset] & 0x7F) << 24)
            | ((hmac_digest[offset + 1] & 0xFF) << 16)
            | ((hmac_digest[offset + 2] & 0xFF) << 8)
            | (hmac_digest[offset + 3] & 0xFF)
        )

        totp_num = binary_code % (10 ** cls.DIGITS)
        return f"{totp_num:0{cls.DIGITS}d}"

    @classmethod
    def verify_totp(
        cls, secret: str, code: str, drift_steps: int = 1, timestamp: Optional[float] = None
    ) -> bool:
        """
        Verifies a user-supplied TOTP code against the secret.
        Allows for ±drift_steps time drift to account for client clock skew.
        Uses constant-time comparison.
        """
        if not code or len(code.strip()) != cls.DIGITS or not code.strip().isdigit():
            return False

        clean_code = code.strip()
        current_counter = cls._get_time_counter(timestamp)

        # Check counter range: [current - drift_steps, current + drift_steps]
        for step_offset in range(-drift_steps, drift_steps + 1):
            expected = cls._generate_hotp(secret, current_counter + step_offset)
            if hmac.compare_digest(clean_code, expected):
                return True

        return False

    @classmethod
    def get_provisioning_uri(
        cls,
        secret: str,
        account_name: str,
        issuer: str = "AnalyzaX",
    ) -> str:
        """
        Generates standard otpauth:// URL for scanning into Google Authenticator,
        Microsoft Authenticator, 1Password, etc.
        """
        label = quote(f"{issuer}:{account_name}")
        params = f"secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={cls.DIGITS}&period={cls.TIME_STEP_SECONDS}"
        return f"otpauth://totp/{label}?{params}"


class RecoveryCodeEngine:
    """Manages secure, single-use hashed recovery backup codes."""

    @staticmethod
    def generate_codes(count: int = 8) -> Tuple[List[str], List[str]]:
        """
        Generates clean human-readable recovery codes formatted as 'XXXX-XXXX'.
        Returns: (raw_codes: List[str], hashed_codes: List[str])
        Raw codes are returned to the user ONCE during setup.
        Hashed codes are stored safely at rest.
        """
        raw_codes = []
        hashed_codes = []

        for _ in range(count):
            token = secrets.token_hex(4).upper()
            formatted = f"{token[:4]}-{token[4:]}"
            raw_codes.append(formatted)

            digest = hashlib.sha256(formatted.replace("-", "").upper().encode("utf-8")).hexdigest()
            hashed_codes.append(digest)

        return raw_codes, hashed_codes

    @staticmethod
    def verify_and_consume(
        code: str, hashed_codes: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Verifies if code matches any stored hash using constant-time comparison.
        If matched, consumes that code (removes it from the list) and returns (True, updated_list).
        If not matched, returns (False, unchanged_list).
        """
        clean_code = code.strip().replace("-", "").upper()
        if not clean_code:
            return False, hashed_codes

        input_hash = hashlib.sha256(clean_code.encode("utf-8")).hexdigest()

        matched_index = -1
        for idx, stored_hash in enumerate(hashed_codes):
            if hmac.compare_digest(input_hash, stored_hash):
                matched_index = idx
                break

        if matched_index >= 0:
            remaining = [h for i, h in enumerate(hashed_codes) if i != matched_index]
            return True, remaining

        return False, hashed_codes


class MFAChallengeEngine:
    """Manages short-lived, tamper-proof MFA challenge tokens for 2-step login."""

    CHALLENGE_TTL_SECONDS = 300  # 5 minutes

    @classmethod
    def create_challenge_token(cls, user_id: str) -> str:
        """Creates a signed challenge token for a user who passed password check."""
        expires_at = int(time.time()) + cls.CHALLENGE_TTL_SECONDS
        nonce = secrets.token_hex(8)
        payload = f"mfa:{user_id}:{expires_at}:{nonce}"
        sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        raw = f"{payload}:{sig}"
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")

    @classmethod
    def verify_challenge_token(cls, token: str) -> Optional[str]:
        """
        Verifies challenge token signature and expiration.
        Returns user_id if valid, or None if invalid or expired.
        """
        try:
            raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
            parts = raw.split(":")
            if len(parts) != 5 or parts[0] != "mfa":
                return None

            user_id = parts[1]
            expires_at = int(parts[2])
            nonce = parts[3]
            sig = parts[4]

            if time.time() > expires_at:
                return None

            expected_payload = f"mfa:{user_id}:{expires_at}:{nonce}"
            expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(expected_sig, sig):
                return None

            return user_id
        except Exception:
            return None
