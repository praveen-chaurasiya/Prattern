"""Gemini AI batch analysis — delegates to the configured provider."""

from typing import Dict, List

from prattern.config import Config
from prattern.providers import get_provider


def analyze_batch_with_gemini(movers_with_news: List[Dict]) -> List[Dict]:
    """Batch classify movers using the primary AI provider.
    Kept for backward compatibility — delegates to providers.
    """
    provider = get_provider("ai", Config.AI_PRIMARY_PROVIDER)
    return provider.classify_batch(movers_with_news)
