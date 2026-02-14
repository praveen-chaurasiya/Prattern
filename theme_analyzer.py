"""
Theme Analyzer Module
Uses Gemini AI for bulk analysis: categorization, summaries, and theme classification
Uses Claude AI only as fallback for stocks Gemini categorizes as "Unknown"
"""

import os
import requests
import time
import json
from bs4 import BeautifulSoup
from anthropic import Anthropic
import google.generativeai as genai
from typing import List, Dict, Optional
from config import Config

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini
if Config.GEMINI_KEY:
    genai.configure(api_key=Config.GEMINI_KEY)


def fetch_finviz_news(ticker: str, max_headlines: int = 3) -> List[str]:
    """
    Scrape latest news headlines from Finviz for a given ticker

    Args:
        ticker: Stock symbol
        max_headlines: Maximum number of headlines to fetch (default: 3)

    Returns:
        List of news headline strings
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Finviz news table
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


def categorize_with_claude(ticker: str, move_pct: float, current_price: float,
                           price_5d_ago: float, headlines: List[str]) -> Dict[str, str]:
    """
    Use Claude API to categorize the stock move and generate summary

    Args:
        ticker: Stock symbol
        move_pct: Percentage change
        current_price: Current stock price
        price_5d_ago: Price 5 days ago
        headlines: List of news headlines

    Returns:
        Dict with 'category' and 'summary' keys
    """
    if not Config.ANTHROPIC_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not found in environment")
        return {'category': 'Unknown', 'summary': 'API key not configured'}

    try:
        client = Anthropic(api_key=Config.ANTHROPIC_KEY)

        # Construct the prompt
        headlines_text = "\n".join([f"- {h}" for h in headlines]) if headlines else "No recent news available"
        categories_text = "\n- ".join(Config.CLAUDE_CATEGORIES)

        themes_text = "\n- ".join(Config.GEMINI_THEMES)

        prompt = f"""You are a financial analyst categorizing stock movements.

Stock: {ticker}
Movement: +{move_pct}% (from ${price_5d_ago} to ${current_price} over 5 trading days)

Recent News Headlines:
{headlines_text}

Based on this information:

1. Categorize WHY this stock moved into ONE of these categories:
- {categories_text}

2. Classify the stock's PRIMARY THEME from this list:
- {themes_text}

3. Identify a specific SUB-NICHE (e.g. "GPU Accelerators", "mRNA Therapeutics", "EV Charging")

4. Identify the ECOSYSTEM ROLE: Producer, Supplier, Integrator, Infrastructure, or Platform

Provide your response in this EXACT format:
CATEGORY: [one of the categories above]
SUMMARY: [2-3 sentence explanation of why the stock moved]
PRIMARY_THEME: [one theme from the list]
SUB_NICHE: [specific sub-niche]
ECOSYSTEM_ROLE: [Producer/Supplier/Integrator/Infrastructure/Platform]

