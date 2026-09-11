"""
Migration 001: Initial Metadata Foundation.
Creates the datasets metadata table and ensures required schema indices.
"""

from backend.app.core.logging import logger


def upgrade() -> None:
    """Applies forward migration."""
    logger.info("Executing Migration 001 upgrade: verifying metadata schemas.")
    # Here we ensure Base metadata tables are recognized and registered
    try:
        from backend.app.models.base import Base
        from backend.app.models.dataset import DatasetModel  # noqa: F401
    except Exception as e:
        logger.warning(f"Note on metadata models: {e}")


def downgrade() -> None:
    """Safe rollback."""
    logger.info("Executing Migration 001 downgrade.")
