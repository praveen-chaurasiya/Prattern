"""Railway startup wrapper — diagnostics before uvicorn."""
import os
import sys
import time

print("=== Prattern Startup ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}", flush=True)

try:
    import resource
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Memory (KB): {mem}", flush=True)
except ImportError:
    print("(resource module not available)", flush=True)

t0 = time.time()
print("Importing app...", flush=True)

from prattern.api.server import app  # noqa: F401

print(f"App imported in {time.time() - t0:.2f}s", flush=True)

port = int(os.environ.get("PORT", 8000))
print(f"Starting uvicorn on port {port}...", flush=True)

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
