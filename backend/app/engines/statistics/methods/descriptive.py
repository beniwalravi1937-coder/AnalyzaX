"""
AnalyzaX — Phase 10: Deterministic Descriptive Statistics
Computes comprehensive univariate statistics for numeric, categorical, boolean, and datetime variables.
All calculations are deterministic using NumPy, SciPy, and Polars.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import polars as pl
from scipy import stats

from backend.app.engines.statistics.models import ConfidenceInterval, MissingDataReport


def compute_numeric_descriptive(
    values: np.ndarray,
    column_name: str,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """
    Computes rigorous numeric descriptive metrics.
    Satisfies STAT-06, STAT-10, STAT-11.
    """
    total_count = len(values)
    valid_mask = ~np.isnan(values) & ~np.isinf(values)
    clean = values[valid_mask].astype(float)
    used_count = len(clean)
    missing_count = total_count - used_count
    missing_pct = round((missing_count / total_count * 100.0), 2) if total_count > 0 else 0.0

    missing_report = MissingDataReport(
        original_observations=total_count,
        used_observations=used_count,
        excluded_observations=missing_count,
        missing_policy="listwise_deletion",
        exclusion_reason="NaN or Infinite values excluded" if missing_count > 0 else None,
    )

    if used_count == 0:
        return {
            "column": column_name,
            "data_type": "numeric",
            "missing_report": missing_report.model_dump(),
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "variance": None,
            "min": None,
            "max": None,
            "range": None,
            "iqr": None,
            "skewness": None,
            "kurtosis": None,
            "confidence_interval_mean": None,
        }

    mean_val = float(np.mean(clean))
    median_val = float(np.median(clean))
    min_val = float(np.min(clean))
    max_val = float(np.max(clean))
    range_val = float(max_val - min_val)

    if used_count > 1:
        variance_val = float(np.var(clean, ddof=1))
        std_val = float(np.std(clean, ddof=1))
        se_val = float(std_val / math.sqrt(used_count))
    else:
        variance_val = 0.0
        std_val = 0.0
        se_val = 0.0

    # Coefficient of variation (CV = std / mean)
    cv_val = None
    if std_val > 0 and abs(mean_val) > 1e-9:
        cv_val = round(float(std_val / abs(mean_val)), 4)

    # Quantiles & Percentiles
    quantiles_to_calc = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    percentiles_res = np.percentile(clean, quantiles_to_calc)
    pct_map = {f"p{q:02d}": round(float(val), 4) for q, val in zip(quantiles_to_calc, percentiles_res)}
    q25 = float(percentiles_res[3])
    q75 = float(percentiles_res[5])
    iqr_val = float(q75 - q25)

    # Median Absolute Deviation (MAD)
    mad_val = float(np.median(np.abs(clean - median_val)))

    # Mode where meaningful
    try:
        mode_res = stats.mode(clean, keepdims=False)
        mode_val = float(mode_res.mode) if used_count > 0 else None
    except Exception:
        mode_val = None

    # Skewness and Kurtosis
    skew_val = None
    kurt_val = None
    if used_count >= 3 and std_val > 1e-9:
        try:
            sk = stats.skew(clean, bias=False)
            if not (math.isnan(sk) or math.isinf(sk)):
                skew_val = round(float(sk), 4)
        except Exception:
            skew_val = None

    if used_count >= 4 and std_val > 1e-9:
        try:
            kt = stats.kurtosis(clean, bias=False, fisher=True)
            if not (math.isnan(kt) or math.isinf(kt)):
                kurt_val = round(float(kt), 4)
        except Exception:
            kurt_val = None

    # Confidence Interval for the mean using Student-t distribution
    ci_mean = None
    if used_count >= 2 and std_val > 0:
        alpha = 1.0 - confidence_level
        df = used_count - 1
        t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
        margin = t_crit * se_val
        ci_mean = ConfidenceInterval(
            level=confidence_level,
            lower=round(mean_val - margin, 4),
            upper=round(mean_val + margin, 4),
            metric_name="mean",
            standard_error=round(se_val, 4),
            margin_of_error=round(margin, 4),
        ).model_dump()

    return {
        "column": column_name,
        "data_type": "numeric",
        "missing_report": missing_report.model_dump(),
        "count": used_count,
        "missing_count": missing_count,
        "missing_percentage": missing_pct,
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "mode": round(mode_val, 4) if mode_val is not None else None,
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "range": round(range_val, 4),
        "variance": round(variance_val, 4),
        "std": round(std_val, 4),
        "cv": cv_val,
        "se": round(se_val, 4),
        "q25": round(q25, 4),
        "q75": round(q75, 4),
        "iqr": round(iqr_val, 4),
        "mad": round(mad_val, 4),
        "skewness": skew_val,
        "kurtosis": kurt_val,
        "percentiles": pct_map,
        "confidence_interval_mean": ci_mean,
    }


def compute_categorical_descriptive(
    series: pl.Series,
    column_name: str,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Computes categorical descriptive metrics.
    Satisfies STAT-07, STAT-10.
    """
    total_count = len(series)
    null_count = series.null_count()
    clean_series = series.drop_nulls()
    used_count = len(clean_series)
    missing_pct = round((null_count / total_count * 100.0), 2) if total_count > 0 else 0.0

    missing_report = MissingDataReport(
        original_observations=total_count,
        used_observations=used_count,
        excluded_observations=null_count,
        missing_policy="listwise_deletion",
        exclusion_reason="Null categorical values excluded" if null_count > 0 else None,
    )

    if used_count == 0:
        return {
            "column": column_name,
            "data_type": "categorical",
            "missing_report": missing_report.model_dump(),
            "count": 0,
            "unique_count": 0,
            "cardinality": 0.0,
            "frequencies": {},
            "top_categories": [],
            "rare_categories": [],
        }

    # Frequencies and proportions
    val_counts = clean_series.value_counts(sort=True)
    categories = val_counts[val_counts.columns[0]].to_list()
    counts = val_counts["count"].to_list()

    freq_map = {}
    prop_map = {}
    top_cats = []
    rare_cats = []
    threshold_rare = 0.01 * used_count  # Categories < 1% of total

    for cat, cnt in zip(categories, counts):
        cat_str = str(cat) if cat is not None else "(null)"
        prop = round(cnt / used_count, 4)
        freq_map[cat_str] = cnt
        prop_map[cat_str] = prop

        if len(top_cats) < top_n:
            top_cats.append({"category": cat_str, "count": cnt, "proportion": prop})
        if cnt <= threshold_rare:
            rare_cats.append({"category": cat_str, "count": cnt, "proportion": prop})

    unique_count = len(categories)
    cardinality = round(unique_count / used_count, 4)

    return {
        "column": column_name,
        "data_type": "categorical",
        "missing_report": missing_report.model_dump(),
        "count": used_count,
        "missing_count": null_count,
        "missing_percentage": missing_pct,
        "unique_count": unique_count,
        "cardinality": cardinality,
        "frequencies": freq_map,
        "proportions": prop_map,
        "top_categories": top_cats,
        "rare_categories": rare_cats[:10],
    }


