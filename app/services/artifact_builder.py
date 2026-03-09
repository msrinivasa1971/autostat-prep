import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.config import SCHEMA_VERSION, get_dataset_dir
from app.models.dataset import Dataset
from app.models.schema import ColumnSchema
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def build_artifacts(
    dataset: Dataset,
    df: pd.DataFrame,
    schemas: List[ColumnSchema],
    transformation_log: Optional[List[Dict[str, Any]]] = None,
    resolver_trace: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Write the four output artifacts to the per-user dataset directory and
    return their absolute paths.

    Artifacts (all inside storage/users/{user_id}/datasets/{dataset_id}/):
        normalized.csv
        report.md
        schema.json
        resolver_trace.json
    """
    logger.info(f"Building artifacts for dataset {dataset.dataset_id}")

    csv_path = _write_normalized_csv(dataset, df)
    report_path = _write_report(dataset, schemas, transformation_log or [])
    schema_path = _write_schema(dataset, schemas)
    trace_path = _write_resolver_trace(dataset, resolver_trace or [])

    logger.info(f"Artifacts generated for dataset {dataset.dataset_id}")
    return {
        "dataset": str(csv_path),
        "report": str(report_path),
        "schema": str(schema_path),
        "resolver_trace": str(trace_path),
    }


# ---------------------------------------------------------------------------
# Private writers
# ---------------------------------------------------------------------------

def _dataset_dir(dataset: Dataset) -> Path:
    d = get_dataset_dir(dataset.user_id, dataset.dataset_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_normalized_csv(dataset: Dataset, df: pd.DataFrame) -> Path:
    path = _dataset_dir(dataset) / "normalized.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def _write_report(
    dataset: Dataset,
    schemas: List[ColumnSchema],
    transformation_log: List[Dict[str, Any]],
) -> Path:
    path = _dataset_dir(dataset) / "report.md"
    path.write_text(
        _build_report_content(dataset, schemas, transformation_log),
        encoding="utf-8",
    )
    return path


def _write_schema(dataset: Dataset, schemas: List[ColumnSchema]) -> Path:
    path = _dataset_dir(dataset) / "schema.json"
    columns = [
        {
            "column_name": s.column_name,
            "inferred_type": s.column_type,
            "missing_ratio": s.missing_ratio,
            "unique_values": s.unique_values,
        }
        for s in schemas
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "columns": columns,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _build_report_content(
    dataset: Dataset,
    schemas: List[ColumnSchema],
    transformation_log: List[Dict[str, Any]],
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    header = f"""\
# AutoStat Prep — Normalization Report

**Dataset ID:** {dataset.dataset_id}
**Dataset Hash:** {dataset.dataset_hash or "N/A"}
**Generated:** {generated_at}
**Pipeline version:** Sprint-5

---

## Summary

| Field | Value |
|---|---|
| Row Count | {dataset.row_count} |
| Column Count | {dataset.column_count} |
| Resolvers Applied | {len(transformation_log)} |

---

## Column Inventory

| # | Column Name | Inferred Type | Missing Ratio | Unique Values |
|---|---|---|---|---|
"""

    col_rows = "\n".join(
        f"| {i + 1} | {s.column_name} | {s.column_type} | {s.missing_ratio:.4f} | {s.unique_values} |"
        for i, s in enumerate(schemas)
    )

    transformations_section = _build_transformations_section(transformation_log)

    footer = """

---

## Notes

- Column types inferred as `TEXT`. Full type inference arrives in Sprint-3.
- Audit trail records pipeline version for reproducibility.
"""

    return header + col_rows + transformations_section + footer


def _write_resolver_trace(dataset: Dataset, resolver_trace: List[Dict[str, Any]]) -> Path:
    path = _dataset_dir(dataset) / "resolver_trace.json"
    path.write_text(json.dumps(resolver_trace, indent=2), encoding="utf-8")
    return path


def _build_transformations_section(transformation_log: List[Dict[str, Any]]) -> str:
    if not transformation_log:
        return """

---

## Transformations Applied

No structural transformations were required.
"""

    rows = "\n".join(
        f"| {entry['resolver']} "
        f"| {entry['details']} "
        f"| {entry['rows_before']}→{entry['rows_after']} "
        f"| {entry['cols_before']}→{entry['cols_after']} "
        f"| {', '.join(entry.get('affected_columns', [])) or 'N/A'} |"
        for entry in transformation_log
    )

    return f"""

---

## Transformations Applied

| Resolver | Details | Rows | Columns | Affected Columns |
|---|---|---|---|---|
{rows}
"""
