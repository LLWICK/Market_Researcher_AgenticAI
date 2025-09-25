# SocialTrends_agent.py
import os
import json
import re
import praw
from phi.agent import Agent
from phi.model.groq import Groq
from twikit import Client
from dotenv import load_dotenv
load_dotenv()

# --------------------------
# Reddit API Setup
# --------------------------
reddit = praw.Reddit(
    client_id="D_me8FcA9CGnYzG1K_k4Lg",
    client_secret="xd6cv-9ytztAq89V-EotdW6KEexxvw",
    user_agent="SocialTrendsAgent"
)

def fetch_reddit_posts(query: str, limit: int = 20):
    posts = []
    for submission in reddit.subreddit("all").search(query, limit=limit):
        posts.append({"platform": "Reddit", "text": submission.title})
    return posts

# --------------------------
# Twitter (Twikit)
# --------------------------
#client = Client(language='en-US')
#client.load_cookies("C:/Users/CHAMA COMPUTERS/Desktop/Data_Science/Academic/IRWA/Project/AgenticAI_project/Market_Researcher_AgenticAI/cookies_fixed.json")

def fetch_twitter_posts(query: str, limit: int = 20):
    posts = []
    tweets = client.search_tweet(query, product='Top', count=limit)
    for tweet in tweets:
        posts.append({"platform": "Twitter", "text": tweet.text})
    return posts

# --------------------------
# Combine sources
# --------------------------
def fetch_social_posts(query: str, limit: int = 20):
    reddit_data = fetch_reddit_posts(query, limit=limit // 2)
    #twitter_data = fetch_twitter_posts(query, limit=limit // 2)
    return reddit_data

# --------------------------
# LLM Agent Setup
# --------------------------
llm = Groq(id="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))

instructions = """
You are a Social Trends Analysis agent.

Task:
- Analyze ALL the provided social media posts.
- Go through each post individually.
- Identify every market trend mentioned in any post, even if it appears only once.
- Count exactly how many posts mention each trend.
- Determine the sentiment of each trend: positive, negative, or neutral.
- Do NOT omit minor or historical trends.
- ONLY output a JSON array with the fields:
    {
        "trend": "<string, trend description>",
        "mentions": <integer, number of posts mentioning the trend>,
        "sentiment": "<positive|negative|neutral>"
    }
- DO NOT include explanations, reasoning, <think> tags, or extra text.
- Ensure the JSON is valid and parseable, with no trailing commas.

Example output:
[
    {
        "trend": "Apple's growth in the smartphone market",
        "mentions": 4,
        "sentiment": "positive"
    },
    {
        "trend": "Market contraction due to COVID-19",
        "mentions": 3,
        "sentiment": "negative"
    },
    {
        "trend": "Rise of Chinese smartphone brands",
        "mentions": 2,
        "sentiment": "neutral"
    }
]
"""


social_agent = Agent(
    name="Social Trends Agent",
    model=llm,
    instructions=instructions
)

# --------------------------
# JSON Extraction Helper
# --------------------------
def extract_trends_from_agent_response(response):
    trends = []
    for msg in getattr(response, "messages", []):
        if not getattr(msg, "content", None):
            continue
        text = msg.content
        # Remove <think> tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Remove code fences
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = text.strip()
        # Find JSON array
        match = re.search(r"\[\s*{.*?}\s*\]", text, flags=re.DOTALL)
        if match:
            try:
                trends = json.loads(match.group())
                return trends
            except json.JSONDecodeError:
                continue
    return trends

# --------------------------
# Main Agent Function
# --------------------------
def SocialTrends_agent(query: str):
    posts = fetch_social_posts(query, limit=20)

    response = social_agent.run(f"Analyze these posts for trends: {posts}")

    try:
        # The model outputs JSON directly in response.content
        raw = response.content.strip()

        # Parse into Python list
        trends = json.loads(raw)
        return trends
    except Exception as e:
        print("JSON parsing error:", e)
        return []

# --------------------------
# Example Usage
# --------------------------
""" if __name__ == "__main__":
    results = SocialTrends_agent("Global EV vehicle industry")
    print(results) """
