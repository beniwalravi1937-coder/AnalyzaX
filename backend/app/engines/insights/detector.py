"""
AnalyzaX — Phase 25: Proactive Insight Signal Detector.
Coordinates deterministic discovery of anomalies, quality degradation,
correlations, segment differences, and trend breaks across existing engines.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.core.logging import logger
from backend.app.engines.insights.models import (
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    Insight,
    InsightConfidence,
    InsightEvidence,
    InsightSeverity,
    InsightType,
    RecommendedAction,
)


class InsightSignalDetector:
    """Discovers measurable analytical signals from deterministic domain engines."""

    @classmethod
    def detect_signals_from_context(
        cls,
        workspace_id: str,
        dataset_id: str,
        version_id: str,
        project_id: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        quality_data: Optional[Dict[str, Any]] = None,
        eda_data: Optional[Dict[str, Any]] = None,
        stats_data: Optional[Dict[str, Any]] = None,
    ) -> List[Insight]:
        """
        Scans structured outputs from Profiling, Quality, EDA, and Statistics engines
        to generate candidate Insight objects with concrete evidence graphs.
        """
        insights: List[Insight] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # ─────────────────────────────────────────────────────────────
        # 1. Quality Signals (Anomalies, High Missingness, Duplicates)
        # ─────────────────────────────────────────────────────────────
        if quality_data:
            score = quality_data.get("score") or quality_data.get("quality_score") or 100.0
            if score < 75.0:
                ins_id = f"ins_{uuid4().hex[:8]}"
                ev_id = f"ev_{uuid4().hex[:8]}"
                evidence = InsightEvidence(
                    evidence_id=ev_id,
                    evidence_type="quality_metric",
                    description=f"Overall data quality score is degraded at {score:.1f}/100.",
                    metrics={"quality_score": score},
                    created_at=now_iso,
                )
                graph = EvidenceGraph(
                    nodes=[
                        EvidenceGraphNode(id=ins_id, label="Degraded Data Quality", node_type="insight"),
                        EvidenceGraphNode(id=ev_id, label="Quality Evaluation", node_type="quality_metric", properties={"score": score}),
                        EvidenceGraphNode(id=f"ds_{version_id}", label=f"Dataset {version_id}", node_type="dataset_version"),
                    ],
                    edges=[
                        EvidenceGraphEdge(source=ins_id, target=ev_id, relation="GROUNDED_BY"),
                        EvidenceGraphEdge(source=ev_id, target=f"ds_{version_id}", relation="DERIVED_FROM"),
                    ],
                )
                insights.append(
                    Insight(
                        insight_id=ins_id,
                        workspace_id=workspace_id,
                        project_id=project_id,
                        dataset_id=dataset_id,
                        dataset_version_id=version_id,
                        insight_type=InsightType.DATA_QUALITY,
                        title="Substantial Data Quality Degradation",
                        summary=f"Dataset version {version_id} exhibits a low overall quality score of {score:.1f}/100, impacting downstream modeling reliability.",
                        severity=InsightSeverity.MEDIUM if score >= 50 else InsightSeverity.CRITICAL,
                        importance_score=round(100.0 - score, 2),
                        confidence=InsightConfidence.HIGH,
                        evidence=[evidence],
                        evidence_graph=graph,
                        recommended_actions=[
                            RecommendedAction(
                                action_id=f"act_{uuid4().hex[:6]}",
                                title="Inspect Quality Scorecard",
                                description="Review dimension violations and outlier clusters.",
                                action_type="inspect_quality",
                                tool_id="get_quality_report",
                                parameters={"dataset_id": dataset_id},
                            ),
                            RecommendedAction(
                                action_id=f"act_{uuid4().hex[:6]}",
                                title="Propose Cleaning Plan",
                                description="Generate automated non-destructive cleaning transformations.",
                                action_type="propose_cleaning",
                                tool_id="propose_cleaning",
                                parameters={"dataset_id": dataset_id},
                            ),
                        ],
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                )

        # ─────────────────────────────────────────────────────────────
        # 2. Profiling Signals (High Missing Rates, High Skewness)
        # ─────────────────────────────────────────────────────────────
        if profile_data:
            col_profiles = profile_data.get("columns") or profile_data.get("column_profiles") or {}
            if isinstance(col_profiles, list):
                col_profiles = {c.get("name", f"col_{i}"): c for i, c in enumerate(col_profiles)}

            for col_name, col_info in col_profiles.items():
                missing_pct = col_info.get("missing_percentage") or col_info.get("missing_rate", 0) * 100
                if missing_pct >= 25.0:
                    ins_id = f"ins_{uuid4().hex[:8]}"
                    ev_id = f"ev_{uuid4().hex[:8]}"
                    evidence = InsightEvidence(
                        evidence_id=ev_id,
                        evidence_type="profile",
                        description=f"Column '{col_name}' has {missing_pct:.1f}% missing values.",
                        metrics={"column": col_name, "missing_pct": missing_pct},
                        created_at=now_iso,
                    )
                    insights.append(
                        Insight(
                            insight_id=ins_id,
                            workspace_id=workspace_id,
                            project_id=project_id,
                            dataset_id=dataset_id,
                            dataset_version_id=version_id,
                            insight_type=InsightType.DATA_QUALITY,
                            title=f"Severe Missingness in '{col_name}'",
                            summary=f"Column '{col_name}' is missing {missing_pct:.1f}% of its values, which may distort descriptive statistics.",
                            severity=InsightSeverity.WARNING,
                            importance_score=round(min(90.0, missing_pct * 1.5), 2),
                            confidence=InsightConfidence.HIGH,
                            affected_columns=[col_name],
                            evidence=[evidence],
                            recommended_actions=[
                                RecommendedAction(
                                    action_id=f"act_{uuid4().hex[:6]}",
                                    title=f"Impute or Filter '{col_name}'",
                                    description="Review imputation or filtering strategies.",
                                    action_type="propose_cleaning",
                                    tool_id="propose_cleaning",
                                    parameters={"dataset_id": dataset_id, "columns": [col_name]},
                                )
                            ],
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                    )

        # ─────────────────────────────────────────────────────────────
        # 3. EDA & Correlation Signals (Strong Associations & Outliers)
        # ─────────────────────────────────────────────────────────────
        if eda_data:
            correlations = eda_data.get("correlations") or []
            for corr in correlations:
                col_a = corr.get("column_a") or corr.get("col1")
                col_b = corr.get("column_b") or corr.get("col2")
                val = abs(corr.get("correlation", 0.0) or corr.get("r_value", 0.0))
                if val >= 0.70 and col_a and col_b:
                    ins_id = f"ins_{uuid4().hex[:8]}"
                    ev_id = f"ev_{uuid4().hex[:8]}"
                    evidence = InsightEvidence(
                        evidence_id=ev_id,
                        evidence_type="eda_correlation",
                        description=f"Strong linear correlation (|r| = {val:.2f}) observed between '{col_a}' and '{col_b}'.",
                        metrics={"column_a": col_a, "column_b": col_b, "correlation": val},
                        created_at=now_iso,
                    )
                    insights.append(
                        Insight(
                            insight_id=ins_id,
                            workspace_id=workspace_id,
                            project_id=project_id,
                            dataset_id=dataset_id,
                            dataset_version_id=version_id,
                            insight_type=InsightType.CORRELATION,
                            title=f"Strong Correlation: '{col_a}' & '{col_b}'",
                            summary=f"A high correlation coefficient of {val:.2f} exists between '{col_a}' and '{col_b}', indicating a potential collinear relationship.",
                            severity=InsightSeverity.INFO,
                            importance_score=round(val * 85.0, 2),
                            confidence=InsightConfidence.HIGH,
                            affected_columns=[col_a, col_b],
                            evidence=[evidence],
                            recommended_actions=[
                                RecommendedAction(
                                    action_id=f"act_{uuid4().hex[:6]}",
                                    title=f"Plot Scatter: {col_a} vs {col_b}",
                                    description="Visualize relationship and detect potential outliers.",
                                    action_type="create_chart",
                                    tool_id="create_visualization",
                                    parameters={"x_column": col_a, "y_column": col_b, "chart_type": "scatter"},
                                )
                            ],
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                    )

            outliers = eda_data.get("outliers") or []
            for out in outliers:
                col = out.get("column") or out.get("col")
                cnt = out.get("outlier_count", 0)
                pct = out.get("percentage", 0.0)
                if col and (cnt > 0 or pct > 0):
                    ins_id = f"ins_{uuid4().hex[:8]}"
                    ev_id = f"ev_{uuid4().hex[:8]}"
                    evidence = InsightEvidence(
                        evidence_id=ev_id,
                        evidence_type="eda_outlier",
                        description=f"Column '{col}' exhibits {cnt} extreme outliers ({pct:.1f}% of total).",
                        metrics={"column": col, "outlier_count": cnt, "percentage": pct},
                        created_at=now_iso,
                    )
                    insights.append(
                        Insight(
                            insight_id=ins_id,
                            workspace_id=workspace_id,
                            project_id=project_id,
                            dataset_id=dataset_id,
                            dataset_version_id=version_id,
                            insight_type=InsightType.ANOMALY,
                            title=f"Distribution Outliers in '{col}'",
                            summary=f"Detected {cnt} potential anomaly points in column '{col}' ({pct:.1f}%).",
                            severity=InsightSeverity.MEDIUM if pct < 5.0 else InsightSeverity.HIGH,
                            importance_score=round(min(80.0, max(20.0, pct * 15.0)), 2),
                            confidence=InsightConfidence.HIGH,
                            affected_columns=[col],
                            evidence=[evidence],
                            recommended_actions=[
                                RecommendedAction(
                                    action_id=f"act_{uuid4().hex[:6]}",
                                    title=f"Inspect Outliers in {col}",
                                    description="Examine boxplots and extreme quantiles.",
                                    action_type="create_chart",
                                    tool_id="create_visualization",
                                    parameters={"column": col, "chart_type": "boxplot"},
                                )
                            ],
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                    )

        # ─────────────────────────────────────────────────────────────
        # 4. Statistical Test Signals (Significant Differences)
        # ─────────────────────────────────────────────────────────────
        if stats_data:
            p_val = stats_data.get("p_value")
            test_name = stats_data.get("test_name", "Hypothesis Test")
            if p_val is not None and p_val < 0.05:
                ins_id = f"ins_{uuid4().hex[:8]}"
                ev_id = f"ev_{uuid4().hex[:8]}"
                evidence = InsightEvidence(
                    evidence_id=ev_id,
                    evidence_type="statistical_test",
                    description=f"{test_name} rejected the null hypothesis with p = {p_val:.4f}.",
                    metrics={"p_value": p_val, "test_name": test_name},
                    created_at=now_iso,
                )
                insights.append(
                    Insight(
                        insight_id=ins_id,
                        workspace_id=workspace_id,
                        project_id=project_id,
                        dataset_id=dataset_id,
                        dataset_version_id=version_id,
                        insight_type=InsightType.STATISTICAL_SIGNAL,
                        title=f"Statistically Significant Difference ({test_name})",
                        summary=f"Rigorous hypothesis testing confirms a statistically significant difference (p = {p_val:.4f} < 0.05).",
                        severity=InsightSeverity.INFO if p_val > 0.01 else InsightSeverity.WARNING,
                        importance_score=round(min(95.0, (1.0 - p_val) * 90.0), 2),
                        confidence=InsightConfidence.HIGH,
                        evidence=[evidence],
                        recommended_actions=[
                            RecommendedAction(
                                action_id=f"act_{uuid4().hex[:6]}",
                                title="Synthesize Findings",
                                description="Generate an analytical narrative explaining the statistical implications.",
                                action_type="generate_narrative",
                                tool_id="generate_narrative",
                                parameters={"test_name": test_name, "p_value": p_val},
                            )
                        ],
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                )

        return insights

    detect_insights = detect_signals_from_context


ProactiveInsightDetector = InsightSignalDetector
