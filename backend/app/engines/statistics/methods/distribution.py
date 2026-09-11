"""
AnalyzaX — Phase 10: Distribution Analysis & Outlier Diagnostics
Computes deterministic histogram bins, ECDF, quantiles, and IQR outlier boundaries.
Does NOT modify or remove outliers from the dataset (STAT-30, STAT-39).
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from backend.app.engines.statistics.models import MissingDataReport


def compute_distribution_analysis(
    values: np.ndarray,
    column_name: str,
    max_bins: int = 30,
) -> Dict[str, Any]:
    """
    Analyzes numerical distributions deterministically.
    Satisfies STAT-09, STAT-30, STAT-36.
    """
    total_count = len(values)
    valid_mask = ~np.isnan(values) & ~np.isinf(values)
    clean = values[valid_mask].astype(float)
    used_count = len(clean)
    missing_count = total_count - used_count

    missing_report = MissingDataReport(
        original_observations=total_count,
        used_observations=used_count,
        excluded_observations=missing_count,
        missing_policy="listwise_deletion",
        exclusion_reason="Non-finite values excluded" if missing_count > 0 else None,
    )

    if used_count < 3:
        return {
            "column": column_name,
            "count": used_count,
            "missing_report": missing_report.model_dump(),
            "status": "INSUFFICIENT_DATA",
            "histogram_bins": [],
            "ecdf": [],
            "outliers": {"mild_count": 0, "extreme_count": 0, "mild_bounds": [0, 0], "extreme_bounds": [0, 0]},
        }

    min_val = float(np.min(clean))
    max_val = float(np.max(clean))
    mean_val = float(np.mean(clean))
    std_val = float(np.std(clean, ddof=1)) if used_count > 1 else 0.0

    # 1. Histogram binning: Freedman-Diaconis with Sturges fallback
    q75, q25 = np.percentile(clean, [75, 25])
    iqr = float(q75 - q25)
    bin_method = "freedman_diaconis"

    if iqr > 0:
        bin_width = 2.0 * iqr * (used_count ** (-1.0 / 3.0))
        calculated_bins = int(math.ceil((max_val - min_val) / max(bin_width, 1e-6)))
    else:
        bin_method = "sturges"
        calculated_bins = int(math.ceil(math.log2(used_count) + 1))

    bin_count = max(5, min(max_bins, calculated_bins))
    if math.isclose(min_val, max_val):
        bin_count = 1

    counts, bin_edges = np.histogram(clean, bins=bin_count)
    bins_data = []
    total_f = float(used_count)
    for i in range(len(counts)):
        b_start = float(bin_edges[i])
        b_end = float(bin_edges[i + 1])
        c = int(counts[i])
        mid_point = round((b_start + b_end) / 2.0, 4)
        normal_pdf_val = 0.0
        if std_val > 1e-9:
            normal_pdf_val = float(stats.norm.pdf(mid_point, loc=mean_val, scale=std_val) * (b_end - b_start) * total_f)

        bins_data.append({
            "bin_start": round(b_start, 4),
            "bin_end": round(b_end, 4),
            "mid_point": mid_point,
            "count": c,
            "percentage": round(c / total_f * 100.0, 2),
            "expected_normal_count": round(normal_pdf_val, 2),
        })

    # 2. Empirical Cumulative Distribution Function (ECDF) - Sampled down to at most 100 points
    sorted_vals = np.sort(clean)
    step = max(1, used_count // 100)
    sampled_indices = list(range(0, used_count, step))
    if (used_count - 1) not in sampled_indices:
        sampled_indices.append(used_count - 1)

    ecdf_data = []
    for idx in sampled_indices:
        val = float(sorted_vals[idx])
        cum_prob = round((idx + 1) / total_f, 4)
        ecdf_data.append({"value": round(val, 4), "cumulative_probability": cum_prob})

    # 3. Outlier Indicators using Tukey's fences (1.5 * IQR and 3.0 * IQR)
    mild_lower = q25 - 1.5 * iqr
    mild_upper = q75 + 1.5 * iqr
    extreme_lower = q25 - 3.0 * iqr
    extreme_upper = q75 + 3.0 * iqr

    mild_outliers = clean[(clean < mild_lower) | (clean > mild_upper)]
    extreme_outliers = clean[(clean < extreme_lower) | (clean > extreme_upper)]

    outlier_info = {
        "q25": round(float(q25), 4),
        "q75": round(float(q75), 4),
        "iqr": round(float(iqr), 4),
        "mild_bounds": [round(float(mild_lower), 4), round(float(mild_upper), 4)],
        "extreme_bounds": [round(float(extreme_lower), 4), round(float(extreme_upper), 4)],
        "mild_outlier_count": len(mild_outliers),
        "mild_outlier_percentage": round(len(mild_outliers) / total_f * 100.0, 2),
        "extreme_outlier_count": len(extreme_outliers),
        "extreme_outlier_percentage": round(len(extreme_outliers) / total_f * 100.0, 2),
        "has_outliers": len(mild_outliers) > 0,
        "sample_outlier_values": [round(float(v), 4) for v in mild_outliers[:10]],
    }

    # 4. Q-Q Plot Coordinates (Theoretical standard normal quantiles vs standardized sample quantiles)
    qq_points = []
    if used_count >= 5 and std_val > 1e-9:
        qq_sample_size = min(100, used_count)
        quantiles_probs = np.linspace(0.01, 0.99, qq_sample_size)
        theoretical_quantiles = stats.norm.ppf(quantiles_probs)
        sample_quantiles = np.percentile(clean, quantiles_probs * 100.0)
        standardized_sample = (sample_quantiles - mean_val) / std_val

        for t_q, s_q in zip(theoretical_quantiles, standardized_sample):
            qq_points.append({
                "theoretical": round(float(t_q), 4),
                "observed": round(float(s_q), 4),
            })

    return {
        "column": column_name,
        "count": used_count,
        "missing_report": missing_report.model_dump(),
        "bin_method": bin_method,
        "bin_count": bin_count,
        "histogram_bins": bins_data,
        "ecdf": ecdf_data,
        "outliers": outlier_info,
        "qq_points": qq_points,
    }
