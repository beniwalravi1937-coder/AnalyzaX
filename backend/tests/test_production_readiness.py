"""
AnalyzaX — Phase 22 Test Suite: Production Readiness, Operations & Deployment Infrastructure.
Tests configuration auditing, structured logging, correlation tracing, security headers,
rate limiting, liveness/readiness probes, metrics telemetry, path isolation, and migrations.
"""

import os
import tempfile
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.core.config_validator import ProductionConfigValidator
from backend.app.core.error_tracking import error_tracker
from backend.app.core.logging import (
    ctx_correlation_id,
    ctx_request_id,
    redact_sensitive_dict,
    redact_sensitive_string,
)
from backend.app.core.metrics import metrics_collector
from backend.app.core.middleware.security import rate_limiter
from backend.app.core.migrations.locking import MigrationLock
from backend.app.core.migrations.runner import migration_runner
from backend.app.engines.jobs.models import (
    Job,
    JobPriority,
    JobStatus,
    JobType,
    PermanentJobError,
    TransientJobError,
)
from backend.app.engines.jobs.queue import LocalDurableQueue
from backend.app.engines.jobs.worker import JobWorkerPool
from backend.app.engines.storage.local_provider import LocalStorageProvider
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Configuration Validation Tests
# ------------------------------------------------------------------------------
def test_config_validator_development():
    validator = ProductionConfigValidator()
    report = validator.validate(target_env="development")
    # Development allows warnings for local default secrets
    assert report.environment == "development"
    assert report.critical_count == 0
    assert report.is_valid is True


def test_config_validator_production_fail_fast():
    validator = ProductionConfigValidator()
    report = validator.validate(target_env="production")
    # Should flag critical failures because development defaults are active
    assert report.environment == "production"
    assert report.is_valid is False
    assert report.critical_count > 0
    assert any(c.name == "DEBUG_DISABLED" and not c.passed for c in report.checks)
    assert any(c.name == "SECRET_KEY_COMPLEXITY" and not c.passed for c in report.checks)


# ------------------------------------------------------------------------------
# 2. Structured Logging & Sensitive Data Redaction Tests
# ------------------------------------------------------------------------------
def test_sensitive_string_redaction():
    text_with_token = "User authorized with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    scrubbed = redact_sensitive_string(text_with_token)
    assert "[REDACTED]" in scrubbed
    assert "eyJhbGci" not in scrubbed

    text_with_pwd = 'Config item password="super_secret_password_123"'
    scrubbed_pwd = redact_sensitive_string(text_with_pwd)
    assert "[REDACTED]" in scrubbed_pwd
    assert "super_secret_password_123" not in scrubbed_pwd

    stripe_prefix = "sk_live_"
    stripe_key = f"Received payload with key: {stripe_prefix}mockdummykey1234567890"
    assert "[REDACTED_LIVE_KEY]" in redact_sensitive_string(stripe_key)


def test_sensitive_dict_redaction():
    payload = {
        "user_id": "usr_123",
        "username": "alice",
        "password": "my_plaintext_password",
        "access_token": "secret_access_token_val",
        "nested": {
            "api_key": "secret_api_key_val",
            "normal_field": "ok_value",
        },
    }
    scrubbed = redact_sensitive_dict(payload)
    assert scrubbed["user_id"] == "usr_123"
    assert scrubbed["password"] == "[REDACTED]"
    assert scrubbed["access_token"] == "[REDACTED]"
    assert scrubbed["nested"]["api_key"] == "[REDACTED]"
    assert scrubbed["nested"]["normal_field"] == "ok_value"


