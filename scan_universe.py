"""
Universe Scanner — Background Job
Run this daily after market close (~4:30 PM ET) to pre-compute movers.
Results are saved to data/daily_movers.json for instant loading by the app.

Usage:
    python scan_universe.py

Schedule with Windows Task Scheduler or cron to run daily.
"""

import json
import logging
import os
import sys
from datetime import datetime

import pandas as pd
import yfinance as yf

from data_fetcher import fetch_fmp_universe, UNIVERSE_STOCKS_ONLY
from config import Config

# Suppress yfinance timeout spam
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DAILY_MOVERS_PATH = os.path.join(DATA_DIR, "daily_movers.json")


def scan_full_universe(threshold: float = 20.0):
    """
    Scan the full US stock universe for 5-day high-velocity movers.
    Downloads price data in batches, calculates rolling 5-day % change,
    and saves results to data/daily_movers.json.
    """
    start_time = datetime.now()
    print("=" * 70)
    print("UNIVERSE SCANNER — Background Job")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Threshold: >= {threshold}% gain in 5 trading days")
    print("=" * 70)

    # Step 1: Get universe
    tickers = fetch_fmp_universe()

    # Deduplicate
    seen = set()
    unique_tickers = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    tickers = unique_tickers
    total = len(tickers)

    print(f"\n[1/3] Universe: {total} tickers")

    # Step 2: Download price data in batches
    print(f"[2/3] Downloading price data...")

    BATCH_SIZE = 200
    all_close_data = {}

    for i in range(0, total, BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} tickers)...", end=" ")

        try:
            df_batch = yf.download(
                batch, period="10d", progress=False,
                threads=4, timeout=20
            )
        except Exception as e:
            print(f"FAILED: {e}")
            continue

        if df_batch.empty:
            print("empty")
            continue

        # Extract close prices for each ticker in batch
        fetched = 0
        for ticker in batch:
            try:
                if len(batch) == 1:
                    close = df_batch["Close"].dropna()
                else:
                    close = df_batch["Close"][ticker].dropna()

                if len(close) >= 6:
                    all_close_data[ticker] = {
                        "current": float(close.iloc[-1]),
                        "5d_ago": float(close.iloc[-6]),
                    }
                    fetched += 1
            except Exception:
                continue

        print(f"{fetched} OK")

    print(f"\n  Price data fetched for {len(all_close_data)}/{total} tickers")

    # Step 3: Calculate movers
    print(f"[3/3] Calculating 5-day movers (>= {threshold}%)...")

    movers = []
    for ticker, prices in all_close_data.items():
        current = prices["current"]
        ago = prices["5d_ago"]

        if ago <= 0:
            continue

        change_pct = round(((current - ago) / ago) * 100, 2)

        if change_pct >= threshold:
            movers.append({
                "ticker": ticker,
                "current_price": round(current, 2),
                "price_5d_ago": round(ago, 2),
                "move_pct": change_pct,
            })

    movers.sort(key=lambda x: x["move_pct"], reverse=True)

    # Save results
    os.makedirs(DATA_DIR, exist_ok=True)

    result = {
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_time": datetime.now().strftime("%H:%M:%S"),
        "universe_size": total,
        "tickers_with_data": len(all_close_data),
        "threshold": threshold,
        "movers_found": len(movers),
        "movers": movers,
    }

    with open(DAILY_MOVERS_PATH, "w") as f:
        json.dump(result, f, indent=2)

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n{'=' * 70}")
    print(f"SCAN COMPLETE")
    print(f"  Movers found: {len(movers)}")
    print(f"  Saved to: {DAILY_MOVERS_PATH}")
    print(f"  Time: {elapsed:.0f}s")
    print(f"{'=' * 70}")

    # Print top movers
    if movers:
        print(f"\nTop movers:")
        for m in movers[:20]:
            print(f"  {m['ticker']:>6}: +{m['move_pct']}%  (${m['price_5d_ago']} -> ${m['current_price']})")

    return movers


if __name__ == "__main__":
    threshold = Config.VELOCITY_THRESHOLD
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
        except ValueError:
            pass

    scan_full_universe(threshold=threshold)
