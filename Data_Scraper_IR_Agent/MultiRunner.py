# social_trends_agent_no_tools.py
import os, logging, json
from typing import List, Dict
from phi.agent import Agent
from phi.model.groq import Groq
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("SocialTrendsAgent")

# -------- Mock Data Fetcher (replace with APIs) --------
def fetch_social_data(query: str, limit: int = 20) -> List[Dict]:
    sample_posts = [
        {"platform": "twitter", "text": f"{query} is booming in AI startups"},
        {"platform": "reddit", "text": f"Investors are bullish on {query} in 2025"},
        {"platform": "twitter", "text": f"{query} market is expected to grow fast"},
    ]
    return sample_posts[:limit]

# --------- LLM ----------
llm = Groq(
    id="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
)

# --------- Agent ----------
social_agent = Agent(
    name="Social Trends Agent",
    model=llm,
    instructions=(
        "You analyze social media posts to extract trending topics. "
        "Always return JSON as a list of objects with keys: "
        "`trend` (string), `mentions` (int), `sentiment` ('positive'|'negative'|'neutral')."
    ),
)

# --------- Output validation ---------
class Trend(BaseModel):
    trend: str
    mentions: int
    sentiment: str

def parse_trends_output(raw: str) -> List[Dict]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        return [Trend(**t).dict() for t in parsed]
    except (json.JSONDecodeError, ValidationError) as e:
        log.warning(f"Failed to parse trends output: {e}")
        return []

# --------- Public function ---------
def get_trends(topic: str):
    """Run the agent to extract trends from social posts"""
    raw_posts = fetch_social_data(topic)
    response = social_agent.run(
        f"Analyze these posts and extract market trends: {raw_posts}"
    )

    # Extract text from RunResponse
    if hasattr(response, "output_text"):
        raw_text = response.output_text
    else:
        raw_text = str(response)  # fallback

    # Parse JSON
    import json
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        log.error(f"Failed to parse JSON: {raw_text}")
        return []

    return parsed



# --------- Example usage ---------
if __name__ == "__main__":
    trends = get_trends("Nvidia GPUs")
    print("Extracted Trends:")
    for t in trends:
        print(t)
