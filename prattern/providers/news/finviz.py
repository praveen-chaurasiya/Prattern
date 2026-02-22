"""Finviz news headline provider."""

import requests
from bs4 import BeautifulSoup
from typing import List


class FinvizNewsProvider:
    """Scrape latest news headlines from Finviz."""

    def fetch_headlines(self, ticker: str, max_headlines: int = 3) -> List[str]:
        """Scrape latest news headlines from Finviz for a given ticker."""
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            news_table = soup.find('table', {'id': 'news-table'})

            if not news_table:
                print(f"[!]  No news found for {ticker}")
                return []

            headlines = []
            for row in news_table.find_all('tr')[:max_headlines]:
                link = row.find('a')
                if link:
                    headlines.append(link.get_text().strip())

            return headlines

        except Exception as e:
            print(f"[ERROR] Error fetching news for {ticker}: {str(e)}")
            return []
