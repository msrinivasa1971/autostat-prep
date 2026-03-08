from pathlib import Path
from typing import Any, Dict

from app.services.artifact_builder import build_artifacts
from app.services.dataset_loader import load_dataset
from app.services.profiler import profile_dataset
from app.services.validator import validate_dataset
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_normalization_pipeline(dataset_id: str, file_path: Path) -> Dict[str, Any]:
    """
    Execute the Sprint-1 normalization pipeline.

    Stages:
        1. Load     — parse CSV/XLSX into a DataFrame
        2. Profile  — compute per-column statistics
        3. Validate — assert structural requirements (fail-loud)
        4. Build    — write normalized_dataset.csv, report.md, schema.json

    Returns a result dict on success.
    Raises ValueError (FDG prefix) on validation failure.
    Raises any lower-level exception as-is for the caller to handle.
    """
    logger.info(f"[Pipeline] START  dataset_id={dataset_id}")

    # --- Stage 1: Load -------------------------------------------------------
    dataset, df = load_dataset(dataset_id, file_path)

    # --- Stage 2: Profile ----------------------------------------------------
    schemas = profile_dataset(dataset, df)

    # --- Stage 3: Validate ---------------------------------------------------
    validate_dataset(dataset, df)

    # --- Stage 4: Build artifacts --------------------------------------------
    artifacts = build_artifacts(dataset, df, schemas)

    logger.info(f"[Pipeline] COMPLETE dataset_id={dataset_id}")

    return {
        "dataset_id": dataset_id,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "artifacts": artifacts,
    }
