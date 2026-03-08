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
