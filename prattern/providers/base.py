"""Protocol definitions for all swappable providers."""

from typing import Dict, List, Optional, Protocol

import pandas as pd


class UniverseProvider(Protocol):
    """Fetches the ticker universe to scan."""

    def fetch_universe(self) -> List[str]: ...


class PriceProvider(Protocol):
    """Downloads price data for tickers."""

    def fetch_batch_prices(self, tickers: List[str], period: str = "10d") -> Dict[str, Dict[str, float]]:
        """Return {ticker: {"current": float, "5d_ago": float}} for tickers with >= 6 days of data."""
        ...

    def fetch_single(self, ticker: str, period: str = "10d") -> Optional[pd.DataFrame]:
        """Return OHLCV DataFrame for a single ticker, or None."""
        ...


class NewsProvider(Protocol):
    """Fetches news headlines for a ticker."""

    def fetch_headlines(self, ticker: str, max_headlines: int = 3) -> List[str]: ...


class AIClassifier(Protocol):
    """Classifies movers with category, theme, summary."""

    def classify_batch(self, movers_with_news: List[Dict]) -> List[Dict]:
        """Classify a list of movers (mutates and returns them)."""
        ...

    def classify_single(self, ticker: str, move_pct: float, current_price: float,
                        price_5d_ago: float, headlines: List[str]) -> Dict:
        """Classify a single mover, returning result dict."""
        ...
