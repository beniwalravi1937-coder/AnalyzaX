# AnalyzaX — Security & Multi-User Authorization Architecture (Phase 17)

This document provides the authoritative specification for Authentication, Authorization, Session Management, Role-Based Access Control (RBAC), and Tenant Isolation in **AnalyzaX**.

---

## 1. Core Architectural Principles

1. **Server-Authoritative Security:** All authentication and authorization decisions are enforced by backend Application Services and Engine guards. Frontend checks (e.g., `ProtectedRoute`, hidden UI buttons) are purely for user experience and never serve as security boundaries.
2. **Deterministic Identity & Cryptography:** 
   - Passwords are never stored in plaintext.
   - Hashing uses standard Python library `hashlib.scrypt` with OWASP-recommended parameters:
     - CPU/memory cost parameter $N = 16384$ ($2^{14}$)
     - Block size parameter $r = 8$
     - Parallelization parameter $p = 1$
     - Cryptographically secure random 16-byte hex salt per user
   - Password and token verification uses constant-time comparison (`hmac.compare_digest`) to prevent timing side-channel attacks.
3. **Session State Security:**
   - Raw session tokens generated via `secrets.token_urlsafe(32)`.
   - The backend stores only cryptographic SHA-256 hashes of session tokens (`token_hash`). If the session database is compromised, active session tokens cannot be recovered.
   - Dual-transport support: `analyzax_session` HttpOnly, SameSite=Lax cookie AND `Authorization: Bearer <token>` header.
4. **Owner Protection:**
   - A workspace must always retain at least one active `OWNER`.
   - The system strictly forbids deleting, removing, or downgrading the role of the last active owner of any workspace.
5. **Universal IDOR Resolution:**
   - Client-provided identifiers (workspace IDs, project IDs, dataset IDs, version IDs, dashboard IDs, query IDs, export IDs) are validated against user workspace and project memberships through `AuthorizationService.can()`.
   - Foreign asset lookups cross-reference the centralized asset registry (`find_asset_by_source_id`), ensuring cross-tenant boundaries cannot be bypassed via direct object references.

---

## 2. Role-Based Access Control (RBAC) Model

AnalyzaX implements 5 distinct hierarchical roles:

| Role | Description | Core Capabilities |
|---|---|---|
| **OWNER** | Full administrative and destructive authority over workspace. | Workspace deletion/transfer, member role management, security audit logs, billing, all data/ML/export capabilities. |
| **ADMIN** | Workspace operational administrator. | Invite/manage non-owner members, project management, dataset deletion, all data/ML/export capabilities. |
| **EDITOR** | Core data creator and pipeline editor. | Dataset upload, cleaning, profiling, transformation, model training, dashboard editing, SQL execution. |
| **ANALYST** | Read and query specialist. | Run read-only SQL, generate charts, run EDA, run AI chat queries, export analytical reports. Cannot mutate core pipelines or datasets. |
| **VIEWER** | Read-only stakeholder. | View dashboards, view reports, inspect dataset summaries. Cannot run ad-hoc SQL, cannot train models, cannot export raw datasets. |

### Complete Permission Matrix

```
┌───────────────────────────┬────────┬───────┬────────┬─────────┬────────┐
│ Permission                │ OWNER  │ ADMIN │ EDITOR │ ANALYST │ VIEWER │
├───────────────────────────┼────────┼───────┼────────┼─────────┼────────┤
│ workspace:read            │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
│ workspace:update          │   ✓    │   ✓   │   -    │    -    │   -    │
│ workspace:delete          │   ✓    │   -   │   -    │    -    │   -    │
│ workspace:members:read    │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
│ workspace:members:manage  │   ✓    │   ✓   │   -    │    -    │   -    │
│ workspace:roles:assign    │   ✓    │   -   │   -    │    -    │   -    │
│ workspace:audit:read      │   ✓    │   ✓   │   -    │    -    │   -    │
│ project:create            │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ project:read              │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
│ project:update            │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ project:delete            │   ✓    │   ✓   │   -    │    -    │   -    │
│ dataset:read              │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
│ dataset:create            │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ dataset:update            │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ dataset:delete            │   ✓    │   ✓   │   -    │    -    │   -    │
│ dataset:profile           │   ✓    │   ✓   │   ✓    │    ✓    │   -    │
│ dataset:clean             │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ sql:execute               │   ✓    │   ✓   │   ✓    │    ✓    │   -    │
│ ml:train                  │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ ml:predict                │   ✓    │   ✓   │   ✓    │    ✓    │   -    │
│ dashboard:view            │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
│ dashboard:edit            │   ✓    │   ✓   │   ✓    │    -    │   -    │
│ ai:query                  │   ✓    │   ✓   │   ✓    │    ✓    │   -    │
│ export:data               │   ✓    │   ✓   │   ✓    │    ✓    │   -    │
│ export:report             │   ✓    │   ✓   │   ✓    │    ✓    │   ✓    │
└───────────────────────────┴────────┴───────┴────────┴─────────┴────────┘
```

---

## 3. Session Lifecycle & Dual-Transport Architecture

