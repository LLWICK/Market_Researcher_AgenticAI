import streamlit as st
import pandas as pd
from  TrendChart import run_pipeline_b   # change `your_module` to your actual filename (e.g. pipeline_b)

st.set_page_config(page_title="Pipeline B Test", layout="wide")
st.title("🔬 Market Scope → Trend → Tickers → Performance (Pipeline B)")

# User query
query = st.text_input("Enter your market query:", "Cloud security vendors in the US")

if st.button("Run Pipeline B"):
    with st.spinner("Running pipeline..."):
        results = run_pipeline_b(query)

    # --- Scope ---
    st.header("📌 Query Scope")
    st.json(results["scope"])

    # --- Trend Chart ---
    st.header("📊 Trend Chart (Top 5 Competitors)")
    trend = results.get("trend", {})
    st.json(trend)

    if trend and "charts" in trend and len(trend["charts"]) > 0:
        chart_data = trend["charts"][0]["series"][0]["data"]
        if chart_data:
            df = pd.DataFrame(chart_data, columns=["Company", "Market Value"])
            st.bar_chart(df.set_index("Company"))

    # --- Resolved Tickers ---
    st.header("🏷️ Resolved Tickers")
    st.json(results["tickers"])

    # --- Market Performance ---
    st.header("📈 Market Performance (Rebased Index)")
    perf = results.get("performance", {})
    st.json(perf)

    if perf and "timeseries" in perf and perf["timeseries"].get("series"):
        df = pd.DataFrame({
            s["name"]: s["data"]
            for s in perf["timeseries"]["series"]
        }, index=perf["timeseries"]["x"])
        st.line_chart(df)
