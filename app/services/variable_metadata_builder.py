"""
Variable metadata builder — enriches schema.json with per-column label maps
useful for SPSS import and AutoStat statistical tests.

Rules by detected type:

  binary      — map the two distinct values to integer keys 1 and 2,
                preserving the original text as labels.
  ordinal     — record the sorted unique values as an ordered label map;
                if values are already the standard 1–5 / 1–7 Likert integers,
                attach the canonical Likert text labels.
  categorical — capture up to MAX_CATEGORICAL_LABELS unique values as a
                sorted label list.
  continuous  — no labels produced (statistical tests use the raw numeric
                distribution).
"""
from typing import Any, Dict

import pandas as pd

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

MAX_CATEGORICAL_LABELS = 20

_LIKERT_5_LABELS = {
    1: "Strongly Disagree",
    2: "Disagree",
    3: "Neutral",
    4: "Agree",
    5: "Strongly Agree",
}
_LIKERT_7_LABELS = {
    1: "Strongly Disagree",
    2: "Disagree",
    3: "Somewhat Disagree",
    4: "Neutral",
    5: "Somewhat Agree",
    6: "Agree",
    7: "Strongly Agree",
}


def build_variable_metadata(
    df: pd.DataFrame,
    column_types: Dict[str, str],
) -> Dict[str, Any]:
    """
    Build per-column metadata for every column in *df*.

    Args:
        df:           Normalized DataFrame (post-pipeline).
        column_types: Mapping of column name → statistical type string
                      as produced by detect_variable_types().

    Returns:
        {
            "column_metadata": {
                "gender":       {"labels": {"1": "Male", "2": "Female"}},
                "satisfaction": {"labels": {"1": "Strongly Disagree", ...}},
                "country":      {"values": ["AU", "DE", "FR", ...]},
                "age":          {}
            }
        }
    """
    column_metadata: Dict[str, Any] = {}

    for col in df.columns:
        col_type = column_types.get(col, "categorical")
        meta = _build_column_meta(df[col], col_type)
        column_metadata[col] = meta
        logger.debug(f"Metadata for '{col}' ({col_type}): {meta}")

    logger.info(f"Variable metadata built for {len(column_metadata)} columns")
    return {"column_metadata": column_metadata}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_column_meta(series: pd.Series, col_type: str) -> Dict[str, Any]:
    non_null = series.dropna()

    if col_type == "binary":
        return _binary_meta(non_null)

    if col_type == "ordinal":
        return _ordinal_meta(non_null)

    if col_type == "categorical":
        return _categorical_meta(non_null)

    if col_type == "continuous":
        return {}

    # Unknown type — treat as categorical (safe fallback).
    return _categorical_meta(non_null)


def _binary_meta(non_null: pd.Series) -> Dict[str, Any]:
    """Map the two distinct values to integer keys 1 and 2."""
    distinct = sorted(non_null.unique(), key=lambda v: str(v))
    labels = {str(i + 1): str(v) for i, v in enumerate(distinct)}
    return {"labels": labels}


def _ordinal_meta(non_null: pd.Series) -> Dict[str, Any]:
    """
    For standard Likert ranges use canonical text labels.
    For other ordinal columns record sorted unique values as label map.
    """
    if pd.api.types.is_numeric_dtype(non_null):
        try:
            int_vals = frozenset(int(float(v)) for v in non_null.unique())
            if int_vals <= frozenset(_LIKERT_5_LABELS):
                labels = {str(k): v for k, v in _LIKERT_5_LABELS.items() if k in int_vals}
                return {"labels": labels}
            if int_vals <= frozenset(_LIKERT_7_LABELS):
                labels = {str(k): v for k, v in _LIKERT_7_LABELS.items() if k in int_vals}
                return {"labels": labels}
        except (TypeError, ValueError):
            pass

    # Non-standard ordinal: preserve sorted unique values as an ordered map.
    sorted_vals = sorted(non_null.unique(), key=lambda v: (str(type(v)), str(v)))
    labels = {str(i + 1): str(v) for i, v in enumerate(sorted_vals)}
    return {"labels": labels}


def _categorical_meta(non_null: pd.Series) -> Dict[str, Any]:
    """Capture up to MAX_CATEGORICAL_LABELS unique values as a sorted list."""
    unique_vals = sorted(non_null.unique(), key=str)
    values = [str(v) for v in unique_vals[:MAX_CATEGORICAL_LABELS]]
    return {"values": values}
