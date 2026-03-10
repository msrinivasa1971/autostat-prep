"""
Variable type detector — infers statistical type for each column so AutoStat
can choose appropriate tests.

Detection priority (first matching rule wins):

  1. BINARY     — exactly 2 distinct non-null values (any dtype)
  2. ORDINAL    — numeric, all values are integer-valued and form a subset of
                  {1..5} or {1..7} (Likert scales)
  3. CONTINUOUS — numeric dtype with more than 10 distinct values
  4. CATEGORICAL — all remaining columns (object dtype, or sparse numeric)
"""
from typing import Dict

import pandas as pd

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_LIKERT_5 = frozenset({1, 2, 3, 4, 5})
_LIKERT_7 = frozenset({1, 2, 3, 4, 5, 6, 7})
_CONTINUOUS_THRESHOLD = 10


def detect_variable_types(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Infer the statistical type of every column in *df*.

    Returns:
        {
            "column_types": {
                "age":          "continuous",
                "gender":       "binary",
                "satisfaction": "ordinal",
                "country":      "categorical",
            }
        }
    """
    column_types: Dict[str, str] = {}
    for col in df.columns:
        col_type = _detect_type(df[col])
        column_types[col] = col_type
        logger.debug(f"Variable type for '{col}': {col_type}")

    logger.info(f"Variable type detection complete: {len(column_types)} columns")
    return {"column_types": column_types}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _detect_type(series: pd.Series) -> str:
    non_null = series.dropna()

    # Columns that are entirely missing cannot be typed reliably.
    if non_null.empty:
        return "categorical"

    unique_count = non_null.nunique()

    # Rule 1 — Binary
    if unique_count == 2:
        return "binary"

    # Rules 2–3 apply to numeric columns only.
    if pd.api.types.is_numeric_dtype(series):

        # Rule 2 — Ordinal (Likert)
        if _is_likert(non_null):
            return "ordinal"

        # Rule 3 — Continuous
        if unique_count > _CONTINUOUS_THRESHOLD:
            return "continuous"

    # Rule 4 — Categorical (object dtype, or numeric with ≤ 10 unique values)
    return "categorical"


def _is_likert(non_null: pd.Series) -> bool:
    """
    Return True when all values in *non_null* are integer-valued numbers
    that form a subset of {1..5} or {1..7}.
    """
    try:
        unique_floats = non_null.unique()
        # All values must be whole numbers.
        if not all(float(v) == int(float(v)) for v in unique_floats):
            return False
        int_vals = frozenset(int(float(v)) for v in unique_floats)
        return int_vals <= _LIKERT_5 or int_vals <= _LIKERT_7
    except (TypeError, ValueError):
        return False
