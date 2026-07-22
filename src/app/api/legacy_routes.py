from fastapi import APIRouter, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, RedirectResponse, HTMLResponse
from pathlib import Path
import os
import sys

# Import helper functions and state from protein_viewer_web
from protein_viewer_web import (
    page_html,
    state_payload,
    run_scientist_job,
    snapshot_state,
    RUN_LOCK,
    RUN_STATE,
    latest_artifacts,
    detect_default_runtime,
    ROOT,
    OUTPUTS,
    REPORT_PATH
)

legacy_router = APIRouter()

@legacy_router.get("/", response_class=HTMLResponse)
def get_index_page():
    return HTMLResponse(content=page_html())

@legacy_router.get("/api/state")
def get_legacy_state():
    return JSONResponse(content=state_payload())

@legacy_router.post("/api/run/start")
async def start_legacy_run(
    request: Request,
    background_tasks: BackgroundTasks,
    goal: str = Form("Fold a protein sequence and explain the confidence metrics."),
    runtime: str = Form(None),
    sequence: str = Form(""),
    display_name: str = Form("")
):
    # Support both Form data and JSON body
    if request.headers.get("content-type") == "application/json":
        body = await request.json()
        goal = body.get("goal", goal)
        runtime = body.get("runtime", runtime)
        sequence = body.get("sequence", sequence)
        display_name = body.get("display_name", display_name)

    if not runtime:
        runtime = detect_default_runtime()

    with RUN_LOCK:
        active = bool(RUN_STATE.get("active"))
    if active:
        return JSONResponse(
            status_code=409,
            content={"ok": False, "error": "Run already active", "run_state": snapshot_state()}
        )

    # Launch scientist job in background task
    background_tasks.add_task(run_scientist_job, goal, runtime, sequence, display_name)

    return JSONResponse(
        content={"ok": True, "message": "Scientist run started.", "run_state": snapshot_state()}
    )

@legacy_router.get("/report")
def get_report():
    if REPORT_PATH.exists():
        content = REPORT_PATH.read_text(encoding="utf-8")
    else:
        content = "# No report generated yet."
    return PlainTextResponse(content=content, media_type="text/markdown; charset=utf-8")

@legacy_router.get("/results.html")
def get_results_html():
    p = ROOT / "results.html"
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="results.html not found")

@legacy_router.get("/handoff.html")
def get_handoff_html():
    p = ROOT / "handoff.html"
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="handoff.html not found")

@legacy_router.get("/learning_pack.html")
def get_learning_pack_html():
    p = OUTPUTS / "learning_pack.html"
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="learning_pack.html not found")

@legacy_router.get("/5-lesson-learning-pack.html")
def get_learning_pack_redirect():
    return RedirectResponse(url="/learning_pack.html")

@legacy_router.get("/outputs/{filename:path}")
def get_output_file(filename: str):
    file_path = OUTPUTS / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@legacy_router.get("/artifact/{artifact_name}")
def get_artifact_file(artifact_name: str):
    artifacts = latest_artifacts()
    artifact = next((item for item in artifacts if item.get("name") == artifact_name), None)
    if artifact and artifact.get("path"):
        p = Path(str(artifact["path"]))
        if p.exists():
            return FileResponse(p)
    candidate = OUTPUTS / artifact_name
    if candidate.exists():
        return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="Artifact not found")

@legacy_router.get("/viewer/{filename:path}")
def get_viewer_file(filename: str):
    if filename in ("", "/"):
        viewer_html = OUTPUTS / "viewer.html"
        if viewer_html.exists():
            return FileResponse(viewer_html)
        raise HTTPException(status_code=404, detail="Viewer HTML not found")
    root_path = ROOT / filename
    if root_path.exists() and root_path.is_file():
        return FileResponse(root_path)
    output_path = OUTPUTS / filename
    if output_path.exists() and output_path.is_file():
        return FileResponse(output_path)
    raise HTTPException(status_code=404, detail="Viewer asset not found")
