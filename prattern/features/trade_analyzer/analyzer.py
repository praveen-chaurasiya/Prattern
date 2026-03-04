"""
Post-Trade Analyzer — computes key trading performance metrics.

Reads matched trades and calculates:
- Win rate, profit factor, risk-reward ratio
- Drawdown, streaks, expectancy
- Breakdowns by ticker, month, weekday, side
- Equity curve
"""

import logging
from collections import defaultdict
from typing import List

from prattern.features.trade_analyzer.models import Trade, TradeMetrics

_log = logging.getLogger(__name__)


def analyze_trades(trades: List[Trade]) -> TradeMetrics:
    """Compute all trading metrics from a list of completed trades."""
    if not trades:
        return TradeMetrics()

    m = TradeMetrics()
    m.total_trades = len(trades)

    # Sort by exit date for equity curve / streak calculation
    trades = sorted(trades, key=lambda t: t.exit_date)

    winners = [t for t in trades if t.pnl_net > 0]
    losers = [t for t in trades if t.pnl_net < 0]
    breakevens = [t for t in trades if t.pnl_net == 0]

    m.winning_trades = len(winners)
    m.losing_trades = len(losers)
    m.breakeven_trades = len(breakevens)

    # Win Rate
    m.win_rate = round((m.winning_trades / m.total_trades) * 100, 2) if m.total_trades > 0 else 0.0

    # P&L
    m.total_pnl = round(sum(t.pnl_net for t in trades), 2)
    m.total_pnl_gross = round(sum(t.pnl_gross for t in trades), 2)
    m.total_commissions = round(sum(t.commission for t in trades), 2)
    m.avg_pnl_per_trade = round(m.total_pnl / m.total_trades, 2) if m.total_trades > 0 else 0.0

    # Average Win / Loss
    m.avg_win = round(sum(t.pnl_net for t in winners) / len(winners), 2) if winners else 0.0
    m.avg_loss = round(sum(t.pnl_net for t in losers) / len(losers), 2) if losers else 0.0
    m.largest_win = round(max((t.pnl_net for t in winners), default=0.0), 2)
    m.largest_loss = round(min((t.pnl_net for t in losers), default=0.0), 2)

    # Risk-Reward Ratio
    if m.avg_loss != 0:
        m.risk_reward_ratio = round(abs(m.avg_win / m.avg_loss), 2)

    # Profit Factor
    gross_wins = sum(t.pnl_net for t in winners)
    gross_losses = abs(sum(t.pnl_net for t in losers))
    m.profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else float('inf')

    # Expectancy: (win_rate * avg_win) - (loss_rate * abs(avg_loss))
    win_rate_dec = m.win_rate / 100
    loss_rate_dec = 1 - win_rate_dec
    m.expectancy = round(
        (win_rate_dec * m.avg_win) - (loss_rate_dec * abs(m.avg_loss)), 2
    )

    # Streaks
    m.max_win_streak, m.max_loss_streak, m.current_streak, m.current_streak_type = _calc_streaks(trades)

    # Drawdown
    m.max_drawdown, m.max_drawdown_pct = _calc_drawdown(trades)

    # Hold Time
    all_hold = [t.hold_days for t in trades]
    win_hold = [t.hold_days for t in winners]
    loss_hold = [t.hold_days for t in losers]

    m.avg_hold_days = round(sum(all_hold) / len(all_hold), 1) if all_hold else 0.0
    m.avg_hold_days_winners = round(sum(win_hold) / len(win_hold), 1) if win_hold else 0.0
    m.avg_hold_days_losers = round(sum(loss_hold) / len(loss_hold), 1) if loss_hold else 0.0

    # Breakdowns
    m.pnl_by_ticker = _group_pnl(trades, key=lambda t: t.ticker)
    m.pnl_by_month = _group_pnl(trades, key=lambda t: t.exit_date.strftime("%Y-%m"))
    m.pnl_by_weekday = _group_pnl(trades, key=lambda t: t.exit_date.strftime("%A"))
    m.pnl_by_side = _group_pnl(trades, key=lambda t: t.side)

    # Best/Worst ticker
    if m.pnl_by_ticker:
        m.best_ticker = max(m.pnl_by_ticker, key=lambda k: m.pnl_by_ticker[k]["pnl"])
        m.worst_ticker = min(m.pnl_by_ticker, key=lambda k: m.pnl_by_ticker[k]["pnl"])

    # Equity Curve
    m.equity_curve = _build_equity_curve(trades)

    return m


def _calc_streaks(trades: List[Trade]):
    """Calculate max win/loss streaks and current streak."""
    max_win = max_loss = current = 0
    current_type = ""

    for t in trades:
        if t.pnl_net > 0:
            if current_type == "W":
                current += 1
            else:
                current = 1
                current_type = "W"
            max_win = max(max_win, current)
        elif t.pnl_net < 0:
            if current_type == "L":
                current += 1
            else:
                current = 1
                current_type = "L"
            max_loss = max(max_loss, current)
        # Breakeven doesn't affect streak

    return max_win, max_loss, current, current_type


def _calc_drawdown(trades: List[Trade]):
    """Calculate max drawdown in $ and %."""
    if not trades:
        return 0.0, 0.0

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    max_dd_pct = 0.0

    for t in trades:
        cumulative += t.pnl_net
        if cumulative > peak:
            peak = cumulative

        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
            if peak > 0:
                max_dd_pct = (dd / peak) * 100

    return round(max_dd, 2), round(max_dd_pct, 2)


