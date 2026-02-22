"""
Prattern API Server
FastAPI backend with SSE streaming (web dashboard) and polling (mobile app) endpoints.

Run: uvicorn prattern.api.server:app --port 8000
"""

import asyncio
import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from prattern.config import Config
from prattern.data.precomputed import load_precomputed_movers, load_precomputed_analysis
from prattern.analysis.orchestrator import analyze_all_movers
from prattern.api.auth import ApiKeyMiddleware

app = FastAPI(title="Prattern Stock Engine API", version="1.0.0")

# CORS first (Starlette executes middleware in reverse order)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in Config.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth after CORS so preflight is handled before auth runs
app.add_middleware(ApiKeyMiddleware)

# In-memory job store for polling pattern
_jobs: Dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Health check (public, no auth)
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Pattern 1: Pre-computed data endpoints (instant)
# ---------------------------------------------------------------------------

@app.get("/movers")
def get_movers():
    """Return pre-computed movers from daily_movers.json (instant)."""
    data = load_precomputed_movers()
    if not data:
        raise HTTPException(status_code=404, detail="No pre-computed movers found. Run scan_universe.py first.")
    return data


@app.get("/analysis/latest")
def get_latest_analysis():
    """Return pre-computed analyzed movers from daily_analyzed.json (instant)."""
    data = load_precomputed_analysis()
    if not data:
        raise HTTPException(status_code=404, detail="No pre-computed analysis found. Run analyze_movers.py first.")
    return data


@app.get("/scan/status")
def get_scan_status():
    """Return scan metadata + staleness info."""
    movers_data = load_precomputed_movers()
    analysis_data = load_precomputed_analysis()
    today = datetime.now().strftime("%Y-%m-%d")

    result = {"today": today, "movers": None, "analysis": None}

    if movers_data:
        scan_date = movers_data.get("scan_date", "")
        result["movers"] = {
            "scan_date": scan_date,
            "scan_time": movers_data.get("scan_time", ""),
            "universe_size": movers_data.get("universe_size"),
            "movers_count": len(movers_data.get("movers", [])),
            "is_stale": scan_date != today,
        }

    if analysis_data:
        scan_date = analysis_data.get("scan_date", "")
        result["analysis"] = {
            "scan_date": scan_date,
            "analysis_time": analysis_data.get("analysis_time", ""),
            "analysis_duration_seconds": analysis_data.get("analysis_duration_seconds"),
            "movers_count": analysis_data.get("movers_count", 0),
            "is_stale": scan_date != today,
        }

    return result


# ---------------------------------------------------------------------------
# Pattern 2: SSE streaming endpoint (for web dashboard)
# ---------------------------------------------------------------------------

@app.post("/movers/analyze")
def analyze_movers_sse():
    """Run AI analysis with Server-Sent Events progress streaming."""
    movers_data = load_precomputed_movers()
    if not movers_data:
        raise HTTPException(status_code=404, detail="No pre-computed movers found. Run scan_universe.py first.")

    movers = movers_data["movers"]
    if not movers:
        raise HTTPException(status_code=404, detail="No movers in pre-computed data.")

    events = []
    done = threading.Event()
    result_holder = {"movers": None, "error": None}

    def on_progress(event):
        events.append(event)

    def run_analysis():
        try:
            analyzed = analyze_all_movers(movers, on_progress=on_progress)
            result_holder["movers"] = analyzed
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            done.set()

    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()

    async def event_generator():
        sent = 0
        while not done.is_set():
            while sent < len(events):
                evt = events[sent]
                yield f"event: progress\ndata: {json.dumps(evt)}\n\n"
                sent += 1
            await asyncio.sleep(0.5)

        while sent < len(events):
            evt = events[sent]
            yield f"event: progress\ndata: {json.dumps(evt)}\n\n"
            sent += 1

        if result_holder["error"]:
            yield f"event: error\ndata: {json.dumps({'error': result_holder['error']})}\n\n"
        else:
            analyzed = result_holder["movers"] or []
            yield f"event: complete\ndata: {json.dumps({'movers_count': len(analyzed), 'movers': analyzed})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Pattern 3: Polling endpoints (for iPhone app)
# ---------------------------------------------------------------------------

@app.post("/jobs/analyze")
def start_analysis_job():
    """Start a background analysis job. Returns job_id for polling."""
    movers_data = load_precomputed_movers()
    if not movers_data:
        raise HTTPException(status_code=404, detail="No pre-computed movers found. Run scan_universe.py first.")

    movers = movers_data["movers"]
    if not movers:
        raise HTTPException(status_code=404, detail="No movers in pre-computed data.")

    job_id = str(uuid.uuid4())
    job = {
        "status": "running",
        "progress": {"stage": "starting", "current": 0, "total": len(movers), "detail": ""},
        "results": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }
    _jobs[job_id] = job

    def on_progress(event):
        job["progress"] = event

    def run_analysis():
        try:
            analyzed = analyze_all_movers(movers, on_progress=on_progress)
            job["results"] = analyzed
            job["status"] = "complete"
        except Exception as e:
            job["error"] = str(e)
            job["status"] = "failed"

    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Poll status + progress for a background analysis job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "created_at": job["created_at"],
    }

    if job["status"] == "complete":
        response["movers_count"] = len(job["results"] or [])
        response["movers"] = job["results"]
    elif job["status"] == "failed":
        response["error"] = job["error"]

    return response


# ---------------------------------------------------------------------------
# SPA static file serving (production: serve built frontend)
# ---------------------------------------------------------------------------

_dist_dir = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
if _dist_dir.is_dir():
    from starlette.responses import FileResponse

    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(_dist_dir / "assets")), name="static")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Catch-all: serve index.html for SPA client-side routing."""
        file_path = _dist_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_dist_dir / "index.html"))
