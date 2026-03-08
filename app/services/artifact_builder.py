import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

from app.config import NORMALIZED_DIR, REPORTS_DIR, SCHEMAS_DIR
from app.models.dataset import Dataset
from app.models.schema import ColumnSchema
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def build_artifacts(
    dataset: Dataset,
    df: pd.DataFrame,
    schemas: List[ColumnSchema],
) -> Dict[str, str]:
    """
    Write the three output artifacts and return their absolute paths.

    Artifacts:
        normalized_dataset.csv  → storage/normalized/
        normalization_report.md → storage/reports/
        dataset_schema.json     → storage/schemas/
    """
    logger.info(f"Building artifacts for dataset {dataset.dataset_id}")

    csv_path = _write_normalized_csv(dataset, df)
    report_path = _write_report(dataset, schemas)
    schema_path = _write_schema(dataset, schemas)

    logger.info(f"Artifacts generated for dataset {dataset.dataset_id}")
    return {
        "dataset": str(csv_path),
        "report": str(report_path),
        "schema": str(schema_path),
    }


# ---------------------------------------------------------------------------
# Private writers
# ---------------------------------------------------------------------------

def _write_normalized_csv(dataset: Dataset, df: pd.DataFrame) -> Path:
    path = NORMALIZED_DIR / f"{dataset.dataset_id}_normalized.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def _write_report(dataset: Dataset, schemas: List[ColumnSchema]) -> Path:
    path = REPORTS_DIR / f"{dataset.dataset_id}_report.md"
    path.write_text(_build_report_content(dataset, schemas), encoding="utf-8")
    return path


def _write_schema(dataset: Dataset, schemas: List[ColumnSchema]) -> Path:
    path = SCHEMAS_DIR / f"{dataset.dataset_id}_schema.json"
    payload = [
        {
            "column_name": s.column_name,
            "inferred_type": s.column_type,
            "missing_ratio": s.missing_ratio,
            "unique_values": s.unique_values,
        }
        for s in schemas
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _build_report_content(dataset: Dataset, schemas: List[ColumnSchema]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    header = f"""\
# AutoStat Prep — Normalization Report

**Dataset ID:** {dataset.dataset_id}
**Generated:** {generated_at}
**Pipeline version:** Sprint-1

---

## Summary

| Field | Value |
|---|---|
| Row Count | {dataset.row_count} |
| Column Count | {dataset.column_count} |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
"""

    rows = "\n".join(
        f"| {i + 1} | {s.column_name} | {s.column_type} | {s.missing_ratio:.4f} | {s.unique_values} |"
        for i, s in enumerate(schemas)
    )

    footer = """

---

## Sprint-1 Notes

- All columns inferred as `TEXT`. Full type inference arrives in Sprint-2.
- Resolver pipeline not yet active. Structural normalization only.
- Audit trail records pipeline version for reproducibility.
"""

    return header + rows + footer
