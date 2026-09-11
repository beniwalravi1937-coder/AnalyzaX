"""
Multi-Signal Semantic Type Inference Module
Classifies columns into controlled semantic taxonomy with calibrated confidence scores.
"""

import re
from typing import Any, List, Optional, Tuple

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")
URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
PHONE_REGEX = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")

# Controlled naming keyword patterns
MONETARY_KEYWORDS = ("price", "cost", "revenue", "sales", "salary", "amount", "charge", "fare", "fee", "income", "profit", "budget", "total_due", "balance")
PERCENTAGE_KEYWORDS = ("pct", "percent", "percentage", "rate", "ratio", "margin", "discount")
IDENTIFIER_KEYWORDS = ("id", "uuid", "guid", "key", "code", "hash", "num", "number", "sku", "isbn", "account")
LAT_KEYWORDS = ("lat", "latitude", "coord_lat")
LON_KEYWORDS = ("lon", "lng", "longitude", "coord_lon")


def infer_semantic_type(
    col_name: str,
    physical_type: str,
    unique_count: int,
    total_non_null: int,
    cardinality_ratio: float,
    sample_values: List[Any],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    is_text: bool = False,
) -> Tuple[str, float, bool, float]:
    """
    Infers the semantic type and confidence using physical type, naming, patterns, and cardinality.
    Returns: (semantic_type, confidence, is_identifier_candidate, identifier_confidence)
    """
    clean_name = col_name.strip().lower().replace("-", "_")
    name_parts = clean_name.split("_")

    # 1. Specialized String Types (Email, URL, Phone) take priority over generic uniqueness
    if physical_type == "string" and sample_values:
        valid_strings = [str(s).strip() for s in sample_values if s is not None and str(s).strip()]
        if valid_strings:
            email_matches = sum(1 for s in valid_strings if EMAIL_REGEX.match(s))
            if (email_matches / len(valid_strings) >= 0.8) or "email" in clean_name:
                return "email", 0.95, False, 0.0

            url_matches = sum(1 for s in valid_strings if URL_REGEX.match(s))
            if (url_matches / len(valid_strings) >= 0.8) or any(k in clean_name for k in ("url", "website", "link")):
                return "url", 0.95, False, 0.0

            phone_matches = sum(1 for s in valid_strings if PHONE_REGEX.match(s))
            if (phone_matches / len(valid_strings) >= 0.8) and any(k in clean_name for k in ("phone", "mobile", "tel", "fax")):
                return "phone", 0.90, False, 0.0

    # 2. Geographic Coordinates
    if physical_type in ("float", "decimal"):
        if any(clean_name == kw or clean_name.endswith(kw) for kw in LAT_KEYWORDS):
            if min_val is not None and max_val is not None and -90.0 <= min_val and max_val <= 90.0:
                return "geographic_latitude", 0.95, False, 0.0
        if any(clean_name == kw or clean_name.endswith(kw) for kw in LON_KEYWORDS):
            if min_val is not None and max_val is not None and -180.0 <= min_val and max_val <= 180.0:
                return "geographic_longitude", 0.95, False, 0.0

    # 3. Date and Datetime
    if physical_type == "datetime":
        return "datetime", 0.98, False, 0.0
    if physical_type == "date":
        return "date", 0.98, False, 0.0
    if physical_type == "time":
        return "time", 0.95, False, 0.0

    if physical_type == "string" and any(k in clean_name for k in ("date", "time", "timestamp", "created_at", "updated_at")):
        return "datetime", 0.85, False, 0.0

    # 4. Boolean Check
    if physical_type == "boolean":
        return "boolean", 1.0, False, 0.0
    if unique_count == 2 and total_non_null >= 2:
        str_samples = {str(s).strip().lower() for s in sample_values if s is not None}
        if str_samples.issubset({"0", "1", "0.0", "1.0", "true", "false", "yes", "no", "t", "f", "y", "n"}):
            return "boolean", 0.90, False, 0.0

    # 5. Identifier Check
    is_identifier = False
    id_conf = 0.0
    if total_non_null > 0 and cardinality_ratio >= 0.95:
        if any(kw in name_parts for kw in IDENTIFIER_KEYWORDS) or clean_name.endswith("id"):
            is_identifier = True
            id_conf = 0.95
        elif cardinality_ratio == 1.0 and physical_type in ("integer", "string") and not any(kw in clean_name for kw in MONETARY_KEYWORDS):
            is_identifier = True
            id_conf = 0.80

    if is_identifier:
        return "identifier", id_conf, True, id_conf

    # 6. Percentage / Ratio Check
    if physical_type in ("float", "decimal"):
        if any(kw in clean_name for kw in PERCENTAGE_KEYWORDS):
            if min_val is not None and max_val is not None:
                if 0.0 <= min_val and max_val <= 1.0:
                    return "ratio", 0.90, False, 0.0
                if 0.0 <= min_val and max_val <= 100.0:
                    return "percentage", 0.92, False, 0.0
            return "percentage", 0.80, False, 0.0

    # 7. Monetary Check
    if physical_type in ("float", "decimal", "integer"):
        if any(kw in clean_name for kw in MONETARY_KEYWORDS):
            conf = 0.90 if (min_val is not None and min_val >= 0) else 0.80
            return "monetary", conf, False, 0.0

    # 8. Numeric fallback (integer vs decimal)
    if physical_type == "integer":
        return "integer", 0.85, False, 0.0
    if physical_type in ("float", "decimal"):
        return "decimal", 0.85, False, 0.0

    # 9. Categorical vs Long-Form Text
    if physical_type == "string":
        if is_text:
            return "text", 0.85, False, 0.0
        return "categorical", 0.85, False, 0.0

    return "unknown", 0.50, False, 0.0
