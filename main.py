"""
Stock Market Engine - Main Orchestrator
Identifies high-velocity movers and categorizes them using AI

Two Modes:
- Mode 1: Auto-scan universe for 20% movers
- Mode 2: Analyze user-provided tickers
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict

from data_fetcher import get_high_velocity_movers, UNIVERSE_STOCKS_ONLY, load_precomputed_movers, fetch_stock_data, calculate_5day_change
from theme_analyzer import analyze_all_movers
from config import Config


def save_results(movers: List[Dict], total_scanned: int = None, output_dir: str = "themes") -> str:
    """
    Save analysis results to daily JSON file

    Args:
        movers: List of analyzed movers with category and summary
        total_scanned: Number of tickers scanned (optional)
        output_dir: Directory to save results (default: themes)

    Returns:
        Path to saved file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with today's date
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}_movers.json"
    filepath = os.path.join(output_dir, filename)

    # Prepare output data
    output_data = {
        "date": today,
        "total_tickers_scanned": total_scanned or len(UNIVERSE_STOCKS_ONLY),
        "movers_found": len(movers),
        "movers": movers
    }

    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return filepath


def validate_user_tickers(tickers: List[str]) -> List[Dict]:
    """
    Validate user-provided tickers and check if they are high-velocity movers

    Args:
        tickers: List of ticker symbols provided by user

    Returns:
        List of validated movers with price data
    """
    print(f"\n[VALIDATE] Checking {len(tickers)} tickers for 5-day performance...\n")

    movers = []
    for idx, ticker in enumerate(tickers, 1):
        ticker = ticker.strip().upper()
        print(f"[{idx}/{len(tickers)}] Checking {ticker}...", end='\r')

        df = fetch_stock_data(ticker)
        if df is None:
            print(f"\n[!] {ticker}: Unable to fetch data")
            continue

        change_pct = calculate_5day_change(df)
        if change_pct is None:
            print(f"\n[!] {ticker}: Insufficient data")
            continue

        current_price = df['Close'].iloc[-1]
        price_5d_ago = df['Close'].iloc[-6]

        mover = {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'price_5d_ago': round(price_5d_ago, 2),
            'move_pct': change_pct,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        movers.append(mover)

        status = "[MOVER]" if change_pct >= Config.VELOCITY_THRESHOLD else "       "
        print(f"\n[{idx}/{len(tickers)}] {ticker}: {change_pct:+.2f}% {status}")

    print(f"\n[>] Validated {len(movers)}/{len(tickers)} tickers")
    print(f"[>] Found {sum(1 for m in movers if m['move_pct'] >= Config.VELOCITY_THRESHOLD)} movers (>={Config.VELOCITY_THRESHOLD}%)")

    return movers


def print_summary(movers: List[Dict]):
    """
    Print a formatted summary of the results

    Args:
        movers: List of analyzed movers
    """
    print("\n" + "=" * 80)
    print("STOCK MARKET ENGINE - SUMMARY REPORT")
    print("=" * 80)

    if not movers:
        print("\n[!] No high-velocity movers found today.")
        return

    # Category breakdown
    category_counts = {}
    theme_counts = {}
    role_counts = {}

    for mover in movers:
        cat = mover.get('category', 'Unknown')
        theme = mover.get('primary_theme', 'Unknown')
        role = mover.get('ecosystem_role', 'Unknown')

        category_counts[cat] = category_counts.get(cat, 0) + 1
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
        role_counts[role] = role_counts.get(role, 0) + 1

    print(f"\n[>] Total Movers Found: {len(movers)}")

    print(f"\n[+] Category Breakdown:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    * {category}: {count}")

    print(f"\n[+] Primary Theme Breakdown:")
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    * {theme}: {count}")

    print(f"\n[+] Ecosystem Role Distribution:")
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    * {role}: {count}")

    print(f"\n{'='*80}")
    print("DETAILED RESULTS:")
    print("=" * 80)

    for idx, mover in enumerate(movers, 1):
        print(f"\n[{idx}] {mover['ticker']} - {mover.get('category', 'N/A')}")
        print(f"    Price: ${mover['price_5d_ago']} -> ${mover['current_price']} (+{mover['move_pct']}%)")
        print(f"    Category: {mover.get('category', 'N/A')}")
        print(f"    Primary Theme: {mover.get('primary_theme', 'N/A')}")
        print(f"    Sub-Niche: {mover.get('sub_niche', 'N/A')}")
        print(f"    Ecosystem Role: {mover.get('ecosystem_role', 'N/A')}")
        print(f"    Summary: {mover.get('summary', 'N/A')}")


def read_tickers_from_file(filename: str) -> List[str]:
    """
    Read tickers from a file

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

            # Split by newlines and commas
            lines = content.replace(',', '\n').split('\n')

            for line in lines:
                ticker = line.strip().upper()
                # Skip empty lines, comments, and header lines
                if not ticker or ticker.startswith('#') or ' ' in ticker:
                    continue
                # Only add if it looks like a ticker (alphanumeric, 1-6 chars typically)
                if ticker.replace('.', '').replace('-', '').isalnum():
                    if 1 <= len(ticker) <= 6:  # Most tickers are 1-6 chars
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


def select_mode() -> str:
    """
    Interactive mode selection

    Returns:
        '1' for auto-scan, '2' for manual input
    """
    print("\n" + "=" * 80)
    print("SELECT MODE")
    print("=" * 80)
    print("[1] Mode 1: Auto-scan universe for 20% movers")
    print("[2] Mode 2: Analyze user-provided tickers (manual or file)")
    print("=" * 80)

    while True:
        choice = input("\nEnter mode (1 or 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("[!] Invalid choice. Please enter 1 or 2.")


def main(mode: str = None, manual_tickers: List[str] = None):
    """
    Main execution pipeline

    Args:
        mode: '1' for auto-scan, '2' for manual, None for interactive
        manual_tickers: List of tickers for mode 2 (optional)
    """
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n{e}")
        print("\nPlease update your .env file with the required API keys.")
        return

    print("\n" + "=" * 80)
    print("STOCK MARKET ENGINE v2.0")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Threshold: >= {Config.VELOCITY_THRESHOLD}% gain in 5 trading days")
    print("=" * 80)

    # Mode selection
    if mode is None:
        mode = select_mode()

    # Step 1: Get movers based on mode
    print("\n" + "=" * 80)
    print("STEP 1: DATA ACQUISITION & FILTERING")
    print("=" * 80)

    total_scanned = None

    if mode == '1':
        # Try pre-computed scan first (instant), fall back to live scan
        precomputed = load_precomputed_movers()
        if precomputed:
            movers = precomputed["movers"]
            total_scanned = precomputed.get("universe_size")
            scan_date = precomputed.get("scan_date", "unknown")
            scan_time = precomputed.get("scan_time", "")
            print(f"\n[MODE 1] Loaded {len(movers)} pre-computed movers")
            print(f"  Scanned {total_scanned} tickers on {scan_date} at {scan_time}")
        else:
            print("\n[MODE 1] No pre-computed scan found. Run scan_universe.py first.")
            print("  Falling back to live scan of hardcoded list...")
            total_scanned = len(UNIVERSE_STOCKS_ONLY)
            movers = get_high_velocity_movers(
                tickers=UNIVERSE_STOCKS_ONLY,
                threshold=Config.VELOCITY_THRESHOLD
            )
    else:  # mode == '2'
        print(f"\n[MODE 2] Analyzing user-provided tickers...")
        if manual_tickers is None:
            print("\nOptions:")
            print("  [1] Enter tickers manually (comma-separated)")
            print("  [2] Upload from file (.txt or .csv)")

            input_choice = input("\nChoose option (1 or 2): ").strip()

            if input_choice == '1':
                ticker_input = input("\nEnter tickers (comma-separated): ").strip()
                manual_tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
            elif input_choice == '2':
                file_path = input("\nEnter file path: ").strip()
                # Remove quotes if present (Windows copy path adds quotes)
                file_path = file_path.strip('"').strip("'")
                manual_tickers = read_tickers_from_file(file_path)
            else:
                print("[!] Invalid choice. Exiting.")
                return

        if not manual_tickers:
            print("[!] No tickers provided. Exiting.")
            return

        print(f"\n[>] Processing {len(manual_tickers)} tickers: {', '.join(manual_tickers[:10])}")
        if len(manual_tickers) > 10:
            print(f"    ... and {len(manual_tickers) - 10} more")

        movers = validate_user_tickers(manual_tickers)

    if not movers:
        print("\n[OK] Analysis complete. No movers found.")
        filepath = save_results([], total_scanned=total_scanned)
        print(f"\n[SAVED] Results saved to: {filepath}")
        return

    # Step 2: Analyze with AI (Claude + Gemini)
    print("\n" + "=" * 80)
    print("STEP 2: AI ANALYSIS (CLAUDE + GEMINI)")
    print("=" * 80)

    analyzed_movers = analyze_all_movers(movers)

    # Step 3: Save results
    print("\n" + "=" * 80)
    print("STEP 3: SAVING RESULTS")
    print("=" * 80)

    filepath = save_results(analyzed_movers, total_scanned=total_scanned)
    print(f"\n[SAVED] Results saved to: {filepath}")

    # Step 4: Print summary
    print_summary(analyzed_movers)

    print("\n" + "=" * 80)
    print("[OK] STOCK MARKET ENGINE - EXECUTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        # Support command-line arguments
        # Usage: python main.py [mode] [tickers_or_file]
        # Example: python main.py 1                      (auto-scan)
        # Example: python main.py 2 NVDA,TSLA,AAPL       (manual tickers)
        # Example: python main.py 2 tickers.txt          (file upload)

        mode = None
        manual_tickers = None

        if len(sys.argv) > 1:
            mode = sys.argv[1]
            if mode == '2' and len(sys.argv) > 2:
                input_arg = sys.argv[2].strip()

                # Check if it's a file path
                if os.path.isfile(input_arg):
                    print(f"[>] Reading tickers from file: {input_arg}")
                    manual_tickers = read_tickers_from_file(input_arg)
                else:
                    # Treat as comma-separated tickers
                    manual_tickers = [t.strip().upper() for t in input_arg.split(',')]

        main(mode=mode, manual_tickers=manual_tickers)

    except KeyboardInterrupt:
        print("\n\n[!] Execution interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {str(e)}")
        raise
