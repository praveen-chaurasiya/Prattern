"""
Pratten GUI App v3.0
Stock Market Engine - Modern Dashboard Interface
"""

import os
os.environ["POLARS_SKIP_CPU_CHECK"] = "1"  # Fix for older CPUs

import sys

# Ensure the project root is on sys.path so `prattern` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import customtkinter as ctk
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Optional

from prattern.config import Config
from prattern.core.ticker_lists import UNIVERSE_STOCKS_ONLY
from prattern.core.file_io import read_tickers_from_file
from prattern.core.validation import validate_user_tickers
from prattern.data import get_high_velocity_movers, load_precomputed_movers, load_precomputed_analysis
from prattern.analysis import analyze_all_movers
from prattern.features.theme_tracker.db import (
    load_theme_db, create_theme, delete_theme,
    add_ticker_to_theme, remove_ticker_from_theme,
)
from prattern.features.theme_tracker.service import get_all_themes_performance

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_sidebar": "#0f3460",
    "bg_row": "#1e2a3a",
    "bg_row_hover": "#263545",
    "accent_blue": "#3282b8",
    "accent_green": "#00b894",
    "accent_red": "#e74c3c",
    "accent_orange": "#f39c12",
    "text_primary": "#ecf0f1",
    "text_secondary": "#95a5a6",
    "text_muted": "#636e72",
    "border": "#2d3436",
}

CATEGORY_COLORS = {
    "Earnings Beat": "#2ecc71",
    "FDA Approval": "#3498db",
    "M&A/Rumors": "#9b59b6",
    "Sector Momentum": "#f39c12",
    "Macro/Short Squeeze": "#e74c3c",
    "Unknown": "#95a5a6",
}

ROLE_COLORS = {
    "Producer": "#1abc9c",
    "Supplier": "#e67e22",
    "Integrator": "#9b59b6",
    "Platform": "#3498db",
}


# ---------------------------------------------------------------------------
# StatCard — summary metric box
# ---------------------------------------------------------------------------
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str = "--",
                 fg_color: str = COLORS["bg_card"], value_color: str = COLORS["text_primary"],
                 **kwargs):
        super().__init__(parent, fg_color=fg_color, corner_radius=10, **kwargs)
        self.title_label = ctk.CTkLabel(
            self, text=title, font=("Arial", 10), text_color=COLORS["text_secondary"]
        )
        self.title_label.pack(pady=(10, 2), padx=12)
        self.value_label = ctk.CTkLabel(
            self, text=value, font=("Arial", 18, "bold"), text_color=value_color
        )
        self.value_label.pack(pady=(0, 10), padx=12)

    def set_value(self, value: str, color: str = None):
        self.value_label.configure(text=value)
        if color:
            self.value_label.configure(text_color=color)


# ---------------------------------------------------------------------------
# TableRow — single row in the table view
# ---------------------------------------------------------------------------
class TableRow(ctk.CTkFrame):
    COL_WIDTHS = [40, 70, 80, 80, 150, 180, 200, 110]

    def __init__(self, parent, index: int, mover: dict, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_row"], corner_radius=4,
                         height=32, **kwargs)
        self.pack_propagate(False)
        self.configure(height=32)

        cat_color = CATEGORY_COLORS.get(mover.get("category", "Unknown"), "#95a5a6")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=6, pady=2)

        fields = [
            (str(index), COLORS["text_muted"], ("Arial", 10)),
            (mover["ticker"], COLORS["text_primary"], ("Arial", 11, "bold")),
            (f"+{mover['move_pct']:.1f}%", "#2ecc71", ("Arial", 11, "bold")),
            (f"${mover['current_price']:.2f}", COLORS["text_secondary"], ("Arial", 10)),
            (mover.get("category", "N/A"), cat_color, ("Arial", 10, "bold")),
            (mover.get("primary_theme", "N/A"), COLORS["text_secondary"], ("Arial", 10)),
            (mover.get("sub_niche", "N/A"), COLORS["text_muted"], ("Arial", 9)),
            (mover.get("ecosystem_role", "N/A"),
             ROLE_COLORS.get(mover.get("ecosystem_role", ""), COLORS["text_muted"]),
             ("Arial", 10)),
        ]

        for i, (text, color, font) in enumerate(fields):
            lbl = ctk.CTkLabel(
                inner, text=text, font=font, text_color=color,
                width=self.COL_WIDTHS[i], anchor="w"
            )
            lbl.pack(side="left", padx=(0, 6))

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_row_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_row"]))


