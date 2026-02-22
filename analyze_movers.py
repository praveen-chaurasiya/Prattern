# Redirect — real code lives in jobs/analyze_movers.py
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from jobs.analyze_movers import main

if __name__ == "__main__":
    main()
