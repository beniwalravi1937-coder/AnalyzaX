# AnalyzaX — STRIDE Security Threat Model

## Executive Summary
This document defines the formal Threat Model for **AnalyzaX**, an AI-powered end-to-end data analytics SaaS platform. The system operates on a **Default-Deny** and **Secure-by-Default** posture across all layers: multi-tenant authentication, RBAC authorization, DuckDB analytical sandboxing, object storage signed URLs, upload validation, network SSRF defenses, cryptographic envelope key management, and LLM prompt boundary isolation.

---

## 1. System Architecture & Trust Boundaries

```
[ Public Internet / Untrusted Clients ]
                  │
                  ▼ [ Trust Boundary 1: Transport & Network Gateway ]
    TLS 1.3 / HTTPS / HSTS / Reverse Proxy / Rate Limiter
                  │
                  ▼ [ Trust Boundary 2: FastAPI Application Tier ]
  Authentication (MFA, Sessions) & Authorization (RBAC / Scopes / IDOR Defenses)
                  │
                  ├──────────────────────┬──────────────────────┐
                  ▼                      ▼                      ▼
  [ Trust Boundary 3 ]          [ Trust Boundary 4 ]    [ Trust Boundary 5 ]
  DuckDB Analytical Sandbox     Storage & Cryptography  AI Analyst / LLM
  - Memory: 4GB ceiling         - AES-256-GCM (HKDF)    - Untrusted Delimiter Escaping
  - Threads: 4 max              - HMAC-SHA256 Signed    - API Key & Secret Redaction
  - enable_external_access=0      Storage URLs          - Data Minimization (Summaries)
  - lock_configuration=1        - Safe Path Containment - Read-Only DuckDB Execution
```

### Trust Boundary Descriptions:
1. **TB-1 (Perimeter / Transport):** Demarcates external untrusted clients from the web application gateway. Enforces TLS 1.3, CSP, CORS origin whitelisting, IP rate-limiting, and request size boundaries.
2. **TB-2 (Application / Access Control):** Separates unauthenticated/untrusted request payloads from tenant business logic. Enforces RFC 6238 TOTP MFA, signed challenges, universal 14-resource-domain IDOR authorization checks, and step-up auth for sensitive actions.
3. **TB-3 (Analytical Execution Sandbox):** Isolates arbitrary, user-controlled SQL execution within in-memory DuckDB instances. Filesystem reading, network access, internal catalogs (`duckdb_*`, `information_schema`), and configuration alterations are locked.
4. **TB-4 (Object Storage & Cryptographic Layer):** Separates raw storage files from direct client downloads. Direct paths are strictly forbidden; downloads require time-limited HMAC-SHA256 signed URLs validated at request time. At-rest encryption uses AES-256-GCM envelope encryption with HKDF key derivation and rotation.
5. **TB-5 (AI Analyst & External Providers):** Separates customer datasets from third-party LLMs. Raw rows are never transmitted; prompts are sanitized, secrets are redacted, and SQL generation is treated as hostile input.

---

## 2. STRIDE Threat Catalog & Implemented Mitigations