def compute_boolean_descriptive(
    series: pl.Series,
    column_name: str,
) -> Dict[str, Any]:
    """
    Computes boolean descriptive metrics.
    Satisfies STAT-08, STAT-10.
    """
    total_count = len(series)
    null_count = series.null_count()
    clean = series.drop_nulls()
    used_count = len(clean)

    missing_report = MissingDataReport(
        original_observations=total_count,
        used_observations=used_count,
        excluded_observations=null_count,
        missing_policy="listwise_deletion",
        exclusion_reason="Null boolean values excluded" if null_count > 0 else None,
    )

    if used_count == 0:
        return {
            "column": column_name,
            "data_type": "boolean",
            "missing_report": missing_report.model_dump(),
            "count": 0,
            "true_count": 0,
            "false_count": 0,
            "true_percentage": 0.0,
            "false_percentage": 0.0,
        }

    bool_vals = clean.cast(pl.Boolean).to_list()
    true_count = sum(1 for v in bool_vals if v is True)
    false_count = used_count - true_count
    true_pct = round(true_count / used_count * 100.0, 2)
    false_pct = round(false_count / used_count * 100.0, 2)

    return {
        "column": column_name,
        "data_type": "boolean",
        "missing_report": missing_report.model_dump(),
        "count": used_count,
        "missing_count": null_count,
        "missing_percentage": round(null_count / total_count * 100.0, 2) if total_count > 0 else 0.0,
        "true_count": true_count,
        "false_count": false_count,
        "true_percentage": true_pct,
        "false_percentage": false_pct,
    }


def compute_datetime_descriptive(
    series: pl.Series,
    column_name: str,
) -> Dict[str, Any]:
    """
    Computes datetime descriptive metrics.
    Satisfies STAT-09, STAT-10.
    """
    total_count = len(series)
    null_count = series.null_count()
    clean = series.drop_nulls()
    used_count = len(clean)

    missing_report = MissingDataReport(
        original_observations=total_count,
        used_observations=used_count,
        excluded_observations=null_count,
        missing_policy="listwise_deletion",
        exclusion_reason="Null datetime values excluded" if null_count > 0 else None,
    )

    if used_count == 0:
        return {
            "column": column_name,
            "data_type": "datetime",
            "missing_report": missing_report.model_dump(),
            "count": 0,
            "min": None,
            "max": None,
            "span_days": None,
            "unique_periods": 0,
            "inferred_granularity": None,
        }

    try:
        if clean.dtype in (pl.String, pl.Utf8):
            try:
                dt_series = clean.str.to_datetime()
            except Exception:
                dt_series = clean.str.to_date().cast(pl.Datetime)
        else:
            dt_series = clean.cast(pl.Datetime)

        min_dt = dt_series.min()
        max_dt = dt_series.max()
        unique_periods = dt_series.n_unique()

        span_days = None
        if min_dt is not None and max_dt is not None:
            delta = max_dt - min_dt
            span_days = delta.days if hasattr(delta, "days") else None

        # Infer granularity
        granularity = "daily"
        if span_days is not None:
            if span_days < 2:
                granularity = "hourly"
            elif span_days > 730:
                granularity = "yearly"
            elif span_days > 60:
                granularity = "monthly"

        return {
            "column": column_name,
            "data_type": "datetime",
            "missing_report": missing_report.model_dump(),
            "count": used_count,
            "missing_count": null_count,
            "missing_percentage": round(null_count / total_count * 100.0, 2) if total_count > 0 else 0.0,
            "min": str(min_dt),
            "max": str(max_dt),
            "span_days": span_days,
            "unique_periods": unique_periods,
            "inferred_granularity": granularity,
        }
    except Exception:
        return {
            "column": column_name,
            "data_type": "datetime",
            "missing_report": missing_report.model_dump(),
            "count": used_count,
            "min": None,
            "max": None,
            "span_days": None,
            "unique_periods": 0,
            "inferred_granularity": None,
        }
