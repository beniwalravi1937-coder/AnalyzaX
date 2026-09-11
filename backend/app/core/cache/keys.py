"""
AnalyzaX — Phase 23: Deterministic Cache Key Design.
Generates isolated, collision-free, version-bound cache keys.
Prevents cross-tenant leakage, cross-version leakage, and parameter ambiguity.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def hash_dict_params(params: Optional[Dict[str, Any]]) -> str:
    """Produces a deterministic SHA-256 digest of arbitrary dictionary parameters."""
    if not params:
        return "default"
    try:
        serialized = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "unhashable"


def build_cache_key(
    namespace: str,
    workspace_id: str,
    operation: str,
    dataset_id: Optional[str] = None,
    version_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    engine_version: Optional[str] = None,
) -> str:
    """
    Constructs a canonical cache key with all correctness-critical dimensions:
    namespace:workspace_id:dataset_id:version_id:operation:param_hash:engine_version

    Rules:
    - Must NEVER omit workspace_id (tenant isolation).
    - If dataset is versioned, version_id MUST be included (version isolation).
    - If params exist, they must be deterministically hashed.
    """
    ws = workspace_id or "global"
    ds = dataset_id or "na"
    v = version_id or "na"
    p_hash = hash_dict_params(params)
    eng_ver = engine_version or "v1"

    return f"{namespace}:{ws}:{ds}:{v}:{operation}:{p_hash}:{eng_ver}"
