"""Theme database CRUD — reads/writes data/theme_db.json."""

import json
import os
from datetime import datetime
from typing import List, Optional


_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "theme_db.json")
)


def _migrate_tickers(tickers: list) -> list:
    """Convert plain string tickers to structured objects if needed."""
    migrated = []
    for t in tickers:
        if isinstance(t, str):
            migrated.append({"ticker": t, "subtheme": "", "role": ""})
        else:
            migrated.append(t)
    return migrated


def _get_ticker_strings(tickers: list) -> List[str]:
    """Extract ticker symbol strings from structured ticker objects."""
    return [t["ticker"] for t in tickers]


def load_theme_db() -> dict:
    """Load the theme database from disk, auto-migrating flat tickers to structured."""
    if not os.path.exists(_DB_PATH):
        return {"themes": {}, "last_updated": None}
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Auto-migrate any plain string tickers to structured format
    migrated = False
    for theme_data in db.get("themes", {}).values():
        tickers = theme_data.get("tickers", [])
        if any(isinstance(t, str) for t in tickers):
            theme_data["tickers"] = _migrate_tickers(tickers)
            migrated = True

    if migrated:
        save_theme_db(db)

    return db


def save_theme_db(db: dict) -> None:
    """Save the theme database to disk."""
    db["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with open(_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def add_ticker_to_theme(theme: str, ticker: str, subtheme: str = "", role: str = "") -> dict:
    """Add a ticker to a theme. Returns updated theme entry."""
    db = load_theme_db()
    ticker = ticker.upper()

    if theme not in db["themes"]:
        raise KeyError(f"Theme '{theme}' not found")

    tickers = db["themes"][theme]["tickers"]
    existing = _get_ticker_strings(tickers)
    if ticker not in existing:
        tickers.append({"ticker": ticker, "subtheme": subtheme, "role": role})
        save_theme_db(db)

    return db["themes"][theme]


def update_ticker_in_theme(theme: str, ticker: str, subtheme: Optional[str] = None, role: Optional[str] = None) -> dict:
    """Update subtheme/role for an existing ticker in a theme. Returns updated theme entry."""
    db = load_theme_db()
    ticker = ticker.upper()

    if theme not in db["themes"]:
        raise KeyError(f"Theme '{theme}' not found")

    tickers = db["themes"][theme]["tickers"]
    for t in tickers:
        if t["ticker"] == ticker:
            if subtheme is not None:
                t["subtheme"] = subtheme
            if role is not None:
                t["role"] = role
            save_theme_db(db)
            return db["themes"][theme]

    raise ValueError(f"Ticker '{ticker}' not in theme '{theme}'")


def create_theme(name: str, description: str = "") -> dict:
    """Create a new empty theme. Returns the new theme entry."""
    name = name.strip()
    if not name:
        raise ValueError("Theme name cannot be empty")

    db = load_theme_db()
    if name in db["themes"]:
        raise ValueError(f"Theme '{name}' already exists")

    db["themes"][name] = {"description": description, "tickers": []}
    save_theme_db(db)
    return db["themes"][name]


def delete_theme(name: str) -> None:
    """Delete a theme. Only empty themes (no tickers) can be deleted."""
    db = load_theme_db()
    if name not in db["themes"]:
        raise KeyError(f"Theme '{name}' not found")

    tickers = db["themes"][name].get("tickers", [])
    if tickers:
        raise ValueError(
            f"Cannot delete theme '{name}' -- it still has {len(tickers)} ticker(s). "
            "Remove all tickers first."
        )

    del db["themes"][name]
    save_theme_db(db)


def remove_ticker_from_theme(theme: str, ticker: str) -> dict:
    """Remove a ticker from a theme. Returns updated theme entry."""
    db = load_theme_db()
    ticker = ticker.upper()

    if theme not in db["themes"]:
        raise KeyError(f"Theme '{theme}' not found")

    tickers = db["themes"][theme]["tickers"]
    for i, t in enumerate(tickers):
        if t["ticker"] == ticker:
            tickers.pop(i)
            save_theme_db(db)
            return db["themes"][theme]

    raise ValueError(f"Ticker '{ticker}' not in theme '{theme}'")
