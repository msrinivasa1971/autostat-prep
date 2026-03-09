"""
UI routes — Jinja2-rendered HTML pages for dataset inspection.
"""
import json
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.routes import _jobs, _run_normalization_job
from app.config import TEMPLATES_DIR, USERS_STORAGE_DIR
from app.models.overrides import ColumnOverride
from app.services.autostat_client import send_dataset_for_analysis
from app.services.override_service import load_overrides, save_overrides
from app.utils.file_storage import find_dataset_dir, save_uploaded_file

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
ui_router = APIRouter(tags=["ui"])

_ARTIFACT_FILENAMES = {
    "normalized": "normalized.csv",
    "report":     "report.md",
    "schema":     "schema.json",
    "trace":      "resolver_trace.json",
    "overrides":  "overrides.json",
    "analysis":   "analysis_report.json",
}
_ARTIFACT_MEDIA = {
    "normalized": "text/csv",
    "report":     "text/markdown",
    "schema":     "application/json",
    "trace":      "application/json",
    "overrides":  "application/json",
    "analysis":   "application/json",
}


def _user_id_from_dir(dataset_dir: Path) -> str:
    return dataset_dir.parent.parent.name


@ui_router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html")


@ui_router.post("/ui/upload")
async def ui_upload(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    content = await file.read()
    try:
        dataset_id, file_path = save_uploaded_file(content, file.filename or "upload")
    except ValueError as exc:
        return templates.TemplateResponse(request, "home.html", {"error": str(exc)}, status_code=400)
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "NORMALIZING", "dataset_id": dataset_id}
    background_tasks.add_task(_run_normalization_job, job_id, dataset_id, file_path)
    return RedirectResponse(f"/jobs/{job_id}/view", status_code=303)


@ui_router.get("/jobs/{job_id}/view", response_class=HTMLResponse)
def job_status_page(request: Request, job_id: str) -> HTMLResponse:
    job = _jobs.get(job_id)
    return templates.TemplateResponse(request, "job_status.html", {"job_id": job_id, "job": job})


@ui_router.get("/datasets/{dataset_id}/preview", response_class=HTMLResponse)
def dataset_preview(request: Request, dataset_id: str) -> HTMLResponse:
    dataset_dir = find_dataset_dir(dataset_id)
    _error_ctx = {"dataset_id": dataset_id, "error": "Normalized dataset not found. Run normalization first.",
                  "columns": [], "rows": [], "schema_types": {}, "overrides_count": 0, "has_analysis_report": False}
    if dataset_dir is None or not (dataset_dir / "normalized.csv").exists():
        return templates.TemplateResponse(request, "dataset_preview.html", _error_ctx)

    df = pd.read_csv(dataset_dir / "normalized.csv", nrows=50)
    schema_types: dict = {}
    schema_path = dataset_dir / "schema.json"
    if schema_path.exists():
        for col in json.loads(schema_path.read_text(encoding="utf-8")).get("columns", []):
            schema_types[col["column_name"]] = col["inferred_type"]

    user_id = _user_id_from_dir(dataset_dir)
    overrides = load_overrides(dataset_id, user_id=user_id)
    ignored = {o.column_name for o in overrides if o.override_type == "IGNORE"}
    visible = [c for c in df.columns if c not in ignored]
    df = df[visible]
    return templates.TemplateResponse(request, "dataset_preview.html", {
        "dataset_id": dataset_id, "columns": list(df.columns),
        "rows": df.values.tolist(), "schema_types": schema_types, "overrides_count": len(overrides),
        "has_analysis_report": (dataset_dir / "analysis_report.json").exists(),
    })


