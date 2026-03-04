"""Polygon.io price provider — cloud-friendly alternative to yfinance.

Uses the Grouped Daily endpoint to fetch ALL US tickers in a single API call per date.
6 calls total for 5-day change calculation vs 31+ batches with yfinance.

Free tier: 5 API calls/min. Basic plan ($29/mo): unlimited.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from prattern.config import Config

_log = logging.getLogger(__name__)


def _get_trading_days(n: int = 8) -> List[str]:
    """Return the last `n` trading days (Mon-Fri) as YYYY-MM-DD strings, most recent first."""
    days = []
    d = datetime.now()
    while len(days) < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:  # Mon=0 .. Fri=4
            days.append(d.strftime("%Y-%m-%d"))
    return days


class PolygonPriceProvider:
    """Downloads price data via Polygon.io Grouped Daily endpoint.

    One API call returns close prices for ALL ~10,000 US tickers for a given date.
    We fetch ~8 trading days to reliably get 6+ data points per ticker.
    """

    BASE_URL = "https://api.polygon.io"
    RATE_LIMIT_PAUSE = 12.5  # seconds between calls (free tier: 5/min)

    def __init__(self):
        self.api_key = Config.POLYGON_API_KEY
        if not self.api_key:
            raise ValueError(
                "POLYGON_API_KEY is required. Get one free at https://polygon.io/dashboard/signup"
            )

    def _fetch_grouped_daily(self, date: str) -> Dict[str, float]:
        """Fetch close prices for all US stocks on a given date.

        Returns {ticker: close_price}.
        """
        import requests

        url = f"{self.BASE_URL}/v2/aggs/grouped/locale/us/market/stocks/{date}"
        params = {"adjusted": "true", "apiKey": self.api_key}

        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, timeout=30)

                if resp.status_code == 429:
                    wait = self.RATE_LIMIT_PAUSE * (2 ** attempt)
                    print(f"  [!] Rate limited, waiting {wait:.0f}s...", flush=True)
                    time.sleep(wait)
                    continue

                if resp.status_code == 403:
                    _log.error("Polygon API key invalid or plan insufficient")
                    return {}

                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "OK":
                    _log.warning("Polygon returned status: %s for date %s", data.get("status"), date)
                    return {}

                results = data.get("results", [])
                prices = {}
                for r in results:
                    ticker = r.get("T")
                    close = r.get("c")
                    if ticker and close is not None:
                        prices[ticker] = float(close)

                return prices

            except Exception as e:
                if attempt < 2:
                    _log.warning("Polygon fetch error for %s (attempt %d): %s", date, attempt + 1, e)
                    time.sleep(5)
                else:
                    _log.error("Polygon fetch failed for %s after 3 attempts: %s", date, e)
                    return {}

        return {}

    def fetch_batch_prices(self, tickers: List[str], period: str = "10d") -> Dict[str, Dict[str, float]]:
        """
        Fetch 5-day price change data for all tickers using Grouped Daily endpoint.

        Returns {ticker: {"current": float, "5d_ago": float}} for tickers with sufficient data.
        """
        # Get last 8 trading days (ensures we have at least 6 data points)
        trading_days = _get_trading_days(8)
        ticker_set = set(tickers) if tickers else None

        # Fetch close prices for each trading day
        # daily_prices[date] = {ticker: close}
        daily_prices: Dict[str, Dict[str, float]] = {}

        print(f"  Fetching {len(trading_days)} trading days from Polygon.io...", flush=True)

        for i, date in enumerate(trading_days):
            print(f"    Day {i + 1}/{len(trading_days)}: {date}...", end=" ", flush=True)
            prices = self._fetch_grouped_daily(date)
            print(f"{len(prices)} tickers", flush=True)

            if prices:
                daily_prices[date] = prices

            # Rate limit pause (skip after last call)
            if i < len(trading_days) - 1:
                time.sleep(self.RATE_LIMIT_PAUSE)

        if len(daily_prices) < 2:
            print("[!] Insufficient daily data from Polygon", flush=True)
            return {}

        # Sort dates oldest → newest
        sorted_dates = sorted(daily_prices.keys())

        # Build result: current = most recent day, 5d_ago = 6th most recent day
        result: Dict[str, Dict[str, float]] = {}

        # We need at least the most recent date and a date ~5 trading days back
        most_recent = sorted_dates[-1]
        # Find the date that's ~5 trading days before the most recent
        if len(sorted_dates) >= 6:
            five_days_ago = sorted_dates[-6]
        elif len(sorted_dates) >= 2:
            five_days_ago = sorted_dates[0]
        else:
            return {}

        current_prices = daily_prices[most_recent]
        old_prices = daily_prices[five_days_ago]

        for ticker in current_prices:
            # Filter to requested tickers if provided
            if ticker_set and ticker not in ticker_set:
                continue

            if ticker in old_prices:
                result[ticker] = {
                    "current": current_prices[ticker],
                    "5d_ago": old_prices[ticker],
                }

        print(f"  [OK] Price data for {len(result)} tickers ({most_recent} vs {five_days_ago})", flush=True)
        return result

    def fetch_single(self, ticker: str, period: str = "10d") -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a single ticker using Polygon aggregates."""
        import requests

        # Parse period to get date range
        days = int(period.replace("d", "")) if "d" in period else 10
        end = datetime.now()
        start = end - timedelta(days=days + 5)  # Extra buffer for weekends

        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
        params = {"adjusted": "true", "sort": "asc", "apiKey": self.api_key}

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                print(f"[!] No data for {ticker}", flush=True)
                return None

            rows = []
            for r in results:
                rows.append({
                    "Open": r.get("o"),
                    "High": r.get("h"),
                    "Low": r.get("l"),
                    "Close": r.get("c"),
                    "Volume": r.get("v"),
                })

            df = pd.DataFrame(rows)
            return df

        except Exception as e:
            print(f"[ERROR] Error fetching {ticker}: {e}", flush=True)
            return None
