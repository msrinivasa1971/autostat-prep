"""
Sprint-3 encoding resolvers.

Each resolver handles one class of encoding pathology in a survey dataset.
All resolvers are stateless, deterministic, and return new DataFrames.
"""
import re
from typing import List

import pandas as pd

from app.resolvers.base_resolver import BaseResolver


# ---------------------------------------------------------------------------
# BooleanResolver
# ---------------------------------------------------------------------------

class BooleanResolver(BaseResolver):
    """
    Convert boolean-like text values to numeric 1/0.

    Detects columns where values are predominantly:
      - Yes/No, True/False, Y/N (case insensitive)

    Converts:
      - Yes, True, Y → 1
      - No, False, N → 0

    Ignores NaN and other values.
    """

    @property
    def resolver_name(self) -> str:
        return "BooleanResolver"

    @property
    def description(self) -> str:
        return "Converted boolean text to numeric (1/0)"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            values = df[col].dropna().astype(str).str.lower()
            if values.empty:
                continue
            boolean_values = {'yes', 'no', 'true', 'false', 'y', 'n'}
            if values.isin(boolean_values).all():
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        mapping = {
            'yes': 1, 'true': 1, 'y': 1,
            'no': 0, 'false': 0, 'n': 0
        }
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_boolean_column(df[col]):
                df[col] = df[col].astype(str).str.lower().map(mapping).fillna(df[col])
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_boolean_column(df[col]):
                affected.append(col)
        return affected

    def _is_boolean_column(self, series: pd.Series) -> bool:
        values = series.dropna().astype(str).str.lower()
        if values.empty:
            return False
        boolean_values = {'yes', 'no', 'true', 'false', 'y', 'n'}
        return values.isin(boolean_values).all()


# ---------------------------------------------------------------------------
# LikertScaleResolver
# ---------------------------------------------------------------------------

class LikertScaleResolver(BaseResolver):
    """
    Convert Likert scale text to numeric 1-5.

    Detects common Likert patterns and maps to 1-5 scale.

    Mapping:
      - Strongly Disagree → 1
      - Disagree → 2
      - Neutral → 3
      - Agree → 4
      - Strongly Agree → 5

    Case insensitive, handles variations.
    """

    _likert_mapping = {
        'strongly disagree': 1, 'disagree': 2, 'neutral': 3, 'agree': 4, 'strongly agree': 5,
        'sd': 1, 'd': 2, 'n': 3, 'a': 4, 'sa': 5,
        'very dissatisfied': 1, 'dissatisfied': 2, 'satisfied': 3, 'very satisfied': 4,  # adjust as needed
    }

    @property
    def resolver_name(self) -> str:
        return "LikertScaleResolver"

    @property
    def description(self) -> str:
        return "Converted Likert scale to numeric (1–5)"

    _likert_detection_values = {
        'strongly disagree', 'disagree', 'neutral', 'agree', 'strongly agree',
    }

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            values = df[col].dropna().astype(str).str.lower().str.strip()
            if values.empty:
                continue
            if values.isin(self._likert_detection_values).all():
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_likert_column(df[col]):
                df[col] = df[col].astype(str).str.lower().str.strip().map(self._likert_mapping).fillna(df[col])
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_likert_column(df[col]):
                affected.append(col)
        return affected

    def _is_likert_column(self, series: pd.Series) -> bool:
        values = series.dropna().astype(str).str.lower().str.strip()
        if values.empty:
            return False
        return values.isin(self._likert_detection_values).all()


# ---------------------------------------------------------------------------
# PercentResolver
# ---------------------------------------------------------------------------

class PercentResolver(BaseResolver):
    """
    Convert percent strings to decimal values.

    Detects values ending with '%'.

    Converts "45%" → 0.45
    """

    @property
    def resolver_name(self) -> str:
        return "PercentResolver"

    @property
    def description(self) -> str:
        return "Converted percent strings to decimal values"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            values = df[col].dropna().astype(str)
            if values.str.endswith('%').sum() > 0:
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_percent_column(df[col]):
                df[col] = df[col].astype(str).str.rstrip('%').astype(float) / 100
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_percent_column(df[col]):
                affected.append(col)
        return affected

    def _is_percent_column(self, series: pd.Series) -> bool:
        values = series.dropna().astype(str)
        return values.str.endswith('%').sum() > 0


# ---------------------------------------------------------------------------
# NumericTextResolver
# ---------------------------------------------------------------------------

class NumericTextResolver(BaseResolver):
    """
    Convert numeric strings to numeric dtype.

    Detects columns where all non-null values are numeric strings.

    Converts dtype to numeric.
    """

    @property
    def resolver_name(self) -> str:
        return "NumericTextResolver"

    @property
    def description(self) -> str:
        return "Converted numeric text to numeric dtype"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_numeric_text_column(df[col]):
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_numeric_text_column(df[col]):
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.select_dtypes(include=['object']).columns:
            if self._is_numeric_text_column(df[col]):
                affected.append(col)
        return affected

    _id_keywords = ('id', 'code', 'identifier')

    def _is_numeric_text_column(self, series: pd.Series) -> bool:
        col_name = str(series.name).lower()
        if any(kw in col_name for kw in self._id_keywords):
            return False
        values = series.dropna().astype(str)
        if values.empty:
            return False
        # Check if all values can be converted to numeric
        try:
            pd.to_numeric(values, errors='raise')
            return True
        except (ValueError, TypeError):
            return False


# ---------------------------------------------------------------------------
# MissingValueResolver
# ---------------------------------------------------------------------------

class MissingValueResolver(BaseResolver):
    """
    Normalize common missing value indicators to pandas NaN.

    Converts: NA, N/A, null, "", " "

    Case insensitive for text.
    """

    _missing_indicators = {'na', 'n/a', 'null', '', ' '}

    @property
    def resolver_name(self) -> str:
        return "MissingValueResolver"

    @property
    def description(self) -> str:
        return "Normalized missing value indicators to NaN"

    def detect(self, df: pd.DataFrame) -> bool:
        for col in df.columns:
            values = df[col].dropna().astype(str).str.lower().str.strip()
            if values.isin(self._missing_indicators).sum() > 0:
                return True
        return False

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            mask = df[col].astype(str).str.lower().str.strip().isin(self._missing_indicators)
            df.loc[mask, col] = pd.NA
        return df

    def get_affected_columns(self, df: pd.DataFrame) -> List[str]:
        affected = []
        for col in df.columns:
            values = df[col].dropna().astype(str).str.lower().str.strip()
            if values.isin(self._missing_indicators).sum() > 0:
                affected.append(col)
        return affected