"""
AnalyzaX — Phase 22: Durable Job Queue Implementation.
Provides thread-safe priority queueing with atomic filesystem durability.
Ensures crashes never cause silent job loss.
"""

import heapq
import json
import os
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.jobs.models import Job, JobStatus


class JobQueue(ABC):
    @abstractmethod
    def enqueue(self, job: Job) -> Job:
        pass

    @abstractmethod
    def dequeue(self, timeout_seconds: float = 1.0) -> Optional[Job]:
        pass

    @abstractmethod
    def update_job(self, job: Job) -> None:
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        pass


class LocalDurableQueue(JobQueue):
    """File-backed priority queue persisting state on disk."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = os.path.abspath(storage_dir or getattr(settings, "DATA_JOBS_DIR", "./data/jobs"))
        self.active_dir = os.path.join(self.storage_dir, "active")
        self.completed_dir = os.path.join(self.storage_dir, "completed")
        self.dlq_dir = os.path.join(self.storage_dir, "dlq")

        for d in (self.active_dir, self.completed_dir, self.dlq_dir):
            os.makedirs(d, exist_ok=True)

        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._heap: List[tuple[int, float, str]] = []  # (-priority, created_timestamp, job_id)
        self._jobs: Dict[str, Job] = {}

        self._restore_from_disk()

    def _restore_from_disk(self) -> None:
        """Restores pending and retrying jobs from disk on worker startup."""
        count = 0
        for fname in os.listdir(self.active_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.active_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        job = Job(**data)
                        if job.status in (JobStatus.PENDING, JobStatus.RETRYING, JobStatus.RUNNING):
                            # Mark running jobs from previous crash as RETRYING or PENDING
                            if job.status == JobStatus.RUNNING:
                                job.status = JobStatus.RETRYING
                            self._jobs[job.id] = job
                            heapq.heappush(self._heap, (-job.priority.value, 0.0, job.id))
                            count += 1
                except Exception as e:
                    logger.warning(f"Could not load job {fname}: {e}")
        if count > 0:
            logger.info(f"Restored {count} pending background jobs from durable disk.")

    def _persist_job(self, job: Job) -> None:
        """Writes job to disk atomically."""
        target_dir = self.active_dir
        if job.status == JobStatus.COMPLETED:
            target_dir = self.completed_dir
        elif job.status in (JobStatus.FAILED, JobStatus.CANCELLED):
            target_dir = self.dlq_dir

        target_file = os.path.join(target_dir, f"{job.id}.json")
        temp_file = f"{target_file}.tmp_{os.getpid()}"

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(job.model_dump_json(indent=2))
        os.replace(temp_file, target_file)

        # If completed or DLQ, remove from active_dir if present
        if target_dir != self.active_dir:
            active_file = os.path.join(self.active_dir, f"{job.id}.json")
            if os.path.exists(active_file):
                try:
                    os.remove(active_file)
                except Exception:
                    pass

    def enqueue(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
            self._persist_job(job)
            heapq.heappush(self._heap, (-job.priority.value, 0.0, job.id))
            self._cv.notify()
            logger.info(f"Enqueued job [{job.id}] type={job.job_type.value} priority={job.priority.name}")
            return job

    def dequeue(self, timeout_seconds: float = 1.0) -> Optional[Job]:
        with self._cv:
            start_time = threading.current_thread()
            if not self._heap:
                self._cv.wait(timeout=timeout_seconds)

            if not self._heap:
                return None

            _, _, job_id = heapq.heappop(self._heap)
            job = self._jobs.get(job_id)
            if job and job.status in (JobStatus.PENDING, JobStatus.RETRYING):
                job.status = JobStatus.RUNNING
                self._persist_job(job)
                return job
            return None

    def update_job(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job
            self._persist_job(job)
            if job.status == JobStatus.RETRYING:
                heapq.heappush(self._heap, (-job.priority.value, 0.0, job.id))
                self._cv.notify()

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]

        # Check disk directories
        for d in (self.active_dir, self.completed_dir, self.dlq_dir):
            p = os.path.join(d, f"{job_id}.json")
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return Job(**json.load(f))
                except Exception:
                    pass
        return None

    def list_dlq(self, limit: int = 50) -> List[Job]:
        """Returns failed/dead-letter jobs for administrative inspection."""
        results: List[Job] = []
        if not os.path.exists(self.dlq_dir):
            return results

        files = sorted(os.listdir(self.dlq_dir), reverse=True)[:limit]
        for fname in files:
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self.dlq_dir, fname), "r", encoding="utf-8") as f:
                        results.append(Job(**json.load(f)))
                except Exception:
                    pass
        return results


job_queue = LocalDurableQueue()
