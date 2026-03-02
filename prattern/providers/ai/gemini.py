"""Gemini AI batch classification provider — uses google.genai SDK."""

import json
import time
from typing import Dict, List

from prattern.config import Config


def _parse_gemini_json(response_text: str, expected_count: int) -> List[Dict]:
    """Parse JSON array from Gemini response, handling markdown blocks and truncation."""
    fallback = [{"category": "Unknown", "summary": "Gemini parse error", "primary_theme": "Other", "sub_niche": "Unknown", "ecosystem_role": "Platform"} for _ in range(expected_count)]

    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    if "[" in response_text and "]" in response_text:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        response_text = response_text[start:end]

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
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

    while len(data) < expected_count:
        data.append({"category": "Unknown", "summary": "Not classified", "primary_theme": "Other", "sub_niche": "Unknown", "ecosystem_role": "Platform"})

    return data


class GeminiClassifier:
    """Primary AI classifier using Google Gemini (google.genai SDK)."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-init the genai client on first use."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=Config.GEMINI_KEY)
        return self._client

    def classify_batch(self, movers_with_news: List[Dict]) -> List[Dict]:
        """
        Single Gemini call per batch does categorization + summary + theme classification.
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
            from google.genai import types

            client = self._get_client()

            # Strip "models/" prefix if present — new SDK doesn't need it
            model_name = Config.GEMINI_MODEL
            if model_name.startswith("models/"):
                model_name = model_name[len("models/"):]

            gen_config = types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                max_output_tokens=8192,
            )

            allowed_categories = ", ".join(Config.CLAUDE_CATEGORIES)
            allowed_themes = ", ".join(Config.GEMINI_THEMES)
            batch_size = 7
            results = []

            print(f"\n[GEMINI] Analyzing {len(movers_with_news)} stocks (categorize + theme + summary)...")

            for i in range(0, len(movers_with_news), batch_size):
                batch = movers_with_news[i:i + batch_size]

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

                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=gen_config,
                        )
                        response_text = response.text.strip()
                        print(f"   [DEBUG] Gemini response length: {len(response_text)} chars")

                        if len(response_text) > 0:
                            print(f"   [DEBUG] Response preview: {response_text[:200]}...")

                        parsed = _parse_gemini_json(response_text, len(batch))

                        for idx, obj in enumerate(parsed):
                            if idx < len(batch):
                                category = obj.get("category", "Unknown")
                                if category not in Config.CLAUDE_CATEGORIES:
                                    category = "Unknown"

                                primary_theme = obj.get("primary_theme", "Other")
                                if primary_theme not in Config.GEMINI_THEMES:
                                    primary_theme = "Other"

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

                        if i + batch_size < len(movers_with_news):
                            print(f"   [WAIT] Pausing 5s between batches...")
                            time.sleep(5)

                        break

                    except Exception as e:
                        wait_time = 2 ** attempt
                        error_msg = str(e)
                        print(f"   [!] Retry {attempt + 1}/3 after {wait_time}s: {error_msg[:80]}")

                        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                            backoff = wait_time * 5
                            print(f"   [WARNING] Rate limit detected! Waiting {backoff}s...")
                            time.sleep(backoff)
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

    def classify_single(self, ticker: str, move_pct: float, current_price: float,
                        price_5d_ago: float, headlines: List[str]) -> Dict:
        """Classify a single mover by wrapping it in a batch of one."""
        mover = {
            'ticker': ticker,
            'move_pct': move_pct,
            'current_price': current_price,
            'price_5d_ago': price_5d_ago,
            'headlines': headlines,
        }
        results = self.classify_batch([mover])
        return results[0] if results else {'category': 'Unknown', 'summary': 'Classification failed'}
