# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys (required: ANTHROPIC_API_KEY, GEMINI_API_KEY)
cp .env.example .env

# Run daily background scanner + analyzer (after market close ~4:30 PM ET)
python jobs/scan_universe.py            # Default 20% threshold
python jobs/scan_universe.py 15.0       # Custom threshold
python jobs/analyze_movers.py           # Pre-compute AI analysis

# Automated daily pipeline (Task Scheduler)
run_scan.bat                            # Runs scanner then analyzer

# GUI app
python gui/pratten_app.py

# CLI
python cli/main.py                      # Interactive mode selection
python cli/main.py 1                    # Auto-scan (pre-computed movers)
python cli/main.py 2 "NVDA,TSLA,AAPL"  # Manual tickers
python cli/main.py 2 tickers.txt       # Tickers from file

# API server
uvicorn prattern.api.server:app --port 8000

# Web dashboard (React + Vite)
cd web && npm install                  # First time setup
cd web && npm run dev                  # Dev server at http://localhost:5173
cd web && npm run build                # Production build to web/dist/

# Root-level redirects still work (backward compat)
python main.py 1
python pratten_app.py
python scan_universe.py
python analyze_movers.py
```

No test framework is configured.

## Project Structure

```
prattern/                    # Main package
  config.py                  # Config class (API keys, models, thresholds, provider selection)
  providers/                 # Provider abstraction layer (swap any API via config)
    __init__.py              # Registry + get_provider() factory
    base.py                  # 4 Protocol definitions (UniverseProvider, PriceProvider, NewsProvider, AIClassifier)
    universe/
      nasdaq.py              # NasdaqUniverseProvider — NASDAQ screener API
    prices/
      yfinance_provider.py   # YFinancePriceProvider — yfinance batch downloads
    news/
      finviz.py              # FinvizNewsProvider — Finviz headline scraping
    ai/
      gemini.py              # GeminiClassifier — primary AI (batch classification)
      claude.py              # ClaudeClassifier — fallback AI (single classification)
  core/
    models.py                # Dataclasses: Mover, AnalyzedMover, ScanResult
    ticker_lists.py          # Hardcoded fallback ticker lists
    file_io.py               # read_tickers_from_file(), save_results()
    validation.py            # validate_user_tickers()
  data/
    universe.py              # Thin wrapper — delegates to universe provider
    prices.py                # Thin wrapper — delegates to price provider
    precomputed.py           # load_precomputed_movers(), load_precomputed_analysis()
  analysis/
    news.py                  # Thin wrapper — delegates to news provider
    gemini.py                # Thin wrapper — delegates to primary AI provider
    claude.py                # Thin wrapper — delegates to fallback AI provider
    orchestrator.py          # analyze_all_movers() — uses providers via get_provider()
  api/
    server.py                # FastAPI: SSE streaming + polling endpoints

cli/main.py                  # CLI entry point
gui/pratten_app.py           # CustomTkinter GUI entry point
jobs/scan_universe.py        # Background scanner job (uses providers)
jobs/analyze_movers.py       # Background analyzer job
run_scan.bat                 # Task Scheduler batch file

web/                         # React web dashboard (Vite + TypeScript + Tailwind)
  src/
    types/movers.ts          # TS interfaces matching backend JSON
    api/                     # client.ts, movers.ts, sse.ts — fetch wrappers
    hooks/                   # useMovers, useScanStatus, useAnalysisSSE
    components/              # layout/, movers/, breakdown/, analysis/, common/
    pages/Dashboard.tsx      # Main page composing all components
    utils/                   # format.ts, aggregate.ts

data/                        # Runtime data (gitignored)
  daily_movers.json          # Raw movers from scanner
  daily_analyzed.json        # AI-analyzed movers
  universe_cache.json        # Cached ticker universe
