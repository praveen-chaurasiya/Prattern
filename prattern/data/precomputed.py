"""Load pre-computed JSON data files (movers + analyzed movers)."""

import json
import os
from datetime import datetime
from typing import Dict, Optional

DAILY_MOVERS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "daily_movers.json")
DAILY_ANALYZED_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "daily_analyzed.json")


def load_precomputed_movers() -> Optional[Dict]:
    """
    Load pre-computed movers from data/daily_movers.json (created by scan_universe.py).
    Returns the full result dict if it exists, otherwise None.
    """
    path = os.path.normpath(DAILY_MOVERS_PATH)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
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


def load_precomputed_analysis() -> Optional[Dict]:
    """
    Load pre-computed analyzed movers from data/daily_analyzed.json
    (created by analyze_movers.py). Returns the full result dict if it exists,
    otherwise None. Caller decides whether to accept stale data.
    """
    path = os.path.normpath(DAILY_ANALYZED_PATH)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            data = json.load(f)

        scan_date = data.get("scan_date", "")
        today = datetime.now().strftime("%Y-%m-%d")

        if scan_date == today:
            return data
        else:
            print(f"[!] Pre-computed analysis is from {scan_date}, not today ({today})")
            return data  # Still return stale data — let caller decide
    except (json.JSONDecodeError, KeyError):
        return None
