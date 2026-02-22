# Prattern - Stock Market Engine

A dual-AI stock analysis engine that scans the US market for high-velocity movers (20%+ gain in 5 trading days) and classifies them using **Gemini AI** (primary) with **Claude AI** as fallback.

## Features

- **Auto-scan mode** — scans ~6,200 US tickers for 20%+ movers in 5 days
- **Manual mode** — analyze any list of tickers you provide
- **Dual AI pipeline** — Gemini classifies in batches, Claude handles edge cases
- **News context** — scrapes Finviz headlines to inform AI analysis
- **Pre-computed scanning** — background job runs daily, app loads results instantly
- **GUI & CLI** — CustomTkinter desktop app or command-line interface
- **Price filtering** — filter results by minimum price (GUI: No filter, >$1, >$5, >$10, >$20, Custom)

## Installation

### Prerequisites

- Python 3.8+
- Internet connection (for market data and AI APIs)

### Setup

```bash
# Clone the repository
git clone https://github.com/praveen-chaurasiya/Prattern.git
cd Prattern

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### Dependencies

| Package | Purpose |
|---------|---------|
| yfinance | Stock price data from Yahoo Finance |
| google-generativeai | Gemini AI — primary analysis engine |
| anthropic | Claude AI — fallback for unclassified stocks |
| beautifulsoup4, lxml | Finviz news scraping |
| requests | HTTP client |
| pandas, numpy, polars | Data processing |
| python-dotenv | Environment variable management |
| customtkinter | Modern desktop GUI (optional, GUI only) |

## Configuration

### API Keys

Edit `.env` with your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your keys from:
- **Gemini**: https://aistudio.google.com/app/apikey
- **Claude**: https://console.anthropic.com/settings/keys

Both keys are required. The app validates them at startup.

### Tunable Parameters

All configuration lives in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VELOCITY_THRESHOLD` | `20.0` | Minimum % gain in 5 days to qualify as a mover |
| `LOOKBACK_PERIOD` | `"10d"` | Price history period (ensures 5 trading days) |
| `MAX_NEWS_HEADLINES` | `3` | Headlines to fetch per stock from Finviz |
| `GEMINI_MODEL` | `models/gemini-3-flash-preview` | Primary AI model |
| `CLAUDE_MODEL` | `claude-sonnet-4-5-20250929` | Fallback AI model |

### Categories & Themes

The AI classifies each mover into:

**Category** (why it moved):
Earnings Beat, FDA Approval, M&A/Rumors, Sector Momentum, Macro/Short Squeeze, Unknown

**Theme** (what sector/niche):
AI Infrastructure, Semiconductors, Semiconductor Equipment, Memory, Data Storage, Data Center Enablers, Quantum Computing, Cloud Computing, Energy Storage, Natural Gas/Clean Energy, Nuclear SMR, Space, Space Defense, Drone/UAV, Robotics, Cybersecurity, Optical Fiber & AI Optics, Copper, Gold, Silver, Rare-earth Minerals, Biotech/Pharma, EP, Other

Both lists are editable in `config.py` (`CLAUDE_CATEGORIES` and `GEMINI_THEMES`).

## Usage

### Background Scanner

Run daily after market close (~4:30 PM ET) to pre-compute movers. Schedule with Windows Task Scheduler or cron.

```bash
python scan_universe.py            # Default 20% threshold
python scan_universe.py 15.0       # Custom threshold
```

This fetches ~6,200 tickers from the NASDAQ API, downloads prices in batches of 200, and saves movers to `data/daily_movers.json`. No AI analysis is performed at this stage.

### GUI Application

```bash
python pratten_app.py
```

- Select **Mode 1** (auto-scan) to load pre-computed movers instantly
- Select **Mode 2** (manual) to enter tickers or browse a .txt/.csv file
- Apply price filters from the dropdown
- Results display in real-time as AI analysis completes

### CLI

```bash
# Interactive — prompts for mode selection
python main.py

# Mode 1 — auto-scan pre-computed movers
python main.py 1

# Mode 2 — comma-separated tickers
python main.py 2 "NVDA,TSLA,AAPL,META,SMCI"

# Mode 2 — tickers from file
python main.py 2 tickers.txt
```

**Ticker file format** (`tickers.txt`):
```
NVDA
TSLA
AAPL
META, MSFT, GOOGL
```

One ticker per line, comma-separated, or mixed. Lines starting with `#` are ignored.

## How It Works

```
scan_universe.py (daily, offline)
  │
  ├── Fetch ~6,200 tickers from NASDAQ screener API (free, no key)
  ├── Download prices via yfinance (batches of 200)
  ├── Calculate 5-day % change
  └── Save movers → data/daily_movers.json

pratten_app.py / main.py (user-facing)
  │
  ├── Load pre-computed movers (Mode 1) or fetch user tickers (Mode 2)
  ├── Scrape Finviz news headlines (up to 3 per ticker)
  ├── Gemini AI — batch analysis (7 stocks per call)
  │     Returns: category, summary, primary_theme, sub_niche, ecosystem_role
  ├── Claude AI — fallback per-stock for:
  │     • category == "Unknown"
  │     • sub_niche == "Classification Failed"
  │     • primary_theme == "Other"
  └── Display results / save to themes/YYYY-MM-DD_movers.json
```

## Output Format

Results are saved to `themes/YYYY-MM-DD_movers.json`:

```json
{
  "date": "2026-02-14",
  "total_tickers_scanned": 6200,
  "movers_found": 12,
  "movers": [
    {
      "ticker": "NVDA",
      "current_price": 150.0,
      "price_5d_ago": 120.0,
      "move_pct": 25.0,
      "date": "2026-02-14",
      "category": "Earnings Beat",
      "summary": "Stock surged after reporting Q4 earnings with strong AI chip demand...",
      "primary_theme": "AI Infrastructure",
      "sub_niche": "GPU Accelerators",
      "ecosystem_role": "Producer",
      "micro_theme": "AI Infrastructure"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `ticker` | Stock symbol |
| `current_price` | Latest closing price |
| `price_5d_ago` | Price 5 trading days ago |
| `move_pct` | Percentage gain over 5 days |
| `category` | Why it moved (from `CLAUDE_CATEGORIES`) |
| `summary` | AI-generated explanation of the move |
| `primary_theme` | Sector/niche classification (from `GEMINI_THEMES`) |
| `sub_niche` | More specific classification within the theme |
| `ecosystem_role` | Role in the ecosystem (e.g., Producer, Enabler, Beneficiary) |

## Project Structure

```
├── pratten_app.py       # GUI application (CustomTkinter)
├── main.py              # CLI application
├── scan_universe.py     # Background scanner (run daily)
├── data_fetcher.py      # Universe fetching, yfinance downloads, price calculations
├── theme_analyzer.py    # Gemini batch analysis, Claude fallback, Finviz scraping
├── config.py            # All configuration (API keys, models, thresholds, categories)
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── data/                # Auto-generated: cached universe, daily movers (gitignored)
└── themes/              # Auto-generated: daily JSON reports (gitignored)
```

## License

MIT
