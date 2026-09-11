"""
AnalyzaX — Phase 25: Scoped Analytical Memory Engine.
Maintains authorized analytical memory across USER, WORKSPACE, PROJECT, and SESSION scopes
with automated secret scrubbing and isolation enforcement.
"""

import re
import threading
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MemoryScope(str, Enum):
    USER = "USER"
    WORKSPACE = "WORKSPACE"
    PROJECT = "PROJECT"
    SESSION = "SESSION"


FORBIDDEN_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9_\-]{20,}",
    r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"password[\"']?\s*[:=]\s*[\"'][^\"']+[\"']",
    r"postgres(ql)?://[^\s]+",
    r"mysql://[^\s]+",
]


class AnalyticalMemoryEngine:
    """Thread-safe analytical memory scoped to authorized tenants and sessions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # scope_key -> dict of analytical state
        # scope_key format: "{scope}:{id}" (e.g. "WORKSPACE:ws_123", "SESSION:sess_456")
        self._memory: Dict[str, Dict[str, Any]] = {}

    def _sanitize(self, value: Any) -> Any:
        """Removes secrets, keys, or sensitive patterns from values prior to storing in memory."""
        if isinstance(value, str):
            clean = value
            for pattern in FORBIDDEN_SECRET_PATTERNS:
                clean = re.sub(pattern, "[REDACTED_SECRET]", clean, flags=re.IGNORECASE)
            return clean
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items() if not any(s in k.lower() for s in ["password", "secret", "token", "key"])}
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        return value

    def set_entry(
        self,
        scope: MemoryScope,
        scope_id: str,
        key: str,
        value: Any,
    ) -> None:
        scope_key = f"{scope.value}:{scope_id}"
        sanitized_value = self._sanitize(value)
        with self._lock:
            store = self._memory.setdefault(scope_key, {})
            store[key] = sanitized_value

    def get_entry(
        self,
        scope: MemoryScope,
        scope_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        scope_key = f"{scope.value}:{scope_id}"
        with self._lock:
            store = self._memory.get(scope_key, {})
            return store.get(key, default)

    def get_all_for_scope(
        self,
        scope: MemoryScope,
        scope_id: str,
    ) -> Dict[str, Any]:
        scope_key = f"{scope.value}:{scope_id}"
        with self._lock:
            return dict(self._memory.get(scope_key, {}))

    def clear_scope(
        self,
        scope: MemoryScope,
        scope_id: str,
    ) -> None:
        scope_key = f"{scope.value}:{scope_id}"
        with self._lock:
            if scope_key in self._memory:
                del self._memory[scope_key]

    def record_memory(
        self,
        scope: Any,
        scope_id: str,
        key: str,
        content: Any,
    ) -> None:
        mem_scope = MemoryScope(scope) if isinstance(scope, str) else scope
        self.set_entry(mem_scope, scope_id, key, content)

    def get_recent_context(
        self,
        scope: Any,
        scope_id: str,
        limit: int = 5,
    ) -> List[Any]:
        mem_scope = MemoryScope(scope) if isinstance(scope, str) else scope
        entries = self.get_all_for_scope(mem_scope, scope_id)
        class MemItem:
            def __init__(self, key: str, content: Any):
                self.key = key
                self.content = content
        return [MemItem(k, v) for k, v in list(entries.items())[-limit:]]


analytical_memory = AnalyticalMemoryEngine()
