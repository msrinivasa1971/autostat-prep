from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import pandas as pd

from app.models.dataset import Dataset
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# utf-8-sig handles BOM-prefixed files produced by Windows tools
_CSV_READ_KWARGS = {"encoding": "utf-8-sig", "dtype": str, "keep_default_na": False}

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_formula_injection(value):
    """
    Treat spreadsheet formula-like cell values as plain text by prepending a
    single quote. This prevents formula injection rather than rejecting the file.
    """
    if value is None:
        return value
    s = str(value).strip()
    if s.startswith(_FORMULA_PREFIXES):
        return "'" + s
    return value


def load_dataset(dataset_id: str, file_path: Path) -> Tuple[Dataset, pd.DataFrame]:
    """
    Load a CSV or XLSX file into a DataFrame and return a Dataset descriptor.

    All columns are read as str in Sprint-1 (type inference happens in the profiler).
    Raises ValueError for unsupported formats or unreadable files.
    """
    logger.info(f"Loading dataset {dataset_id} from {file_path.name}")

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(file_path, **_CSV_READ_KWARGS)
    elif suffix == ".xlsx":
        df = pd.read_excel(file_path, engine="openpyxl", dtype=str, keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file format: '{suffix}'")

    df = df.apply(lambda col: col.map(sanitize_formula_injection))

    dataset = Dataset(
        dataset_id=dataset_id,
        file_path=str(file_path),
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
        created_at=datetime.now(timezone.utc),
    )

    logger.info(
        f"Dataset {dataset_id} loaded: {dataset.row_count} rows × {dataset.column_count} columns"
    )
    return dataset, df
