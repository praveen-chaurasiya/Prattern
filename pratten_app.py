# Redirect — real code lives in gui/pratten_app.py
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gui.pratten_app import PratternApp

if __name__ == "__main__":
    app = PratternApp()
    app.mainloop()
