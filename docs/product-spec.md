# AnalyzaX — Product Specification

## 1. Product Identification & Vision

- **Product Name:** AnalyzaX
- **Product Category:** AI-Powered End-to-End Data Analytics Platform
- **Product Positioning:** *"An AI Data Analyst that takes raw data all the way to actionable insights."*

### The Market Gap & Differentiation

Traditional BI platforms (such as Tableau, PowerBI, or Metabase) and modern semantic BI platforms (such as Omni) assume that enterprise data is already structured, cleaned, and connected to a governed cloud data warehouse:

```
Omni-style:
Connected Cloud Warehouse ➔ Semantic Layer ➔ SQL ➔ BI ➔ AI Assistant
```

In contrast, real-world analysts and business operators constantly deal with messy, ad-hoc, unformatted raw datasets: exported CSVs, disparate Excel spreadsheets, and fragmented customer dumps. AnalyzaX bridges this gap:

```
AnalyzaX:
Raw Dataset ➔ Automated Data Engineering ➔ EDA ➔ SQL ➔ Statistics ➔ ML ➔ Forecasting ➔ AI Analyst ➔ Visualization ➔ Dashboard ➔ Export
```

AnalyzaX acts as an autonomous pair-programmer for data analysts: handling tedious data wrangling, running deterministic statistical tests, recommending and tuning models, generating interactive ECharts dashboards, and explaining findings in clear business language.

---

## 2. Core Capabilities Matrix

AnalyzaX provides 26 foundational capabilities:

| # | Capability | Description | Deterministic Engine |
| :--- | :--- | :--- | :--- |
| 1 | **Understand Dataset** | Auto-detect schema, column semantics (ID, categorical, numerical, datetime, text), and volume. | Profiling |
| 2 | **Detect Quality Issues** | Identify schema mismatches, trailing whitespaces, irregular formatting, and corrupt records. | Profiling / Ingestion |
| 3 | **Detect Missing Values** | Quantify null counts, null percentages, and patterns (e.g., MCAR, MAR). | Profiling |
| 4 | **Detect Duplicates** | Detect exact duplicate rows and fuzzy/near duplicates across specific keys. | Cleaning |
| 5 | **Detect Inconsistent Data** | Flag casing inconsistencies (e.g., "NY", "New York", "ny"), mixed date formats, and conflicting categories. | Profiling |
| 6 | **Suggest Cleaning Steps** | Generate high-confidence, actionable cleaning recommendations with expected impact. | Cleaning / AI |
| 7 | **Apply Approved Cleaning** | Execute deterministic cleaning operations approved by the user. | Cleaning |
| 8 | **Preserve Original Data** | Immutable original raw uploads stored in separate, write-protected storage. | Storage / Ingestion |
| 9 | **Maintain Data Lineage** | Record DAG of every transformation: author, timestamp, rows before/after, and exact diff. | Lineage Service |
| 10 | **Automated EDA** | Generate distributions, quantiles, histograms, skewness, and cardinality metrics automatically. | EDA |
| 11 | **Statistical Analysis** | Compute correlation matrices, run hypothesis tests (t-test, ANOVA, Chi-Square), and normality tests. | Statistics |
| 12 | **Natural Language Q&A** | Answer ad-hoc questions about dataset semantics, trends, and anomalies. | AI Engine |
| 13 | **NL to SQL Translation** | Translate business intent into performant DuckDB SQL queries. | AI Engine |
| 14 | **Safe SQL Execution** | Validate generated SQL with AST checks, enforce read-only semantics, row limits, and timeouts. | SQL Engine |
| 15 | **Table Generation** | Display virtualized, paginated, sortable, and filterable data tables for raw and queried data. | Presentation |
| 16 | **Visualization Specs** | Automatically recommend and render chart specifications (bar, line, scatter, boxplot, heatmap). | Visualization |
| 17 | **Detect ML Opportunities** | Inspect column types and variance to identify classification, regression, and clustering viability. | ML Engine |
| 18 | **Perform Regression** | Train and evaluate baseline regression models (Linear, Ridge, Lasso, Random Forest, Gradient Boosting). | ML Engine |
| 19 | **Perform Classification** | Train and evaluate binary/multiclass classification models (Logistic Regression, Random Forest, GBM). | ML Engine |
| 20 | **Perform Clustering** | Perform unsupervised segmentation (K-Means, DBSCAN) with optimal k selection (Elbow/Silhouette). | ML Engine |
| 21 | **Feature Engineering** | Execute one-hot encoding, target encoding, scaling (Standard, Robust), and interaction features. | ML Engine |
| 22 | **Perform Forecasting** | Detect time frequencies, check stationarity, and generate multi-step forecasts with confidence intervals. | Forecasting |
| 23 | **Model Comparison** | Produce standardized evaluation leaderboards (RMSE, MAE, R², F1, ROC-AUC, Silhouette score). | ML Engine |
| 24 | **AI Result Explanation** | Translate raw statistical outputs and model metrics into executive narrative summaries. | AI Engine |
| 25 | **Dashboard Generation** | Automatically assemble multiple analytical widgets into a responsive, customizable dashboard. | Dashboard Engine |
| 26 | **Multi-format Export** | Export processed datasets, query results, chart images, and executive summaries to CSV, Excel, Parquet, JSON, and PDF. | Export Engine |

