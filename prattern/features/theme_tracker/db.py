"""Theme database CRUD — reads/writes data/theme_db.json."""

import json
import os
from datetime import datetime


_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "theme_db.json")
)


def load_theme_db() -> dict:
    """Load the theme database from disk."""
    if not os.path.exists(_DB_PATH):
        return {"themes": {}, "last_updated": None}
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_theme_db(db: dict) -> None:
    """Save the theme database to disk."""
    db["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with open(_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def add_ticker_to_theme(theme: str, ticker: str) -> dict:
    """Add a ticker to a theme. Returns updated theme entry."""
    db = load_theme_db()
    ticker = ticker.upper()

    if theme not in db["themes"]:
        raise KeyError(f"Theme '{theme}' not found")

    tickers = db["themes"][theme]["tickers"]
    if ticker not in tickers:
        tickers.append(ticker)
        save_theme_db(db)

    return db["themes"][theme]


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
    if ticker not in tickers:
        raise ValueError(f"Ticker '{ticker}' not in theme '{theme}'")

    tickers.remove(ticker)
    save_theme_db(db)

    return db["themes"][theme]
