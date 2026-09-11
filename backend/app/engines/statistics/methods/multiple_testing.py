"""
AnalyzaX — Phase 10: Multiple Testing Correction Engine
Provides Bonferroni, Holm, and Benjamini-Hochberg (FDR) corrections (STAT-15).
"""

from typing import Any, Dict, List, Tuple
import numpy as np


def adjust_p_values(
    p_values: List[float],
    method: str = "fdr_bh",
    alpha: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Applies multiple-comparison corrections to a list of p-values.
    Methods:
      - 'bonferroni': Single-step family-wise error rate control
      - 'holm': Step-down sequentially rejective procedure
      - 'fdr_bh': Benjamini-Hochberg False Discovery Rate control
      - 'none': Unadjusted raw p-values
    """
    m = len(p_values)
    if m == 0:
        return []

    method_clean = method.lower().strip()
    if method_clean in ("none", "raw") or m == 1:
        return [
            {
                "index": i,
                "raw_p_value": round(p, 6),
                "adjusted_p_value": round(p, 6),
                "rejected": bool(p < alpha),
                "method": "none",
                "comparisons": m,
            }
            for i, p in enumerate(p_values)
        ]

    # Convert to indexed array
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m

    if method_clean == "bonferroni":
        for idx, (orig_idx, p_val) in enumerate(indexed):
            adj_p = min(1.0, p_val * m)
            adjusted[orig_idx] = adj_p

    elif method_clean == "holm":
        # Step-down: p_(i) * (m - i + 1)
        running_max = 0.0
        for rank, (orig_idx, p_val) in enumerate(indexed):
            multiplier = m - rank
            val = p_val * multiplier
            running_max = max(running_max, val)
            adjusted[orig_idx] = min(1.0, running_max)

    elif method_clean in ("fdr_bh", "benjamini_hochberg", "fdr"):
        # Step-up: p_(i) * m / (rank + 1)
        # Traversed in reverse order to ensure monotonicity
        running_min = 1.0
        for rank in range(m - 1, -1, -1):
            orig_idx, p_val = indexed[rank]
            val = (p_val * m) / (rank + 1)
            running_min = min(running_min, val)
            adjusted[orig_idx] = min(1.0, running_min)

    else:
        # Fallback to unadjusted
        return adjust_p_values(p_values, method="none", alpha=alpha)

    results = []
    for i, p_val in enumerate(p_values):
        adj_p = adjusted[i]
        results.append({
            "index": i,
            "raw_p_value": round(p_val, 6),
            "adjusted_p_value": round(adj_p, 6),
            "rejected": bool(adj_p < alpha),
            "method": method_clean,
            "comparisons": m,
        })

    return results
