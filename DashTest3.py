import streamlit as st
import pandas as pd
from  TrendChart import run_pipeline_b   # change `your_module` to your actual filename (e.g. pipeline_b)
import altair as alt

st.set_page_config(page_title="Pipeline B Test", layout="wide")
st.title("🔬 Market Scope → Trend → Tickers → Performance (Pipeline B)")
# --- Helpers ---
def _series_to_df(timeseries: dict) -> pd.DataFrame:
    """Convert {'x':[], 'series':[{'name':..,'data':[...]}, ...]} to DataFrame indexed by x."""
    if not isinstance(timeseries, dict):
        return pd.DataFrame()
    x = timeseries.get("x") or []
    ser = timeseries.get("series") or []
    if not x or not ser:
        return pd.DataFrame()
    data = {}
    min_len = None
    for s in ser:
        name = s.get("name") or s.get("ticker") or "series"
        vals = s.get("data") or []
        n = min(len(x), len(vals))
        min_len = n if min_len is None else min(min_len, n)
        data[name] = vals[:n]
    idx = x[: (min_len or len(x))]
    return pd.DataFrame(data, index=idx)

# User query
query = st.text_input("Enter your market query:", "Cloud security vendors in the US")

if st.button("Run Pipeline B"):
    with st.spinner("Running pipeline..."):
        results = run_pipeline_b(query)
    # --- Sector Average Performance (index) ---
    with st.expander("📈 Sector Average Performance (index)", expanded=True):
        sp = results.get("sector_performance", {})
        try:
            ts_sp = (sp.get("sector_performance", {}) or {}).get("series")
            if isinstance(sp, dict) and sp.get("sector_performance"):
                ts_obj = sp["sector_performance"]
                df_sp = _series_to_df(ts_obj)

                # ---- KPI + YoY prep ----
                # Expect yearly index rebased=100; x are years (strings)
                years = list(map(str, ts_obj.get("x") or []))
                vals = []
                try:
                    series0 = (ts_obj.get("series") or [])[0] if isinstance(ts_obj.get("series"), list) else {}
                    vals = series0.get("data") or []
                except Exception:
                    vals = []
                # Ensure alignment
                n = min(len(years), len(vals))
                years = years[:n]
                vals = vals[:n]
                # Compute YoY list
                yoy = []
                for i in range(1, len(vals)):
                    try:
                        base = float(vals[i-1])
                        curr = float(vals[i])
                        pct = None if base in (None, 0) else ((curr - base) / base) * 100.0
                        yoy.append(None if pct is None else round(pct, 2))
                    except Exception:
                        yoy.append(None)
                # Current YoY (last vs previous)
                curr_yoy = None
                if len(yoy) >= 1 and yoy[-1] is not None:
                    curr_yoy = yoy[-1]
                # Build YoY DataFrame
                yoy_years = years[1:] if len(years) > 1 else []
                df_yoy = pd.DataFrame({"YoY %": yoy}, index=yoy_years)
  
                # ---- Best/Worst performer from Trend Charts (if available) ----
                tcandidates = results.get("trend") or results.get("market_performance") or results.get("timeseries") or {}
                ts_obj_tc = tcandidates.get("timeseries") if isinstance(tcandidates, dict) and "timeseries" in tcandidates else tcandidates
                df_tc = _series_to_df(ts_obj_tc) if isinstance(ts_obj_tc, dict) else pd.DataFrame()
                best_name, best_change, worst_name, worst_change = None, None, None, None
                if not df_tc.empty:
                    try:
                        first = df_tc.iloc[0]
                        last = df_tc.iloc[-1]
                        pct = (last - first) / first.replace({0: pd.NA}) * 100.0
                        pct = pct.dropna()
                        if not pct.empty:
                            best_name = str(pct.idxmax())
                            best_change = round(float(pct.max()), 2)
                            worst_name = str(pct.idxmin())
                            worst_change = round(float(pct.min()), 2)
                    except Exception:
                        pass
  
                # ---- KPI row ----
                k1, k2, k3 = st.columns(3)
                with k1:
                    if curr_yoy is not None:
                        delta_txt = f"{curr_yoy:+.2f}% vs prev year"
                        st.metric("Sector YoY (latest)", f"{float(vals[-1]):.2f}", delta_txt)
                    else:
                        st.metric("Sector YoY (latest)", "—", "n/a")
  
                # ---- Charts: index (left) and YoY bars (right) ----
                c1, c2 = st.columns([2,1])
                with c1:
                    if not df_sp.empty:
                        st.line_chart(df_sp)
                with c2:
                    if not df_yoy.empty:
                        yoy_chart = (
                            alt.Chart(df_yoy.reset_index(names="Year"))
                            .mark_bar()
                            .encode(
                                x=alt.X("Year:N", title="Year"),
                                y=alt.Y("YoY %:Q", title="YoY %"),
                                tooltip=[alt.Tooltip("Year:N"), alt.Tooltip("YoY %:Q", format=".2f")],
                            )
                        )
                        st.altair_chart(yoy_chart, use_container_width=True)
                    else:
                        st.caption("YoY: insufficient data")
            else:
                st.info("No data was extracted.")
        except Exception:
            st.info("No data was extracted.")

    # --- Trend Chart ---
    st.header("📊 Trend Chart (Top 5 Competitors)")
    trend = results.get("trend", {})

    if trend and "charts" in trend and len(trend["charts"]) > 0:
        chart_data = trend["charts"][0]["series"][0]["data"]
        if chart_data:
            df = pd.DataFrame(chart_data, columns=["Company", "Market Value"])
            st.bar_chart(df.set_index("Company"))


    # --- Market Performance ---
    st.header("📈 Market Performance (Rebased Index)")
    perf = results.get("performance", {})

    if perf and "timeseries" in perf and perf["timeseries"].get("series"):
        df = pd.DataFrame({
            s["name"]: s["data"]
            for s in perf["timeseries"]["series"]
        }, index=perf["timeseries"]["x"])
        st.line_chart(df)

    # ===== Extended Metrics =====
    st.header("🧩 Extended Metrics")

    # Adoption: early vs current
    with st.expander("🚀 Adoption — early adopters vs current top", expanded=True):
        ad = results.get("adoption", {})
        try:
            ad_root = ad.get("adoption", {}) if isinstance(ad, dict) else {}
            ea = ad_root.get("early_adopters_top3") or []
            cu = ad_root.get("current_adopters_top3") or ad_root.get("current_adopters_top5") or []

            def _name_list(items):
                names = []
                for it in items:
                    if isinstance(it, dict):
                        n = it.get("company") or it.get("region") or it.get("name")
                        if n:
                            names.append(str(n))
                # keep only top 3 visually
                return names[:3]

            early_names = _name_list(ea)
            current_names = _name_list(cu)

            c1, c2 = st.columns(2)
            with c1:
                with st.container():
                    st.subheader("Top 3 Early Adopters")
                    if early_names:
                        for n in early_names:
                            st.markdown(f"- {n}")
                    else:
                        st.info("No data was extracted.")
            with c2:
                with st.container():
                    st.subheader("Top 3 Current Adopters")
                    if current_names:
                        for n in current_names:
                            st.markdown(f"- {n}")
                    else:
                        st.info("No data was extracted.")

            st.caption("Listed in rank order when provided by the agent; scores are omitted by design.")
        except Exception:
            st.info("No data was extracted.")

    # Event-driven spikes (token-free, price-based)
    with st.expander("⚡ Event-driven Spikes — price-based detector", expanded=True):
        ps = results.get("price_spikes", {})
        try:
            ev = ps.get("events_detected", []) if isinstance(ps, dict) else []
            # Legend / how to read
            st.markdown(
                """
                **How to read:**
                - **Direction**: ▲ up / ▼ down
                - **1‑Day %**: Close-to-close percent change around the event date.
                - **Period %**: Cumulative percent change from the start of the analysis window.
                - **Magnitude**: qualitative size (low/medium/high)
                - **Confidence**: model confidence (0–100%)
                """
            )
            if ev:
                import pandas as _pd
                rows = []
                for e in ev:
                    try:
                        rows.append({
                            "Date": e.get("date"),
                            "Ticker/Company": e.get("entity_or_topic"),
                            "Headline": e.get("headline"),
                            "Direction": "▲" if (e.get("direction") == "+") else ("▼" if e.get("direction") == "-" else "~"),
                            "1‑Day %": None if e.get("price_move_1d_pct") is None else round(float(e.get("price_move_1d_pct")), 2),
                            "Period %": None if e.get("price_move_period_pct") is None else round(float(e.get("price_move_period_pct")), 2),
                            "Magnitude": e.get("magnitude"),
                            "Confidence": None if e.get("confidence") is None else round(float(e.get("confidence")) * 100.0, 1),
                            "Reason": e.get("blurb")
                        })
                    except Exception:
                        pass
                df_ev = _pd.DataFrame(rows)
                if not df_ev.empty:
                    st.dataframe(df_ev, use_container_width=True)
                else:
                    st.info("No data was extracted.")
            else:
                st.info("No data was extracted.")
        except Exception:
            st.info("No data was extracted.")