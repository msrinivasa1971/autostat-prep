import csv
import hashlib
import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.config import RAW_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Characters that start an Excel/CSV formula injection payload.
_INJECTION_CHARS = frozenset({"=", "+", "-", "@"})


def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, Path]:
    """
    Save raw uploaded bytes to storage/raw/.

    Returns (dataset_id, dest_path).
    Raises ValueError for unsupported extensions, oversized files, or
    detected CSV formula injection.
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

    if suffix == ".csv":
        _check_formula_injection(file_content)

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


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file using streaming reads.

    Reads the file in 64 KB chunks to avoid loading the entire file into memory.
    Returns the hex digest string.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _check_formula_injection(content: bytes) -> None:
    """
    Parse CSV bytes and raise ValueError if any cell starts with a formula
    injection character (=, +, -, @).

    Only called for CSV uploads.
    """
    try:
        text = content.decode("utf-8-sig", errors="replace")
    except Exception:
        return  # Cannot decode — let the loader surface the error later

    reader = csv.reader(io.StringIO(text))
    for row in reader:
        for cell in row:
            if cell and cell[0] in _INJECTION_CHARS:
                raise ValueError(
                    f"Upload rejected: potential formula injection detected "
                    f"in cell starting with {cell[0]!r}: {cell[:40]!r}"
                )
