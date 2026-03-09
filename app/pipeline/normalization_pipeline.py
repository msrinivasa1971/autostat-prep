from pathlib import Path
from typing import Any, Dict

from app.models.dataset import Dataset
from app.models.state import DatasetState
from app.resolvers.resolver_engine import ResolverEngine
from app.resolvers.resolver_registry import get_default_resolvers
from app.services.artifact_builder import build_artifacts
from app.services.dataset_loader import load_dataset
from app.services.profiler import profile_dataset
from app.services.validator import validate_dataset
from app.utils.file_storage import compute_file_hash
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_normalization_pipeline(
    dataset_id: str,
    file_path: Path,
    user_id: str = "default",
) -> Dict[str, Any]:
    """
    Execute the normalization pipeline.

    Stages:
        1. Load     — parse CSV/XLSX into a DataFrame; compute SHA-256 hash;
                      transition dataset state UPLOADED → NORMALIZING
        2. Resolve  — run all resolvers in registry order:
                        BOMResolver → BlankColumnResolver → BlankRowResolver
                        → HeaderNormalizerResolver → DuplicateColumnResolver
                        → BooleanResolver → LikertScaleResolver → PercentResolver
                        → NumericTextResolver → MissingValueResolver
                        → MultiRowHeaderResolver → MultiSelectResolver
                        → DelimitedListResolver → CarryForwardResolver
        3. Profile  — rebuild Dataset descriptor and column schemas to reflect
                      any rows/columns that resolvers removed or renamed
        4. Validate — assert structural requirements (fail-loud)
        5. Build    — write artifacts to storage/users/{user_id}/datasets/{dataset_id}/;
                      transition state NORMALIZING → COMPLETE

    Returns a result dict on success.
    Raises ValueError (FDG prefix) on validation or resolver failure.
    """
    logger.info(f"[Pipeline] START  dataset_id={dataset_id} user={user_id}")

    # --- Stage 1: Load -------------------------------------------------------
    dataset, df = load_dataset(dataset_id, file_path)
    dataset_hash = compute_file_hash(file_path)
    dataset.transition(DatasetState.NORMALIZING)

    # --- Stage 2: Resolve ----------------------------------------------------
    engine = ResolverEngine(get_default_resolvers())
    df, transformation_log = engine.run(df)
    resolver_trace = engine.resolver_trace

    # --- Stage 3: Profile ----------------------------------------------------
    # Rebuild the Dataset descriptor and column schemas to match the resolved
    # DataFrame.  Resolvers may change row count, column count, or column names.
    dataset = Dataset(
        dataset_id=dataset.dataset_id,
        file_path=dataset.file_path,
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
        created_at=dataset.created_at,
        dataset_hash=dataset_hash,
        state=DatasetState.NORMALIZING,
        user_id=user_id,
    )
    schemas = profile_dataset(dataset, df)

    # --- Stage 4: Validate ---------------------------------------------------
    validate_dataset(dataset, df)

    # --- Stage 5: Build artifacts --------------------------------------------
    artifacts = build_artifacts(dataset, df, schemas, transformation_log, resolver_trace)
    dataset.transition(DatasetState.COMPLETE)

    logger.info(
        f"[Pipeline] COMPLETE dataset_id={dataset_id} "
        f"resolvers_applied={len(transformation_log)}"
    )

    return {
        "dataset_id": dataset_id,
        "user_id": user_id,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "resolvers_applied": len(transformation_log),
        "dataset_hash": dataset_hash,
        "state": dataset.state.value,
        "artifacts": artifacts,
    }
