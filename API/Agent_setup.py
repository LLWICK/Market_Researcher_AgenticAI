# agents/team_b.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from AgentTeam import DataScraper_agent, Summarizer_agent, MarketResearch_agent
from SocialMedia_Trend_Agent.SocialAgent import SocialTrends_agent
from TrendChart2 import CompetitorTrend_agent, MarketTrendAnalyzer_agent, EventPriceSpike_agent
from utills.ta_helpers import _salvage_json_text
from utills.cleaning import remove_think_tags
from utills.extractUtills import extract_competitor_data,clean_text,extract_statistics_from_trends

import pandas as pd

def run_team_b(query: str):
    """Run all unstructured/research-based agents sequentially and return structured JSON output."""
    
    # 1️⃣ Data Scraper
    scraper_out = DataScraper_agent(query)
    scraped_docs = scraper_out.get("docs", [])
    
    # 2️⃣ Summarizer
    summary_out = Summarizer_agent()
    summary_text = remove_think_tags(summary_out.get("summary", ""))
    
    # 3️⃣ Market Research
    research_out = MarketResearch_agent()
    insights = remove_think_tags(clean_text(research_out.get("insights", "")))
    
    # 4️⃣ Social Media Trends
    trends = SocialTrends_agent(query)
    df_trends = pd.DataFrame(trends)
    
    # 5️⃣ Competitor Trends
    comp_trend_text = CompetitorTrend_agent(query)
    comp_trend = _salvage_json_text(comp_trend_text)
    
    # 6️⃣ Market Trend Analyzer
    market_trend_text = MarketTrendAnalyzer_agent(query)
    market_trend = _salvage_json_text(market_trend_text)
    
    # 7️⃣ Event-driven Price Spikes
    event_spike_text = EventPriceSpike_agent(query)
    event_spikes = _salvage_json_text(event_spike_text)
    
    return {
        "data_scraper_docs": scraped_docs[:5],
        "summary": summary_text,
        "market_insights": insights,
        "social_trends": df_trends.to_dict(orient="records"),
        "competitor_trend": comp_trend,
        "market_trend": market_trend,
        "event_spikes": event_spikes,
    }


#run_team_b("What are the latest trends in online grocery delivery services?")