| Category | Threat ID | Threat Description | Attack Vector | Implemented Mitigation | Validation |
|---|---|---|---|---|---|
| **Spoofing** | T-S01 | Credential Stuffing & Account Takeover | Replay stolen passwords | RFC 6238 TOTP MFA, ±1 drift window, signed challenge tokens, single-use SHA-256 recovery codes, IP/account rate limits | `test_phase24_mfa_and_auth.py` |
| **Spoofing** | T-S02 | Tenant Context Spoofing | Client sends forged `X-Workspace-Id` or spoofed UUID | Server-side `AuthorizationService` resolves user identity strictly from cryptographic session token and verifies tenant membership | `test_phase24_tenant_isolation_and_idor.py` |
| **Tampering** | T-T01 | DuckDB Sandbox Escape & Reconfiguration | Attacker issues `SET enable_external_access = true;` | DuckDB `SET lock_configuration = true;` executed before running user query; forbids any runtime setting mutation | `test_phase24_sql_security.py` |
| **Tampering** | T-T02 | Malicious Polyglot & Executable Upload | Attacker uploads PE/ELF executable or SVG with embedded JS renamed to `.csv` | Magic byte inspection (`MZ`, `\x7fELF`, `\xca\xfe\xba\xbe`), dangerous script extension blocking (`.exe`, `.sh`, `.bat`, `.svg`, `.html`), and zip bomb limits | `test_phase24_upload_and_ssrf.py` |
| **Tampering** | T-T03 | Download URL Tampering | Attacker tampers with signed download URL query parameters | Cryptographic HMAC-SHA256 signature verification over path, expiry timestamp, and signature; rejects any modified parameters | `test_phase24_storage_and_exports.py` |
| **Repudiation** | T-R01 | Untracked Destructive Actions | Admin denies deleting workspace or purging sensitive project | Immutable, append-only audit trail logs actor ID, action type, IP address, timestamp, and diff summary for every modification | `test_phase24_crypto_and_deletion.py` |
| **Information Disclosure** | T-I01 | Cross-Tenant IDOR on Assets | User in Tenant B queries Tenant A dataset ID | Universal IDOR defense across all 14 resource types. `authorization_service.can()` validates resource ownership and workspace containment | `test_phase24_tenant_isolation_and_idor.py` |
| **Information Disclosure** | T-I02 | SSRF via External Dataset Import | Attacker imports `http://169.254.169.254/latest/meta-data/` or internal IPs | `SSRFGuard` validates scheme, checks loopback, private RFC 1918, link-local, cloud metadata, and resolves DNS to detect rebinding | `test_phase24_upload_and_ssrf.py` |
| **Information Disclosure** | T-I03 | Storage Path Traversal | Attacker requests `../../../../etc/passwd` via storage download | `storage_service` validates `os.path.abspath` containment within `settings.DATA_STORAGE_ROOT`, rejecting traversal sequences | `test_phase24_storage_and_exports.py` |
| **Information Disclosure** | T-I04 | AI Prompt Injection & Secret Leak | User prompt contains delimiter injection to reveal API keys or system prompts | AI prompt sanitizer replaces `"""` and delimiter sequences with safe tokens; regex engine redacts OpenAI, Anthropic, Bearer tokens, and DB URLs | `test_phase24_golden_security.py` |
| **Information Disclosure** | T-I05 | Data at Rest Interception | Stolen hard disk or raw storage dump reveals plain text | Envelope encryption using AES-256-GCM, HKDF-SHA256 derived keys, key versioning, and zero-downtime key rotation | `test_phase24_crypto_and_deletion.py` |
| **Denial of Service** | T-D01 | DuckDB Resource Exhaustion / OOM | Malicious query generates infinite Cartesian join | `SET max_memory = '4GB';`, `SET threads = 4;`, strict row limits (`max_rows=10000`), and thread execution watchdog with timeout cancellation | `test_phase24_sql_security.py` |
| **Denial of Service** | T-D02 | Decompression Bomb (Zip Bomb) | Attacker uploads tiny archive that expands to hundreds of gigabytes | `IngestionDetector` enforces 100x uncompressed expansion ratio limit and 500MB absolute ceiling during zip decompression | `test_phase24_upload_and_ssrf.py` |
| **Elevation of Privilege** | T-E01 | Admin Workspace Deletion Hijack | Compromised Admin member attempts to permanently delete workspace | RBAC policy strictly reserves `WORKSPACE_DELETE` to the `OWNER` role only; Admins and Editors are rejected with 403 Forbidden | `test_phase24_tenant_isolation_and_idor.py` |

---

## 3. Defense-in-Depth Summary

AnalyzaX implements minimum 3 independent defensive barriers for every critical operation:
1. **Network Layer:** IP rate limiting, TLS 1.3, SSRF resolution filters, and strict CORS.
2. **Application Tier:** Session validation, TOTP challenge verification, and RBAC matrix enforcement.
3. **Execution Engine:** AST parsing, forbidden keyword/table blocking, memory limits, and locked DuckDB sandbox configurations.
