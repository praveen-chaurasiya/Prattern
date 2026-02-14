import polars as pl
import yfinance as yf

def get_stock_data(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            data.append({
                "ticker": ticker,
                "summary": info.get("longBusinessSummary", "N/A"),
                "price": stock.fast_info.last_price
            })
        except Exception:
            continue
    return pl.DataFrame(data)