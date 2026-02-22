"""Provider registry — swap any external API with a single config change."""

from typing import Any, Dict

# Registry: {provider_type: {name: instance}}
_registry: Dict[str, Dict[str, Any]] = {}


def register(provider_type: str, name: str, instance: Any) -> None:
    """Register a provider instance under a type and name."""
    if provider_type not in _registry:
        _registry[provider_type] = {}
    _registry[provider_type][name] = instance


def get_provider(provider_type: str, name: str) -> Any:
    """Get a registered provider by type and name.

    Auto-registers built-in providers on first call.
    """
    if not _registry:
        _auto_register()

    providers = _registry.get(provider_type)
    if not providers:
        raise ValueError(f"No providers registered for type '{provider_type}'")

    instance = providers.get(name)
    if not instance:
        available = ", ".join(providers.keys())
        raise ValueError(f"Unknown {provider_type} provider '{name}'. Available: {available}")

    return instance


def _auto_register() -> None:
    """Register all built-in providers."""
    from prattern.config import Config

    # Universe
    from prattern.providers.universe.nasdaq import NasdaqUniverseProvider
    register("universe", "nasdaq", NasdaqUniverseProvider())

    # Prices
    from prattern.providers.prices.yfinance_provider import YFinancePriceProvider
    register("prices", "yfinance", YFinancePriceProvider())

    # News
    from prattern.providers.news.finviz import FinvizNewsProvider
    register("news", "finviz", FinvizNewsProvider())

    # AI classifiers
    from prattern.providers.ai.gemini import GeminiClassifier
    register("ai", "gemini", GeminiClassifier())

    from prattern.providers.ai.claude import ClaudeClassifier
    register("ai", "claude", ClaudeClassifier())
