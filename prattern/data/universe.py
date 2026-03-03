"""Universe fetching — delegates to the configured provider."""

from typing import List

from prattern.config import Config
from prattern.providers import get_provider


def fetch_fmp_universe() -> List[str]:
    """
    Fetch full US stock universe using the configured provider.
    Kept for backward compatibility — delegates to providers.
    """
    provider = get_provider("universe", Config.UNIVERSE_PROVIDER)
    return provider.fetch_universe()
