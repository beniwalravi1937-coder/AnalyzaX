# AnalyzaX — Workspace, Project & Asset Lifecycle Architecture

This document specifies the technical design, data structures, storage mechanics, and operational policies for Phase 16: **Advanced Workspace, Project & Dataset Lifecycle Management**.

---

## 1. Architectural Overview & Boundaries

Phase 16 introduces an organizational and governance layer that sits strictly atop existing analytical engines (DuckDB, Polars, Stats, ML, Dashboards, Reports, Exports).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST Layer                              │
│  /api/v1/workspaces | /api/v1/projects | /api/v1/assets | /api/v1/search │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Application Services                            │
│    WorkspaceService | ProjectService | AssetRegistryService            │
│         SearchService | WorkspaceMigrationService                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Domain Engine & Repository                         │
│     WorkspaceRepository (Atomic File + Memory Cache with RLock)       │
│     DependencyAnalyzer  (Lineage DAG, Safe Deletions, Health)          │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Persistence Layer                               │
│       data/workspace/{workspaces,projects,assets,relationships}.json    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Entities & Contracts

### 2.1 Workspace
A Workspace is the top-level operational boundary.
- `workspace_id`: Unique identifier (e.g. `ws_default`, `ws_...`).
- `name`, `slug`, `description`: Human-readable and URL-friendly identifiers.
- `status`: `ACTIVE` or `ARCHIVED`.

### 2.2 Project
A Project is an isolated container for datasets, visualizations, dashboards, queries, and reports.
- `project_id`: Unique identifier (e.g. `proj_default`, `proj_...`).
- `workspace_id`: Parent workspace reference.
- `status`: `ACTIVE` or `ARCHIVED`.
- `settings`: Project-level configuration (e.g., query limits, defaults).

### 2.3 Asset Registry
A centralized registry tracking all first-class platform entities:
- `AssetType`: `DATASET`, `DATASET_VERSION`, `VISUALIZATION`, `QUERY`, `STATISTICAL_ANALYSIS`, `ML_EXPERIMENT`, `ML_RESULT`, `FORECAST_EXPERIMENT`, `FORECAST_RESULT`, `AI_SESSION`, `DASHBOARD`, `REPORT`, `EXPORT`.
- `source_entity_id`: Real ID in underlying engine (e.g. `ds_123`, `dash_456`).
- `status`: `ACTIVE`, `ARCHIVED`, `DELETED`.
- `tags`: Cleaned, normalized taxonomy tags.
- `is_favorite`: Quick access flag.

### 2.4 Asset Relationships & Lineage DAG
Directed, typed edges representing dependencies:
- `RelationshipType`: `DERIVED_FROM`, `USES`, `CONTAINS`, `REFERENCES`, `GENERATED_FROM`, `VISUALIZES`, `SUMMARIZES`, `EXPORTED_FROM`, `DEPENDS_ON`.
- Lineage is computed via recursive BFS downstream and upstream graph traversal.

---

## 3. Storage & Concurrency Model

All workspace state is stored under `data/workspace/`:
- `workspaces.json`: All workspace definitions.
- `projects.json`: All project definitions.
- `assets.json`: Unified asset registry.
- `relationships.json`: Directed dependency graph edges.
- `activity.json`: Audit log of user actions.

**Concurrency & Thread Safety:**
- Managed via `threading.RLock()` across all repository reads and mutations.
- Atomic file writes via Windows-resilient temporary file writing (`.tmp`) with multi-attempt `os.replace` and `shutil.copyfile` fallback to prevent file locking issues on Windows NTFS filesystems.

---

## 4. Deletion Safeguards & Lifecycle Rules

1. **Delete Safeguard Protocol:**
   - Before deleting any asset, the `DependencyAnalyzer` inspects active downstream dependents.
   - If downstream dashboards, reports, or visualizations depend on the asset, deletion is rejected (`HTTP 400`) unless `force=True` is explicitly specified.
   - The user is prompted to **Archive** instead.
2. **Reversible Dataset Archiving:**
   - Archiving marks status as `ARCHIVED` and records an audit activity.
   - Archiving preserves all raw data, Parquet files, DuckDB views, and lineage connections.
   - Restoring an archived dataset immediately returns it to `ACTIVE` status without changing its `id`.

---

## 5. Global Search Engine (`/api/v1/search`)

- Scans in-memory indexed assets across workspaces and projects.
- Ranked scoring: Exact title match (+100), title substring (+50), tag match (+30), description match (+10), recency bonus (+5).
- Parameterized filtering by `workspace_id`, `project_id`, `asset_type` / `asset_types`, `status`, `is_favorite`, and `tags`.
- Every search result includes a valid, navigable frontend route (e.g. `/dataset?id=...`, `/dashboards?id=...`, `/sql?query=...`, `/reports?id=...`).