Be concise and data-driven. If the reason is unclear from the news, use "Unknown" for category and "Other" for theme."""

        # Call Claude API with correct model
        message = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        response_text = message.content[0].text.strip()

        # Extract all fields
        category = "Unknown"
        summary = "Unable to determine reason for movement"
        primary_theme = "Other"
        sub_niche = "Unknown"
        ecosystem_role = "Platform"

        for line in response_text.split('\n'):
            if line.startswith('CATEGORY:'):
                category = line.replace('CATEGORY:', '').strip()
            elif line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('PRIMARY_THEME:'):
                primary_theme = line.replace('PRIMARY_THEME:', '').strip()
            elif line.startswith('SUB_NICHE:'):
                sub_niche = line.replace('SUB_NICHE:', '').strip()
            elif line.startswith('ECOSYSTEM_ROLE:'):
                ecosystem_role = line.replace('ECOSYSTEM_ROLE:', '').strip()

        # Validate category
        if category not in Config.CLAUDE_CATEGORIES:
            category = "Unknown"

        # Validate theme
        if primary_theme not in Config.GEMINI_THEMES:
            primary_theme = "Other"

        # Validate ecosystem role
        valid_roles = {"Producer", "Supplier", "Integrator", "Infrastructure", "Platform"}
        if ecosystem_role not in valid_roles:
            ecosystem_role = "Platform"

        return {
            'category': category,
            'summary': summary,
            'primary_theme': primary_theme,
            'sub_niche': sub_niche,
            'ecosystem_role': ecosystem_role,
        }

    except Exception as e:
        print(f"[ERROR] Error calling Claude API for {ticker}: {str(e)}")
        return {
            'category': 'Unknown',
            'summary': f'Error analyzing: {str(e)}'
        }


def _parse_gemini_json(response_text: str, expected_count: int) -> List[Dict]:
    """
    Parse JSON array from Gemini response, handling markdown blocks and truncation.

    Args:
        response_text: Raw response text from Gemini
        expected_count: Number of objects expected in the array

    Returns:
        List of dicts parsed from JSON
    """
    fallback = [{"category": "Unknown", "summary": "Gemini parse error", "primary_theme": "Other", "sub_niche": "Unknown", "ecosystem_role": "Platform"} for _ in range(expected_count)]

    # Strip markdown code blocks
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    # Extract JSON array
    if "[" in response_text and "]" in response_text:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        response_text = response_text[start:end]

    # Parse JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to salvage truncated JSON
        last_brace = response_text.rfind("}")
        if last_brace > 0:
            truncated = response_text[:last_brace + 1]
            if not truncated.rstrip().endswith("]"):
                truncated = truncated.rstrip().rstrip(",") + "]"
            try:
                data = json.loads(truncated)
                print(f"   [RECOVERED] Salvaged {len(data)} of {expected_count} from truncated response")
            except json.JSONDecodeError:
                print(f"   [WARNING] JSON parse failed, using fallback")
                return fallback
        else:
            print(f"   [WARNING] JSON parse failed, using fallback")
            return fallback

    # Pad if needed
    while len(data) < expected_count:
        data.append({"category": "Unknown", "summary": "Not classified", "primary_theme": "Other", "sub_niche": "Unknown", "ecosystem_role": "Platform"})

    return data


def analyze_batch_with_gemini(movers_with_news: List[Dict]) -> List[Dict]:
    """
    Single Gemini call per batch does categorization + summary + theme classification.
    Replaces both categorize_with_claude() and classify_theme_with_gemini() for most stocks.

    Args:
        movers_with_news: List of mover dicts, each with a 'headlines' key

    Returns:
        List of movers with category, summary, primary_theme, sub_niche, ecosystem_role
    """
    if not Config.GEMINI_KEY:
        print("[WARNING] GEMINI_API_KEY not found, skipping Gemini analysis")
        for mover in movers_with_news:
            mover['category'] = 'Unknown'
            mover['summary'] = 'Gemini API key not configured'
            mover['primary_theme'] = 'N/A'
            mover['sub_niche'] = 'N/A'
            mover['ecosystem_role'] = 'N/A'
            mover['micro_theme'] = 'N/A'
        return movers_with_news

    try:
        model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )

        allowed_categories = ", ".join(Config.CLAUDE_CATEGORIES)
        allowed_themes = ", ".join(Config.GEMINI_THEMES)
        batch_size = 7  # Larger batches = fewer API calls to stay within free tier RPD limits
        results = []

        print(f"\n[GEMINI] Analyzing {len(movers_with_news)} stocks (categorize + theme + summary)...")

        for i in range(0, len(movers_with_news), batch_size):
            batch = movers_with_news[i:i + batch_size]

            # Format batch with headlines and move data
            stocks_list = []
            for idx, m in enumerate(batch, 1):
                headlines = m.get('headlines', [])
                headlines_text = "; ".join(headlines) if headlines else "No recent news"
                stocks_list.append(
                    f"{idx}. {m['ticker']} | Move: {m['move_pct']:+.1f}% "
                    f"(${m.get('price_5d_ago', 0):.2f} -> ${m.get('current_price', 0):.2f}) | "
                    f"Headlines: {headlines_text}"
                )

            stocks_input = "\n".join(stocks_list)

            prompt = f"""You are an expert financial analyst. For each stock below, perform TWO tasks:

TASK 1 - CATEGORIZE why the stock moved. Pick ONE category:
{allowed_categories}

TASK 2 - CLASSIFY the stock's thematic sector. Pick ONE theme:
{allowed_themes}

Also determine the ecosystem_role: "Producer" (raw materials/goods), "Infrastructure" (pipes/cooling/connectivity), or "Platform" (software/data/services).

STOCKS TO ANALYZE:
{stocks_input}

