import polars as pl
from config import Config
from openai import OpenAI
import time
import json

client = OpenAI(
    api_key=Config.GEMINI_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def classify_themes(df):
    results = []
    allowed_themes = ", ".join(Config.THEME_CRITERIA)
    
    # Process 10 stocks at once to avoid 429 errors
    batch_size = 10 
    rows = df.to_dicts()
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        
        # Format multiple stocks into one request
        stocks_input = "\n".join([f"{r['ticker']}: {r['summary'][:300]}" for r in batch])
        
        system_instruction = f"""
        Classify these {len(batch)} stocks into ONE theme from: [{allowed_themes}]
        Return a JSON list of strings only. Example: ["Energy Storage", "Nuclear SMR"]
        """

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=Config.GEMINI_MODEL.replace("models/", ""),  # Use config model
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": stocks_input}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Parse the AI response back into the list
                themes = json.loads(response.choices[0].message.content)
                for idx, theme in enumerate(themes):
                    if idx < len(batch):
                        batch[idx]["micro_theme"] = theme
                break 

            except Exception as e:
                # Wait and retry if we hit a rate limit (429)
                time.sleep(2 ** attempt) 
                if attempt == 2:
                    for r in batch: r["micro_theme"] = f"Error: {str(e)[:20]}"

        results.extend(batch)
    
    return pl.DataFrame(results)