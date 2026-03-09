"""
UI routes — Jinja2-rendered HTML pages for dataset inspection.

Routes:
    GET  /                               → home page (upload form)
    POST /ui/upload                      → handle form upload, start job, redirect
    GET  /jobs/{job_id}/view             → job status page
    GET  /datasets/{dataset_id}/preview  → normalized data preview (respects overrides)
    GET  /datasets/{dataset_id}/overrides  → column override management page
    POST /datasets/{dataset_id}/overrides  → save column overrides
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
from app.config import NORMALIZED_DIR, OVERRIDES_DIR, REPORTS_DIR, SCHEMAS_DIR, TEMPLATES_DIR
from app.models.overrides import ALLOWED_OVERRIDE_TYPES, ColumnOverride
from app.services.override_service import load_overrides, save_overrides
from app.utils.file_storage import find_raw_file, save_uploaded_file

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ui_router = APIRouter(tags=["ui"])

# Artifact-type → file path resolver
_ARTIFACT_PATHS = {
    "normalized": lambda did: NORMALIZED_DIR / f"{did}_normalized.csv",
    "report":     lambda did: REPORTS_DIR    / f"{did}_report.md",
    "schema":     lambda did: SCHEMAS_DIR    / f"{did}_schema.json",
    "trace":      lambda did: REPORTS_DIR    / f"{did}_resolver_trace.json",
    "overrides":  lambda did: OVERRIDES_DIR  / f"{did}_overrides.json",
}

_ARTIFACT_MEDIA = {
    "normalized": "text/csv",
    "report":     "text/markdown",
    "schema":     "application/json",
    "trace":      "application/json",
    "overrides":  "application/json",
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
                "overrides_count": 0,
            },
        )

    df = pd.read_csv(csv_path, nrows=50)

    schema_types: dict = {}
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for col in schema.get("columns", []):
            schema_types[col["column_name"]] = col["inferred_type"]

    # Apply overrides: remove IGNORE columns from the preview
    overrides = load_overrides(dataset_id)
    ignored = {o.column_name for o in overrides if o.override_type == "IGNORE"}
    visible_cols = [c for c in df.columns if c not in ignored]
    df = df[visible_cols]
    columns = list(df.columns)
    rows = df.values.tolist()

    return templates.TemplateResponse(
        request,
        "dataset_preview.html",
        {
            "dataset_id": dataset_id,
            "columns": columns,
            "rows": rows,
            "schema_types": schema_types,
            "overrides_count": len(overrides),
        },
    )


# ---------------------------------------------------------------------------
# GET /datasets/{dataset_id}/overrides  — Override management page
# ---------------------------------------------------------------------------

@ui_router.get("/datasets/{dataset_id}/overrides", response_class=HTMLResponse)
def overrides_page(request: Request, dataset_id: str, saved: int = 0) -> HTMLResponse:
    csv_path = NORMALIZED_DIR / f"{dataset_id}_normalized.csv"
    if not csv_path.exists():
        return templates.TemplateResponse(
            request,
            "overrides.html",
            {
                "dataset_id": dataset_id,
                "error": "Normalization not complete for this dataset.",
                "columns": [],
                "schema_types": {},
                "override_map": {},
            },
        )

    schema_path = SCHEMAS_DIR / f"{dataset_id}_schema.json"
    columns: list = []
    schema_types: dict = {}
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for col in schema.get("columns", []):
            columns.append(col["column_name"])
            schema_types[col["column_name"]] = col["inferred_type"]

    existing = load_overrides(dataset_id)
    override_map = {o.column_name: o.override_type for o in existing}

    return templates.TemplateResponse(
        request,
        "overrides.html",
        {
            "dataset_id": dataset_id,
            "columns": columns,
            "schema_types": schema_types,
            "override_map": override_map,
            "saved": bool(saved),
        },
    )


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/overrides  — Save overrides
# ---------------------------------------------------------------------------

@ui_router.post("/datasets/{dataset_id}/overrides")
async def save_dataset_overrides(request: Request, dataset_id: str) -> RedirectResponse:
    """
    Parse the override form and persist selected overrides.
    Only allowed when normalization is complete (normalized CSV must exist).
    """
    csv_path = NORMALIZED_DIR / f"{dataset_id}_normalized.csv"
    if not csv_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Cannot set overrides: dataset normalization is not complete.",
        )

    schema_path = SCHEMAS_DIR / f"{dataset_id}_schema.json"
    columns: list = []
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        columns = [c["column_name"] for c in schema.get("columns", [])]

    form = await request.form()
    overrides: list = []
    for col in columns:
        raw_value = str(form.get(f"col_{col}", "DEFAULT"))
        if raw_value == "DEFAULT":
            continue
        try:
            overrides.append(
                ColumnOverride(
                    dataset_id=dataset_id,
                    column_name=col,
                    override_type=raw_value,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    save_overrides(dataset_id, overrides)
    return RedirectResponse(f"/datasets/{dataset_id}/overrides?saved=1", status_code=303)


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
