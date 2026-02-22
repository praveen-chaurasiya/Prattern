"""NASDAQ screener universe provider."""

import json
import os
import requests
from datetime import datetime
from typing import List

from prattern.core.ticker_lists import UNIVERSE_STOCKS_ONLY

UNIVERSE_CACHE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "universe_cache.json")
)


class NasdaqUniverseProvider:
    """Fetch full US stock universe from NASDAQ's free screener API."""

    def fetch_universe(self) -> List[str]:
        """
        Returns all traded stocks on NYSE/NASDAQ/AMEX with price > $0.50.
        Caches result daily to avoid repeated API calls.
        Falls back to hardcoded list if the call fails.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Check cache first
        if os.path.exists(UNIVERSE_CACHE_PATH):
            try:
                with open(UNIVERSE_CACHE_PATH, "r") as f:
                    cache = json.load(f)
                if cache.get("date") == today:
                    tickers = cache["tickers"]
                    print(f"[UNIVERSE] Loading cached universe: {len(tickers)} tickers (cached {today})")
                    return tickers
            except (json.JSONDecodeError, KeyError):
                pass

        # Fetch from NASDAQ screener (free, no API key needed)
        url = "https://api.nasdaq.com/api/screener/stocks?tableType=traded&limit=10000&offset=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        print("[UNIVERSE] Fetching full US stock universe from NASDAQ...")

        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("data", {}).get("table", {}).get("rows", [])
        except Exception as e:
            print(f"[UNIVERSE] NASDAQ call failed: {e} -- falling back to hardcoded list")
            return UNIVERSE_STOCKS_ONLY

        if not rows:
            print("[UNIVERSE] NASDAQ returned no data -- falling back to hardcoded list")
            return UNIVERSE_STOCKS_ONLY

        tickers = []
        for row in rows:
            symbol = row.get("symbol", "").strip()
            lastsale = row.get("lastsale", "")

            try:
                price = float(lastsale.replace("$", "").replace(",", ""))
            except (ValueError, AttributeError):
                continue

            if price <= 0.50:
                continue

            if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
                continue

            if len(symbol) > 5 and "." not in symbol:
                continue

            tickers.append(symbol)

        if not tickers:
            print("[UNIVERSE] No valid tickers after filtering -- falling back to hardcoded list")
            return UNIVERSE_STOCKS_ONLY

        # Cache result
        os.makedirs(os.path.dirname(UNIVERSE_CACHE_PATH), exist_ok=True)
        with open(UNIVERSE_CACHE_PATH, "w") as f:
            json.dump({"date": today, "tickers": tickers}, f)

        print(f"[UNIVERSE] Loaded {len(tickers)} US stocks from NASDAQ (cached for {today})")
        return tickers
