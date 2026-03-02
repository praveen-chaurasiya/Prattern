"""Yahoo Finance price provider."""

import logging
import time
from typing import Dict, List, Optional

import pandas as pd


class YFinancePriceProvider:
    """Downloads price data via yfinance."""

    BATCH_SIZE = 200
    MAX_RETRIES = 3
    BASE_DELAY = 5  # seconds — initial wait after 429
    BATCH_PAUSE = 2  # seconds — pause between successful batches to avoid 429

    def fetch_batch_prices(self, tickers: List[str], period: str = "10d") -> Dict[str, Dict[str, float]]:
        """
        Download close prices for all tickers in batches.
        Returns {ticker: {"current": float, "5d_ago": float}} for tickers with >= 6 days of data.
        """
        import yfinance as yf

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
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} tickers)...", end=" ", flush=True)

            df_batch = self._download_with_retry(yf, batch, period)

            if df_batch is None or df_batch.empty:
                print("empty/failed", flush=True)
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

            print(f"{fetched} OK", flush=True)

            # Pause between batches to avoid triggering rate limits
            if i + self.BATCH_SIZE < total:
                time.sleep(self.BATCH_PAUSE)

        return all_close_data

    def _download_with_retry(self, yf, batch: List[str], period: str):
        """Download with exponential backoff on 429/errors."""
        for attempt in range(self.MAX_RETRIES):
            try:
                df = yf.download(
                    batch, period=period, progress=False,
                    threads=4, timeout=30
                )
                return df
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate" in err_str or "too many" in err_str

                if is_rate_limit and attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    print(f"429 rate limited, waiting {delay}s (retry {attempt + 1}/{self.MAX_RETRIES})...", end=" ", flush=True)
                    time.sleep(delay)
                elif attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY
                    print(f"error: {e}, retrying in {delay}s...", end=" ", flush=True)
                    time.sleep(delay)
                else:
                    print(f"FAILED after {self.MAX_RETRIES} attempts: {e}", flush=True)
                    return None
        return None

    def fetch_single(self, ticker: str, period: str = "10d") -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a single ticker."""
        import yfinance as yf

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
