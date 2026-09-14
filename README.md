<div align="center">

<img src="logo.png" alt="AnalyzaX Logo" width="160" style="filter: drop-shadow(0 10px 30px rgba(59,130,246,0.5));" />

# AnalyzaX
### The Autonomous AI Data Analytics & Engineering Platform

**Deterministic Data Intelligence • Zero Numerical Hallucinations • Enterprise-Grade Analytical Engines**

<p align="center">
  <a href="https://analyzaxab-vp.vercel.app/" target="_blank">
    <img src="https://img.shields.io/badge/🚀_LIVE_PRODUCTION_WORKSPACE-OPEN_APP-0070F3?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Demo" />
  </a>
  <a href="https://analyzaxab-vp.vercel.app/" target="_blank">
    <img src="https://img.shields.io/badge/📱_MOBILE_%26_DESKTOP-READY-10B981?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Mobile Ready" />
  </a>
  <a href="https://github.com/beniwalravi1937-coder/AnalyzaX" target="_blank">
    <img src="https://img.shields.io/badge/GITHUB-STAR_REPOSITORY-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />
  </a>
</p>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![DuckDB](https://img.shields.io/badge/DuckDB-v1.5.5-FFF000.svg?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Polars](https://img.shields.io/badge/Polars-Columnar-CD792C.svg?style=for-the-badge&logo=polars&logoColor=white)](https://pola.rs)
[![Next.js](https://img.shields.io/badge/Next.js-14_App_Router-black.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![TanStack](https://img.shields.io/badge/TanStack-Router_%26_Start-FF4154.svg?style=for-the-badge&logo=react-query&logoColor=white)](https://tanstack.com)
[![Apache ECharts](https://img.shields.io/badge/ECharts-5.5+-AA344D.svg?style=for-the-badge&logo=apacheecharts&logoColor=white)](https://echarts.apache.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-AutoML-F7931E.svg?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<br/>

<table>
  <tr>
    <td align="center" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 22px; border-radius: 12px; border: 1px solid #334155;">
      <h3>⚡ Instant Cloud Access — No Installation Required</h3>
      <p style="font-size: 15px; margin: 10px 0;">
        Experience AnalyzaX's complete autonomous analytics workspace live on web & mobile:
      </p>
      <a href="https://analyzaxab-vp.vercel.app/" target="_blank">
        <img src="https://img.shields.io/badge/👉_LAUNCH_ANALYZAX_LIVE_DASHBOARD-https%3A%2F%2Fanalyzaxab--vp.vercel.app-0070F3?style=for-the-badge&logo=vercel&logoColor=white" alt="Launch Live Dashboard" height="42" />
      </a>
      <p style="font-size: 13px; color: #94a3b8; margin-top: 10px; margin-bottom: 0;">
        ✅ Live Interactive Demo &nbsp;|&nbsp; 📱 iOS & Android Optimized &nbsp;|&nbsp; ⚡ Sub-Second Vectorized DuckDB Analytics
      </p>
    </td>
  </tr>
</table>

<br/>

<p align="center">
  <a href="https://analyzaxab-vp.vercel.app/"><b>🚀 Launch Live App</b></a> •
  <a href="#-live-cloud-workspace--mobile-access">Cloud Workspace</a> •
  <a href="#-key-features--capabilities">Key Features</a> •
  <a href="#-why-analyzax-the-paradigm-shift">Why AnalyzaX?</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-the-analyzax-constitution-agentsmd">Constitution</a>
</p>

---

</div>

##  Overview

**AnalyzaX** is a next-generation autonomous data analytics platform engineered to bridge the gap between raw, messy enterprise datasets and production-ready decision intelligence.

Unlike naive LLM wrappers that paste raw data into chat prompts and hallucinate calculations, AnalyzaX operates on a fundamental principle:

> **"Deterministic software calculates numbers. Intelligent AI reasons over verified facts."**

AnalyzaX orchestrates **11 high-performance analytical engines** (powered by DuckDB, Polars, SciPy, statsmodels, and scikit-learn) with an **autonomous LLM Copilot** equipped with 16 analytical tools. The result is an end-to-end analytics workflow from ingestion and quality audit to SQL analytics, AutoML, forecasting, and interactive visualizations.

```text
Raw Dataset ➔ Ingestion & Parquet ➔ 6D Quality Audit ➔ Lineage Cleaning ➔ Vectorized SQL ➔ EDA & Stats ➔ AutoML ➔ Forecasting ➔ AI Analyst Copilot ➔ Executive Dashboards & Exports
```

---

## 🌐 Live Cloud Workspace & Mobile Access

AnalyzaX is deployed to production and accessible directly in your web or mobile browser:

<div align="center">

| 🚀 **Direct Production URL** | 📱 **Supported Formats** | ⚡ **Cloud Deployment** |
| :---: | :---: | :---: |
| [**`https://analyzaxab-vp.vercel.app`**](https://analyzaxab-vp.vercel.app/) | Mobile (iOS / Android), Tablet, Desktop | Vercel Edge Global Network |

</div>

<br/>

| Module | Live Features & Capabilities | Engine |
| :--- | :--- | :--- |
| 📊 **Dataset Profiling** | Schema inference, null ratios, cardinality scoring, memory footprint | **Polars** |
| 🛡️ **6D Quality Audit** | Automated scoring across Completeness, Uniqueness, Validity, Consistency, Timeliness, Accuracy | **Vectorized Profiler** |
| 🧹 **Data Cleaning & Lineage** | Detect ➔ Explain ➔ Suggest ➔ Approve ➔ Apply recipe lineage DAG with before/after diffs | **Polars Lineage** |
| ⚡ **DuckDB SQL Studio** | Sandboxed in-browser SQL editor, schema explorer, execution time, result grid | **DuckDB** |
| 📈 **Exploratory Data Analysis** | Univariate distributions, skewness, quantiles, bivariate Pearson/Spearman correlation matrices | **Polars + SciPy** |
| 🔬 **Statistical Hypothesis Lab** | Independent & Paired t-tests, One-way ANOVA, Mann-Whitney U, Chi-Square contingency | **SciPy + statsmodels** |
| 🧠 **AutoML Studio** | Classification & regression benchmarks, ROC/AUC, Precision-Recall curves, Feature Importance | **scikit-learn** |
| 🔮 **Time-Series Forecasting** | ADF/KPSS stationarity tests, seasonal decomposition, ARIMA & Holt-Winters ETS projections | **statsmodels** |
| 🤖 **Autonomous AI Copilot** | Conversational assistant with 16 analytical tools to inspect, query, chart, and explain data | **Multi-Tool Agent** |
| 📱 **Mobile Responsive Design** | Optimized touch interactions, collapsible navigation drawers, dark-mode native layout | **Tailwind + TanStack** |

> [!TIP]
> **Mobile Web App:** AnalyzaX is fully responsive. On iOS Safari tap **Share ➔ Add to Home Screen** or on Android Chrome tap **Settings ➔ Add to Home screen** to install AnalyzaX as a standalone PWA dashboard.

---

##  Why AnalyzaX? The Paradigm Shift

Traditional analytics tools force teams to choose between manual BI dashboard fatigue, steep SQL learning curves, or risky generative AI tools that hallucinate statistics.

| Feature | Naive AI Analytics / Chatbots | Traditional BI Tools (Tableau, PowerBI) | **AnalyzaX Platform** |
| :--- | :--- | :--- | :--- |
| **Numerical Accuracy** | ❌ Hallucinates averages, correlations, sums | ✅ Deterministic (rigid calculations) | 🛡️ **100% Deterministic (DuckDB + Polars)** |
| **Data Privacy** | ❌ Sends entire datasets to external LLMs | 🔒 On-premise / cloud DB | 🔒 **Zero raw data sent to LLMs (Aggregated context only)** |
| **Transformation Lineage**| ❌ Ephemeral & untraceable | ⚠️ Complex ETL dependencies | 📜 **Immutable DAG Versioning & Cleaning Recipes** |
| **Interactive SQL** | ❌ Blind text generation | ⚠️ Manual syntax authoring | ⚡ **AST-Sandboxed DuckDB Vectorized Workbench** |
| **Machine Learning** | ❌ Non-existent | ❌ Requires data science team | 🧠 **Built-in AutoML (Auto-detection, Train/Test, ROC/AUC)** |
| **Forecasting** | ❌ Guesses future trends | ⚠️ Basic trendline extrapolations | 🔮 **Statistical ARIMA, ETS & Stationarity Tests** |
| **User Interface** | ❌ Chat text only | ⚠️ Heavy, dated enterprise UIs | 🎨 **Modern Dual Frontend (Next.js & TanStack/Lovable)** |

---

##  Architecture

AnalyzaX strictly enforces a **4-tier layered architecture** separating presentation, routing, application orchestration, domain computation engines, and data storage.

```mermaid
flowchart TD
    subgraph Presentation[" Presentation Layer (Dual Frontend)"]
        FE1["Next.js 14 Enterprise (App Router)"]
        FE2["Frontend_Lovable (TanStack Start & Router)"]
    end

    subgraph Transport[" Transport & Routing (FastAPI)"]
        API["FastAPI REST & SSE Router (/api/v1)"]
        CORS["Security & CORS Middleware"]
    end

    subgraph Services[" Application Services"]
        SVC1["Dataset Service"]
        SVC2["SQL Query Service"]
        SVC3["Data Quality Service"]
        SVC4["AutoML & Forecasting Service"]
        SVC5["AI Analyst Copilot Service"]
    end

    subgraph Engines[" 11 Deterministic Analytical Engines"]
        E1["Ingestion Engine (MIME, Parquet)"]
        E2["Profiling Engine (Column Types, Stats)"]
        E3["Quality Engine (6D Audit, Anomaly)"]
        E4["Cleaning Engine (Diffs, Lineage DAG)"]
        E5["SQL Engine (DuckDB, AST Parser)"]
        E6["EDA Engine (Polars Distributions)"]
        E7["Statistics Engine (SciPy Tests)"]
        E8["ML Engine (scikit-learn AutoML)"]
        E9["Forecasting Engine (ARIMA, ETS)"]
        E10["Visualization Engine (Chart Advisor)"]
        E11["Export Engine (PDF, Excel, Parquet)"]
    end

    subgraph Data[" Storage & Execution Layer"]
        DuckDB[("DuckDB Vectorized In-Memory / File")]
        Polars["Polars High-Performance DataFrames"]
        Postgres[("PostgreSQL Metadata & DAG")]
        Filesystem["Immutable Parquet Filesystem Storage"]
    end

    Presentation --> API
    API --> CORS
    CORS --> Services
    Services --> Engines
    Engines --> Data
```

---

##  Key Features & Capabilities

### 1.  Ingestion & Columnar Profiling
- Multi-format ingestion: CSV, Excel (`.xlsx`), JSON, Parquet, and TSV.
- Automatic schema inference, null detection, cardinality scoring, memory footprint estimation, and zero-copy conversion to versioned Parquet storage.

### 2.  6-Dimensional Data Quality Engine
Audits datasets across 6 foundational quality dimensions:
- **Completeness**: Missing values, null ratios, and column drop thresholds.
- **Uniqueness**: Primary key candidate detection and duplicate row tracking.
- **Validity**: Type conformance, regex compliance, and format detection.
- **Consistency**: Conflicting values across cross-dependent fields.
- **Timeliness**: Temporal freshness, interval gaps, and datetime validation.
- **Accuracy**: Z-Score, IQR, and Isolation Forest statistical outlier detection.

### 3.  Interactive Cleaning & Immutable Lineage
- **The Analytical Handshake**: *Detect ➔ Explain ➔ Suggest ➔ Approve ➔ Apply ➔ Log*.
- Step-by-step transformation recipes with before-and-after preview diffs.
- Immutable dataset versioning (`v1`, `v2`, `v3`) with complete audit trails and undo capabilities.

### 4.  Vectorized DuckDB SQL Workbench
- Sub-millisecond SQL analytics powered by **DuckDB**.
- **AST Security Sandboxing**: Analyzes SQL queries at the AST level to enforce read-only execution, prevent injections, and block dangerous filesystem commands.
- Interactive schema tree, query execution statistics (run time, scanned rows, memory bytes), and tabular data grid.

### 5.  Polars Exploratory Data Analysis & Statistics
- Ultra-fast univariate distribution metrics (skewness, kurtosis, quantiles).
- Bivariate correlation matrices (Pearson, Spearman, Kendall) computed via Polars.
- Hypothesis testing suite: Independent Student's t-test, Paired t-test, One-way ANOVA, Mann-Whitney U, and Chi-Square contingency analysis.

### 6.  Autonomous AI Analyst Copilot
- Equipped with **16 deterministic tools** to inspect schemas, execute sandboxed SQL, request statistical tests, run chart recommendations, and generate forecasts.
- Context-bounded prompt assembler that prevents token bloat and never sends raw row dumps to LLMs.
- Streams real-time insights, explanations, and follow-up query suggestions.

### 7.  Machine Learning Studio (AutoML)
- Automated task detection: Binary Classification, Multi-class Classification, and Regression.
- Automated feature preprocessing: One-hot encoding, target imputation, standard scaling.
- Benchmark leaderboards comparing Logistic Regression, Random Forest, Gradient Boosting, Ridge, and Lasso.
- Production evaluation curves: Confusion Matrices, ROC/AUC, Precision-Recall curves, and Feature Importance rankings.

### 8.  Time-Series Forecasting
- Automated datetime column resolution and frequency detection (hourly, daily, weekly, monthly).
- Augmented Dickey-Fuller (ADF) and KPSS stationarity testing.
- Seasonal decomposition (Trend, Seasonal, Residual) and ARIMA/ETS forecasting with confidence intervals.

### 9.  Chart Advisor & Apache ECharts Builder
- AI-assisted chart recommendation based on variable types, distributions, and cardinalities.
- Produces declarative Apache ECharts specifications: Bar, Line, Scatter, Heatmap, Boxplot, Radar, Treemap, and Candlestick.
- Responsive, dark-mode native, and interactive zoom/pan controls.

### 10.  Multi-Format Export Center
- Export cleaned datasets to Parquet, Excel (with auto-formatted tabs and headers), or CSV.
- Download production executive PDF analytical briefs complete with summary KPIs, data quality scorecards, and high-resolution chart snapshots.

---

##  Unified Frontend Architecture

AnalyzaX features a single, unified enterprise-grade frontend workspace:

```
Frontend/                         # Unified Vite + TanStack Router & Start Workspace
├── src/routes/                   # File-based declarative routing with loaders & auth protection
├── src/components/               # Glassmorphic UI with Omni-inspired design tokens
│   ├── ui/                       # Centralized 25+ primitives (buttons, modals, cards, etc.)
│   └── workspace/                # Domain-specific analytical studios & inspectors
└── src/services/                 # Typed FastAPI client SDK & real-time WebSocket bindings
```

- **`Frontend/`**: Ultra-fluid modern analytical workspace built with TanStack Router, Vite, dynamic responsive animations, Radix UI primitives, Apache ECharts, and seamless dark-mode aesthetics.

---

##  The AnalyzaX Constitution (AGENTS.md)

Every line of code in AnalyzaX adheres to strict architectural principles:

1. **Never Expose Secrets:** Zero credentials, tokens, or encryption keys in logs or git.
2. **Never Send Raw Datasets to LLMs:** Context windows receive only metadata, summaries, and SQL aggregates.
3. **Zero Numerical Calculations in LLMs:** AI plans and explains; DuckDB, Polars, and SciPy compute.
4. **Data Immutability:** Raw uploads are never mutated; transformations create traceable lineage nodes.
5. **Strict Layer Separation:** Routes handle HTTP ➔ Services coordinate ➔ Engines calculate ➔ Storage persists.
6. **AST SQL Validation:** All user or AI-generated SQL is rigorously sandboxed before execution.
7. **14-Point Global Quality Gate:** Every phase must pass functional, performance, security, and automated test gates.

---

##  Technology Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance asynchronous REST API & SSE streaming |
| **Data Engine (SQL)** | [DuckDB](https://duckdb.org/) | Vectorized in-process analytical SQL database engine |
| **Data Engine (Columnar)**| [Polars](https://pola.rs/) | Multithreaded Rust-backed columnar DataFrame processing |
| **Data Engine (Legacy)** | [Pandas](https://pandas.pydata.org/) | Interoperability & serialization bridge |
| **Machine Learning** | [scikit-learn](https://scikit-learn.org/) | Automated classification, regression, and model evaluation |
| **Statistics & Time-Series**| [SciPy](https://scipy.org/) & [statsmodels](https://www.statsmodels.org/) | Hypothesis testing, distribution analysis, ARIMA/ETS forecasting |
| **Frontend Framework (1)**| [Next.js 14](https://nextjs.org/) | Enterprise React framework with App Router |
| **Frontend Framework (2)**| [TanStack Router](https://tanstack.com/) & [Vite](https://vitejs.dev/) | High-speed reactive client with fluid micro-interactions |
| **UI Styling** | [Tailwind CSS](https://tailwindcss.com/) & [shadcn/ui](https://ui.shadcn.com/) | Accessible, modern, dark-mode design system |
| **Data Visualization** | [Apache ECharts](https://echarts.apache.org/) | Interactive, performant charting engine |
| **Metadata Database** | [PostgreSQL](https://www.postgresql.org/) + [SQLAlchemy](https://www.sqlalchemy.org/) | Workspace boundaries, lineage DAG, user profiles |
| **AI LLM Gateway** | [OpenRouter](https://openrouter.ai/) / LiteLLM | Multi-model LLM abstraction layer with strict tool calling |
| **Containerization** | [Docker](https://www.docker.com/) & Docker Compose | Multi-container staging and production deployment |

---

##  Quickstart

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** (or Bun)
- **Git**
- *(Optional)* Docker & Docker Compose

### 1. Clone the Repository
```bash
git clone https://github.com/beniwalravi1937-coder/AnalyzaX.git
cd AnalyzaX
```

### 2. Configure Environment
```bash
# Copy the template configuration
cp .env.example .env
```

### 3. Start the Backend
```bash
# Create and activate virtual environment
python -m venv backend/.venv

# Windows:
.\backend\.venv\Scripts\Activate.ps1
# Linux/macOS:
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Launch FastAPI analytical server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: **`http://127.0.0.1:8000/docs`**

### 4. Start the Frontend
```bash
cd Frontend
npm install
npm run dev
```
Visit **`http://localhost:3000`**

### 5. One-Command Docker Deployment
```bash
docker-compose up --build
```

---

##  API Reference

AnalyzaX exposes a RESTful API with automated OpenAPI / Swagger documentation:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/health` | `GET` | System status, DuckDB version, and engine diagnostics |
| `/api/v1/datasets/upload` | `POST` | Upload raw dataset (CSV, Parquet, Excel, JSON) |
| `/api/v1/datasets/{id}/profile` | `GET` | Structural, semantic, and statistical column profiling |
| `/api/v1/quality/{id}/audit` | `GET` | 6D Data Quality score and anomaly report |
| `/api/v1/cleaning/{id}/recipes` | `POST` | Apply transformation recipe and create versioned lineage |
| `/api/v1/sql/query` | `POST` | Execute AST-sandboxed DuckDB SQL query with timing |
| `/api/v1/eda/{id}/summary` | `GET` | Column distributions, skewness, and correlations |
| `/api/v1/statistics/{id}/test` | `POST` | Execute parametric and non-parametric hypothesis tests |
| `/api/v1/ml/{id}/train` | `POST` | Train AutoML benchmark models and compute ROC/confusion metrics |
| `/api/v1/forecasting/{id}/forecast` | `POST` | Run ARIMA / ETS time-series decomposition and forecast |
| `/api/v1/ai-analyst/chat` | `POST` | Natural language queries with autonomous tool orchestration |
| `/api/v1/exports/{id}/pdf` | `GET` | Download compiled executive PDF intelligence report |

Explore the interactive API explorer at `http://127.0.0.1:8000/docs`.

---

##  Master Roadmap

- [x] **Phase 0: Architecture & Constitution** (System specs, AGENTS.md, schema contracts)
- [x] **Phase 1: Foundation & Health** (FastAPI app, DuckDB in-process engine, health diagnostics)
- [x] **Phase 2: Frontend Shell & Workspaces** (Responsive multi-page layout, theme tokens)
- [x] **Phase 3: High-Speed Ingestion** (MIME sniffing, zero-copy Parquet conversion)
- [x] **Phase 4: Columnar Profiling** (Type inference, null ratios, descriptive stats)
- [x] **Phase 5: 6D Data Quality Engine** (Anomaly detection, quality radar score)
- [x] **Phase 6: Interactive Cleaning & Lineage** (Transformation recipes, before/after diffs)
- [x] **Phase 7: Automated EDA & Statistics** (Polars correlation heatmaps, hypothesis suite)
- [x] **Phase 8: DuckDB SQL Studio** (AST sandboxing, schema tree, query cache)
- [x] **Phase 9: Chart Advisor & ECharts** (AI visualization recommendations, interactive charts)
- [x] **Phase 10: AI Copilot Architecture** (OpenRouter integration, streaming transport)
- [x] **Phase 11: 16-Tool AI Analyst Agent** (Natural language to verified SQL, insights synthesis)
- [x] **Phase 12: AutoML Studio** (Automated classification, regression, model leaderboards)
- [x] **Phase 13: Time-Series Forecasting** (Stationarity testing, seasonal decomposition, ARIMA)
- [x] **Phase 14: Executive Dashboards** (Interactive analytical widgets, KPI scorecards)
- [x] **Phase 15: Multi-Format Export Center** (Executive PDF reports, multi-tab Excel, Parquet)
- [ ] **Phase 16: Multi-Tenant Enterprise Auth** (OAuth2, RBAC, workspace isolation)
- [ ] **Phase 17: Security Hardening** (Penetration audit, advanced rate-limiting)
- [ ] **Phase 18: Out-of-Core 100M+ Row Benchmarks** (Polars streaming optimization)
- [ ] **Phase 19: Kubernetes & Cloud Helm Charts** (Cloud-native production deployment)

---

##  Contributing

Contributions make the open-source community an incredible place to learn, inspire, and create:

1. **Fork** the project
2. **Create** your feature branch (`git checkout -b feature/AmazingFeature`)
3. **Verify** all test suites pass (`pytest backend/tests`)
4. **Commit** your changes (`git commit -m 'feat: add AmazingFeature'`)
5. **Push** to the branch (`git push origin feature/AmazingFeature`)
6. **Open** a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">

**Built with precision for the future of data intelligence.**

 **Star this repository if AnalyzaX helped accelerate your analytics workflow!** ⭐

</div>
