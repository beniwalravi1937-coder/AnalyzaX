# AnalyzaX — API Design Specification

This document defines the REST and real-time API specifications for the AnalyzaX FastAPI backend. All endpoints are versioned under `/api/v1`.

---

## 1. Global Conventions & Standards

- **Protocol:** HTTPS / WSS
- **Base URI:** `/api/v1`
- **Request/Response Encoding:** `application/json` (except multipart file uploads and binary file downloads)
- **Authentication:** Bearer JWT Token in `Authorization` header (implemented in Phase 16)
- **Standard Pagination:** `?page=1&limit=50&sort_by=column_name&sort_dir=asc|desc`

### Standard Success Envelope
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-09-08T13:45:00Z",
    "request_id": "req_01h8a9b2c3d4e5f6"
  }
}
```

### Standard Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "DATASET_NOT_FOUND",
    "message": "Dataset ds_8f72ab91 does not exist or has been deleted.",
    "details": {}
  },
  "meta": {
    "timestamp": "2026-09-08T13:45:00Z",
    "request_id": "req_01h8a9b2c3d4e5f6"
  }
}
```

---

## 2. Core Endpoints Specification

### 2.1 System & Health
- `GET /healthz` — Basic liveness probe (returns `{"status": "ok"}`)
- `GET /readyz` — Readiness probe verifying PostgreSQL, Redis, and disk storage access
- `GET /api/v1/system/info` — Engine versions, DuckDB limits, and configured LLM provider

---

### 2.2 Datasets & Versions
- `POST /api/v1/datasets/upload`
  - **Content-Type:** `multipart/form-data`
  - **Body:** `file` (binary), `name` (optional string)
  - **Response (202 Accepted):** Returns `dataset_id` (e.g., `ds_8f72ab91`) and background ingestion `job_id`.
- `GET /api/v1/datasets`
  - **Query Params:** `page`, `limit`, `search`
  - **Response (200 OK):** List of dataset summaries (ID, name, row count, column count, created timestamp, active version).
- `GET /api/v1/datasets/{dataset_id}`
  - **Response (200 OK):** Complete metadata, schema, column data types, and storage statistics.
- `GET /api/v1/datasets/{dataset_id}/preview`
  - **Query Params:** `version_id` (optional), `offset`, `limit` (default 50, max 500)
  - **Response (200 OK):** Tabular preview data with column names and row values.
- `GET /api/v1/datasets/{dataset_id}/versions`
  - **Response (200 OK):** Array of immutable versions (`v1_raw`, `v2_cleaned`, etc.) with lineage IDs.

---

