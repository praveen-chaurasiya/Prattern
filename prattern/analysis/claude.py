"""Claude AI fallback classification — delegates to the configured provider."""

from typing import Dict, List

from prattern.config import Config
from prattern.providers import get_provider


def categorize_with_claude(ticker: str, move_pct: float, current_price: float,
                           price_5d_ago: float, headlines: List[str]) -> Dict[str, str]:
    """Classify a single mover using the fallback AI provider.
    Kept for backward compatibility — delegates to providers.
    """
    provider = get_provider("ai", Config.AI_FALLBACK_PROVIDER)
    return provider.classify_single(ticker, move_pct, current_price, price_5d_ago, headlines)
