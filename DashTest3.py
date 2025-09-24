import streamlit as st
import pandas as pd
from  TrendChart2 import run_pipeline_b   # change `your_module` to your actual filename (e.g. pipeline_b)
import altair as alt

st.set_page_config(page_title="Pipeline B Test", layout="wide")
st.title("🔬 Market Scope → Trend → Tickers → Performance (Pipeline B)")
# --- Minimal CSS for cards and chips ---
st.markdown("""
    <style>
    .card {padding:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.04);}
    .card h4 {margin:0 0 8px 0;}
    .chip {display:inline-block;padding:6px 10px;margin:4px;border-radius:16px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.06);font-size:0.9rem;}
    .muted {opacity:0.8;font-size:0.85rem;}
    .rank-item{display:flex;align-items:center;gap:10px;padding:10px 12px;margin:8px 0;border-radius:12px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03)}
    .rank-badge{font-weight:700;padding:4px 10px;border-radius:999px;font-size:0.9rem;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.06)}
    .rank-name{font-size:1rem}
    .gold{background:linear-gradient(180deg, rgba(255,215,0,0.18), rgba(255,215,0,0.06));}
    .gold .rank-badge{background:linear-gradient(180deg, #FFD700, #E6C200);color:#1d1d1d;border-color:#E6C200}
    .silver{background:linear-gradient(180deg, rgba(192,192,192,0.18), rgba(192,192,192,0.06));}
    .silver .rank-badge{background:linear-gradient(180deg, #C0C0C0, #AFAFAF);color:#1d1d1d;border-color:#B5B5B5}
    .bronze{background:linear-gradient(180deg, rgba(205,127,50,0.18), rgba(205,127,50,0.06));}
    .bronze .rank-badge{background:linear-gradient(180deg, #CD7F32, #B96F28);color:#1d1d1d;border-color:#B96F28}
    .card h4 .sub{opacity:.65;font-weight:500;margin-left:6px;font-size:.9rem}
    </style>
""", unsafe_allow_html=True)
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
query = st.text_input("Enter your market query:", "Global Smartphone market")