CLASSIFICATION METHODOLOGY:
1. CATEGORY: Match headlines to category. Use "Earnings Beat" for earnings/revenue news, "FDA Approval" for biotech/drug news, "M&A/Rumors" for acquisition/merger news, "Sector Momentum" for industry-wide trends, "Macro/Short Squeeze" for macro events or squeezes. Use "Unknown" ONLY if headlines give no clear signal.
2. SUMMARY: Write 1-2 sentences explaining why the stock moved, based on the headlines.
3. THEME: Classify based on the company's core business, not the news event.
4. SUB-NICHE: A specific 2-4 word descriptor of their niche (e.g., "Liquid Cooling Systems", "AI Chip Design").
5. ECOSYSTEM ROLE: Producer, Infrastructure, or Platform.

CRITICAL OUTPUT REQUIREMENTS:
1. Return ONLY a valid JSON array with exactly {len(batch)} objects (one per stock, in order)
2. Each object format:
   {{
     "category": "ONE category from the list above",
     "summary": "1-2 sentence explanation",
     "primary_theme": "ONE theme from the list above",
     "sub_niche": "Specific 2-4 word descriptor",
     "ecosystem_role": "Producer OR Infrastructure OR Platform"
   }}
3. No explanations, no markdown, ONLY the JSON array

