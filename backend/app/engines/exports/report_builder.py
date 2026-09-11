"""
Report Builder for Phase 15 Export Engine.
Composes ReportDefinition from templates by reading existing analytical results.
Never recomputes — assembles sections from persisted, deterministic results.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.exports.models import (
    ExportProvenance,
    ReportDefinition,
    ReportSection,
    ReportSectionType,
    ReportTemplate,
)
from backend.app.engines.exports.source_reader import (
    BaseSourceReader,
    EdaSourceReader,
    ForecastSourceReader,
    MlSourceReader,
    ProfileSourceReader,
    QualitySourceReader,
    StatisticsSourceReader,
)


class ReportBuilder:
    """
    Composes ReportDefinition from templates by assembling
    sections from existing analytical engine outputs.
    """

    TEMPLATE_METADATA = {
        ReportTemplate.EXECUTIVE_SUMMARY: {
            "name": "Executive Summary",
            "description": "High-level overview with key metrics, quality score, and top findings.",
            "sections": ["profile_overview", "quality_summary", "top_eda_findings"],
        },
        ReportTemplate.DATA_QUALITY: {
            "name": "Data Quality Report",
            "description": "Comprehensive quality assessment with all issues and recommendations.",
            "sections": ["profile_overview", "quality_full"],
        },
        ReportTemplate.EDA_DEEP_DIVE: {
            "name": "EDA Deep Dive",
            "description": "All exploratory data analysis findings organized by category.",
            "sections": ["profile_overview", "eda_full"],
        },
        ReportTemplate.ML_EXPERIMENT: {
            "name": "ML Experiment Report",
            "description": "Machine learning experiment results with metrics and feature importance.",
            "sections": ["profile_overview", "ml_full"],
        },
        ReportTemplate.FORECAST_BRIEF: {
            "name": "Forecast Brief",
            "description": "Time-series forecasting results with horizons and backtest metrics.",
            "sections": ["profile_overview", "forecast_full"],
        },
        ReportTemplate.FULL_ANALYSIS: {
            "name": "Full Analysis Report",
            "description": "Comprehensive report combining all available analytical results.",
            "sections": [
                "profile_overview",
                "quality_summary",
                "eda_full",
                "statistics_full",
                "ml_full",
                "forecast_full",
            ],
        },
        ReportTemplate.CUSTOM: {
            "name": "Custom Report",
            "description": "User-defined report with custom sections.",
            "sections": [],
        },
    }

    def __init__(self):
        self._profile_reader = ProfileSourceReader()
        self._quality_reader = QualitySourceReader()
        self._eda_reader = EdaSourceReader()
        self._statistics_reader = StatisticsSourceReader()
        self._ml_reader = MlSourceReader()
        self._forecast_reader = ForecastSourceReader()

    def build(
        self,
        dataset_id: str,
        version_id: str,
        template: ReportTemplate,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        custom_sections: Optional[List[ReportSection]] = None,
    ) -> ReportDefinition:
        """
        Build a ReportDefinition from a template.
        Auto-populates sections by reading existing analytical results.
        Gracefully handles missing results by skipping unavailable sections.
        """
        template_meta = self.TEMPLATE_METADATA.get(template, {})

        if template == ReportTemplate.CUSTOM and custom_sections:
            sections = custom_sections
        else:
            section_builders = template_meta.get("sections", [])
            sections = []
            order = 0
            for builder_name in section_builders:
                try:
                    built = self._build_section(
                        builder_name, dataset_id, version_id, order
                    )
                    if built:
                        if isinstance(built, list):
                            for s in built:
                                s.order = order
                                sections.append(s)
                                order += 1
                        else:
                            built.order = order
                            sections.append(built)
                            order += 1
                except Exception as e:
                    logger.warning(
                        f"Skipping report section '{builder_name}': {e}"
                    )

        # Add "no data" section if everything failed
        if not sections:
            sections = [
                ReportSection(
                    title="No Data Available",
                    content_type=ReportSectionType.MARKDOWN,
                    content={
                        "text": "No analytical results are available for this dataset. "
                        "Run profiling, quality assessment, or EDA before generating a report."
                    },
                    order=0,
                )
            ]

        report_title = title or template_meta.get("name", "Analysis Report")

        return ReportDefinition(
            dataset_id=dataset_id,
            version_id=version_id,
            title=report_title,
            subtitle=subtitle or template_meta.get("description", ""),
            template=template,
            sections=sections,
            provenance=ExportProvenance(
                dataset_id=dataset_id,
                dataset_version_id=version_id,
                source_engine="report_builder",
            ),
        )

    def list_templates(self) -> List[Dict[str, Any]]:
        """Return metadata for all available report templates."""
        return [
            {
                "template": template.value,
                "name": meta["name"],
                "description": meta["description"],
                "section_count": len(meta["sections"]),
            }
            for template, meta in self.TEMPLATE_METADATA.items()
        ]

    def _build_section(
        self,
        builder_name: str,
        dataset_id: str,
        version_id: str,
        order: int,
    ) -> Optional[ReportSection | List[ReportSection]]:
        """Dispatch to the appropriate section builder."""
        builders = {
            "profile_overview": self._build_profile_overview,
            "quality_summary": self._build_quality_summary,
            "quality_full": self._build_quality_full,
            "top_eda_findings": self._build_top_eda_findings,
            "eda_full": self._build_eda_full,
            "statistics_full": self._build_statistics_full,
            "ml_full": self._build_ml_full,
            "forecast_full": self._build_forecast_full,
        }

        builder_fn = builders.get(builder_name)
        if not builder_fn:
            return None
        return builder_fn(dataset_id, version_id)

    def _build_profile_overview(
        self, dataset_id: str, version_id: str
    ) -> ReportSection:
        """Build profile overview section with KPIs."""
        source = self._profile_reader.read(dataset_id, version_id)
        metadata = source.metadata

        kpis = [
            {"label": "Rows", "value": metadata.get("row_count", "N/A")},
            {"label": "Columns", "value": metadata.get("column_count", "N/A")},
        ]

        # Extract column type breakdown if available
        if isinstance(source.data, list):
            type_counts: Dict[str, int] = {}
            for col in source.data:
                if isinstance(col, dict):
                    col_type = col.get("semantic_type", col.get("dtype", "unknown"))
                    type_counts[str(col_type)] = type_counts.get(str(col_type), 0) + 1

            for type_name, count in list(type_counts.items())[:4]:
                kpis.append({"label": type_name.title(), "value": count})

        return ReportSection(
            title="Dataset Overview",
            content_type=ReportSectionType.KPI_GRID,
            content={"kpis": kpis},
        )

    def _build_quality_summary(
        self, dataset_id: str, version_id: str
    ) -> ReportSection:
        """Build quality summary section."""
        source = self._quality_reader.read(dataset_id, version_id)
        metadata = source.metadata

        score = metadata.get("overall_score", "N/A")
        total_issues = metadata.get("total_issues", 0)

        text = f"**Overall Quality Score:** {score}\n\n"
        text += f"**Total Issues Detected:** {total_issues}\n\n"

        severity = metadata.get("severity_breakdown", {})
        if severity:
            text += "**Severity Breakdown:**\n"
            for level, count in severity.items():
                text += f"- {level}: {count}\n"

        return ReportSection(
            title="Data Quality Summary",
            content_type=ReportSectionType.MARKDOWN,
            content={"text": text},
        )

    def _build_quality_full(
        self, dataset_id: str, version_id: str
    ) -> List[ReportSection]:
        """Build comprehensive quality report sections."""
        source = self._quality_reader.read(dataset_id, version_id)
        sections = []

        # Summary section
        sections.append(self._build_quality_summary(dataset_id, version_id))

        # Issues table
        issues = source.data
        if isinstance(issues, list) and issues:
            # Try to extract tabular columns from issues
            if isinstance(issues[0], dict):
                columns = list(issues[0].keys())
                sections.append(
                    ReportSection(
                        title="Quality Issues",
                        content_type=ReportSectionType.TABLE,
                        content={
                            "columns": columns,
                            "rows": issues[:settings.EXPORT_MAX_TABLE_ROWS_IN_REPORT],
                        },
                    )
                )

        return sections

    def _build_top_eda_findings(
        self, dataset_id: str, version_id: str
    ) -> ReportSection:
        """Build top EDA findings section."""
        source = self._eda_reader.read(dataset_id, version_id)
        findings = source.data

        text = ""
        if isinstance(findings, list):
            for i, finding in enumerate(findings[:10], 1):
                if isinstance(finding, dict):
                    title = finding.get("title", finding.get("observation", f"Finding {i}"))
                    severity = finding.get("severity", finding.get("importance", ""))
                    description = finding.get("description", finding.get("detail", ""))
                    text += f"### {i}. {title}"
                    if severity:
                        text += f" ({severity})"
                    text += f"\n{description}\n\n"
                else:
                    text += f"### {i}. {finding}\n\n"
        else:
            text = "No EDA findings available."

        return ReportSection(
            title="Top Exploratory Findings",
            content_type=ReportSectionType.MARKDOWN,
            content={"text": text},
        )

    def _build_eda_full(
        self, dataset_id: str, version_id: str
    ) -> List[ReportSection]:
        """Build full EDA sections."""
        source = self._eda_reader.read(dataset_id, version_id)
        findings = source.data
        sections = []

        if isinstance(findings, list):
            # Group by category if available
            categorized: Dict[str, List] = {}
            for finding in findings:
                if isinstance(finding, dict):
                    category = finding.get("category", finding.get("type", "General"))
                    categorized.setdefault(category, []).append(finding)
                else:
                    categorized.setdefault("General", []).append(finding)

            for category, items in categorized.items():
                text = ""
                for finding in items:
                    if isinstance(finding, dict):
                        title = finding.get("title", finding.get("observation", ""))
                        desc = finding.get("description", finding.get("detail", ""))
                        text += f"**{title}**\n{desc}\n\n"
                    else:
                        text += f"- {finding}\n"

                sections.append(
                    ReportSection(
                        title=f"EDA: {category}",
                        content_type=ReportSectionType.MARKDOWN,
                        content={"text": text},
                    )
                )
        else:
            sections.append(self._build_top_eda_findings(dataset_id, version_id))

        return sections if sections else [self._build_top_eda_findings(dataset_id, version_id)]

    def _build_statistics_full(
        self, dataset_id: str, version_id: str
    ) -> Optional[ReportSection | List[ReportSection]]:
        """Build statistics results sections."""
        source = self._statistics_reader.read(dataset_id, version_id)
        results = source.data

        sections = []
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    sections.append(
                        ReportSection(
                            title=f"Statistical Test: {result.get('test_type', result.get('test_name', 'Unknown'))}",
                            content_type=ReportSectionType.STATISTICS_SUMMARY,
                            content=result,
                        )
                    )

        return sections if sections else None

    def _build_ml_full(
        self, dataset_id: str, version_id: str
    ) -> Optional[ReportSection | List[ReportSection]]:
        """Build ML experiment sections."""
        source = self._ml_reader.read(dataset_id, version_id)
        results = source.data

        sections = []
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    sections.append(
                        ReportSection(
                            title=f"ML Experiment: {result.get('experiment_name', result.get('experiment_id', 'Unknown'))}",
                            content_type=ReportSectionType.ML_METRICS,
                            content=result,
                        )
                    )

        return sections if sections else None

    def _build_forecast_full(
        self, dataset_id: str, version_id: str
    ) -> Optional[ReportSection | List[ReportSection]]:
        """Build forecast results sections."""
        source = self._forecast_reader.read(dataset_id, version_id)
        results = source.data

        sections = []
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    sections.append(
                        ReportSection(
                            title=f"Forecast: {result.get('model_type', result.get('forecast_id', 'Unknown'))}",
                            content_type=ReportSectionType.FORECAST_HORIZON,
                            content=result,
                        )
                    )

        return sections if sections else None
