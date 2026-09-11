# AnalyzaX — Compliance Readiness & Standards Alignment

> [!IMPORTANT]
> **Legal Compliance & Certification Disclaimer:**
> AnalyzaX provides technical architecture, security controls, and governance features designed to support enterprise compliance readiness. This document reflects technical readiness and control alignment. It **does not** constitute, nor should it be construed as, formal legal certification or third-party audit attestation (such as an issued SOC 2 Type II report, ISO/IEC 27001 certificate, or GDPR legal seal). Formal certification requires an independent assessment of operational policies, personnel, and infrastructure by an accredited third-party auditing firm.

---

## 1. Overview
AnalyzaX is architected to align with the core security, confidentiality, processing integrity, and privacy principles outlined in **SOC 2**, **ISO/IEC 27001:2022**, and the **EU General Data Protection Regulation (GDPR)**.

---

## 2. SOC 2 Trust Services Criteria (TSC) Mapping

| TSC Category | Control Objective | AnalyzaX Technical Control Implementation | Verification Artifact |
|---|---|---|---|
| **CC6.1 (Logical Access)** | Multi-factor authentication & session control | RFC 6238 TOTP MFA, signed challenges, 24-hr session lifetime, instantaneous session revocation | `engines/auth/mfa.py`, `test_phase24_mfa_and_auth.py` |
| **CC6.2 (User Registration & Access)** | Role-based authorization & least privilege | 4 hierarchical roles (OWNER, ADMIN, EDITOR, VIEWER), project/workspace scope boundaries | `engines/auth/permissions.py`, `test_phase24_tenant_isolation_and_idor.py` |
| **CC6.3 (Revocation of Access)** | Immediate suspension of compromised users | `UserStatus.SUSPENDED`, session cache purge, cascading revocation | `services/auth/auth_service.py` |
| **CC6.6 (Boundary Protection)** | Network segregation, SSRF, and perimeter defense | `SSRFGuard` with DNS rebinding defenses, loopback/private IP blocking, secure headers (HSTS, CSP) | `engines/security/ssrf_guard.py`, `middleware/security.py` |
| **CC6.7 (Data Transmission)** | Cryptographic protection in transit | Enforced TLS 1.3, HTTPS redirection, HSTS headers (`max-age=63072000; includeSubDomains`) | `core/middleware/security.py` |
| **CC7.1 (Vulnerability & Threat Mgmt)** | Input validation & execution sandboxing | Strict AST SQL validation, DuckDB 4GB/4-thread sandboxing, disabled external access | `engines/sql/validator.py`, `engines/sql/executor.py` |
| **CC7.2 (Security Monitoring)** | Comprehensive audit logging | Append-only, tamper-resistant audit logs tracking actor, IP, timestamp, and diff summary | `engines/collaboration/audit_log.py` |
| **PI1.1 (Processing Integrity)** | Accurate, deterministic calculation | Deterministic analytical engines (DuckDB, Polars, SciPy), zero LLM math hallucination | `AGENTS.md` Rule 4, Phase 8/10 engines |
| **C1.1 (Confidentiality)** | Tenant data isolation | Universal IDOR defense across all 14 resource domains, path traversal rejection | `services/auth/authorization_service.py`, `api/v1/storage.py` |

---

## 3. ISO/IEC 27001:2022 Annex A Controls Alignment

| ISO 27001 Control | Control Name | Implemented Technical Architecture |
|---|---|---|
| **A.5.15** | Access control | Default-deny RBAC model enforced in middleware and application dependencies. |
| **A.8.7** | Protection against malware | File upload magic-byte inspection rejecting binary executables (PE/ELF/Mach-O) and active scripts. |
| **A.8.9** | Configuration management | DuckDB `lock_configuration = true`, preventing query-level privilege escalation. |
| **A.8.12** | Data leakage prevention | AI Analyst untrusted delimiter escaping and automatic secret redaction (API keys, passwords). |
| **A.8.20** | Network security | SSRF protection layer blocking internal subnet discovery and cloud metadata endpoints. |
| **A.8.24** | Use of cryptography | AES-256-GCM envelope encryption with HKDF key derivation and zero-downtime rotation. |
| **A.8.26** | Application security requirements | Automated security audit script (`scripts/security_audit.py`) validating CIS/OWASP baselines. |

---

## 4. GDPR Article 25 & 32 Compliance Readiness Matrix

| GDPR Article | Requirement | Technical Implementation |
|---|---|---|
| **Article 25 (Data Protection by Design & Default)** | System defaults to minimum exposure; personal data not accessible without authorization. | - Multi-tenant isolation by default.<br>- Storage URLs require cryptographic HMAC signatures.<br>- Raw datasets never sent to third-party LLMs. |
| **Article 32 (Security of Processing)** | Pseudonymization and encryption of personal data; confidentiality, integrity, availability. | - Envelope encryption (AES-256-GCM) at rest.<br>- In-memory DuckDB query sandboxing.<br>- Resource isolation and rate limiting. |
| **Article 17 (Right to Erasure)** | Obligation to delete personal data without undue delay. | - `/api/v1/governance/users/delete-account` endpoint executes irreversible pseudonymization.<br>- Credentials purged, names replaced with anonymous tokens, audit trails preserved without PII. |
| **Article 20 (Right to Data Portability)** | Provide personal data in a structured, commonly used, machine-readable format. | - `/api/v1/governance/users/dsr-export` endpoint generates structured JSON data package of user activity, profile, and memberships. |
| **Article 33 (Data Breach Notification)** | Ability to detect, investigate, and notify within 72 hours. | - Immutable audit logs provide forensic tracing of all data reads and modifications. |
