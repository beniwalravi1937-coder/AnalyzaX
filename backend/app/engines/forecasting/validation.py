"""
AnalyzaX — Phase 12: Time-Series Temporal Validation & Frequency Detection.
Provides deterministic time-column detection, frequency inference, regularity scoring,
gap analysis, duplicate detection, and target validation.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import polars as pl

from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException
from backend.app.engines.forecasting.models import (
    ForecastFrequency,
    ForecastQualityIssue,
    QualitySeverity,
    RegularityStatus,
    TemporalValidationReport,
)


def detect_time_column_candidates(df: pl.DataFrame) -> List[Dict[str, Any]]:
    """Detect and rank candidate time/date columns deterministically."""
    candidates = []

    name_patterns = [
        (re.compile(r"^(date|datetime|timestamp|time|created_at|updated_at|day|event_time|period|year|month)$", re.I), 0.4),
        (re.compile(r"(date|time|timestamp|day|month|year)", re.I), 0.2),
    ]

    for col in df.columns:
        score = 0.0
        dtype = df[col].dtype

        # 1. Physical type check
        if dtype in (pl.Date, pl.Datetime, pl.Time):
            score += 0.5
        elif dtype in (pl.Utf8, pl.String):
            # Check sample parseability
            sample = df[col].drop_nulls().head(20).to_list()
            if sample:
                try:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    valid_ratio = parsed.notnull().mean()
                    if valid_ratio > 0.8:
                        score += 0.4
                except Exception:
                    pass
        elif dtype in (pl.Int32, pl.Int64):
            # Could be epoch timestamp or year
            sample = df[col].drop_nulls().head(20).to_list()
            if sample and all(1900 <= x <= 2100 for x in sample if isinstance(x, (int, float))):
                score += 0.25

        # 2. Name heuristic
        for pattern, boost in name_patterns:
            if pattern.search(col):
                score += boost
                break

        # 3. Uniqueness and Monotonicity check
        try:
            s = df[col].drop_nulls()
            if len(s) > 1:
                uniq_ratio = s.n_unique() / len(s)
                if uniq_ratio > 0.8:
                    score += 0.1
        except Exception:
            pass

        if score >= 0.2:
            candidates.append({
                "column_name": col,
                "confidence": min(1.0, round(score, 2)),
                "data_type": str(dtype),
            })

    # Sort descending by confidence
    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    return candidates


def infer_frequency(timestamps: pd.Series) -> Tuple[ForecastFrequency, str, RegularityStatus, float]:
    """
    Infer temporal frequency, pandas frequency offset alias, regularity, and confidence
    based on successive timestamp differences.
    """
    if len(timestamps) < 3:
        return ForecastFrequency.CUSTOM, "D", RegularityStatus.INSUFFICIENT_DATA, 0.0

    sorted_ts = timestamps.sort_values().drop_duplicates()
    deltas = sorted_ts.diff().dropna()
    median_delta = deltas.median()
    total_seconds = median_delta.total_seconds()

    if total_seconds <= 0:
        return ForecastFrequency.CUSTOM, "D", RegularityStatus.IRREGULAR, 0.2

    # Map seconds to frequency
    # Minutely: 60s (+- 10s)
    if 50 <= total_seconds <= 70:
        freq = ForecastFrequency.MINUTELY
        pandas_str = "min"
    # Hourly: 3600s (+- 300s)
    elif 3300 <= total_seconds <= 3900:
        freq = ForecastFrequency.HOURLY
        pandas_str = "h"
    # Daily: 86400s (+- 3600s)
    elif 82800 <= total_seconds <= 90000:
        # Check if business day (no weekends)
        dayofweek = sorted_ts.dt.dayofweek
        if dayofweek.max() < 5 and len(sorted_ts) >= 10:
            freq = ForecastFrequency.BUSINESS_DAY
            pandas_str = "B"
        else:
            freq = ForecastFrequency.DAILY
            pandas_str = "D"
    # Weekly: 7 days (+- 1 day)
    elif 500000 <= total_seconds <= 700000:
        freq = ForecastFrequency.WEEKLY
        pandas_str = "W"
    # Monthly: ~28 - 31 days
    elif 2300000 <= total_seconds <= 2750000:
        freq = ForecastFrequency.MONTHLY
        pandas_str = "MS"
    # Quarterly: ~90 - 92 days
    elif 7500000 <= total_seconds <= 8200000:
        freq = ForecastFrequency.QUARTERLY
        pandas_str = "QS"
    # Yearly: ~365 days
    elif 30000000 <= total_seconds <= 33000000:
        freq = ForecastFrequency.YEARLY
        pandas_str = "YS"
    else:
        freq = ForecastFrequency.CUSTOM
        pandas_str = "D"

    # Regularity evaluation
    delta_seconds = deltas.dt.total_seconds()
    coef_variation = delta_seconds.std() / max(1.0, delta_seconds.mean())

    if coef_variation < 0.05:
        regularity = RegularityStatus.REGULAR
        confidence = 0.95
    elif coef_variation < 0.25:
        regularity = RegularityStatus.MOSTLY_REGULAR
        confidence = 0.80
    else:
        regularity = RegularityStatus.IRREGULAR
        confidence = 0.50

    return freq, pandas_str, regularity, confidence


def validate_time_series(
    df: pl.DataFrame,
    time_column: str,
    target_column: str,
    user_frequency: Optional[ForecastFrequency] = None,
) -> TemporalValidationReport:
    """Perform deterministic temporal validation on a dataset version."""
    issues: List[ForecastQualityIssue] = []
    warnings: List[str] = []

    # 1. Existence checks
    if time_column not in df.columns:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_TIME_COLUMN,
            message=f"Time column '{time_column}' not found in dataset.",
        )
    if target_column not in df.columns:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_TARGET,
            message=f"Target column '{target_column}' not found in dataset.",
        )
    if time_column == target_column:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_TARGET,
            message="Time column and Target column cannot be the same.",
        )

    # 2. Extract and parse time column
    time_series = df[time_column].to_pandas()
    try:
        parsed_ts = pd.to_datetime(time_series, errors="coerce")
    except Exception as e:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_TIME_COLUMN,
            message=f"Failed to parse time column '{time_column}' as datetime: {str(e)}",
        )

    null_ts_count = int(parsed_ts.isnull().sum())
    if null_ts_count > 0:
        issues.append(
            ForecastQualityIssue(
                issue_id="QI_NULL_TIMESTAMPS",
                issue_type="NULL_TIMESTAMPS",
                severity=QualitySeverity.HIGH if null_ts_count / len(df) > 0.1 else QualitySeverity.MEDIUM,
                description=f"Time column contains {null_ts_count} null or unparseable timestamps.",
                affected_rows=null_ts_count,
                recommendation="Drop or impute missing dates before forecasting.",
            )
        )

    valid_mask = parsed_ts.notnull()
    valid_ts = parsed_ts[valid_mask]

    if len(valid_ts) < 5:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INSUFFICIENT_HISTORY,
            message=f"Time series has only {len(valid_ts)} usable observations. Minimum 5 required.",
        )

    # Check duplicate timestamps
    duplicate_count = int(valid_ts.duplicated().sum())
    if duplicate_count > 0:
        issues.append(
            ForecastQualityIssue(
                issue_id="QI_DUPLICATE_TIMESTAMPS",
                issue_type="DUPLICATE_TIMESTAMPS",
                severity=QualitySeverity.HIGH,
                description=f"Found {duplicate_count} duplicate timestamps.",
                affected_rows=duplicate_count,
                recommendation="Aggregate duplicates by sum/mean or verify grouped series definition.",
            )
        )

    # 3. Frequency & Regularity
    inferred_freq, pandas_freq, regularity, confidence = infer_frequency(valid_ts)
    if user_frequency:
        inferred_freq = user_frequency

    # 4. Target column check
    target_series = df[target_column].to_pandas()
    # Check numeric type
    try:
        numeric_target = pd.to_numeric(target_series, errors="coerce")
    except Exception:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INVALID_TARGET,
            message=f"Target column '{target_column}' cannot be cast to numeric.",
        )

    target_missing = int(numeric_target.isnull().sum())
    target_zeros = int((numeric_target == 0).sum())

    valid_target = numeric_target[valid_mask].dropna()
    if len(valid_target) < 5:
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_INSUFFICIENT_HISTORY,
            message="Insufficient valid numeric target observations.",
        )

    t_mean = float(valid_target.mean())
    t_var = float(valid_target.var())

    if t_var == 0.0 or np.isnan(t_var):
        issues.append(
            ForecastQualityIssue(
                issue_id="QI_CONSTANT_TARGET",
                issue_type="CONSTANT_TARGET",
                severity=QualitySeverity.CRITICAL,
                description="Target column has zero variance (constant values). Forecasting is trivial or invalid.",
                recommendation="Select a target with meaningful variance.",
            )
        )

    if target_missing > 0:
        issues.append(
            ForecastQualityIssue(
                issue_id="QI_TARGET_MISSING",
                issue_type="TARGET_MISSING",
                severity=QualitySeverity.MEDIUM,
                description=f"Target column contains {target_missing} null values.",
                affected_rows=target_missing,
                recommendation="Missing target values should be linearly interpolated or handled explicitly.",
            )
        )

    # 5. Missing timestamps gap analysis
    min_ts = valid_ts.min()
    max_ts = valid_ts.max()

    expected_count = len(valid_ts)
    missing_ts_count = 0
    try:
        full_range = pd.date_range(start=min_ts, end=max_ts, freq=pandas_freq)
        expected_count = len(full_range)
        missing_ts_count = max(0, expected_count - len(valid_ts.drop_duplicates()))
        if missing_ts_count > 0:
            issues.append(
                ForecastQualityIssue(
                    issue_id="QI_MISSING_TIMESTAMPS",
                    issue_type="MISSING_TIMESTAMPS",
                    severity=QualitySeverity.MEDIUM if missing_ts_count / expected_count < 0.2 else QualitySeverity.HIGH,
                    description=f"Expected {expected_count} observations for inferred frequency {inferred_freq.value}, but found {len(valid_ts)}. {missing_ts_count} timestamps are missing.",
                    affected_rows=missing_ts_count,
                    recommendation="Resample time series to complete regular grid.",
                )
            )
    except Exception:
        pass

    has_critical = any(issue.severity == QualitySeverity.CRITICAL for issue in issues)

    return TemporalValidationReport(
        is_valid=not has_critical,
        time_column=time_column,
        target_column=target_column,
        inferred_frequency=inferred_freq,
        pandas_frequency_str=pandas_freq,
        regularity=regularity,
        confidence=confidence,
        observation_count=len(valid_ts),
        expected_observation_count=expected_count,
        missing_timestamp_count=missing_ts_count,
        duplicate_timestamp_count=duplicate_count,
        min_timestamp=str(min_ts),
        max_timestamp=str(max_ts),
        target_missing_count=target_missing,
        target_zero_count=target_zeros,
        target_mean=round(t_mean, 4),
        target_variance=round(t_var, 4),
        issues=issues,
        warnings=warnings,
    )
