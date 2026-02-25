"""Theme tracker service — fetches prices and calculates performance per theme."""

import logging
from typing import List

import yfinance as yf

from prattern.features.theme_tracker.db import load_theme_db

# Map API period params to yfinance period strings
PERIOD_MAP = {
    "today": "2d",
    "1w": "7d",
    "1m": "1mo",
    "3m": "3mo",
    "ytd": "ytd",
}


def _fetch_theme_prices(tickers: List[str], period: str) -> dict:
    """Fetch current price and % change for each ticker over the given period."""
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    yf_period = PERIOD_MAP.get(period, "7d")

    results = {}
    if not tickers:
        return results

    try:
        df = yf.download(tickers, period=yf_period, progress=False, threads=4, timeout=20)
    except Exception:
        return results

    if df.empty:
        return results

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                close = df["Close"].dropna()
            else:
                close = df["Close"][ticker].dropna()

            if len(close) < 2:
                continue

            current = float(close.iloc[-1])
            previous = float(close.iloc[0])
            change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0.0

            results[ticker] = {
                "ticker": ticker,
                "current_price": round(current, 2),
                "change_pct": round(change_pct, 2),
            }
        except Exception:
            continue

    return results


def get_all_themes_performance(period: str = "1w") -> List[dict]:
    """Get performance data for all themes."""
    db = load_theme_db()
    themes = db.get("themes", {})

    # Collect all unique tickers across themes
    all_tickers = set()
    for theme_data in themes.values():
        all_tickers.update(theme_data.get("tickers", []))

    # Fetch prices for all tickers at once
    prices = _fetch_theme_prices(list(all_tickers), period)

    results = []
    for theme_name, theme_data in themes.items():
        tickers = theme_data.get("tickers", [])
        stocks = []
        for ticker in tickers:
            if ticker in prices:
                stocks.append(prices[ticker])

        avg_change = 0.0
        if stocks:
            avg_change = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2)

        results.append({
            "theme": theme_name,
            "description": theme_data.get("description", ""),
            "avg_change_pct": avg_change,
            "stock_count": len(tickers),
            "stocks": sorted(stocks, key=lambda s: s["change_pct"], reverse=True),
        })

    # Sort by avg change (hottest first)
    results.sort(key=lambda t: t["avg_change_pct"], reverse=True)
    return results


def get_theme_performance(theme_name: str, period: str = "1w") -> dict:
    """Get performance data for a single theme."""
    db = load_theme_db()
    themes = db.get("themes", {})

    if theme_name not in themes:
        raise KeyError(f"Theme '{theme_name}' not found")

    theme_data = themes[theme_name]
    tickers = theme_data.get("tickers", [])
    prices = _fetch_theme_prices(tickers, period)

    stocks = [prices[t] for t in tickers if t in prices]
    avg_change = 0.0
    if stocks:
        avg_change = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2)

    return {
        "theme": theme_name,
        "description": theme_data.get("description", ""),
        "avg_change_pct": avg_change,
        "stock_count": len(tickers),
        "stocks": sorted(stocks, key=lambda s: s["change_pct"], reverse=True),
    }
