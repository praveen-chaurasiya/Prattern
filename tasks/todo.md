# Task: Admin Refresh Button + Startup Performance Fixes

**Date:** 2026-02-27
**Status:** In Progress
**Session:** Refresh button, lazy imports, darkdetect fix, provider registry

---

## What Was Done

### Admin Refresh Button (All Platforms)
- [x] Backend: `POST /scan/refresh` endpoint — runs scanner + analyzer as subprocesses, returns job_id for polling
- [x] GUI: "Refresh Scan" button in sidebar (always visible), chains scanner then analyzer
- [x] GUI: Live subprocess output streaming to Log tab (Popen + line-by-line)
- [x] GUI: Auto-switches to Log tab on refresh start
- [x] Web: `startScanRefresh()` + `pollJob()` API functions
- [x] Web: `useScanRefresh` hook with 2s polling, progress state, error handling
- [x] Web: StaleBanner refresh button (admin-only, shown when `VITE_API_KEY` set)
- [x] Web: Header passes refresh props through to StaleBanner
- [x] Web: Dashboard wires up `useScanRefresh`, reloads movers on complete
- [x] Web: `useMovers` now exposes `reload()` function

### Startup Performance Fixes
- [x] Stubbed `darkdetect` before `import customtkinter` — was hanging on Python 3.14
- [x] Lazy-imported `yfinance` in `theme_tracker/service.py` and `yfinance_provider.py`
- [x] Lazy-imported `pandas` in `prattern/data/prices.py`
- [x] Rewrote provider registry to lazy factories — providers only imported on first use
- [x] Result: startup from infinite hang to ~0.2s

### yfinance 429 Rate Limit Handling
- [x] Added exponential backoff (5s/10s/20s) on 429 errors in `yfinance_provider.py`
- [x] Added 2s pause between batches to avoid triggering rate limits
- [x] Added 3 retries per batch with error-specific handling
- [x] Subprocess timeout increased from 600s to 1200s (scan takes 5-10 min for 6200 tickers)

### Subprocess Output Streaming
- [x] `PYTHONUNBUFFERED=1` env var for real-time output in GUI
- [x] `-u` flag on API subprocess calls

---

## Open / Next Steps

- [ ] Migrate Gemini SDK: `google.generativeai` -> `google.genai` (deprecated, FutureWarning)
- [ ] Upgrade to paid Gemini API to avoid free tier 429 quota exhaustion
- [ ] Manual test: web dashboard refresh button in browser
- [ ] Manual test: full scan + analyze via GUI refresh button
- [ ] Consider reducing yfinance BATCH_SIZE to 100 if 429s persist
- [ ] `git commit` all changes from this session

---

## Files Modified
| File | Change |
|------|--------|
| `prattern/features/analyzer/routes.py` | Added `POST /scan/refresh`, bumped subprocess timeouts |
| `prattern/providers/__init__.py` | Rewritten — lazy factory pattern instead of eager import |
| `prattern/providers/prices/yfinance_provider.py` | Lazy yfinance import, backoff + retry on 429, batch pausing |
| `prattern/features/theme_tracker/service.py` | Lazy yfinance import |
| `prattern/data/prices.py` | Lazy pandas import |
| `gui/pratten_app.py` | darkdetect stub, sidebar refresh button, subprocess streaming, Log tab auto-switch |
| `web/src/features/analyzer/api.ts` | `startScanRefresh()`, `pollJob()`, `JobStatus` type |
| `web/src/features/analyzer/hooks/useScanRefresh.ts` | New — polling hook for refresh |
| `web/src/features/analyzer/hooks/useMovers.ts` | Added `reload()` |
| `web/src/features/analyzer/pages/Dashboard.tsx` | Wired up `useScanRefresh` |
| `web/src/shared/components/StaleBanner.tsx` | Admin refresh button + progress display |
| `web/src/shared/components/Header.tsx` | Passes refresh props to StaleBanner |

---

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Stub darkdetect instead of upgrading | darkdetect 0.8.0 + Python 3.14 incompatibility; we hardcode dark mode |
| Lazy provider registry | Scanner shouldn't pay cost of importing AI libs it doesn't use |
| PYTHONUNBUFFERED over flush=True everywhere | Single env var covers all print() calls in subprocess |
| 1200s timeout for scan | 31 batches x 200 tickers + backoff pauses can exceed 10 min |

---

## Lessons Captured
- L-007: Heavy imports at module level caused GUI hang
- L-008: darkdetect 0.8.0 hangs on Python 3.14
- L-009: Provider registry must lazy-import per provider
