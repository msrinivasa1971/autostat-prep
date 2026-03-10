"""
Variable type detector — infers statistical type for each column so AutoStat
can choose appropriate tests.

Detection priority (first matching rule wins):

  1. BINARY     — exactly 2 distinct non-null values (any dtype)
  2. ORDINAL    — numeric, all values are integer-valued, the unique values form
                  a contiguous integer sequence, AND that sequence is a subset
                  of a known ordinal range: {1..5}, {1..7}, or {0..10}
  3. CONTINUOUS — numeric dtype with ≥ 3 distinct values
  4. CATEGORICAL — all remaining columns (object dtype, or single-value numeric)
"""
from typing import Dict

import pandas as pd

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Known ordinal ranges checked in order; first match wins.
_ORDINAL_RANGES = (
    frozenset(range(1, 6)),    # {1, 2, 3, 4, 5}
    frozenset(range(1, 8)),    # {1, 2, 3, 4, 5, 6, 7}
    frozenset(range(0, 11)),   # {0, 1, 2, …, 10}
)


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

    # Rule 1 — Binary
    if non_null.nunique() == 2:
        return "binary"

    # Rules 2–3 apply to numeric columns only.
    if pd.api.types.is_numeric_dtype(series):

        # Rule 2 — Ordinal
        if _is_ordinal(non_null):
            return "ordinal"

        # Rule 3 — Continuous (≥ 3 distinct values, not already classified)
        if non_null.nunique() >= 3:
            return "continuous"

    # Rule 4 — Categorical
    return "categorical"


def _is_integer_series(series: pd.Series) -> bool:
    """Return True when every non-null value is integer-valued (e.g. 3.0 → 3)."""
    return series.dropna().apply(lambda v: float(v).is_integer()).all()


def _is_contiguous(int_vals: frozenset) -> bool:
    """Return True when the integer set forms a gap-free sequence."""
    vals = sorted(int_vals)
    return vals == list(range(vals[0], vals[-1] + 1))


def _is_ordinal(non_null: pd.Series) -> bool:
    """
    Return True when:
      - all values are integer-valued,
      - the unique values form a contiguous integer range, and
      - that range is a subset of a known ordinal scale.
    """
    if not _is_integer_series(non_null):
        return False
    try:
        int_vals = frozenset(int(float(v)) for v in non_null.unique())
        return _is_contiguous(int_vals) and any(int_vals <= r for r in _ORDINAL_RANGES)
    except (TypeError, ValueError):
        return False
