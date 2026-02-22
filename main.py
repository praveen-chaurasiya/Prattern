# Redirect — real code lives in cli/main.py
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from cli.main import main, select_mode, print_summary
from prattern.core.file_io import read_tickers_from_file

if __name__ == "__main__":
    try:
        mode = None
        manual_tickers = None

        if len(sys.argv) > 1:
            mode = sys.argv[1]
            if mode == '2' and len(sys.argv) > 2:
                input_arg = sys.argv[2].strip()
                if os.path.isfile(input_arg):
                    manual_tickers = read_tickers_from_file(input_arg)
                else:
                    manual_tickers = [t.strip().upper() for t in input_arg.split(',')]

        main(mode=mode, manual_tickers=manual_tickers)

    except KeyboardInterrupt:
        print("\n\n[!] Execution interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {str(e)}")
        raise
