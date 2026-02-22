"""News fetching — delegates to the configured provider."""

from typing import List

from prattern.config import Config
from prattern.providers import get_provider


def fetch_finviz_news(ticker: str, max_headlines: int = 3) -> List[str]:
    """Fetch news headlines using the configured provider.
    Kept for backward compatibility — delegates to providers.
    """
    provider = get_provider("news", Config.NEWS_PROVIDER)
    return provider.fetch_headlines(ticker, max_headlines)
