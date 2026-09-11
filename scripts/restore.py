"""
AnalyzaX — Phase 22: Disaster Recovery & Restore Verification Utility.
Verifies SHA-256 archive checksums and safely restores data assets to target directories.
"""

import argparse
import hashlib
import os
import sys
import tarfile
import tempfile
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.logging import logger


def verify_sha256(archive_path: str, expected_hash: str) -> bool:
    """Verifies file checksum against expected SHA-256."""
    hasher = hashlib.sha256()
    with open(archive_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()
    return actual_hash.strip().lower() == expected_hash.strip().lower()


def restore_backup(archive_path: str, target_dir: str, verify_only: bool = False) -> bool:
    """Restores backup archive after cryptographic verification."""
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    checksum_file = f"{archive_path}.sha256"
    if os.path.exists(checksum_file):
        with open(checksum_file, "r", encoding="utf-8") as f:
            line = f.readline()
            expected_hash = line.split()[0]
        logger.info(f"Verifying SHA-256 checksum: {expected_hash[:12]}...")
        if not verify_sha256(archive_path, expected_hash):
            raise ValueError(f"CRITICAL: Checksum verification FAILED for {archive_path}!")
        logger.info("Checksum verification PASSED.")
    else:
        logger.warning(f"No .sha256 checksum file found for {archive_path}. Proceeding with caution.")

    if verify_only:
        logger.info(f"Running integrity verification on archive structure...")
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            logger.info(f"Archive valid. Contains {len(members)} entries.")
        return True

    logger.info(f"Restoring {archive_path} -> {target_dir}...")
    os.makedirs(target_dir, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=target_dir)

    logger.info(f"Restore successfully completed to '{target_dir}'.")
    return True


def main():
    parser = argparse.ArgumentParser(description="AnalyzaX Disaster Recovery Restore Utility")
    parser.add_argument("archive", help="Path to .tar.gz backup archive")
    parser.add_argument("--target", default="./data", help="Target restore directory (default: ./data)")
    parser.add_argument("--verify-only", action="store_true", help="Test archive integrity without restoring")
    args = parser.parse_args()

    try:
        ok = restore_backup(args.archive, args.target, verify_only=args.verify_only)
        if ok:
            print("Restore validation succeeded.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
