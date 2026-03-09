"""
Sprint-4 survey-specific resolvers.

Each resolver handles one class of survey export pathology found in data from
Google Forms, Qualtrics, SurveyMonkey, and manual Excel surveys.
All resolvers are stateless, deterministic, and return new DataFrames.
"""
import re
from typing import List, Set

import pandas as pd

from app.resolvers.base_resolver import BaseResolver


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    """Normalize a string to lowercase_with_underscores."""
    name = str(name).lower()
    name = re.sub(r"[^a-z0-9 _]", "", name)
    name = re.sub(r"[ ]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


# ---------------------------------------------------------------------------
# MultiSelectResolver
# ---------------------------------------------------------------------------

class MultiSelectResolver(BaseResolver):
    """
    Expand multi-select cells (semicolon or pipe separated) into binary
    indicator columns.

    Detects columns where cells contain ';' or '|' and all tokens produced
    by splitting on that delimiter are valid option tokens (not free text).

    Detection criteria (all must hold for at least one delimiter):
      - At least one non-null cell contains the delimiter.
      - Every cell that contains the delimiter splits into ≥ 2 tokens.
      - Every token, after stripping whitespace, is ≤ 30 characters long.
      - Every token contains no internal spaces (i.e. each is a single word).

    This prevents false positives on free-text answers such as
    "Research; development phase" where tokens contain internal spaces.

    Transformation:
      - The original column is replaced by one binary (0/1) column per
        unique option.
      - New column names: {original_column}_{normalized_option_value}
      - A cell that contains an option scores 1; otherwise 0.

    Example:
        Input column "tools": ["Jira;Trello;Asana", "Jira", "Trello;Asana"]
        Output columns:
            tools_asana   [1, 0, 1]
            tools_jira    [1, 1, 0]
            tools_trello  [1, 0, 1]
    """

    _DELIMITERS = (';', '|')
    _MAX_TOKEN_LEN = 30

    @property
    def resolver_name(self) -> str:
        return "MultiSelectResolver"

    @property
    def description(self) -> str:
        return "Expanded multi-select columns into binary indicator columns"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_multi_select_column(df[col]):
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        multi_cols = set(self.get_affected_columns(df))
        parts = []
        for col in df.columns:
            if col in multi_cols:
                parts.append(self._expand_column(df[col], col))
            else:
                parts.append(df[[col]])
        return pd.concat(parts, axis=1)

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        return [
            col for col in df.select_dtypes(include=['object']).columns
            if self._is_multi_select_column(df[col])
        ]

    def _is_multi_select_column(self, series: pd.Series) -> bool:
        values = series.dropna().astype(str)
        if values.empty:
            return False
        for delim in self._DELIMITERS:
            candidate_cells = values[values.str.contains(re.escape(delim), regex=True)]
            if candidate_cells.empty:
                continue
            # Validate every delimited cell: tokens must be ≥2, short, and space-free.
            all_valid = True
            for cell in candidate_cells:
                tokens = [t.strip() for t in cell.split(delim)]
                if len(tokens) < 2:
                    all_valid = False
                    break
                for token in tokens:
                    if not token or len(token) > self._MAX_TOKEN_LEN or ' ' in token:
                        all_valid = False
                        break
                if not all_valid:
                    break
            if all_valid:
                return True
        return False

    def _get_delimiter(self, values: pd.Series) -> str:
        for delim in self._DELIMITERS:
            if values.str.contains(re.escape(delim), regex=True).any():
                return delim
        return self._DELIMITERS[0]

    def _expand_column(self, series: pd.Series, col_name: str) -> pd.DataFrame:
        non_null = series.dropna().astype(str)
        delim = self._get_delimiter(non_null)
        prefix = _norm(col_name)

        all_vals: Set[str] = set()
        for cell in non_null:
            for part in cell.split(delim):
                stripped = part.strip()
                if stripped:
                    all_vals.add(stripped.lower())

        result = {}
        for val in sorted(all_vals):
            new_col = f"{prefix}_{_norm(val)}"
            sep = delim
            result[new_col] = series.apply(
                lambda x, v=val, d=sep: (
                    1 if pd.notna(x) and v in [p.strip().lower() for p in str(x).split(d)]
                    else 0
                )
            )
        return pd.DataFrame(result, index=series.index)


# ---------------------------------------------------------------------------
# DelimitedListResolver
# ---------------------------------------------------------------------------

class DelimitedListResolver(BaseResolver):
    """
    Expand comma-separated list cells into binary indicator columns.

    Handles the generic case where a cell contains multiple short, space-free
    tokens separated by commas — common in Excel survey exports where
    respondents type "A,B,C" rather than using a proper multi-select control.

    Detection criteria (all must hold):
      - At least one non-null cell in the column contains a comma.
      - Every part produced by splitting any non-null cell on ',' is:
          - Non-empty after stripping whitespace.
          - No longer than 30 characters.
          - Contains no internal spaces (i.e., each part is a single token).

    Transformation:
      - Same binary expansion as MultiSelectResolver.

    Example:
        Input column "categories": ["A,B,C", "A,B", "C"]
        Output columns:
            categories_a  [1, 1, 0]
            categories_b  [1, 1, 0]
            categories_c  [1, 0, 1]
    """

    _DELIMITER = ','
    _MAX_PART_LEN = 30

    @property
    def resolver_name(self) -> str:
        return "DelimitedListResolver"

    @property
    def description(self) -> str:
        return "Expanded comma-delimited list columns into binary indicator columns"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_delimited_list_column(df[col]):
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        list_cols = set(self.get_affected_columns(df))
        parts = []
        for col in df.columns:
            if col in list_cols:
                parts.append(self._expand_column(df[col], col))
            else:
                parts.append(df[[col]])
        return pd.concat(parts, axis=1)

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        return [
            col for col in df.select_dtypes(include=['object']).columns
            if self._is_delimited_list_column(df[col])
        ]

    def _is_delimited_list_column(self, series: pd.Series) -> bool:
        values = series.dropna().astype(str)
        if values.empty:
            return False
        if not values.str.contains(self._DELIMITER, regex=False).any():
            return False
        for cell in values:
            parts = [p.strip() for p in cell.split(self._DELIMITER)]
            for part in parts:
                if not part:
                    return False              # empty token — malformed list
                if len(part) > self._MAX_PART_LEN:
                    return False              # too long — likely natural language
                if ' ' in part:
                    return False              # internal space — likely natural language
        return True

    def _expand_column(self, series: pd.Series, col_name: str) -> pd.DataFrame:
        non_null = series.dropna().astype(str)
        prefix = _norm(col_name)
        delim = self._DELIMITER

        all_vals: Set[str] = set()
        for cell in non_null:
            for part in cell.split(delim):
                stripped = part.strip()
                if stripped:
                    all_vals.add(stripped.lower())

        result = {}
        for val in sorted(all_vals):
            new_col = f"{prefix}_{_norm(val)}"
            result[new_col] = series.apply(
                lambda x, v=val, d=delim: (
                    1 if pd.notna(x) and v in [p.strip().lower() for p in str(x).split(d)]
                    else 0
                )
            )
        return pd.DataFrame(result, index=series.index)


# ---------------------------------------------------------------------------
# MultiRowHeaderResolver
# ---------------------------------------------------------------------------

class MultiRowHeaderResolver(BaseResolver):
    """
    Detect and collapse multi-row headers in survey exports.

    Survey tools (especially Qualtrics) often export datasets where the first
    data row is actually a second header row containing the full question text,
    import IDs, or other metadata rather than a real respondent record.

    Detection criterion:
      - The DataFrame has at least 3 rows.
      - The first data row (index 0) has an average string length across
        non-null values greater than 15 characters — indicating descriptive
        metadata text rather than short data values.

    Transformation:
      - The column name and the first-row metadata value are combined and
        normalized to produce a new column name.
      - The first row is then dropped and the index is reset.

    Example:
        Column "Q1", first row "Overall satisfaction with coordination"
        → new column name: "q1_overall_satisfaction_with_coordination"
    """

    _MIN_ROWS = 3
    _MIN_AVG_LEN = 15

    @property
    def resolver_name(self) -> str:
        return "MultiRowHeaderResolver"

    @property
    def description(self) -> str:
        return "Collapsed multi-row header metadata into column names"

    def detect(self, df: pd.DataFrame) -> bool:
        if len(df) < self._MIN_ROWS:
            return False
        return self._first_row_is_metadata(df)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        meta_row = df.iloc[0].fillna("").astype(str).str.strip()
        new_cols = []
        for col, meta in zip(df.columns, meta_row):
            col_norm = _norm(str(col))
            meta_norm = _norm(meta)
            new_cols.append(f"{col_norm}_{meta_norm}" if meta_norm else col_norm)
        result = df.iloc[1:].copy().reset_index(drop=True)
        result.columns = new_cols
        return result

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        return list(df.columns)

    def _first_row_is_metadata(self, df: pd.DataFrame) -> bool:
        row0 = df.iloc[0].dropna().astype(str)
        if row0.empty:
            return False
        avg_len = row0.str.len().mean()
        return bool(avg_len > self._MIN_AVG_LEN)


# ---------------------------------------------------------------------------
# CarryForwardResolver
# ---------------------------------------------------------------------------

class CarryForwardResolver(BaseResolver):
    """
    Convert survey routing artifact strings to NaN.

    Survey tools insert sentinel values when a question was not displayed to
    a respondent due to branching or skip-logic routing. These are not real
    responses and must be treated as missing data.

    Recognized artifact strings (case-insensitive, exact match after strip):
      - "Not displayed"
      - "Question not asked"
      - "Skipped"
      - "N/A (routing)"

    Converts all matching values to pandas NA.
    """

    _ARTIFACTS = frozenset({
        'not displayed',
        'question not asked',
        'skipped',
        'n/a (routing)',
    })

    @property
    def resolver_name(self) -> str:
        return "CarryForwardResolver"

    @property
    def description(self) -> str:
        return "Converted survey routing artifacts to NaN"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.columns:
            values = df[col].dropna().astype(str).str.lower().str.strip()
            if values.isin(self._ARTIFACTS).any():
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            mask = df[col].astype(str).str.lower().str.strip().isin(self._ARTIFACTS)
            df.loc[mask, col] = pd.NA
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.columns:
            values = df[col].dropna().astype(str).str.lower().str.strip()
            if values.isin(self._ARTIFACTS).any():
                affected.append(col)
        return affected
