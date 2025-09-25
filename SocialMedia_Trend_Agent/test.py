import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from SocialAgent import SocialTrends_agent

# Sample data from your agent
trends = [
    {'trend': 'global auto industry price war due to EV cost dropping', 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'electric vehicle cost reduction', 'mentions': 1, 'sentiment': 'positive'},
    {'trend': 'EVs priced around $25,000', 'mentions': 1, 'sentiment': 'positive'},
    {'trend': 'Canada 2035 gas vehicle ban', 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'EVs inadequate for Canadian winters', 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'automakers turning to hybrids during EV transition', 'mentions': 1, 'sentiment': 'neutral'},
    {'trend': 'global EV adoption mandate deadlines approaching', 'mentions': 1, 'sentiment': 'neutral'},
    {'trend': 'bullish on lithium stocks due to EV demand', 'mentions': 1, 'sentiment': 'positive'},
    {'trend': "America's failure to transition to EVs", 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'over 100 electric vehicle brands in China being pushed out', 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'clean energy high IQ play including solar, hydrogen, nuclear', 'mentions': 1, 'sentiment': 'positive'},
    {'trend': 'climate change fatality', 'mentions': 1, 'sentiment': 'negative'},
    {'trend': 'Toyota increasing supply to Tesla of EV-use electric compressors', 'mentions': 1, 'sentiment': 'neutral'}
]


query = st.text_input("Enter your query:", "What are the latest trends in online grocery delivery services?")

if st.button("Run Agents") and query.strip():
    trends = SocialTrends_agent(query)

    # Convert to DataFrame
    df = pd.DataFrame(trends)

    st.set_page_config(page_title="Market Trend analysis", layout="wide")

    st.title("📈 EV Market Trends Analysis")
    st.markdown("Analysis of extracted market trends from social media posts.")

    # =========================
    # Sentiment Distribution
    # =========================
    st.subheader("🔹 Sentiment Distribution")

    sentiment_counts = df["sentiment"].value_counts()

    fig1, ax1 = plt.subplots()
    ax1.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={'edgecolor': 'white'}
    )
    ax1.set_title("Sentiment Breakdown")
    st.pyplot(fig1)

    # =========================
    # Mentions per Trend
    # =========================
    st.subheader("🔹 Mentions per Trend")

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    df_sorted = df.sort_values(by="mentions", ascending=False)
    ax2.barh(df_sorted["trend"], df_sorted["mentions"], color="skyblue")
    ax2.set_xlabel("Mentions")
    ax2.set_ylabel("Trend")
    ax2.set_title("Mentions per Trend")
    st.pyplot(fig2)

    # =========================
    # Trends Table
    # =========================
    st.subheader("🔹 Detailed Trends Data")
    st.dataframe(df, use_container_width=True)

    # =========================
    # Sentiment vs Mentions
    # =========================
    st.subheader("🔹 Sentiment vs Mentions")

    fig3, ax3 = plt.subplots(figsize=(7, 5))
    df.groupby("sentiment")["mentions"].sum().plot(kind="bar", ax=ax3, color=["green", "red", "gray"])
    ax3.set_ylabel("Total Mentions")
    ax3.set_title("Mentions by Sentiment")
    st.pyplot(fig3)

    # =========================
    # Highlight Insights
    # =========================
    st.subheader("🔹 Key Insights")
    st.markdown(f"""
    - **Total Trends Analyzed:** {len(df)}
    - **Most Frequent Sentiment:** {sentiment_counts.idxmax()} ({sentiment_counts.max()} mentions)
    - **Most Talked About Trend:** {df_sorted.iloc[0]['trend']} ({df_sorted.iloc[0]['mentions']} mentions)
    """)
