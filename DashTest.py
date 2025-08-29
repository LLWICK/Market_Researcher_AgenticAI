# streamlit_app.py
import streamlit as st
from AgentTeam import DataScraper_agent, Summarizer_agent, MarketResearch_agent

st.title("🧠 Multi-Agent Market Research Pipeline")

query = st.text_input("Enter your market research query:", "What are the latest trends in online grocery delivery services?")

if st.button("Run Pipeline"):
    with st.spinner("Scraping data..."):
        msg1 = DataScraper_agent(query)
        st.subheader("🔍 Step 1: Data Scraper")
        st.json(msg1.to_dict())

    with st.spinner("Summarizing insights..."):
        msg2 = Summarizer_agent(msg1)
        st.subheader("📝 Step 2: Summarizer")
        st.json(msg2.to_dict())

    with st.spinner("Analyzing market research..."):
        msg3 = MarketResearch_agent(msg2)
        st.subheader("📊 Step 3: Market Research")
        st.json(msg3.to_dict())

    """ with st.spinner("Analyzing trends..."):
        msg4 = TrendAnalyzer_agent(msg1)
        st.subheader("📈 Step 4: Trend Analyzer")
        st.json(msg4.to_dict()) """

    st.success("✅ Pipeline completed!")
