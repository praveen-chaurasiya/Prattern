import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Unified configuration for Stock Market Engine"""

    # API Keys
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")

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

    # Polygon.io API Key (cloud-friendly price provider)
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

    # Auth & Deployment
    PRATTERN_API_KEY = os.getenv("PRATTERN_API_KEY")       # None = auth disabled (local dev)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    # Provider Selection (change these or set env vars to swap providers)
    UNIVERSE_PROVIDER = os.getenv("UNIVERSE_PROVIDER", "nasdaq")
    PRICE_PROVIDER = os.getenv("PRICE_PROVIDER", "polygon" if os.getenv("POLYGON_API_KEY") else "yfinance")
    NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "finviz")
    AI_PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "gemini")
    AI_FALLBACK_PROVIDER = os.getenv("AI_FALLBACK_PROVIDER", "claude")

    # API Models
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"  # Used only for fallback on "Unknown" categorizations
    GEMINI_MODEL = "gemini-2.5-flash"  # Gemini 2.5 Flash — primary analysis engine (stable)

    @classmethod
    def validate(cls):
        """Validates that required API keys are loaded"""
        errors = []

        if not cls.ANTHROPIC_KEY:
            errors.append("ANTHROPIC_API_KEY missing")
        else:
            print(f"[OK] Claude API Key Loaded: {cls.ANTHROPIC_KEY[:4]}...")

        if not cls.GEMINI_KEY:
            errors.append("GEMINI_API_KEY missing")
        else:
            print(f"[OK] Gemini API Key Loaded: {cls.GEMINI_KEY[:4]}...")

        if errors:
            raise ValueError(f"Configuration Error: {', '.join(errors)}. Check your .env file.")

        print("[OK] Required API keys validated successfully!")
