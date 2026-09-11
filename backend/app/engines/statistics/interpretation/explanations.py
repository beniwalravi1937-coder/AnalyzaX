"""
AnalyzaX — Phase 10: Statistical Interpretation & Narrative Engine
Generates rigorous, human-interpretable statistical summaries without an LLM.
Strictly adheres to causality safety (STAT-43) and proper p-value interpretation (STAT-14, STAT-41).
"""

from typing import Any, Dict, List, Optional


def generate_structured_interpretation(
    analysis_type: str,
    method: str,
    method_name: str,
    target_columns: List[str],
    group_columns: List[str],
    statistics: Dict[str, Any],
    p_values: Dict[str, Optional[float]],
    effect_sizes: List[Dict[str, Any]],
    assumptions_summary: List[Dict[str, Any]],
    missing_data: Dict[str, Any],
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Generates deterministic, structured plain-language explanations answering the 7 core analytical questions.
    """
    primary_p = p_values.get("primary") or statistics.get("p_value") or statistics.get("f_p_value")
    test_stat = statistics.get("statistic")
    stat_name = statistics.get("test_statistic_name", "test statistic")
    sample_size = missing_data.get("used_observations", 0)
    excluded = missing_data.get("excluded_observations", 0)

    # 1. What was tested?
    null_hyp = statistics.get("null_hypothesis", "No null hypothesis specified.")
    alt_hyp = statistics.get("alternative_hypothesis", "No alternative hypothesis specified.")
    what_was_tested = (
        f"A hypothesis test was conducted on '{', '.join(target_columns)}' "
        f"{f'grouped by {group_columns[0]}' if group_columns else ''}. "
        f"Null hypothesis: {null_hyp}"
    )

    # 2. Which method was used and why?
    why_method = (
        f"Analysis executed using {method_name}. "
        "This method was deterministically selected based on variable types, group design, and distributional characteristics."
    )

    # 3. What was observed?
    if primary_p is not None:
        p_str = f"p = {round(primary_p, 4)}" if primary_p >= 0.0001 else "p < 0.0001"
        if primary_p < alpha:
            evidence_summary = (
                f"Statistically significant evidence against the null hypothesis was observed ({stat_name} = {test_stat}, {p_str}, alpha = {alpha}). "
                f"Under the assumption that the null hypothesis were true, the probability of observing a result as extreme as or more extreme than this is {p_str}."
            )
            evidence_strength = "Strong" if primary_p < 0.01 else "Moderate"
        else:
            evidence_summary = (
                f"The observed data did not reach statistical significance at the alpha = {alpha} threshold ({stat_name} = {test_stat}, {p_str}). "
                "The observed differences or associations could plausibly have occurred by chance alone under the null hypothesis."
            )
            evidence_strength = "Weak / Inconclusive"
    else:
        evidence_summary = f"Summary statistics computed across {sample_size} valid observations."
        evidence_strength = "Descriptive"

    # 4. How large is the effect?
    effect_magnitude_text = "No standardized effect size was computed for this analysis."
    if effect_sizes:
        eff = effect_sizes[0]
        val = eff.get("value")
        metric = eff.get("metric_name", "effect")
        interp = eff.get("interpretation", "unclassified")
        effect_magnitude_text = (
            f"The estimated effect size is {metric} = {val}, which is classified as {interp} practical magnitude. "
            "Practical importance should be evaluated in domain context alongside statistical significance."
        )

    # 5. What assumptions matter?
    violated = [a for a in assumptions_summary if a.get("status") in ("VIOLATION", "WARNING")]
    if violated:
        assumptions_text = (
            f"{len(violated)} potential assumption concern(s) were flagged: "
            + "; ".join(f"{a.get('assumption')}: {a.get('evidence')}" for a in violated[:2])
            + ". Review diagnostic charts before drawing firm conclusions."
        )
    else:
        assumptions_text = "Key test assumptions (distribution, variance, sample adequacy) appear reasonably satisfied based on diagnostics."

    # 6. Limitations & Causality Safety (STAT-43)
    limitations = [
        "Observational Association: This analysis measures statistical association and correlation. It does not establish causal direction or prove that changes in one variable cause changes in another.",
        f"Data Completeness: {excluded} observations were excluded from analysis due to missing or non-finite values.",
        "Generalizability: Findings apply to the sampled population and specific dataset version analyzed.",
    ]
    if "ols" in method:
        limitations.append("Model Specificity: Linear regression assumes a linear functional form and additive predictor relationships.")

    return {
        "what_was_tested": what_was_tested,
        "method_used": why_method,
        "observed_summary": evidence_summary,
        "evidence_strength": evidence_strength,
        "effect_magnitude": effect_magnitude_text,
        "assumptions_impact": assumptions_text,
        "causality_caveat": (
            "Caution: Observational data indicates association, not causation. "
            "Do not infer that independent variables directly cause changes in outcomes without randomized experimental design."
        ),
        "limitations": limitations,
    }
