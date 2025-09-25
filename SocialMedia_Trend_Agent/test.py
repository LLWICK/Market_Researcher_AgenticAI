import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from SocialAgent import SocialTrends_agent, extract_trends_from_agent_response

st.set_page_config(page_title="Social Trends Dashboard", layout="wide")

st.title("📊 Social Trends Dashboard")

# ---------------------------
# User Input
# ---------------------------
query = st.text_input("Enter a topic to analyze:", "Automobile market")

if query:
    with st.spinner("Fetching social posts and analyzing trends..."):
        # Run your agent
        response = SocialTrends_agent(query)
        trends = extract_trends_from_agent_response(response)

    if not trends:
        st.warning("No trends found for this query.")
    else:
        # ---------------------------
        # Prepare Data
        # ---------------------------
        df = pd.DataFrame(trends)
        df['sentiment'] = df['sentiment'].str.capitalize()  # Normalize for display

        # ---------------------------
        # Display Data
        # ---------------------------
        st.subheader("Trends Table")
        st.dataframe(df)

        # ---------------------------
        # Sentiment Distribution
        # ---------------------------
        st.subheader("Sentiment Distribution")
        sentiment_counts = df['sentiment'].value_counts()
        fig1, ax1 = plt.subplots()
        sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette="coolwarm", ax=ax1)
        ax1.set_ylabel("Number of Trends")
        ax1.set_xlabel("Sentiment")
        st.pyplot(fig1)

        # ---------------------------
        # Trend Mentions Chart
        # ---------------------------
        st.subheader("Trend Mentions")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.barplot(
            x="trend", y="mentions", hue="sentiment",
            data=df.sort_values("mentions", ascending=False),
            dodge=False, palette={"Positive": "green", "Negative": "red", "Neutral": "gray"}, ax=ax2
        )
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha="right")
        ax2.set_ylabel("Mentions")
        ax2.set_xlabel("Trend")
        st.pyplot(fig2)
