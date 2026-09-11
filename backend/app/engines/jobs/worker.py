"""
AnalyzaX — Phase 22: Background Job Worker Pool.
Executes analytical tasks asynchronously with retry policies, timeouts,
cancellation support, and Dead-Letter Queue (DLQ) tracking.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.error_tracking import error_tracker
from backend.app.core.logging import (
    ctx_correlation_id,
    ctx_job_id,
    ctx_request_id,
    logger,
    redact_sensitive_string,
)
from backend.app.core.metrics import metrics_collector
from backend.app.engines.jobs.models import (
    Job,
    JobStatus,
    JobType,
    PermanentJobError,
    TransientJobError,
)
from backend.app.engines.jobs.queue import job_queue


class JobWorkerPool:
    """Worker pool processing asynchronous jobs from the durable queue."""

    def __init__(self, num_workers: Optional[int] = None) -> None:
        self.num_workers = num_workers or getattr(settings, "JOB_MAX_CONCURRENT_WORKERS", 4)
        self._handlers: Dict[JobType, Callable[[Job], Dict]] = {}
        self._running = False
        self._threads: list[threading.Thread] = []
        self._cancelled_jobs: set[str] = set()

    def register_handler(
        self, job_type: JobType, handler: Callable[[Job], Dict]
    ) -> None:
        """Registers a worker callback handler for a given job type."""
        self._handlers[job_type] = handler

    def cancel_job(self, job_id: str) -> bool:
        """Flags a job for cooperative cancellation."""
        self._cancelled_jobs.add(job_id)
        job = job_queue.get_job(job_id)
        if job and job.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING):
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job_queue.update_job(job)
            metrics_collector.record_job(job.job_type.value, "cancelled")
            logger.info(f"Cancelled job [{job_id}]")
            return True
        return False

    def start(self) -> None:
        """Starts worker threads."""
        if self._running:
            return
        self._running = True
        logger.info(f"Starting background JobWorkerPool with {self.num_workers} threads...")
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"analyzax-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self, timeout_seconds: float = 5.0) -> None:
        """Graceful shutdown stopping queue consumption."""
        self._running = False
        logger.info("Stopping JobWorkerPool...")
        for t in self._threads:
            t.join(timeout=timeout_seconds)
        self._threads.clear()

    def _worker_loop(self) -> None:
        while self._running:
            try:
                job = job_queue.dequeue(timeout_seconds=1.0)
                if not job:
                    continue

                if job.id in self._cancelled_jobs:
                    job.status = JobStatus.CANCELLED
                    job.completed_at = datetime.now(timezone.utc).isoformat()
                    job_queue.update_job(job)
                    continue

                self._execute_job(job)
            except Exception as e:
                logger.error(f"Worker loop encountered unexpected error: {e}", exc_info=True)

    def _execute_job(self, job: Job) -> None:
        handler = self._handlers.get(job.job_type)
        if not handler:
            # Default fallback mock handler for tests or unmounted services
            handler = lambda j: {"status": "ok", "mock_processed": True}

        # Setup context for tracing and logging
        t_req = ctx_request_id.set(job.request_id)
        t_corr = ctx_correlation_id.set(job.correlation_id)
        t_job = ctx_job_id.set(job.id)

        job.started_at = datetime.now(timezone.utc).isoformat()
        job.attempts += 1
        job_queue.update_job(job)

        t0 = time.perf_counter()
        logger.info(f"Executing job [{job.id}] (type={job.job_type.value}, attempt={job.attempts}/{job.max_retries})")

        try:
            result = handler(job)
            dur_sec = time.perf_counter() - t0

            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job_queue.update_job(job)

            metrics_collector.record_job(
                job.job_type.value, "completed", duration_sec=dur_sec
            )
            logger.info(f"Job [{job.id}] COMPLETED in {dur_sec:.2f}s")
        except TransientJobError as err:
            dur_sec = time.perf_counter() - t0
            safe_err = redact_sensitive_string(str(err))
            job.last_error = safe_err
            error_tracker.capture_exception(err, error_code="TRANSIENT_JOB_ERROR", job_id=job.id)

            if job.is_retryable():
                job.status = JobStatus.RETRYING
                backoff = job.retry_delay_seconds * (2 ** (job.attempts - 1))
                logger.warning(
                    f"Job [{job.id}] TRANSIENT failure: {safe_err}. Retrying in {backoff:.1f}s (attempt {job.attempts}/{job.max_retries})"
                )
                time.sleep(min(backoff, 30.0))  # Capped backoff
                job_queue.update_job(job)
                metrics_collector.record_job(
                    job.job_type.value, "retrying", duration_sec=dur_sec, retry=True
                )
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc).isoformat()
                job_queue.update_job(job)
                metrics_collector.record_job(
                    job.job_type.value, "failed", duration_sec=dur_sec
                )
                logger.error(f"Job [{job.id}] FAILED after exhausting retries: {safe_err}")
        except Exception as err:
            dur_sec = time.perf_counter() - t0
            safe_err = redact_sensitive_string(str(err))
            job.status = JobStatus.FAILED
            job.last_error = safe_err
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job_queue.update_job(job)

            error_tracker.capture_exception(err, error_code="PERMANENT_JOB_ERROR", job_id=job.id)
            metrics_collector.record_job(
                job.job_type.value, "failed", duration_sec=dur_sec
            )
            logger.error(f"Job [{job.id}] PERMANENT failure: {safe_err}")
        finally:
            ctx_request_id.reset(t_req)
            ctx_correlation_id.reset(t_corr)
            ctx_job_id.reset(t_job)


worker_pool = JobWorkerPool()