if st.button("Run Pipeline B"):
    with st.spinner("Running pipeline..."):
        results = run_pipeline_b(query)
        # ---- Summary row ----
        try:
            scope = results.get("scope", {}) or {}
            geo = (scope.get("countries") or scope.get("regions") or ["Global"])[0] if isinstance(scope, dict) else "Global"
            sectors = ", ".join(scope.get("sectors", [])[:2]) if isinstance(scope, dict) else ""
            perf = results.get("performance", {}) or {}
            rt = perf.get("resolved_tickers", []) if isinstance(perf, dict) else []
            c1, c2, c3 = st.columns(3)
            c1.metric("Geo", geo)
            c2.metric("Sector(s)", sectors if sectors else "—")
            c3.metric("Resolved Tickers", len([r for r in rt if r.get('ticker')]))
        except Exception:
            pass
    # --- Resolved Tickers ---
    with st.expander("🔤 Major player Tickers", expanded=True):
        perf = results.get("performance", {}) or {}
        rt = perf.get("resolved_tickers", []) if isinstance(perf, dict) else []
        if rt:
            df_rt = pd.DataFrame([{
                "Company": r.get("name"),
                "Ticker": r.get("ticker"),
                "Exchange": r.get("exchange"),
                "Confidence": r.get("confidence")
            } for r in rt])
            st.dataframe(df_rt, use_container_width=True)
        else:
            st.info("No tickers resolved.")
    # --- Sector Average Performance (index) ---
    with st.expander("📈 Sector Average Performance (index)", expanded=True):
        sp = results.get("sector_performance", {})
        try:
            if isinstance(sp, dict) and sp.get("sector_performance"):
                ts_obj = sp["sector_performance"]
                df_sp = _series_to_df(ts_obj)
                try:
                    df_sp = df_sp.apply(pd.to_numeric, errors="coerce")
                except Exception:
                    pass
                # Prepare YoY DataFrame
                years = list(map(str, ts_obj.get("x") or []))
                vals = []
                try:
                    series0 = (ts_obj.get("series") or [])[0] if isinstance(ts_obj.get("series"), list) else {}
                    vals = series0.get("data") or []
                except Exception:
                    vals = []
                n = min(len(years), len(vals))
                years = years[:n]
                vals = vals[:n]
                yoy = []
                for i in range(1, len(vals)):
                    try:
                        base = float(vals[i-1])
                        curr = float(vals[i])
                        pct = None if base in (None, 0) else ((curr - base) / base) * 100.0
                        yoy.append(None if pct is None else round(pct, 2))
                    except Exception:
                        yoy.append(None)
                yoy_years = years[1:] if len(years) > 1 else []
                df_yoy = pd.DataFrame({"YoY %": yoy}, index=yoy_years)

                # ---- Charts: index (left) and YoY bars (right) ----
                c1, c2 = st.columns([2,1])
                with c1:
                    if not df_sp.empty:
                        st.line_chart(df_sp)
                        st.caption("Index rebased to 100 at the first available year.")
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
        try:
            chart_data = trend["charts"][0]["series"][0]["data"]
        except Exception:
            chart_data = []
        if chart_data:
            # chart_data is [[name, value], ...]; values may be None
            names = [row[0] for row in chart_data if isinstance(row, (list, tuple)) and len(row) >= 1]
            vals  = [row[1] for row in chart_data if isinstance(row, (list, tuple)) and len(row) >= 2]
            if any(v is not None for v in vals):
                df = pd.DataFrame(chart_data, columns=["Company", "Market Value"]).dropna()
                if not df.empty:
                    st.bar_chart(df.set_index("Company"))
                    st.caption("Market capitalization for top companies (if available).")
                else:
                    st.write(", ".join(names))
            else:
                # Fallback: use latest relative performance index from timeseries if available
                perf_fallback = results.get("performance", {}) or {}
                ts_fb = perf_fallback.get("timeseries", {}) or {}
                ser_fb = ts_fb.get("series") or []
                latest_map = {}
                for s in ser_fb:
                    try:
                        label = s.get("name") or s.get("ticker") or "series"
                        data = [v for v in (s.get("data") or []) if v is not None]
                        if data:
                            latest_map[label] = float(data[-1])
                    except Exception:
                        pass
                if latest_map:
                    df_fb = pd.DataFrame(
                        {"Company": list(latest_map.keys()), "Relative Index": list(latest_map.values())}
                    ).set_index("Company")
                    st.bar_chart(df_fb)
                    st.caption("Fallback: latest relative performance index (rebased), not market cap.")
                else:
                    # Render names as chips for a nicer look
                    chips_html = "".join([f"<span class='chip'>{n}</span>" for n in names])
                    st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.info("No trend data.")
    else:
        st.info("No trend data.")


    # --- Market Performance ---
    st.header("📈 Market Performance (Rebased Index)")
    perf = results.get("performance", {})

    if isinstance(perf, dict) and isinstance(perf.get("timeseries"), dict) and (perf["timeseries"].get("series") or perf["timeseries"].get("x")):
        try:
            ts = perf.get("timeseries") or {"x": [], "series": []}
            x_vals = ts.get("x", []) or []
            cols = {}
            for s in (ts.get("series") or []):
                label = (s.get("name") or s.get("ticker") or "series")
                data = list(s.get("data") or [])
                # skip completely empty series (prevents ValueError)
                if len(data) == 0:
                    continue
                # pad/truncate to match index length
                if len(x_vals) == 0:
                    continue
                if len(data) < len(x_vals):
                    data = data + [None] * (len(x_vals) - len(data))
                elif len(data) > len(x_vals):
                    data = data[:len(x_vals)]
                cols[label] = data

            if cols:
                df = pd.DataFrame(cols, index=x_vals)
                df = df.apply(pd.to_numeric, errors="coerce")
                st.line_chart(df)
                st.caption("Price-index series rebased to 100 at the first available year.")
            else:
                st.info("No performance data.")
        except Exception:
            st.info("No performance data.")
    else:
        st.info("No performance data.")

    # ===== Extended Metrics =====
    st.header("🧩 Extended Metrics")

    # Adoption: early vs current
    with st.expander("🚀 Customer Base Shifts — early companies vs current top companies the largest customer base", expanded=True):
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
                return names[:3]

            early_names = _name_list(ea)
            current_names = _name_list(cu)

            def _podium_html(title: str, names: list[str]) -> str:
                # Build three ranked rows with gold/silver/bronze styles
                ranks = ["gold","silver","bronze"]
                medals = ["🥇","🥈","🥉"]
                rows = []
                for i, n in enumerate(names[:3]):
                    cls = ranks[i] if i < 3 else ""
                    badge = f"{medals[i]} {i+1}"
                    rows.append(f"<div class='rank-item {cls}'><span class='rank-badge'>{badge}</span><span class='rank-name'>{n}</span></div>")
                if not rows:
                    return "<div class='muted'>No data was extracted.</div>"
                return f"""\n<div class='card'>\n  <h4>{title}<span class='sub'>ranked</span></h4>\n  {''.join(rows)}\n</div>\n"""  # noqa: E501

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(_podium_html("Top 3 Early Adopters", early_names), unsafe_allow_html=True)
            with c2:
                st.markdown(_podium_html("Top 3 Current Customer Base Dominators", current_names), unsafe_allow_html=True)

            st.caption("Rank 1–3 shown with gold/silver/bronze styling; scores omitted by design. This is different than market capitalization. This is the amount of products consmer population use.")
        except Exception:
            st.info("No data was extracted.")

    # Event-driven spikes (token-free, price-based)
    with st.expander("⚡ Event-driven Spikes — price-based detector", expanded=True):
        ps = results.get("price_spikes", {})
        try:
            ev = ps.get("events_detected", []) if isinstance(ps, dict) else []
            st.markdown(
                """
                **How to read:**
                - **Direction**: ▲ up / ▼ down
                - **1-Day %**: Close-to-close percent change around the event date.
                - **Period %**: Cumulative percent change from the start of the analysis window.
                - **Magnitude**: qualitative size (low/medium/high)
                - **Confidence**: model confidence (0–100%)
                """
            )
            if ev:
                rows = []
                for e in ev:
                    try:
                        rows.append({
                            "Date": e.get("date"),
                            "Ticker/Company": e.get("entity_or_topic"),
                            "Headline": e.get("headline"),
                            "Direction": "▲" if (e.get("direction") == "+") else ("▼" if e.get("direction") == "-" else "~"),
                            "1-Day %": None if e.get("price_move_1d_pct") is None else round(float(e.get("price_move_1d_pct")), 2),
                            "Period %": None if e.get("price_move_period_pct") is None else round(float(e.get("price_move_period_pct")), 2),
                            "Magnitude": e.get("magnitude"),
                            "Confidence": None if e.get("confidence") is None else round(float(e.get("confidence")) * 100.0, 1),
                            "Reason": e.get("blurb")
                        })
                    except Exception:
                        pass
                df_ev = pd.DataFrame(rows)
                if not df_ev.empty:
                    st.dataframe(df_ev, use_container_width=True)
                else:
                    st.info("No data was extracted.")
            else:
                st.info("No data was extracted.")
        except Exception:
            st.info("No data was extracted.")