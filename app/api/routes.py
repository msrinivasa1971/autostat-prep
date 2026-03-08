from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.pipeline.normalization_pipeline import run_normalization_pipeline
from app.services.dataset_loader import load_dataset
from app.services.profiler import profile_dataset
from app.utils.file_storage import find_raw_file, save_uploaded_file
from app.utils.logging_config import get_logger

router = APIRouter(prefix="/prep", tags=["prep"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# POST /prep/upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)) -> JSONResponse:
    """
    Accept a CSV or XLSX file and store it in storage/raw/.

    Returns dataset_id for use in subsequent endpoints.
    """
    logger.info(f"Upload request: filename={file.filename}")

    content = await file.read()

    try:
        dataset_id, _ = save_uploaded_file(content, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info(f"Upload complete: dataset_id={dataset_id}")
    return JSONResponse({"dataset_id": dataset_id, "status": "uploaded"})


# ---------------------------------------------------------------------------
# GET /prep/profile/{dataset_id}
# ---------------------------------------------------------------------------

@router.get("/profile/{dataset_id}")
def get_profile(dataset_id: str) -> JSONResponse:
    """
    Return a column-level profile of an uploaded dataset.
    """
    file_path = find_raw_file(dataset_id)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        )

    try:
        dataset, df = load_dataset(dataset_id, file_path)
        schemas = profile_dataset(dataset, df)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    columns_detail = [
        {
            "column_name": s.column_name,
            "missing_ratio": s.missing_ratio,
            "unique_values": s.unique_values,
        }
        for s in schemas
    ]

    return JSONResponse(
        {
            "dataset_id": dataset_id,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "column_names": dataset.columns,
            "columns": columns_detail,
        }
    )


# ---------------------------------------------------------------------------
# POST /prep/normalize/{dataset_id}
# ---------------------------------------------------------------------------

@router.post("/normalize/{dataset_id}")
def normalize_dataset(dataset_id: str) -> JSONResponse:
    """
    Run the full normalization pipeline and write all output artifacts.
    """
    file_path = find_raw_file(dataset_id)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        )

    try:
        result: Dict[str, Any] = run_normalization_pipeline(dataset_id, file_path)
    except ValueError as exc:
        # FDG validation failures → 422 Unprocessable Entity
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return JSONResponse(
        {
            "dataset_id": result["dataset_id"],
            "status": "normalized",
            "artifacts": result["artifacts"],
        }
    )
