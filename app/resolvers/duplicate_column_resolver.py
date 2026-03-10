"""
Content-based duplicate column resolver.

Detects columns whose data is byte-for-byte identical (using pandas hashing),
which is common in Google Forms exports where the same question appears twice.
Keeps the first occurrence and drops subsequent duplicates.
"""
from typing import List

import pandas as pd

from app.resolvers.base_resolver import BaseResolver


class DuplicateDataColumnResolver(BaseResolver):
    """
    Drop columns whose content is identical to an earlier column.

    Google Forms and some Qualtrics exports duplicate columns when a question
    appears in multiple survey blocks. Name-based deduplication (handled by
    DuplicateColumnResolver in structural_resolvers) cannot catch these because
    the two columns may have distinct names after normalization.

    Detection:
      - Compute a row-wise hash vector for each column using
        pd.util.hash_pandas_object.
      - A column is a duplicate if its hash vector is identical to any
        previously seen hash vector.

    Transformation:
      - Keep the first occurrence of each unique content hash.
      - Drop all subsequent duplicates.
    """

    @property
    def resolver_name(self) -> str:
        return "DuplicateDataColumnResolver"

    @property
    def description(self) -> str:
        return "Dropped columns with identical content to an earlier column"

    def detect(self, df: pd.DataFrame) -> bool:
        return len(self._duplicate_columns(df)) > 0

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        duplicates = set(self._duplicate_columns(df))
        return df.drop(columns=list(duplicates))

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        return self._duplicate_columns(df)

    def _duplicate_columns(self, df: pd.DataFrame) -> List[str]:
        seen: dict = {}  # hash tuple → first column name
        duplicates: List[str] = []
        for col in df.columns:
            col_hash = tuple(pd.util.hash_pandas_object(df[col], index=False))
            if col_hash in seen:
                duplicates.append(col)
            else:
                seen[col_hash] = col
        return duplicates
