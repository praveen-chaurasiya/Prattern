"""Provider registry — swap any external API with a single config change."""

from typing import Any, Callable, Dict, Tuple

# Registry: {provider_type: {name: factory_fn_or_instance}}
_registry: Dict[str, Dict[str, Any]] = {}
_factories: Dict[Tuple[str, str], Callable] = {}
_initialized = False


def register(provider_type: str, name: str, instance: Any) -> None:
    """Register a provider instance under a type and name."""
    if provider_type not in _registry:
        _registry[provider_type] = {}
    _registry[provider_type][name] = instance


def get_provider(provider_type: str, name: str) -> Any:
    """Get a registered provider by type and name.

    Providers are registered lazily — only imported when first requested.
    """
    if not _initialized:
        _setup_factories()

    # Check if already instantiated
    instance = _registry.get(provider_type, {}).get(name)
    if instance is not None:
        return instance

    # Try lazy instantiation from factory
    factory = _factories.get((provider_type, name))
    if factory:
        instance = factory()
        register(provider_type, name, instance)
        return instance

    available = list(_registry.get(provider_type, {}).keys())
    available += [n for (t, n) in _factories if t == provider_type and n not in available]
    if not available:
        raise ValueError(f"No providers registered for type '{provider_type}'")
    raise ValueError(f"Unknown {provider_type} provider '{name}'. Available: {', '.join(available)}")


def _setup_factories() -> None:
    """Register lazy factories for all built-in providers.

    Nothing is imported here — imports happen on first use of each provider.
    """
    global _initialized
    _initialized = True

    def _make_nasdaq():
        from prattern.providers.universe.nasdaq import NasdaqUniverseProvider
        return NasdaqUniverseProvider()

    def _make_yfinance():
        from prattern.providers.prices.yfinance_provider import YFinancePriceProvider
        return YFinancePriceProvider()

    def _make_finviz():
        from prattern.providers.news.finviz import FinvizNewsProvider
        return FinvizNewsProvider()

    def _make_gemini():
        from prattern.providers.ai.gemini import GeminiClassifier
        return GeminiClassifier()

    def _make_claude():
        from prattern.providers.ai.claude import ClaudeClassifier
        return ClaudeClassifier()

    _factories[("universe", "nasdaq")] = _make_nasdaq
    _factories[("prices", "yfinance")] = _make_yfinance
    _factories[("news", "finviz")] = _make_finviz
    _factories[("ai", "gemini")] = _make_gemini
    _factories[("ai", "claude")] = _make_claude
