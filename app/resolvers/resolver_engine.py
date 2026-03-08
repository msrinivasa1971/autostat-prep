"""
Resolver Engine — iterates the resolver registry, detects pathologies,
applies fixes, and returns the cleaned DataFrame with a transformation log.
"""
from typing import Any, Dict, List, Tuple

import pandas as pd

from app.resolvers.base_resolver import BaseResolver
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Type alias for a single log entry
TransformationEntry = Dict[str, Any]


class ResolverEngine:
    """
    Runs an ordered list of resolvers against a DataFrame.

    For each resolver:
      1. Call detect(df) — if False, skip.
      2. Call apply(df)  — returns a new, corrected DataFrame.
      3. Append a log entry recording what changed.

    Returns the final DataFrame and the complete transformation log.
    Only resolvers that fired (detect returned True) appear in the log.
    """

    def __init__(self, resolvers: List[BaseResolver]) -> None:
        self._resolvers = resolvers

    def run(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[TransformationEntry]]:
        """
        Execute all resolvers in registration order.

        Returns:
            (df, log) where df is the fully resolved DataFrame and log is
            a list of dicts describing each transformation that was applied.

        Raises:
            ValueError: (FDG prefix) if any resolver raises an exception,
                        wrapping the original error for governance traceability.
        """
        log: List[TransformationEntry] = []

        for resolver in self._resolvers:
            try:
                if not resolver.detect(df):
                    continue

                rows_before = len(df)
                cols_before = len(df.columns)

                df = resolver.apply(df)

                rows_after = len(df)
                cols_after = len(df.columns)

                entry: TransformationEntry = {
                    "resolver": resolver.resolver_name,
                    "details": resolver.description,
                    "rows_before": rows_before,
                    "rows_after": rows_after,
                    "cols_before": cols_before,
                    "cols_after": cols_after,
                }
                log.append(entry)
                logger.info(
                    f"[Resolver] {resolver.resolver_name} fired — "
                    f"rows {rows_before}→{rows_after}, "
                    f"cols {cols_before}→{cols_after}"
                )

            except Exception as exc:
                raise ValueError(
                    f"FDG: Resolver '{resolver.resolver_name}' failed: {exc}"
                ) from exc

        return df, log
