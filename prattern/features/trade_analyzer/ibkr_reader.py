"""
IBKR Trade Data Readers

Supports:
1. Flex Query XML reports (recommended — most reliable)
2. CSV activity statement exports
3. Live TWS/Gateway API via ib_insync (requires running TWS or IB Gateway)
"""

import csv
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from prattern.features.trade_analyzer.models import Trade

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Flex Query XML Parser
# ---------------------------------------------------------------------------

def parse_flex_xml(filepath: str) -> List[Trade]:
    """Parse IBKR Flex Query XML report into Trade objects.

    Set up Flex Query in IBKR Account Management:
    1. Reports > Flex Queries > Create
    2. Select 'Trades' section
    3. Include fields: Symbol, DateTime, Buy/Sell, Quantity, Price, Commission, AssetCategory
    4. Delivery: XML
    """
    trades_raw = []

    tree = ET.parse(filepath)
    root = tree.getroot()

    # Handle both FlexQueryResponse and FlexStatementResponse formats
    trade_elements = root.iter("Trade")

    for elem in trade_elements:
        asset_cat = elem.get("assetCategory", "STK")
        if asset_cat not in ("STK", "OPT"):  # stocks and options only
            continue

        trades_raw.append({
            "ticker": elem.get("symbol", ""),
            "datetime": elem.get("dateTime", elem.get("tradeDate", "")),
            "side": elem.get("buySell", ""),
            "quantity": abs(float(elem.get("quantity", 0))),
            "price": float(elem.get("tradePrice", elem.get("price", 0))),
            "commission": abs(float(elem.get("ibCommission", elem.get("commission", 0)))),
            "code": elem.get("code", ""),
            "open_close": elem.get("openCloseIndicator", ""),
        })

    return _match_trades(trades_raw)


# ---------------------------------------------------------------------------
# 2. CSV Activity Statement Parser
# ---------------------------------------------------------------------------

def parse_csv_statement(filepath: str) -> List[Trade]:
    """Parse IBKR CSV activity statement (Trades section).

    Export from: Account Management > Reports > Statements > Activity > CSV
    """
    trades_raw = []
    in_trades_section = False

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            # Find the Trades section header
            if len(row) >= 2 and row[0] == "Trades" and row[1] == "Header":
                in_trades_section = True
                headers = row
                continue

            if in_trades_section:
                if row[0] != "Trades" or row[1] != "Data":
                    if row[0] != "Trades":
                        in_trades_section = False
                    continue

                try:
                    # Map CSV columns (IBKR format: Trades,Data,Order,Stocks,...)
                    h = {headers[i]: i for i in range(len(headers))}

                    asset_cat = row[h.get("Asset Category", 3)] if "Asset Category" in h else "Stocks"
                    if asset_cat not in ("Stocks", "Equity and Index Options"):
                        continue

                    ticker = row[h.get("Symbol", 5)] if "Symbol" in h else ""
                    date_str = row[h.get("Date/Time", 6)] if "Date/Time" in h else ""
                    qty = abs(float(row[h.get("Quantity", 7)] if "Quantity" in h else 0))
                    price = float(row[h.get("T. Price", 8)] if "T. Price" in h else 0)
                    commission = abs(float(row[h.get("Comm/Fee", 10)] if "Comm/Fee" in h else 0))
                    code = row[h.get("Code", 12)] if "Code" in h else ""

                    # Determine side from quantity sign in original
                    raw_qty = float(row[h.get("Quantity", 7)] if "Quantity" in h else 0)
                    side = "BUY" if raw_qty > 0 else "SELL"

                    trades_raw.append({
                        "ticker": ticker,
                        "datetime": date_str,
                        "side": side,
                        "quantity": qty,
                        "price": price,
                        "commission": commission,
                        "code": code,
                        "open_close": "",
                    })

                except (IndexError, ValueError) as e:
                    _log.warning("Skipping CSV row: %s — %s", row[:6], e)
                    continue

    return _match_trades(trades_raw)


# ---------------------------------------------------------------------------
# 3. Live IBKR API (ib_insync)
# ---------------------------------------------------------------------------

def fetch_from_ibkr_api(
    host: str = "127.0.0.1",
    port: int = 7497,          # TWS paper=7497, live=7496; Gateway paper=4002, live=4001
    client_id: int = 10,
    days_back: int = 30,
) -> List[Trade]:
    """Fetch completed trades from a running TWS or IB Gateway via ib_insync.

    Requires:
    - pip install ib_insync
    - TWS or IB Gateway running with API enabled
    - API settings: Enable ActiveX/Socket, allow connections
    """
    try:
        from ib_insync import IB
    except ImportError:
        raise ImportError(
            "ib_insync is required for live IBKR API access. "
            "Install with: pip install ib_insync"
        )

    ib = IB()
    trades_raw = []

    try:
        ib.connect(host, port, clientId=client_id)
        _log.info("Connected to IBKR at %s:%d", host, port)

        # Fetch completed trades (fills)
        fills = ib.fills()

        for fill in fills:
            contract = fill.contract
            execution = fill.execution
            commission_report = fill.commissionReport

            if contract.secType not in ("STK", "OPT"):
                continue

            trades_raw.append({
                "ticker": contract.symbol,
                "datetime": execution.time.strftime("%Y-%m-%d %H:%M:%S"),
                "side": execution.side,  # "BOT" or "SLD"
                "quantity": abs(execution.shares),
                "price": execution.price,
                "commission": abs(commission_report.commission) if commission_report else 0.0,
                "code": "",
                "open_close": "",
            })

    finally:
        ib.disconnect()

    # Normalize side names
    for t in trades_raw:
        if t["side"] in ("BOT", "BUY"):
            t["side"] = "BUY"
        elif t["side"] in ("SLD", "SELL"):
            t["side"] = "SELL"

    return _match_trades(trades_raw)


