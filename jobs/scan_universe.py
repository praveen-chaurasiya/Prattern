"""
Universe Scanner -- Background Job
Run this daily after market close (~4:30 PM ET) to pre-compute movers.
"""

import json
import os
import sys

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from prattern.config import Config
from prattern.providers import get_provider

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DAILY_MOVERS_PATH = os.path.join(DATA_DIR, "daily_movers.json")


def scan_full_universe(threshold: float = 20.0):
    """Scan the full US stock universe for 5-day high-velocity movers."""
    start_time = datetime.now()
    print("=" * 70)
    print("UNIVERSE SCANNER -- Background Job")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Threshold: >= {threshold}% gain in 5 trading days")
    print("=" * 70)

    universe = get_provider("universe", Config.UNIVERSE_PROVIDER)
    prices = get_provider("prices", Config.PRICE_PROVIDER)

    tickers = universe.fetch_universe()

    # Deduplicate while preserving order
    seen = set()
    unique_tickers = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    tickers = unique_tickers
    total = len(tickers)

    print(f"\n[1/3] Universe: {total} tickers")
    print(f"[2/3] Downloading price data...")

    all_close_data = prices.fetch_batch_prices(tickers, period="10d")

    print(f"\n  Price data fetched for {len(all_close_data)}/{total} tickers")
    print(f"[3/3] Calculating 5-day movers (>= {threshold}%)...")

    movers = []
    for ticker, price_data in all_close_data.items():
        current = price_data["current"]
        ago = price_data["5d_ago"]

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

    data_dir = os.path.normpath(DATA_DIR)
    movers_path = os.path.normpath(DAILY_MOVERS_PATH)
    os.makedirs(data_dir, exist_ok=True)

    result = {
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_time": datetime.now().strftime("%H:%M:%S"),
        "universe_size": total,
        "tickers_with_data": len(all_close_data),
        "threshold": threshold,
        "movers_found": len(movers),
        "movers": movers,
    }

    with open(movers_path, "w") as f:
        json.dump(result, f, indent=2)

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n{'=' * 70}")
    print(f"SCAN COMPLETE")
    print(f"  Movers found: {len(movers)}")
    print(f"  Saved to: {movers_path}")
    print(f"  Time: {elapsed:.0f}s")
    print(f"{'=' * 70}")

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
