import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from app.pipeline.normalization_pipeline import run_normalization_pipeline
from app.services.dataset_loader import load_dataset
from app.services.profiler import profile_dataset
from app.utils.file_storage import find_raw_file, save_uploaded_file
from app.utils.logging_config import get_logger

router = APIRouter(prefix="/prep", tags=["prep"])
logger = get_logger(__name__)

# In-memory job store: job_id → {status, dataset_id, user_id, artifacts?, error?}
_jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# POST /prep/upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    user_id: str = Form(default="default"),
) -> JSONResponse:
    """
    Accept a CSV or XLSX file and store it under the user's dataset directory.

    Returns dataset_id for use in subsequent endpoints.
    """
    logger.info(f"Upload request: filename={file.filename} user={user_id}")

    content = await file.read()

    try:
        dataset_id, _ = save_uploaded_file(content, file.filename or "upload", user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info(f"Upload complete: dataset_id={dataset_id} user={user_id}")
    return JSONResponse({"dataset_id": dataset_id, "user_id": user_id, "status": "uploaded"})


# ---------------------------------------------------------------------------
# GET /prep/profile/{dataset_id}
# ---------------------------------------------------------------------------

@router.get("/profile/{dataset_id}")
def get_profile(dataset_id: str, user_id: str = Query(default="default")) -> JSONResponse:
    """
    Return a column-level profile of an uploaded dataset.
    """
    file_path = find_raw_file(dataset_id, user_id=user_id or None)
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
# POST /prep/normalize/{dataset_id}  (async — returns job_id immediately)
# ---------------------------------------------------------------------------

@router.post("/normalize/{dataset_id}")
async def normalize_dataset(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Query(default="default"),
) -> JSONResponse:
    """
    Start asynchronous normalization of an uploaded dataset.

    Returns a job_id immediately; normalization runs in the background.
    Poll GET /prep/jobs/{job_id} for status and results.
    """
    file_path = find_raw_file(dataset_id, user_id=user_id or None)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        )

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "NORMALIZING", "dataset_id": dataset_id, "user_id": user_id}
    background_tasks.add_task(_run_normalization_job, job_id, dataset_id, file_path, user_id)

    logger.info(f"Normalization job queued: job_id={job_id} dataset_id={dataset_id} user={user_id}")
    return JSONResponse({"job_id": job_id, "status": "NORMALIZING"})


# ---------------------------------------------------------------------------
# GET /prep/jobs/{job_id}
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> JSONResponse:
    """
    Return the current status of a normalization job.

    Status values: NORMALIZING, COMPLETE, FAILED
    """
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JSONResponse({"job_id": job_id, **job})


# ---------------------------------------------------------------------------
# Background task helper
# ---------------------------------------------------------------------------

def _run_normalization_job(
    job_id: str,
    dataset_id: str,
    file_path: Path,
    user_id: str = "default",
) -> None:
    """Execute the normalization pipeline and update the job store."""
    try:
        result: Dict[str, Any] = run_normalization_pipeline(dataset_id, file_path, user_id=user_id)
        _jobs[job_id] = {
            "status": "COMPLETE",
            "dataset_id": dataset_id,
            "user_id": user_id,
            "row_count": result["row_count"],
            "column_count": result["column_count"],
            "resolvers_applied": result["resolvers_applied"],
            "dataset_hash": result["dataset_hash"],
            "artifacts": result["artifacts"],
        }
        logger.info(f"Job {job_id} COMPLETE")
    except Exception as exc:
        _jobs[job_id] = {
            "status": "FAILED",
            "dataset_id": dataset_id,
            "user_id": user_id,
            "error": str(exc),
        }
        logger.error(f"Job {job_id} FAILED: {exc}")
