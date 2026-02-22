"""File I/O helpers — read tickers from files, save analysis results."""

import json
import os
from datetime import datetime
from typing import List, Dict

from prattern.core.ticker_lists import UNIVERSE_STOCKS_ONLY


def read_tickers_from_file(filename: str) -> List[str]:
    """
    Read tickers from a file.

    Supports formats:
    - One ticker per line: NVDA\\nTSLA\\nAAPL
    - Comma-separated: NVDA, TSLA, AAPL
    - Mixed: supports both formats

    Args:
        filename: Path to file

    Returns:
        List of ticker symbols
    """
    tickers = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

            lines = content.replace(',', '\n').split('\n')

            for line in lines:
                ticker = line.strip().upper()
                if not ticker or ticker.startswith('#') or ' ' in ticker:
                    continue
                if ticker.replace('.', '').replace('-', '').isalnum():
                    if 1 <= len(ticker) <= 6:
                        tickers.append(ticker)

        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for ticker in tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)

        print(f"[OK] Loaded {len(unique_tickers)} tickers from: {filename}")
        return unique_tickers

    except FileNotFoundError:
        print(f"[ERROR] File not found: {filename}")
        return []
    except Exception as e:
        print(f"[ERROR] Error reading file: {str(e)}")
        return []


def save_results(movers: List[Dict], total_scanned: int = None, output_dir: str = "themes") -> str:
    """
    Save analysis results to daily JSON file.

    Args:
        movers: List of analyzed movers with category and summary
        total_scanned: Number of tickers scanned (optional)
        output_dir: Directory to save results (default: themes)

    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}_movers.json"
    filepath = os.path.join(output_dir, filename)

    output_data = {
        "date": today,
        "total_tickers_scanned": total_scanned or len(UNIVERSE_STOCKS_ONLY),
        "movers_found": len(movers),
        "movers": movers
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return filepath