def _group_pnl(trades: List[Trade], key) -> dict:
    """Group trades by a key function and aggregate P&L."""
    groups = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})

    for t in trades:
        k = key(t)
        groups[k]["trades"] += 1
        groups[k]["pnl"] += t.pnl_net
        if t.pnl_net > 0:
            groups[k]["wins"] += 1

    # Round and add win rate
    result = {}
    for k, v in groups.items():
        result[k] = {
            "trades": v["trades"],
            "pnl": round(v["pnl"], 2),
            "wins": v["wins"],
            "win_rate": round((v["wins"] / v["trades"]) * 100, 1) if v["trades"] > 0 else 0.0,
        }

    return dict(sorted(result.items(), key=lambda x: x[1]["pnl"], reverse=True))


def _build_equity_curve(trades: List[Trade]) -> List[tuple]:
    """Build cumulative P&L equity curve."""
    curve = []
    cumulative = 0.0

    for t in trades:
        cumulative += t.pnl_net
        curve.append((t.exit_date.strftime("%Y-%m-%d"), round(cumulative, 2)))

    return curve


# ---------------------------------------------------------------------------
# Report Formatting
# ---------------------------------------------------------------------------

def format_report(m: TradeMetrics, title: str = "Post-Trade Analysis") -> str:
    """Format metrics into a readable text report."""
    lines = []
    lines.append(f"{'=' * 55}")
    lines.append(f"  {title}")
    lines.append(f"{'=' * 55}")

    lines.append("")
    lines.append("  PERFORMANCE SUMMARY")
    lines.append(f"  {'─' * 45}")
    lines.append(f"  Total Trades:        {m.total_trades}")
    lines.append(f"  Win Rate:            {m.win_rate}% ({m.winning_trades}W / {m.losing_trades}L / {m.breakeven_trades}BE)")
    lines.append(f"  Total P&L:           ${m.total_pnl:,.2f}")
    lines.append(f"  Total Commissions:   ${m.total_commissions:,.2f}")
    lines.append(f"  Avg P&L per Trade:   ${m.avg_pnl_per_trade:,.2f}")

    lines.append("")
    lines.append("  RISK METRICS")
    lines.append(f"  {'─' * 45}")
    lines.append(f"  Risk-Reward Ratio:   {m.risk_reward_ratio}")
    lines.append(f"  Profit Factor:       {m.profit_factor}")
    lines.append(f"  Expectancy:          ${m.expectancy:,.2f} per trade")
    lines.append(f"  Max Drawdown:        ${m.max_drawdown:,.2f} ({m.max_drawdown_pct}%)")

    lines.append("")
    lines.append("  WIN / LOSS DETAIL")
    lines.append(f"  {'─' * 45}")
    lines.append(f"  Avg Win:             ${m.avg_win:,.2f}")
    lines.append(f"  Avg Loss:            ${m.avg_loss:,.2f}")
    lines.append(f"  Largest Win:         ${m.largest_win:,.2f}")
    lines.append(f"  Largest Loss:        ${m.largest_loss:,.2f}")

    lines.append("")
    lines.append("  STREAKS")
    lines.append(f"  {'─' * 45}")
    lines.append(f"  Max Win Streak:      {m.max_win_streak}")
    lines.append(f"  Max Loss Streak:     {m.max_loss_streak}")
    streak_label = f"{m.current_streak} ({'Winning' if m.current_streak_type == 'W' else 'Losing'})" if m.current_streak_type else "N/A"
    lines.append(f"  Current Streak:      {streak_label}")

    lines.append("")
    lines.append("  HOLD TIME")
    lines.append(f"  {'─' * 45}")
    lines.append(f"  Avg Hold (all):      {m.avg_hold_days} days")
    lines.append(f"  Avg Hold (winners):  {m.avg_hold_days_winners} days")
    lines.append(f"  Avg Hold (losers):   {m.avg_hold_days_losers} days")

    if m.pnl_by_side:
        lines.append("")
        lines.append("  BY SIDE")
        lines.append(f"  {'─' * 45}")
        for side, stats in m.pnl_by_side.items():
            lines.append(f"  {side:6s}  {stats['trades']} trades  ${stats['pnl']:>10,.2f}  WR: {stats['win_rate']}%")

    if m.pnl_by_ticker:
        lines.append("")
        lines.append("  TOP TICKERS (by P&L)")
        lines.append(f"  {'─' * 45}")
        sorted_tickers = sorted(m.pnl_by_ticker.items(), key=lambda x: x[1]["pnl"], reverse=True)
        for ticker, stats in sorted_tickers[:10]:
            lines.append(f"  {ticker:>6s}  {stats['trades']} trades  ${stats['pnl']:>10,.2f}  WR: {stats['win_rate']}%")
        if len(sorted_tickers) > 10:
            lines.append(f"  ... and {len(sorted_tickers) - 10} more tickers")

    if m.pnl_by_month:
        lines.append("")
        lines.append("  BY MONTH")
        lines.append(f"  {'─' * 45}")
        for month, stats in m.pnl_by_month.items():
            bar = "+" * min(int(abs(stats['pnl']) / 100), 20) if stats['pnl'] > 0 else "-" * min(int(abs(stats['pnl']) / 100), 20)
            lines.append(f"  {month}  {stats['trades']} trades  ${stats['pnl']:>10,.2f}  {bar}")

    lines.append("")
    lines.append(f"{'=' * 55}")

    return "\n".join(lines)
