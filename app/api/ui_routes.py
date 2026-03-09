"""
UI routes — Jinja2-rendered HTML pages for dataset inspection.

Routes:
    GET  /                          → home page (upload form)
    POST /ui/upload                 → handle form upload, start job, redirect
    GET  /jobs/{job_id}/view        → job status page
    GET  /datasets/{dataset_id}/preview  → normalized data preview
    GET  /download/{dataset_id}/{artifact} → serve artifact file
"""
import json
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.routes import _jobs, _run_normalization_job
from app.config import NORMALIZED_DIR, REPORTS_DIR, SCHEMAS_DIR, TEMPLATES_DIR
from app.utils.file_storage import find_raw_file, save_uploaded_file

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ui_router = APIRouter(tags=["ui"])

# Artifact-type → file path resolver
_ARTIFACT_PATHS = {
    "normalized": lambda did: NORMALIZED_DIR / f"{did}_normalized.csv",
    "report":     lambda did: REPORTS_DIR   / f"{did}_report.md",
    "schema":     lambda did: SCHEMAS_DIR   / f"{did}_schema.json",
    "trace":      lambda did: REPORTS_DIR   / f"{did}_resolver_trace.json",
}

_ARTIFACT_MEDIA = {
    "normalized": "text/csv",
    "report":     "text/markdown",
    "schema":     "application/json",
    "trace":      "application/json",
}


# ---------------------------------------------------------------------------
# GET /  — Home page
# ---------------------------------------------------------------------------

@ui_router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html")


# ---------------------------------------------------------------------------
# POST /ui/upload  — Form upload handler
# ---------------------------------------------------------------------------

@ui_router.post("/ui/upload")
async def ui_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> RedirectResponse:
    """
    Accept form file upload, save file, queue normalization job, redirect to
    job status page.  Upload logic is delegated to save_uploaded_file() — not
    duplicated here.
    """
    content = await file.read()
    try:
        dataset_id, file_path = save_uploaded_file(content, file.filename or "upload")
    except ValueError as exc:
        return templates.TemplateResponse(
            request, "home.html", {"error": str(exc)}, status_code=400
        )

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "NORMALIZING", "dataset_id": dataset_id}
    background_tasks.add_task(_run_normalization_job, job_id, dataset_id, file_path)

    return RedirectResponse(f"/jobs/{job_id}/view", status_code=303)


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/view  — Job status page
# ---------------------------------------------------------------------------

@ui_router.get("/jobs/{job_id}/view", response_class=HTMLResponse)
def job_status_page(request: Request, job_id: str) -> HTMLResponse:
    job = _jobs.get(job_id)
    return templates.TemplateResponse(
        request, "job_status.html", {"job_id": job_id, "job": job}
    )


# ---------------------------------------------------------------------------
# GET /datasets/{dataset_id}/preview  — Data preview page
# ---------------------------------------------------------------------------

@ui_router.get("/datasets/{dataset_id}/preview", response_class=HTMLResponse)
def dataset_preview(request: Request, dataset_id: str) -> HTMLResponse:
    csv_path = NORMALIZED_DIR / f"{dataset_id}_normalized.csv"
    schema_path = SCHEMAS_DIR / f"{dataset_id}_schema.json"

    if not csv_path.exists():
        return templates.TemplateResponse(
            request,
            "dataset_preview.html",
            {
                "dataset_id": dataset_id,
                "error": "Normalized dataset not found. Run normalization first.",
                "columns": [],
                "rows": [],
                "schema_types": {},
            },
        )

    df = pd.read_csv(csv_path, nrows=50)
    columns = list(df.columns)
    rows = df.values.tolist()

    schema_types: dict = {}
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for col in schema.get("columns", []):
            schema_types[col["column_name"]] = col["inferred_type"]

    return templates.TemplateResponse(
        request,
        "dataset_preview.html",
        {
            "dataset_id": dataset_id,
            "columns": columns,
            "rows": rows,
            "schema_types": schema_types,
        },
    )


# ---------------------------------------------------------------------------
# GET /download/{dataset_id}/{artifact}  — Serve artifact file
# ---------------------------------------------------------------------------

@ui_router.get("/download/{dataset_id}/{artifact}")
def download_artifact(dataset_id: str, artifact: str) -> FileResponse:
    """Serve a generated artifact file for download."""
    if artifact not in _ARTIFACT_PATHS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown artifact type: {artifact!r}. "
                   f"Valid types: {list(_ARTIFACT_PATHS)}",
        )
    path: Path = _ARTIFACT_PATHS[artifact](dataset_id)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Artifact not found for dataset {dataset_id}",
        )
    return FileResponse(
        path=str(path),
        media_type=_ARTIFACT_MEDIA[artifact],
        filename=path.name,
    )
