"""Typed data models for the Prattern pipeline."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Mover:
    """A stock that moved >= threshold% in 5 trading days."""
    ticker: str
    current_price: float
    price_5d_ago: float
    move_pct: float
    date: str = ""
    headlines: List[str] = field(default_factory=list)


@dataclass
class AnalyzedMover(Mover):
    """A mover with AI classification fields."""
    category: str = "Unknown"
    summary: str = ""
    primary_theme: str = "Other"
    sub_niche: str = "Unknown"
    ecosystem_role: str = "Platform"
    micro_theme: str = "Other"


@dataclass
class ScanResult:
    """Metadata + movers from a daily scan."""
    scan_date: str
    scan_time: str
    universe_size: int
    threshold: float
    movers_found: int
    movers: List[dict] = field(default_factory=list)
    tickers_with_data: Optional[int] = None
    analysis_time: Optional[str] = None
    analysis_duration_seconds: Optional[float] = None
