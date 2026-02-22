"""Yahoo Finance price provider."""

import logging
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf


class YFinancePriceProvider:
    """Downloads price data via yfinance."""

    BATCH_SIZE = 200

    def fetch_batch_prices(self, tickers: List[str], period: str = "10d") -> Dict[str, Dict[str, float]]:
        """
        Download close prices for all tickers in batches.
        Returns {ticker: {"current": float, "5d_ago": float}} for tickers with >= 6 days of data.
        """
        logging.getLogger("yfinance").setLevel(logging.CRITICAL)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for t in tickers:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        tickers = unique
        total = len(tickers)

        all_close_data: Dict[str, Dict[str, float]] = {}

        for i in range(0, total, self.BATCH_SIZE):
            batch = tickers[i:i + self.BATCH_SIZE]
            batch_num = i // self.BATCH_SIZE + 1
            total_batches = (total + self.BATCH_SIZE - 1) // self.BATCH_SIZE
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} tickers)...", end=" ")

            try:
                df_batch = yf.download(
                    batch, period=period, progress=False,
                    threads=4, timeout=20
                )
            except Exception as e:
                print(f"FAILED: {e}")
                continue

            if df_batch.empty:
                print("empty")
                continue

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

        return all_close_data

    def fetch_single(self, ticker: str, period: str = "10d") -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a single ticker."""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if df.empty:
                print(f"[!]  No data for {ticker}")
                return None

            return df
        except Exception as e:
            print(f"[ERROR] Error fetching {ticker}: {str(e)}")
            return None
