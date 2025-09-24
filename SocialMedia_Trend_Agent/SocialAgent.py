# SocialTrends_agent.py
import os, json, re
import pandas as pd
import snscrape.modules.twitter as sntwitter
import praw
from phi.agent import Agent
from phi.model.groq import Groq

# --------------------------
# Reddit API Setup (Free)
# --------------------------
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",       # get from https://www.reddit.com/prefs/apps
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="SocialTrendsAgent"
)

def fetch_reddit_posts(query: str, limit: int = 20):
    posts = []
    for submission in reddit.subreddit("all").search(query, limit=limit):
        posts.append({"platform": "Reddit", "text": submission.title})
    return posts

# --------------------------
# Twitter (snscrape, Free)
# --------------------------
def fetch_twitter_posts(query: str, limit: int = 20):
    posts = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{query} since:2024-09-01").get_items()):
        if i >= limit:
            break
        posts.append({"platform": "Twitter", "text": tweet.content})
    return posts

# --------------------------
# Combine sources
# --------------------------
def fetch_social_posts(query: str, limit: int = 20):
    reddit_data = fetch_reddit_posts(query, limit=limit//2)
    twitter_data = fetch_twitter_posts(query, limit=limit//2)
    return reddit_data + twitter_data

# --------------------------
# LLM Agent
# --------------------------
llm = Groq(id="deepseek-r1-distill-llama-70b", api_key=os.getenv("GROQ_API_KEY"))

social_agent = Agent(
    name="Social Trends Agent",
    model=llm,
    instructions=(
        "Analyze the provided social media posts and extract clear market trends. "
        "Return a JSON list with fields: trend (str), mentions (int), sentiment (positive/negative/neutral)."
    ),
)

def SocialTrends_agent(query: str):
    posts = fetch_social_posts(query, limit=20)
    response = social_agent.run(f"Analyze these posts for trends: {posts}")
    raw = response.output_text.strip()

    try:
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        return []
    return []
