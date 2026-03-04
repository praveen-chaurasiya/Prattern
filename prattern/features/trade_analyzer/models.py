"""Data models for trade analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Trade:
    """A single completed trade (entry + exit)."""
    ticker: str
    side: str                          # "LONG" or "SHORT"
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: float
    commission: float = 0.0

    @property
    def pnl_gross(self) -> float:
        """Gross P&L before commissions."""
        if self.side == "LONG":
            return (self.exit_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.exit_price) * self.quantity

    @property
    def pnl_net(self) -> float:
        """Net P&L after commissions."""
        return self.pnl_gross - self.commission

    @property
    def pnl_pct(self) -> float:
        """P&L as percentage of entry."""
        if self.entry_price == 0:
            return 0.0
        if self.side == "LONG":
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.exit_price) / self.entry_price) * 100

    @property
    def is_winner(self) -> bool:
        return self.pnl_net > 0

    @property
    def hold_days(self) -> int:
        return (self.exit_date - self.entry_date).days


@dataclass
class TradeMetrics:
    """Aggregated trading performance metrics."""
    # Core
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0

    # Win Rate
    win_rate: float = 0.0              # percentage

    # P&L
    total_pnl: float = 0.0
    total_pnl_gross: float = 0.0
    total_commissions: float = 0.0
    avg_pnl_per_trade: float = 0.0

    # Win/Loss
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Risk-Reward
    risk_reward_ratio: float = 0.0     # avg_win / abs(avg_loss)
    profit_factor: float = 0.0         # gross_wins / abs(gross_losses)

    # Streaks
    max_win_streak: int = 0
    max_loss_streak: int = 0
    current_streak: int = 0
    current_streak_type: str = ""      # "W" or "L"

    # Drawdown
    max_drawdown: float = 0.0          # max peak-to-trough in $
    max_drawdown_pct: float = 0.0      # max peak-to-trough in %

    # Time
    avg_hold_days: float = 0.0
    avg_hold_days_winners: float = 0.0
    avg_hold_days_losers: float = 0.0

    # Expectancy
    expectancy: float = 0.0            # (win_rate * avg_win) - (loss_rate * abs(avg_loss))

    # By ticker
    best_ticker: str = ""
    worst_ticker: str = ""

    # Distribution
    pnl_by_ticker: dict = field(default_factory=dict)
    pnl_by_month: dict = field(default_factory=dict)
    pnl_by_weekday: dict = field(default_factory=dict)
    pnl_by_side: dict = field(default_factory=dict)

    # Equity curve points: [(date, cumulative_pnl)]
    equity_curve: List[tuple] = field(default_factory=list)
