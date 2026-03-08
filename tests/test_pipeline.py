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
    df = pd.DataFrame({"id": ["1", "2"], "score": ["5", "4"]})
    engine = ResolverEngine(get_default_resolvers())
    _, log = engine.run(df)
    assert log == []


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
    content = _make_csv_bytes(SAMPLE_HEADER, *SAMPLE_ROWS)
    dataset_id, file_path = save_uploaded_file(content, "survey_clean.csv")
    result = run_normalization_pipeline(dataset_id, file_path)

    report_text = Path(result["artifacts"]["report"]).read_text(encoding="utf-8")
    assert "No structural transformations were required" in report_text
