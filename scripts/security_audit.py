"""
AnalyzaX — Phase 24: Security Configuration Audit CLI.
Validates the current environment, application configuration, secret entropy,
CORS restrictions, cookie flags, and rate limiting against enterprise hardening standards.
"""

import argparse
import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.engines.security.config_audit import (
    FindingSeverity,
    config_audit_engine,
)


def main():
    parser = argparse.ArgumentParser(description="AnalyzaX Enterprise Security Configuration Audit")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        default=None,
        help="Simulate audit against a specific environment (default uses APP_ENV setting)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce production rules regardless of local environment setting",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format",
    )
    args = parser.parse_args()

    enforce_prod = args.strict or (args.env == "production")
    report = config_audit_engine.audit(enforce_prod=enforce_prod)

    if args.json:
        print(report.model_dump_json(indent=2))
        sys.exit(0 if report.passed else 1)

    print("\n" + "=" * 76)
    print(" AnalyzaX - Enterprise Security Configuration Audit Report")
    print("=" * 76)
    print(f"Target Environment:    {report.target_env.upper()} (Enforce Strict: {enforce_prod})")
    print(f"Hardening Score:       {report.score}/100")
    print(f"Audit Status:          {'PASSED [PASS]' if report.passed else 'FAILED [FAIL]'}")
    print(f"Checks Passed:         {report.passed_count}")
    print(f"Critical Findings:     {report.critical_count}")
    print(f"Warning Findings:      {report.warning_count}")
    print("=" * 76)

    if report.findings:
        print("\nFINDINGS:")
        for f in report.findings:
            tag = f"[{f.severity.value}]"
            print(f"\n{tag:<11} {f.check_id}: {f.title}")
            print(f"            Description: {f.description}")
            print(f"            Remediation: {f.remediation}")
    else:
        print("\nNo security configuration findings detected. Baseline fully hardened!")

    print("\nPASSED CHECKS:")
    for chk in report.passed_checks:
        print(f"  [OK] {chk}")

    print("\n" + "=" * 76)
    if report.passed:
        print("RESULT: Security configuration meets required posture.")
        sys.exit(0)
    else:
        print("RESULT: CRITICAL security findings detected. Do NOT deploy to production without resolving.")
        sys.exit(1)


if __name__ == "__main__":
    main()
