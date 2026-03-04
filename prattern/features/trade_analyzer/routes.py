"""Trade Analyzer API routes."""

import json
import logging
import os
import tempfile
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from prattern.features.trade_analyzer.analyzer import analyze_trades, format_report
from prattern.features.trade_analyzer.ibkr_reader import (
    load_trades,
    fetch_from_ibkr_api,
)
from prattern.features.trade_analyzer.models import Trade

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/trades", tags=["trade-analyzer"])


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
):
    """Upload an IBKR Flex XML or CSV statement and get trade analysis.

    Accepts:
    - .xml — IBKR Flex Query report
    - .csv — IBKR Activity Statement CSV export
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in (".xml", ".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {suffix}. Use .xml (Flex Query) or .csv (Activity Statement)"
        )

    # Save to temp file for parsing
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        trades = load_trades(tmp_path)

        if not trades:
            raise HTTPException(status_code=422, detail="No completed trades found in the uploaded file")

        metrics = analyze_trades(trades)

        return {
            "status": "ok",
            "filename": file.filename,
            "trades_found": len(trades),
            "metrics": asdict(metrics),
            "trades": [
                {
                    "ticker": t.ticker,
                    "side": t.side,
                    "entry_date": t.entry_date.strftime("%Y-%m-%d"),
                    "exit_date": t.exit_date.strftime("%Y-%m-%d"),
                    "entry_price": round(t.entry_price, 2),
                    "exit_price": round(t.exit_price, 2),
                    "quantity": t.quantity,
                    "pnl_net": round(t.pnl_net, 2),
                    "pnl_pct": round(t.pnl_pct, 2),
                    "hold_days": t.hold_days,
                    "commission": round(t.commission, 2),
                }
                for t in sorted(trades, key=lambda t: t.exit_date)
            ],
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        _log.error("Trade analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.post("/analyze/live")
def analyze_live_ibkr(
    host: str = Query("127.0.0.1", description="TWS/Gateway host"),
    port: int = Query(7497, description="TWS/Gateway port (7497=paper, 7496=live)"),
    client_id: int = Query(10, description="API client ID"),
):
    """Fetch trades from a running TWS/IB Gateway and analyze.

    Requires: TWS or IB Gateway running with API enabled, ib_insync installed.
    """
    try:
        trades = fetch_from_ibkr_api(host=host, port=port, client_id=client_id)

        if not trades:
            raise HTTPException(status_code=404, detail="No completed trades found in IBKR account")

        metrics = analyze_trades(trades)

        return {
            "status": "ok",
            "source": "ibkr_live",
            "connection": f"{host}:{port}",
            "trades_found": len(trades),
            "metrics": asdict(metrics),
        }

    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ConnectionRefusedError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to IBKR at {host}:{port}. Is TWS/Gateway running with API enabled?"
        )
    except Exception as e:
        _log.error("Live IBKR analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/report")
def get_text_report(
    source: str = Query("upload", description="Data source: 'upload' (last uploaded) or 'live'"),
):
    """Get a formatted text report of the last analysis. Useful for Telegram/CLI."""
    # This would need state management — for now, return instructions
    return {
        "message": "Use POST /trades/upload with a Flex XML or CSV file to get analysis. "
                   "The response includes full metrics. For live IBKR, use POST /trades/analyze/live."
    }
