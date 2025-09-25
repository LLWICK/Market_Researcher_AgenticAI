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
        """
You are a Social Trends Analysis agent.

Task:
- Analyze the given list of social media posts.
- Identify market trends mentioned in the posts.
- Count how many posts mention each trend.
- Determine the sentiment of each trend: positive, negative, or neutral.

Output requirements:
- ONLY output a valid JSON array of objects.
- Each object must have exactly these fields:
    {
        "trend": "<string, trend description>",
        "mentions": <integer, number of posts mentioning the trend>,
        "sentiment": "<positive|negative|neutral>"
    }
- DO NOT include any explanations, reasoning, <think> tags, or extra text.
- Ensure the JSON is parseable and contains no trailing commas.

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
    }
]
"""
    ),
)

# --------------------------
# JSON extraction helper
# --------------------------
def extract_json_from_response(messages):
    """
    Extract JSON array from a list of Phi messages.
    """
    for m in messages:
        if not m.content:
            continue
        text = m.content

        # Remove <think> tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Remove code fences
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = text.strip()

        # Try to find JSON array
        match = re.search(r"\[\s*{.*?}\s*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    return match


def clean_agent_output(text: str) -> str:
    """
    Clean agent output by removing think tags and other unwanted elements
    """
    if not text:
        return text
    
    # Remove <think>...</think> tags and their content
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove any remaining opening/closing think tags
    text = re.sub(r'</?think[^>]*>', '', text, flags=re.IGNORECASE)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\n\s*\n+', '\n', text)
    text = text.strip()
    
    return text



def extract_trends_from_agent_response(response):
    """
    Extracts the JSON trends array from a Phi Agent RunResponse.

    Args:
        response: RunResponse object returned by agent.run()

    Returns:
        List of trend dictionaries, e.g.:
        [
            {"trend": "Fiat's marketing campaign", "mentions": 1, "sentiment": "negative"},
            ...
        ]
    """
    trends = []

    # Loop through all messages in the response
    for msg in getattr(response, "messages", []):
        if not getattr(msg, "content", None):
            continue

        text = msg.content

        # Remove <think> tags and everything inside
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Remove code fences ``` or ```json
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = text.strip()

        # Look for JSON array inside the text
        match = re.search(r"\[\s*{.*?}\s*\]", text, flags=re.DOTALL)
        if match:
            try:
                trends = json.loads(match.group())
                return trends  # Return first valid JSON array found
            except json.JSONDecodeError:
                continue

    # If nothing found, return empty list
    return trends

# --------------------------
# Main agent function
# --------------------------
def SocialTrends_agent(query: str):
    posts = fetch_social_posts(query, limit=20)
    response = social_agent.run(f"Analyze these posts for trends: {posts}")

    #trends = extract_trends_from_agent_response(response)
    return response.messages

# --------------------------
# Example usage
# --------------------------



""" if __name__ == "__main__":
    results = SocialTrends_agent("Automobile market")
    print(results) """