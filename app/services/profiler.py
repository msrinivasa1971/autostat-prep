from typing import List

import pandas as pd

from app.models.dataset import Dataset
from app.models.schema import ColumnSchema
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Sprint-1: all columns are typed as TEXT.
# Future sprints will introduce LikertScaleResolver, BooleanResolver, etc.
_DEFAULT_COLUMN_TYPE = "TEXT"


def profile_dataset(dataset: Dataset, df: pd.DataFrame) -> List[ColumnSchema]:
    """
    Compute per-column statistics and return a list of ColumnSchema objects.

    missing_ratio — fraction of cells that are empty or NaN (0.0–1.0, 4 d.p.)
    unique_values — count of distinct non-null values
    column_type   — always TEXT in Sprint-1
    """
    logger.info(f"Profiling dataset {dataset.dataset_id}")

    schemas: List[ColumnSchema] = []
    total_rows = len(df)

    for col in df.columns:
        null_count = df[col].isna().sum() + (df[col] == "").sum()
        missing_ratio = float(null_count / total_rows) if total_rows > 0 else 0.0
        unique_values = int(df[col].replace("", pd.NA).nunique(dropna=True))

        schemas.append(
            ColumnSchema(
                column_name=col,
                column_type=_DEFAULT_COLUMN_TYPE,
                missing_ratio=round(missing_ratio, 4),
                unique_values=unique_values,
            )
        )

    logger.info(f"Profiling complete for {dataset.dataset_id}: {len(schemas)} columns")
    return schemas
