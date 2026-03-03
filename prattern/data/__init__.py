"""Data layer — universe fetching, price downloads, pre-computed file loading."""

from prattern.data.universe import fetch_fmp_universe
from prattern.data.prices import fetch_stock_data, calculate_5day_change, get_high_velocity_movers
from prattern.data.precomputed import load_precomputed_movers, load_precomputed_analysis

__all__ = [
    "fetch_fmp_universe",
    "fetch_stock_data",
    "calculate_5day_change",
    "get_high_velocity_movers",
    "load_precomputed_movers",
    "load_precomputed_analysis",
]
