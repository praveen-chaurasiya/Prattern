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

## Recurring Patterns (Quick Reference)

| # | Rule | File(s) |
|---|------|---------|
| L-001 | All config in `Config` class, never hardcoded | `prattern/config.py` |
| L-002 | Read `base.py` Protocol before writing a provider | `prattern/providers/base.py` |
| L-003 | No emoji in backend — use `[OK]`/`[ERROR]` | All `prattern/`, `jobs/`, `cli/` |
| L-004 | `POLARS_SKIP_CPU_CHECK=1` before polars import | `gui/pratten_app.py` |
| L-005 | Keep `models.py` and `movers.ts` in sync | `prattern/core/models.py` + `web/src/types/movers.ts` |
| L-006 | Enforce per-ticker isolation in AI batch prompts | `prattern/providers/ai/gemini.py` |

---

## Session Checklist (Read at Start of Every Session)

Before starting any work on this project:

1. **Skim the Recurring Patterns table above** — takes 30 seconds, prevents the most common mistakes
2. **Check if a `todo.md` already exists** in `tasks/` for the current task
3. **Confirm which providers are active** — check `prattern/config.py` defaults before touching provider code
4. **Remember the pipeline order** — scanner → analyzer → display. Changes to Phase 1 data shapes cascade to Phase 2 and 3.
