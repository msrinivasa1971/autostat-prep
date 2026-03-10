"""
Tests for app/services/variable_type_detector.py

Run with:  pytest tests/test_variable_type_detector.py -v
"""
import pandas as pd
import pytest

from app.services.variable_type_detector import detect_variable_types


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _types(df: pd.DataFrame) -> dict:
    """Return just the column_types dict from detect_variable_types."""
    return detect_variable_types(df)["column_types"]


# ---------------------------------------------------------------------------
# Binary detection
# ---------------------------------------------------------------------------

class TestBinaryDetection:
    def test_numeric_zero_one(self):
        df = pd.DataFrame({"flag": [0, 1, 0, 1, 1]})
        assert _types(df)["flag"] == "binary"

    def test_string_two_values(self):
        df = pd.DataFrame({"gender": ["M", "F", "M", "F"]})
        assert _types(df)["gender"] == "binary"

    def test_boolean_column(self):
        df = pd.DataFrame({"active": [True, False, True, False]})
        assert _types(df)["active"] == "binary"

    def test_binary_ignores_nulls(self):
        # NaN should not count as a third unique value.
        df = pd.DataFrame({"x": [0, 1, None, 0, 1]})
        assert _types(df)["x"] == "binary"


# ---------------------------------------------------------------------------
# Ordinal detection
# ---------------------------------------------------------------------------

class TestOrdinalDetection:
    def test_likert_5_int(self):
        df = pd.DataFrame({"satisfaction": [1, 2, 3, 4, 5, 3, 2, 1]})
        assert _types(df)["satisfaction"] == "ordinal"

    def test_likert_7_int(self):
        df = pd.DataFrame({"rating": [1, 2, 3, 4, 5, 6, 7, 4, 3]})
        assert _types(df)["rating"] == "ordinal"

    def test_likert_partial_range(self):
        # {1, 3, 5} is a subset of {1..5} → ordinal
        df = pd.DataFrame({"q": [1, 3, 5, 1, 3]})
        assert _types(df)["q"] == "ordinal"

    def test_likert_float_values(self):
        # Integer-valued floats like 1.0, 2.0, 3.0 should be recognised.
        df = pd.DataFrame({"score": [1.0, 2.0, 3.0, 4.0, 5.0, 3.0]})
        assert _types(df)["score"] == "ordinal"

    def test_likert_with_nulls(self):
        df = pd.DataFrame({"q": [1, 2, 3, None, 4, 5]})
        assert _types(df)["q"] == "ordinal"

    def test_non_likert_range_not_ordinal(self):
        # {1, 2, 3, 8, 9} is not a subset of either Likert set.
        df = pd.DataFrame({"x": [1, 2, 3, 8, 9, 1, 2]})
        assert _types(df)["x"] != "ordinal"

    def test_float_non_integer_not_ordinal(self):
        # 1.5 is not integer-valued → not Likert.
        df = pd.DataFrame({"x": [1.0, 1.5, 2.0, 3.0, 4.0]})
        assert _types(df)["x"] != "ordinal"


# ---------------------------------------------------------------------------
# Continuous detection
# ---------------------------------------------------------------------------

class TestContinuousDetection:
    def test_numeric_many_unique(self):
        df = pd.DataFrame({"age": list(range(20, 70))})  # 50 unique values
        assert _types(df)["age"] == "continuous"

    def test_float_many_unique(self):
        df = pd.DataFrame({"weight": [i * 0.7 for i in range(30)]})
        assert _types(df)["weight"] == "continuous"

    def test_numeric_eleven_unique(self):
        # Exactly 11 unique values → crosses the > 10 threshold.
        df = pd.DataFrame({"x": list(range(11))})
        assert _types(df)["x"] == "continuous"

    def test_numeric_ten_unique_not_continuous(self):
        # Exactly 10 unique values → NOT continuous (≤ 10 → categorical).
        df = pd.DataFrame({"x": list(range(10))})
        assert _types(df)["x"] != "continuous"


# ---------------------------------------------------------------------------
# Categorical detection
# ---------------------------------------------------------------------------

class TestCategoricalDetection:
    def test_string_many_unique(self):
        df = pd.DataFrame({"country": ["US", "UK", "DE", "FR", "JP", "CA", "AU"]})
        assert _types(df)["country"] == "categorical"

    def test_numeric_few_unique(self):
        # 5 unique numeric values but NOT in Likert range → categorical.
        df = pd.DataFrame({"code": [10, 20, 30, 40, 50, 10, 20]})
        assert _types(df)["code"] == "categorical"

    def test_object_dtype(self):
        df = pd.DataFrame({"notes": ["good", "bad", "ok", "good", "bad"]})
        # 3 unique values → not binary, not numeric → categorical
        assert _types(df)["notes"] == "categorical"

    def test_all_null_column(self):
        df = pd.DataFrame({"empty": [None, None, None]})
        assert _types(df)["empty"] == "categorical"


# ---------------------------------------------------------------------------
# Return structure
# ---------------------------------------------------------------------------

class TestReturnStructure:
    def test_returns_column_types_key(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = detect_variable_types(df)
        assert "column_types" in result

    def test_covers_all_columns(self):
        df = pd.DataFrame({
            "age":          list(range(20, 70)),
            "gender":       ["M", "F"] * 25,
            "satisfaction": [1, 2, 3, 4, 5] * 10,
            "country":      ["US", "UK", "DE", "FR", "JP"] * 10,
        })
        result = detect_variable_types(df)
        assert set(result["column_types"].keys()) == set(df.columns)

    def test_mixed_dataset(self):
        df = pd.DataFrame({
            "age":          list(range(20, 70)),           # continuous
            "gender":       ["M", "F"] * 25,               # binary
            "satisfaction": [1, 2, 3, 4, 5] * 10,         # ordinal
            "country":      ["US", "UK", "DE", "FR", "JP"] * 10,  # categorical
        })
        ct = _types(df)
        assert ct["age"] == "continuous"
        assert ct["gender"] == "binary"
        assert ct["satisfaction"] == "ordinal"
        assert ct["country"] == "categorical"
