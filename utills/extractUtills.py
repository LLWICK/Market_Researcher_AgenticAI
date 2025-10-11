import pandas as pd
import re
import json
def extract_competitor_data(text: str):
    """
    Try to parse competitor comparison data from the LLM output.
    Expecting structured JSON like:
    [
      {"Competitor": "X", "Sales": 1000, "MarketShare": 20, "GrowthRate": 5},
      {"Competitor": "Y", "Sales": 2000, "MarketShare": 30, "GrowthRate": 10}
    ]
    """
    try:
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, list) and all(isinstance(d, dict) for d in data):
                return pd.DataFrame(data)
    except Exception as e:
        print(f"[extract_competitor_data] Failed: {e}")
    return None


def clean_text(text: str) -> str:
    """Remove unwanted characters and extra whitespace"""
    if not text:
        return "No data available."
    text = re.sub(r"[^\x00-\x7F]+", "", text)  # Remove non-ASCII
    text = re.sub(r"\n\s*\n+", "\n\n", text)   # Normalize newlines
    return text.strip()

def extract_statistics_from_trends(trends: str):
    """
    Try to parse structured statistics from trend text.
    Expecting something like JSON or percentage patterns inside the LLM output.
    """
    stats = {}
    try:
        # Look for JSON in the text
        json_match = re.search(r"\{.*\}", trends, re.DOTALL)
        if json_match:
            stats = json.loads(json_match.group())
        else:
            # Fallback: extract percentage stats from text
            matches = re.findall(r"([A-Za-z ]+):?\s?(\d+)%", trends)
            stats = {m[0].strip(): int(m[1]) for m in matches}
    except Exception as e:
        print(f"[extract_statistics_from_trends] Failed: {e}")
    return stats