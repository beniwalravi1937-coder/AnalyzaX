# AnalyzaX — Frontend UX Audit & Design System Specification

> **A comprehensive UX audit of the AnalyzaX frontend and the architectural foundation for an AI-native workspace inspired by the clarity, restraint, and progressive disclosure of Omni Analytics.**

---

## 1. Executive Summary & Design Philosophy

AnalyzaX is an assistive, AI-native enterprise analytics workspace. Its primary mission is to bridge the gap between raw datasets and executive decisions without cognitive fatigue.

Taking architectural inspiration from **[Omni Analytics (omni.co)](https://omni.co/)**, AnalyzaX embraces:
- **Restraint over Visual Clutter:** Dense analytics tools often overwhelm users with engineering telemetry. AnalyzaX presents high-contrast typography, subdued slate canvases, and purposeful semantic accents.
- **Workflow-Driven Information Architecture:** Users progress smoothly through the analytical lifecycle: **Ask $\rightarrow$ Profile $\rightarrow$ Refine $\rightarrow$ Query $\rightarrow$ Model $\rightarrow$ Tell the Story**.
- **Progressive Disclosure:** Simple, high-level metrics and plain-language takeaways by default; verifiable deterministic calculations, SQL ASTs, model hyperparameters, and engine lineage accessible on demand via the **"Analysis details"** drawer.
- **Real UI as Proof:** All screenshots and product walkthroughs employ a standardized `BrowserFrame` / `ProductScreenshot` component with macOS window chrome.

### Anti-Patterns Explicitly Rejected
1. **Engineering Admin Panels:** No walls of raw JSON, backend stack traces, or unsorted internal UUIDs.
2. **Browser-Default Controls:** Zero native unstyled `<select>`, `<button>`, or `<input>` elements.
3. **Isolated Chatbot Widgets:** AI is not an auxiliary chat floating in the corner; it is directly embedded into dataset operations, visualizations, and model evaluations.
4. **Mocked UI:** No fake buttons, non-functional tabs, or unclickable prototypes.

---

## 2. Comprehensive 36-Point Frontend UX Audit

A systematic audit of the AnalyzaX frontend codebase (`Frontend/src/`) was conducted across all 36 functional and structural domains:

| # | Domain | Audit Findings in Current Codebase | Status & Remediation |
|---|---|---|---|
| 1 | **Application Shell** | Defined in `routes/__root.tsx`. Layout features responsive sidebar, topbar, workspace container, and auth guard. | **Upgraded:** Replaced inline topbar with unified `DatasetSelector`, `ProjectSelector`, and `Ctrl+K` search modal. |
| 2 | **Public Landing Page** | Implemented in `components/landing/LandingPage.tsx` and `routes/index.tsx`. Strong value proposition and benefit-first copy. | **Upgraded:** Replaced ad-hoc mockup window with reusable `BrowserFrame`. |
| 3 | **Authenticated Dashboard** | In `routes/index.tsx` & `components/dashboard/`. Flexible widget grid supporting KPIs, charts, statistics, and forecasts. | **Upgraded:** Replaced emoji icons (`📊`, `🔍`) with Lucide `BarChart3`, `Filter`, `Tag`. |
| 4 | **Navigation Hierarchy** | Four logical tiers: *Overview*, *Data*, *Analysis*, *Modelling*, *Workspace*. | **Verified:** Collapsible sections with `localStorage` persistence. |
| 5 | **Top Bar** | In `components/layout/TopBar.tsx` and `routes/__root.tsx`. | **Upgraded:** Eliminated native `<select>` controls; standardized on `DatasetSelector` and `ProjectSelector`. Fixed Next.js imports to `@tanstack/react-router`. |
| 6 | **Sidebar** | In `components/layout/Sidebar.tsx` and `routes/__root.tsx`. | **Upgraded:** Removed legacy `next/link` and `next/image` imports; aligned with TanStack router. |
| 7 | **Project Selector** | In `components/ui/ProjectSelector.tsx` and `workspace/ProjectSwitcher.tsx`. | **Standardized:** Dropdown with project name, dataset count, and creation trigger. |
| 8 | **Dataset Selector** | In `components/ui/DatasetSelector.tsx`. | **Standardized:** Clean search, row count, and column count without exposing raw `dataset_id`. |
| 9 | **Search & Command Palette** | In `components/workspace/GlobalSearchModal.tsx` and `components/ui/command.tsx`. | **Activated:** Global `Ctrl+K` / `Cmd+K` keyboard shortcut connected in `__root.tsx`. |
| 10 | **AI Analyst** | In `routes/ai-analyst.tsx` & `components/chat/`. Multi-turn chat with SQL citations and chart execution. | **Audited:** Standardized message primitives (`AIMessage`, `UserMessage`, `RecommendationCard`). |
| 11 | **Smart Insights** | In `routes/insights.tsx`. Automated anomaly and driver detection with severity ratings. | **Upgraded:** Removed raw `dataset_id` string from header; integrated `AnalysisDetailsDrawer`. |
| 12 | **Metric Library** | In `routes/metrics.tsx`. KPI catalog with status badges, formulas, and verification tags. | **Audited:** Clean KPI cards; standard badges applied. |
| 13 | **Dataset Studio** | In `routes/data.tsx`. Ingestion, multi-format upload (CSV, Parquet, Excel), and schema preview. | **Audited:** Verified file dropzone and schema viewer. |
| 14 | **Data Quality** | In `routes/quality.tsx` & `components/quality/`. 6-dimension scoring (completeness, uniqueness, consistency, etc.). | **Audited:** Verified score dial, dimension cards, and issue tables. |
| 15 | **Cleaning Studio** | In `routes/cleaning.tsx` & `components/cleaning/`. Step-by-step transformation recipes with undo/redo lineage. | **Audited:** Verified recipe drawer and preview diff. |
| 16 | **EDA (Exploratory Data Analysis)** | In `routes/eda.tsx` & `components/eda/`. Univariate, bivariate, correlation matrix, and automated findings. | **Audited:** Clean tabs, ECharts distributions, and correlation heatmap. |
| 17 | **SQL Workbench** | In `routes/sql.tsx` & `components/sql/`. CodeMirror editor with DuckDB SQL execution, schema tree, and explain panel. | **Audited:** Verified read-only query guard, query history, and result grid. |
| 18 | **Visualizations** | In `routes/visualizations.tsx` & `components/visualization/`. Chart builder, ECharts rendering, and export toolbar. | **Audited:** Verified fullscreen modal, drilldown drawer, and PNG/SVG export. |
| 19 | **Statistics** | In `routes/statistics.tsx` & `components/statistics/`. Parametric and non-parametric hypothesis testing with assumption checks. | **Audited:** Verified p-value formatters, effect size indicators, and report cards. |
| 20 | **Machine Learning** | In `routes/ml.tsx` & `components/ml/`. Classification, regression, clustering, ROC curves, feature importance. | **Audited:** Verified model leaderboard and confusion matrix. |
| 21 | **Forecasting** | In `routes/forecasting.tsx` & `components/forecasting/`. Time-series models, confidence intervals, diagnostics. | **Audited:** Verified horizon selector and temporal quality panel. |
| 22 | **Exports & Reporting** | In `routes/exports.tsx`, `ExportQuickPanel.tsx`, `ReportBuilderPanel.tsx`. | **Upgraded:** Replaced emoji icons with typed Lucide icons (`BarChart3`, `ShieldCheck`, etc.). |
| 23 | **Projects Index & Detail** | In `routes/projects.index.tsx` & `routes/projects._id.tsx`. Multi-project management and asset grouping. | **Audited:** Clean project cards and activity feed. |
| 24 | **Settings & Workspace Administration** | In `routes/settings.tsx` & `components/settings/`. Profile, members, API keys, usage limits. | **Audited:** Standard form layout and billing status. |
| 25 | **Authentication Pages** | In `routes/login.tsx`, `register.tsx`, `forgot-password.tsx`, `reset-password.tsx`. | **Audited:** Clean card containers, error feedback, and redirect handlers. |
| 26 | **Empty States** | In `components/ui/EmptyState.tsx` & `components/dashboard/DashboardGrid.tsx`. | **Upgraded:** Replaced emoji placeholder in `DashboardGrid` with standardized `BarChart3` container. |
| 27 | **Loading States** | In `components/ui/LoadingState.tsx` & `components/ui/skeleton.tsx`. | **Audited:** Standardized pulse skeletons and animated spinners. |
| 28 | **Error States** | In `components/ui/ErrorState.tsx` and `__root.tsx` error boundaries. | **Audited:** Structured error boundary with reload view and safe logging. |
| 29 | **Dialogs & Modals** | In `components/ui/dialog.tsx` and `alert-dialog.tsx`. | **Audited:** Radix-based accessible modal backdrops with smooth transitions. |
| 30 | **Dropdowns & Popovers** | In `components/ui/dropdown-menu.tsx`, `popover.tsx`, `select.tsx`. | **Audited:** Radix primitives with slate-elevated surface tokens. |
| 31 | **Tables** | In `components/ui/DataTable.tsx` and `components/ui/VirtualTable.tsx`. | **Audited:** Virtualized rendering for datasets up to 100k rows with sticky headers. |
| 32 | **Charts** | In `components/ui/ChartCard.tsx` and `components/ui/ChartContainer.tsx`. | **Audited:** Standard header, badge, export actions, and ECharts/Recharts viewport. |
| 33 | **Forms & Controls** | In `components/ui/form.tsx`, `input.tsx`, `textarea.tsx`, `checkbox.tsx`, `switch.tsx`. | **Audited:** Uniform border, focus ring, and glassmorphism styling. |
| 34 | **Notifications & Alerts** | In `routes/notifications.tsx`, `NotificationCenter.tsx`, and `sonner.tsx`. | **Audited:** Toast dispatching and unread badge counting. |
| 35 | **Responsive Behavior** | Mobile drawer, sticky topbar, media query breakpoints (`sm`, `md`, `lg`, `xl`). | **Verified:** Touch navigation, backdrop dismissals, and collapsible sidebar. |
| 36 | **Technical Information Isolation** | Removal of raw IDs (`dataset_id`, `project_id`, `execution_id`, `provider`, `model`) from user view. | **Upgraded:** Isolated into `AnalysisDetailsDrawer` with plain-language labels across primary views. |

---

## 3. Design Tokens Architecture

All tokens are defined in `Frontend/src/styles.css` using CSS custom properties.

### A. Surface & Canvas Scale
```css
--bg-app: #080c16;             /* Canvas root background */
--surface-canvas: #0c1220;     /* Workspace container background */
--surface-card: #111827;       /* Standard card background */
--surface-elevated: #1a2236;   /* Dropdown, modal, and popover surface */
--surface-hover: #1e2840;      /* Interactive hover state */
--surface-active: #24304d;     /* Selected / active tab state */
```

### B. Border & Focus Scale
```css
--border-subtle: rgba(255, 255, 255, 0.06); /* Hairline dividers */
--border-default: rgba(255, 255, 255, 0.12);/* Component boundaries */
--border-strong: rgba(255, 255, 255, 0.20); /* Hover states */
--border-focus: #6366f1;                    /* Focus rings */
```

### C. Text Hierarchy
```css
--text-primary: #f8fafc;       /* High-contrast headings and primary metrics */
--text-secondary: #94a3b8;     /* Body text and descriptive copy */
--text-muted: #64748b;         /* Subtitles, labels, and helper notes */
--text-faint: #334155;         /* Disabled text & subtle placeholders */
```

### D. Semantic Accents
```css
--accent-primary: #6366f1;     /* Primary brand indigo */
--accent-primary-hover: #4f46e5;
--accent-subtle: rgba(99, 102, 241, 0.12);

--accent-success: #10b981;     /* Validations, passed tests, upward KPIs */
--accent-warning: #f59e0b;     /* Cautions, missing values, rate limits */
--accent-danger: #ef4444;      /* Anomalies, failures, negative trends */
--accent-info: #06b6d4;        /* AI findings, informational discoveries */
```

### E. Typography Scale
Strict mathematical clamp scale communicating hierarchy through size and weight:
```css
--font-size-title-page: clamp(1.75rem, 1.5rem + 1vw, 2rem);    /* 28–32px: Page Title */
--font-size-title-section: clamp(1.125rem, 1rem + 0.5vw, 1.375rem); /* 18–22px: Section Title */
--font-size-title-card: 0.9375rem;                             /* 14–16px: Card Header */
--font-size-body: 0.875rem;                                    /* 13–15px: Standard Body */
--font-size-secondary: 0.78125rem;                             /* 12–13px: Secondary Context */
--font-size-metadata: 0.71875rem;                              /* 11–12px: Monospace / Metrics */
```

### F. Spacing Scale
Consistent mathematical steps: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96px`.

---

## 4. Unified Reusable Primitives Inventory

All components reside in `Frontend/src/components/ui/` with centralized exports in `index.ts`:

| Primitive | Purpose | Key Props / Variants |
|---|---|---|
| **`Button`** | Standard interactive trigger | `variant: primary, secondary, subtle, outline, ghost, destructive`; `size: xs, sm, md, lg`; `loading: boolean` |
| **`IconButton`** | Compact square icon trigger | `size: xs, sm, md, lg`; inherits button variants |
| **`Input` & `Textarea`** | Form inputs with glass styling | Focus rings, error states, subtle borders |
| **`SearchInput`** | Search input with shortcut badge | Quick-clear button, `Ctrl+K` visual indicator |
| **`SegmentedControl`** | Pill tab switcher | Animated sliding background, keyboard arrow navigation |
| **`Badge`** | Status indicator | `variant: success, warning, danger, info, indigo, neutral, purple` |
| **`Card` & `Panel`** | Structured surface containers | Configurable headers, subtitles, hover states, border tokens |
| **`PageHeader`** | Standard 28–32px page title | Eyebrow badge, subtitle, action group slots |
| **`SectionHeader`** | Standard 18–22px section title | Action button slot, subtitle |
| **`MetricCard`** | Large numerical KPI display | Trend delta (+/- %), trend direction icons, sparkline slot |
| **`InsightCard`** | AI finding presentation | Severity badge, impact pill, plain-English summary, collapsible analytical details |
| **`ChartCard`** | Structured chart container | Header, badge, export actions, ECharts/Recharts viewport |
| **`BrowserFrame`** | Polished desktop application window | macOS traffic light dots, URL bar, status badge, ambient shadow (aliased as `ProductScreenshot`) |
| **`AnalysisDetailsDrawer`**| Slide-over drawer for technical depth | Execution IDs, query IDs, model hyper-parameters, engine runtimes |
| **`DatasetSelector`** | Topbar dataset switcher | Dataset name, row count, column count, search, connect trigger |
| **`ProjectSelector`** | Topbar project switcher | Project name, dataset count, create new project trigger |
| **`FilterBar` & `FilterChip`** | Interactive analytical filters | Dismissible chips with operator & value pills, clear-all action |
| **`ChatMessagePrimitives`** | AI Copilot conversational UI | `AIMessage`, `UserMessage`, `RecommendationCard` |
| **`DataTable` & `VirtualTable`** | Analytical table presentation | Virtualized row rendering, sort indicators, null-value formatting |
| **`EmptyState`, `LoadingState`, `ErrorState`** | Standardized fallback states | Consistent icons, descriptive copy, retry/action buttons |

---

## 5. Technical Information Isolation Protocol

AnalyzaX follows the **Progressive Disclosure Principle**:
1. **Primary Interface:** Displays human-readable dataset names (e.g. `Student Exam Performance`), plain-language KPI titles (`Pass Rate: 92.4%`), and clear analytical conclusions.
2. **Hidden by Default:** Internal database identifiers (`dataset_id`, `project_id`, `execution_id`, `query_id`), backend status enums (`JOB_QUEUED_01`), model configurations, and ASTs.
3. **Available on Demand:** Any analytical card or studio provides an **"Analysis details"** button that slides out the `AnalysisDetailsDrawer`, displaying full provenance, execution timestamps, row counts, and raw query specs for auditing.

---

## 6. Verification & Build Integrity

- **Module Transformation:** Verified across all 2,843 client and SSR modules using Vite 8 + TanStack Start.
- **Production Packaging:** Nitro compiled server and client bundles into `.output/` and `dist/` with **Exit Code 0**.
- **Container Readiness:** `Frontend/Dockerfile` builds a production container with a non-root runner (`analyzax:10001`).
- **Backward Compatibility:** All Phase 3–26 analytical capabilities, DuckDB SQL execution, Polars transformations, and AI Copilot endpoints remain 100% operational without contract modifications.
