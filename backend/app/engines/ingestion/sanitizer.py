import os
import re
import secrets
import time


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user-provided filename to prevent directory traversal,
    null byte attacks, and filesystem injection.

    Rules:
    - Strips all leading directory components (e.g. ../../, C:\\, etc.)
    - Removes null bytes and forbidden characters
    - Replaces whitespace with underscores
    - Preserves a clean alphanumeric base and extension
    """
    if not filename:
        return f"dataset_{int(time.time())}.dat"

    # Strip directory paths
    base_name = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes
    base_name = base_name.replace("\x00", "")

    # Split name and extension
    parts = base_name.rsplit(".", 1)
    name_part = parts[0]
    ext_part = ("." + parts[1].lower()) if len(parts) > 1 else ""

    # Clean name part: keep only alphanumeric, hyphen, underscore
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_part)
    clean_name = re.sub(r"_+", "_", clean_name).strip("_")

    if not clean_name:
        clean_name = f"dataset_{int(time.time())}"

    # Clean extension: only alphanumeric
    clean_ext = re.sub(r"[^a-zA-Z0-9.]", "", ext_part)

    # Limit length
    if len(clean_name) > 80:
        clean_name = clean_name[:80]

    return f"{clean_name}{clean_ext}"


def generate_dataset_id() -> str:
    """
    Generates a collision-resistant, URL-safe dataset identifier.
    Format: ds_<timestamp_hex><random_token>
    Example: ds_66dd8f12a3bc49f81b
    """
    timestamp_hex = hex(int(time.time()))[2:]
    random_hex = secrets.token_hex(8)
    return f"ds_{timestamp_hex}{random_hex}"


def generate_safe_sql_identifier(dataset_id: str) -> str:
    """
    Generates a safe, SQL-compliant table/view identifier for DuckDB.
    Guarantees no SQL injection or unexpected identifier quoting issues.
    """
    if not dataset_id or not re.match(r"^ds_[a-zA-Z0-9_]+$", dataset_id):
        raise ValueError(f"Invalid dataset ID format: '{dataset_id}'. Must match '^ds_[a-zA-Z0-9_]+$'.")

    return f"dataset_{dataset_id}"
