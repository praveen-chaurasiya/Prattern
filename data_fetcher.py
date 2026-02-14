"""
Data Fetcher Module
Fetches stock data and identifies high-velocity movers (>=20% gain in 5 days)
Supports FMP universe discovery for full US market coverage (~6,000 stocks)
"""

import json
import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from config import Config


# ============================================================================
# US STOCKS - Comprehensive List
# ============================================================================

# S&P 500 Large Caps
SP500_LARGE_CAPS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL',
    'ADBE', 'CRM', 'CSCO', 'ACN', 'INTC', 'AMD', 'IBM', 'QCOM', 'TXN', 'INTU',
    'NOW', 'AMAT', 'ADI', 'MU', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'MCHP', 'FTNT',
    'NXPI', 'MRVL', 'WDAY', 'TEAM', 'PANW', 'CRWD', 'DDOG', 'NET', 'ZS', 'SNOW',

    # Financials
    'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'SPGI', 'BLK',
    'C', 'SCHW', 'AXP', 'CB', 'PNC', 'USB', 'TFC', 'COF', 'BK', 'AIG',
    'MMC', 'AON', 'ICE', 'CME', 'MCO', 'AFL', 'MET', 'PRU', 'ALL', 'TRV',

    # Healthcare
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
    'AMGN', 'GILD', 'CVS', 'CI', 'ISRG', 'SYK', 'BSX', 'MDT', 'ZTS', 'REGN',
    'VRTX', 'HUM', 'ELV', 'MCK', 'COR', 'A', 'IQV', 'RMD', 'DXCM', 'IDXX',

    # Consumer Discretionary
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'ABNB',
    'CMG', 'MAR', 'GM', 'F', 'YUM', 'ORLY', 'AZO', 'DHI', 'LEN', 'NVR',
    'RCL', 'CCL', 'NCLH', 'LVS', 'MGM', 'WYNN', 'POOL', 'HLT', 'DRI', 'ULTA',

    # Consumer Staples
    'WMT', 'PG', 'KO', 'PEP', 'COST', 'PM', 'MO', 'MDLZ', 'CL', 'GIS',
    'KMB', 'SYY', 'HSY', 'K', 'CAG', 'TSN', 'HRL', 'CPB', 'MKC', 'CHD',

    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
    'WMB', 'KMI', 'HES', 'DVN', 'FANG', 'BKR', 'MRO', 'APA', 'CTRA', 'EQT',

    # Industrials
    'GE', 'CAT', 'BA', 'HON', 'RTX', 'UPS', 'DE', 'UNP', 'LMT', 'GD',
    'MMM', 'NOC', 'CSX', 'NSC', 'FDX', 'WM', 'EMR', 'ITW', 'ETN', 'PH',

    # Materials
    'LIN', 'APD', 'SHW', 'FCX', 'NEM', 'ECL', 'DD', 'NUE', 'DOW', 'PPG',

    # Real Estate
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'SPG', 'O', 'WELL', 'AVB',

    # Utilities
    'NEE', 'SO', 'DUK', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ES', 'PCG',

    # Communication Services
    'META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR',
    'PARA', 'OMC', 'EA', 'TTWO', 'WBD', 'MTCH', 'NWSA', 'FOX', 'FOXA', 'IPG'
]

# Mid-Cap Stocks
MIDCAP_STOCKS = [
    # Technology
    'PLTR', 'COIN', 'HOOD', 'SQ', 'SHOP', 'ZM', 'DOCU', 'OKTA', 'DBX', 'BOX',
    'TWLO', 'ESTC', 'MDB', 'PATH', 'DT', 'BILL', 'CFLT', 'S', 'GTLB', 'FROG',

    # Healthcare
    'MRNA', 'TECH', 'EXAS', 'ALGN', 'PODD', 'PEN', 'HOLX', 'INCY', 'BMRN', 'UTHR',
    'SGEN', 'ALNY', 'RARE', 'SRPT', 'IONS', 'NBIX', 'JAZZ', 'FOLD', 'BLUE', 'ARWR',

    # Consumer
    'LULU', 'DECK', 'BURL', 'FIVE', 'OLLI', 'DKS', 'TSCO', 'AAP', 'AEO', 'ANF',
    'CROX', 'SKX', 'FL', 'WSM', 'RH', 'W', 'CHWY', 'PETS', 'CAVA', 'WING',

    # Financials
    'SOFI', 'ALLY', 'HBAN', 'RF', 'KEY', 'CFG', 'FITB', 'EWBC', 'WTFC', 'ZION',

    # Industrials
    'CARR', 'OTIS', 'XYL', 'VRSK', 'IEX', 'GNRC', 'AOS', 'DOV', 'IR', 'ROK',

    # Energy
    'TPL', 'PR', 'CHK', 'AR', 'SM', 'RRC', 'MTDR', 'NOG', 'MGY', 'VTLE'
]

