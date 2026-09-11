# AnalyzaX — Phase 25: AI Product Intelligence, Autonomous Analytics & AI Copilot

## 1. Executive Summary
Phase 25 marks the evolutionary transition of AnalyzaX from a passive question-answering assistant into an intelligent, proactive analytical platform. The platform features an **AI Copilot**, a **Proactive Insight Intelligence Engine**, and a governed **Semantic / Metrics Layer**, while rigorously upholding the core development constitution: **the LLM is strictly an orchestration and synthesis layer, never computing numerical or deterministic results directly.**

---

## 2. Architectural Layering Discipline
The Copilot architecture strictly maintains the platform's multi-tier boundary:

```text
User Interaction (Web UI / Copilot Studio / Insight Center / Metrics Catalog)
   │
   ▼
FastAPI API Endpoints (/api/v1/ai/copilot, /api/v1/ai/insights, /api/v1/metrics)
   │
   ▼
Application Services (CopilotService, InsightService, SemanticService)
   │
   ▼
AI & Semantic Engines (Copilot, Workflows, Narratives, Detector, Ranker, AST Parser)
   │
   ▼
Deterministic Analytical Engines (DuckDB, Polars, Statsmodels, Scikit-Learn)
   │
   ▼
Data Storage & Execution Layer (Parquet, DuckDB instances, Local file repositories)
```

---

## 3. Core Subsystems

### 3.1 AI Copilot (`backend/app/engines/ai_copilot/`)
- **Intent Dispatch:** Automatically classifies user intent into:
  - `build_dashboard`: Deterministic multi-component dashboard planning.
  - `analytical_story`: Cross-engine narrative generation with non-causal guardrails.
  - `multi_step_investigation`: Controlled multi-step agentic workflow execution.
  - `general_query`: Semantic term resolution and grounding.
- **Context Engine:** Assembles bounded metadata, schema summaries, recent analytical memory, and active metrics within strict token budgets.
- **Analytical Memory:** Scoped isolation (`USER`, `WORKSPACE`, `PROJECT`, `SESSION`) with automatic credential scrubbing (Bearer tokens, API keys, private keys).
- **Model Router:** Policy-based routing mapping task complexity to optimal models (e.g. `anthropic/claude-3-haiku` for classification, `anthropic/claude-3.5-sonnet` for synthesis) and estimating per-request costs.

### 3.2 Proactive Insight Engine (`backend/app/engines/insights/`)
- **Signal Detector:** Deterministically detects signals across four analytical domains:
  - *Data Quality:* Degradation below threshold (score < 75.0) and severe missingness (>= 25%).
  - *Advanced EDA:* Strong collinear correlations (|r| >= 0.70) and distribution outliers (> 0 count).
  - *Statistical Engine:* Hypothesis test significance (p-value < 0.05).
  - *Forecasting & Trends:* Directional break deviations.
- **Multi-Criteria Ranker:** Calibrates priority scores (0–100) based on effect size, significance, and evidence completeness, categorizing into `CRITICAL`, `WARNING`, and `INFO`.
- **Evidence Graph:** Connects each insight to underlying analytical objects (`dataset_version`, `statistical_result`, `quality_metric`, `chart`).
- **Staleness Tracking:** Automatically marks insights `STALE` when new dataset versions are committed.

### 3.3 Controlled Multi-Step Workflows (`backend/app/engines/ai_copilot/workflows.py`)
- Executes analytical sequences step-by-step.
- **Human-in-the-Loop Approval Gates:** Consequential or mutating actions (`propose_cleaning`, `apply_cleaning`, `create_dashboard`, `delete_dataset`) automatically pause execution into `WAITING_FOR_APPROVAL` state until explicit user confirmation.
- Original uploaded datasets remain strictly immutable.

### 3.4 Multi-Tone Narratives & Causality Guard (`backend/app/engines/ai_copilot/narratives.py`)
- Generates tailored analytical narratives across three personas:
  - `EXECUTIVE`: High-level strategic briefing focusing on bottom-line impacts and trends.
  - `ANALYST`: Actionable diagnostic summary highlighting segment variations.
  - `TECHNICAL`: In-depth methodological notes detailing assumptions and statistical p-values.
- **CausalityGuard:** Enforces observational integrity by sanitizing unjustified causal terms (`"caused by"`, `"leads to"`) to associative phrasing (`"is associated with"`, `"correlates with"`).

---

## 4. Evaluation & Safety Framework
- **AnswerValidator:** Verifies that numeric claims and percentage figures cite valid tool evidence.
- **PromptInjectionDetector:** Detects and defuses prompt injection attempts (`"ignore instructions"`, `"system prompt"`, `"reveal api key"`).
- **TenantIsolationValidator:** Strictly enforces workspace boundary isolation, rejecting cross-workspace context or data access.

---

## 5. Frontend Interfaces
1. **`/insights` (Insight Center):** Comprehensive discovery center with metric filters, severity tags, and interactive evidence graph viewers.
2. **`/metrics` (Governed Metrics Catalog):** Reusable business metrics management with live formula validation, preview calculation, and versioning.
3. **`/ai-analyst` (AI Copilot Studio):** Dual-mode interface supporting interactive Copilot discussions with live tool status badges, suggested next steps, and classical analytical inquiry.
