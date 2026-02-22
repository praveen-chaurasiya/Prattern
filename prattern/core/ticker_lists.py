"""
Hardcoded fallback ticker lists.
Used when the NASDAQ API is unavailable.
"""

# S&P 500 Large Caps
SP500_LARGE_CAPS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL',
    'ADBE', 'CRM', 'CSCO', 'ACN', 'INTC', 'AMD', 'IBM', 'QCOM', 'TXN', 'INTU',
    'NOW', 'AMAT', 'ADI', 'MU', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'MCHP', 'FTNT',
    'NXPI', 'MRVL', 'WDAY', 'TEAM', 'PANW', 'CRWD', 'DDOG', 'NET', 'ZS', 'SNOW',

    # Financials
    'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'SPGI', 'BLK',
    'C', 'SCHW', 'AXP', 'CB', 'PNC', 'USB', 'TFC', 'COF', 'BK', 'AIG',
    'MMC', 'AON', 'ICE', 'CME', 'MCO', 'AFL', 'MET', 'PRU', 'ALL', 'TRV',

    # Healthcare
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
    'AMGN', 'GILD', 'CVS', 'CI', 'ISRG', 'SYK', 'BSX', 'MDT', 'ZTS', 'REGN',
    'VRTX', 'HUM', 'ELV', 'MCK', 'COR', 'A', 'IQV', 'RMD', 'DXCM', 'IDXX',

    # Consumer Discretionary
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'ABNB',
    'CMG', 'MAR', 'GM', 'F', 'YUM', 'ORLY', 'AZO', 'DHI', 'LEN', 'NVR',
    'RCL', 'CCL', 'NCLH', 'LVS', 'MGM', 'WYNN', 'POOL', 'HLT', 'DRI', 'ULTA',

    # Consumer Staples
    'WMT', 'PG', 'KO', 'PEP', 'COST', 'PM', 'MO', 'MDLZ', 'CL', 'GIS',
    'KMB', 'SYY', 'HSY', 'K', 'CAG', 'TSN', 'HRL', 'CPB', 'MKC', 'CHD',

    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
    'WMB', 'KMI', 'HES', 'DVN', 'FANG', 'BKR', 'MRO', 'APA', 'CTRA', 'EQT',

    # Industrials
    'GE', 'CAT', 'BA', 'HON', 'RTX', 'UPS', 'DE', 'UNP', 'LMT', 'GD',
    'MMM', 'NOC', 'CSX', 'NSC', 'FDX', 'WM', 'EMR', 'ITW', 'ETN', 'PH',

    # Materials
    'LIN', 'APD', 'SHW', 'FCX', 'NEM', 'ECL', 'DD', 'NUE', 'DOW', 'PPG',

    # Real Estate
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'SPG', 'O', 'WELL', 'AVB',

    # Utilities
    'NEE', 'SO', 'DUK', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ES', 'PCG',

    # Communication Services
    'META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR',
    'PARA', 'OMC', 'EA', 'TTWO', 'WBD', 'MTCH', 'NWSA', 'FOX', 'FOXA', 'IPG'
]

# Mid-Cap Stocks
MIDCAP_STOCKS = [
    # Technology
    'PLTR', 'COIN', 'HOOD', 'SQ', 'SHOP', 'ZM', 'DOCU', 'OKTA', 'DBX', 'BOX',
    'TWLO', 'ESTC', 'MDB', 'PATH', 'DT', 'BILL', 'CFLT', 'S', 'GTLB', 'FROG',

    # Healthcare
    'MRNA', 'TECH', 'EXAS', 'ALGN', 'PODD', 'PEN', 'HOLX', 'INCY', 'BMRN', 'UTHR',
    'SGEN', 'ALNY', 'RARE', 'SRPT', 'IONS', 'NBIX', 'JAZZ', 'FOLD', 'BLUE', 'ARWR',

    # Consumer
    'LULU', 'DECK', 'BURL', 'FIVE', 'OLLI', 'DKS', 'TSCO', 'AAP', 'AEO', 'ANF',
    'CROX', 'SKX', 'FL', 'WSM', 'RH', 'W', 'CHWY', 'PETS', 'CAVA', 'WING',

    # Financials
    'SOFI', 'ALLY', 'HBAN', 'RF', 'KEY', 'CFG', 'FITB', 'EWBC', 'WTFC', 'ZION',

    # Industrials
    'CARR', 'OTIS', 'XYL', 'VRSK', 'IEX', 'GNRC', 'AOS', 'DOV', 'IR', 'ROK',

    # Energy
    'TPL', 'PR', 'CHK', 'AR', 'SM', 'RRC', 'MTDR', 'NOG', 'MGY', 'VTLE'
]

