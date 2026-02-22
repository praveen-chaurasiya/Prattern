"""
Stock Market Engine - CLI Entry Point
"""

import os
import sys

# Ensure the project root is on sys.path so `prattern` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from typing import List, Dict

from prattern.config import Config
from prattern.core.ticker_lists import UNIVERSE_STOCKS_ONLY
from prattern.core.file_io import read_tickers_from_file, save_results
from prattern.core.validation import validate_user_tickers
from prattern.data import get_high_velocity_movers, load_precomputed_movers, load_precomputed_analysis
from prattern.analysis import analyze_all_movers


def print_summary(movers: List[Dict]):
    """Print a formatted summary of the results."""
    print("\n" + "=" * 80)
    print("STOCK MARKET ENGINE - SUMMARY REPORT")
    print("=" * 80)

    if not movers:
        print("\n[!] No high-velocity movers found today.")
        return

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


def select_mode() -> str:
    """Interactive mode selection."""
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
    """Main execution pipeline."""
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

    if mode is None:
        mode = select_mode()

    print("\n" + "=" * 80)
    print("STEP 1: DATA ACQUISITION & FILTERING")
    print("=" * 80)

    total_scanned = None

    if mode == '1':
        # Try pre-analyzed data first (instant, no AI needed)
        pre_analyzed = load_precomputed_analysis()
        if pre_analyzed:
            analyzed_movers = pre_analyzed["movers"]
            total_scanned = pre_analyzed.get("universe_size")
            scan_date = pre_analyzed.get("scan_date", "unknown")
            analysis_time = pre_analyzed.get("analysis_time", "")
            print(f"\n[MODE 1] [PRE-ANALYZED] Loaded {len(analyzed_movers)} analyzed movers")
            print(f"  Scanned {total_scanned} tickers on {scan_date}")
            print(f"  Analysis completed at {analysis_time}")

            if not analyzed_movers:
                print("\n[OK] Analysis complete. No movers found.")
                filepath = save_results([], total_scanned=total_scanned)
                print(f"\n[SAVED] Results saved to: {filepath}")
                return

            filepath = save_results(analyzed_movers, total_scanned=total_scanned)
            print(f"\n[SAVED] Results saved to: {filepath}")
            print_summary(analyzed_movers)
            print("\n" + "=" * 80)
            print("[OK] STOCK MARKET ENGINE - EXECUTION COMPLETE (pre-analyzed)")
            print("=" * 80)
            return

        # Fall back to pre-computed movers (needs live AI)
        precomputed = load_precomputed_movers()
        if precomputed:
            movers = precomputed["movers"]
            total_scanned = precomputed.get("universe_size")
            scan_date = precomputed.get("scan_date", "unknown")
            scan_time = precomputed.get("scan_time", "")
            print(f"\n[MODE 1] Loaded {len(movers)} pre-computed movers (no pre-analysis found)")
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

    print("\n" + "=" * 80)
    print("STEP 2: AI ANALYSIS (CLAUDE + GEMINI)")
    print("=" * 80)

    analyzed_movers = analyze_all_movers(movers)

    print("\n" + "=" * 80)
    print("STEP 3: SAVING RESULTS")
    print("=" * 80)

    filepath = save_results(analyzed_movers, total_scanned=total_scanned)
    print(f"\n[SAVED] Results saved to: {filepath}")

    print_summary(analyzed_movers)

    print("\n" + "=" * 80)
    print("[OK] STOCK MARKET ENGINE - EXECUTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        mode = None
        manual_tickers = None

        if len(sys.argv) > 1:
            mode = sys.argv[1]
            if mode == '2' and len(sys.argv) > 2:
                input_arg = sys.argv[2].strip()

                if os.path.isfile(input_arg):
                    print(f"[>] Reading tickers from file: {input_arg}")
                    manual_tickers = read_tickers_from_file(input_arg)
                else:
                    manual_tickers = [t.strip().upper() for t in input_arg.split(',')]

        main(mode=mode, manual_tickers=manual_tickers)

    except KeyboardInterrupt:
        print("\n\n[!] Execution interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {str(e)}")
        raise