themes/                      # Saved results (gitignored)
```

## Architecture

**Three-phase pipeline:** scanner → analyzer → app loads instantly.

### Provider Abstraction Layer (`prattern/providers/`)
All 5 external APIs are behind swappable provider interfaces. To swap any provider:
1. Create a new class implementing the Protocol from `providers/base.py`
2. Register it in `providers/__init__.py` `_auto_register()`
3. Set the env var (e.g., `PRICE_PROVIDER=polygon`) or change `Config` default

Provider config variables (in `prattern/config.py`):
- `UNIVERSE_PROVIDER` (default: `nasdaq`)
- `PRICE_PROVIDER` (default: `yfinance`)
- `NEWS_PROVIDER` (default: `finviz`)
- `AI_PRIMARY_PROVIDER` (default: `gemini`)
- `AI_FALLBACK_PROVIDER` (default: `claude`)

### Phase 1: Data Collection (`jobs/scan_universe.py`)
- Fetches ~6,200 tickers via configured universe provider, cached daily in `data/universe_cache.json`
- Downloads prices via configured price provider in batches of 200, calculates 5-day % change
- Writes movers (>=20% gain) to `data/daily_movers.json`

### Phase 2: AI Analysis (`jobs/analyze_movers.py`)
- Loads `daily_movers.json`, runs `analyze_all_movers()` with progress callback
- Saves analyzed results to `data/daily_analyzed.json`
- Primary AI (default: Gemini, batches of 7) + fallback AI (default: Claude, for Unknown/Failed/Other)

### Phase 3: Display (GUI / CLI / API / Web Dashboard)
- Loads pre-analyzed data from `daily_analyzed.json` (instant, no AI calls)
- Falls back to live AI analysis if pre-analyzed data is missing
- API provides SSE streaming + polling patterns for web/mobile clients
- Web dashboard (`web/`) consumes API via fetch; SSE for live analysis via POST stream reader

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/movers` | Raw movers (instant) |
| GET | `/analysis/latest` | Pre-analyzed movers (instant) |
| GET | `/scan/status` | Scan/analysis metadata + staleness |
| POST | `/movers/analyze` | SSE streaming analysis (web) |
| POST | `/jobs/analyze` | Start background job (mobile) |
| GET | `/jobs/{job_id}` | Poll job status (mobile) |

## Key Patterns

- **Rate limiting:** Gemini free tier ~5 RPM. 15-second pause between batches, exponential backoff (3 retries), 3x wait multiplier on 429 errors.
- **on_progress callback:** `analyze_all_movers(movers, on_progress=fn)` reports `{stage, current, total, detail}` events. Used by CLI, API SSE, and polling endpoints.
- **GUI threading:** Analysis runs in `threading.Thread(daemon=True)`. `self.log()` does text insertion + `self.update()` for real-time display.
- **Polars CPU fix:** `os.environ["POLARS_SKIP_CPU_CHECK"] = "1"` must appear before `import polars` in gui/pratten_app.py.
- **Allowed enums:** Categories validated against `Config.CLAUDE_CATEGORIES`, themes against `Config.GEMINI_THEMES`. Both lists live in prattern/config.py.
- **sys.path in entry points:** `cli/`, `gui/`, `jobs/` scripts insert project root into `sys.path` so `prattern.*` imports work.
- `data/` and `themes/` directories are gitignored (regenerated at runtime).

### Stale Documentation
- `README.md` references old flat file structure and outdated model names. Update README if modifying these areas.

## Compact Instructions

When compacting, focus on code changes, config updates, and AI classification results. Discard verbose tool output and intermediate search results.

## Rules & Guardrails

- **Precision:** Use `decimal.Decimal` for all stock price calculations in `prattern/data/prices.py` to avoid floating-point rounding errors.
- **Model roles:** `Config.AI_PRIMARY_PROVIDER` (default: gemini) is the primary classification engine. `Config.AI_FALLBACK_PROVIDER` (default: claude) fires when primary returns Unknown/Failed/Other. Swap via env vars or config.
- **GUI requirements:** `gui/pratten_app.py` uses `customtkinter` and requires `os.environ["POLARS_SKIP_CPU_CHECK"] = "1"` set before importing polars to prevent crashes on older hardware.
- **Encoding:** Avoid emojis in backend code (Windows charmap crashes). Use `[OK]`/`[ERROR]` text prefixes instead.
