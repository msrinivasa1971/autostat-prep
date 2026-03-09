"""
AutoStat client — sends normalized datasets to the AutoStat analysis service.

Integration is optional: if AUTOSTAT_API_URL is not set (empty string), all
calls raise RuntimeError and the rest of AutoStat Prep continues to work normally.
"""
import json
from pathlib import Path
from typing import Any, Dict

import requests

from app.config import AUTOSTAT_API_URL, AUTOSTAT_API_TIMEOUT
from app.utils.file_storage import find_dataset_dir


def send_dataset_for_analysis(
    dataset_id: str,
    user_id: str = "default",
) -> Dict[str, Any]:
    """
    Locate the normalized dataset and schema, POST them to AutoStat, and
    save the returned analysis results as analysis_report.json in the dataset
    directory.

    Returns the analysis result dict received from AutoStat.

    Raises:
        RuntimeError: if AUTOSTAT_API_URL is not configured.
        FileNotFoundError: if the normalized dataset does not exist.
        requests.RequestException: if the HTTP call fails.
    """
    if not AUTOSTAT_API_URL:
        raise RuntimeError(
            "AutoStat integration is not configured. "
            "Set AUTOSTAT_API_URL in app/config.py to enable it."
        )

    dataset_dir = find_dataset_dir(dataset_id, user_id=user_id)
    if dataset_dir is None:
        dataset_dir = find_dataset_dir(dataset_id)
    if dataset_dir is None:
        raise FileNotFoundError(f"Dataset not found: {dataset_id!r}")

    csv_path = dataset_dir / "normalized.csv"
    schema_path = dataset_dir / "schema.json"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Normalized dataset not found for dataset_id={dataset_id!r}. "
            "Run normalization first."
        )

    files: dict = {
        "dataset": ("normalized.csv", csv_path.read_bytes(), "text/csv"),
    }
    if schema_path.exists():
        files["schema"] = ("schema.json", schema_path.read_bytes(), "application/json")

    response = requests.post(
        f"{AUTOSTAT_API_URL.rstrip('/')}/analyze",
        data={"dataset_id": dataset_id, "user_id": user_id},
        files=files,
        timeout=AUTOSTAT_API_TIMEOUT,
    )
    response.raise_for_status()
    result: Dict[str, Any] = response.json()

    report_path = dataset_dir / "analysis_report.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result
