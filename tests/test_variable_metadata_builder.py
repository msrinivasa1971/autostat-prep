"""
Tests for app/services/variable_metadata_builder.py

Run with:  pytest tests/test_variable_metadata_builder.py -v
"""
import pandas as pd
import pytest

from app.services.variable_metadata_builder import (
    MAX_CATEGORICAL_LABELS,
    build_variable_metadata,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _meta(df: pd.DataFrame, column_types: dict) -> dict:
    return build_variable_metadata(df, column_types)["column_metadata"]


# ---------------------------------------------------------------------------
# Binary
# ---------------------------------------------------------------------------

class TestBinaryMetadata:
    def test_string_binary_produces_labels(self):
        df = pd.DataFrame({"gender": ["Male", "Female", "Male", "Female"]})
        meta = _meta(df, {"gender": "binary"})
        assert "labels" in meta["gender"]
        labels = meta["gender"]["labels"]
        assert set(labels.values()) == {"Male", "Female"}
        assert set(labels.keys()) == {"1", "2"}

    def test_numeric_binary_0_1(self):
        df = pd.DataFrame({"flag": [0, 1, 0, 1]})
        meta = _meta(df, {"flag": "binary"})
        labels = meta["flag"]["labels"]
        assert set(labels.values()) == {"0", "1"}
        assert set(labels.keys()) == {"1", "2"}

    def test_binary_ignores_nulls(self):
        df = pd.DataFrame({"x": ["Yes", "No", None, "Yes"]})
        meta = _meta(df, {"x": "binary"})
        labels = meta["x"]["labels"]
        assert set(labels.values()) == {"No", "Yes"}

    def test_binary_keys_are_strings(self):
        df = pd.DataFrame({"b": ["A", "B", "A"]})
        meta = _meta(df, {"b": "binary"})
        for k in meta["b"]["labels"]:
            assert isinstance(k, str)


# ---------------------------------------------------------------------------
# Ordinal
# ---------------------------------------------------------------------------

class TestOrdinalMetadata:
    def test_likert_5_uses_canonical_labels(self):
        df = pd.DataFrame({"satisfaction": [1, 2, 3, 4, 5, 3, 2]})
        meta = _meta(df, {"satisfaction": "ordinal"})
        labels = meta["satisfaction"]["labels"]
        assert labels["1"] == "Strongly Disagree"
        assert labels["3"] == "Neutral"
        assert labels["5"] == "Strongly Agree"

    def test_likert_7_uses_canonical_labels(self):
        df = pd.DataFrame({"rating": [1, 2, 3, 4, 5, 6, 7]})
        meta = _meta(df, {"rating": "ordinal"})
        labels = meta["rating"]["labels"]
        assert labels["4"] == "Neutral"
        assert labels["7"] == "Strongly Agree"

    def test_partial_likert_5_only_present_keys(self):
        # Only values {1, 3, 5} are present — only those keys should appear.
        df = pd.DataFrame({"q": [1, 3, 5, 1, 3]})
        meta = _meta(df, {"q": "ordinal"})
        labels = meta["q"]["labels"]
        assert set(labels.keys()) == {"1", "3", "5"}
        assert labels["1"] == "Strongly Disagree"

    def test_likert_float_values(self):
        df = pd.DataFrame({"score": [1.0, 2.0, 3.0, 4.0, 5.0]})
        meta = _meta(df, {"score": "ordinal"})
        labels = meta["score"]["labels"]
        assert labels["1"] == "Strongly Disagree"

    def test_non_standard_ordinal_uses_sorted_map(self):
        # Values outside Likert range → sorted label map.
        df = pd.DataFrame({"rank": [10, 20, 30, 40]})
        meta = _meta(df, {"rank": "ordinal"})
        labels = meta["rank"]["labels"]
        assert len(labels) == 4
        # Keys must be consecutive string integers starting at "1".
        assert set(labels.keys()) == {"1", "2", "3", "4"}


# ---------------------------------------------------------------------------
# Categorical
# ---------------------------------------------------------------------------

class TestCategoricalMetadata:
    def test_produces_values_list(self):
        df = pd.DataFrame({"country": ["US", "UK", "DE", "FR"]})
        meta = _meta(df, {"country": "categorical"})
        assert "values" in meta["country"]
        assert set(meta["country"]["values"]) == {"US", "UK", "DE", "FR"}

    def test_values_capped_at_max(self):
        many = [str(i) for i in range(MAX_CATEGORICAL_LABELS + 5)]
        df = pd.DataFrame({"x": many})
        meta = _meta(df, {"x": "categorical"})
        assert len(meta["x"]["values"]) == MAX_CATEGORICAL_LABELS

    def test_values_are_strings(self):
        df = pd.DataFrame({"code": [10, 20, 30]})
        meta = _meta(df, {"code": "categorical"})
        for v in meta["code"]["values"]:
            assert isinstance(v, str)

    def test_values_sorted(self):
        df = pd.DataFrame({"tag": ["C", "A", "B", "A", "C"]})
        meta = _meta(df, {"tag": "categorical"})
        assert meta["tag"]["values"] == sorted({"A", "B", "C"})


# ---------------------------------------------------------------------------
# Continuous
# ---------------------------------------------------------------------------

class TestContinuousMetadata:
    def test_continuous_returns_empty_dict(self):
        df = pd.DataFrame({"age": list(range(20, 70))})
        meta = _meta(df, {"age": "continuous"})
        assert meta["age"] == {}

    def test_continuous_has_no_labels_key(self):
        df = pd.DataFrame({"weight": [60.5, 72.1, 88.3, 55.0]})
        meta = _meta(df, {"weight": "continuous"})
        assert "labels" not in meta["weight"]
        assert "values" not in meta["weight"]


# ---------------------------------------------------------------------------
# Return structure
# ---------------------------------------------------------------------------

class TestReturnStructure:
    def test_top_level_key(self):
        df = pd.DataFrame({"x": [1, 2]})
        result = build_variable_metadata(df, {"x": "binary"})
        assert "column_metadata" in result

    def test_covers_all_columns(self):
        df = pd.DataFrame({
            "age":          list(range(20, 70)),
            "gender":       ["M", "F"] * 25,
            "satisfaction": [1, 2, 3, 4, 5] * 10,
            "country":      ["US", "UK", "DE", "FR", "JP"] * 10,
        })
        column_types = {
            "age": "continuous",
            "gender": "binary",
            "satisfaction": "ordinal",
            "country": "categorical",
        }
        meta = _meta(df, column_types)
        assert set(meta.keys()) == set(df.columns)

    def test_unknown_type_falls_back_to_categorical(self):
        df = pd.DataFrame({"x": ["a", "b", "c"]})
        # Pass a type not in the known set — should fall back to categorical.
        meta = _meta(df, {"x": "unknown_type"})
        assert "values" in meta["x"]
