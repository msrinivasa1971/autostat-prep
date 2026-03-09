from pathlib import Path

# Repository root — two levels up from app/config.py
BASE_DIR: Path = Path(__file__).resolve().parent.parent

STORAGE_DIR: Path = BASE_DIR / "storage"
RAW_DIR: Path = STORAGE_DIR / "raw"
NORMALIZED_DIR: Path = STORAGE_DIR / "normalized"
REPORTS_DIR: Path = STORAGE_DIR / "reports"
SCHEMAS_DIR: Path = STORAGE_DIR / "schemas"

ALLOWED_EXTENSIONS: set = {".csv", ".xlsx"}
MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB

APP_TITLE: str = "AutoStat Prep"
APP_VERSION: str = "1.0.0-sprint5"

SCHEMA_VERSION: str = "1.0"
