"""
Migration 002: Asynchronous Jobs Ledger.
Creates the durable job execution registry foundation for Phase 22.
"""

import os
from backend.app.core.config import settings
from backend.app.core.logging import logger


def upgrade() -> None:
    """Applies forward migration."""
    logger.info("Executing Migration 002 upgrade: creating jobs ledger storage.")
    jobs_dir = os.path.abspath(getattr(settings, "DATA_JOBS_DIR", "./data/jobs"))
    os.makedirs(jobs_dir, exist_ok=True)
    os.makedirs(os.path.join(jobs_dir, "dlq"), exist_ok=True)


def downgrade() -> None:
    """Safe rollback."""
    logger.info("Executing Migration 002 downgrade.")
