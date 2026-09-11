# AnalyzaX — Disaster Recovery, Backup & Business Continuity Plan

This document establishes the official Disaster Recovery (DR), backup retention, cryptographic verification, and restore execution runbook for **AnalyzaX**.

---

## 1. Executive Objectives

| Objective | Target | Operational Boundary |
|---|---|---|
| **Recovery Point Objective (RPO)** | **$\le$ 1 hour** | Maximum permissible loss of data in a catastrophic disaster. Backups and write-ahead logs must execute on an hourly or continuous basis. |
| **Recovery Time Objective (RTO)** | **$\le$ 30 minutes** | Maximum allowable elapsed time from incident declaration until the platform is fully restored, verified, and serving customer traffic. |
| **Integrity Assurance** | **SHA-256 Checksums** | All archive files must be accompanied by cryptographic hash manifests. Corrupted or altered archives are rejected. |
| **Non-Destructive Storage Rule** | **Zero Silent Data Loss** | Original uploaded datasets and processed versions are immutable artifacts. Restores must never silently overwrite newer clean data without explicit operator confirmation. |

---

## 2. Backup Topology & Data Classification

AnalyzaX partitions operational state into three tiers:

### Tier 1: Immutable Analytical Artifacts (`data/uploads/`, `data/processed/`)
- Contains raw customer datasets (CSV, Parquet, JSON, Excel) and transformed versions.
- **RPO:** 0 (Original datasets are immutable once committed).
- **Strategy:** Replicated continuously to durable cloud object storage (`S3StorageProvider` or off-site MinIO mirror).

### Tier 2: Relational Metadata & RBAC (`PostgreSQL` / `DuckDB`)
- Contains user accounts, workspaces, projects, roles, permissions, audit events, and usage meters.
- **RPO:** $\le 1$ hour.
- **Strategy:** Daily full backups via `scripts/backup.py` plus PostgreSQL Write-Ahead Log (WAL) archiving.

### Tier 3: Operational Ephemeral State (`data/jobs/`, `data/temp/`)
- Asynchronous job execution states and transient cache files.
- **RPO:** Not applicable (Jobs are idempotent and re-executable).
- **Strategy:** Recovered automatically by `LocalDurableQueue` upon service reboot; stale temp files purged by `StorageCleanupService`.

---

## 3. Automated Backup Execution

Backups are executed using `scripts/backup.py`:

```bash
# Automated daily backup with 7-day retention rotation
python scripts/backup.py --dest /backups/daily --keep 7
```

### Generated Artifacts
Every backup run creates:
1. `analyzax_backup_YYYYMMDD_HHMMSS.tar.gz` — Gzip-compressed archive of all storage root assets (excluding ephemeral `.tmp` and socket locks).
2. `analyzax_backup_YYYYMMDD_HHMMSS.tar.gz.sha256` — Cryptographic SHA-256 checksum manifest.

---

## 4. Disaster Recovery & Restore Runbook

When a host failure, storage volume loss, or database corruption incident occurs, follow this sequence:

### Step 1: Incident Assessment & Quarantine
1. Isolate the damaged environment by removing it from the load balancer pool.
2. Put Nginx into maintenance mode if the API cannot serve requests:
   ```bash
   touch /var/run/analyzax.maintenance
   ```

### Step 2: Archive Integrity Verification
Before any restore begins, verify that the selected backup archive has not suffered bit-rot or tampering:
```bash
python scripts/restore.py /backups/daily/analyzax_backup_20260910_120000.tar.gz --verify-only
```
- If the SHA-256 checksum matches, the script outputs `Checksum verification PASSED`.
- If a discrepancy is detected, the script terminates immediately with a critical alert. Never proceed with a corrupted archive.

### Step 3: Safe Restoration to Storage Root
Restore the verified archive into the target persistent volume:
```bash
python scripts/restore.py /backups/daily/analyzax_backup_20260910_120000.tar.gz --target /app/data
```

### Step 4: Run Versioned Migrations
Verify database schema versioning and apply any pending migrations:
```bash
python -m backend.app.core.migrations.runner
```

### Step 5: Execute Automated Smoke Test
Run the non-destructive production smoke test:
```bash
python scripts/smoke_test.py --url http://localhost:8000
```

### Step 6: Route Production Traffic
Re-enable Nginx upstream routing and verify operational metrics on `/metrics` and `/api/v1/health`.

---

## 5. Split-Brain & Dual-Write Conflict Resolution

In multi-region or failover situations where two instances simultaneously accepted writes:
1. **Lineage Invariance:** AnalyzaX dataset versions are indexed by UUID and SHA-256 hash. Because versions are content-addressed and append-only, conflicting versions never overwrite each other.
2. **Usage & Quotas:** The usage ledger records events idempotently using `event_id`. Duplicate events are automatically deduplicated by `usage_service.record_usage()`.
3. **Audit Trail:** In case of dual-write discrepancies, query `audit_log` with timestamps to reconstruct chronological operator sequence.

---

## 6. Periodic DR Drilling Cadence

To guarantee that backup and restore capabilities remain functional:
- **Monthly:** Automated restoration drill of the latest backup into an isolated staging environment.
- **Quarterly:** Simulated total node loss drill measuring actual RTO against the 30-minute target.
- **Bi-annual:** Verification of offsite S3 bucket encryption keys, access policies, and lifecycle rules.
