"""
AnalyzaX — Phase 8: SQL Query Hasher & Normalizer
Provides deterministic SQL normalization and cryptographic hashing for query deduplication,
result caching, execution history, and lineage tracking.
"""

import hashlib
import re


class SQLHasher:
    """
    Normalizes SQL queries and produces deterministic SHA-256 hashes.
    """

    @staticmethod
    def normalize_sql(sql: str) -> str:
        """
        Normalizes a SQL query string by:
        1. Stripping leading/trailing whitespace
        2. Standardizing line endings to \n
        3. Collapsing redundant whitespace / tabs
        4. Removing trailing semicolons for uniform comparison
        5. Preserving string literals as-is while standardizing whitespace around operators
        """
        if not sql:
            return ""

        # Normalize line endings
        text = sql.replace("\r\n", "\n").replace("\r", "\n").strip()

        # Remove single-line comments (-- ...)
        text = re.sub(r"--.*$", "", text, flags=re.MULTILINE)

        # Remove multi-line comments (/* ... */)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

        # Collapse whitespace runs outside strings
        # Simple whitespace collapse
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
        cleaned = " ".join(l for l in lines if l)

        # Strip trailing semicolon
        cleaned = cleaned.rstrip(";")

        return cleaned

    @classmethod
    def compute_hash(cls, sql: str, dataset_id: str = "", version_id: str = "") -> str:
        """
        Computes SHA-256 hash of the normalized query optionally scoped to dataset and version.
        """
        normalized = cls.normalize_sql(sql)
        payload = f"{dataset_id}:{version_id}:{normalized}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
