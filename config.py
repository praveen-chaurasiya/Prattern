import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Unified configuration for Stock Market Engine"""

    # API Keys
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    FMP_KEY = os.getenv("FMP_API_KEY")

    # FMP (Financial Modeling Prep) Settings
    FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

    # Analysis Parameters
    VELOCITY_THRESHOLD = 20.0  # Minimum % gain in 5 days to qualify as mover
    LOOKBACK_PERIOD = "10d"     # Period to fetch data (ensures 5 trading days)
    MAX_NEWS_HEADLINES = 3      # Headlines to fetch per stock

    # Claude Categories
    CLAUDE_CATEGORIES = [
        "Earnings Beat",
        "FDA Approval",
        "M&A/Rumors",
        "Sector Momentum",
        "Macro/Short Squeeze",
        "Unknown"
    ]

    # Gemini Theme Criteria (for deeper classification)
    GEMINI_THEMES = [
        # AI & Computing
        "AI Infrastructure",
        "Semiconductors",
        "Semiconductor Equipment",
        "Memory",
        "Data Storage",
        "Data Center Enablers",
        "Quantum Computing",
        "Cloud Computing",

        # Energy & Clean Tech
        "Energy Storage",
        "Natural Gas/Clean Energy",
        "Nuclear SMR",

        # Defense & Aerospace
        "Space",
        "Space Defense",
        "Drone/UAV",

        # Advanced Tech
        "Robotics",
        "Cybersecurity",
        "Optical Fiber & AI Optics",

        # Commodities & Materials
        "Copper",
        "Gold",
        "Silver",
        "Rare-earth Minerals",

        # Healthcare
        "Biotech/Pharma",

        # Other
        "EP",
        "Other"
    ]

    # API Models
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"  # Used only for fallback on "Unknown" categorizations
    GEMINI_MODEL = "models/gemini-3-flash-preview"  # Gemini 3 Flash Preview — primary analysis engine

    @classmethod
    def validate(cls):
        """Validates that required API keys are loaded"""
        errors = []

        if not cls.ANTHROPIC_KEY:
            errors.append("ANTHROPIC_API_KEY missing")
        else:
            print(f"✅ Claude API Key Loaded: {cls.ANTHROPIC_KEY[:8]}...")

        if not cls.GEMINI_KEY:
            errors.append("GEMINI_API_KEY missing")
        else:
            print(f"✅ Gemini API Key Loaded: {cls.GEMINI_KEY[:8]}...")

        if errors:
            raise ValueError(f"❌ Configuration Error: {', '.join(errors)}. Check your .env file.")

        if not cls.FMP_KEY:
            print("⚠️  FMP_API_KEY missing — will use hardcoded ticker list as fallback")
        else:
            print(f"✅ FMP API Key Loaded: {cls.FMP_KEY[:8]}...")

        print("✅ All API keys validated successfully!")