# ---------------------------------------------------------------------------
# Generic trade file loader (auto-detect format)
# ---------------------------------------------------------------------------

def load_trades(filepath: str) -> List[Trade]:
    """Auto-detect file format and parse trades.

    Supported: .xml (Flex Query), .csv (Activity Statement)
    """
    path = Path(filepath)

    if path.suffix.lower() == ".xml":
        _log.info("Parsing Flex Query XML: %s", filepath)
        return parse_flex_xml(filepath)
    elif path.suffix.lower() == ".csv":
        _log.info("Parsing CSV statement: %s", filepath)
        return parse_csv_statement(filepath)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .xml or .csv")


# ---------------------------------------------------------------------------
# Trade Matching Engine
# ---------------------------------------------------------------------------

def _parse_datetime(dt_str: str) -> datetime:
    """Parse various IBKR datetime formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d, %H:%M:%S",
        "%Y%m%d;%H%M%S",
        "%Y%m%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: '{dt_str}'")


def _match_trades(raw_executions: list) -> List[Trade]:
    """Match buy/sell executions into completed Trade objects using FIFO.

    Handles:
    - Simple long trades (buy then sell)
    - Simple short trades (sell then buy-to-cover)
    - Partial fills (aggregated)
    - Multiple positions in same ticker
    """
    # Sort by datetime
    for r in raw_executions:
        r["_dt"] = _parse_datetime(r["datetime"])
    raw_executions.sort(key=lambda x: x["_dt"])

    # Track open positions per ticker: {ticker: [{"side": BUY/SELL, "qty": float, "price": float, ...}]}
    positions = {}
    completed_trades = []

    for exec_data in raw_executions:
        ticker = exec_data["ticker"]
        side = exec_data["side"].upper()
        qty = exec_data["quantity"]
        price = exec_data["price"]
        dt = exec_data["_dt"]
        commission = exec_data["commission"]

        if ticker not in positions:
            positions[ticker] = {"qty": 0, "avg_price": 0.0, "side": None,
                                 "entry_date": None, "total_commission": 0.0}

        pos = positions[ticker]

        # Normalize: BUY adds positive qty, SELL adds negative
        signed_qty = qty if side in ("BUY", "BOT") else -qty

        if pos["qty"] == 0:
            # Opening a new position
            pos["qty"] = signed_qty
            pos["avg_price"] = price
            pos["side"] = "LONG" if signed_qty > 0 else "SHORT"
            pos["entry_date"] = dt
            pos["total_commission"] = commission

        elif (pos["qty"] > 0 and signed_qty > 0) or (pos["qty"] < 0 and signed_qty < 0):
            # Adding to existing position — update average price
            total_cost = pos["avg_price"] * abs(pos["qty"]) + price * qty
            pos["qty"] += signed_qty
            if pos["qty"] != 0:
                pos["avg_price"] = total_cost / abs(pos["qty"])
            pos["total_commission"] += commission

        else:
            # Closing (fully or partially)
            close_qty = min(abs(signed_qty), abs(pos["qty"]))

            trade = Trade(
                ticker=ticker,
                side=pos["side"],
                entry_date=pos["entry_date"],
                exit_date=dt,
                entry_price=pos["avg_price"],
                exit_price=price,
                quantity=close_qty,
                commission=pos["total_commission"] + commission,
            )
            completed_trades.append(trade)

            # Update remaining position
            if abs(signed_qty) >= abs(pos["qty"]):
                # Fully closed (or flipped)
                remainder = abs(signed_qty) - abs(pos["qty"])
                if remainder > 0:
                    # Flipped — open new position in opposite direction
                    new_side = "LONG" if signed_qty > 0 else "SHORT"
                    pos["qty"] = signed_qty + (-1 * pos["qty"]) if signed_qty > 0 else signed_qty - pos["qty"]
                    pos["avg_price"] = price
                    pos["side"] = new_side
                    pos["entry_date"] = dt
                    pos["total_commission"] = 0.0
                else:
                    # Fully closed
                    positions[ticker] = {"qty": 0, "avg_price": 0.0, "side": None,
                                         "entry_date": None, "total_commission": 0.0}
            else:
                # Partially closed
                pos["qty"] += signed_qty
                pos["total_commission"] = 0.0  # Reset commission for remaining

    _log.info("Matched %d completed trades from %d executions", len(completed_trades), len(raw_executions))
    return completed_trades
