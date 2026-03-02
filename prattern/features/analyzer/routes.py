"""Analyzer feature routes — movers, analysis, scan status, SSE, and polling."""

import asyncio
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from prattern.data.precomputed import load_precomputed_movers, load_precomputed_analysis
from prattern.features.analyzer.orchestrator import analyze_all_movers

router = APIRouter()

# In-memory job store for polling pattern
_jobs: Dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pattern 1: Pre-computed data endpoints (instant)
# ---------------------------------------------------------------------------

@router.get("/movers")
def get_movers():
    """Return pre-computed movers from daily_movers.json (instant)."""
    data = load_precomputed_movers()
    if not data:
        raise HTTPException(status_code=404, detail="No pre-computed movers found. Run scan_universe.py first.")
    return data


@router.get("/analysis/latest")
def get_latest_analysis():
    """Return pre-computed analyzed movers from daily_analyzed.json (instant)."""
    data = load_precomputed_analysis()
    if not data:
        raise HTTPException(status_code=404, detail="No pre-computed analysis found. Run analyze_movers.py first.")
    return data


@router.get("/scan/status")
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

@router.post("/movers/analyze")
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

@router.post("/jobs/analyze")
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


@router.get("/jobs/{job_id}")
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
# Pattern 4: Full pipeline refresh (admin-only, runs scanner + analyzer)
# ---------------------------------------------------------------------------

# Project root for locating job scripts
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@router.post("/scan/refresh")
def start_scan_refresh():
    """Run scanner + analyzer pipeline as subprocesses. Returns job_id for polling via GET /jobs/{job_id}."""
    job_id = str(uuid.uuid4())
    job = {
        "status": "running",
        "progress": {"stage": "scanning", "current": 0, "total": 2, "detail": "Starting universe scan..."},
        "results": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }
    _jobs[job_id] = job

    def run_pipeline():
        scanner_script = os.path.join(_PROJECT_ROOT, "jobs", "scan_universe.py")
        analyzer_script = os.path.join(_PROJECT_ROOT, "jobs", "analyze_movers.py")

        # Phase 1: Scanner
        try:
            job["progress"] = {"stage": "scanning", "current": 1, "total": 2, "detail": "Scanning universe for movers..."}
            result = subprocess.run(
                [sys.executable, "-u", scanner_script],
                capture_output=True, text=True, timeout=1200,
                cwd=_PROJECT_ROOT,
            )
            if result.returncode != 0:
                job["error"] = f"Scanner failed: {result.stderr[:500]}"
                job["status"] = "failed"
                return
        except subprocess.TimeoutExpired:
            job["error"] = "Scanner timed out after 10 minutes"
            job["status"] = "failed"
            return
        except Exception as e:
            job["error"] = f"Scanner error: {str(e)}"
            job["status"] = "failed"
            return

        # Phase 2: Analyzer
        try:
            job["progress"] = {"stage": "analyzing", "current": 2, "total": 2, "detail": "Running AI analysis on movers..."}
            result = subprocess.run(
                [sys.executable, "-u", analyzer_script],
                capture_output=True, text=True, timeout=1200,
                cwd=_PROJECT_ROOT,
            )
            if result.returncode != 0:
                job["error"] = f"Analyzer failed: {result.stderr[:500]}"
                job["status"] = "failed"
                return
        except subprocess.TimeoutExpired:
            job["error"] = "Analyzer timed out after 15 minutes"
            job["status"] = "failed"
            return
        except Exception as e:
            job["error"] = f"Analyzer error: {str(e)}"
            job["status"] = "failed"
            return

        # Load fresh results
        analysis = load_precomputed_analysis()
        job["results"] = analysis.get("movers", []) if analysis else []
        job["progress"] = {"stage": "complete", "current": 2, "total": 2, "detail": "Pipeline complete"}
        job["status"] = "complete"

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    return {"job_id": job_id}
