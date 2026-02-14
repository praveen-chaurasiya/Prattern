"""
Pratten GUI App v2.0
Stock Market Engine with dual-mode support
"""

import os
os.environ["POLARS_SKIP_CPU_CHECK"] = "1"  # Fix for older CPUs

import customtkinter as ctk
import threading
from typing import List
from config import Config
from data_fetcher import get_high_velocity_movers, load_precomputed_movers, UNIVERSE_STOCKS_ONLY
from main import validate_user_tickers
from theme_analyzer import analyze_all_movers

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PratternApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Validate API keys
        try:
            Config.validate()
        except ValueError as e:
            print(f"Configuration Error: {e}")

        self.title("Pratten Stock Engine v2.0")
        self.geometry("1000x700")

        # Mode selection
        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.mode_frame, text="Select Mode:", font=("Arial", 16, "bold")).pack(pady=10)

        self.mode_var = ctk.StringVar(value="1")

        self.mode1_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Mode 1: Auto-scan universe for 20% movers",
            variable=self.mode_var,
            value="1",
            command=self.on_mode_change
        )
        self.mode1_radio.pack(pady=5)

        self.mode2_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Mode 2: Analyze custom tickers",
            variable=self.mode_var,
            value="2",
            command=self.on_mode_change
        )
        self.mode2_radio.pack(pady=5)

        # Input frame (for Mode 2)
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.input_frame, text="Enter Tickers (comma-separated) OR Upload File:", font=("Arial", 12)).pack(pady=5)

        # Entry + Browse button in horizontal layout
        self.entry_frame = ctk.CTkFrame(self.input_frame)
        self.entry_frame.pack(pady=5)

        self.ticker_entry = ctk.CTkEntry(self.entry_frame, width=500, placeholder_text="NVDA, TSLA, AAPL, META")
        self.ticker_entry.pack(side="left", padx=5)
        self.ticker_entry.configure(state="disabled")  # Disabled by default (Mode 1)

        self.browse_btn = ctk.CTkButton(
            self.entry_frame,
            text="📁 Browse File",
            command=self.browse_file,
            width=120,
            state="disabled"  # Disabled by default (Mode 1)
        )
        self.browse_btn.pack(side="left", padx=5)

        self.file_label = ctk.CTkLabel(self.input_frame, text="", font=("Arial", 10), text_color="gray")
        self.file_label.pack(pady=2)

        # Price filter frame (for Mode 1)
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.filter_frame, text="Min Price Filter:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))

        self.price_filter_var = ctk.StringVar(value="> $5")
        self.price_filter_menu = ctk.CTkOptionMenu(
            self.filter_frame,
            variable=self.price_filter_var,
            values=["No filter", "> $1", "> $5", "> $10", "> $20", "Custom"],
            command=self.on_price_filter_change,
            width=120
        )
        self.price_filter_menu.pack(side="left", padx=5)

        self.custom_price_entry = ctk.CTkEntry(
            self.filter_frame, width=80,
            placeholder_text="e.g. 3"
        )
        # Hidden by default, shown when "Custom" is selected
        self.custom_price_label = ctk.CTkLabel(self.filter_frame, text="$", font=("Arial", 12))

        # Run button
        self.run_btn = ctk.CTkButton(
            self,
            text="🚀 Run Analysis",
            command=self.run_analysis_thread,
            font=("Arial", 14, "bold"),
            height=40
        )
        self.run_btn.pack(pady=20)

        # Progress label
        self.progress_label = ctk.CTkLabel(self, text="", font=("Arial", 11))
        self.progress_label.pack(pady=5)

        # Output textbox
        self.output = ctk.CTkTextbox(self, width=950, height=400, font=("Consolas", 11))
        self.output.pack(pady=10, padx=20)

    def on_mode_change(self):
        """Handle mode radio button changes"""
        if self.mode_var.get() == "1":
            self.ticker_entry.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            self.file_label.configure(text="")
            self.filter_frame.pack(pady=10, padx=20, fill="x", before=self.run_btn)
        else:
            self.ticker_entry.configure(state="normal")
            self.browse_btn.configure(state="normal")
            self.filter_frame.pack_forget()

    def on_price_filter_change(self, choice):
        """Show/hide custom price entry based on dropdown selection"""
        if choice == "Custom":
            self.custom_price_label.pack(side="left", padx=(10, 0))
            self.custom_price_entry.pack(side="left", padx=(2, 5))
        else:
            self.custom_price_label.pack_forget()
            self.custom_price_entry.pack_forget()

    def get_min_price(self) -> float:
        """Get the minimum price filter value from the UI"""
        choice = self.price_filter_var.get()
        if choice == "No filter":
            return 0.0
        elif choice == "Custom":
            try:
                return float(self.custom_price_entry.get().strip())
            except (ValueError, AttributeError):
                return 5.0  # Default if invalid input
        else:
            # Parse "> $5" format
            return float(choice.replace(">", "").replace("$", "").strip())

    def browse_file(self):
        """Open file dialog to select ticker list file"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Select Ticker List File",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                # Read tickers from file
                tickers = self.read_tickers_from_file(filename)

                if tickers:
                    # Display tickers in entry field
                    self.ticker_entry.delete(0, "end")
                    self.ticker_entry.insert(0, ", ".join(tickers))

                    # Show success message
                    self.file_label.configure(
                        text=f"[OK] Loaded {len(tickers)} tickers from: {filename.split('/')[-1]}",
                        text_color="green"
                    )
                else:
                    self.file_label.configure(
                        text="[!] No tickers found in file",
                        text_color="orange"
                    )

            except Exception as e:
                self.file_label.configure(
                    text=f"[ERROR] Reading file: {str(e)[:30]}",
                    text_color="red"
                )

    def read_tickers_from_file(self, filename: str) -> List[str]:
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

        return unique_tickers

    def run_analysis_thread(self):
        """Run analysis in separate thread to prevent GUI freezing"""
        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()

    def run_analysis(self):
        """Main analysis logic"""
        try:
            # Disable button during execution
            self.run_btn.configure(state="disabled", text="⏳ Running...")
            self.output.delete("1.0", "end")
            self.log("=" * 80)
            self.log("STOCK MARKET ENGINE - ANALYSIS STARTED")
            self.log("=" * 80)

            mode = self.mode_var.get()

            # Step 1: Get movers
            if mode == "1":
                min_price = self.get_min_price()

                # Try pre-computed scan first (instant), fall back to live scan
                precomputed = load_precomputed_movers()
                if precomputed:
                    movers = precomputed["movers"]
                    scan_date = precomputed.get("scan_date", "unknown")
                    scan_time = precomputed.get("scan_time", "")
                    universe_size = precomputed.get("universe_size", "?")
                    self.log(f"\n[MODE 1] Loaded {len(movers)} pre-computed movers")
                    self.log(f"  Scanned {universe_size} tickers on {scan_date} at {scan_time}")

                    # Apply price filter
                    if min_price > 0:
                        before = len(movers)
                        movers = [m for m in movers if m["current_price"] >= min_price]
                        self.log(f"  Price filter: > ${min_price:.2f} ({before} -> {len(movers)} movers)")

                    self.progress_label.configure(text=f"Loaded {len(movers)} movers from scan ({scan_date})")
                else:
                    self.log("\n[MODE 1] No pre-computed scan found. Run scan_universe.py first.")
                    self.log("  Falling back to live scan of hardcoded list...")
                    self.progress_label.configure(text=f"Live scanning {len(UNIVERSE_STOCKS_ONLY)} tickers...")
                    movers = get_high_velocity_movers(
                        tickers=UNIVERSE_STOCKS_ONLY,
                        threshold=Config.VELOCITY_THRESHOLD
                    )
                    if min_price > 0:
                        movers = [m for m in movers if m["current_price"] >= min_price]
            else:
                ticker_input = self.ticker_entry.get().strip()
                if not ticker_input:
                    self.log("\n[ERROR] No tickers entered!")
                    return

                tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
                self.log(f"\n[MODE 2] Analyzing {len(tickers)} tickers: {', '.join(tickers)}")
                self.progress_label.configure(text=f"Validating {len(tickers)} tickers...")
                movers = validate_user_tickers(tickers)

            if not movers:
                self.log("\n[!] No movers found matching criteria.")
                self.progress_label.configure(text="No movers found")
                return

            self.log(f"\n[✓] Found {len(movers)} movers!")

            # Step 2: AI Analysis
            self.log("\n" + "=" * 80)
            self.log("AI ANALYSIS (Gemini + Claude Fallback)")
            self.log("=" * 80)
            self.progress_label.configure(text=f"Analyzing {len(movers)} movers with AI...")

            analyzed_movers = analyze_all_movers(movers)

            # Step 3: Display results
            self.log("\n" + "=" * 80)
            self.log("RESULTS")
            self.log("=" * 80)

            # Create formatted table with enhanced theme data
            self.log(f"\n{'#':<4} {'TICKER':<8} {'MOVE%':<8} {'CATEGORY':<20} {'PRIMARY THEME':<25} {'SUB-NICHE':<30} {'ROLE':<15}")
            self.log("-" * 130)

            for idx, mover in enumerate(analyzed_movers, 1):
                self.log(
                    f"{idx:<4} "
                    f"{mover['ticker']:<8} "
                    f"{mover['move_pct']:+.2f}{'':5} "
                    f"{mover.get('category', 'N/A'):<20} "
                    f"{mover.get('primary_theme', 'N/A'):<25} "
                    f"{mover.get('sub_niche', 'N/A'):<30} "
                    f"{mover.get('ecosystem_role', 'N/A'):<15}"
                )

            # Theme breakdown
            self.log("\n" + "=" * 130)
            self.log("THEME BREAKDOWN")
            self.log("=" * 130)

            # Primary theme counts
            theme_counts = {}
            for mover in analyzed_movers:
                theme = mover.get('primary_theme', 'Unknown')
                theme_counts[theme] = theme_counts.get(theme, 0) + 1

            self.log("\nPrimary Themes:")
            for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
                self.log(f"  {theme}: {count}")

            # Ecosystem role distribution
            role_counts = {}
            for mover in analyzed_movers:
                role = mover.get('ecosystem_role', 'Unknown')
                role_counts[role] = role_counts.get(role, 0) + 1

            self.log("\nEcosystem Roles:")
            for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                self.log(f"  {role}: {count}")

            # Top sub-niches
            niche_counts = {}
            for mover in analyzed_movers:
                niche = mover.get('sub_niche', 'Unknown')
                if niche != 'Unknown':
                    niche_counts[niche] = niche_counts.get(niche, 0) + 1

            if niche_counts:
                self.log("\nTop Sub-Niches:")
                for niche, count in sorted(niche_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    self.log(f"  {niche}: {count}")

            self.log("\n" + "=" * 80)
            self.log("[✓] ANALYSIS COMPLETE!")
            self.log("=" * 80)

            self.progress_label.configure(text=f"✓ Analysis complete! Found {len(analyzed_movers)} movers")

        except Exception as e:
            self.log(f"\n[ERROR] {str(e)}")
            self.progress_label.configure(text=f"Error: {str(e)}")

        finally:
            self.run_btn.configure(state="normal", text="🚀 Run Analysis")

    def log(self, message: str):
        """Thread-safe logging to output textbox"""
        self.output.insert("end", message + "\n")
        self.output.see("end")
        self.update()


if __name__ == "__main__":
    app = PratternApp()
    app.mainloop()