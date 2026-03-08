from abc import ABC, abstractmethod
from typing import List

import pandas as pd


class BaseResolver(ABC):
    """
    Abstract base class for all AutoStat Prep resolvers.

    Contract:
      - detect(df) reports whether this resolver's pathology exists in df.
      - apply(df)  returns a new, corrected DataFrame. Input is never mutated.
      - Resolvers are stateless: no instance variables are written during
        detect() or apply(). Identical input always produces identical output.

    Subclasses must implement: resolver_name, detect(), apply().
    Subclasses may override: description.
    """

    @property
    @abstractmethod
    def resolver_name(self) -> str:
        """Unique, stable identifier for this resolver."""
        ...

    @property
    def description(self) -> str:
        """
        Human-readable summary used in the normalization report.

        Subclasses should override this with a more specific message.
        """
        return f"Applied {self.resolver_name}"

    @abstractmethod
    def detect(self, df: pd.DataFrame) -> bool:
        """
        Return True if the pathology this resolver handles is present in df.

        Must not modify df.
        Must be deterministic.
        """
        ...

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a corrected copy of df with the pathology resolved.

        Rules:
          - Never modify the input DataFrame in place.
          - Return a new DataFrame (use df.copy() before any mutation).
          - Must be deterministic: identical input → identical output.
          - Use pandas operations only for data transformations.
        """
        ...

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Return a list of column names that this resolver will modify.

        Called before apply() with the original df.
        Default implementation returns an empty list.
        Subclasses should override if they affect specific columns.
        """
        return []
