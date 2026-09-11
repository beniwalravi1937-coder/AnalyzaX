"""
Format-Specific Renderers for Phase 15 Export Engine.
Pure serialization functions — no HTTP awareness, no analytical recomputation.
Each renderer takes structured data + provenance and writes to a file.
"""

import csv
import io
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.exports.models import ExportProvenance, ExportSourceData


class CsvRenderer:
    """Exports tabular data to CSV via Polars."""

    def render(
        self,
        source_data: ExportSourceData,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int, int]:
        """
        Render data to CSV file.
        Returns (file_path, file_size_bytes, row_count).
        """
        opts = options or {}
        delimiter = opts.get("delimiter", ",")
        include_headers = opts.get("include_headers", True)

        data = source_data.data
        if not data:
            # Write empty CSV with headers only
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                f.write("")
            return output_path, 0, 0

        # Normalize data to list of dicts
        rows = self._normalize_to_rows(data)
        if not rows:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                f.write("")
            return output_path, 0, 0

        # Enforce row limit
        max_rows = min(len(rows), settings.EXPORT_MAX_ROWS)
        rows = rows[:max_rows]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            df = pl.DataFrame(rows)
            df.write_csv(
                output_path,
                separator=delimiter,
                include_header=include_headers,
            )
        except Exception:
            # Fallback to stdlib csv for complex/mixed types
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                if not rows:
                    return output_path, 0, 0
                writer = csv.DictWriter(
                    f,
                    fieldnames=list(rows[0].keys()),
                    delimiter=delimiter,
                )
                if include_headers:
                    writer.writeheader()
                for row in rows:
                    # Stringify non-primitive values
                    clean_row = {}
                    for k, v in row.items():
                        if isinstance(v, (dict, list)):
                            clean_row[k] = json.dumps(v)
                        else:
                            clean_row[k] = v
                    writer.writerow(clean_row)

        file_size = os.path.getsize(output_path)
        return output_path, file_size, len(rows)

    def _normalize_to_rows(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize various data shapes to list of dicts."""
        if isinstance(data, list):
            if all(isinstance(r, dict) for r in data):
                return data
            return [{"value": r} for r in data]
        elif isinstance(data, dict):
            # Single dict — try to find tabular data within
            for key in ("rows", "data", "results", "records"):
                if key in data and isinstance(data[key], list):
                    return self._normalize_to_rows(data[key])
            return [data]
        return []


class JsonRenderer:
    """Exports structured results to JSON."""

    def render(
        self,
        source_data: ExportSourceData,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int, int]:
        """
        Render data to JSON file.
        Returns (file_path, file_size_bytes, row_count).
        """
        opts = options or {}
        indent = opts.get("indent", 2)
        orient = opts.get("orient", "records")  # "records" or "full"

        data = source_data.data
        row_count = 0

        if orient == "full":
            # Include metadata and provenance
            output = {
                "data": data,
                "metadata": source_data.metadata,
                "provenance": source_data.provenance.model_dump() if source_data.provenance else {},
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            output = data

        if isinstance(data, list):
            row_count = len(data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                output,
                f,
                indent=indent,
                default=str,
                ensure_ascii=False,
            )

        file_size = os.path.getsize(output_path)
        return output_path, file_size, row_count


class XlsxRenderer:
    """Exports tabular data to Excel via Polars + openpyxl."""

    def render(
        self,
        source_data: ExportSourceData,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int, int]:
        """
        Render data to XLSX file. Supports multi-sheet workbooks.
        Returns (file_path, file_size_bytes, row_count).
        """
        opts = options or {}
        sheet_name = opts.get("sheet_name", "Data")
        include_provenance_sheet = opts.get("include_provenance", True)

        data = source_data.data
        rows = CsvRenderer()._normalize_to_rows(data)

        # Enforce row limit
        max_rows = min(len(rows), settings.EXPORT_MAX_ROWS)
        rows = rows[:max_rows]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name

            if rows:
                clean_rows = []
                for row in rows:
                    clean = {}
                    for k, v in row.items():
                        if isinstance(v, (dict, list)):
                            clean[k] = json.dumps(v)
                        else:
                            clean[k] = v
                    clean_rows.append(clean)

                headers = list(clean_rows[0].keys())
                ws.append(headers)
                for r in clean_rows:
                    ws.append([r.get(h) for h in headers])
            else:
                ws.append(["No data available"])

            wb.save(output_path)

            # Add provenance sheet if requested
            if include_provenance_sheet and source_data.provenance:
                self._add_provenance_sheet(output_path, source_data)

        except Exception as e:
            logger.error(f"XLSX render failed: {e}")
            raise ValueError(f"Failed to create Excel file: {e}")

        file_size = os.path.getsize(output_path)
        return output_path, file_size, len(rows)

    def _add_provenance_sheet(
        self, output_path: str, source_data: ExportSourceData
    ) -> None:
        """Add a Provenance metadata sheet to the workbook."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(output_path)
            ws = wb.create_sheet("Provenance")
            prov = source_data.provenance
            ws.append(["Property", "Value"])
            ws.append(["Dataset ID", prov.dataset_id])
            ws.append(["Dataset Version", prov.dataset_version_id])
            ws.append(["Source Engine", prov.source_engine or "N/A"])
            ws.append(["Source Result ID", prov.source_result_id or "N/A"])
            ws.append(["Stale", "Yes" if prov.is_stale else "No"])
            if prov.stale_reason:
                ws.append(["Stale Reason", prov.stale_reason])
            ws.append(["Exported At", prov.exported_at])
            ws.append(["Platform", prov.platform_version])

            # Add metadata
            if source_data.metadata:
                ws.append([])
                ws.append(["Metadata", ""])
                for key, value in source_data.metadata.items():
                    ws.append([str(key), str(value)])

            wb.save(output_path)
        except Exception as e:
            logger.warning(f"Failed to add provenance sheet: {e}")


class HtmlReportRenderer:
    """Renders self-contained HTML reports from ReportDefinition using Jinja2."""

    def render(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int, int]:
        """
        Render report to self-contained HTML file.
        Returns (file_path, file_size_bytes, section_count).
        """
        import jinja2
        import markdown as md_lib

        title = report_data.get("title", "Analysis Report")
        subtitle = report_data.get("subtitle", "")
        sections = report_data.get("sections", [])
        provenance = report_data.get("provenance", {})
        dataset_id = report_data.get("dataset_id", "")

        # Render sections to HTML
        rendered_sections = []
        for section in sections:
            rendered = self._render_section(section, md_lib)
            rendered_sections.append(rendered)

        # Build the full HTML document
        template_str = self._get_html_template()
        env = jinja2.Environment(autoescape=True)
        template = env.from_string(template_str)

        html = template.render(
            title=title,
            subtitle=subtitle,
            sections=rendered_sections,
            provenance=provenance,
            dataset_id=dataset_id,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        file_size = os.path.getsize(output_path)
        return output_path, file_size, len(sections)

    def _render_section(self, section: Dict[str, Any], md_lib: Any) -> Dict[str, Any]:
        """Render a single report section to HTML content."""
        content_type = section.get("content_type", "MARKDOWN")
        content = section.get("content", {})
        title = section.get("title", "")

        if content_type == "MARKDOWN":
            text = content.get("text", content.get("markdown", ""))
            html_content = md_lib.markdown(
                str(text), extensions=["tables", "fenced_code"]
            )
        elif content_type == "TABLE":
            html_content = self._render_table(content)
        elif content_type == "KPI_GRID":
            html_content = self._render_kpi_grid(content)
        elif content_type == "STATISTICS_SUMMARY":
            html_content = self._render_statistics(content)
        elif content_type == "ML_METRICS":
            html_content = self._render_ml_metrics(content)
        elif content_type == "FORECAST_HORIZON":
            html_content = self._render_forecast(content)
        else:
            html_content = f"<pre>{json.dumps(content, indent=2, default=str)}</pre>"

        return {"title": title, "html": html_content, "type": content_type}

    def _render_table(self, content: Dict[str, Any]) -> str:
        """Render a data table to HTML."""
        headers = content.get("columns", content.get("headers", []))
        rows = content.get("rows", content.get("data", []))
        max_rows = min(len(rows), settings.EXPORT_MAX_TABLE_ROWS_IN_REPORT)
        rows = rows[:max_rows]

        if not headers and rows:
            if isinstance(rows[0], dict):
                headers = list(rows[0].keys())

        html = '<table class="report-table"><thead><tr>'
        for h in headers:
            html += f"<th>{_escape_html(str(h))}</th>"
        html += "</tr></thead><tbody>"

        for row in rows:
            html += "<tr>"
            if isinstance(row, dict):
                for h in headers:
                    val = row.get(h, "")
                    html += f"<td>{_escape_html(str(val))}</td>"
            elif isinstance(row, (list, tuple)):
                for val in row:
                    html += f"<td>{_escape_html(str(val))}</td>"
            html += "</tr>"

        html += "</tbody></table>"
        if len(content.get("rows", content.get("data", []))) > max_rows:
            html += f'<p class="truncation-note">Showing {max_rows} of {len(content.get("rows", content.get("data", [])))} rows</p>'
        return html

    def _render_kpi_grid(self, content: Dict[str, Any]) -> str:
        """Render KPI metrics as a grid."""
        kpis = content.get("kpis", content.get("metrics", content.get("cards", [])))
        html = '<div class="kpi-grid">'
        for kpi in kpis:
            label = kpi.get("label", kpi.get("name", ""))
            value = kpi.get("value", "")
            unit = kpi.get("unit", "")
            html += f"""
            <div class="kpi-card">
                <div class="kpi-value">{_escape_html(str(value))}{_escape_html(str(unit))}</div>
                <div class="kpi-label">{_escape_html(str(label))}</div>
            </div>"""
        html += "</div>"
        return html

    def _render_statistics(self, content: Dict[str, Any]) -> str:
        """Render statistics summary."""
        test_name = content.get("test_name", content.get("test_type", ""))
        p_value = content.get("p_value", "")
        statistic = content.get("statistic", content.get("test_statistic", ""))
        conclusion = content.get("conclusion", content.get("interpretation", ""))

        html = f"""
        <div class="stats-summary">
            <div class="stat-row"><strong>Test:</strong> {_escape_html(str(test_name))}</div>
            <div class="stat-row"><strong>Test Statistic:</strong> {_escape_html(str(statistic))}</div>
            <div class="stat-row"><strong>p-value:</strong> {_escape_html(str(p_value))}</div>
            <div class="stat-row"><strong>Conclusion:</strong> {_escape_html(str(conclusion))}</div>
        </div>"""
        return html

    def _render_ml_metrics(self, content: Dict[str, Any]) -> str:
        """Render ML experiment metrics."""
        metrics = content.get("metrics", {})
        model_type = content.get("model_type", content.get("algorithm", ""))

        html = f'<div class="ml-metrics"><div class="stat-row"><strong>Model:</strong> {_escape_html(str(model_type))}</div>'
        html += '<div class="metrics-grid">'
        for name, value in metrics.items():
            formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
            html += f"""
            <div class="metric-card">
                <div class="metric-value">{_escape_html(formatted)}</div>
                <div class="metric-name">{_escape_html(str(name))}</div>
            </div>"""
        html += "</div></div>"
        return html

    def _render_forecast(self, content: Dict[str, Any]) -> str:
        """Render forecast results."""
        model_type = content.get("model_type", "")
        horizon = content.get("horizon", "")
        backtest = content.get("backtest_metrics", {})

        html = f"""
        <div class="forecast-summary">
            <div class="stat-row"><strong>Model:</strong> {_escape_html(str(model_type))}</div>
            <div class="stat-row"><strong>Horizon:</strong> {_escape_html(str(horizon))} periods</div>"""
        if backtest:
            html += '<div class="stat-row"><strong>Backtest Metrics:</strong></div>'
            for k, v in backtest.items():
                formatted = f"{v:.4f}" if isinstance(v, float) else str(v)
                html += f'<div class="stat-row ml-2">{_escape_html(str(k))}: {_escape_html(formatted)}</div>'
        html += "</div>"
        return html

    def _get_html_template(self) -> str:
        """Return the self-contained HTML report template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        :root {
            --bg: #0f1117;
            --surface: #1a1d27;
            --surface-2: #252836;
            --border: #2e3140;
            --text: #e4e4e7;
            --text-muted: #9ca3af;
            --primary: #6366f1;
            --primary-light: #818cf8;
            --accent: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }
        .report-container { max-width: 900px; margin: 0 auto; }
        .report-header {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--primary);
        }
        .report-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
        }
        .report-header .subtitle {
            font-size: 1rem;
            color: var(--text-muted);
        }
        .report-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .report-section h2 {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--primary-light);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .report-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8125rem;
        }
        .report-table th {
            background: var(--surface-2);
            color: var(--text-muted);
            font-weight: 600;
            text-align: left;
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            text-transform: uppercase;
            font-size: 0.6875rem;
            letter-spacing: 0.05em;
        }
        .report-table td {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            color: var(--text);
        }
        .report-table tr:hover td { background: var(--surface-2); }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
        }
        .kpi-card {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1rem;
            text-align: center;
        }
        .kpi-value { font-size: 1.5rem; font-weight: 700; color: var(--primary-light); }
        .kpi-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .stats-summary, .ml-metrics, .forecast-summary {
            background: var(--surface-2);
            border-radius: 6px;
            padding: 1rem;
        }
        .stat-row { padding: 0.25rem 0; font-size: 0.875rem; }
        .stat-row strong { color: var(--text-muted); }
        .ml-2 { margin-left: 1rem; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 0.75rem;
            text-align: center;
        }
        .metric-value { font-size: 1.125rem; font-weight: 600; color: var(--accent); }
        .metric-name { font-size: 0.6875rem; color: var(--text-muted); text-transform: uppercase; margin-top: 0.25rem; }
        .truncation-note { font-size: 0.75rem; color: var(--warning); margin-top: 0.5rem; font-style: italic; }
        .report-footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            font-size: 0.75rem;
            color: var(--text-muted);
            text-align: center;
        }
        .stale-warning {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid var(--warning);
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            color: var(--warning);
            font-size: 0.8125rem;
        }
        pre {
            background: var(--surface-2);
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.8125rem;
        }
        code { font-family: 'JetBrains Mono', 'Cascadia Code', monospace; }
        @media print {
            body { background: white; color: #1a1a1a; padding: 0; }
            .report-container { max-width: 100%; }
            .report-section { border: 1px solid #ddd; break-inside: avoid; }
            .report-header { border-bottom-color: #6366f1; }
            .report-header h1 { color: #1a1a1a; }
            .kpi-value, .metric-value { color: #6366f1; }
            .report-table th { background: #f3f4f6; color: #374151; }
            .report-table td { color: #1a1a1a; border-color: #e5e7eb; }
            .stats-summary, .ml-metrics, .forecast-summary,
            .kpi-card, .metric-card { background: #f9fafb; border-color: #e5e7eb; }
            .stat-row strong { color: #6b7280; }
            .report-footer { color: #9ca3af; }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{{ title }}</h1>
            {% if subtitle %}<div class="subtitle">{{ subtitle }}</div>{% endif %}
        </div>

        {% if provenance and provenance.is_stale %}
        <div class="stale-warning">
            ⚠ This report contains results from a superseded dataset version.
            {% if provenance.stale_reason %}Reason: {{ provenance.stale_reason }}{% endif %}
        </div>
        {% endif %}

        {% for section in sections %}
        <div class="report-section">
            <h2>{{ section.title }}</h2>
            {{ section.html | safe }}
        </div>
        {% endfor %}

        <div class="report-footer">
            <p>Generated by AnalyzaX &mdash; {{ generated_at }}</p>
            {% if dataset_id %}<p>Dataset: {{ dataset_id }}</p>{% endif %}
            {% if provenance %}
            <p>Version: {{ provenance.dataset_version_id }} | Engine: {{ provenance.source_engine or 'N/A' }}</p>
            {% endif %}
        </div>
    </div>
</body>
</html>"""


class MarkdownReportRenderer:
    """Renders Markdown reports from ReportDefinition."""

    def render(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int, int]:
        """
        Render report to Markdown file.
        Returns (file_path, file_size_bytes, section_count).
        """
        title = report_data.get("title", "Analysis Report")
        subtitle = report_data.get("subtitle", "")
        sections = report_data.get("sections", [])
        provenance = report_data.get("provenance", {})
        dataset_id = report_data.get("dataset_id", "")

        lines = []
        lines.append(f"# {title}")
        if subtitle:
            lines.append(f"\n*{subtitle}*")
        lines.append("")

        # Stale warning
        if provenance and provenance.get("is_stale"):
            lines.append(f"> ⚠️ **Warning:** This report contains results from a superseded dataset version.")
            if provenance.get("stale_reason"):
                lines.append(f"> Reason: {provenance['stale_reason']}")
            lines.append("")

        for section in sections:
            rendered = self._render_section(section)
            lines.append(rendered)
            lines.append("")

        # Footer
        lines.append("---")
        lines.append(
            f"*Generated by AnalyzaX — "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        )
        if dataset_id:
            lines.append(f"\n*Dataset: {dataset_id}*")

        content = "\n".join(lines)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_size = os.path.getsize(output_path)
        return output_path, file_size, len(sections)

    def _render_section(self, section: Dict[str, Any]) -> str:
        """Render a single section to Markdown."""
        content_type = section.get("content_type", "MARKDOWN")
        content = section.get("content", {})
        title = section.get("title", "")

        lines = [f"## {title}", ""]

        if content_type == "MARKDOWN":
            text = content.get("text", content.get("markdown", ""))
            lines.append(str(text))

        elif content_type == "TABLE":
            lines.append(self._render_table_md(content))

        elif content_type == "KPI_GRID":
            kpis = content.get("kpis", content.get("metrics", []))
            for kpi in kpis:
                label = kpi.get("label", kpi.get("name", ""))
                value = kpi.get("value", "")
                unit = kpi.get("unit", "")
                lines.append(f"- **{label}:** {value}{unit}")

        elif content_type == "STATISTICS_SUMMARY":
            test_name = content.get("test_name", content.get("test_type", ""))
            p_value = content.get("p_value", "")
            statistic = content.get("statistic", content.get("test_statistic", ""))
            conclusion = content.get("conclusion", content.get("interpretation", ""))
            lines.append(f"- **Test:** {test_name}")
            lines.append(f"- **Test Statistic:** {statistic}")
            lines.append(f"- **p-value:** {p_value}")
            lines.append(f"- **Conclusion:** {conclusion}")

        elif content_type == "ML_METRICS":
            model_type = content.get("model_type", content.get("algorithm", ""))
            metrics = content.get("metrics", {})
            lines.append(f"**Model:** {model_type}")
            lines.append("")
            if metrics:
                lines.append("| Metric | Value |")
                lines.append("|--------|-------|")
                for name, value in metrics.items():
                    formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
                    lines.append(f"| {name} | {formatted} |")

        elif content_type == "FORECAST_HORIZON":
            model_type = content.get("model_type", "")
            horizon = content.get("horizon", "")
            lines.append(f"- **Model:** {model_type}")
            lines.append(f"- **Horizon:** {horizon} periods")
            backtest = content.get("backtest_metrics", {})
            if backtest:
                lines.append("")
                lines.append("**Backtest Metrics:**")
                for k, v in backtest.items():
                    formatted = f"{v:.4f}" if isinstance(v, float) else str(v)
                    lines.append(f"- {k}: {formatted}")

        else:
            lines.append(f"```json\n{json.dumps(content, indent=2, default=str)}\n```")

        return "\n".join(lines)

    def _render_table_md(self, content: Dict[str, Any]) -> str:
        """Render a data table in GFM format."""
        headers = content.get("columns", content.get("headers", []))
        rows = content.get("rows", content.get("data", []))
        max_rows = min(len(rows), settings.EXPORT_MAX_TABLE_ROWS_IN_REPORT)
        rows = rows[:max_rows]

        if not headers and rows:
            if isinstance(rows[0], dict):
                headers = list(rows[0].keys())

        if not headers:
            return "*No data available*"

        lines = []
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")

        for row in rows:
            if isinstance(row, dict):
                values = [str(row.get(h, "")) for h in headers]
            elif isinstance(row, (list, tuple)):
                values = [str(v) for v in row]
            else:
                values = [str(row)]
            lines.append("| " + " | ".join(values) + " |")

        if len(content.get("rows", content.get("data", []))) > max_rows:
            lines.append(
                f"\n*Showing {max_rows} of "
                f"{len(content.get('rows', content.get('data', [])))} rows*"
            )

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Renderer Registry
# ─────────────────────────────────────────────────────────────

RENDERERS = {
    "CSV": CsvRenderer,
    "JSON": JsonRenderer,
    "XLSX": XlsxRenderer,
    "HTML_REPORT": HtmlReportRenderer,
    "MARKDOWN_REPORT": MarkdownReportRenderer,
}


def get_renderer(format_name: str):
    """Factory function to get the appropriate renderer."""
    renderer_class = RENDERERS.get(format_name)
    if not renderer_class:
        raise ValueError(f"Unsupported export format: {format_name}")
    return renderer_class()


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
