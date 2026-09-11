"""
Data Quality Engine Thresholds
Centralized thresholds and configuration values for deterministic quality rules.
"""

from backend.app.core.config import settings

# Missingness percentage thresholds
QUALITY_MISSING_LOW: float = settings.QUALITY_MISSING_LOW
QUALITY_MISSING_MEDIUM: float = settings.QUALITY_MISSING_MEDIUM
QUALITY_MISSING_HIGH: float = settings.QUALITY_MISSING_HIGH
QUALITY_MISSING_CRITICAL: float = settings.QUALITY_MISSING_CRITICAL

# Constant / near-constant threshold (percentage of total non-null rows occupied by dominant value)
QUALITY_NEAR_CONSTANT_THRESHOLD: float = settings.QUALITY_NEAR_CONSTANT_THRESHOLD

# Outlier IQR multiplier (Tukey's standard: 1.5 for moderate outliers)
QUALITY_OUTLIER_IQR_MULTIPLIER: float = settings.QUALITY_OUTLIER_IQR_MULTIPLIER

# High cardinality ratio for non-identifier string columns
QUALITY_HIGH_CARDINALITY_THRESHOLD: float = settings.QUALITY_HIGH_CARDINALITY_THRESHOLD

# Version identifier for deterministic scoring and rule catalog
QUALITY_REPORT_VERSION: str = settings.QUALITY_REPORT_VERSION