# Small-Cap High-Growth Stocks
SMALLCAP_GROWTH = [
    # EV & Clean Energy
    'RIVN', 'LCID', 'CHPT', 'BLNK', 'PLUG', 'FCEL', 'ENPH', 'SEDG', 'RUN', 'NOVA',

    # Biotech
    'SAVA', 'NKTR', 'CRISPR', 'NTLA', 'BEAM', 'CRSP', 'EDIT', 'VCYT', 'FATE', 'NTLA',

    # Fintech
    'UPST', 'AFRM', 'LC', 'PAYC', 'PAYO', 'GPN', 'FIS', 'FISV', 'FOUR', 'STNE',

    # AI/Cloud
    'AI', 'SMCI', 'IONQ', 'RGTI', 'BBAI', 'SOUN', 'AMBA', 'QUBT', 'LUNR', 'RKLB',

    # Meme Stocks
    'GME', 'AMC', 'BBBY', 'BB', 'NOK', 'EXPR', 'KOSS', 'NAKD', 'CLOV', 'WKHS'
]

# ============================================================================
# ETFs - Comprehensive List
# ============================================================================

# Broad Market ETFs
BROAD_MARKET_ETFS = [
    'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'SCHX', 'IVV', 'VEA', 'IEFA',
    'VWO', 'IEMG', 'EEM', 'EFA', 'ACWI', 'URTH', 'VT', 'IXUS', 'VXUS', 'SPDW'
]

# Sector ETFs
SECTOR_ETFS = [
    'XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP', 'XLRE', 'XLU', 'XLC',
    'VGT', 'VFH', 'VHT', 'VDE', 'VIS', 'VCR', 'VDC', 'VNQ', 'VPU', 'VOX',
    'IYW', 'IYF', 'IYH', 'IYE', 'IYJ', 'IYC', 'IYK', 'IYR', 'IDU', 'IYZ'
]

# Thematic ETFs
THEMATIC_ETFS = [
    # Technology & Innovation
    'ARKK', 'ARKG', 'ARKQ', 'ARKW', 'ARKF', 'CIBR', 'HACK', 'ROBO', 'BOTZ', 'IRBO',
    'CLOU', 'WCLD', 'SKYY', 'IGV', 'FDN', 'FINX', 'IPAY', 'THNQ', 'AIQ', 'QTUM',

    # Clean Energy
    'ICLN', 'TAN', 'QCLN', 'PBW', 'ACES', 'SMOG', 'FAN', 'EVX', 'LIT', 'BATT',

    # Crypto & Blockchain
    'BITO', 'BITI', 'BLOK', 'LEGR', 'KOIN', 'CRPT', 'BITQ', 'BLCN', 'GBTC', 'ETHE',

    # Semiconductors
    'SOXX', 'SMH', 'XSD', 'PSI', 'SOXL', 'SOXS',

    # Healthcare
    'XBI', 'IBB', 'BBH', 'IHI', 'IHE', 'ARKG', 'GNOM', 'SBIO',

    # Commodities
    'GLD', 'SLV', 'GDX', 'GDXJ', 'USO', 'UNG', 'DBA', 'DBC', 'PDBC', 'GSG',

    # Cannabis
    'MJ', 'THCX', 'YOLO', 'CNBS', 'POTX', 'MSOS',

    # ESG
    'ESGU', 'ESGV', 'SUSL', 'DSI', 'USSG', 'VSGX', 'SUSA'
]

# Leveraged & Inverse ETFs
LEVERAGED_ETFS = [
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'TNA', 'TZA', 'UDOW', 'SDOW', 'FAS', 'FAZ',
    'TECL', 'TECS', 'LABU', 'LABD', 'CURE', 'RXD', 'ERX', 'ERY', 'NAIL', 'DRV',
    'NUGT', 'DUST', 'JNUG', 'JDST', 'UVXY', 'SVXY', 'VXX', 'VIXY', 'SPXL', 'SPXS'
]

# Bond & Fixed Income ETFs
BOND_ETFS = [
    'AGG', 'BND', 'LQD', 'HYG', 'JNK', 'TLT', 'IEF', 'SHY', 'TIP', 'VCIT',
    'VCSH', 'BNDX', 'VWOB', 'EMB', 'MUB', 'SUB', 'BKLN', 'SJNK', 'SHYG', 'FLOT'
]

