from pathlib import Path

# Repository root — two levels up from app/config.py
BASE_DIR: Path = Path(__file__).resolve().parent.parent

STORAGE_DIR: Path = BASE_DIR / "storage"
# Legacy flat directories (kept for reference; primary storage is now per-user)
RAW_DIR: Path = STORAGE_DIR / "raw"
NORMALIZED_DIR: Path = STORAGE_DIR / "normalized"
REPORTS_DIR: Path = STORAGE_DIR / "reports"
SCHEMAS_DIR: Path = STORAGE_DIR / "schemas"
OVERRIDES_DIR: Path = STORAGE_DIR / "overrides"
# Per-user storage root
USERS_STORAGE_DIR: Path = STORAGE_DIR / "users"
USERS_JSON: Path = USERS_STORAGE_DIR / "users.json"

TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
STATIC_DIR: Path = BASE_DIR / "app" / "static"

ALLOWED_EXTENSIONS: set = {".csv", ".xlsx"}
MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB

APP_TITLE: str = "AutoStat Prep"
APP_VERSION: str = "1.0.0-sprint8"

SCHEMA_VERSION: str = "1.0"


def get_dataset_dir(user_id: str, dataset_id: str) -> Path:
    """Return the per-dataset storage directory: storage/users/{user_id}/datasets/{dataset_id}/"""
    return USERS_STORAGE_DIR / user_id / "datasets" / dataset_id
