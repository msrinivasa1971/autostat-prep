import csv
import hashlib
import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, USERS_STORAGE_DIR, get_dataset_dir
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Characters that start an Excel/CSV formula injection payload.
_INJECTION_CHARS = frozenset({"=", "+", "-", "@"})


def save_uploaded_file(
    file_content: bytes,
    original_filename: str,
    user_id: str = "default",
) -> Tuple[str, Path]:
    """
    Save raw uploaded bytes to storage/users/{user_id}/datasets/{dataset_id}/.

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
    dataset_dir = get_dataset_dir(user_id, dataset_id)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dataset_dir / f"{dataset_id}{suffix}"
    dest_path.write_bytes(file_content)

    logger.info(f"Saved uploaded file as {dest_path.name} (dataset_id={dataset_id}, user={user_id})")
    return dataset_id, dest_path


def find_raw_file(dataset_id: str, user_id: Optional[str] = None) -> Optional[Path]:
    """
    Locate the raw file for a dataset.

    If user_id is specified, look only in that user's directory.
    Otherwise scan all user directories.
    """
    if user_id:
        dataset_dir = get_dataset_dir(user_id, dataset_id)
        for ext in ALLOWED_EXTENSIONS:
            candidate = dataset_dir / f"{dataset_id}{ext}"
            if candidate.exists():
                return candidate
        return None

    # Scan all users
    if not USERS_STORAGE_DIR.exists():
        return None
    for user_dir in sorted(USERS_STORAGE_DIR.iterdir()):
        if not user_dir.is_dir():
            continue
        dataset_dir = user_dir / "datasets" / dataset_id
        for ext in ALLOWED_EXTENSIONS:
            candidate = dataset_dir / f"{dataset_id}{ext}"
            if candidate.exists():
                return candidate
    return None


def find_dataset_dir(dataset_id: str, user_id: Optional[str] = None) -> Optional[Path]:
    """
    Return the dataset directory for a given dataset_id.

    If user_id is specified, look only in that user's directory.
    Otherwise scan all users and return the first match.
    Returns None if not found.
    """
    if user_id:
        d = get_dataset_dir(user_id, dataset_id)
        return d if d.exists() else None

    if not USERS_STORAGE_DIR.exists():
        return None
    for user_dir in sorted(USERS_STORAGE_DIR.iterdir()):
        if not user_dir.is_dir():
            continue
        d = user_dir / "datasets" / dataset_id
        if d.exists():
            return d
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
