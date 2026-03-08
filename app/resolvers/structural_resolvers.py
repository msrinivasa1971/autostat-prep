"""
Sprint-2 structural resolvers.

Each resolver handles one class of structural pathology in a survey dataset.
All resolvers are stateless, deterministic, and return new DataFrames.
"""
import re
from typing import List

import pandas as pd

from app.resolvers.base_resolver import BaseResolver

# ---------------------------------------------------------------------------
# BOMResolver
# ---------------------------------------------------------------------------

_BOM = "\ufeff"


class BOMResolver(BaseResolver):
    """
    Remove a UTF-8 BOM character (\ufeff) from the first column name.

    Defense-in-depth: the dataset loader already strips BOM via utf-8-sig
    encoding, but this resolver guards against other load paths (e.g., XLSX,
    direct DataFrame construction) where the BOM survives into the header.
    """

    @property
    def resolver_name(self) -> str:
        return "BOMResolver"

    @property
    def description(self) -> str:
        return "Removed BOM character (\\ufeff) from first column name"

    def detect(self, df: pd.DataFrame) -> bool:
        return len(df.columns) > 0 and str(df.columns[0]).startswith(_BOM)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        cols = list(df.columns)
        cols[0] = cols[0].lstrip(_BOM)
        df.columns = cols
        return df


# ---------------------------------------------------------------------------
# BlankColumnResolver
# ---------------------------------------------------------------------------

class BlankColumnResolver(BaseResolver):
    """
    Remove columns where every value is blank (empty string or NaN).

    Blank columns carry no information and can corrupt downstream type
    inference. They are dropped unconditionally (AUTO_FIX).
    """

    @property
    def resolver_name(self) -> str:
        return "BlankColumnResolver"

    @property
    def description(self) -> str:
        return "Removed columns where all values were blank"

    def detect(self, df: pd.DataFrame) -> bool:
        return any(_column_is_blank(df[col]) for col in df.columns)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        blank_cols = [col for col in df.columns if _column_is_blank(df[col])]
        return df.drop(columns=blank_cols)


# ---------------------------------------------------------------------------
# BlankRowResolver
# ---------------------------------------------------------------------------

class BlankRowResolver(BaseResolver):
    """
    Remove rows where every value is blank (empty string or NaN).

    Blank rows are common in survey exports with padding or separator lines.
    They are dropped unconditionally and the index is reset (AUTO_FIX).
    """

    @property
    def resolver_name(self) -> str:
        return "BlankRowResolver"

    @property
    def description(self) -> str:
        return "Removed rows where all values were blank"

    def detect(self, df: pd.DataFrame) -> bool:
        # Explicitly cast: pandas .any() returns np.bool_, not Python bool
        return bool(_blank_row_mask(df).any())

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = _blank_row_mask(df)
        return df[~mask].reset_index(drop=True).copy()


# ---------------------------------------------------------------------------
# HeaderNormalizerResolver
# ---------------------------------------------------------------------------

class HeaderNormalizerResolver(BaseResolver):
    """
    Normalize column names to lowercase_with_underscores.

    Transformation steps (applied per column name):
      1. Lowercase
      2. Remove any character that is not alphanumeric, space, or underscore
      3. Replace one or more spaces with a single underscore
      4. Collapse consecutive underscores to one
      5. Strip leading/trailing underscores
      6. Fall back to "unnamed_{index}" if the result is empty

    Example:
      "Project Coordination Satisfaction" → "project_coordination_satisfaction"
      "Q1 (Score)"                        → "q1_score"
      "  ---  "                           → "unnamed_0"
    """

    @property
    def resolver_name(self) -> str:
        return "HeaderNormalizerResolver"

    @property
    def description(self) -> str:
        return "Normalized column names to lowercase_with_underscores"

    def detect(self, df: pd.DataFrame) -> bool:
        return any(_normalize_name(str(col)) != str(col) for col in df.columns)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        new_names = [
            _normalize_name(str(col)) or f"unnamed_{i}"
            for i, col in enumerate(df.columns)
        ]
        df = df.copy()
        df.columns = new_names
        return df


# ---------------------------------------------------------------------------
# DuplicateColumnResolver
# ---------------------------------------------------------------------------

class DuplicateColumnResolver(BaseResolver):
    """
    Rename duplicate column names by appending a numeric suffix.

    Duplicates most commonly arise when HeaderNormalizerResolver maps two
    distinct original names to the same normalized form
    (e.g., "Project Score" and "Project_Score" both → "project_score").

    Renaming strategy: the first occurrence keeps its name; subsequent
    occurrences become name_2, name_3, … (skipping any suffix that would
    collide with an already-assigned name).

    Example: [q1, q2, q1] → [q1, q2, q1_2]
    """

    @property
    def resolver_name(self) -> str:
        return "DuplicateColumnResolver"

    @property
    def description(self) -> str:
        return "Renamed duplicate column names with numeric suffixes"

    def detect(self, df: pd.DataFrame) -> bool:
        return len(df.columns) != len(set(df.columns))

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        new_cols: List[str] = []
        assigned: set = set()
        next_counter: dict = {}   # base_name → next counter to try

        for col in df.columns:
            col = str(col)
            if col not in assigned:
                new_cols.append(col)
                assigned.add(col)
            else:
                counter = next_counter.get(col, 2)
                candidate = f"{col}_{counter}"
                while candidate in assigned:
                    counter += 1
                    candidate = f"{col}_{counter}"
                next_counter[col] = counter + 1
                new_cols.append(candidate)
                assigned.add(candidate)

        df = df.copy()
        df.columns = new_cols
        return df


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _column_is_blank(series: pd.Series) -> bool:
    """True if every value in the series is NaN or an empty string."""
    return series.apply(lambda x: pd.isna(x) or str(x) == "").all()


def _blank_row_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask — True for rows where every value is NaN or empty string."""
    return df.apply(lambda row: all(pd.isna(v) or str(v) == "" for v in row), axis=1)


def _normalize_name(name: str) -> str:
    """Apply the header normalization rules to a single column name string."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9 _]", "", name)   # keep letters, digits, spaces, underscores
    name = re.sub(r" +", "_", name)            # spaces → underscore
    name = re.sub(r"_+", "_", name)            # collapse consecutive underscores
    name = name.strip("_")
    return name
