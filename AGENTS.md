# AnalyzaX — Development Constitution (AGENTS.md)

This document defines the non-negotiable operational, architectural, and behavioral rules for all human developers and autonomous AI agents contributing to **AnalyzaX**. Adherence to this constitution is mandatory across all phases of the project.

---

## 1. Core Development Rules

1. **Never expose secrets:** Never print, log, return in API responses, or commit API keys, database credentials, tokens, or encryption keys.
2. **Never commit API keys or sensitive `.env` files:** All secret management must rely exclusively on environment variables loaded via secure configurations and `.env.example` templates.
3. **Never send entire raw datasets to an LLM unnecessarily:** Always operate on metadata, schema information, sampled rows, aggregated summaries, statistical metrics, or SQL execution results. Data privacy and context window efficiency are foundational.
4. **Never use an LLM for deterministic numerical calculations:** The LLM must NEVER compute averages, correlations, quantiles, p-values, loss functions, metrics, or forecasts. All calculations must be performed by deterministic analytical engines (DuckDB, Polars, SciPy, statsmodels, scikit-learn).
5. **Never silently modify original datasets:** Raw uploaded datasets are immutable artifacts. Any transformation, imputation, or cleaning creates a new version with an auditable lineage record.
6. **Every transformation must be traceable:** Every data transformation operation must record its author, timestamp, operational parameters, rows/columns before and after, diff summary, and rationale.
7. **Every analytical result must be reproducible:** Given a dataset version and a query, algorithm, or model seed, analytical outcomes must produce identical results across runs.
8. **AI-generated SQL must be validated:** Treat all LLM-generated SQL as untrusted, potentially hostile input. Run it through strict AST parsing and security validation before execution in an isolated, read-only DuckDB engine.
9. **Backend logic must not live inside frontend code:** The frontend is strictly a presentation and interaction layer. Business logic, data transformations, engine orchestrations, and analytics must live on the backend.
10. **Analytical logic must not live inside API routes:** FastAPI routes are thin orchestration and routing layers. Routes delegate to Application Services, which in turn coordinate domain Engines.
11. **Every major feature requires tests:** No engine, service, or critical transformation can be introduced without accompanying unit and integration tests.
12. **Test before declaring a feature complete:** A phase or feature is only complete when all test suites pass, error boundaries are validated, and requirements are satisfied.
13. **Verify important frontend behavior in a browser:** Frontend components, visualizations, and reactive workflows must be visually and functionally validated, ensuring charts render cleanly and responsive states behave predictably.
14. **Avoid unnecessary dependencies:** Evaluate every new library against existing capabilities in Polars, DuckDB, FastAPI, and standard Python/TypeScript packages. Keep dependencies minimal, lean, and auditable.
15. **Do not create fake functionality:** Never mock or simulate core analytical results to make a feature appear functional. Either implement the real deterministic computation or mark the phase as pending.
16. **Do not pretend unfinished functionality is complete:** Document missing edge cases, limitations, and future steps honestly. Never declare a phase complete if deliverables are stubbed.
17. **Preserve backward compatibility where possible:** Ensure schema migrations, dataset formats, lineage records, and API contracts do not break existing projects or dataset versions.
18. **Document important architectural decisions:** Any structural deviation, engine swap, or critical schema evolution must be documented in `docs/` with an architectural decision record (ADR).

---

## 2. Architectural Layering Discipline

Every code contribution must respect the strict four-tier backend hierarchy:

```
[API Routes] (backend/app/api/)
      │  Handles HTTP / WebSocket transport, auth, request validation
      ▼
[Services]   (backend/app/services/)
      │  Coordinates workflows, transactions, jobs, and cross-engine logic
      ▼
[Engines]    (backend/app/engines/)
      │  Pure domain logic: Ingestion, Profiling, Cleaning, SQL, EDA, ML, AI
      ▼
[Data / Storage / Execution Layer]
         DuckDB, Polars, PostgreSQL, Parquet filesystem
```

