"""Price fetching — delegates to the configured provider."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import pandas as pd

from prattern.config import Config
from prattern.data.universe import fetch_fmp_universe
from prattern.providers import get_provider


def fetch_stock_data(ticker: str, period: str = "10d") -> "Optional[pd.DataFrame]":
    """Fetch OHLCV data for a single ticker."""
    provider = get_provider("prices", Config.PRICE_PROVIDER)
    return provider.fetch_single(ticker, period)


def calculate_5day_change(df: "pd.DataFrame") -> Optional[float]:
    """Calculate percentage change from 5 trading days ago."""
    if len(df) < 6:
        return None

    current_price = df['Close'].iloc[-1]
    price_5_days_ago = df['Close'].iloc[-6]

    if price_5_days_ago == 0:
        return None

    change_pct = ((current_price - price_5_days_ago) / price_5_days_ago) * 100
    return round(change_pct, 2)


def get_high_velocity_movers(tickers: List[str] = None, threshold: float = 20.0) -> List[Dict]:
    """
    Identify stocks with >= threshold% gain in 5 trading days.
    Uses the configured price provider for batch downloads.
    """
    if tickers is None:
        tickers = fetch_fmp_universe()

    total = len(tickers)
    print(f"[SCAN] Scanning {total} tickers for high-velocity movers (>={threshold}% in 5 days)...")

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    provider = get_provider("prices", Config.PRICE_PROVIDER)
    all_close_data = provider.fetch_batch_prices(tickers, period="10d")

    if not all_close_data:
        print("[!] No data returned from downloads")
        return []

    movers = []

    for ticker, prices in all_close_data.items():
        current_price = prices["current"]
        price_5d_ago = prices["5d_ago"]

        if price_5d_ago <= 0:
            continue

        change_pct = round(((current_price - price_5d_ago) / price_5d_ago) * 100, 2)

        if change_pct >= threshold:
            mover = {
                'ticker': ticker,
                'current_price': round(float(current_price), 2),
                'price_5d_ago': round(float(price_5d_ago), 2),
                'move_pct': change_pct,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            movers.append(mover)
            print(f"   [+] {ticker}: +{change_pct}% (${price_5d_ago:.2f} -> ${current_price:.2f})")

    movers.sort(key=lambda x: x['move_pct'], reverse=True)

    print(f"\n[>] Found {len(movers)} high-velocity movers out of {total} scanned!")
    return movers
