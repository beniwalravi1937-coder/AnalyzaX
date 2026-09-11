"""
AnalyzaX — Phase 22: Centralized Production Configuration Validator.
Validates environment settings, secret policies, storage, and networking
to ensure the system fails fast before starting with insecure or invalid configuration.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings


class ValidationCheck(BaseModel):
    category: str
    name: str
    passed: bool
    severity: str  # "CRITICAL", "WARNING", "INFO"
    message: str


class ValidationReport(BaseModel):
    environment: str
    is_valid: bool
    critical_count: int
    warning_count: int
    checks: List[ValidationCheck] = Field(default_factory=list)


def _mask_secret(val: str) -> str:
    """Masks secrets for safe diagnostic output."""
    if not val:
        return "(empty)"
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"


class ProductionConfigValidator:
    """Validator enforcing production readiness and security gates."""

    INSECURE_SECRET_SUBSTRINGS = [
        "development-secret",
        "change-in-production",
        "secure-random",
        "sandbox_secret_key",
        "analyzax_secure_password",
        "test_secret",
    ]

    def validate(self, target_env: Optional[str] = None) -> ValidationReport:
        env = (target_env or settings.APP_ENV or "development").lower()
        is_prod = env in ("production", "prod")
        is_staging = env in ("staging", "stage")
        is_strict = is_prod or is_staging

        checks: List[ValidationCheck] = []

        # 1. Environment & Debug Flag
        if is_prod and settings.DEBUG:
            checks.append(
                ValidationCheck(
                    category="Environment",
                    name="DEBUG_DISABLED",
                    passed=False,
                    severity="CRITICAL",
                    message="DEBUG mode must be disabled (False) in production.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Environment",
                    name="DEBUG_DISABLED",
                    passed=True,
                    severity="INFO",
                    message=f"DEBUG is {'disabled' if not settings.DEBUG else 'enabled'}.",
                )
            )

        # 2. Secret Key Validation
        secret_is_insecure = (
            not settings.SECRET_KEY
            or len(settings.SECRET_KEY) < 32
            or any(s in settings.SECRET_KEY for s in self.INSECURE_SECRET_SUBSTRINGS)
        )
        if is_strict and secret_is_insecure:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="SECRET_KEY_COMPLEXITY",
                    passed=False,
                    severity="CRITICAL",
                    message="SECRET_KEY must be a unique, cryptographically random secret of at least 32 characters in production.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="SECRET_KEY_COMPLEXITY",
                    passed=not secret_is_insecure,
                    severity="WARNING" if secret_is_insecure else "INFO",
                    message="SECRET_KEY validated." if not secret_is_insecure else "SECRET_KEY uses an insecure or development default.",
                )
            )

        # 3. Auth Session Secret
        auth_secret_insecure = (
            not settings.AUTH_SESSION_SECRET
            or len(settings.AUTH_SESSION_SECRET) < 32
            or any(s in settings.AUTH_SESSION_SECRET for s in self.INSECURE_SECRET_SUBSTRINGS)
        )
        if is_strict and auth_secret_insecure:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="AUTH_SESSION_SECRET",
                    passed=False,
                    severity="CRITICAL",
                    message="AUTH_SESSION_SECRET must be configured with a strong production secret in production.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="AUTH_SESSION_SECRET",
                    passed=not auth_secret_insecure,
                    severity="WARNING" if auth_secret_insecure else "INFO",
                    message="AUTH_SESSION_SECRET validated." if not auth_secret_insecure else "AUTH_SESSION_SECRET uses a default value.",
                )
            )

        # 4. CORS Safety
        has_wildcard_cors = "*" in settings.ALLOWED_CORS_ORIGINS
        if is_strict and has_wildcard_cors:
            checks.append(
                ValidationCheck(
                    category="Networking",
                    name="CORS_NO_WILDCARD",
                    passed=False,
                    severity="CRITICAL",
                    message="Wildcard '*' in ALLOWED_CORS_ORIGINS is forbidden when session cookies and credentials are used.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Networking",
                    name="CORS_NO_WILDCARD",
                    passed=not has_wildcard_cors,
                    severity="WARNING" if has_wildcard_cors else "INFO",
                    message="CORS origin configuration is explicit.",
                )
            )

        # 5. Database Connection Bounds & Credentials
        db_url = settings.DATABASE_URL or ""
        uses_default_db_pass = "analyzax_secure_password" in db_url
        if is_strict and uses_default_db_pass:
            checks.append(
                ValidationCheck(
                    category="Database",
                    name="DATABASE_CREDENTIALS",
                    passed=False,
                    severity="CRITICAL",
                    message="DATABASE_URL contains the default development password. Production requires unique credentials.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Database",
                    name="DATABASE_CREDENTIALS",
                    passed=not uses_default_db_pass,
                    severity="INFO",
                    message="Database credentials verified.",
                )
            )

        # 6. Database Connection Pool Bounds
        pool_bounded = 1 <= settings.DB_POOL_SIZE <= 100 and settings.DB_MAX_OVERFLOW <= 100
        checks.append(
            ValidationCheck(
                category="Database",
                name="DB_POOL_BOUNDS",
                passed=pool_bounded,
                severity="CRITICAL" if not pool_bounded else "INFO",
                message=f"Connection pool size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}.",
            )
        )

        # 7. Secure Cookie Configuration
        if is_prod and not settings.SECURE_COOKIES:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="SECURE_COOKIES",
                    passed=False,
                    severity="CRITICAL",
                    message="SECURE_COOKIES must be enabled in production environments.",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    category="Security",
                    name="SECURE_COOKIES",
                    passed=True,
                    severity="INFO",
                    message="Secure cookies setting verified.",
                )
            )

        # 8. Storage Root Durability
        storage_root = os.path.abspath(settings.DATA_STORAGE_ROOT)
        try:
            os.makedirs(storage_root, exist_ok=True)
            storage_writable = os.access(storage_root, os.W_OK)
        except Exception:
            storage_writable = False

        checks.append(
            ValidationCheck(
                category="Storage",
                name="STORAGE_WRITABLE",
                passed=storage_writable,
                severity="CRITICAL" if not storage_writable else "INFO",
                message=f"Storage root '{storage_root}' is writable." if storage_writable else f"Storage root '{storage_root}' is NOT writable.",
            )
        )

        # 9. S3 / Cloud Object Storage Settings (if S3 backend chosen)
        if settings.STORAGE_BACKEND == "s3":
            s3_ok = bool(settings.S3_BUCKET_NAME and settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY)
            if not s3_ok:
                checks.append(
                    ValidationCheck(
                        category="Storage",
                        name="S3_CONFIG",
                        passed=False,
                        severity="CRITICAL",
                        message="STORAGE_BACKEND is 's3' but S3_BUCKET_NAME, S3_ACCESS_KEY_ID, or S3_SECRET_ACCESS_KEY is missing.",
                    )
                )
            else:
                checks.append(
                    ValidationCheck(
                        category="Storage",
                        name="S3_CONFIG",
                        passed=True,
                        severity="INFO",
                        message=f"S3 Object storage configured for bucket '{settings.S3_BUCKET_NAME}'.",
                    )
                )

        # 10. Billing Provider Configuration
        if settings.BILLING_ENABLED and is_prod:
            webhook_insecure = (
                not settings.BILLING_WEBHOOK_SECRET
                or "sandbox_secret" in settings.BILLING_WEBHOOK_SECRET
            )
            if webhook_insecure:
                checks.append(
                    ValidationCheck(
                        category="Billing",
                        name="BILLING_WEBHOOK_SECRET",
                        passed=False,
                        severity="CRITICAL",
                        message="BILLING_WEBHOOK_SECRET must be configured with a production webhook signing secret.",
                    )
                )
            else:
                checks.append(
                    ValidationCheck(
                        category="Billing",
                        name="BILLING_WEBHOOK_SECRET",
                        passed=True,
                        severity="INFO",
                        message="Billing webhook secret configured.",
                    )
                )

        # Summarize Report
        criticals = [c for c in checks if not c.passed and c.severity == "CRITICAL"]
        warnings = [c for c in checks if not c.passed and c.severity == "WARNING"]
        is_valid = len(criticals) == 0

        return ValidationReport(
            environment=env,
            is_valid=is_valid,
            critical_count=len(criticals),
            warning_count=len(warnings),
            checks=checks,
        )


config_validator = ProductionConfigValidator()


def main():
    parser = argparse.ArgumentParser(description="AnalyzaX Production Configuration Validator")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production", "test"],
        default=None,
        help="Target environment to validate against (defaults to APP_ENV)",
    )
    args = parser.parse_args()

    report = config_validator.validate(target_env=args.env)

    print("\n" + "=" * 70)
    print(f" AnalyzaX Configuration Audit - Environment: {report.environment.upper()}")
    print("=" * 70)

    for check in report.checks:
        symbol = "PASS" if check.passed else ("FAIL" if check.severity == "CRITICAL" else "WARN")
        status_str = f"[{symbol}] {check.category} / {check.name}: {check.message}"
        print(status_str)

    print("-" * 70)
    print(f" Summary: {'PASSED' if report.is_valid else 'FAILED'} (Critical: {report.critical_count}, Warnings: {report.warning_count})")
    print("=" * 70 + "\n")

    if not report.is_valid:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