- **Routes** MUST NOT query databases directly or execute SQL queries.
- **Engines** MUST NOT know about HTTP requests, cookies, or FastAPI dependencies.
- **Engines** MUST be pure, deterministic Python modules with explicit inputs and outputs.

---

## 3. The Analytical Handshake (Human-in-the-Loop)

AnalyzaX is an assistive analyst, not an uncontrolled autonomous agent:
- High-impact data modifications (e.g., column drop, outlier trimming, imputation) MUST follow the **Detect → Explain → Suggest → Approve → Apply → Log** protocol.
- Automated suggestions must always be accompanied by a clear human-readable explanation and impact assessment.

---

## 4. Phase Execution Policy

- Development is executed strictly phase by phase according to `docs/roadmap.md`.
- Never skip phases without explicit user consent and an updated ADR in `docs/`.
- Phase 0 is limited to planning, architecture, schemas, and constitutions. Actual implementation begins only in Phase 1 upon user sign-off.

---

## 5. Global Acceptance Standard (Defined in Phase 0)

Every phase automatically inherits and must satisfy this 14-point Global Acceptance Standard. Individual phases define **only phase-specific criteria** (e.g., AC-01, AC-02) and do not repeat generic test, browser, or security boilerplate.

### The 14 Universal Quality Gates:

1. **Functional correctness:** All implemented functionality works end-to-end. No fake buttons, placeholder behavior, mocked success states, or stubbed flows presented as complete.
2. **Automated testing:** Comprehensive unit tests for domain engines, integration/API tests for services/routes, and regression test suites for all previously completed phases.
3. **Golden-path E2E:** The complete user journey for the phase must function from UI presentation through backend processing and back to presentation.
4. **Browser verification:** Important user-facing workflows must be verified in a real browser (checking loading, empty, success, and error states, responsiveness, and clean rendering).
5. **Data integrity:** Never silently corrupt, overwrite, or mutate source data. Preserve dataset/version isolation and lineage.
6. **Security:** Validate all external/user-controlled inputs. Prevent injection, path traversal, arbitrary code execution, unauthorized access, and unsafe resource usage. Never expose secrets.
7. **Performance & resource limits:** Enforce bounded memory, query timeouts, row limits, and pagination/sampling.
8. **Error handling:** Fail explicitly and safely. Return structured error objects; never silently fall back to fake or incorrect results.
9. **Observability:** Structured logging for critical operations and failures without logging secrets or raw datasets.
10. **API contracts:** Validate request/response schemas, maintain backward compatibility, and use consistent status codes.
11. **Architecture boundaries:** Strictly maintain separation between Presentation, Routes, Services, Engines, and Data layers.
12. **Documentation:** Keep architecture/API documentation, ADRs, and roadmaps up to date.
13. **No unnecessary dependencies:** Add dependencies only when strictly justified; leverage existing tools.
14. **Completion gate:** A phase is **NOT COMPLETE** if critical tests fail, the golden path fails, browser verification fails, or any data integrity/security requirement is violated.

### Standards Division Matrix:

| Requirement | Phase-specific? | Location |
|---|---:|---|
| Unit/integration tests | No | Phase 0 (Global Standard) |
| Browser verification | No | Phase 0 (Global Standard) |
| Golden-path E2E | No | Phase 0 (Global Standard) |
| Security baseline | No | Phase 0 (Global Standard) |
| Performance baseline | No | Phase 0 (Global Standard) |
| Regression testing | No | Phase 0 (Global Standard) |
| Error handling baseline | No | Phase 0 (Global Standard) |
| API contract discipline | No | Phase 0 (Global Standard) |
| Documentation | No | Phase 0 (Global Standard) |
| Data integrity baseline | No | Phase 0 (Global Standard) |
| Phase-specific functionality | **Yes** | Individual phase |
| Phase-specific security constraints | **Yes** | Individual phase |
| Phase-specific performance limits | **Yes** | Individual phase |
| Phase-specific UX behavior | **Yes** | Individual phase |
| Phase-specific acceptance criteria | **Yes** | Individual phase |

