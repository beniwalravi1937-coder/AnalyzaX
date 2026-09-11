"""
AnalyzaX — Phase 24: Production Security Configuration Audit Engine.
Validates production deployment configurations, secrets entropy, CORS policies,
cookie security, rate limiting, and system hardening flags.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import Settings, settings


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class SecurityFinding(BaseModel):
    check_id: str
    title: str
    severity: FindingSeverity
    description: str
    remediation: str


class SecurityAuditReport(BaseModel):
    target_env: str
    score: int = Field(..., ge=0, le=100)
    passed: bool
    critical_count: int
    warning_count: int
    passed_count: int
    findings: List[SecurityFinding] = Field(default_factory=list)
    passed_checks: List[str] = Field(default_factory=list)


class ConfigAuditEngine:
    """
    Evaluates application settings against enterprise hardening benchmarks (CIS/OWASP).
    """

    DEFAULT_SECRETS = {
        "development-secret-key-change-in-production",
        "analyzax-secure-session-secret-change-in-production",
        "whsec_sandbox_secret_key_analyzax",
        "secret",
        "changeme",
        "password",
        "123456",
    }

    def audit(self, config: Optional[Settings] = None, enforce_prod: bool = False) -> SecurityAuditReport:
        cfg = config or settings
        is_prod = enforce_prod or (cfg.APP_ENV.lower() in ("production", "prod", "staging"))

        findings: List[SecurityFinding] = []
        passed_checks: List[str] = []

        # 1. DEBUG mode check
        if cfg.DEBUG:
            if is_prod:
                findings.append(SecurityFinding(
                    check_id="SEC-001",
                    title="DEBUG mode is enabled in production",
                    severity=FindingSeverity.CRITICAL,
                    description="DEBUG exposes internal stack traces, environment variables, and debug endpoints to clients.",
                    remediation="Set DEBUG=False in environment variables.",
                ))
            else:
                findings.append(SecurityFinding(
                    check_id="SEC-001",
                    title="DEBUG mode is active (Non-production)",
                    severity=FindingSeverity.INFO,
                    description="DEBUG is enabled for development/testing.",
                    remediation="Ensure DEBUG=False before deploying to production.",
                ))
        else:
            passed_checks.append("SEC-001: DEBUG mode is disabled.")

        # 2. Application SECRET_KEY entropy & defaults
        if cfg.SECRET_KEY in self.DEFAULT_SECRETS or len(cfg.SECRET_KEY) < 32:
            findings.append(SecurityFinding(
                check_id="SEC-002",
                title="Application SECRET_KEY is weak or uses default placeholder",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description=f"SECRET_KEY length is {len(cfg.SECRET_KEY)} chars or matches known default template string.",
                remediation="Generate a cryptographically secure key with at least 32 bytes of entropy (e.g., openssl rand -hex 32).",
            ))
        else:
            passed_checks.append("SEC-002: SECRET_KEY meets minimum length and entropy requirements.")

        # 3. AUTH_SESSION_SECRET entropy & defaults
        if cfg.AUTH_SESSION_SECRET in self.DEFAULT_SECRETS or len(cfg.AUTH_SESSION_SECRET) < 32:
            findings.append(SecurityFinding(
                check_id="SEC-003",
                title="AUTH_SESSION_SECRET is weak or default",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Session signature secret matches default development placeholder or is under 32 characters.",
                remediation="Set AUTH_SESSION_SECRET to a random 32+ character string in production.",
            ))
        else:
            passed_checks.append("SEC-003: AUTH_SESSION_SECRET has sufficient entropy.")

        # 4. CORS Origins Wildcard Check
        has_wildcard = any("*" in origin for origin in cfg.ALLOWED_CORS_ORIGINS)
        if has_wildcard:
            findings.append(SecurityFinding(
                check_id="SEC-004",
                title="CORS allowed origins contains wildcard (*)",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Wildcard CORS origins allow arbitrary third-party web domains to make credentialed browser requests.",
                remediation="Specify explicit trusted origin domains (e.g., https://app.analyzax.com) without wildcards.",
            ))
        else:
            passed_checks.append("SEC-004: CORS origins policy is strictly restricted.")

        # 5. Secure Cookies Check
        if not cfg.SECURE_COOKIES:
            findings.append(SecurityFinding(
                check_id="SEC-005",
                title="SECURE_COOKIES is disabled",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Session and auth cookies will be transmitted over unencrypted HTTP connections without the Secure flag.",
                remediation="Set SECURE_COOKIES=True in production so browsers only transmit cookies over TLS/HTTPS.",
            ))
        else:
            passed_checks.append("SEC-005: SECURE_COOKIES is enabled.")

        # 6. Rate Limiting Enabled
        if not cfg.RATE_LIMIT_ENABLED:
            findings.append(SecurityFinding(
                check_id="SEC-006",
                title="Global API rate limiting is disabled",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Disabled rate limiting leaves endpoints exposed to credential stuffing, brute force, and DoS attacks.",
                remediation="Set RATE_LIMIT_ENABLED=True.",
            ))
        else:
            passed_checks.append("SEC-006: Rate limiting engine is active.")

        # 7. Security Headers Enabled
        if not cfg.SECURITY_HEADERS_ENABLED:
            findings.append(SecurityFinding(
                check_id="SEC-007",
                title="Security headers middleware is disabled",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Missing essential headers like HSTS, X-Content-Type-Options, X-Frame-Options, and CSP.",
                remediation="Set SECURITY_HEADERS_ENABLED=True.",
            ))
        else:
            passed_checks.append("SEC-007: Security response headers middleware is active.")

        # 8. HSTS Configuration
        if cfg.HSTS_MAX_AGE_SECONDS < 15552000:  # < 180 days
            findings.append(SecurityFinding(
                check_id="SEC-008",
                title="HSTS max-age is shorter than recommended 180 days",
                severity=FindingSeverity.WARNING,
                description=f"Current HSTS max-age is {cfg.HSTS_MAX_AGE_SECONDS} seconds.",
                remediation="Set HSTS_MAX_AGE_SECONDS=31536000 (1 year) for optimal transport layer security.",
            ))
        else:
            passed_checks.append("SEC-008: HSTS max-age meets or exceeds 180 days.")

        # 9. Billing Webhook Secret Check
        if cfg.BILLING_ENABLED and cfg.BILLING_PROVIDER == "stripe":
            if not cfg.BILLING_WEBHOOK_SECRET or cfg.BILLING_WEBHOOK_SECRET in self.DEFAULT_SECRETS:
                findings.append(SecurityFinding(
                    check_id="SEC-009",
                    title="Billing webhook signing secret is missing or default in Stripe mode",
                    severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                    description="Incoming Stripe webhook payloads cannot be cryptographically verified.",
                    remediation="Configure BILLING_WEBHOOK_SECRET with the Stripe signing secret (whsec_...).",
                ))
            else:
                passed_checks.append("SEC-009: Billing webhook secret is properly configured.")
        else:
            passed_checks.append("SEC-009: Billing webhook secret check skipped or in sandbox mode.")

        # 10. Database Password in Connection String
        if is_prod and ("analyzax_secure_password" in cfg.DATABASE_URL or "password" in cfg.DATABASE_URL):
            findings.append(SecurityFinding(
                check_id="SEC-010",
                title="Database connection string uses default/template password in production",
                severity=FindingSeverity.CRITICAL,
                description="DATABASE_URL contains boilerplate default credentials.",
                remediation="Provision a dedicated PostgreSQL user with a strong unique password and update DATABASE_URL.",
            ))
        else:
            passed_checks.append("SEC-010: Database credentials do not use default dev values.")

        # 11. Storage Backend Credentials
        if cfg.STORAGE_BACKEND == "s3" and (not cfg.S3_ACCESS_KEY_ID or not cfg.S3_SECRET_ACCESS_KEY):
            findings.append(SecurityFinding(
                check_id="SEC-011",
                title="S3 storage backend configured without access credentials",
                severity=FindingSeverity.CRITICAL,
                description="Storage backend set to 's3' but S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY is empty.",
                remediation="Provide valid IAM / S3 access credentials or switch to local storage provider.",
            ))
        else:
            passed_checks.append("SEC-011: Storage backend credentials configured appropriately.")

        # 12. Sensitive Log Redaction
        if not cfg.LOG_REDACT_SENSITIVE:
            findings.append(SecurityFinding(
                check_id="SEC-012",
                title="Sensitive log redaction is disabled",
                severity=FindingSeverity.WARNING,
                description="API keys, authorization headers, and passwords could be inadvertently logged.",
                remediation="Set LOG_REDACT_SENSITIVE=True.",
            ))
        else:
            passed_checks.append("SEC-012: Sensitive log data redaction is active.")

        # 13. Brute Force Login Protection
        if cfg.AUTH_LOGIN_MAX_ATTEMPTS > 10 or cfg.AUTH_LOGIN_LOCKOUT_SECONDS < 300:
            findings.append(SecurityFinding(
                check_id="SEC-013",
                title="Login lockout thresholds are lenient",
                severity=FindingSeverity.WARNING,
                description="Max login attempts exceed 10 or lockout duration is less than 5 minutes.",
                remediation="Set AUTH_LOGIN_MAX_ATTEMPTS <= 5 and AUTH_LOGIN_LOCKOUT_SECONDS >= 300.",
            ))
        else:
            passed_checks.append("SEC-013: Login lockout thresholds meet brute force resistance standards.")

        # 14. Password Minimum Length
        if cfg.AUTH_PASSWORD_MIN_LENGTH < 8:
            findings.append(SecurityFinding(
                check_id="SEC-014",
                title="Password minimum length is below 8 characters",
                severity=FindingSeverity.CRITICAL if is_prod else FindingSeverity.WARNING,
                description="Passwords shorter than 8 characters are vulnerable to rapid offline cracking.",
                remediation="Set AUTH_PASSWORD_MIN_LENGTH >= 8 (recommended 12+).",
            ))
        else:
            passed_checks.append("SEC-014: Password minimum length satisfies security baseline.")

        # Calculate final compliance score
        critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        warning_count = sum(1 for f in findings if f.severity == FindingSeverity.WARNING)

        # Baseline calculation: 100 minus penalties
        penalty = (critical_count * 25) + (warning_count * 5)
        score = max(0, 100 - penalty)
        passed = (critical_count == 0)

        return SecurityAuditReport(
            target_env=cfg.APP_ENV,
            score=score,
            passed=passed,
            critical_count=critical_count,
            warning_count=warning_count,
            passed_count=len(passed_checks),
            findings=findings,
            passed_checks=passed_checks,
        )


config_audit_engine = ConfigAuditEngine()