@ui_router.get("/datasets/{dataset_id}/overrides", response_class=HTMLResponse)
def overrides_page(request: Request, dataset_id: str, saved: int = 0) -> HTMLResponse:
    dataset_dir = find_dataset_dir(dataset_id)
    if dataset_dir is None or not (dataset_dir / "normalized.csv").exists():
        return templates.TemplateResponse(request, "overrides.html", {
            "dataset_id": dataset_id, "error": "Normalization not complete for this dataset.",
            "columns": [], "schema_types": {}, "override_map": {},
        })
    schema_path = dataset_dir / "schema.json"
    columns, schema_types = [], {}
    if schema_path.exists():
        for col in json.loads(schema_path.read_text(encoding="utf-8")).get("columns", []):
            columns.append(col["column_name"])
            schema_types[col["column_name"]] = col["inferred_type"]
    user_id = _user_id_from_dir(dataset_dir)
    override_map = {o.column_name: o.override_type for o in load_overrides(dataset_id, user_id=user_id)}
    return templates.TemplateResponse(request, "overrides.html", {
        "dataset_id": dataset_id, "columns": columns, "schema_types": schema_types,
        "override_map": override_map, "saved": bool(saved),
    })


@ui_router.post("/datasets/{dataset_id}/overrides")
async def save_dataset_overrides(request: Request, dataset_id: str):
    dataset_dir = find_dataset_dir(dataset_id)
    if dataset_dir is None or not (dataset_dir / "normalized.csv").exists():
        raise HTTPException(status_code=400, detail="Cannot set overrides: dataset normalization is not complete.")
    schema_path = dataset_dir / "schema.json"
    columns = []
    if schema_path.exists():
        columns = [c["column_name"] for c in json.loads(schema_path.read_text(encoding="utf-8")).get("columns", [])]
    form = await request.form()
    overrides = []
    for col in columns:
        raw = str(form.get(f"col_{col}", "DEFAULT"))
        if raw == "DEFAULT":
            continue
        try:
            overrides.append(ColumnOverride(dataset_id=dataset_id, column_name=col, override_type=raw))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    user_id = _user_id_from_dir(dataset_dir)
    save_overrides(dataset_id, overrides, user_id=user_id)
    return RedirectResponse(f"/datasets/{dataset_id}/overrides?saved=1", status_code=303)


@ui_router.get("/download/{dataset_id}/{artifact}")
def download_artifact(dataset_id: str, artifact: str) -> FileResponse:
    if artifact not in _ARTIFACT_FILENAMES:
        raise HTTPException(status_code=404, detail=f"Unknown artifact: {artifact!r}")
    dataset_dir = find_dataset_dir(dataset_id)
    if dataset_dir is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    path = dataset_dir / _ARTIFACT_FILENAMES[artifact]
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact}' not found")
    return FileResponse(path=str(path), media_type=_ARTIFACT_MEDIA[artifact], filename=_ARTIFACT_FILENAMES[artifact])


@ui_router.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard(request: Request, user_id: str) -> HTMLResponse:
    datasets_root = USERS_STORAGE_DIR / user_id / "datasets"
    datasets = []
    if datasets_root.exists():
        for d in sorted(datasets_root.iterdir()):
            if not d.is_dir():
                continue
            datasets.append({
                "dataset_id": d.name,
                "state": "COMPLETE" if (d / "normalized.csv").exists() else "UPLOADED",
                "preview_url": f"/datasets/{d.name}/preview",
                "overrides_url": f"/datasets/{d.name}/overrides",
                "download_normalized": f"/download/{d.name}/normalized",
                "download_report": f"/download/{d.name}/report",
                "download_schema": f"/download/{d.name}/schema",
            })
    return templates.TemplateResponse(request, "dashboard.html", {"user_id": user_id, "datasets": datasets})


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/analyze  — Send to AutoStat
# ---------------------------------------------------------------------------

@ui_router.post("/datasets/{dataset_id}/analyze")
def analyze_dataset(dataset_id: str) -> JSONResponse:
    """
    Send the normalized dataset to AutoStat for statistical analysis.

    Returns 503 if AUTOSTAT_API_URL is not configured.
    Returns 400 if normalization is not complete.
    Saves analysis_report.json in the dataset directory on success.
    """
    dataset_dir = find_dataset_dir(dataset_id)
    if dataset_dir is None or not (dataset_dir / "normalized.csv").exists():
        raise HTTPException(
            status_code=400,
            detail="Cannot analyze: dataset normalization is not complete.",
        )

    user_id = _user_id_from_dir(dataset_dir)
    try:
        result = send_dataset_for_analysis(dataset_id, user_id=user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AutoStat service error: {exc}")

    return JSONResponse(
        {"status": "complete", "dataset_id": dataset_id, "analysis": result}
    )