# ============================================================================
# UNIVERSE DEFINITIONS
# ============================================================================

# Universe 1: Stocks Only (Large + Mid + Small Cap) — deduplicated
UNIVERSE_STOCKS_ONLY = list(dict.fromkeys(SP500_LARGE_CAPS + MIDCAP_STOCKS + SMALLCAP_GROWTH))

# Universe 2: Stocks + ETFs (Complete Universe)
UNIVERSE_STOCKS_AND_ETFS = (
    SP500_LARGE_CAPS +
    MIDCAP_STOCKS +
    SMALLCAP_GROWTH +
    BROAD_MARKET_ETFS +
    SECTOR_ETFS +
    THEMATIC_ETFS +
    LEVERAGED_ETFS +
    BOND_ETFS
)

# Legacy alias for backward compatibility
SP500_TICKERS = SP500_LARGE_CAPS[:100]  # Keep first 100 for backward compat


UNIVERSE_CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "universe_cache.json")


def fetch_fmp_universe() -> List[str]:
    """
    Fetch full US stock universe from NASDAQ's free screener API.
    Returns all traded stocks on NYSE/NASDAQ/AMEX with price > $0.50.
    Caches result daily to avoid repeated API calls.
    Falls back to hardcoded UNIVERSE_STOCKS_ONLY if the call fails.

    Returns:
        List of ticker symbols
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Check cache first
    if os.path.exists(UNIVERSE_CACHE_PATH):
        try:
            with open(UNIVERSE_CACHE_PATH, "r") as f:
                cache = json.load(f)
            if cache.get("date") == today:
                tickers = cache["tickers"]
                print(f"[UNIVERSE] Loading cached universe: {len(tickers)} tickers (cached {today})")
                return tickers
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupted cache, re-fetch

    # Fetch from NASDAQ screener (free, no API key needed)
    url = "https://api.nasdaq.com/api/screener/stocks?tableType=traded&limit=10000&offset=0"
    headers = {"User-Agent": "Mozilla/5.0"}
    print("[UNIVERSE] Fetching full US stock universe from NASDAQ...")

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("data", {}).get("table", {}).get("rows", [])
    except Exception as e:
        print(f"[UNIVERSE] NASDAQ call failed: {e} — falling back to hardcoded list")
        return UNIVERSE_STOCKS_ONLY

    if not rows:
        print("[UNIVERSE] NASDAQ returned no data — falling back to hardcoded list")
        return UNIVERSE_STOCKS_ONLY

    # Filter: price > $0.50, valid ticker format
    tickers = []
    for row in rows:
        symbol = row.get("symbol", "").strip()
        lastsale = row.get("lastsale", "")

        # Parse price (comes as "$123.45" string)
        try:
            price = float(lastsale.replace("$", "").replace(",", ""))
        except (ValueError, AttributeError):
            continue

        if price <= 0.50:
            continue

        # Skip tickers with special chars (warrants, units, etc.)
        if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
            continue

        # Skip very long symbols (likely warrants/units like ABCDW)
        if len(symbol) > 5 and not "." in symbol:
            continue

        tickers.append(symbol)

    if not tickers:
        print("[UNIVERSE] No valid tickers after filtering — falling back to hardcoded list")
        return UNIVERSE_STOCKS_ONLY

    # Cache result
    os.makedirs(os.path.dirname(UNIVERSE_CACHE_PATH), exist_ok=True)
    with open(UNIVERSE_CACHE_PATH, "w") as f:
        json.dump({"date": today, "tickers": tickers}, f)

    print(f"[UNIVERSE] Loaded {len(tickers)} US stocks from NASDAQ (cached for {today})")
    return tickers


def fetch_stock_data(ticker: str, period: str = "10d") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a single ticker

    Args:
        ticker: Stock symbol
        period: Data period (default: 10d to ensure we get 5 trading days)

    Returns:
        DataFrame with OHLCV data or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            print(f"[!]  No data for {ticker}")
            return None

        return df
    except Exception as e:
        print(f"[ERROR] Error fetching {ticker}: {str(e)}")
        return None


def calculate_5day_change(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate percentage change from 5 trading days ago

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Percentage change or None if insufficient data
    """
    if len(df) < 6:  # Need at least 6 days to compare current vs 5 days ago
        return None

    current_price = df['Close'].iloc[-1]
    price_5_days_ago = df['Close'].iloc[-6]  # -6 because -1 is today, -6 is 5 days ago

    if price_5_days_ago == 0:
        return None

    change_pct = ((current_price - price_5_days_ago) / price_5_days_ago) * 100
    return round(change_pct, 2)


