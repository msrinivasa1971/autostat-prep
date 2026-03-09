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

# Type alias for a single trace entry
TraceEntry = Dict[str, Any]


class ResolverEngine:
    """
    Runs an ordered list of resolvers against a DataFrame.

    For each resolver:
      1. Call detect(df) — record the result in resolver_trace regardless.
      2. If detect returned False, skip apply.
      3. Call apply(df)  — returns a new, corrected DataFrame.
      4. Append a transformation log entry recording what changed.

    After run() completes:
      - resolver_trace  contains one entry per resolver (detected or not).
      - transformation_log contains entries only for resolvers that applied.
    """

    def __init__(self, resolvers: List[BaseResolver]) -> None:
        self._resolvers = resolvers
        self.resolver_trace: List[TraceEntry] = []

    def run(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[TransformationEntry]]:
        """
        Execute all resolvers in registration order.

        Populates self.resolver_trace with one entry per resolver:
            {resolver, detected, applied, affected_columns}

        Returns:
            (df, log) where df is the fully resolved DataFrame and log is
            a list of dicts describing each transformation that was applied.
            Only resolvers that fired (detect returned True) appear in log.

        Raises:
            ValueError: (FDG prefix) if any resolver raises an exception,
                        wrapping the original error for governance traceability.
        """
        log: List[TransformationEntry] = []
        self.resolver_trace = []

        for resolver in self._resolvers:
            try:
                detected = resolver.detect(df)

                if not detected:
                    self.resolver_trace.append({
                        "resolver": resolver.resolver_name,
                        "detected": False,
                        "applied": False,
                        "affected_columns": [],
                    })
                    continue

                rows_before = len(df)
                cols_before = len(df.columns)
                affected_columns = resolver.get_affected_columns(df)

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
                    "affected_columns": affected_columns,
                }
                log.append(entry)

                self.resolver_trace.append({
                    "resolver": resolver.resolver_name,
                    "detected": True,
                    "applied": True,
                    "affected_columns": affected_columns,
                })

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
