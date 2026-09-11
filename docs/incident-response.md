# AnalyzaX — Security Incident Response Plan (IRP)

## 1. Purpose & Incident Response Philosophy
This document establishes the official **Incident Response Plan** for AnalyzaX. The primary goal of incident response is to contain threats rapidly, minimize customer impact, protect multi-tenant data confidentiality, preserve forensically sound evidence, and systematically eliminate root causes.

---

## 2. Severity Classification Framework

| Severity | Definition | Target Initial Response | Target Resolution | Escalation Path |
|---|---|---|---|---|
| **P1 — Critical** | Active cross-tenant data leak (IDOR), unauthorized remote code execution, active database compromise, or catastrophic data loss across multiple tenants. | < 15 minutes | < 2 hours | Head of Engineering, Lead Security Architect, Legal Counsel, CEO |
| **P2 — High** | Account takeover of an organization admin, failure of DuckDB sandbox restrictions, unverified privilege escalation, or production outage impacting customer security controls. | < 30 minutes | < 6 hours | Lead Security Engineer, Backend Core Team, Customer Success Lead |
| **P3 — Medium** | Flaw in rate limiting, suspicious automated probing without exploitation, SSRF probe stopped by defense-in-depth, or non-exploitable configuration deviation. | < 2 hours | < 24 hours | On-call Security Engineer, Core Developer |
| **P4 — Low** | Low-risk dependency vulnerability without exploit pathway, minor audit log formatting inconsistency, or non-sensitive telemetry warning. | < 24 hours | < 5 business days | Assigned Engineering Sprint Team |

---

## 3. Incident Lifecycle Phases

```
   ┌───────────────────────────────────────────────────────────┐
   │                    1. Preparation                         │
   │  Hardened Sandboxes, Immutable Audit Logs, Golden Tests   │
   └─────────────────────────────┬─────────────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │           2. Detection, Triage & Analysis                 │
   │  Alert Monitors, Security Audit CLI, Anomaly Telemetry    │
   └─────────────────────────────┬─────────────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │                   3. Containment                          │
   │  Token Revocation, Account Suspension, Network Isolation   │
   └─────────────────────────────┬─────────────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │                    4. Eradication                         │
   │  Vulnerability Patching, Secret Rotation, Cache Purge     │
   └─────────────────────────────┬─────────────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │                     5. Recovery                           │
   │  Integrity Verification, Controlled Canary Release        │
   └─────────────────────────────┬─────────────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │                 6. Post-Incident Review                   │
   │  Blameless Post-Mortem, ADR Documentation, New Tests      │
   └───────────────────────────────────────────────────────────┘
```

---

## 4. Specific Incident Runbooks

### Runbook 1: Cross-Tenant Data Leak (IDOR / Scope Breach)
1. **Identification:**
   - Review audit logs for atypical asset query patterns (`GET /api/v1/workspaces/{id}`, `/api/v1/projects/{id}`, or `/api/v1/storage/download`).
   - Identify actor ID, tenant ID, and source IP addresses.
2. **Immediate Containment:**
   - Immediately terminate active sessions for the compromised actor:
     ```python
     auth_service.revoke_all_user_sessions(user_id)
     ```
   - If a broader API route lacks authorization enforcement, temporarily deploy emergency hotfix or block the endpoint via gateway rules.
3. **Forensic Assessment:**
   - Query immutable audit repository for all read events executed by the actor within the incident timeframe.
   - Compile exact list of leaked datasets, project IDs, and metadata accessed.
4. **Notification:**
   - If customer personal or confidential data was exposed, notify the Data Protection Officer (DPO) and affected tenant owners within 72 hours per GDPR Art. 33/34 requirements.
5. **Eradication & Regression Prevention:**
   - Commit strict authorization checks in the affected router.
   - Add targeted test case to `tests/test_phase24_tenant_isolation_and_idor.py`.

---

### Runbook 2: Credential / API Key Compromise & Revocation
1. **Identification:**
   - An API key, master encryption secret, or service token is detected in logs, committed to Git, or reported by a researcher.
2. **Immediate Rotation:**
   - For Master Encryption Secret (`DATA_ENCRYPTION_MASTER_KEY`):
     - Generate a new 32-byte secret.
     - Add new key as `v2` in `KeyManager`.
     - Run background re-encryption job using `KeyManager.rotate_ciphertext()`.
   - For LLM / Third-party API keys:
     - Generate new key in provider console.
     - Update environment variable in container deployment.
     - Invalidate compromised key in provider console.
3. **Audit & Verification:**
   - Search audit logs for unauthorized LLM invocations or decryption attempts during the exposure window.

---

### Runbook 3: Account Takeover (ATO) & MFA Invalidation
1. **Identification:**
   - Rapid succession of failed login attempts followed by sudden password change and MFA reset, or user-reported unauthorized access.
2. **Immediate Containment:**
   - Suspend user account immediately (`UserStatus.SUSPENDED`).
   - Revoke all active session tokens in `AuthRepository`.
   - Invalidate existing TOTP secrets and recovery codes.
3. **Identity Verification & Restoration:**
   - Verify user identity through secondary out-of-band channel.
   - Reset password hash with high-entropy temporary token.
   - Require immediate MFA re-enrollment upon next login.

---

### Runbook 4: Data Corruption & Cascading Deletion Recovery
1. **Identification:**
   - Accidental or malicious execution of cascading workspace deletion or corrupting transformation.
2. **Assessment:**
   - Check `AuditLog` to confirm whether deletion was triggered via `/api/v1/governance/workspaces/{id}/delete`.
   - Verify cold backup status of Parquet files in object storage.
3. **Restoration:**
   - Restore Parquet artifacts from immutable, versioned backup storage.
   - Replay dataset version metadata records up to point-in-time of corruption.
