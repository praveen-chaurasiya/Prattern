"""
Analyze Movers -- Pre-compute AI analysis for daily movers.
Loads data/daily_movers.json, runs analyze_all_movers(), saves to data/daily_analyzed.json.
"""

import json
import os
import sys
import time
from datetime import datetime

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prattern.data.precomputed import load_precomputed_movers
from prattern.features.analyzer.orchestrator import analyze_all_movers

DAILY_ANALYZED_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "daily_analyzed.json")
)


def main():
    print("=" * 80)
    print("ANALYZE MOVERS -- Pre-computing AI analysis")
    print("=" * 80)

    precomputed = load_precomputed_movers()
    if not precomputed:
        print("[ERROR] No daily_movers.json found. Run scan_universe.py first.")
        return

    movers = precomputed["movers"]
    scan_date = precomputed.get("scan_date", "unknown")
    print(f"[OK] Loaded {len(movers)} movers from scan ({scan_date})")

    if not movers:
        print("[OK] No movers to analyze.")
        return

    start = time.time()

    def on_progress(event):
        stage = event.get("stage", "")
        current = event.get("current", 0)
        total = event.get("total", 0)
        detail = event.get("detail", "")
        print(f"  [PROGRESS] {stage} {current}/{total} -- {detail}")

    analyzed = analyze_all_movers(movers, on_progress=on_progress)

    duration = round(time.time() - start, 1)

    os.makedirs(os.path.dirname(DAILY_ANALYZED_PATH), exist_ok=True)

    output = {
        "scan_date": precomputed.get("scan_date"),
        "scan_time": precomputed.get("scan_time"),
        "universe_size": precomputed.get("universe_size"),
        "threshold": precomputed.get("threshold"),
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis_duration_seconds": duration,
        "movers_count": len(analyzed),
        "movers": analyzed,
    }

    with open(DAILY_ANALYZED_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"[OK] Analysis saved to {DAILY_ANALYZED_PATH}")
    print(f"[OK] {len(analyzed)} movers analyzed in {duration}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
