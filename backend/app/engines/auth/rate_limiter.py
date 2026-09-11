"""
Thread-safe in-memory rate limiter for login failure and brute-force protection.
Tracks failed authentication attempts within a sliding time window and applies
temporary lockouts without leaking lockout internals to external attackers.
"""

from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional, Tuple

from backend.app.core.config import settings


class LoginRateLimiter:
    """
    Sliding window rate limiter protecting authentication endpoints.
    """

    def __init__(
        self,
        max_attempts: Optional[int] = None,
        window_seconds: Optional[int] = None,
        lockout_seconds: Optional[int] = None,
    ):
        self.max_attempts = max_attempts or settings.AUTH_LOGIN_MAX_ATTEMPTS
        self.window_seconds = window_seconds or settings.AUTH_LOGIN_WINDOW_SECONDS
        self.lockout_seconds = lockout_seconds or settings.AUTH_LOGIN_LOCKOUT_SECONDS
        self._lock = threading.Lock()
        # key -> list of failure timestamps (unix epoch float)
        self._failures: Dict[str, List[float]] = {}
        # key -> lockout expiry timestamp (unix epoch float)
        self._lockouts: Dict[str, float] = {}

    def _get_now(self) -> float:
        return datetime.now(timezone.utc).timestamp()

    def is_locked(self, key: str) -> Tuple[bool, int]:
        """
        Checks whether the key (e.g. email or email:ip) is currently locked out.
        Returns (is_locked, seconds_remaining).
        """
        now = self._get_now()
        with self._lock:
            lockout_until = self._lockouts.get(key)
            if lockout_until:
                if now < lockout_until:
                    remaining = int(lockout_until - now) + 1
                    return True, remaining
                else:
                    # Lockout expired
                    del self._lockouts[key]
                    self._failures.pop(key, None)
            return False, 0

    def record_failure(self, key: str) -> None:
        """
        Records a failed attempt. If failures exceed threshold within the window,
        locks the key for lockout_seconds.
        """
        now = self._get_now()
        with self._lock:
            # Clean old failures outside sliding window
            failures = self._failures.get(key, [])
            cutoff = now - self.window_seconds
            failures = [t for t in failures if t > cutoff]
            failures.append(now)
            self._failures[key] = failures

            if len(failures) >= self.max_attempts:
                self._lockouts[key] = now + self.lockout_seconds

    def record_success(self, key: str) -> None:
        """Clears failures and lockouts on successful authentication."""
        with self._lock:
            self._failures.pop(key, None)
            self._lockouts.pop(key, None)

    def reset(self) -> None:
        """Clears all tracking state (used in testing)."""
        with self._lock:
            self._failures.clear()
            self._lockouts.clear()


# Global singleton instance
login_rate_limiter = LoginRateLimiter()
