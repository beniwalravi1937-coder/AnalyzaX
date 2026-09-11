"""
AnalyzaX — Phase 22: Production Smoke Test Suite.
Performs comprehensive non-destructive verification against a live AnalyzaX instance.
Used in CI/CD release pipelines and post-deployment validation.
"""

import argparse
import sys
import urllib.request
import urllib.error
import json
import time


def run_check(name: str, test_func) -> bool:
    try:
        t0 = time.perf_counter()
        passed, msg = test_func()
        dur_ms = round((time.perf_counter() - t0) * 1000, 1)
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {name} ({dur_ms}ms): {msg}")
        return passed
    except Exception as e:
        print(f"[FAIL] {name}: Exception: {e}")
        return False


def make_request(url: str, method: str = "GET", headers: dict = None) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.status
            resp_headers = dict(response.headers)
            body = response.read().decode("utf-8")
            return status_code, resp_headers, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, dict(e.headers), body
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed to {url}: {e}")


def main():
    parser = argparse.ArgumentParser(description="AnalyzaX Production Smoke Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of AnalyzaX API")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print("\n" + "=" * 70)
    print(f" AnalyzaX Deployment Smoke Test Suite — Target: {base_url}")
    print("=" * 70)

    results = []

    # 1. Process Liveness Check
    def check_liveness():
        code, _, body = make_request(f"{base_url}/health/live")
        data = json.loads(body)
        return code == 200 and data.get("status") == "alive", f"HTTP {code}, status={data.get('status')}"

    results.append(run_check("Process Liveness (/health/live)", check_liveness))

    # 2. Dependency Readiness Check
    def check_readiness():
        code, _, body = make_request(f"{base_url}/health/ready")
        data = json.loads(body)
        is_ready = data.get("is_ready")
        return code == 200 and is_ready is True, f"HTTP {code}, is_ready={is_ready}"

    results.append(run_check("Dependency Readiness (/health/ready)", check_readiness))

    # 3. Telemetry & Analytical Engines Check
    def check_health():
        code, _, body = make_request(f"{base_url}/health")
        data = json.loads(body)
        duck_ok = data.get("duckdb") == "available"
        return code == 200 and duck_ok, f"HTTP {code}, duckdb={data.get('duckdb')}, version={data.get('version')}"

    results.append(run_check("System Telemetry (/health)", check_health))

    # 4. Prometheus Metrics Exposition Check
    def check_metrics():
        code, headers, body = make_request(f"{base_url}/metrics")
        has_metrics = "analyzax_http_requests_total" in body or "analyzax_uptime_seconds" in body
        return code == 200 and has_metrics, f"HTTP {code}, metric_lines={len(body.splitlines())}"

    results.append(run_check("Prometheus Metrics (/metrics)", check_metrics))

    # 5. Security Headers Check
    def check_security_headers():
        code, headers, _ = make_request(f"{base_url}/health")
        has_nosniff = headers.get("X-Content-Type-Options") == "nosniff" or headers.get("x-content-type-options") == "nosniff"
        has_frame = headers.get("X-Frame-Options") == "DENY" or headers.get("x-frame-options") == "DENY"
        has_req_id = "X-Request-ID" in headers or "x-request-id" in headers
        passed = has_nosniff and has_frame and has_req_id
        return passed, f"nosniff={has_nosniff}, frame_deny={has_frame}, req_id={has_req_id}"

    results.append(run_check("OWASP Security Headers", check_security_headers))

    # 6. Plan Catalog API Check
    def check_plans_api():
        code, _, body = make_request(f"{base_url}/api/v1/plans")
        data = json.loads(body)
        has_plans = isinstance(data, list) and len(data) >= 4
        return code == 200 and has_plans, f"HTTP {code}, plans_count={len(data) if isinstance(data, list) else 0}"

    results.append(run_check("Plan Catalog (/api/v1/plans)", check_plans_api))

    # 7. 404 Handling & Structured Error Check
    def check_error_handling():
        code, headers, body = make_request(f"{base_url}/api/v1/non_existent_route_404")
        data = json.loads(body)
        has_error = data.get("error") is not None or data.get("detail") is not None
        return code == 404 and has_error, f"HTTP {code}, structured_error={has_error}"

    results.append(run_check("Structured 404 Error Handling", check_error_handling))

    print("-" * 70)
    all_passed = all(results)
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    print(f" Summary: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'} ({passed_count}/{total_count} passed)")
    print("=" * 70 + "\n")

    if not all_passed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