---

## 3. The 10-Step User Experience Journey

```
[1. UPLOAD] ➔ [2. UNDERSTAND] ➔ [3. CLEAN] ➔ [4. ANALYZE] ➔ [5. MODEL]
     │
     ▼
[6. FORECAST] ➔ [7. ASK AI] ➔ [8. VISUALIZE] ➔ [9. DASHBOARD] ➔ [10. EXPORT]
```

### 1. UPLOAD
- User drags and drops CSV, Parquet, Excel (.xlsx, .xls), or JSON files.
- System validates file magic bytes, checks max size threshold, generates a unique Dataset ID (e.g., `ds_9a1f4b2e`), and streams the raw file to immutable storage.
- Immediate conversion to an internal columnar Parquet representation for high-speed downstream processing.

### 2. UNDERSTAND
- System triggers automated profiling: detects column data types (inferred vs raw), memory usage, row count, null percentages, unique value counts, and min/max ranges.
- A "Data Health Card" grades the dataset across Completeness, Uniqueness, Validity, and Consistency.

### 3. CLEAN (Human-in-the-Loop)
- AnalyzaX identifies quality issues and presents prioritized cleaning recommendations:
  - *"17 duplicate rows detected (0.17% of dataset). Recommend deduplication."*
  - *"Column 'Age' contains 4.2% missing values. Recommend median imputation (29.5)."*
- User reviews, accepts, rejects, or customizes operations.
- Upon approval, the Cleaning Engine creates a new dataset version (e.g., `v2_cleaned`), persisting a structured lineage record. The original upload remains untouched.

### 4. ANALYZE (EDA & Statistics)
- Automated generation of univariate distributions (histograms, box plots, frequency charts) and bivariate correlations.
- Statistical testing suite enables the user to select two columns and run appropriate tests (e.g., comparing conversion rates across user segments via Chi-Square).

### 5. MODEL (Machine Learning)
- User selects a target column or requests auto-detection.
- System detects task type:
  - Continuous target ➔ Regression
  - Discrete/categorical target ➔ Classification
  - No target selected ➔ Unsupervised Clustering
- System trains candidate baseline models, computes cross-validated metrics, and ranks models on a comparison leaderboard with feature importance charts.

### 6. FORECAST
- If a datetime column and numerical measure are present, the user can request a forecast.
- The engine checks for regular intervals (daily, weekly, monthly), handles missing timestamps, tests stationarity (ADF test), fits time-series models (ETS, ARIMA), and outputs multi-period forecasts with 80% and 95% confidence bands.

### 7. ASK AI (Conversational Data Analyst)
- User queries the dataset via natural language: *"Which marketing channel had the lowest CAC last quarter, and did its volume drop?"*
- The AI Agent generates a validated DuckDB SQL query, runs it deterministically, inspects the table result, and writes an executive explanation accompanied by a recommended chart.

### 8. VISUALIZE
- Users explore and customize charts generated from query results or EDA metrics.
- All charts are defined via declarative JSON specifications rendered by Apache ECharts, allowing zoom, pan, tooltip inspection, and color palette switching.

### 9. DASHBOARD
- Users pin key visualizations, KPI summary cards, and AI narrative blocks onto a responsive grid canvas.
- Dashboards can be auto-generated with one click from automated EDA and ML insights.

### 10. EXPORT
- One-click export of:
  - Cleaned datasets (Parquet, CSV, Excel)
  - SQL query results (CSV, JSON)
  - Visualizations (PNG, SVG)
  - Comprehensive Executive Summary Briefs (PDF with narrative analysis and key charts).

---

## 4. User Personas

1. **The Business Analyst:**
   - Wants fast, trustworthy answers without spending hours writing boilerplate Python/Pandas scripts or manual Excel cleanups.
   - Values: Automated data health detection, reliable SQL generation, and instant interactive charts.

2. **The Data Scientist:**
   - Wants rapid exploratory baseline modeling and data profiling before building production pipelines.
   - Values: Clean Parquet conversion, auditable lineage, scikit-learn model comparisons, and DuckDB SQL performance.

3. **The Executive / Founder:**
   - Wants high-level answers to strategic questions backed by verified numbers, not AI hallucinations.
   - Values: Narrative summaries, clear risk flags, and professional PDF export reports.