### 2.3 Asynchronous Job Management
- `GET /api/v1/jobs/{job_id}`
  - **Response (200 OK):** Current job status (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`), progress percentage (0–100), step description, and result payload if finished.
- `POST /api/v1/jobs/{job_id}/cancel`
  - **Response (200 OK):** Cancels running background task.

---

### 2.4 Profiling & Data Quality
- `GET /api/v1/datasets/{dataset_id}/profile`
  - **Response (200 OK):** Full statistical profile: column types, null counts, cardinalities, value distributions, continuous quantiles, ML target candidates.
- `POST /api/v1/datasets/{dataset_id}/profile/refresh`
  - **Response (200 OK):** Forces recalculation of structural and statistical profile.
- `GET /api/v1/datasets/{dataset_id}/quality`
  - **Query Params:** `severity` (optional), `dimension` (optional), `column` (optional).
  - **Response (200 OK):** Comprehensive Data Quality report:
    - `overall_score` (0.0 to 100.0) and `overall_grade` (`EXCELLENT`, `GOOD`, `FAIR`, `POOR`, `CRITICAL`).
    - `dimension_scores` across Completeness, Validity, Uniqueness, Consistency, Integrity, and Anomaly Risk.
    - `issues` list with severity ratings, affected rows/percentage, statistical evidence, and recommended Phase 6 cleaning actions.
    - `column_summaries` detailing column-specific quality ratings.
- `POST /api/v1/datasets/{dataset_id}/quality/refresh`
  - **Response (200 OK):** Invalidates quality report cache and re-executes all 8 modular quality rules against the DuckDB view.

---

### 2.5 Cleaning, Transformations & Dataset Versions
- `GET /api/v1/cleaning/recommendations/{dataset_id}`
  - **Query Params:** `force_refresh` (optional boolean)
  - **Response (200 OK):** List of prioritized `CleaningRecommendation` cards derived from Phase 5 quality issues, complete with pre-configured `suggested_step`.
- `GET /api/v1/cleaning/plan/{dataset_id}`
  - **Response (200 OK):** Current draft `TransformationPlan` for the dataset.
- `POST /api/v1/cleaning/plan/{dataset_id}`
  - **Body:** `{"steps": [...], "source_version_id": "v1"}`
  - **Response (200 OK):** Persisted `TransformationPlan`.
- `POST /api/v1/cleaning/preview/{dataset_id}`
  - **Body:** `{"steps": [...], "source_version_id": "v1", "preview_rows": 10}`
  - **Response (200 OK):** `TransformationPreview` containing sample before and after rows, column diffs, and step impact summaries.
- `POST /api/v1/cleaning/dry-run/{dataset_id}`
  - **Body:** `{"steps": [...], "source_version_id": "v1"}`
  - **Response (200 OK):** `DryRunResult` with validation errors and schema diff prediction.
- `POST /api/v1/cleaning/apply/{dataset_id}`
  - **Body:** `{"steps": [...], "version_label": "Cleaned Dataset", "source_version_id": "v1"}`
  - **Response (200 OK):** `ApplyPlanResponse` containing `new_version`, `comparison` scorecard, and `audit` log.
- `GET /api/v1/versions/{dataset_id}`
  - **Response (200 OK):** List of all `DatasetVersion` instances (`v1`, `v2`, ...).
- `GET /api/v1/versions/{dataset_id}/active`
  - **Response (200 OK):** Active `DatasetVersion`.
- `POST /api/v1/versions/{dataset_id}/activate/{version_id}`
  - **Response (200 OK):** Rollback / switch dataset to specified version and update DuckDB active views.
- `GET /api/v1/versions/{dataset_id}/lineage`
  - **Response (200 OK):** `LineageResponse` with DAG nodes and parent-child edges.
- `GET /api/v1/versions/{dataset_id}/compare?before=v1&after=v2`
  - **Response (200 OK):** `QualityComparison` differential scorecard between two versions.

---

### 2.6 EDA & Statistical Testing
- `POST /api/v1/datasets/{dataset_id}/eda/correlations`
  - **Body:** `{"method": "pearson" | "spearman", "columns": ["col1", "col2"]}`
  - **Response (200 OK):** Symmetric correlation matrix and p-value matrix.
- `POST /api/v1/datasets/{dataset_id}/eda/distributions`
  - **Body:** `{"columns": ["revenue", "age"], "bin_count": 30}`
  - **Response (200 OK):** Bin edges, frequencies, quantiles, skewness, and kurtosis.
- `POST /api/v1/datasets/{dataset_id}/statistics/test`
  - **Body:**
    ```json
    {
      "test_type": "two_sample_ttest",
      "column_a": "revenue_group_a",
      "column_b": "revenue_group_b",
      "alpha": 0.05
    }
    ```
  - **Response (200 OK):** Test statistic, p-value, degrees of freedom, confidence interval, and interpretation.

---

### 2.7 SQL Analytics Studio (DuckDB)
- `POST /api/v1/datasets/{dataset_id}/sql/validate`
  - **Body:** `{"query": "SELECT category, SUM(sales) FROM dataset GROUP BY category"}`
  - **Response (200 OK):** AST validation status (`valid: true/false`), detected tables, read-only verification, and syntax errors.
- `POST /api/v1/datasets/{dataset_id}/sql/execute`
  - **Body:**
    ```json
    {
      "query": "SELECT category, SUM(sales) AS total_sales FROM dataset GROUP BY category ORDER BY total_sales DESC LIMIT 50",
      "timeout_seconds": 15
    }
    ```
  - **Response (200 OK):** Schema, column types, row records (JSON array), execution duration (ms), total rows scanned.

---

### 2.8 Machine Learning & Forecasting
- `POST /api/v1/datasets/{dataset_id}/ml/detect-task`
  - **Body:** `{"target_column": "churn"}`
  - **Response (200 OK):** Inferred task (`classification`), candidate algorithms, recommended evaluation metrics.
- `POST /api/v1/datasets/{dataset_id}/ml/train`
  - **Body:** `{"task_type": "classification", "target_column": "churn", "feature_columns": ["tenure", "monthly_charges"], "algorithms": ["logistic_regression", "random_forest"]}`
  - **Response (202 Accepted):** Returns `job_id`.
- `GET /api/v1/datasets/{dataset_id}/ml/results/{model_job_id}`
  - **Response (200 OK):** Model leaderboard, cross-validation metrics, confusion matrix / residuals, feature importance rankings.
- `POST /api/v1/datasets/{dataset_id}/forecasting/train`
  - **Body:** `{"time_column": "date", "target_column": "daily_sales", "horizon": 30, "frequency": "D"}`
  - **Response (202 Accepted):** Dispatches forecasting job.

---

### 2.9 Visualization & Dashboards
- `POST /api/v1/datasets/{dataset_id}/charts/generate-spec`
  - **Body:** `{"chart_type": "bar", "x_column": "category", "y_column": "total_sales", "title": "Sales by Category"}`
  - **Response (200 OK):** Complete declarative Apache ECharts JSON specification.
- `GET /api/v1/datasets/{dataset_id}/dashboards`
  - **Response (200 OK):** List of saved dashboards.
- `POST /api/v1/datasets/{dataset_id}/dashboards`
  - **Body:** `{"title": "Executive Summary", "widgets": [...]}`
  - **Response (201 Created):** Persisted dashboard entity.

---

### 2.10 AI Analyst & Conversational Copilot
- `POST /api/v1/datasets/{dataset_id}/chat`
  - **Content-Type:** `application/json` (or Server-Sent Events stream `text/event-stream`)
  - **Body:**
    ```json
    {
      "conversation_id": "conv_91fa8b",
      "message": "Which product category generated the highest profit margin in Q3?",
      "stream": true
    }
    ```
  - **Stream Protocol:** Emits events for:
    1. `thought` — High-level intent analysis
    2. `tool_call` — e.g., `execute_sql`, `get_statistics`
    3. `tool_result` — Deterministic output from engine
    4. `content_delta` — Natural language narrative explanation
    5. `visualization` — Recommended ECharts configuration
- `POST /api/v1/datasets/{dataset_id}/chat/nl-to-sql`
  - **Body:** `{"prompt": "Show me monthly churn rates for 2025"}`
  - **Response (200 OK):** Generated SQL query, AST validation report, explanation of SQL logic.

---

### 2.11 Export Service
- `POST /api/v1/datasets/{dataset_id}/export`
  - **Body:** `{"format": "csv" | "xlsx" | "parquet" | "pdf", "version_id": "v2_cleaned"}`
  - **Response (202 Accepted):** Returns `export_id` and background compilation `job_id`.
- `GET /api/v1/exports/{export_id}/download`
  - **Response (200 OK):** Binary file stream with `Content-Disposition: attachment; filename="AnalyzaX_export.xlsx"`.

