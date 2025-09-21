# streamlit_app.py
import streamlit as st
import re
import json
import matplotlib.pyplot as plt
import pandas as pd
from AgentTeam import DataScraper_agent, Summarizer_agent, MarketResearch_agent, TrendAnalyzer_agent, CompetitorComparison_agent

# ---------------------------
# Helpers
# ---------------------------


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

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Market Insights Dashboard", layout="wide")
st.title("📊 Multi-Agent Market Research System")

query = st.text_input("Enter your query:", "What are the latest trends in online grocery delivery services?")

if st.button("Run Agents") and query.strip():
    # ---------------------------
    # Data Scraper
    # ---------------------------
    with st.spinner("Running Data Scraper..."):
        scraper_out = DataScraper_agent(query)
        st.subheader("🔎 Data Scraper Output (Preview)")
        for i, doc in enumerate(scraper_out.get("docs", [])[:5]):
            st.text_area(f"Doc {i+1}: {doc[:500]}...", doc[:500], height=150)

    # ---------------------------
    # Summarizer
    # ---------------------------
    with st.spinner("Running Summarizer..."):
        summary_out = Summarizer_agent()
        st.subheader("📝 Summarizer Output")
        st.text_area("Summary", clean_text(summary_out.get("summary", "")), height=200)

    # ---------------------------
    # Market Research
    # ---------------------------
    with st.spinner("Running Market Research..."):
        research_out = MarketResearch_agent()
        st.subheader("📈 Market Research Insights")
        st.text_area("Insights", clean_text(research_out.get("insights", "")), height=200)

    # ---------------------------
    # Trend Analyzer
    # ---------------------------
    with st.spinner("Running Trend Analyzer..."):
        trend_out = TrendAnalyzer_agent()
        trends_text = clean_text(trend_out.get("trends", ""))

        st.subheader("📊 Trend Analyzer Trends")
        st.text_area("Trends", trends_text, height=250)

        # ---------------------------
        # Charts Section
        # ---------------------------
        stats = extract_statistics_from_trends(trends_text)
        if stats:
            st.subheader("📈 Trend Statistics (Charts)")
            df = pd.DataFrame(list(stats.items()), columns=["Category", "Value"])

            # Bar chart
            st.bar_chart(df.set_index("Category"))

            # Pie chart
            fig, ax = plt.subplots()
            ax.pie(df["Value"], labels=df["Category"], autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("No structured statistics found in the trend analysis output.")

            # ---------------------------

    # Competitor Comparison
    # ---------------------------
    with st.spinner("Running Competitor Comparison..."):
        # Pass scraped docs into the competitor comparison agent
        competitor_out = CompetitorComparison_agent(query=query, docs=scraper_out.get("docs", []))

        # Case 1: Already parsed JSON list
        if isinstance(competitor_out, list):
            df_comp = pd.DataFrame(competitor_out)
            comp_text = json.dumps(competitor_out, indent=2)
        else:
            # Case 2: Fallback (raw_output text)
            comp_text = clean_text(competitor_out.get("raw_output", "No competitor data."))
            df_comp = extract_competitor_data(comp_text)

        st.subheader("🏢 Competitor Comparison")
        st.text_area("Competitor Analysis", comp_text, height=250)

        if df_comp is not None and not df_comp.empty:
            st.subheader("📊 Competitor Sales & Market Share")

            # Bar chart for Sales
            if "Sales" in df_comp.columns:
                st.bar_chart(df_comp.set_index("Competitor")["Sales"])

            # Pie chart for Market Share
            if "MarketShare" in df_comp.columns:
                fig, ax = plt.subplots()
                ax.pie(df_comp["MarketShare"], labels=df_comp["Competitor"], autopct="%1.1f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)

            # Growth Rate line chart
            if "GrowthRate" in df_comp.columns:
                st.line_chart(df_comp.set_index("Competitor")["GrowthRate"])
        else:
            st.info("No structured competitor data found. Showing only raw analysis text above.")


