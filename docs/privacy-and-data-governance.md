# AnalyzaX — Privacy & Data Governance Architecture

## 1. Overview
Data governance and customer privacy are core design pillars of AnalyzaX. The platform adheres to the principles of **Data Minimization**, **Purpose Limitation**, **Storage Limitation**, and **Accountability** (GDPR Article 5).

---

## 2. Data Classification Framework

AnalyzaX categorizes all data assets into four distinct tiers:

| Tier | Classification | Examples | Storage Location | Protection Controls |
|---|---|---|---|---|
| **Tier 1** | **Public** | Marketing documentation, public API schemas, product documentation | Git / Static web host | Integrity checks, CDN caching |
| **Tier 2** | **Internal** | Application telemetry, anonymous performance metrics, error traces | Local filesystem / TSDB | Secret redaction, log aggregation, access logging |
| **Tier 3** | **Confidential** | Customer dataset schemas, project metadata, analysis lineage records | Metadata repository / JSON | RBAC, tenant isolation, backup versioning |
| **Tier 4** | **Restricted / PII** | Customer uploaded datasets, Parquet data files, user emails, passwords, MFA secrets, DSAR exports | Encrypted storage (`/storage/`) / Auth repo | AES-256-GCM encryption, HMAC signed URLs, PBKDF2/Argon2 hashing |

---

## 3. Data Retention & Lifecycle Management

1. **Active Datasets:** Retained indefinitely while the workspace is in `ACTIVE` status.
2. **Archived Workspaces/Projects:** Retained in read-only state for 90 days following soft archival before eligible for automated purging.
3. **Session Tokens & MFA Challenges:** Session tokens expire after 24 hours of inactivity. Temporary MFA challenge tokens expire strictly after 300 seconds (5 minutes).
4. **Temporary Exports & DSR Packages:** Export zip archives and DSR bundles automatically expire and are purged from storage after 7 days.
5. **Audit Logs:** Immutable audit records are retained for a minimum of 365 days for regulatory compliance, even if the associated project or workspace is deleted.

---

## 4. Data Subject Rights (DSAR / DSR) Workflow

In compliance with GDPR (Articles 15–20) and CCPA/CPRA, data subjects can exercise their rights to access and portability:

1. **Request Submission:**
   - Authenticated users trigger:
     `POST /api/v1/governance/users/dsr-export`
2. **Package Generation (`DeletionService.generate_dsr_export`):**
   - Extracts all user profile records (email, display name, account status, timestamps).
   - Extracts workspace memberships and assigned RBAC roles.
   - Extracts author audit trails and personal activity logs.
   - Packages all metadata into a JSON archive `dsr_{user_id}_{timestamp}.json`.
3. **Secure Delivery:**
   - Stores the export package in the secure storage directory.
   - Generates a time-limited HMAC-SHA256 signed download URL (expires in 24 hours).
   - Logs the DSAR fulfillment in the immutable audit trail.

---

## 5. Right-to-be-Forgotten & Audit-Safe User Pseudonymization

Under GDPR Article 17, users may request total erasure of their personal data. However, regulatory frameworks (SOX, SOC 2, HIPAA) simultaneously require non-repudiation of financial and analytical audit trails.

AnalyzaX resolves this using **Cryptographic Pseudonymization**:

```
[ User Account Deletion Triggered ]
               │
               ▼
[ 1. Invalidate & Delete Credentials ]
- Purge password hash
- Purge TOTP secret and recovery codes
- Revoke all active sessions
               │
               ▼
[ 2. Irreversible Pseudonymization ]
- Replace email with: deleted_user_{user_id[:8]}@pseudonymized.local
- Replace display name with: [Deleted User {user_id[:8]}]
- Set user status to DELETED
               │
               ▼
[ 3. Audit Trail Preservation ]
- Existing audit logs retain actor_user_id (e.g. usr_12345)
- All PII (real email, real name, IP references) is stripped
- Historical lineage, dataset creation timestamps, and query IDs remain valid
```

This guarantees compliance with GDPR Article 17 while maintaining audit log integrity for compliance standards.
