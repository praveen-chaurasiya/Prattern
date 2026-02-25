# Task: Theme Tracker Admin Management — All Platforms

**Date:** 2026-02-24
**Status:** ✅ Done
**Session:** Theme Admin Implementation

---

## Context
> The daily analyzer classifies stocks into themes via AI, producing `daily_analyzed.json`. The admin needs a way to review AI suggestions and manage the theme database (`data/theme_db.json`) from the GUI and web dashboard instead of raw API calls or editing JSON by hand.

**Affected files:**
- `prattern/features/theme_tracker/db.py` — new CRUD functions
- `prattern/features/theme_tracker/routes.py` — new endpoints
- `gui/pratten_app.py` — new Theme Tracker tab
- `web/src/features/theme-tracker/` — admin components, hooks, API calls
- `web/src/shared/types/themes.ts` — new suggestion types

---

## Acceptance Criteria
- [x] `create_theme()` and `delete_theme()` work in db.py
- [x] POST `/themes` and DELETE `/themes/{name}` endpoints respond correctly
- [x] Desktop GUI has Theme Tracker tab with period selector, theme cards, admin controls
- [x] Web dashboard has collapsible Admin Controls with create form + suggestions list
- [x] Backend imports pass: `python -c "from prattern.features.theme_tracker.routes import router"`
- [x] Web production build passes: `cd web && npm run build`

---

## Plan

### Phase 1 — Backend
- [x] Add `create_theme(name, description)` to db.py — validates no empty/duplicate names
- [x] Add `delete_theme(name)` to db.py — only deletes empty themes
- [x] Add `CreateThemeRequest` Pydantic model to routes.py
- [x] Add `POST /themes` endpoint (create, admin)
- [x] Add `DELETE /themes/{name}` endpoint (delete, admin)
- [x] Place new routes before `/{theme_name}` catch-all GET

### Phase 2 — Desktop GUI
- [x] Add "Theme Tracker" tab to CTkTabview
- [x] Period selector (today/1w/1m/3m/ytd) with background data refresh
- [x] Theme cards showing name, avg change %, description, stocks with Remove buttons
- [x] Delete button for empty themes
- [x] Collapsible admin section with Create Theme form
- [x] AI Suggestions panel grouped by theme with Add-to-theme dropdown
- [x] All network calls in background threads via `self.after()` pattern

### Phase 3 — Web Dashboard
- [x] Add `ThemeSuggestion` and `ThemeSuggestionsResponse` types to themes.ts
- [x] Add `fetchSuggestions()`, `createTheme()`, `deleteTheme()` to api.ts
- [x] Create `AdminSection.tsx` — collapsible wrapper
- [x] Create `CreateThemeForm.tsx` — name + description + submit
- [x] Create `SuggestionsList.tsx` — fetches and groups suggestions
- [x] Create `SuggestionRow.tsx` — ticker, move%, category, theme dropdown, Add button
- [x] Create `useThemeNames.ts` hook
- [x] Update `useThemeTracker.ts` — add `refreshKey` + `refresh()` function
- [x] Update `ThemeCard.tsx` — add Remove per stock, Delete Empty Theme button
- [x] Update `ThemeTracker.tsx` — add `<AdminSection>` with refresh callback

### Phase 4 — Verification
- [x] Backend import check passes
- [x] Web TypeScript build passes (0 errors, 71 modules)
- [ ] Manual testing in browser — in progress

---

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Inline stock rows in ThemeCard instead of reusing StockRow | Needed to add Remove button per row; StockRow had its own wrapper div causing layout issues |
| Admin section collapsible by default | Keeps read-only view clean for non-admin users |
| GUI calls db/service directly (no API) | Desktop app runs locally, no need for HTTP round-trip |

---

## Blockers
- ~~None~~

---

## Also Done This Session
- Created `PratternDailyScan` Windows Task Scheduler job (Mon-Fri 4:30 PM, StartWhenAvailable=true)
- Ran fresh scan: 116 movers found, 18 Gemini + 98 Claude fallback analyzed
- Read updated CLAUDE.md with new workflow orchestration rules

---

## Review
**Completed:** 2026-02-24
**Summary of changes:**
- Backend: `create_theme()`, `delete_theme()` in db.py; POST/DELETE endpoints in routes.py
- GUI: Full Theme Tracker tab with read-only view + collapsible admin controls
- Web: 6 new files (AdminSection, CreateThemeForm, SuggestionsList, SuggestionRow, useThemeNames) + 4 modified files
- Infra: Task Scheduler job with run-missed enabled

**Did verification pass?** Yes — backend imports OK, web build OK (71 modules, 0 errors)
**Lessons captured in `lessons.md`?** No corrections received yet this session