Your JSON array:"""

            # Retry logic
            for attempt in range(3):
                try:
                    response = model.generate_content(prompt)
                    response_text = response.text.strip()
                    print(f"   [DEBUG] Gemini response length: {len(response_text)} chars")

                    if len(response_text) > 0:
                        print(f"   [DEBUG] Response preview: {response_text[:200]}...")

                    parsed = _parse_gemini_json(response_text, len(batch))

                    # Assign results to batch
                    for idx, obj in enumerate(parsed):
                        if idx < len(batch):
                            # Validate category
                            category = obj.get("category", "Unknown")
                            if category not in Config.CLAUDE_CATEGORIES:
                                category = "Unknown"

                            # Validate theme
                            primary_theme = obj.get("primary_theme", "Other")
                            if primary_theme not in Config.GEMINI_THEMES:
                                primary_theme = "Other"

                            # Validate ecosystem role
                            ecosystem_role = obj.get("ecosystem_role", "Platform")
                            if ecosystem_role not in ["Producer", "Infrastructure", "Platform"]:
                                ecosystem_role = "Platform"

                            batch[idx]["category"] = category
                            batch[idx]["summary"] = obj.get("summary", "No summary available")
                            batch[idx]["primary_theme"] = primary_theme
                            batch[idx]["sub_niche"] = obj.get("sub_niche", "Unknown")
                            batch[idx]["ecosystem_role"] = ecosystem_role
                            batch[idx]["micro_theme"] = primary_theme

                    print(f"   [+] Analyzed batch {i//batch_size + 1}/{(len(movers_with_news)-1)//batch_size + 1}")

                    # Rate limiting between batches (free tier: ~5 RPM)
                    if i + batch_size < len(movers_with_news):
                        print(f"   [WAIT] Pausing 15s for rate limit (free tier)...")
                        time.sleep(15)

                    break

                except Exception as e:
                    wait_time = 2 ** attempt
                    error_msg = str(e)
                    print(f"   [!] Retry {attempt + 1}/3 after {wait_time}s: {error_msg[:80]}")

                    if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                        print(f"   [WARNING] Rate limit detected! Waiting {wait_time * 3}s...")
                        time.sleep(wait_time * 3)
                    else:
                        time.sleep(wait_time)

                    if attempt == 2:
                        print(f"   [ERROR] All retries failed: {error_msg[:100]}")
                        for m in batch:
                            m["category"] = "Unknown"
                            m["summary"] = f"Gemini error: {error_msg[:50]}"
                            m["primary_theme"] = "Other"
                            m["sub_niche"] = "Classification Failed"
                            m["ecosystem_role"] = "Platform"
                            m["micro_theme"] = "Other"

            results.extend(batch)

        return results

    except Exception as e:
        print(f"[ERROR] Gemini analysis failed: {str(e)}")
        for mover in movers_with_news:
            mover['category'] = 'Unknown'
            mover['summary'] = f'Gemini error: {str(e)[:50]}'
            mover['primary_theme'] = 'Other'
            mover['sub_niche'] = 'Error'
            mover['ecosystem_role'] = 'Platform'
            mover['micro_theme'] = 'Other'
        return movers_with_news


def analyze_all_movers(movers: List[Dict]) -> List[Dict]:
    """
    Analyze all movers: Gemini does 90%+ of work, Claude handles unknowns only.

    Pipeline:
    - Step 1: Fetch news for all stocks
    - Step 2: Batch ALL stocks to Gemini (categorize + theme + summary in one pass)
    - Step 3: Filter unknowns → send only those to Claude as fallback
    - Step 4: Return merged results

    Args:
        movers: List of mover dicts from data_fetcher

    Returns:
        List of analyzed movers with category, summary, primary_theme, sub_niche, ecosystem_role
    """
    if not movers:
        return []

    print(f"\n{'='*80}")
    print(f"THEME ANALYZER - Processing {len(movers)} movers")
    print(f"{'='*80}")

    # Step 1: Fetch news for all stocks
    print(f"\n[STEP 1/3] Fetching News")
    print(f"{'='*80}")

    for idx, mover in enumerate(movers, 1):
        ticker = mover['ticker']
        print(f"\n[{idx}/{len(movers)}] [NEWS] Fetching news for {ticker}...")
        headlines = fetch_finviz_news(ticker, max_headlines=Config.MAX_NEWS_HEADLINES)
        mover['headlines'] = headlines
        if headlines:
            print(f"   [OK] Found {len(headlines)} headlines")
        else:
            print(f"   [WARNING] No headlines found")

    # Step 2: Gemini batch analysis (categorize + theme + summary)
    print(f"\n\n[STEP 2/3] Gemini Analysis (categorize + theme + summary)")
    print(f"{'='*80}")

    analyzed = analyze_batch_with_gemini(movers)

    # Step 3: Claude fallback for unknowns or failed theme classifications
    needs_claude = [
        m for m in analyzed
        if m.get('category') == 'Unknown'
        or m.get('sub_niche') == 'Classification Failed'
        or m.get('primary_theme') == 'Other'
    ]
    print(f"\n\n[STEP 3/3] Claude Fallback")
    print(f"{'='*80}")

    if needs_claude:
        print(f"[CLAUDE] {len(needs_claude)} stocks need Claude fallback: {', '.join(m['ticker'] for m in needs_claude)}")
        for m in needs_claude:
            print(f"   [CLAUDE] Analyzing {m['ticker']}...")
            claude_result = categorize_with_claude(
                ticker=m['ticker'],
                move_pct=m['move_pct'],
                current_price=m['current_price'],
                price_5d_ago=m['price_5d_ago'],
                headlines=m.get('headlines', [])
            )
            # Update category if it was Unknown
            if m.get('category') == 'Unknown':
                m['category'] = claude_result['category']
            m['summary'] = claude_result['summary']
            # Update theme fields if they were failed/default
            if m.get('sub_niche') == 'Classification Failed' or m.get('primary_theme') == 'Other':
                m['primary_theme'] = claude_result.get('primary_theme', m.get('primary_theme'))
                m['sub_niche'] = claude_result.get('sub_niche', m.get('sub_niche'))
                m['ecosystem_role'] = claude_result.get('ecosystem_role', m.get('ecosystem_role'))
            print(f"   [+] Claude: {claude_result['category']} | {claude_result.get('primary_theme')} | {claude_result.get('sub_niche')}")
    else:
        print(f"[OK] No fallbacks needed — Gemini handled all {len(analyzed)} stocks!")

    print(f"\n{'='*80}")
    gemini_count = len(analyzed) - len(needs_claude)
    claude_count = len(needs_claude)
    print(f"[OK] Analysis complete! Gemini: {gemini_count} stocks | Claude fallback: {claude_count} stocks")
    print(f"{'='*80}")

    return analyzed


if __name__ == "__main__":
    # Test the module
    print("=" * 60)
    print("THEME ANALYZER - TEST MODE")
    print("=" * 60)

    # Test with a sample mover
    test_movers = [{
        'ticker': 'NVDA',
        'current_price': 150.0,
        'price_5d_ago': 120.0,
        'move_pct': 25.0,
        'date': '2024-01-15'
    }]

    results = analyze_all_movers(test_movers)

    print("\n" + "=" * 60)
    print("ANALYSIS RESULT:")
    print("=" * 60)
    for result in results:
        print(f"Ticker: {result['ticker']}")
        print(f"Move: +{result['move_pct']}%")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Summary: {result.get('summary', 'N/A')}")
        print(f"Theme: {result.get('primary_theme', 'N/A')}")
        print(f"Sub-niche: {result.get('sub_niche', 'N/A')}")
        print(f"Role: {result.get('ecosystem_role', 'N/A')}")
