# lessons.md — Prattern Stock Engine

> **Purpose:** Running log of mistakes, corrections, and rules learned.  
> **When to update:** After EVERY correction from the user, or after any task post-mortem.  
> **When to read:** At the START of each new Claude Code session on this project.

---

## How to Add a Lesson

```
### [L-###] Short title of the mistake
**Date:** YYYY-MM-DD  
**Category:** [Provider | Pipeline | AI Classification | Frontend | Config | Data Integrity | Other]  
**Trigger:** What happened / what correction was given  
**Root cause:** Why it happened  
**Rule:** The concrete rule to prevent recurrence  
**Files affected:** Which files are involved  
```

---

## Lessons Log

---

### [L-001] Template — Fill this in after your first correction
**Date:** YYYY-MM-DD  
**Category:** Config  
**Trigger:** User corrected Claude for hardcoding a threshold value  
**Root cause:** Threshold was written inline in `scan_universe.py` instead of read from `Config`  
**Rule:** All thresholds, model names, category lists, and provider names MUST live in `prattern/config.py`. Never hardcode these in job scripts, providers, or the CLI.  
**Files affected:** `prattern/config.py`, `jobs/scan_universe.py`

---

### [L-002] Template — Provider interface mismatch
**Date:** YYYY-MM-DD  
**Category:** Provider  
**Trigger:** New provider passed mypy but failed at runtime because return type didn't match Protocol  
**Root cause:** `PriceProvider` Protocol in `base.py` expects `dict[str, Decimal]` but new provider returned `dict[str, float]`  
**Rule:** Before implementing a provider, READ `prattern/providers/base.py` first. Match return types exactly — use `decimal.Decimal` for all price values, not `float`.  
**Files affected:** `prattern/providers/base.py`, any new `*_provider.py`

---

### [L-003] Template — Emoji in backend log broke Windows pipeline
**Date:** YYYY-MM-DD  
**Category:** Pipeline  
**Trigger:** `run_scan.bat` crashed with `UnicodeEncodeError` on Windows  
**Root cause:** A `print("✅ scan complete")` was added during debugging  
**Rule:** Backend code (anything in `prattern/`, `jobs/`, `cli/`) must NEVER use emoji. Use `[OK]` and `[ERROR]` prefixes. Only frontend/web code may use emoji.  
**Files affected:** Any backend `.py` file

---

### [L-004] Template — Polars import order caused GUI crash
**Date:** YYYY-MM-DD  
**Category:** GUI  
**Trigger:** `gui/pratten_app.py` crashed on startup with CPU feature error  
**Root cause:** `import polars` appeared before `os.environ["POLARS_SKIP_CPU_CHECK"] = "1"`  
**Rule:** In `gui/pratten_app.py`, the env var `POLARS_SKIP_CPU_CHECK=1` MUST be set before ANY polars import, even indirect ones. This line must stay at the very top of the file above all other imports.  
**Files affected:** `gui/pratten_app.py`

---

### [L-005] Template — Schema drift between Python and TypeScript
**Date:** YYYY-MM-DD  
**Category:** Data Integrity  
**Trigger:** Web dashboard showed undefined fields after backend dataclass was renamed  
**Root cause:** `AnalyzedMover` field was renamed in Python but `web/src/types/movers.ts` was not updated  
**Rule:** Any rename or addition of fields in `Mover`, `AnalyzedMover`, or `ScanResult` in `prattern/core/models.py` requires an immediate matching update to `web/src/types/movers.ts`. These two files are a contract — treat them as coupled.  
**Files affected:** `prattern/core/models.py`, `web/src/types/movers.ts`

---

### [L-006] Template — AI batch classification bled across tickers
**Date:** YYYY-MM-DD  
**Category:** AI Classification  
**Trigger:** Two tickers in the same Gemini batch were given the same theme despite unrelated news  
**Root cause:** Prompt didn't explicitly enforce per-ticker isolation in batch requests  
**Rule:** Gemini batch classification prompts must include explicit instruction: "Each ticker's classification must be based ONLY on its own news. Do not let one ticker's context influence another's." Add this to the system prompt in `prattern/providers/ai/gemini.py`.  
**Files affected:** `prattern/providers/ai/gemini.py`

