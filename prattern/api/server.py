"""
Prattern API Server
FastAPI backend with feature-based routing.

Run: uvicorn prattern.api.server:app --port 8000
"""

import logging
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

_start = time.time()
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("prattern.startup")

_log.info("Importing config...")
from prattern.config import Config
_log.info("Importing auth...")
from prattern.api.auth import ApiKeyMiddleware
_log.info("Importing analyzer routes...")
from prattern.features.analyzer.routes import router as analyzer_router
_log.info("Importing theme tracker routes...")
from prattern.features.theme_tracker.routes import router as theme_router
_log.info("Importing trade analyzer routes...")
from prattern.features.trade_analyzer.routes import router as trade_router
_log.info("All imports done in %.1fs", time.time() - _start)

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

# Mount feature routers
app.include_router(analyzer_router)
app.include_router(theme_router)
app.include_router(trade_router)


# ---------------------------------------------------------------------------
# Health check (public, no auth)
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


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
