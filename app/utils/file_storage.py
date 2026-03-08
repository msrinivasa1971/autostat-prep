import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.config import RAW_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, Path]:
    """
    Save raw uploaded bytes to storage/raw/.

    Returns (dataset_id, dest_path).
    Raises ValueError for unsupported extensions or oversized files.
    """
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    dataset_id = str(uuid.uuid4())
    dest_path = RAW_DIR / f"{dataset_id}{suffix}"
    dest_path.write_bytes(file_content)

    logger.info(f"Saved uploaded file as {dest_path.name} (dataset_id={dataset_id})")
    return dataset_id, dest_path


def find_raw_file(dataset_id: str) -> Optional[Path]:
    """
    Locate the raw file for a given dataset_id regardless of extension.
    Returns None if not found.
    """
    for ext in ALLOWED_EXTENSIONS:
        candidate = RAW_DIR / f"{dataset_id}{ext}"
        if candidate.exists():
            return candidate
    return None
