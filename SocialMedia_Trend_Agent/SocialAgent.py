# SocialTrends_agent.py
import os, json, re
import pandas as pd
import snscrape_patch
import snscrape.modules.twitter as sntwitter
from twikit import Client
import praw
from phi.agent import Agent
from phi.model.groq import Groq
import asyncio
from dotenv import load_dotenv

load_dotenv()




# --------------------------
# Reddit API Setup (Free)
# --------------------------
reddit = praw.Reddit(
    client_id="D_me8FcA9CGnYzG1K_k4Lg",       # get from https://www.reddit.com/prefs/apps
    client_secret="xd6cv-9ytztAq89V-EotdW6KEexxvw",
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
client = Client(language='en-US')
client.load_cookies("C:/Users/CHAMA COMPUTERS/Desktop/Data_Science/Academic/IRWA/Project/AgenticAI_project/Market_Researcher_AgenticAI/cookies_fixed.json")  # make sure cookies.json is exported from your browser

def fetch_twitter_posts(query: str, limit: int = 20):
    async def _fetch():
        posts = []
        tweets = await client.search_tweet(query, product='Top', count=limit)
        for tweet in tweets:
            posts.append({"platform": "Twitter", "text": tweet.text})
        return posts
    
    return asyncio.run(_fetch())

# --------------------------
# Combine sources
# --------------------------
def fetch_social_posts(query: str, limit: int = 20):
    reddit_data = fetch_reddit_posts(query, limit=limit//2)
    #twitter_data = fetch_twitter_posts(query, limit=limit//2)
    return reddit_data

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
    raw = response
    print(raw)


    try:
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        return []
    return []


results = SocialTrends_agent("Global Smartphone market")
print(results)
