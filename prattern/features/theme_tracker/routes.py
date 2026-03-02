"""Theme tracker feature routes — theme performance, CRUD, and suggestions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from prattern.features.theme_tracker.db import (
    load_theme_db,
    add_ticker_to_theme,
    remove_ticker_from_theme,
    update_ticker_in_theme,
    create_theme,
    delete_theme,
    _get_ticker_strings,
)
from prattern.features.theme_tracker.service import (
    get_all_themes_performance,
    get_theme_performance,
)
from prattern.data.precomputed import load_precomputed_analysis

router = APIRouter(prefix="/themes", tags=["themes"])


# ---------------------------------------------------------------------------
# Public (read-only)
# ---------------------------------------------------------------------------

@router.get("/tracker")
def theme_tracker(period: str = "1w"):
    """Get all themes with performance data for the given period."""
    if period not in ("today", "1w", "1m", "3m", "ytd"):
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}. Use: today, 1w, 1m, 3m, ytd")

    themes = get_all_themes_performance(period)
    return {"period": period, "themes": themes}


# ---------------------------------------------------------------------------
# Admin (requires API key) — must be before /{theme_name} catch-all
# ---------------------------------------------------------------------------

@router.get("/suggestions")
def theme_suggestions():
    """Suggest tickers from recent analyzer classifications (admin)."""
    analysis = load_precomputed_analysis()
    if not analysis:
        return {"suggestions": []}

    db = load_theme_db()
    existing_tickers = set()
    for theme_data in db.get("themes", {}).values():
        existing_tickers.update(_get_ticker_strings(theme_data.get("tickers", [])))

    suggestions = []
    for mover in analysis.get("movers", []):
        ticker = mover.get("ticker", "")
        if ticker and ticker not in existing_tickers:
            suggestions.append({
                "ticker": ticker,
                "primary_theme": mover.get("primary_theme", ""),
                "sub_niche": mover.get("sub_niche", ""),
                "category": mover.get("category", ""),
                "move_pct": mover.get("move_pct", 0),
            })

    return {"suggestions": suggestions}


class CreateThemeRequest(BaseModel):
    name: str
    description: str = ""


@router.post("")
def create_theme_endpoint(body: CreateThemeRequest):
    """Create a new empty theme (admin)."""
    try:
        theme = create_theme(body.name, body.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"theme": body.name, **theme}


@router.delete("/{theme_name}")
def delete_theme_endpoint(theme_name: str):
    """Delete an empty theme (admin)."""
    try:
        delete_theme(theme_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"deleted": theme_name}


# ---------------------------------------------------------------------------
# Public (read-only) — single theme detail
# ---------------------------------------------------------------------------

@router.get("/{theme_name}")
def theme_detail(theme_name: str, period: str = "1w"):
    """Get performance data for a single theme."""
    if period not in ("today", "1w", "1m", "3m", "ytd"):
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}. Use: today, 1w, 1m, 3m, ytd")

    try:
        theme = get_theme_performance(theme_name, period)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"period": period, **theme}


# ---------------------------------------------------------------------------
# Admin CRUD
# ---------------------------------------------------------------------------

class AddTickerRequest(BaseModel):
    ticker: str
    subtheme: str = ""
    role: str = ""


@router.post("/{theme_name}/tickers")
def add_ticker(theme_name: str, body: AddTickerRequest):
    """Add a ticker to a theme (admin)."""
    try:
        theme = add_ticker_to_theme(theme_name, body.ticker, body.subtheme, body.role)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"theme": theme_name, **theme}


class UpdateTickerRequest(BaseModel):
    subtheme: Optional[str] = None
    role: Optional[str] = None


@router.put("/{theme_name}/tickers/{ticker}")
def update_ticker(theme_name: str, ticker: str, body: UpdateTickerRequest):
    """Update subtheme/role for an existing ticker in a theme (admin)."""
    try:
        theme = update_ticker_in_theme(theme_name, ticker, body.subtheme, body.role)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"theme": theme_name, **theme}


@router.delete("/{theme_name}/tickers/{ticker}")
def remove_ticker(theme_name: str, ticker: str):
    """Remove a ticker from a theme (admin)."""
    try:
        theme = remove_ticker_from_theme(theme_name, ticker)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"theme": theme_name, **theme}