# ------------------------------------------------------------------------------
# 3. Request Correlation & Tracing Middleware Tests
# ------------------------------------------------------------------------------
def test_request_correlation_headers(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Request-ID"].startswith("req_")
    assert "X-Correlation-ID" in res.headers
    assert "X-Response-Time" in res.headers


def test_preserves_inbound_request_id(client):
    custom_req_id = "req_custom_trace_998877"
    res = client.get("/health/live", headers={"X-Request-ID": custom_req_id})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == custom_req_id
    assert res.headers["X-Correlation-ID"] == custom_req_id


# ------------------------------------------------------------------------------
# 4. Security Headers & Rate Limiting Tests
# ------------------------------------------------------------------------------
def test_security_headers_present(client):
    res = client.get("/health/live")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in res.headers
    assert "Permissions-Policy" in res.headers


def test_rate_limiter_logic():
    client_id = f"test_client_{time.time()}"
    bucket = "test_bucket"
    limit = 5

    for _ in range(limit):
        allowed, retry = rate_limiter.is_allowed(client_id, bucket, limit_per_minute=limit)
        assert allowed is True
        assert retry == 0

    # Next attempt should be blocked
    allowed, retry = rate_limiter.is_allowed(client_id, bucket, limit_per_minute=limit)
    assert allowed is False
    assert retry > 0


# ------------------------------------------------------------------------------
# 5. Health, Liveness & Readiness Probes Tests
# ------------------------------------------------------------------------------
def test_liveness_probe(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert data["service"] == "analyzax-backend"
    assert "timestamp" in data


def test_readiness_probe(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["is_ready"] is True
    assert len(data["dependencies"]) >= 2

    dep_names = {d["name"]: d for d in data["dependencies"]}
    assert "duckdb" in dep_names
    assert dep_names["duckdb"]["status"] == "healthy"
    assert "storage" in dep_names
    assert dep_names["storage"]["status"] == "healthy"


def test_system_telemetry_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["duckdb"] == "available"
    assert data["storage"] == "available"
    assert "uptime_seconds" in data


# ------------------------------------------------------------------------------
# 6. Metrics & Observability Tests
# ------------------------------------------------------------------------------
def test_prometheus_metrics_endpoint(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    content = res.text
    assert "analyzax_uptime_seconds" in content
    assert "analyzax_http_requests_total" in content


def test_admin_metrics_summary(client):
    res = client.get("/api/v1/admin/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "http" in data
    assert "database" in data
    assert "jobs" in data
    assert "uptime_seconds" in data
    assert "latency_ms" in data["http"]


def test_error_tracker_captures_and_redacts():
    try:
        raise ValueError("Secret database password db_pass_123 failed authentication")
    except ValueError as exc:
        tracked = error_tracker.capture_exception(exc, error_code="TEST_ERR")
        assert "db_pass_123" not in tracked.message
        assert "[REDACTED]" in tracked.message or "password" in tracked.message
        assert tracked.error_code == "TEST_ERR"
        assert tracked.release_version is not None


# ------------------------------------------------------------------------------
# 7. Durable Storage & Path Isolation Security Tests
# ------------------------------------------------------------------------------
def test_storage_provider_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(root_dir=tmpdir)
        rel_path = "workspaces/ws_test/datasets/test.parquet"
        content = b"PARQUET_TEST_HEADER_BINARY_DATA"

        info = storage.save_file(rel_path, content, content_type="application/octet-stream")
        assert info.path == rel_path
        assert info.size_bytes == len(content)
        assert storage.file_exists(rel_path) is True

        retrieved = storage.get_file(rel_path)
        assert retrieved == content

        # Signed URL generation and validation
        signed_url = storage.generate_signed_url(rel_path, expires_in_seconds=60)
        assert "sig=" in signed_url
        assert "expires=" in signed_url

        # Delete
        assert storage.delete_file(rel_path) is True
        assert storage.file_exists(rel_path) is False


def test_storage_directory_traversal_prevention():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(root_dir=tmpdir)

        # Attempt to escape storage root using relative traversal
        traversal_path = "../../etc/passwd"
        with pytest.raises(ValueError) as exc:
            storage.save_file(traversal_path, b"malicious content")
        assert "traversal" in str(exc.value).lower() or "escapes" in str(exc.value).lower()

        # Attempt to access with backslashes on Windows or forward slashes
        traversal_win = "..\\..\\windows\\system32\\config"
        with pytest.raises(ValueError):
            storage.save_file(traversal_win, b"malicious content")


# ------------------------------------------------------------------------------
# 8. Background Queue, Priority & Worker Pool Tests
# ------------------------------------------------------------------------------
def test_job_queue_and_worker_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        q = LocalDurableQueue(storage_dir=tmpdir)
        pool = JobWorkerPool(num_workers=1)

        # Register mock handler
        processed = []
        pool.register_handler(
            JobType.PROFILING,
            lambda j: {"rows_processed": 1000, "status": "completed"},
        )

        job = Job(
            id="job_test_001",
            job_type=JobType.PROFILING,
            workspace_id="ws_001",
            priority=JobPriority.HIGH,
            payload={"dataset_id": "ds_001"},
        )
        q.enqueue(job)

        # Dequeue and execute
        retrieved = q.dequeue(timeout_seconds=0.5)
        assert retrieved is not None
        assert retrieved.id == "job_test_001"

        pool._execute_job(retrieved)
        assert retrieved.status == JobStatus.COMPLETED
        assert retrieved.result == {"rows_processed": 1000, "status": "completed"}


def test_job_transient_retry_policy():
    with tempfile.TemporaryDirectory() as tmpdir:
        q = LocalDurableQueue(storage_dir=tmpdir)
        pool = JobWorkerPool(num_workers=1)

        call_count = [0]

        def flaky_handler(j: Job):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TransientJobError("Transient network timeout to analytics cluster")
            return {"attempt_recovered": True}

        pool.register_handler(JobType.EDA, flaky_handler)

        job = Job(
            id="job_flaky_002",
            job_type=JobType.EDA,
            workspace_id="ws_001",
            max_retries=2,
            retry_delay_seconds=0.01,
        )
        q.enqueue(job)

        deq = q.dequeue(timeout_seconds=0.5)
        assert deq is not None

        # First attempt fails with transient error -> RETRYING
        pool._execute_job(deq)
        assert deq.status == JobStatus.RETRYING
        assert deq.attempts == 1

        # Second attempt succeeds
        deq.status = JobStatus.RUNNING
        pool._execute_job(deq)
        assert deq.status == JobStatus.COMPLETED
        assert deq.result == {"attempt_recovered": True}


# ------------------------------------------------------------------------------
# 9. Migration Runner & Distributed Locking Tests
# ------------------------------------------------------------------------------
def test_migration_runner_status_and_idempotency():
    status = migration_runner.status()
    assert status.total_available >= 2
    assert status.total_applied >= 2
    assert status.pending_count == 0

    # Re-running migrate() should be a no-op
    applied = migration_runner.migrate()
    assert len(applied) == 0


def test_migration_lock_mutual_exclusion():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock1 = MigrationLock(lock_dir=tmpdir)
        lock2 = MigrationLock(lock_dir=tmpdir)

        assert lock1.acquire(timeout_seconds=2) is True
        # Second lock attempt should fail or time out
        assert lock2.acquire(timeout_seconds=1) is False

        lock1.release()
        # Now second lock can acquire
        assert lock2.acquire(timeout_seconds=2) is True
        lock2.release()
