# Redirect — real code lives in jobs/scan_universe.py
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from jobs.scan_universe import scan_full_universe
from prattern.config import Config

if __name__ == "__main__":
    threshold = Config.VELOCITY_THRESHOLD
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
        except ValueError:
            pass
    scan_full_universe(threshold=threshold)