---

### [L-007] Heavy imports at module level caused GUI startup hang
**Date:** 2026-02-26
**Category:** GUI
**Trigger:** User reported GUI taking extremely long to start
**Root cause:** `yfinance` was imported at top level in `theme_tracker/service.py` and `providers/prices/yfinance_provider.py`. Since the GUI imports these modules eagerly, yfinance (which pulls in requests, pandas internals, etc.) loaded before the window could render.
**Rule:** Heavy third-party libraries (yfinance, google.generativeai, anthropic, matplotlib) must be lazy-imported inside the function that uses them, never at module top level. Only stdlib and lightweight internal modules at the top.
**Files affected:** `prattern/features/theme_tracker/service.py`, `prattern/providers/prices/yfinance_provider.py`, `prattern/data/prices.py`

---

### [L-008] darkdetect 0.8.0 hangs on Python 3.14 — must be stubbed
**Date:** 2026-02-27
**Category:** GUI
**Trigger:** GUI hung indefinitely on startup
**Root cause:** `darkdetect` 0.8.0 (dependency of customtkinter 5.2.2) hangs during its `_windows_detect` module import on Python 3.14. The ctypes registry watcher setup never returns.
**Rule:** `gui/pratten_app.py` must stub out `darkdetect` in `sys.modules` BEFORE importing customtkinter. We hardcode dark mode anyway, so system detection is unnecessary. If upgrading customtkinter or darkdetect, re-test startup time.
**Files affected:** `gui/pratten_app.py`

---

### [L-009] Provider registry must be lazy — eager import of all providers blocks scanner
**Date:** 2026-02-27
**Category:** Provider
**Trigger:** Refresh Scan timed out after 600s; last log line was `import google.generativeai`
**Root cause:** `_auto_register()` in `providers/__init__.py` imported ALL providers (including AI libs) on the first `get_provider()` call. The scanner only needs `universe` + `prices`, but it paid the cost of importing `google.generativeai` and `anthropic` — which on Python 3.14 took extremely long or hung.
**Rule:** Provider registry must use lazy factories. Each provider is only imported + instantiated when `get_provider()` is called for that specific type+name. Never eagerly import all providers at once.
**Files affected:** `prattern/providers/__init__.py`

---

### [L-010] Unanchored .gitignore patterns excluded Python packages from repo
**Date:** 2026-03-03
**Category:** Deployment
**Trigger:** Railway deploy failed with `ModuleNotFoundError: No module named 'prattern.data'` — build-time import check caught it
**Root cause:** `.gitignore` had unanchored `data/` and `themes/` patterns. Git's pattern matching applies at any directory level, so `data/` excluded both the root-level `data/` (runtime JSON, correctly ignored) AND `prattern/data/` (Python package with `precomputed.py`, `prices.py`, etc.). The files existed locally but were never committed to git, so Railway's clone didn't have them.
**Rule:** `.gitignore` patterns for top-level directories MUST be anchored with a leading slash (`/data/`, `/themes/`). Before adding any directory to `.gitignore`, verify it won't accidentally match a same-named directory nested inside `prattern/`. After editing `.gitignore`, run `git ls-files prattern/` to confirm all package files are tracked.
**Files affected:** `.gitignore`, `.dockerignore`, `prattern/data/*.py`

---

### [L-011] Same anchoring rule applies to .dockerignore
**Date:** 2026-03-03
**Category:** Deployment
**Trigger:** Same as L-010 — `.dockerignore` had `data/` which excluded `prattern/data/` from the Docker build context
**Root cause:** Copied the `.gitignore` pattern without anchoring
**Rule:** `.dockerignore` patterns must follow the same anchoring rules as `.gitignore`. Any directory exclusion that should only match the repo root must use `/dir/` not `dir/`.
**Files affected:** `.dockerignore`

---

