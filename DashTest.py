# streamlit_app.py
import streamlit as st
from AgentTeam import DataScraper_agent, Summarizer_agent, MarketResearch_agent, TrendAnalyzer_agent

st.set_page_config(page_title="Market Insights Dashboard", layout="wide")

st.title("📊 Multi-Agent Market Research System")
query = st.text_input("Enter your query:", "What are the latest trends in online grocery delivery services?")

if st.button("Run Agents"):
    with st.spinner("Running Data Scraper..."):
        scraper_out = DataScraper_agent(query)
        st.subheader("🔎 Data Scraper Output")
        st.json(scraper_out)

    with st.spinner("Running Summarizer..."):
        summary_out = Summarizer_agent()
        st.subheader("📝 Summarizer Output")
        st.json(summary_out)

    with st.spinner("Running Market Research..."):
        research_out = MarketResearch_agent()
        st.subheader("📈 Market Research Insights")
        st.write(research_out["insights"])

    with st.spinner("Running Trend Analyzer..."):
        trend_out = TrendAnalyzer_agent()
        st.subheader("📊 Trend Analyzer Trends")
        st.write(trend_out["trends"])