# ---------------------------------------------------------------------------
# MoverCard — expandable card in the cards view
# ---------------------------------------------------------------------------
class MoverCard(ctk.CTkFrame):
    def __init__(self, parent, mover: dict, **kwargs):
        cat_color = CATEGORY_COLORS.get(mover.get("category", "Unknown"), "#95a5a6")
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=10,
                         border_width=2, border_color=cat_color, **kwargs)
        self.mover = mover
        self.expanded = False

        # --- Header row (always visible) ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header, text=mover["ticker"],
            font=("Arial", 16, "bold"), text_color=COLORS["text_primary"]
        ).pack(side="left")

        move_color = "#2ecc71" if mover["move_pct"] > 0 else "#e74c3c"
        ctk.CTkLabel(
            header, text=f"+{mover['move_pct']:.1f}%",
            font=("Arial", 14, "bold"), text_color=move_color
        ).pack(side="left", padx=10)

        # Category badge
        badge = ctk.CTkFrame(header, fg_color=cat_color, corner_radius=6)
        badge.pack(side="right")
        ctk.CTkLabel(
            badge, text=mover.get("category", "Unknown"),
            font=("Arial", 10, "bold"), text_color="white"
        ).pack(padx=8, pady=2)

        # --- Meta row: theme + role ---
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(
            meta, text=mover.get("primary_theme", ""),
            font=("Arial", 11), text_color=COLORS["text_secondary"]
        ).pack(side="left")

        role = mover.get("ecosystem_role", "")
        role_color = ROLE_COLORS.get(role, COLORS["text_muted"])
        ctk.CTkLabel(
            meta, text=role, font=("Arial", 10), text_color=role_color
        ).pack(side="right")

        # --- Price info ---
        price_frame = ctk.CTkFrame(self, fg_color="transparent")
        price_frame.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(
            price_frame,
            text=f"${mover['current_price']:.2f}  (from ${mover.get('price_5d_ago', 0):.2f})",
            font=("Arial", 10), text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Expand hint
        self.expand_hint = ctk.CTkLabel(
            price_frame, text="[click to expand]",
            font=("Arial", 9), text_color=COLORS["text_muted"]
        )
        self.expand_hint.pack(side="right")

        # --- Detail section (hidden by default) ---
        self.detail_frame = ctk.CTkFrame(self, fg_color="#0d1b2a", corner_radius=6)

        if mover.get("summary"):
            ctk.CTkLabel(
                self.detail_frame, text=mover["summary"],
                font=("Arial", 11), wraplength=380,
                text_color="#bdc3c7", justify="left"
            ).pack(padx=10, pady=(8, 4), anchor="w")

        for hl in mover.get("headlines", []):
            ctk.CTkLabel(
                self.detail_frame, text=f"  - {hl}",
                font=("Arial", 10), text_color="#7f8c8d",
                wraplength=360, justify="left"
            ).pack(padx=10, pady=1, anchor="w")

        sub = mover.get("sub_niche", "N/A")
        micro = mover.get("micro_theme", "N/A")
        ctk.CTkLabel(
            self.detail_frame,
            text=f"Sub-niche: {sub}  |  Micro: {micro}",
            font=("Arial", 10), text_color=COLORS["text_muted"]
        ).pack(padx=10, pady=(4, 8), anchor="w")

        # Click to expand/collapse — bind on all children
        self._bind_recursive(self, "<Button-1>", self._toggle)

    def _bind_recursive(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            if child != self.detail_frame:
                self._bind_recursive(child, event, callback)

    def _toggle(self, event=None):
        if self.expanded:
            self.detail_frame.pack_forget()
            self.expand_hint.configure(text="[click to expand]")
        else:
            self.detail_frame.pack(fill="x", padx=12, pady=(4, 10))
            self.expand_hint.configure(text="[click to collapse]")
        self.expanded = not self.expanded


# ---------------------------------------------------------------------------
# PratternApp — main application window
# ---------------------------------------------------------------------------
class PratternApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        try:
            Config.validate()
        except ValueError as e:
            print(f"Configuration Error: {e}")

        self.title("Pratten Stock Engine v3.0")
        self.geometry("1400x900")
        self.minsize(1200, 750)
        self.configure(fg_color=COLORS["bg_dark"])

        self.current_movers: List[Dict] = []
        self.current_metadata: Dict = {}

        # Two-column grid: sidebar (fixed 220) + main (stretch)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["bg_sidebar"], width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo
        ctk.CTkLabel(
            self.sidebar, text="PRATTERN",
            font=("Arial", 22, "bold"), text_color=COLORS["text_primary"]
        ).pack(pady=(20, 2))
        ctk.CTkLabel(
            self.sidebar, text="Stock Market Engine",
            font=("Arial", 11), text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 15))

        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=5)

        # Mode selection
        ctk.CTkLabel(
            self.sidebar, text="Analysis Mode",
            font=("Arial", 13, "bold"), text_color=COLORS["text_primary"]
        ).pack(pady=(10, 5))

        self.mode_var = ctk.StringVar(value="Auto-Scan")
        self.mode_segmented = ctk.CTkSegmentedButton(
            self.sidebar, values=["Auto-Scan", "Custom"],
            variable=self.mode_var, command=self._on_mode_change,
            font=("Arial", 11)
        )
        self.mode_segmented.pack(padx=15, pady=5, fill="x")

        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)

        # --- Filter section (Mode 1: Auto-Scan) ---
        self.filter_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.filter_section.pack(fill="x", padx=15)

        ctk.CTkLabel(
            self.filter_section, text="Min Price Filter",
            font=("Arial", 12, "bold"), text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 5))

        self.price_filter_var = ctk.StringVar(value="> $5")
        self.price_filter_menu = ctk.CTkOptionMenu(
            self.filter_section, variable=self.price_filter_var,
            values=["No filter", "> $1", "> $5", "> $10", "> $20", "Custom"],
            command=self._on_price_filter_change, width=180
        )
        self.price_filter_menu.pack(pady=5, anchor="w")

        self.custom_price_frame = ctk.CTkFrame(self.filter_section, fg_color="transparent")
        self.custom_price_entry = ctk.CTkEntry(
            self.custom_price_frame, width=100, placeholder_text="e.g. 3"
        )
        ctk.CTkLabel(
            self.custom_price_frame, text="$ min price",
            font=("Arial", 10), text_color=COLORS["text_muted"]
        ).pack(side="right", padx=5)
        self.custom_price_entry.pack(side="right")

        # --- Ticker section (Mode 2: Custom) ---
        self.ticker_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")

        ctk.CTkLabel(
            self.ticker_section, text="Enter Tickers",
            font=("Arial", 12, "bold"), text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 5))

        self.ticker_entry = ctk.CTkEntry(
            self.ticker_section, placeholder_text="NVDA, TSLA, AAPL", width=200
        )
        self.ticker_entry.pack(pady=3, fill="x")

        self.browse_btn = ctk.CTkButton(
            self.ticker_section, text="Browse File",
            command=self._browse_file, width=120, height=28,
            fg_color=COLORS["accent_blue"]
        )
        self.browse_btn.pack(pady=5, anchor="w")

        self.file_label = ctk.CTkLabel(
            self.ticker_section, text="",
            font=("Arial", 9), text_color=COLORS["text_muted"], wraplength=200
        )
        self.file_label.pack(anchor="w")

        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)

        # Run button
        self.run_btn = ctk.CTkButton(
            self.sidebar, text="Run Analysis",
            command=self._run_analysis_thread,
            font=("Arial", 14, "bold"), height=45,
            fg_color=COLORS["accent_green"], hover_color="#00a381"
        )
        self.run_btn.pack(padx=15, pady=5, fill="x")

        # Progress bar (hidden initially)
        self.progress_bar = ctk.CTkProgressBar(self.sidebar, mode="determinate", width=200)
        self.progress_bar.set(0)

        self.progress_stage_label = ctk.CTkLabel(
            self.sidebar, text="", font=("Arial", 10),
            text_color=COLORS["text_muted"], wraplength=200
        )
        self.progress_detail_label = ctk.CTkLabel(
            self.sidebar, text="", font=("Arial", 9),
            text_color=COLORS["text_muted"], wraplength=200
        )

    # ------------------------------------------------------------------
    # Main content area
    # ------------------------------------------------------------------
    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # tabs row stretches

        # --- Stale data banner (hidden by default) ---
        self.stale_banner = ctk.CTkFrame(self.main_frame, fg_color="#8B0000", corner_radius=8)
        self.stale_label = ctk.CTkLabel(
            self.stale_banner, text="", font=("Arial", 12, "bold"), text_color="white"
        )
        self.stale_label.pack(side="left", padx=10, pady=6)
        self.refresh_btn = ctk.CTkButton(
            self.stale_banner, text="Refresh Scan", width=120,
            fg_color="#cc3333", hover_color="#aa2222",
            command=self._refresh_scan_thread
        )
        self.refresh_btn.pack(side="right", padx=10, pady=6)

        # --- Summary stats bar ---
        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        for i in range(5):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        self.stat_movers = StatCard(self.stats_frame, "Total Movers")
        self.stat_movers.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.stat_top_theme = StatCard(self.stats_frame, "Top Theme")
        self.stat_top_theme.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.stat_avg_move = StatCard(self.stats_frame, "Avg Move %")
        self.stat_avg_move.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.stat_scan_date = StatCard(self.stats_frame, "Scan Date")
        self.stat_scan_date.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.stat_universe = StatCard(self.stats_frame, "Universe Size")
        self.stat_universe.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        # --- Tabview ---
        self.content_tabs = ctk.CTkTabview(
            self.main_frame, fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent_blue"],
        )
        self.content_tabs.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))

        self.tab_table = self.content_tabs.add("Table")
        self.tab_cards = self.content_tabs.add("Cards")
        self.tab_charts = self.content_tabs.add("Charts")
        self.tab_themes = self.content_tabs.add("Theme Tracker")
        self.tab_log = self.content_tabs.add("Log")

        # Table tab setup
        self.tab_table.grid_columnconfigure(0, weight=1)
        self.tab_table.grid_rowconfigure(1, weight=1)

        self._build_table_header()

        self.table_scroll = ctk.CTkScrollableFrame(
            self.tab_table, fg_color=COLORS["bg_dark"]
        )
        self.table_scroll.grid(row=1, column=0, sticky="nsew")

        # Cards tab setup
        self.cards_scroll = ctk.CTkScrollableFrame(
            self.tab_cards, fg_color=COLORS["bg_dark"]
        )
        self.cards_scroll.pack(fill="both", expand=True)

        # Charts tab setup
        self.charts_scroll = ctk.CTkScrollableFrame(
            self.tab_charts, fg_color=COLORS["bg_dark"]
        )
        self.charts_scroll.pack(fill="both", expand=True)

        # Theme Tracker tab setup
        self._build_theme_tracker_tab()

        # Log tab setup
        self.log_output = ctk.CTkTextbox(
            self.tab_log, font=("Consolas", 11), fg_color=COLORS["bg_card"]
        )
        self.log_output.pack(fill="both", expand=True)

    def _build_table_header(self):
        header = ctk.CTkFrame(self.tab_table, fg_color=COLORS["bg_card"], corner_radius=4, height=30)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=6, pady=2)

        headers = ["#", "Ticker", "Move%", "Price", "Category", "Theme", "Sub-Niche", "Role"]
        widths = TableRow.COL_WIDTHS

        for text, w in zip(headers, widths):
            ctk.CTkLabel(
                inner, text=text, font=("Arial", 10, "bold"),
                text_color=COLORS["text_secondary"], width=w, anchor="w"
            ).pack(side="left", padx=(0, 6))

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------
    def _on_mode_change(self, value):
        if value == "Auto-Scan":
            self.ticker_section.pack_forget()
            self.filter_section.pack(fill="x", padx=15)
        else:
            self.filter_section.pack_forget()
            self.ticker_section.pack(fill="x", padx=15)

    def _on_price_filter_change(self, choice):
        if choice == "Custom":
            self.custom_price_frame.pack(pady=3, fill="x")
        else:
            self.custom_price_frame.pack_forget()

    def _get_min_price(self) -> float:
        choice = self.price_filter_var.get()
        if choice == "No filter":
            return 0.0
        elif choice == "Custom":
            try:
                return float(self.custom_price_entry.get().strip())
            except (ValueError, AttributeError):
                return 5.0
        else:
            return float(choice.replace(">", "").replace("$", "").strip())

    # ------------------------------------------------------------------
    # File browser
    # ------------------------------------------------------------------
    def _browse_file(self):
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Select Ticker List File",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if not filename:
            return

        try:
            tickers = read_tickers_from_file(filename)
            if tickers:
                self.ticker_entry.delete(0, "end")
                self.ticker_entry.insert(0, ", ".join(tickers))
                self.file_label.configure(
                    text=f"[OK] Loaded {len(tickers)} tickers from: {filename.split('/')[-1]}",
                    text_color="#2ecc71"
                )
            else:
                self.file_label.configure(
                    text="[!] No tickers found in file",
                    text_color=COLORS["accent_orange"]
                )
        except Exception as e:
            self.file_label.configure(
                text=f"[ERROR] {str(e)[:40]}",
                text_color=COLORS["accent_red"]
            )

    # ------------------------------------------------------------------
    # Analysis execution
    # ------------------------------------------------------------------
    def _run_analysis_thread(self):
        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()

    def _run_analysis(self):
        try:
            self.after(0, lambda: self.run_btn.configure(state="disabled", text="Running..."))
            self.after(0, lambda: self.progress_bar.pack(padx=15, pady=(10, 2), fill="x"))
            self.after(0, lambda: self.progress_stage_label.pack(padx=15))
            self.after(0, lambda: self.progress_detail_label.pack(padx=15))
            self.after(0, lambda: self.progress_bar.set(0))

            self.log("=" * 70)
            self.log("STOCK MARKET ENGINE - ANALYSIS STARTED")
            self.log("=" * 70)

            mode = self.mode_var.get()

            if mode == "Auto-Scan":
                self._run_mode_autoscan()
            else:
                self._run_mode_custom()

        except Exception as e:
            self.log(f"\n[ERROR] {str(e)}")
            self.after(0, lambda: self.progress_stage_label.configure(text=f"Error: {str(e)[:60]}"))

        finally:
            self.after(0, lambda: self.run_btn.configure(state="normal", text="Run Analysis"))
            self.after(0, lambda: self.progress_bar.pack_forget())
            self.after(0, lambda: self.progress_detail_label.pack_forget())

    def _run_mode_autoscan(self):
        min_price = self._get_min_price()

        # Try pre-analyzed data first (instant, no AI needed)
        pre_analyzed = load_precomputed_analysis()
        if pre_analyzed:
            movers = pre_analyzed["movers"]
            metadata = {
                "scan_date": pre_analyzed.get("scan_date", "unknown"),
                "scan_time": pre_analyzed.get("scan_time", ""),
                "universe_size": pre_analyzed.get("universe_size", "?"),
                "analysis_time": pre_analyzed.get("analysis_time", ""),
                "source": "pre-analyzed",
            }

            self.log(f"\n[MODE: Auto-Scan] [PRE-ANALYZED] Loaded {len(movers)} movers")
            self.log(f"  Scanned {metadata['universe_size']} tickers on {metadata['scan_date']} at {metadata['scan_time']}")

            self._handle_staleness(metadata["scan_date"])

            if min_price > 0:
                before = len(movers)
                movers = [m for m in movers if m["current_price"] >= min_price]
                self.log(f"  Price filter: > ${min_price:.2f} ({before} -> {len(movers)} movers)")

            if not movers:
                self.log("\n[!] No movers found matching criteria.")
                self.after(0, lambda: self.progress_stage_label.configure(text="No movers found"))
                return

            self.current_movers = movers
            self.current_metadata = metadata
            self.after(0, self._populate_all_views)
            self.log(f"\n[OK] {len(movers)} pre-analyzed movers loaded (no live AI needed)")
            self.after(0, lambda: self.progress_stage_label.configure(
                text=f"Loaded {len(movers)} pre-analyzed movers"))
            return

        # Fall back to pre-computed movers (needs live AI)
        precomputed = load_precomputed_movers()
        if precomputed:
            movers = precomputed["movers"]
            metadata = {
                "scan_date": precomputed.get("scan_date", "unknown"),
                "scan_time": precomputed.get("scan_time", ""),
                "universe_size": precomputed.get("universe_size", "?"),
                "source": "live-ai",
            }

            self.log(f"\n[MODE: Auto-Scan] Loaded {len(movers)} pre-computed movers (no pre-analysis)")
            self._handle_staleness(metadata["scan_date"])

            if min_price > 0:
                before = len(movers)
                movers = [m for m in movers if m["current_price"] >= min_price]
                self.log(f"  Price filter: > ${min_price:.2f} ({before} -> {len(movers)} movers)")
        else:
            self.log("\n[MODE: Auto-Scan] No pre-computed scan found. Using hardcoded list...")
            self.after(0, lambda: self.progress_stage_label.configure(
                text=f"Live scanning {len(UNIVERSE_STOCKS_ONLY)} tickers..."))
            movers = get_high_velocity_movers(
                tickers=UNIVERSE_STOCKS_ONLY,
                threshold=Config.VELOCITY_THRESHOLD
            )
            metadata = {"scan_date": datetime.now().strftime("%Y-%m-%d"), "source": "live-scan"}
            if min_price > 0:
                movers = [m for m in movers if m["current_price"] >= min_price]

        if not movers:
            self.log("\n[!] No movers found matching criteria.")
            return

        self._run_live_analysis(movers, metadata)

    def _run_mode_custom(self):
        ticker_input = self.ticker_entry.get().strip()
        if not ticker_input:
            self.log("\n[ERROR] No tickers entered!")
            return

        tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
        self.log(f"\n[MODE: Custom] Analyzing {len(tickers)} tickers: {', '.join(tickers)}")
        self.after(0, lambda: self.progress_stage_label.configure(
            text=f"Validating {len(tickers)} tickers..."))

        movers = validate_user_tickers(tickers)
        metadata = {"scan_date": datetime.now().strftime("%Y-%m-%d"), "source": "custom"}

        if not movers:
            self.log("\n[!] No valid movers found.")
            return

        self._run_live_analysis(movers, metadata)

    def _run_live_analysis(self, movers, metadata):
        self.log(f"\n[OK] Found {len(movers)} movers -- running AI analysis...")
        self.after(0, lambda: self.progress_stage_label.configure(
            text=f"Analyzing {len(movers)} movers with AI..."))

        analyzed = analyze_all_movers(movers, on_progress=self._on_analysis_progress)

        self.current_movers = analyzed
        self.current_metadata = metadata
        self.after(0, self._populate_all_views)
        self.log(f"\n[OK] Analysis complete! {len(analyzed)} movers classified.")
        self.after(0, lambda: self.progress_stage_label.configure(
            text=f"Analysis complete! {len(analyzed)} movers"))

    # ------------------------------------------------------------------
    # Progress callback (called from worker thread)
    # ------------------------------------------------------------------
    def _on_analysis_progress(self, event: dict):
        stage = event.get("stage", "")
        current = event.get("current", 0)
        total = event.get("total", 1)
        detail = event.get("detail", "")

        stage_labels = {
            "news": "Fetching headlines...",
            "primary_ai": "Running Gemini analysis...",
            "fallback_ai": "Claude fallback analysis...",
            "complete": "Analysis complete!",
        }

        def _update():
            self.progress_stage_label.configure(text=stage_labels.get(stage, stage))
            self.progress_detail_label.configure(text=detail)
            if stage == "complete":
                self.progress_bar.set(1.0)
            elif total > 0:
                self.progress_bar.set(current / total)

        self.after(0, _update)

    # ------------------------------------------------------------------
    # Staleness handling
    # ------------------------------------------------------------------
    def _handle_staleness(self, scan_date: str):
        today = datetime.now().strftime("%Y-%m-%d")
        if scan_date == today or scan_date == "unknown":
            self.after(0, lambda: self.stale_banner.grid_forget())
            return

        try:
            days_old = (datetime.now() - datetime.strptime(scan_date, "%Y-%m-%d")).days
        except ValueError:
            return

        if days_old <= 1:
            banner_color = "#d4a017"
        else:
            banner_color = "#8B0000"

        def _show():
            self.stale_banner.configure(fg_color=banner_color)
            self.stale_label.configure(text=f"Data is from {scan_date} -- {days_old} day(s) old")
            self.stale_banner.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))

        self.after(0, _show)
        self.log(f"  [!] Data is {days_old} day(s) old")

    # ------------------------------------------------------------------
    # Populate all views
    # ------------------------------------------------------------------
    def _populate_all_views(self):
        self._update_summary_stats()
        self._populate_table()
        self._populate_cards()
        self._build_charts()
        self.content_tabs.set("Table")

    def _update_summary_stats(self):
        movers = self.current_movers
        meta = self.current_metadata
        total = len(movers)

        self.stat_movers.set_value(str(total), color="#2ecc71" if total > 0 else COLORS["text_muted"])

        if movers:
            # Top theme
            theme_counts: Dict[str, int] = {}
            for m in movers:
                t = m.get("primary_theme", "Other")
                theme_counts[t] = theme_counts.get(t, 0) + 1
            top_theme = max(theme_counts, key=theme_counts.get)
            self.stat_top_theme.set_value(top_theme)

            # Average move
            avg_move = sum(m["move_pct"] for m in movers) / total
            self.stat_avg_move.set_value(f"+{avg_move:.1f}%", color="#2ecc71")
        else:
            self.stat_top_theme.set_value("--")
            self.stat_avg_move.set_value("--")

        # Scan date with staleness color
        scan_date = meta.get("scan_date", "N/A")
        today = datetime.now().strftime("%Y-%m-%d")
        if scan_date == today:
            self.stat_scan_date.set_value(scan_date, color="#2ecc71")
        elif scan_date not in ("N/A", "unknown"):
            try:
                days_old = (datetime.now() - datetime.strptime(scan_date, "%Y-%m-%d")).days
                color = "#e74c3c" if days_old > 2 else "#f39c12"
                self.stat_scan_date.set_value(f"{scan_date} ({days_old}d)", color=color)
            except ValueError:
                self.stat_scan_date.set_value(scan_date, color=COLORS["text_muted"])
        else:
            self.stat_scan_date.set_value("N/A", color=COLORS["text_muted"])

        # Universe size
        self.stat_universe.set_value(str(meta.get("universe_size", "?")))

    # ------------------------------------------------------------------
    # Table view
    # ------------------------------------------------------------------
    def _populate_table(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        for idx, mover in enumerate(self.current_movers, 1):
            row = TableRow(self.table_scroll, idx, mover)
            row.pack(fill="x", pady=1, padx=2)

    # ------------------------------------------------------------------
    # Cards view
    # ------------------------------------------------------------------
    def _populate_cards(self):
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        self.cards_scroll.grid_columnconfigure(0, weight=1)
        self.cards_scroll.grid_columnconfigure(1, weight=1)

        for i, mover in enumerate(self.current_movers):
            card = MoverCard(self.cards_scroll, mover)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=6, sticky="nsew")

    # ------------------------------------------------------------------
    # Charts view
    # ------------------------------------------------------------------
    def _build_charts(self):
        for widget in self.charts_scroll.winfo_children():
            widget.destroy()

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            plt.close("all")
        except ImportError:
            ctk.CTkLabel(
                self.charts_scroll, text="matplotlib not installed -- charts unavailable",
                font=("Arial", 12), text_color=COLORS["accent_red"]
            ).pack(pady=20)
            return

        movers = self.current_movers
        if not movers:
            return

        charts_container = ctk.CTkFrame(self.charts_scroll, fg_color="transparent")
        charts_container.pack(fill="both", expand=True)
        charts_container.grid_columnconfigure(0, weight=3)
        charts_container.grid_columnconfigure(1, weight=2)

        # Theme bar chart (left)
        theme_frame = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=10)
        theme_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self._build_theme_chart(theme_frame, movers)

        # Category donut chart (right)
        cat_frame = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=10)
        cat_frame.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        self._build_category_chart(cat_frame, movers)

        # Role distribution (below)
        role_frame = ctk.CTkFrame(charts_container, fg_color=COLORS["bg_card"], corner_radius=10)
        role_frame.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        self._build_role_chart(role_frame, movers)

    def _build_theme_chart(self, parent, movers):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        theme_counts: Dict[str, int] = {}
        for m in movers:
            t = m.get("primary_theme", "Other")
            theme_counts[t] = theme_counts.get(t, 0) + 1

        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        # Show top 15 themes max
        sorted_themes = sorted_themes[:15]
        themes = [t[0] for t in sorted_themes][::-1]
        counts = [t[1] for t in sorted_themes][::-1]

        fig, ax = plt.subplots(figsize=(7, max(3, len(themes) * 0.35)))
        fig.patch.set_facecolor("#16213e")
        ax.set_facecolor("#16213e")

        bars = ax.barh(themes, counts, color=COLORS["accent_blue"], edgecolor="none", height=0.6)
        ax.set_xlabel("Count", color=COLORS["text_primary"], fontsize=10)
        ax.set_title("Primary Theme Distribution", color=COLORS["text_primary"], fontsize=13, pad=12)
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(COLORS["border"])
        ax.spines["left"].set_color(COLORS["border"])

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                    str(count), va="center", color=COLORS["text_primary"], fontsize=9)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    def _build_category_chart(self, parent, movers):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        cat_counts: Dict[str, int] = {}
        for m in movers:
            c = m.get("category", "Unknown")
            cat_counts[c] = cat_counts.get(c, 0) + 1

        labels = list(cat_counts.keys())
        sizes = list(cat_counts.values())
        colors = [CATEGORY_COLORS.get(l, "#95a5a6") for l in labels]

        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor("#16213e")
        ax.set_facecolor("#16213e")

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct="%1.0f%%",
            startangle=90, pctdistance=0.75,
            wedgeprops=dict(width=0.4, edgecolor="#16213e", linewidth=2)
        )
        for t in texts:
            t.set_color(COLORS["text_primary"])
            t.set_fontsize(9)
        for t in autotexts:
            t.set_color("white")
            t.set_fontsize(8)
            t.set_fontweight("bold")
        ax.set_title("Category Distribution", color=COLORS["text_primary"], fontsize=13, pad=12)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    def _build_role_chart(self, parent, movers):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        role_counts: Dict[str, int] = {}
        for m in movers:
            r = m.get("ecosystem_role", "Unknown")
            role_counts[r] = role_counts.get(r, 0) + 1

        roles = list(role_counts.keys())
        counts = list(role_counts.values())
        colors = [ROLE_COLORS.get(r, COLORS["text_muted"]) for r in roles]

        fig, ax = plt.subplots(figsize=(8, 2.5))
        fig.patch.set_facecolor("#16213e")
        ax.set_facecolor("#16213e")

        bars = ax.bar(roles, counts, color=colors, edgecolor="none", width=0.5)
        ax.set_title("Ecosystem Roles", color=COLORS["text_primary"], fontsize=13, pad=12)
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(COLORS["border"])
        ax.spines["left"].set_color(COLORS["border"])

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(count), ha="center", color=COLORS["text_primary"], fontsize=10, fontweight="bold")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    # ------------------------------------------------------------------
    # Theme Tracker tab
    # ------------------------------------------------------------------
    def _build_theme_tracker_tab(self):
        self.tab_themes.grid_columnconfigure(0, weight=1)
        self.tab_themes.grid_rowconfigure(1, weight=1)

        # Header row: title + period selector
        header = ctk.CTkFrame(self.tab_themes, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))

        ctk.CTkLabel(
            header, text="Theme Performance",
            font=("Arial", 16, "bold"), text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.theme_period_var = ctk.StringVar(value="1w")
        self.theme_period_btn = ctk.CTkSegmentedButton(
            header, values=["today", "1w", "1m", "3m", "ytd"],
            variable=self.theme_period_var,
            command=lambda _: self._refresh_themes_thread()
        )
        self.theme_period_btn.pack(side="right")

        self.theme_loading_label = ctk.CTkLabel(
            header, text="", font=("Arial", 10), text_color=COLORS["text_muted"]
        )
        self.theme_loading_label.pack(side="right", padx=10)

        # Scrollable area for theme cards + admin
        self.theme_scroll = ctk.CTkScrollableFrame(
            self.tab_themes, fg_color=COLORS["bg_dark"]
        )
        self.theme_scroll.grid(row=1, column=0, sticky="nsew")

        # Container for theme cards inside scroll
        self.theme_cards_frame = ctk.CTkFrame(self.theme_scroll, fg_color="transparent")
        self.theme_cards_frame.pack(fill="x", expand=False)

        # Admin toggle button
        self.admin_visible = False
        self.admin_toggle_btn = ctk.CTkButton(
            self.theme_scroll, text="Show Admin Controls",
            command=self._toggle_admin_section,
            fg_color=COLORS["bg_card"], hover_color=COLORS["bg_row_hover"],
            height=30, font=("Arial", 11)
        )
        self.admin_toggle_btn.pack(fill="x", padx=5, pady=(10, 2))

        # Admin section (hidden by default)
        self.admin_section = ctk.CTkFrame(self.theme_scroll, fg_color=COLORS["bg_card"], corner_radius=8)
        self._build_admin_section()

        # Track theme data
        self.theme_data = []

    def _toggle_admin_section(self):
        if self.admin_visible:
            self.admin_section.pack_forget()
            self.admin_toggle_btn.configure(text="Show Admin Controls")
        else:
            self.admin_section.pack(fill="x", padx=5, pady=5)
            self.admin_toggle_btn.configure(text="Hide Admin Controls")
        self.admin_visible = not self.admin_visible

    def _build_admin_section(self):
        # Two-column layout: Create Theme (left) | AI Suggestions (right)
        self.admin_section.grid_columnconfigure(0, weight=1)
        self.admin_section.grid_columnconfigure(1, weight=2)

        # --- Left: Create Theme ---
        create_frame = ctk.CTkFrame(self.admin_section, fg_color="transparent")
        create_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            create_frame, text="Create Theme",
            font=("Arial", 13, "bold"), text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            create_frame, text="Name:", font=("Arial", 11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.create_theme_name = ctk.CTkEntry(
            create_frame, placeholder_text="e.g. AI Infrastructure", width=200
        )
        self.create_theme_name.pack(anchor="w", pady=2)

        ctk.CTkLabel(
            create_frame, text="Description:", font=("Arial", 11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(5, 0))
        self.create_theme_desc = ctk.CTkEntry(
            create_frame, placeholder_text="Optional description", width=200
        )
        self.create_theme_desc.pack(anchor="w", pady=2)

        self.create_theme_status = ctk.CTkLabel(
            create_frame, text="", font=("Arial", 10), text_color=COLORS["text_muted"]
        )
        self.create_theme_status.pack(anchor="w", pady=2)

        ctk.CTkButton(
            create_frame, text="Create Theme", width=120, height=30,
            fg_color=COLORS["accent_green"], hover_color="#00a381",
            command=self._create_theme_action
        ).pack(anchor="w", pady=5)

        # --- Right: AI Suggestions ---
        suggest_frame = ctk.CTkFrame(self.admin_section, fg_color="transparent")
        suggest_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        suggest_header = ctk.CTkFrame(suggest_frame, fg_color="transparent")
        suggest_header.pack(fill="x")

        ctk.CTkLabel(
            suggest_header, text="AI Suggestions",
            font=("Arial", 13, "bold"), text_color=COLORS["text_primary"]
        ).pack(side="left")

        ctk.CTkButton(
            suggest_header, text="Refresh", width=80, height=26,
            fg_color=COLORS["accent_blue"], hover_color="#2a6e9e",
            command=self._refresh_suggestions
        ).pack(side="right")

        self.suggestions_scroll = ctk.CTkScrollableFrame(
            suggest_frame, fg_color=COLORS["bg_dark"], height=200
        )
        self.suggestions_scroll.pack(fill="both", expand=True, pady=(5, 0))

    def _create_theme_action(self):
        name = self.create_theme_name.get().strip()
        desc = self.create_theme_desc.get().strip()
        if not name:
            self.create_theme_status.configure(
                text="[!] Name is required", text_color=COLORS["accent_red"]
            )
            return
        try:
            create_theme(name, desc)
            self.create_theme_status.configure(
                text=f"[OK] Created '{name}'", text_color=COLORS["accent_green"]
            )
            self.create_theme_name.delete(0, "end")
            self.create_theme_desc.delete(0, "end")
            self._refresh_themes_thread()
            self._refresh_suggestions()
        except ValueError as e:
            self.create_theme_status.configure(
                text=f"[!] {e}", text_color=COLORS["accent_red"]
            )

    def _refresh_suggestions(self):
        for widget in self.suggestions_scroll.winfo_children():
            widget.destroy()

        analysis = load_precomputed_analysis()
        if not analysis:
            ctk.CTkLabel(
                self.suggestions_scroll, text="No analyzed data found. Run the analyzer first.",
                font=("Arial", 11), text_color=COLORS["text_muted"]
            ).pack(pady=10)
            return

        db = load_theme_db()
        existing_tickers = set()
        for theme_data in db.get("themes", {}).values():
            existing_tickers.update(theme_data.get("tickers", []))

        theme_names = list(db.get("themes", {}).keys())

        # Group suggestions by primary_theme
        grouped = {}
        for mover in analysis.get("movers", []):
            ticker = mover.get("ticker", "")
            if ticker and ticker not in existing_tickers:
                theme_key = mover.get("primary_theme", "Other")
                grouped.setdefault(theme_key, []).append(mover)

        if not grouped:
            ctk.CTkLabel(
                self.suggestions_scroll, text="All tickers already assigned to themes.",
                font=("Arial", 11), text_color=COLORS["text_muted"]
            ).pack(pady=10)
            return

        for ai_theme, movers in sorted(grouped.items()):
            # Theme group header
            ctk.CTkLabel(
                self.suggestions_scroll, text=ai_theme,
                font=("Arial", 12, "bold"), text_color=COLORS["accent_blue"]
            ).pack(anchor="w", padx=5, pady=(8, 2))

            for mover in movers:
                self._build_suggestion_row(mover, theme_names)

    def _build_suggestion_row(self, mover, theme_names):
        row = ctk.CTkFrame(self.suggestions_scroll, fg_color=COLORS["bg_row"], corner_radius=4, height=32)
        row.pack(fill="x", padx=5, pady=1)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=6, pady=2)

        ticker = mover.get("ticker", "")
        move_pct = mover.get("move_pct", 0)
        category = mover.get("category", "N/A")

        ctk.CTkLabel(
            inner, text=ticker, font=("Arial", 11, "bold"),
            text_color=COLORS["text_primary"], width=60, anchor="w"
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            inner, text=f"+{move_pct:.1f}%", font=("Arial", 10, "bold"),
            text_color="#2ecc71", width=60, anchor="w"
        ).pack(side="left", padx=(0, 4))

        cat_color = CATEGORY_COLORS.get(category, "#95a5a6")
        ctk.CTkLabel(
            inner, text=category, font=("Arial", 10),
            text_color=cat_color, width=120, anchor="w"
        ).pack(side="left", padx=(0, 4))

        # Theme dropdown
        dropdown_var = ctk.StringVar(value=theme_names[0] if theme_names else "")
        if theme_names:
            dropdown = ctk.CTkOptionMenu(
                inner, variable=dropdown_var, values=theme_names,
                width=140, height=24, font=("Arial", 10)
            )
            dropdown.pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                inner, text="Add", width=50, height=24,
                fg_color=COLORS["accent_green"], hover_color="#00a381",
                font=("Arial", 10),
                command=lambda t=ticker, v=dropdown_var: self._add_suggestion(t, v.get())
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                inner, text="(create a theme first)", font=("Arial", 9),
                text_color=COLORS["text_muted"]
            ).pack(side="left")

    def _add_suggestion(self, ticker, theme_name):
        if not theme_name:
            return
        try:
            add_ticker_to_theme(theme_name, ticker)
            self._refresh_suggestions()
            self._refresh_themes_thread()
        except (KeyError, ValueError) as e:
            self.create_theme_status.configure(
                text=f"[!] {e}", text_color=COLORS["accent_red"]
            )

    def _refresh_themes_thread(self):
        self.after(0, lambda: self.theme_loading_label.configure(text="Loading..."))
        thread = threading.Thread(target=self._refresh_themes, daemon=True)
        thread.start()

    def _refresh_themes(self):
        try:
            period = self.theme_period_var.get()
            themes = get_all_themes_performance(period)
            self.theme_data = themes
            self.after(0, self._populate_theme_cards)
        except Exception as e:
            self.after(0, lambda: self.theme_loading_label.configure(
                text=f"Error: {str(e)[:40]}"
            ))

    def _populate_theme_cards(self):
        self.theme_loading_label.configure(text="")

        for widget in self.theme_cards_frame.winfo_children():
            widget.destroy()

        if not self.theme_data:
            ctk.CTkLabel(
                self.theme_cards_frame,
                text="No themes configured. Use Admin Controls below to create themes.",
                font=("Arial", 12), text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return

        self.theme_cards_frame.grid_columnconfigure(0, weight=1)
        self.theme_cards_frame.grid_columnconfigure(1, weight=1)

        for i, theme in enumerate(self.theme_data):
            card = self._build_theme_card(theme)
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")

    def _build_theme_card(self, theme):
        avg = theme.get("avg_change_pct", 0)
        border_color = COLORS["accent_green"] if avg >= 0 else COLORS["accent_red"]

        card = ctk.CTkFrame(
            self.theme_cards_frame, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=2, border_color=border_color
        )

        # Header: theme name + avg change
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            header, text=theme["theme"],
            font=("Arial", 14, "bold"), text_color=COLORS["text_primary"]
        ).pack(side="left")

        change_color = COLORS["accent_green"] if avg >= 0 else COLORS["accent_red"]
        ctk.CTkLabel(
            header, text=f"{avg:+.1f}%",
            font=("Arial", 14, "bold"), text_color=change_color
        ).pack(side="right")

        # Description + stock count
        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.pack(fill="x", padx=10, pady=2)

        desc = theme.get("description", "")
        if desc:
            ctk.CTkLabel(
                meta, text=desc, font=("Arial", 10),
                text_color=COLORS["text_muted"]
            ).pack(side="left")

        ctk.CTkLabel(
            meta, text=f"{theme.get('stock_count', 0)} stocks",
            font=("Arial", 10), text_color=COLORS["text_secondary"]
        ).pack(side="right")

        # Stock rows
        for stock in theme.get("stocks", []):
            stock_row = ctk.CTkFrame(card, fg_color=COLORS["bg_row"], corner_radius=4, height=26)
            stock_row.pack(fill="x", padx=8, pady=1)
            stock_row.pack_propagate(False)

            inner = ctk.CTkFrame(stock_row, fg_color="transparent")
            inner.pack(fill="x", padx=6, pady=2)

            ctk.CTkLabel(
                inner, text=stock["ticker"], font=("Arial", 10, "bold"),
                text_color=COLORS["text_primary"], width=50, anchor="w"
            ).pack(side="left")

            s_change = stock.get("change_pct", 0)
            s_color = COLORS["accent_green"] if s_change >= 0 else COLORS["accent_red"]
            ctk.CTkLabel(
                inner, text=f"{s_change:+.1f}%", font=("Arial", 10, "bold"),
                text_color=s_color, width=60, anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                inner, text=f"${stock.get('current_price', 0):.2f}",
                font=("Arial", 10), text_color=COLORS["text_secondary"], width=60, anchor="w"
            ).pack(side="left")

            # Remove button
            ctk.CTkButton(
                inner, text="X", width=24, height=20,
                fg_color=COLORS["accent_red"], hover_color="#c0392b",
                font=("Arial", 9, "bold"),
                command=lambda t=theme["theme"], s=stock["ticker"]: self._remove_ticker_action(t, s)
            ).pack(side="right")

        # Delete empty theme button
        if theme.get("stock_count", 0) == 0:
            ctk.CTkButton(
                card, text="Delete Empty Theme", width=140, height=26,
                fg_color=COLORS["accent_red"], hover_color="#c0392b",
                font=("Arial", 10),
                command=lambda t=theme["theme"]: self._delete_theme_action(t)
            ).pack(pady=(4, 8))

        return card

    def _remove_ticker_action(self, theme_name, ticker):
        try:
            remove_ticker_from_theme(theme_name, ticker)
            self._refresh_themes_thread()
            self._refresh_suggestions()
        except (KeyError, ValueError) as e:
            self.create_theme_status.configure(
                text=f"[!] {e}", text_color=COLORS["accent_red"]
            )

    def _delete_theme_action(self, theme_name):
        try:
            delete_theme(theme_name)
            self._refresh_themes_thread()
        except (KeyError, ValueError) as e:
            self.create_theme_status.configure(
                text=f"[!] {e}", text_color=COLORS["accent_red"]
            )

    # ------------------------------------------------------------------
    # Refresh scan
    # ------------------------------------------------------------------
    def _refresh_scan_thread(self):
        self.refresh_btn.configure(state="disabled", text="Scanning...")
        thread = threading.Thread(target=self._refresh_scan, daemon=True)
        thread.start()

    def _refresh_scan(self):
        try:
            self.log("\n[REFRESH] Running scan_universe.py ...")
            result = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "..", "jobs", "scan_universe.py")],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                self.log("[REFRESH] Scan complete! Reloading data...")
                self.after(0, lambda: self.stale_banner.grid_forget())
                self._run_mode_autoscan()
            else:
                self.log(f"[REFRESH] Scan failed:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            self.log("[REFRESH] Scan timed out after 10 minutes")
        except Exception as e:
            self.log(f"[REFRESH] Error: {e}")
        finally:
            self.after(0, lambda: self.refresh_btn.configure(state="normal", text="Refresh Scan"))

    # ------------------------------------------------------------------
    # Log output (writes to Log tab)
    # ------------------------------------------------------------------
    def log(self, message: str):
        def _insert():
            self.log_output.insert("end", message + "\n")
            self.log_output.see("end")
        self.after(0, _insert)


if __name__ == "__main__":
    app = PratternApp()
    app.mainloop()