### [L-012] exchange_calendars is too heavy for containerized deploys
**Date:** 2026-03-03
**Category:** Deployment
**Trigger:** Railway container never became healthy — 60s+ import time or OOM from `exchange_calendars`
**Root cause:** `exchange_calendars` loads calendar data for every global exchange at import time. On small containers (512MB), this either OOMs or takes too long for the health check window.
**Rule:** Never use `exchange_calendars` in server-side code. Use a static holiday set (`_NYSE_HOLIDAYS` in `service.py`) for NYSE holiday detection — refresh each December for the next year. If accurate global exchange calendars are ever needed, use a lightweight alternative or an API.
**Files affected:** `prattern/features/theme_tracker/service.py`, `requirements-server.txt`

---

### [L-013] polars is GUI-only — never include in server requirements
**Date:** 2026-03-03
**Category:** Deployment
**Trigger:** Unnecessary memory usage in Railway container
**Root cause:** `polars` was in `requirements-server.txt` but is only used in `gui/pratten_app.py`. Heavy packages that aren't needed server-side waste memory and slow container startup.
**Rule:** `requirements-server.txt` must only contain packages actually imported by server code paths (`prattern/api/`, `prattern/features/`, `prattern/providers/`, `prattern/data/`). GUI-only packages (`customtkinter`, `polars`) belong only in `requirements.txt`.
**Files affected:** `requirements-server.txt`, `requirements.txt`

---

### [L-014] Always add a build-time import check and startup diagnostics for containerized deploys
**Date:** 2026-03-03
**Category:** Deployment
**Trigger:** Railway deploys failed silently — no logs, just "service unavailable" health check failures
**Root cause:** Import errors and crashes happened at runtime with no diagnostic output. Without `flush=True` on print statements, Python buffers stdout and logs never reach Railway.
**Rule:** The Dockerfile must include `RUN python -c "from prattern.api.server import app"` after `COPY . .` to catch import failures at build time. The server must start via `start.py` wrapper that prints diagnostics (Python version, PORT, import timing) with `flush=True` before launching uvicorn. Never use bare `uvicorn` as the start command in production — always use the wrapper.
**Files affected:** `Dockerfile`, `start.py`, `railway.toml`

---

## Recurring Patterns (Quick Reference)

| # | Rule | File(s) |
|---|------|---------|
| L-001 | All config in `Config` class, never hardcoded | `prattern/config.py` |
| L-002 | Read `base.py` Protocol before writing a provider | `prattern/providers/base.py` |
| L-003 | No emoji in backend — use `[OK]`/`[ERROR]` | All `prattern/`, `jobs/`, `cli/` |
| L-004 | `POLARS_SKIP_CPU_CHECK=1` before polars import | `gui/pratten_app.py` |
| L-005 | Keep `models.py` and `movers.ts` in sync | `prattern/core/models.py` + `web/src/types/movers.ts` |
| L-006 | Enforce per-ticker isolation in AI batch prompts | `prattern/providers/ai/gemini.py` |
| L-007 | Lazy-import heavy libs (yfinance, etc.) — never at module top | All provider/service files |
| L-008 | Stub darkdetect before importing customtkinter on Python 3.14 | `gui/pratten_app.py` |
| L-009 | Provider registry must lazy-import — never eagerly load all providers | `prattern/providers/__init__.py` |
| L-010 | Anchor `.gitignore` patterns with `/` — `data/` matches everywhere, `/data/` matches root only | `.gitignore` |
| L-011 | Same anchoring rule for `.dockerignore` | `.dockerignore` |
| L-012 | Never use `exchange_calendars` server-side — use static holiday set | `service.py`, `requirements-server.txt` |
| L-013 | `requirements-server.txt` = server-only deps. No GUI packages (polars, customtkinter) | `requirements-server.txt` |
| L-014 | Dockerfile must have build-time import check + `start.py` wrapper with `flush=True` | `Dockerfile`, `start.py`, `railway.toml` |

---

## Session Checklist (Read at Start of Every Session)

Before starting any work on this project:

1. **Skim the Recurring Patterns table above** — takes 30 seconds, prevents the most common mistakes
2. **Check if a `todo.md` already exists** in `tasks/` for the current task
3. **Confirm which providers are active** — check `prattern/config.py` defaults before touching provider code
4. **Remember the pipeline order** — scanner → analyzer → display. Changes to Phase 1 data shapes cascade to Phase 2 and 3.
