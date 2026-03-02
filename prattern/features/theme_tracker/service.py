"""Theme tracker service — fetches prices and calculates performance per theme.

Price fetching strategy:
- One 6-month download from Yahoo Finance computes all periods (1w, 1m, 3m, ytd).
- "Today" uses last close vs previous close from the same daily data.
- During market hours, "today" uses a 5-day daily fetch for fresher data.
- All prices are regular market hours only (prepost=False).

Caching:
- Prices persisted to data/theme_prices_cache.json (survives server restarts).
- Market open (NYSE session hours): refresh every 5 minutes.
- Market closed (evenings, weekends, NYSE holidays): serve from disk, never fetch.
- First-ever load (no cache file): one Yahoo fetch to seed the cache.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

import exchange_calendars as ecals

from prattern.features.theme_tracker.db import load_theme_db, _get_ticker_strings

_ET = ZoneInfo("America/New_York")
_CACHE_TTL_OPEN = 300  # 5 minutes during market hours

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_CACHE_FILE = _CACHE_DIR / "theme_prices_cache.json"

# NYSE calendar for accurate holiday detection
_nyse = ecals.get_calendar("XNYS")

# In-memory mirror of disk cache (loaded once on first access)
_mem_cache: dict | None = None


def _is_market_open() -> bool:
    """Check if US stock market is currently in a regular trading session.

    Uses NYSE calendar — handles weekends AND all holidays
    (MLK, Presidents' Day, Good Friday, Memorial Day, July 4th,
    Labor Day, Thanksgiving, Christmas, etc.).
    """
    now_et = datetime.now(_ET)
    today_str = now_et.strftime("%Y-%m-%d")

    try:
        if not _nyse.is_session(today_str):
            return False
    except ValueError:
        # Date out of calendar range — assume closed
        return False

    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now_et <= market_close


# ---------------------------------------------------------------------------
# Disk cache read/write
# ---------------------------------------------------------------------------

def _load_disk_cache() -> dict:
    """Load price cache from disk. Returns empty structure if missing."""
    global _mem_cache
    if _mem_cache is not None:
        return _mem_cache

    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r") as f:
                _mem_cache = json.load(f)
                return _mem_cache
        except (json.JSONDecodeError, OSError):
            pass

    _mem_cache = {}
    return _mem_cache


def _save_disk_cache(cache: dict) -> None:
    """Persist price cache to disk."""
    global _mem_cache
    _mem_cache = cache
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(_CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main entry point — flat cache logic
# ---------------------------------------------------------------------------

def _fetch_theme_prices(tickers: List[str], period: str) -> dict:
    """Get price data for tickers at a given period.

    Simple flat logic:
    1. Has cache + market closed → return instantly
    2. Has cache + market open + fresh (<5 min) → return instantly
    3. Otherwise → fetch from Yahoo, save to disk, return
    """
    if not tickers:
        return {}

    cache = _load_disk_cache()
    now = time.time()
    market_open = _is_market_open()

    # Determine cache key and timestamp key
    if period == "today":
        cache_key, ts_key = "today", "today_ts"
    else:
        cache_key, ts_key = "daily", "daily_ts"

    cached_data = cache.get(cache_key, {})
    cached_ts = cache.get(ts_key, 0)

    # For non-intraday periods, cached_data is {period: {ticker: data}}
    # For "today", cached_data is {ticker: data}
    if period not in ("today",) and cached_data:
        period_data = cached_data.get(period, {})
    else:
        period_data = cached_data

    # Step 1: Has cache + market closed → return instantly
    if period_data and not market_open:
        return period_data

    # Step 2: Has cache + market open + fresh → return instantly
    if period_data and market_open and (now - cached_ts) < _CACHE_TTL_OPEN:
        return period_data

    # Step 3: Fetch from Yahoo, save, return
    if period == "today" and market_open:
        # During market hours, "today" gets its own fresh fetch
        results = _fetch_intraday_prices(tickers)
        cache["today"] = results
        cache["today_ts"] = now
        _save_disk_cache(cache)
        return results

    # Fetch all daily periods (covers 1w, 1m, 3m, ytd AND "today" when closed)
    all_periods = _fetch_all_daily_periods(tickers)
    cache["daily"] = all_periods
    cache["daily_ts"] = now

    # Also derive "today" from daily data (last close vs prev close)
    cache["today"] = all_periods.get("today_derived", {})
    cache["today_ts"] = now

    _save_disk_cache(cache)

    if period == "today":
        return cache["today"]
    return all_periods.get(period, {})


# ---------------------------------------------------------------------------
# Yahoo Finance fetchers (only called during market hours or first-ever load)
# ---------------------------------------------------------------------------

def _fetch_all_daily_periods(tickers: List[str]) -> dict[str, dict]:
    """Fetch 6 months of daily data and compute 1w, 1m, 3m, ytd from it.

    Also computes "today_derived" (last close vs previous close) so that
    the "today" tab works when market is closed without a separate fetch.

    Uses regular market hours only (prepost=False).
    """
    import yfinance as yf

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    periods = ("1w", "1m", "3m", "ytd")
    results: dict[str, dict] = {p: {} for p in periods}
    results["today_derived"] = {}

    try:
        df = yf.download(
            tickers, period="6mo", progress=False,
            threads=4, timeout=30, prepost=False,
        )
    except Exception:
        return results

    if df.empty:
        return results

    last_date = df.index[-1]
    jan1 = last_date.replace(month=1, day=1)
    cutoffs = {
        "1w": last_date - timedelta(days=7),
        "1m": last_date - timedelta(days=30),
        "3m": last_date - timedelta(days=90),
        "ytd": jan1,
    }

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                close = df["Close"].dropna()
            else:
                close = df["Close"][ticker].dropna()

            if len(close) < 2:
                continue

            current = float(close.iloc[-1])

            # Compute all standard periods
            for period in periods:
                period_data = close[close.index >= cutoffs[period]]
                if len(period_data) < 2:
                    continue

                previous = float(period_data.iloc[0])
                change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0.0

                results[period][ticker] = {
                    "ticker": ticker,
                    "current_price": round(current, 2),
                    "change_pct": round(change_pct, 2),
                }

            # Derive "today" = last close vs previous close
            previous_close = float(close.iloc[-2])
            day_change = ((current - previous_close) / previous_close) * 100 if previous_close != 0 else 0.0
            results["today_derived"][ticker] = {
                "ticker": ticker,
                "current_price": round(current, 2),
                "change_pct": round(day_change, 2),
            }
        except Exception:
            continue

    return results


def _fetch_intraday_prices(tickers: List[str]) -> dict:
    """Fetch yesterday close vs current price using regular hours only.

    Uses daily bars (not 1-minute) with prepost=False so we only see
    regular market session prices.
    """
    import yfinance as yf

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    results = {}
    try:
        df = yf.download(
            tickers, period="5d", progress=False,
            threads=4, timeout=20, prepost=False,
        )
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
            previous = float(close.iloc[-2])
            change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0.0

            results[ticker] = {
                "ticker": ticker,
                "current_price": round(current, 2),
                "change_pct": round(change_pct, 2),
            }
        except Exception:
            continue

    return results


# ---------------------------------------------------------------------------
# Theme assembly
# ---------------------------------------------------------------------------

def _build_stock_entry(ticker_obj: dict, prices: dict) -> dict | None:
    """Merge a structured ticker object with its price data."""
    symbol = ticker_obj["ticker"]
    if symbol not in prices:
        return None
    entry = dict(prices[symbol])
    entry["subtheme"] = ticker_obj.get("subtheme", "")
    entry["role"] = ticker_obj.get("role", "")
    return entry


def get_all_themes_performance(period: str = "1w") -> List[dict]:
    """Get performance data for all themes."""
    db = load_theme_db()
    themes = db.get("themes", {})

    # Collect all unique tickers across themes
    all_tickers = set()
    for theme_data in themes.values():
        all_tickers.update(_get_ticker_strings(theme_data.get("tickers", [])))

    # Fetch prices for all tickers at once
    prices = _fetch_theme_prices(list(all_tickers), period)

    results = []
    for theme_name, theme_data in themes.items():
        ticker_objs = theme_data.get("tickers", [])
        stocks = []
        for t_obj in ticker_objs:
            entry = _build_stock_entry(t_obj, prices)
            if entry:
                stocks.append(entry)

        avg_change = 0.0
        if stocks:
            avg_change = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2)

        results.append({
            "theme": theme_name,
            "description": theme_data.get("description", ""),
            "avg_change_pct": avg_change,
            "stock_count": len(ticker_objs),
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
    ticker_objs = theme_data.get("tickers", [])
    ticker_strings = _get_ticker_strings(ticker_objs)
    prices = _fetch_theme_prices(ticker_strings, period)

    stocks = []
    for t_obj in ticker_objs:
        entry = _build_stock_entry(t_obj, prices)
        if entry:
            stocks.append(entry)

    avg_change = 0.0
    if stocks:
        avg_change = round(sum(s["change_pct"] for s in stocks) / len(stocks), 2)

    return {
        "theme": theme_name,
        "description": theme_data.get("description", ""),
        "avg_change_pct": avg_change,
        "stock_count": len(ticker_objs),
        "stocks": sorted(stocks, key=lambda s: s["change_pct"], reverse=True),
    }
