"""
SPSS-compatible column name resolver.

SPSS imposes the following constraints on variable names:
  1. Maximum 64 characters.
  2. Only [a-zA-Z0-9_] characters allowed.
  3. Must not start with a digit.
  4. Names must be unique after all transformations.

This resolver normalises column names to satisfy those constraints, then
deduplicates any collisions that result from truncation.
"""
import re
from typing import List

import pandas as pd

from app.resolvers.base_resolver import BaseResolver

_MAX_LEN = 64
_INVALID_CHARS = re.compile(r"[^a-zA-Z0-9_]")


class SPSSColumnNameResolver(BaseResolver):
    """
    Ensure every column name is SPSS-compatible.

    Transformation steps (applied per column name):
      1. Replace characters outside [a-zA-Z0-9_] with '_'.
      2. If the first character is a digit, prepend 'v_'.
      3. Truncate to 64 characters.
      4. Deduplicate: if the result collides with a name already assigned,
         append '_2', '_3', … (skipping any suffix that would still collide).

    Example:
      "18_which_coordination_tasks_would_you_most_want_ai_to_automate..."
      → "v_18_which_coordination_tasks_would_you_most_want_ai_to_auto"
         (prefix 'v_' added, then truncated to 64 chars)
    """

    @property
    def resolver_name(self) -> str:
        return "SPSSColumnNameResolver"

    @property
    def description(self) -> str:
        return "Normalised column names to SPSS-compatible identifiers"

    def detect(self, df: pd.DataFrame) -> bool:
        return any(
            _spss_name(str(col)) != str(col) or len(str(col)) > _MAX_LEN
            for col in df.columns
        )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        new_cols = _deduplicate([_spss_name(str(col)) for col in df.columns])
        df = df.copy()
        df.columns = new_cols
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        return [str(col) for col in df.columns if _violates_spss(col)]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _violates_spss(col: str) -> bool:
    """Return True if the column name fails any SPSS constraint."""
    col = str(col)
    if len(col) > _MAX_LEN:
        return True
    if _INVALID_CHARS.search(col):
        return True
    if col and col[0].isdigit():
        return True
    return False


def _spss_name(col: str) -> str:
    """Apply rules 1–3 to a single column name (no deduplication)."""
    # Rule 2 — replace invalid characters
    col = _INVALID_CHARS.sub("_", col)
    # Rule 3 — prefix digit-leading names
    if col and col[0].isdigit():
        col = "v_" + col
    # Rule 1 — truncate
    col = col[:_MAX_LEN]
    return col


def _deduplicate(names: List[str]) -> List[str]:
    """Rule 4 — ensure uniqueness by appending numeric suffixes.

    Suffix length is accounted for before appending so the result never
    exceeds _MAX_LEN characters:

        suffix    = f"_{counter}"
        base      = name[: _MAX_LEN - len(suffix)]
        candidate = base + suffix
    """
    assigned: set = set()
    result: List[str] = []

    for name in names:
        if name not in assigned:
            assigned.add(name)
            result.append(name)
        else:
            counter = 2
            while True:
                suffix = f"_{counter}"
                base = name[: _MAX_LEN - len(suffix)]
                candidate = base + suffix
                if candidate not in assigned:
                    break
                counter += 1
            assigned.add(candidate)
            result.append(candidate)

    return result
