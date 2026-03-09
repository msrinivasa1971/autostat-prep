"""
Sprint-1 pipeline tests.

Run with:  pytest tests/test_pipeline.py -v
"""
import csv
import io
from pathlib import Path

import pytest

from app.models.dataset import Dataset
from app.pipeline.normalization_pipeline import run_normalization_pipeline
from app.services.validator import validate_dataset
from app.utils.file_storage import save_uploaded_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_csv_bytes(*rows: tuple) -> bytes:
    """Encode a list of row-tuples as UTF-8 CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


SAMPLE_HEADER = ("id", "age", "score", "category")
SAMPLE_ROWS = [
    ("1", "25", "4.5", "A"),
    ("2", "30", "3.0", "B"),
    ("3", "22", "5.0", "A"),
]


# ---------------------------------------------------------------------------
# Upload + full pipeline
# ---------------------------------------------------------------------------

def test_upload_saves_file_to_raw_storage() -> None:
    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")

    assert file_path.exists(), "Raw file should exist after upload"
    assert file_path.suffix == ".csv"
    assert dataset_id in file_path.name


def test_pipeline_produces_all_three_artifacts() -> None:
    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")

    result = run_normalization_pipeline(dataset_id, file_path)

    assert result["dataset_id"] == dataset_id
    assert result["row_count"] == len(SAMPLE_ROWS)
    assert result["column_count"] == len(SAMPLE_HEADER)

    artifacts = result["artifacts"]
    assert Path(artifacts["dataset"]).exists(), "normalized_dataset.csv missing"
    assert Path(artifacts["report"]).exists(), "normalization_report.md missing"
    assert Path(artifacts["schema"]).exists(), "dataset_schema.json missing"


def test_normalized_csv_matches_input_shape() -> None:
    import pandas as pd

    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert list(df_out.columns) == list(SAMPLE_HEADER)
    assert len(df_out) == len(SAMPLE_ROWS)


def test_schema_json_contains_all_columns() -> None:
    import json

    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    schema = json.loads(Path(result["artifacts"]["schema"]).read_text(encoding="utf-8"))
    schema_col_names = [s["column_name"] for s in schema]
    assert schema_col_names == list(SAMPLE_HEADER)


def test_schema_json_inferred_type_is_text() -> None:
    import json

    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    schema = json.loads(Path(result["artifacts"]["schema"]).read_text(encoding="utf-8"))
    for col in schema:
        assert col["inferred_type"] == "TEXT", (
            f"Column '{col['column_name']}' should be TEXT in Sprint-1, "
            f"got '{col['inferred_type']}'"
        )


def test_report_md_contains_dataset_id() -> None:
    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    report_text = Path(result["artifacts"]["report"]).read_text(encoding="utf-8")
    assert dataset_id in report_text


# ---------------------------------------------------------------------------
# Validator: fail-loud (FDG) tests
# ---------------------------------------------------------------------------

def test_validator_rejects_empty_dataframe() -> None:
    import pandas as pd
    from datetime import datetime, timezone

    empty_df = pd.DataFrame()
    dataset = Dataset(
        dataset_id="test-no-columns",
        file_path="/dev/null",
        row_count=0,
        column_count=0,
        columns=[],
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="FDG:"):
        validate_dataset(dataset, empty_df)


def test_validator_rejects_no_rows() -> None:
    import pandas as pd
    from datetime import datetime, timezone

    df = pd.DataFrame(columns=["a", "b"])
    dataset = Dataset(
        dataset_id="test-no-rows",
        file_path="/dev/null",
        row_count=0,
        column_count=2,
        columns=["a", "b"],
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="FDG:"):
        validate_dataset(dataset, df)


def test_validator_rejects_empty_column_name() -> None:
    import pandas as pd
    from datetime import datetime, timezone

    df = pd.DataFrame([{"a": 1, "": 2}])
    dataset = Dataset(
        dataset_id="test-blank-col",
        file_path="/dev/null",
        row_count=1,
        column_count=2,
        columns=["a", ""],
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="FDG:"):
        validate_dataset(dataset, df)


# ---------------------------------------------------------------------------
# File storage: unsupported extension
# ---------------------------------------------------------------------------

def test_upload_rejects_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        save_uploaded_file(b"data", "survey.spss")


# ===========================================================================
# Sprint-2 — Resolver tests
# ===========================================================================

import pandas as pd

from app.resolvers.structural_resolvers import (
    BlankColumnResolver,
    BlankRowResolver,
    BOMResolver,
    DuplicateColumnResolver,
    HeaderNormalizerResolver,
)
from app.resolvers.encoding_resolvers import (
    BooleanResolver,
    LikertScaleResolver,
    MissingValueResolver,
    NumericTextResolver,
    PercentResolver,
)
from app.resolvers.survey_resolvers import (
    CarryForwardResolver,
    DelimitedListResolver,
    MultiRowHeaderResolver,
    MultiSelectResolver,
)
from app.resolvers.resolver_engine import ResolverEngine
from app.resolvers.resolver_registry import get_default_resolvers


# ---------------------------------------------------------------------------
# BOMResolver
# ---------------------------------------------------------------------------

def test_bom_resolver_detects_bom_in_first_column() -> None:
    df = pd.DataFrame({"\ufeffQ1": ["a"], "Q2": ["b"]})
    assert BOMResolver().detect(df) is True


def test_bom_resolver_removes_bom() -> None:
    df = pd.DataFrame({"\ufeffQ1": ["a"], "Q2": ["b"]})
    result = BOMResolver().apply(df)
    assert list(result.columns) == ["Q1", "Q2"]
    assert df.columns[0] == "\ufeffQ1", "Input must not be mutated"


def test_bom_resolver_does_not_fire_on_clean_data() -> None:
    df = pd.DataFrame({"Q1": ["a"], "Q2": ["b"]})
    assert BOMResolver().detect(df) is False


# ---------------------------------------------------------------------------
# BlankColumnResolver
# ---------------------------------------------------------------------------

def test_blank_column_resolver_detects_blank_column() -> None:
    df = pd.DataFrame({"id": ["1", "2"], "blank": ["", ""]})
    assert BlankColumnResolver().detect(df) is True


def test_blank_column_resolver_removes_blank_column() -> None:
    df = pd.DataFrame({"id": ["1", "2"], "blank": ["", ""], "score": ["5", "4"]})
    result = BlankColumnResolver().apply(df)
    assert list(result.columns) == ["id", "score"]
    assert "blank" not in result.columns
    assert "blank" in df.columns, "Input must not be mutated"


def test_blank_column_resolver_does_not_fire_on_clean_data() -> None:
    df = pd.DataFrame({"id": ["1"], "score": ["5"]})
    assert BlankColumnResolver().detect(df) is False


def test_pipeline_removes_blank_column() -> None:
    content = _make_csv_bytes(
        ("id", "score", "empty_col"),
        ("1", "5.0", ""),
        ("2", "4.0", ""),
        ("3", "3.0", ""),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_blank_col.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert "empty_col" not in df_out.columns
    assert result["column_count"] == 2


# ---------------------------------------------------------------------------
# BlankRowResolver
# ---------------------------------------------------------------------------

def test_blank_row_resolver_detects_blank_row() -> None:
    df = pd.DataFrame({"id": ["1", "", "2"], "score": ["5", "", "4"]})
    assert BlankRowResolver().detect(df) is True


def test_blank_row_resolver_removes_blank_row() -> None:
    df = pd.DataFrame({"id": ["1", "", "2"], "score": ["5", "", "4"]})
    result = BlankRowResolver().apply(df)
    assert len(result) == 2
    assert list(result["id"]) == ["1", "2"]
    assert len(df) == 3, "Input must not be mutated"


def test_blank_row_resolver_resets_index() -> None:
    df = pd.DataFrame({"id": ["1", "", "2"], "score": ["5", "", "4"]})
    result = BlankRowResolver().apply(df)
    assert list(result.index) == [0, 1]


def test_blank_row_resolver_does_not_fire_on_clean_data() -> None:
    df = pd.DataFrame({"id": ["1", "2"], "score": ["5", "4"]})
    assert BlankRowResolver().detect(df) is False


def test_pipeline_removes_blank_row() -> None:
    content = _make_csv_bytes(
        ("id", "score"),
        ("1", "5.0"),
        ("", ""),      # blank row
        ("2", "4.0"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_blank_row.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert len(df_out) == 2
    assert result["row_count"] == 2


# ---------------------------------------------------------------------------
# HeaderNormalizerResolver
# ---------------------------------------------------------------------------

def test_header_normalizer_detects_messy_headers() -> None:
    df = pd.DataFrame({"Project Score": [1], "Q1": [2]})
    assert HeaderNormalizerResolver().detect(df) is True


def test_header_normalizer_lowercases_and_underscores() -> None:
    df = pd.DataFrame({"Project Coordination Satisfaction": [1], "User ID": [2]})
    result = HeaderNormalizerResolver().apply(df)
    assert list(result.columns) == ["project_coordination_satisfaction", "user_id"]


def test_header_normalizer_removes_punctuation() -> None:
    df = pd.DataFrame({"Q1 (Score)": [1], "Q2 [Answer]": [2]})
    result = HeaderNormalizerResolver().apply(df)
    assert list(result.columns) == ["q1_score", "q2_answer"]


def test_header_normalizer_does_not_fire_on_clean_headers() -> None:
    df = pd.DataFrame({"project_score": [1], "user_id": [2]})
    assert HeaderNormalizerResolver().detect(df) is False


def test_pipeline_normalizes_column_headers() -> None:
    content = b"Project Score,User ID,Q1 Answer\n1,2,3\n4,5,6\n"
    dataset_id, file_path = save_uploaded_file(content, "survey_messy_headers.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert "project_score" in df_out.columns
    assert "user_id" in df_out.columns
    assert "q1_answer" in df_out.columns


# ---------------------------------------------------------------------------
# DuplicateColumnResolver
# ---------------------------------------------------------------------------

def test_duplicate_resolver_detects_duplicates() -> None:
    df = pd.DataFrame([[1, 2, 3]], columns=["q1", "q2", "q1"])
    assert DuplicateColumnResolver().detect(df) is True


def test_duplicate_resolver_renames_second_occurrence() -> None:
    df = pd.DataFrame([[1, 2, 3]], columns=["q1", "q2", "q1"])
    result = DuplicateColumnResolver().apply(df)
    assert list(result.columns) == ["q1", "q2", "q1_2"]


def test_duplicate_resolver_handles_triple_duplicate() -> None:
    df = pd.DataFrame([[1, 2, 3]], columns=["q1", "q1", "q1"])
    result = DuplicateColumnResolver().apply(df)
    assert list(result.columns) == ["q1", "q1_2", "q1_3"]


def test_duplicate_resolver_skips_existing_suffix() -> None:
    # q1_2 already exists — the renamed duplicate must become q1_3
    df = pd.DataFrame([[1, 2, 3]], columns=["q1", "q1_2", "q1"])
    result = DuplicateColumnResolver().apply(df)
    assert list(result.columns) == ["q1", "q1_2", "q1_3"]


def test_duplicate_resolver_does_not_fire_on_unique_columns() -> None:
    df = pd.DataFrame({"q1": [1], "q2": [2], "q3": [3]})
    assert DuplicateColumnResolver().detect(df) is False


def test_pipeline_renames_normalization_created_duplicates() -> None:
    # "Project Score" and "Project_Score" both normalize to "project_score"
    content = b"Project Score,Q2,Project_Score\n1,2,3\n4,5,6\n"
    dataset_id, file_path = save_uploaded_file(content, "survey_norm_dupes.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert "project_score" in df_out.columns
    assert "project_score_2" in df_out.columns
    assert "q2" in df_out.columns


# ---------------------------------------------------------------------------
# Resolver Engine
# ---------------------------------------------------------------------------

def test_engine_returns_empty_log_for_clean_data() -> None:
    # Note: "clean" data may still have numeric strings that need conversion
    df = pd.DataFrame({"id": ["1", "2"], "score": ["5", "4"]})
    engine = ResolverEngine(get_default_resolvers())
    _, log = engine.run(df)
    # NumericTextResolver will fire on numeric strings
    assert len(log) == 1
    assert log[0]["resolver"] == "NumericTextResolver"
    assert log[0]["affected_columns"] == ["score"]


# ===========================================================================
# Sprint-3 — Encoding Resolver tests
# ===========================================================================

# ---------------------------------------------------------------------------
# BooleanResolver
# ---------------------------------------------------------------------------

def test_boolean_resolver_detects_boolean_column() -> None:
    df = pd.DataFrame({"agree": ["Yes", "No", "Yes"]})
    assert BooleanResolver().detect(df) is True


def test_boolean_resolver_converts_to_numeric() -> None:
    df = pd.DataFrame({"agree": ["Yes", "No", "True", "False", "Y", "N"]})
    result = BooleanResolver().apply(df)
    expected = [1, 0, 1, 0, 1, 0]
    assert result["agree"].tolist() == expected


def test_boolean_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"agree": ["Yes", "No"], "score": ["5", "4"]})
    affected = BooleanResolver().get_affected_columns(df)
    assert affected == ["agree"]


def test_boolean_resolver_does_not_fire_on_non_boolean() -> None:
    df = pd.DataFrame({"text": ["Hello", "World"]})
    assert BooleanResolver().detect(df) is False


def test_boolean_resolver_does_not_fire_on_mixed_column() -> None:
    df = pd.DataFrame({"agree": ["Yes", "No", "Maybe"]})
    assert BooleanResolver().detect(df) is False


def test_pipeline_converts_boolean_values() -> None:
    content = _make_csv_bytes(
        ("id", "agree"),
        ("1", "Yes"),
        ("2", "No"),
        ("3", "True"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_boolean.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["agree"].tolist() == [1, 0, 1]


# ---------------------------------------------------------------------------
# LikertScaleResolver
# ---------------------------------------------------------------------------

def test_likert_resolver_detects_likert_column() -> None:
    df = pd.DataFrame({"satisfaction": ["Agree", "Disagree", "Neutral"]})
    assert LikertScaleResolver().detect(df) is True


def test_likert_resolver_converts_to_numeric() -> None:
    df = pd.DataFrame({"satisfaction": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]})
    result = LikertScaleResolver().apply(df)
    expected = [5, 4, 3, 2, 1]
    assert result["satisfaction"].tolist() == expected


def test_likert_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"satisfaction": ["Agree", "Disagree"], "score": ["5", "4"]})
    affected = LikertScaleResolver().get_affected_columns(df)
    assert affected == ["satisfaction"]


def test_likert_resolver_does_not_fire_on_non_likert() -> None:
    df = pd.DataFrame({"text": ["Hello", "World"]})
    assert LikertScaleResolver().detect(df) is False


def test_likert_resolver_does_not_fire_on_mixed_column() -> None:
    df = pd.DataFrame({"satisfaction": ["Agree", "Disagree", "Maybe"]})
    assert LikertScaleResolver().detect(df) is False


def test_pipeline_converts_likert_values() -> None:
    content = _make_csv_bytes(
        ("id", "satisfaction"),
        ("1", "Agree"),
        ("2", "Neutral"),
        ("3", "Disagree"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_likert.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["satisfaction"].tolist() == [4, 3, 2]


# ---------------------------------------------------------------------------
# PercentResolver
# ---------------------------------------------------------------------------

def test_percent_resolver_detects_percent_column() -> None:
    df = pd.DataFrame({"rate": ["45%", "72%"]})
    assert PercentResolver().detect(df) is True


def test_percent_resolver_converts_to_decimal() -> None:
    df = pd.DataFrame({"rate": ["45%", "72%", "100%"]})
    result = PercentResolver().apply(df)
    expected = [0.45, 0.72, 1.0]
    assert result["rate"].tolist() == expected


def test_percent_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"rate": ["45%", "72%"], "score": ["5", "4"]})
    affected = PercentResolver().get_affected_columns(df)
    assert affected == ["rate"]


def test_percent_resolver_does_not_fire_on_non_percent() -> None:
    df = pd.DataFrame({"text": ["Hello", "World"]})
    assert PercentResolver().detect(df) is False


def test_pipeline_converts_percent_values() -> None:
    content = _make_csv_bytes(
        ("id", "rate"),
        ("1", "45%"),
        ("2", "72%"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_percent.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["rate"].tolist() == [0.45, 0.72]


# ---------------------------------------------------------------------------
# NumericTextResolver
# ---------------------------------------------------------------------------

def test_numeric_text_resolver_detects_numeric_text_column() -> None:
    df = pd.DataFrame({"age": ["34", "52"]})
    assert NumericTextResolver().detect(df) is True


def test_numeric_text_resolver_converts_dtype() -> None:
    df = pd.DataFrame({"age": ["34", "52"]})
    result = NumericTextResolver().apply(df)
    assert result["age"].dtype in ['int64', 'float64']


def test_numeric_text_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"age": ["34", "52"], "name": ["John", "Jane"]})
    affected = NumericTextResolver().get_affected_columns(df)
    assert affected == ["age"]


def test_numeric_text_resolver_does_not_fire_on_non_numeric() -> None:
    df = pd.DataFrame({"text": ["Hello", "World"]})
    assert NumericTextResolver().detect(df) is False


def test_numeric_text_resolver_skips_id_column() -> None:
    df = pd.DataFrame({"EmployeeID": ["1001", "1002"], "OrderCode": ["500", "501"], "score": ["5", "4"]})
    resolver = NumericTextResolver()
    affected = resolver.get_affected_columns(df)
    assert "EmployeeID" not in affected
    assert "OrderCode" not in affected
    assert "score" in affected


def test_pipeline_converts_numeric_text() -> None:
    content = _make_csv_bytes(
        ("id", "age"),
        ("1", "25"),
        ("2", "30"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_numeric.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["age"].dtype in ['int64', 'float64']


# ---------------------------------------------------------------------------
# MissingValueResolver
# ---------------------------------------------------------------------------

def test_missing_value_resolver_detects_missing_indicators() -> None:
    df = pd.DataFrame({"score": ["5", "NA", "4"]})
    assert MissingValueResolver().detect(df) is True


def test_missing_value_resolver_converts_to_nan() -> None:
    df = pd.DataFrame({"score": ["5", "NA", "N/A", "null", "", " "]})
    result = MissingValueResolver().apply(df)
    expected_nan_count = 5  # all except "5"
    assert result["score"].isna().sum() == expected_nan_count


def test_missing_value_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"score": ["5", "NA"], "name": ["John", "Jane"]})
    affected = MissingValueResolver().get_affected_columns(df)
    assert affected == ["score"]


def test_missing_value_resolver_does_not_fire_on_no_missing() -> None:
    df = pd.DataFrame({"score": ["5", "4"]})
    assert MissingValueResolver().detect(df) is False


def test_pipeline_normalizes_missing_values() -> None:
    content = _make_csv_bytes(
        ("id", "score"),
        ("1", "5"),
        ("2", "NA"),
        ("3", "N/A"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_missing.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["score"].isna().sum() == 2


def test_engine_logs_fired_resolvers() -> None:
    # HeaderNormalizerResolver should fire on this DataFrame
    df = pd.DataFrame({"Project Score": ["1"], "User ID": ["2"]})
    engine = ResolverEngine(get_default_resolvers())
    _, log = engine.run(df)

    resolver_names = [entry["resolver"] for entry in log]
    assert "HeaderNormalizerResolver" in resolver_names


def test_engine_log_entries_have_required_fields() -> None:
    df = pd.DataFrame({"Project Score": ["1"], "blank_col": [""]})
    engine = ResolverEngine(get_default_resolvers())
    _, log = engine.run(df)

    for entry in log:
        assert "resolver" in entry
        assert "details" in entry
        assert "rows_before" in entry
        assert "rows_after" in entry
        assert "cols_before" in entry
        assert "cols_after" in entry


# ---------------------------------------------------------------------------
# Transformation log in report
# ---------------------------------------------------------------------------

def test_report_contains_transformation_section() -> None:
    # A dataset that will trigger at least HeaderNormalizerResolver
    content = b"Project Score,User ID\n1,2\n3,4\n"
    dataset_id, file_path = save_uploaded_file(content, "survey_report_check.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    report_text = Path(result["artifacts"]["report"]).read_text(encoding="utf-8")
    assert "Transformations Applied" in report_text
    assert "HeaderNormalizerResolver" in report_text


def test_report_notes_no_transformations_for_clean_data() -> None:
    # Note: "clean" data may have numeric strings that are converted
    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey_clean.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    report_text = Path(result["artifacts"]["report"]).read_text(encoding="utf-8")
    assert "Transformations Applied" in report_text
    assert "NumericTextResolver" in report_text


# ===========================================================================
# Sprint-4 — Survey Resolver tests
# ===========================================================================

# ---------------------------------------------------------------------------
# MultiSelectResolver
# ---------------------------------------------------------------------------

def test_multi_select_resolver_detects_semicolon_column() -> None:
    df = pd.DataFrame({"tools": ["Jira;Trello;Asana", "Jira", "Trello;Asana"]})
    assert MultiSelectResolver().detect(df) is True


def test_multi_select_resolver_detects_pipe_column() -> None:
    df = pd.DataFrame({"tools": ["Jira|Trello", "Jira", "Trello|Asana"]})
    assert MultiSelectResolver().detect(df) is True


def test_multi_select_resolver_does_not_fire_on_plain_text() -> None:
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"]})
    assert MultiSelectResolver().detect(df) is False


def test_multi_select_resolver_expands_semicolon_to_binary_columns() -> None:
    df = pd.DataFrame({"tools": ["Jira;Trello", "Jira", "Trello"]})
    result = MultiSelectResolver().apply(df)
    assert "tools_jira" in result.columns
    assert "tools_trello" in result.columns
    assert "tools" not in result.columns
    assert result["tools_jira"].tolist() == [1, 1, 0]
    assert result["tools_trello"].tolist() == [1, 0, 1]


def test_multi_select_resolver_expands_pipe_to_binary_columns() -> None:
    df = pd.DataFrame({"tools": ["Jira|Trello|Asana", "Jira", "Asana"]})
    result = MultiSelectResolver().apply(df)
    assert "tools_jira" in result.columns
    assert "tools_trello" in result.columns
    assert "tools_asana" in result.columns
    assert result["tools_asana"].tolist() == [1, 0, 1]


def test_multi_select_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"tools": ["Jira;Trello", "Jira"], "score": ["5", "4"]})
    affected = MultiSelectResolver().get_affected_columns(df)
    assert affected == ["tools"]
    assert "score" not in affected


def test_engine_logs_multi_select_resolver() -> None:
    df = pd.DataFrame({"tools": ["Jira;Trello", "Asana", "Jira;Asana"]})
    engine = ResolverEngine([MultiSelectResolver()])
    _, log = engine.run(df)
    assert len(log) == 1
    assert log[0]["resolver"] == "MultiSelectResolver"
    assert "tools" in log[0]["affected_columns"]


def test_multi_select_resolver_does_not_fire_on_free_text_with_semicolons() -> None:
    # Tokens like "development phase" contain internal spaces — must be rejected.
    df = pd.DataFrame({"feedback": ["Research; development phase", "Analysis; design phase"]})
    assert MultiSelectResolver().detect(df) is False


def test_multi_select_resolver_fires_on_valid_token_list() -> None:
    # Each token is a single word with no internal spaces — valid multi-select.
    df = pd.DataFrame({"tools": ["Jira;Trello;Asana", "Jira", "Asana"]})
    assert MultiSelectResolver().detect(df) is True


def test_pipeline_expands_multi_select_column() -> None:
    content = _make_csv_bytes(
        ("id", "tools"),
        ("1", "Jira;Trello"),
        ("2", "Asana"),
        ("3", "Jira;Asana"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_multiselect.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert "tools_jira" in df_out.columns
    assert "tools_trello" in df_out.columns
    assert "tools_asana" in df_out.columns
    assert "tools" not in df_out.columns


# ---------------------------------------------------------------------------
# DelimitedListResolver
# ---------------------------------------------------------------------------

def test_delimited_list_resolver_detects_comma_list_column() -> None:
    df = pd.DataFrame({"categories": ["A,B,C", "A,B", "C"]})
    assert DelimitedListResolver().detect(df) is True


def test_delimited_list_resolver_does_not_fire_on_natural_language() -> None:
    # Internal spaces in parts prevent detection
    df = pd.DataFrame({"address": ["New York,Los Angeles", "Chicago,Houston"]})
    # "New York" has an internal space → rejected
    assert DelimitedListResolver().detect(df) is False


def test_delimited_list_resolver_does_not_fire_on_plain_text() -> None:
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"]})
    assert DelimitedListResolver().detect(df) is False


def test_delimited_list_resolver_expands_to_binary_columns() -> None:
    df = pd.DataFrame({"categories": ["A,B", "A", "B"]})
    result = DelimitedListResolver().apply(df)
    assert "categories_a" in result.columns
    assert "categories_b" in result.columns
    assert "categories" not in result.columns
    assert result["categories_a"].tolist() == [1, 1, 0]
    assert result["categories_b"].tolist() == [1, 0, 1]


def test_delimited_list_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"categories": ["A,B", "A"], "score": ["5", "4"]})
    affected = DelimitedListResolver().get_affected_columns(df)
    assert affected == ["categories"]
    assert "score" not in affected


def test_engine_logs_delimited_list_resolver() -> None:
    df = pd.DataFrame({"categories": ["A,B,C", "A", "B,C"]})
    engine = ResolverEngine([DelimitedListResolver()])
    _, log = engine.run(df)
    assert len(log) == 1
    assert log[0]["resolver"] == "DelimitedListResolver"
    assert "categories" in log[0]["affected_columns"]


def test_pipeline_expands_delimited_list_column() -> None:
    content = _make_csv_bytes(
        ("id", "tags"),
        ("1", "alpha,beta"),
        ("2", "alpha"),
        ("3", "beta,gamma"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_delimited.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert "tags_alpha" in df_out.columns
    assert "tags_beta" in df_out.columns
    assert "tags_gamma" in df_out.columns
    assert "tags" not in df_out.columns


# ---------------------------------------------------------------------------
# MultiRowHeaderResolver
# ---------------------------------------------------------------------------

def test_multi_row_header_resolver_detects_metadata_row() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with team coordination", "5", "4", "3"],
        "Q2": ["Please rate your experience with tools", "4", "5", "3"],
    })
    assert MultiRowHeaderResolver().detect(df) is True


def test_multi_row_header_resolver_does_not_fire_on_short_first_row() -> None:
    df = pd.DataFrame({"Q1": ["5", "4", "3"], "Q2": ["4", "5", "3"]})
    assert MultiRowHeaderResolver().detect(df) is False


def test_multi_row_header_resolver_does_not_fire_on_small_dataframe() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with team coordination", "5"],
    })
    assert MultiRowHeaderResolver().detect(df) is False  # fewer than 3 rows


def test_multi_row_header_resolver_combines_headers_and_drops_row() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with coordination", "5", "4"],
        "Q2": ["Rate your experience with tools", "4", "5"],
    })
    result = MultiRowHeaderResolver().apply(df)
    assert "q1_overall_satisfaction_with_coordination" in result.columns
    assert "q2_rate_your_experience_with_tools" in result.columns
    assert len(result) == 2  # metadata row was dropped


def test_multi_row_header_resolver_resets_index() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with team coordination", "5", "4", "3"],
        "Q2": ["Please rate your experience with the tools", "4", "5", "3"],
    })
    result = MultiRowHeaderResolver().apply(df)
    assert list(result.index) == [0, 1, 2]


def test_multi_row_header_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with coordination", "5", "4"],
        "Q2": ["Rate your experience with tools", "4", "5"],
    })
    affected = MultiRowHeaderResolver().get_affected_columns(df)
    assert set(affected) == {"Q1", "Q2"}


def test_engine_logs_multi_row_header_resolver() -> None:
    df = pd.DataFrame({
        "Q1": ["Overall satisfaction with team coordination", "5", "4"],
        "Q2": ["Please rate your experience with tools", "4", "5"],
    })
    engine = ResolverEngine([MultiRowHeaderResolver()])
    _, log = engine.run(df)
    assert len(log) == 1
    assert log[0]["resolver"] == "MultiRowHeaderResolver"
    assert log[0]["cols_before"] == 2


# ---------------------------------------------------------------------------
# CarryForwardResolver
# ---------------------------------------------------------------------------

def test_carry_forward_resolver_detects_not_displayed() -> None:
    df = pd.DataFrame({"Q1": ["5", "Not displayed", "4"]})
    assert CarryForwardResolver().detect(df) is True


def test_carry_forward_resolver_detects_question_not_asked() -> None:
    df = pd.DataFrame({"Q1": ["5", "Question not asked", "4"]})
    assert CarryForwardResolver().detect(df) is True


def test_carry_forward_resolver_detects_skipped() -> None:
    df = pd.DataFrame({"Q1": ["5", "Skipped", "4"]})
    assert CarryForwardResolver().detect(df) is True


def test_carry_forward_resolver_detects_na_routing() -> None:
    df = pd.DataFrame({"Q1": ["5", "N/A (routing)", "4"]})
    assert CarryForwardResolver().detect(df) is True


def test_carry_forward_resolver_does_not_fire_on_clean_data() -> None:
    df = pd.DataFrame({"Q1": ["5", "4", "3"]})
    assert CarryForwardResolver().detect(df) is False


def test_carry_forward_resolver_does_not_fire_on_plain_na() -> None:
    # Plain "N/A" (without routing suffix) must NOT be caught here;
    # that is MissingValueResolver's domain.
    df = pd.DataFrame({"Q1": ["5", "N/A", "4"]})
    assert CarryForwardResolver().detect(df) is False


def test_carry_forward_resolver_converts_all_artifacts_to_nan() -> None:
    df = pd.DataFrame({
        "Q1": ["5", "Not displayed", "Question not asked", "Skipped", "N/A (routing)"]
    })
    result = CarryForwardResolver().apply(df)
    assert result["Q1"].isna().sum() == 4
    assert result["Q1"].iloc[0] == "5"


def test_carry_forward_resolver_is_case_insensitive() -> None:
    df = pd.DataFrame({"Q1": ["NOT DISPLAYED", "SKIPPED", "5"]})
    result = CarryForwardResolver().apply(df)
    assert result["Q1"].isna().sum() == 2


def test_carry_forward_resolver_get_affected_columns() -> None:
    df = pd.DataFrame({"Q1": ["5", "Skipped"], "Q2": ["4", "4"]})
    affected = CarryForwardResolver().get_affected_columns(df)
    assert affected == ["Q1"]
    assert "Q2" not in affected


def test_engine_logs_carry_forward_resolver() -> None:
    df = pd.DataFrame({"Q1": ["5", "Not displayed", "4"]})
    engine = ResolverEngine([CarryForwardResolver()])
    _, log = engine.run(df)
    assert len(log) == 1
    assert log[0]["resolver"] == "CarryForwardResolver"
    assert "Q1" in log[0]["affected_columns"]


# ===========================================================================
# Sprint-4 — Resolver Trace tests
# ===========================================================================

def test_resolver_trace_has_entry_for_every_resolver() -> None:
    # Even resolvers that do not fire must appear in the trace.
    df = pd.DataFrame({"id": ["1", "2"], "score": ["5", "4"]})
    engine = ResolverEngine(get_default_resolvers())
    engine.run(df)
    assert len(engine.resolver_trace) == len(get_default_resolvers())


def test_resolver_trace_applied_only_when_transformation_occurred() -> None:
    # NumericTextResolver fires on numeric strings; all others should not.
    df = pd.DataFrame({"id": ["1", "2"], "score": ["5", "4"]})
    engine = ResolverEngine(get_default_resolvers())
    _, log = engine.run(df)
    applied_in_trace = [e["resolver"] for e in engine.resolver_trace if e["applied"]]
    applied_in_log   = [e["resolver"] for e in log]
    assert applied_in_trace == applied_in_log


def test_resolver_trace_json_written_by_pipeline() -> None:
    import json

    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey_trace.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    trace_path = Path(result["artifacts"]["resolver_trace"])
    assert trace_path.exists(), "resolver_trace.json must be written"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert len(trace) == len(get_default_resolvers())
    for entry in trace:
        assert "resolver" in entry
        assert "detected" in entry
        assert "applied" in entry
        assert "affected_columns" in entry


def test_pipeline_converts_carry_forward_artifacts() -> None:
    content = _make_csv_bytes(
        ("id", "Q1", "Q2"),
        ("1", "5", "Agree"),
        ("2", "Not displayed", "Agree"),
        ("3", "4", "Skipped"),
    )
    dataset_id, file_path = save_uploaded_file(content, "survey_carry_forward.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    df_out = pd.read_csv(result["artifacts"]["dataset"])
    assert df_out["q1"].isna().sum() == 1
    assert df_out["q2"].isna().sum() == 1
