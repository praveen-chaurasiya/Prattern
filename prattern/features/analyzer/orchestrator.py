"""Analysis orchestrator — wires news, primary AI, and fallback AI together."""

from typing import List, Dict

from prattern.config import Config
from prattern.providers import get_provider


def analyze_all_movers(movers: List[Dict], on_progress: callable = None) -> List[Dict]:
    """
    Analyze all movers: primary AI does 90%+ of work, fallback handles unknowns only.

    Pipeline:
    - Step 1: Fetch news for all stocks
    - Step 2: Batch ALL stocks to primary AI (categorize + theme + summary in one pass)
    - Step 3: Filter unknowns -> send only those to fallback AI
    - Step 4: Return merged results

    Args:
        movers: List of mover dicts from data_fetcher
        on_progress: Optional callback(dict) with keys: stage, current, total, detail
    """
    def _report(stage: str, current: int, total: int, detail: str = ""):
        if on_progress:
            try:
                on_progress({"stage": stage, "current": current, "total": total, "detail": detail})
            except Exception:
                pass

    if not movers:
        return []

    news = get_provider("news", Config.NEWS_PROVIDER)
    ai_primary = get_provider("ai", Config.AI_PRIMARY_PROVIDER)
    ai_fallback = get_provider("ai", Config.AI_FALLBACK_PROVIDER)

    total = len(movers)

    print(f"\n{'='*80}")
    print(f"THEME ANALYZER - Processing {total} movers")
    print(f"{'='*80}")

    # Step 1: Fetch news for all stocks
    print(f"\n[STEP 1/3] Fetching News")
    print(f"{'='*80}")

    for idx, mover in enumerate(movers, 1):
        ticker = mover['ticker']
        print(f"\n[{idx}/{total}] [NEWS] Fetching news for {ticker}...")
        _report("news", idx, total, f"Fetching news for {ticker}")
        headlines = news.fetch_headlines(ticker, max_headlines=Config.MAX_NEWS_HEADLINES)
        mover['headlines'] = headlines
        if headlines:
            print(f"   [OK] Found {len(headlines)} headlines")
        else:
            print(f"   [WARNING] No headlines found")

    # Step 2: Primary AI batch analysis (categorize + theme + summary)
    print(f"\n\n[STEP 2/3] Primary AI Analysis ({Config.AI_PRIMARY_PROVIDER})")
    print(f"{'='*80}")

    batch_size = 7
    total_batches = (total + batch_size - 1) // batch_size
    _report("primary_ai", 0, total_batches, f"Starting {Config.AI_PRIMARY_PROVIDER} batch analysis")

    analyzed = ai_primary.classify_batch(movers)

    _report("primary_ai", total_batches, total_batches, f"{Config.AI_PRIMARY_PROVIDER} analysis complete")

    # Step 3: Fallback AI for unknowns or failed theme classifications
    needs_fallback = [
        m for m in analyzed
        if m.get('category') == 'Unknown'
        or m.get('sub_niche') == 'Classification Failed'
        or m.get('primary_theme') == 'Other'
    ]
    print(f"\n\n[STEP 3/3] Fallback AI ({Config.AI_FALLBACK_PROVIDER})")
    print(f"{'='*80}")

    if needs_fallback:
        print(f"[FALLBACK] {len(needs_fallback)} stocks need fallback: {', '.join(m['ticker'] for m in needs_fallback)}")
        for ci, m in enumerate(needs_fallback, 1):
            print(f"   [FALLBACK] Analyzing {m['ticker']}...")
            _report("fallback_ai", ci, len(needs_fallback), f"Fallback for {m['ticker']}")
            fallback_result = ai_fallback.classify_single(
                ticker=m['ticker'],
                move_pct=m['move_pct'],
                current_price=m['current_price'],
                price_5d_ago=m['price_5d_ago'],
                headlines=m.get('headlines', [])
            )
            if m.get('category') == 'Unknown':
                m['category'] = fallback_result['category']
            m['summary'] = fallback_result['summary']
            if m.get('sub_niche') == 'Classification Failed' or m.get('primary_theme') == 'Other':
                m['primary_theme'] = fallback_result.get('primary_theme', m.get('primary_theme'))
                m['sub_niche'] = fallback_result.get('sub_niche', m.get('sub_niche'))
                m['ecosystem_role'] = fallback_result.get('ecosystem_role', m.get('ecosystem_role'))
            print(f"   [+] Fallback: {fallback_result['category']} | {fallback_result.get('primary_theme')} | {fallback_result.get('sub_niche')}")
    else:
        print(f"[OK] No fallbacks needed -- primary AI handled all {len(analyzed)} stocks!")

    print(f"\n{'='*80}")
    primary_count = len(analyzed) - len(needs_fallback)
    fallback_count = len(needs_fallback)
    print(f"[OK] Analysis complete! {Config.AI_PRIMARY_PROVIDER}: {primary_count} stocks | {Config.AI_FALLBACK_PROVIDER} fallback: {fallback_count} stocks")
    print(f"{'='*80}")

    _report("complete", total, total, f"Done -- {Config.AI_PRIMARY_PROVIDER}: {primary_count}, {Config.AI_FALLBACK_PROVIDER}: {fallback_count}")

    return analyzed
