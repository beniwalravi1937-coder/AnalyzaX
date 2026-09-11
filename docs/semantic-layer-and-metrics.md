# AnalyzaX — Governed Semantic Layer & Metrics Intelligence

## 1. Overview
The Governed Semantic Layer in AnalyzaX provides a single source of truth for analytical metrics, business definitions, and entities. It decouples metric calculations from ad-hoc SQL queries and ensures that the AI Copilot and users resolve business concepts identically.

---

## 2. Core Concepts

### 2.1 Metric Definition
A governed metric specifies:
- **`name`:** Canonical metric name (e.g., `Revenue`, `Gross Margin`).
- **`expression`:** Constrained formula expression (e.g., `SUM(sales)`, `(revenue - cost) / revenue`).
- **`aggregation`:** Primary aggregation (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, `CUSTOM`).
- **`unit`:** Currency, percentage, or scalar indicator.
- **`synonyms`:** Natural language aliases (e.g., `sales`, `turnover`, `topline`).
- **`status`:** Lifecycle status (`DRAFT`, `ACTIVE`, `DEPRECATED`, `ARCHIVED`).
- **`version`:** Monotonically increasing version identifier.

### 2.2 Expression Validation & Safety
Metric expressions are parsed through an AST and validated:
- **Allowlisted Functions:** `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `ROUND`, `ABS`, `COALESCE`, `NULLIF`.
- **Forbidden Constructs:** Execution of `eval()`, `exec()`, `import`, arbitrary Python, or unvalidated SQL concatenation is strictly blocked.
- **Column Integrity:** Verified against underlying dataset schema columns.
- **Cycle Detection:** Recursive references (Metric A depending on Metric B which depends on Metric A) are caught and rejected prior to persistence.

---

## 3. Version History & Traceability
- Every edit to an existing metric captures a complete deep-copy snapshot (`MetricVersionRecord`) containing previous expression, aggregation, description, author, and timestamp.
- Analytical results and AI provenance objects cite the specific metric version used during computation.

---

## 4. Deterministic Execution
- Metrics are evaluated in DuckDB using validated parameter bindings and compiled aggregate SQL queries.
- Preview calculation returns sample aggregation values alongside generated SQL for complete transparency.

---

## 5. API Endpoints
- `GET /api/v1/metrics`: List governed metrics filtered by workspace and status.
- `POST /api/v1/metrics`: Create a new governed metric.
- `GET /api/v1/metrics/{metric_id}`: Retrieve metric details.
- `PUT /api/v1/metrics/{metric_id}`: Update metric definition (creates version record).
- `DELETE /api/v1/metrics/{metric_id}`: Archive or delete metric.
- `POST /api/v1/metrics/{metric_id}/validate`: Validate expression AST and column bindings.
- `POST /api/v1/metrics/{metric_id}/preview`: Execute deterministic preview calculation.
- `GET /api/v1/metrics/{metric_id}/versions`: Retrieve version history.