```mermaid
sequenceDiagram
    participant Browser as Client Browser
    participant API as FastAPI /auth/login
    participant Engine as AuthEngine & Repo
    participant Storage as File / DB Storage

    Browser->>API: POST /api/v1/auth/login {email, password}
    API->>Engine: RateLimiter check (account & IP)
    API->>Engine: Verify user scrypt hash
    Engine->>Engine: Generate token = secrets.token_urlsafe(32)
    Engine->>Engine: Compute hash = SHA-256(token)
    Engine->>Storage: Store Session {token_hash, user_id, expires_at}
    API-->>Browser: Set-Cookie: analyzax_session=<token>; HttpOnly; SameSite=Lax
    API-->>Browser: 200 OK {user, token, workspace_id, project_id}

    Note over Browser,API: Subsequent Authenticated Requests
    Browser->>API: GET /api/v1/auth/me (Cookie: analyzax_session or Authorization: Bearer)
    API->>Engine: Extract raw token -> SHA-256 hash -> Lookup active session
    Engine->>API: Valid session & user context
    API-->>Browser: 200 OK {user, workspace_memberships, permissions}
```

### Revocation Capabilities
1. **Single Session Revocation:** Users can revoke specific remote sessions by session ID.
2. **Bulk Revocation:** `revoke_all_user_sessions(user_id, except_session_id)` allows revoking all other devices while maintaining the active session.
3. **Password Change Termination:** Changing password automatically invalidates all existing sessions across all devices for security.

---

## 4. Phase 1–16 Historical Asset Migration

To preserve 100% backward compatibility with all datasets, versions, models, queries, and reports created in Phases 1–16:
- On startup lifespan execution, `AuthMigrationService` deterministically checks for the default workspace `ws_default` and default project `proj_default`.
- Creates or confirms the initial system administrator:
  - User ID: `usr_initial_admin`
  - Email: `admin@analyzax.local`
  - Display Name: `System Administrator`
  - Password (deterministic initial bootstrap): `AdminPassword123!`
  - Workspace Membership: `ws_default` with role `OWNER`
- Associates all existing Phase 1–16 assets (549+ assets) with `usr_initial_admin`.
- The bootstrap is idempotent and runs safely without duplicate entries or data mutation.

---

## 5. Security Audit Logging

All authentication and sensitive access control events are recorded via `SecurityAuditService` into `data/auth/security_audit.json`:
- **Recorded Event Types:**
  - `USER_REGISTERED`
  - `USER_LOGIN`
  - `USER_LOGIN_FAILED`
  - `USER_LOGOUT`
  - `PASSWORD_CHANGED`
  - `PASSWORD_RESET_REQUESTED`
  - `PASSWORD_RESET_COMPLETED`
  - `SESSION_REVOKED`
  - `MEMBER_ADDED`
  - `MEMBER_ROLE_UPDATED`
  - `MEMBER_REMOVED`
  - `ACCESS_DENIED`
- **Sanitization & Redaction:** Event metadata filters out passwords, raw tokens, password reset secrets, and private dataset contents.
- **Auditing Context:** Every entry includes `actor_user_id`, `ip_address`, `user_agent`, `target_resource_id`, and `created_at` timestamp.

---

## 6. Phase 24 Enterprise Hardening & Governance Additions

Phase 24 elevates AnalyzaX to an enterprise-ready, compliance-aligned security posture:

1. **Multi-Factor Authentication (MFA):**
   - RFC 6238 TOTP engine with ±1 time-step drift tolerance.
   - 10 single-use cryptographic recovery codes stored as irreversible SHA-256 hashes.
   - HMAC-SHA256 signed ephemeral challenge tokens (5-minute TTL) bridging password verification and MFA completion.
   - Sensitive operational step-up re-authentication (`POST /api/v1/auth/step-up`).

2. **DuckDB Analytical Sandboxing & Containment:**
   - Strict resource limits: `SET max_memory = '4GB'`, `SET threads = 4`.
   - Complete external lockdown: `SET enable_external_access = false` and `SET lock_configuration = true`.
   - Parquet datasets pre-loaded into isolated in-memory tables before locking.
   - Lexical and AST blocking of internal catalogs (`duckdb_*`, `information_schema`).

3. **Upload Defense & Decompression Bombs:**
   - Binary executable rejection via magic bytes (`MZ`, `\x7fELF`, `\xca\xfe\xba\xbe`).
   - Dangerous script extension blocking (`.exe`, `.sh`, `.bat`, `.svg`, `.html`, `.php`).
   - Zip bomb containment: 100x uncompressed expansion ratio ceiling, 500MB max decompressed size.

4. **Network SSRF Guard:**
   - `SSRFGuard` validates URL schemes (HTTP/HTTPS only), rejects credentials in URLs.
   - Blocks private RFC 1918 networks, loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`, `fe80::/10`), and cloud metadata IP (`169.254.169.254`).
   - Resolves DNS to detect and prevent DNS rebinding attacks.

5. **Cryptographic Storage & Signed URLs:**
   - Time-limited HMAC-SHA256 signed download URLs (`/api/v1/storage/download`).
   - Strict path containment preventing directory traversal outside `DATA_STORAGE_ROOT`.
   - Download-time authorization checking dataset read permissions.

6. **Envelope Cryptography (AES-256-GCM):**
   - HKDF-SHA256 key derivation from master secret with context-specific salts.
   - Authenticated ciphertext format: `v1:{nonce}:{ciphertext_and_tag}`.
   - Zero-downtime key rotation mechanism re-encrypting data with target key versions.

7. **Data Governance, DSAR & GDPR Right-to-be-Forgotten:**
   - Safe cascading workspace deletion (`POST /api/v1/governance/workspaces/{id}/delete`), restricted to `OWNER`.
   - User account deletion with irreversible cryptographic pseudonymization, preserving non-repudiable audit trails.
   - Automated Data Subject Access Request (DSAR) export bundle generation (`POST /api/v1/governance/users/dsr-export`).

