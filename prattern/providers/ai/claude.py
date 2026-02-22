"""Claude AI fallback classification provider."""

from typing import Dict, List

from anthropic import Anthropic

from prattern.config import Config


class ClaudeClassifier:
    """Fallback AI classifier using Anthropic Claude."""

    def classify_single(self, ticker: str, move_pct: float, current_price: float,
                        price_5d_ago: float, headlines: List[str]) -> Dict:
        """Use Claude API to categorize the stock move and generate summary."""
        if not Config.ANTHROPIC_KEY:
            print("[ERROR] ANTHROPIC_API_KEY not found in environment")
            return {'category': 'Unknown', 'summary': 'API key not configured'}

        try:
            client = Anthropic(api_key=Config.ANTHROPIC_KEY)

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

            message = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

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

            if category not in Config.CLAUDE_CATEGORIES:
                category = "Unknown"
            if primary_theme not in Config.GEMINI_THEMES:
                primary_theme = "Other"

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

    def classify_batch(self, movers_with_news: List[Dict]) -> List[Dict]:
        """Classify a batch by calling classify_single for each mover."""
        for mover in movers_with_news:
            result = self.classify_single(
                ticker=mover['ticker'],
                move_pct=mover['move_pct'],
                current_price=mover['current_price'],
                price_5d_ago=mover['price_5d_ago'],
                headlines=mover.get('headlines', [])
            )
            mover.update(result)
            if 'micro_theme' not in mover:
                mover['micro_theme'] = result.get('primary_theme', 'Other')
        return movers_with_news