def get_high_velocity_movers(tickers: List[str] = None, threshold: float = 20.0) -> List[Dict]:
    """
    Identify stocks with >= threshold% gain in 5 trading days.
    Uses batch yf.download() for speed — scans hundreds of tickers in seconds.

    Args:
        tickers: List of tickers to analyze (default: full stock universe)
        threshold: Minimum percentage gain to qualify (default: 20.0)

    Returns:
        List of dicts with ticker, current_price, price_5d_ago, move_pct
    """
    if tickers is None:
        tickers = fetch_fmp_universe()

    # Deduplicate while preserving order
    seen = set()
    unique_tickers = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    tickers = unique_tickers

    total = len(tickers)
    print(f"[SCAN] Scanning {total} tickers for high-velocity movers (>={threshold}% in 5 days)...")

    # Batch download in chunks of 200 for reliability with large universes
    # Smaller batches reduce timeouts; threads=4 avoids connection flooding
    import logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    BATCH_SIZE = 200
    df_all = pd.DataFrame()

    for i in range(0, total, BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"[SCAN] Downloading batch {batch_num}/{total_batches} ({len(batch)} tickers)...")

        try:
            df_batch = yf.download(
                batch, period="10d", progress=False,
                threads=4, timeout=20
            )
        except Exception as e:
            print(f"[ERROR] Batch {batch_num} download failed: {str(e)}")
            continue

        if df_batch.empty:
            continue

        # Merge batch results
        if df_all.empty:
            df_all = df_batch
        else:
            if isinstance(df_batch.columns, pd.MultiIndex):
                df_all = pd.concat([df_all, df_batch], axis=1)

    if df_all.empty:
        print("[!] No data returned from downloads")
        return []

    movers = []

    for ticker in tickers:
        try:
            # Extract single ticker's Close prices from multi-ticker DataFrame
            if len(tickers) == 1:
                close = df_all['Close']
            else:
                close = df_all['Close'][ticker]

            close = close.dropna()

            if len(close) < 6:
                continue

            current_price = close.iloc[-1]
            price_5d_ago = close.iloc[-6]

            if price_5d_ago == 0:
                continue

            change_pct = round(((current_price - price_5d_ago) / price_5d_ago) * 100, 2)

            if change_pct >= threshold:
                mover = {
                    'ticker': ticker,
                    'current_price': round(float(current_price), 2),
                    'price_5d_ago': round(float(price_5d_ago), 2),
                    'move_pct': change_pct,
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
                movers.append(mover)
                print(f"   [+] {ticker}: +{change_pct}% (${price_5d_ago:.2f} -> ${current_price:.2f})")

        except Exception:
            continue

    # Sort by move percentage descending
    movers.sort(key=lambda x: x['move_pct'], reverse=True)

    print(f"\n[>] Found {len(movers)} high-velocity movers out of {total} scanned!")
    return movers


DAILY_MOVERS_PATH = os.path.join(os.path.dirname(__file__), "data", "daily_movers.json")


def load_precomputed_movers() -> Optional[Dict]:
    """
    Load pre-computed movers from data/daily_movers.json (created by scan_universe.py).
    Returns the full result dict if today's scan exists, otherwise None.
    """
    if not os.path.exists(DAILY_MOVERS_PATH):
        return None

    try:
        with open(DAILY_MOVERS_PATH, "r") as f:
            data = json.load(f)

        scan_date = data.get("scan_date", "")
        today = datetime.now().strftime("%Y-%m-%d")

        if scan_date == today:
            return data
        else:
            print(f"[!] Pre-computed scan is from {scan_date}, not today ({today})")
            return data  # Still return stale data — let caller decide
    except (json.JSONDecodeError, KeyError):
        return None


if __name__ == "__main__":
    # Test the module
    print("=" * 60)
    print("STOCK DATA FETCHER - TEST MODE")
    print("=" * 60)

    movers = get_high_velocity_movers()

    if movers:
        print("\n" + "=" * 60)
        print("HIGH-VELOCITY MOVERS:")
        print("=" * 60)
        for mover in movers:
            print(f"{mover['ticker']}: ${mover['price_5d_ago']} -> ${mover['current_price']} (+{mover['move_pct']}%)")
    else:
        print("\n[!]  No movers found matching criteria")
