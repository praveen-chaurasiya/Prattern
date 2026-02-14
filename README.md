# Prattern Stock Market Engine v2.0 🚀

A dual-AI-powered stock market analysis engine that identifies high-velocity movers and categorizes them using **Claude AI** (categorization) + **Gemini AI** (theme classification).

## Features

- 🎯 **Dual Mode System**:
  - **Mode 1**: Auto-scan universe for 20% movers
  - **Mode 2**: Analyze user-provided tickers
- 🤖 **Dual AI Analysis**:
  - **Claude Sonnet 4.5**: Categorizes WHY stocks moved
  - **Gemini 2.0 Flash**: Classifies stocks into micro-themes
- 📰 Real-time news scraping from Finviz
- 💾 Daily JSON reports saved to `themes/` directory
- 🖥️ **GUI & CLI** support
- 📈 Beautiful progress tracking and summaries

## AI Analysis Layers

### Layer 1: Claude Categories (Why it moved)
- **Earnings Beat**: Positive earnings surprises
- **FDA Approval**: Regulatory approvals (pharma/biotech)
- **M&A/Rumors**: Merger & acquisition activity
- **Sector Momentum**: Broad sector trends
- **Macro/Short Squeeze**: Market-wide or technical moves
- **Unknown**: Insufficient data to categorize

### Layer 2: Gemini Themes (Which theme it belongs to)
- AI Infrastructure
- Semiconductors
- Optical Fiber & AI Optics
- Energy Storage
- Nuclear SMR
- HBM Memory
- Biotech/Pharma
- Cybersecurity
- Cloud Computing
- Clean Energy
- Other

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add BOTH API keys:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your API keys from:
- Claude: https://console.anthropic.com/settings/keys
- Gemini: https://aistudio.google.com/app/apikey

### 3. Run the Engine

**CLI Mode (Interactive):**
```bash
python main.py
# Then select mode 1 or 2
```

**CLI Mode (Auto-scan):**
```bash
python main.py 1
```

**CLI Mode (Manual tickers):**
```bash
python main.py 2 "NVDA,TSLA,AAPL"
```

**CLI Mode (Upload file):**
```bash
python main.py 2 tickers.txt
```

**GUI Mode:**
```bash
python prattern_app.py
# Use browse button to upload ticker list file
```

## Project Structure

```
/
├── main.py              # Main CLI orchestrator (dual-mode)
├── prattern_app.py      # GUI application
├── data_fetcher.py      # Stock data acquisition & filtering
├── theme_analyzer.py    # AI analysis (Claude + Gemini)
├── config.py            # Unified configuration
├── data_manager.py      # Legacy data utilities
├── theme_classifier.py  # Legacy Gemini classifier (deprecated)
├── requirements.txt     # Python dependencies
├── .env                 # API keys (create from .env.example)
└── themes/             # Output directory
    └── YYYY-MM-DD_movers.json
```

## Output Format

Results are saved to `themes/YYYY-MM-DD_movers.json`:

```json
{
  "date": "2026-02-14",
  "total_tickers_scanned": 100,
  "movers_found": 2,
  "movers": [
    {
      "ticker": "NVDA",
      "current_price": 150.0,
      "price_5d_ago": 120.0,
      "move_pct": 25.0,
      "date": "2026-02-14",
      "category": "Earnings Beat",
      "micro_theme": "AI Infrastructure",
      "summary": "Stock surged after reporting Q4 earnings with strong AI chip demand..."
    },
    {
      "ticker": "SMCI",
      "current_price": 85.0,
      "price_5d_ago": 68.0,
      "move_pct": 25.0,
      "date": "2026-02-14",
      "category": "Sector Momentum",
      "micro_theme": "AI Infrastructure",
      "summary": "Benefiting from AI server demand tailwinds..."
    }
  ]
}
```

## Customization

### Change Threshold
Edit `config.py`:
```python
VELOCITY_THRESHOLD = 15.0  # Change from default 20.0
```

### Modify Ticker Universe
Edit `data_fetcher.py` to add/remove tickers from `SP500_TICKERS`

### Add Categories or Themes
Edit `config.py`:
```python
# Modify Claude categories
CLAUDE_CATEGORIES = [...]

# Modify Gemini themes
GEMINI_THEMES = [...]
```

### Change AI Models
Edit `config.py`:
```python
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
GEMINI_MODEL = "gemini-2.0-flash-exp"
```

## Usage Examples

### Mode 1: Auto-scan universe
Automatically scans 100 S&P 500 stocks for 20% movers:
```bash
python main.py 1
```

### Mode 2: Analyze specific tickers

**Option A: Manual input**
```bash
python main.py 2 "NVDA,TSLA,AAPL,META,SMCI"
```

**Option B: Upload file**
```bash
python main.py 2 tickers.txt
```

**File Format** (`tickers.txt`):
```
# One ticker per line
NVDA
TSLA
AAPL

# OR comma-separated
META, MSFT, GOOGL

# OR mixed format (both work)
AMD
CRM, SNOW
```

### GUI Mode
Interactive GUI with mode selection and real-time progress:
```bash
python prattern_app.py
```

**GUI Features:**
- ✅ Radio buttons for Mode 1 or Mode 2
- ✅ Manual ticker entry
- ✅ **📁 Browse button to upload .txt/.csv files**
- ✅ Real-time progress tracking
- ✅ Theme breakdown analysis

### Testing Individual Modules

```bash
# Test data fetcher
python data_fetcher.py

# Test theme analyzer
python theme_analyzer.py
```

## Requirements

- Python 3.8+
- Anthropic API key (Claude AI)
- Internet connection for data fetching

## License

MIT
