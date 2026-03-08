from typing import List

import pandas as pd

from app.models.dataset import Dataset
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def validate_dataset(dataset: Dataset, df: pd.DataFrame) -> None:
    """
    Assert the dataset meets minimum structural requirements.

    All failures raise ValueError with an "FDG:" prefix (fail-loud governance).
    No silent fallbacks — invalid datasets are rejected, not silently repaired.
    """
    logger.info(f"Validating dataset {dataset.dataset_id}")

    _require_at_least_one_column(df)
    _require_at_least_one_row(df)
    _require_non_empty_column_names(df)

    logger.info(f"Dataset {dataset.dataset_id} passed validation.")


# ---------------------------------------------------------------------------
# Private validators
# ---------------------------------------------------------------------------

def _require_at_least_one_column(df: pd.DataFrame) -> None:
    if len(df.columns) == 0:
        raise ValueError("FDG: Dataset has no columns.")


def _require_at_least_one_row(df: pd.DataFrame) -> None:
    if len(df) == 0:
        raise ValueError("FDG: Dataset has no rows.")


def _require_non_empty_column_names(df: pd.DataFrame) -> None:
    empty_positions: List[int] = [
        i for i, col in enumerate(df.columns)
        if not str(col).strip()
    ]
    if empty_positions:
        raise ValueError(
            f"FDG: Dataset has empty or whitespace-only column names "
            f"at positions: {empty_positions}"
        )