# Small-Cap High-Growth Stocks
SMALLCAP_GROWTH = [
    # EV & Clean Energy
    'RIVN', 'LCID', 'CHPT', 'BLNK', 'PLUG', 'FCEL', 'ENPH', 'SEDG', 'RUN', 'NOVA',

    # Biotech
    'SAVA', 'NKTR', 'CRISPR', 'NTLA', 'BEAM', 'CRSP', 'EDIT', 'VCYT', 'FATE', 'NTLA',

    # Fintech
    'UPST', 'AFRM', 'LC', 'PAYC', 'PAYO', 'GPN', 'FIS', 'FISV', 'FOUR', 'STNE',

    # AI/Cloud
    'AI', 'SMCI', 'IONQ', 'RGTI', 'BBAI', 'SOUN', 'AMBA', 'QUBT', 'LUNR', 'RKLB',

    # Meme Stocks
    'GME', 'AMC', 'BBBY', 'BB', 'NOK', 'EXPR', 'KOSS', 'NAKD', 'CLOV', 'WKHS'
]

# ETFs
BROAD_MARKET_ETFS = [
    'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'SCHX', 'IVV', 'VEA', 'IEFA',
    'VWO', 'IEMG', 'EEM', 'EFA', 'ACWI', 'URTH', 'VT', 'IXUS', 'VXUS', 'SPDW'
]

SECTOR_ETFS = [
    'XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP', 'XLRE', 'XLU', 'XLC',
    'VGT', 'VFH', 'VHT', 'VDE', 'VIS', 'VCR', 'VDC', 'VNQ', 'VPU', 'VOX',
    'IYW', 'IYF', 'IYH', 'IYE', 'IYJ', 'IYC', 'IYK', 'IYR', 'IDU', 'IYZ'
]

THEMATIC_ETFS = [
    # Technology & Innovation
    'ARKK', 'ARKG', 'ARKQ', 'ARKW', 'ARKF', 'CIBR', 'HACK', 'ROBO', 'BOTZ', 'IRBO',
    'CLOU', 'WCLD', 'SKYY', 'IGV', 'FDN', 'FINX', 'IPAY', 'THNQ', 'AIQ', 'QTUM',

    # Clean Energy
    'ICLN', 'TAN', 'QCLN', 'PBW', 'ACES', 'SMOG', 'FAN', 'EVX', 'LIT', 'BATT',

    # Crypto & Blockchain
    'BITO', 'BITI', 'BLOK', 'LEGR', 'KOIN', 'CRPT', 'BITQ', 'BLCN', 'GBTC', 'ETHE',

    # Semiconductors
    'SOXX', 'SMH', 'XSD', 'PSI', 'SOXL', 'SOXS',

    # Healthcare
    'XBI', 'IBB', 'BBH', 'IHI', 'IHE', 'ARKG', 'GNOM', 'SBIO',

    # Commodities
    'GLD', 'SLV', 'GDX', 'GDXJ', 'USO', 'UNG', 'DBA', 'DBC', 'PDBC', 'GSG',

    # Cannabis
    'MJ', 'THCX', 'YOLO', 'CNBS', 'POTX', 'MSOS',

    # ESG
    'ESGU', 'ESGV', 'SUSL', 'DSI', 'USSG', 'VSGX', 'SUSA'
]

LEVERAGED_ETFS = [
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'TNA', 'TZA', 'UDOW', 'SDOW', 'FAS', 'FAZ',
    'TECL', 'TECS', 'LABU', 'LABD', 'CURE', 'RXD', 'ERX', 'ERY', 'NAIL', 'DRV',
    'NUGT', 'DUST', 'JNUG', 'JDST', 'UVXY', 'SVXY', 'VXX', 'VIXY', 'SPXL', 'SPXS'
]

BOND_ETFS = [
    'AGG', 'BND', 'LQD', 'HYG', 'JNK', 'TLT', 'IEF', 'SHY', 'TIP', 'VCIT',
    'VCSH', 'BNDX', 'VWOB', 'EMB', 'MUB', 'SUB', 'BKLN', 'SJNK', 'SHYG', 'FLOT'
]

# Universe definitions
UNIVERSE_STOCKS_ONLY = list(dict.fromkeys(SP500_LARGE_CAPS + MIDCAP_STOCKS + SMALLCAP_GROWTH))

UNIVERSE_STOCKS_AND_ETFS = (
    SP500_LARGE_CAPS +
    MIDCAP_STOCKS +
    SMALLCAP_GROWTH +
    BROAD_MARKET_ETFS +
    SECTOR_ETFS +
    THEMATIC_ETFS +
    LEVERAGED_ETFS +
    BOND_ETFS
)

SP500_TICKERS = SP500_LARGE_CAPS[:100]
