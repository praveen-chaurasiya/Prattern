"""Ticker validation — fetch price data and check 5-day performance."""

from datetime import datetime
from typing import List, Dict

from prattern.config import Config
from prattern.data.prices import fetch_stock_data, calculate_5day_change


def validate_user_tickers(tickers: List[str]) -> List[Dict]:
    """
    Validate user-provided tickers and check if they are high-velocity movers.

    Args:
        tickers: List of ticker symbols provided by user

    Returns:
        List of validated movers with price data
    """
    print(f"\n[VALIDATE] Checking {len(tickers)} tickers for 5-day performance...\n")

    movers = []
    for idx, ticker in enumerate(tickers, 1):
        ticker = ticker.strip().upper()
        print(f"[{idx}/{len(tickers)}] Checking {ticker}...", end='\r')

        df = fetch_stock_data(ticker)
        if df is None:
            print(f"\n[!] {ticker}: Unable to fetch data")
            continue

        change_pct = calculate_5day_change(df)
        if change_pct is None:
            print(f"\n[!] {ticker}: Insufficient data")
            continue

        current_price = df['Close'].iloc[-1]
        price_5d_ago = df['Close'].iloc[-6]

        mover = {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'price_5d_ago': round(price_5d_ago, 2),
            'move_pct': change_pct,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        movers.append(mover)

        status = "[MOVER]" if change_pct >= Config.VELOCITY_THRESHOLD else "       "
        print(f"\n[{idx}/{len(tickers)}] {ticker}: {change_pct:+.2f}% {status}")

    print(f"\n[>] Validated {len(movers)}/{len(tickers)} tickers")
    print(f"[>] Found {sum(1 for m in movers if m['move_pct'] >= Config.VELOCITY_THRESHOLD)} movers (>={Config.VELOCITY_THRESHOLD}%)")

    return movers
