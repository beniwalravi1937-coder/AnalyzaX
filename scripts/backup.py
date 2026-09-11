"""
AnalyzaX — Phase 22: Automated Production Backup Script.
Packages persistent datasets, lineage, migrations, and metadata
with SHA-256 integrity verification and automated retention pruning.
"""

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import time
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.logging import logger


def calculate_sha256(file_path: str) -> str:
    """Computes cryptographic SHA-256 hash for archive integrity validation."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_backup(dest_dir: str, keep_backups: int = 7) -> str:
    """Creates a timestamped compressed backup archive with SHA-256 manifest."""
    os.makedirs(dest_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_name = f"analyzax_backup_{timestamp}.tar.gz"
    archive_path = os.path.join(dest_dir, archive_name)
    checksum_path = f"{archive_path}.sha256"

    data_root = os.path.abspath(settings.DATA_STORAGE_ROOT)
    logger.info(f"Initiating backup from '{data_root}' -> '{archive_path}'...")

    t0 = time.time()
    # Create compressed archive
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in os.listdir(data_root):
            # Skip temporary directory and socket/lock files
            if item in ("temp", ".migration.lock"):
                continue
            item_path = os.path.join(data_root, item)
            tar.add(item_path, arcname=item)

    # Compute checksum
    sha256_hash = calculate_sha256(archive_path)
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{sha256_hash}  {archive_name}\n")

    dur = round(time.time() - t0, 2)
    size_mb = round(os.path.getsize(archive_path) / (1024 * 1024), 2)
    logger.info(f"Backup created successfully: {archive_name} ({size_mb} MB, SHA-256: {sha256_hash[:12]}...) in {dur}s")

    # Prune old backups
    prune_old_backups(dest_dir, keep_backups)

    return archive_path


def prune_old_backups(dest_dir: str, keep_count: int) -> None:
    """Retains the newest keep_count backup archives and deletes older ones."""
    archives = []
    for f in os.listdir(dest_dir):
        if f.startswith("analyzax_backup_") and f.endswith(".tar.gz"):
            p = os.path.join(dest_dir, f)
            archives.append((os.path.getmtime(p), p))

    archives.sort(reverse=True)
    if len(archives) > keep_count:
        for _, old_path in archives[keep_count:]:
            try:
                os.remove(old_path)
                sha_path = f"{old_path}.sha256"
                if os.path.exists(sha_path):
                    os.remove(sha_path)
                logger.info(f"Pruned older backup: {os.path.basename(old_path)}")
            except Exception as e:
                logger.warning(f"Failed to delete old backup {old_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="AnalyzaX Production Backup Utility")
    parser.add_argument(
        "--dest",
        default="./backups",
        help="Destination directory for backup archives (default: ./backups)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=7,
        help="Number of daily backups to retain (default: 7)",
    )
    args = parser.parse_args()

    try:
        archive = create_backup(args.dest, keep_backups=args.keep)
        print(f"Backup complete: {archive}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
