import streamlit as st
import pandas as pd
from TrendChart2 import CompetitorTrend_agent, MarketTrendAnalyzer_agent, EventPriceSpike_agent
from utills.ta_helpers import _altair_timeseries_chart, _salvage_json_text
import altair as alt
import numpy as np

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
    df = pd.DataFrame(data, index=idx)
    # coerce to numeric; None/strings -> NaN
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def _calc_kpis(timeseries: dict) -> dict:
    """Return simple KPIs: total return, CAGR, best/worst year."""
    df = _series_to_df(timeseries)
    if df.empty:
        return {}
    # Use first non-NA row as base; work per series then average
    kpis = {}
    years = list(df.index)
    # compute YoY for each series
    yoy = df.pct_change() * 100.0
    # choose a representative (first column) for KPI headline
    rep = df.columns[0]
    start_val = df[rep].dropna().iloc[0]
    end_val = df[rep].dropna().iloc[-1]
    n_years = max(1, len(df.dropna().index) - 1)
    total_return = ((end_val / start_val) - 1.0) * 100.0 if start_val and end_val else np.nan
    cagr = ((end_val / start_val) ** (1.0 / n_years) - 1.0) * 100.0 if start_val and end_val else np.nan
    # best/worst year based on rep series YoY
    yoy_rep = yoy[rep].dropna()
    best_year = yoy_rep.idxmax() if not yoy_rep.empty else None
    worst_year = yoy_rep.idxmin() if not yoy_rep.empty else None
    return {
        "rep_series": rep,
        "total_return_pct": None if pd.isna(total_return) else round(float(total_return), 2),
        "cagr_pct": None if pd.isna(cagr) else round(float(cagr), 2),
        "best_year": best_year,
        "best_year_yoy_pct": None if yoy_rep.empty else round(float(yoy_rep.max()), 2),
        "worst_year": worst_year,
        "worst_year_yoy_pct": None if yoy_rep.empty else round(float(yoy_rep.min()), 2),
    }

# User query
query = st.text_input("Enter your market query:", "Global Smartphone market")

if st.button("Run(Agents)"):

    st.header("🧠 Trend Charts — Agent Outputs")

    # Competitor Comparison (structured list) + Competitor Trend timeseries
    with st.expander("🏁 Trend of Major Market Players", expanded=True):
       
        # Competitor trend (timeseries JSON comes as a text blob from the agent)
        with st.spinner("Competitor Trend Analyzer Agent..."):
            comp_trend_text = CompetitorTrend_agent(query)
        comp_trend = _salvage_json_text(comp_trend_text)
        ts_ct = comp_trend.get("timeseries") if isinstance(comp_trend, dict) else {}

        # Show resolved tickers if present
        rt = comp_trend.get("resolved_tickers") if isinstance(comp_trend, dict) else None
        if isinstance(rt, list) and rt:
            try:
                st.write("**Major Market PLayer Tickers**")
                df_rt = pd.DataFrame(rt)
                if "confidence" in df_rt.columns:
                    df_rt = df_rt.drop(columns=["confidence"])
                st.dataframe(df_rt, use_container_width=True, hide_index=True)
            except Exception:
                pass

        if isinstance(ts_ct, dict) and (ts_ct.get("x") or ts_ct.get("series")):
            chart = _altair_timeseries_chart(ts_ct, title=ts_ct.get("title","Competitor price movement (rebased)"))
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
                st.caption("Competitor price movement")
            else:
                st.info("Competitor trend: no series.")
        else:
            st.info("Competitor trend: no data.")

    # Market Trend Analyzer (product vs sector + adoption)
    with st.expander("📈 Sector Trends & Movements", expanded=True):
        with st.spinner("Running Market Trend Analyzer Agent..."):
            market_trend_text = MarketTrendAnalyzer_agent(query)
            adoption = None
            try:
                mt_parsed = _salvage_json_text(market_trend_text)
                adoption = mt_parsed.get("adoption")
            except Exception:
                adoption = None        
        mt_text = market_trend_text
        mt = _salvage_json_text(mt_text)
        sp = mt.get("sector_performance", {}) if isinstance(mt, dict) else {}
        if sp and isinstance(sp, dict) and (sp.get("x") or sp.get("series")):
            chart = _altair_timeseries_chart(sp, title=sp.get("title","Sector / product price index (rebased)"))
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
                # KPIs
                k = _calc_kpis(sp) or {}
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Return (rep series)", f"{k.get('total_return_pct','–')}%")
                c2.metric("CAGR (rep series)", f"{k.get('cagr_pct','–')}%")
                c3.metric("Best Year", f"{k.get('best_year','–')}", f"{k.get('best_year_yoy_pct','–')}%")
                c4.metric("Worst Year", f"{k.get('worst_year','–')}", f"{k.get('worst_year_yoy_pct','–')}%")
                # Proxies
                proxies = sp.get("proxies_used", {})
                chips = []
                for kx, vx in (proxies or {}).items():
                    if not vx:
                        continue
                    chips.append(f"<span class='chip'><b>{kx.capitalize()}</b>: {vx}</span>")
                if chips:
                    st.markdown(" ".join(chips), unsafe_allow_html=True)
            else:
                st.info("Market Trend: no series.")
        else:
            st.info("Market Trend: no data.")

        # Adoption podiums from MarketTrendAnalyzer agent output
        ad = mt.get("adoption", {}) if isinstance(mt, dict) else {}
        ea = ad.get("early_adopters_top3") or []
        cu = ad.get("current_adopters_top3") or ad.get("current_adopters_top5") or []

        def _name_list_agent(items):
            names = []
            for it in items:
                if isinstance(it, dict):
                    n = it.get("company") or it.get("region") or it.get("name")
                    if n:
                        names.append(str(n))
            return names[:3]

        early_names = _name_list_agent(ea)
        current_names = _name_list_agent(cu)

        def _podium_html(title: str, names: list[str]) -> str:
            ranks = ["gold","silver","bronze"]
            medals = ["🥇","🥈","🥉"]
            rows = []
            for i, n in enumerate(names[:3]):
                cls = ranks[i] if i < 3 else ""
                badge = f"{medals[i]} {i+1}"
                rows.append(f"<div class='rank-item {cls}'><span class='rank-badge'>{badge}</span><span class='rank-name'>{n}</span></div>")
            if not rows:
                return "<div class='muted'>No data.</div>"
            return f"""\n<div class='card'>\n  <h4>{title}<span class='sub'>ranked</span></h4>\n  {''.join(rows)}\n</div>\n"""  # noqa: E501

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(_podium_html("Top 3 Early Customer Base Builders", early_names), unsafe_allow_html=True)
        with c2:
            st.markdown(_podium_html("Top 3 Current Customer Base Dominators", current_names), unsafe_allow_html=True)

        # Reasons list (compact)
        def _reasons(items):
            out = []
            for it in items[:3]:
                if isinstance(it, dict):
                    name = it.get("company") or it.get("name")
                    why = it.get("why")
                    if name and why:
                        out.append(f"- **{name}** — {why}")
            return "\n".join(out) if out else "–"
        st.markdown("<div class='muted'>Early adopters — reasons:</div>", unsafe_allow_html=True)
        st.markdown(_reasons(ea))
        st.markdown("<div class='muted'>Current dominators — reasons:</div>", unsafe_allow_html=True)
        st.markdown(_reasons(cu))

    # Event-driven price spikes (Agent)
    with st.expander("⚡ Event-driven Price Spikes", expanded=True):
        with st.spinner("Agent finding out sginifcant event-driven price spikes..."):
            ps_text = EventPriceSpike_agent(query, adoption=adoption)
        ps = _salvage_json_text(ps_text)
        ev = ps.get("events_detected", []) if isinstance(ps, dict) else []
        if ev:
            rows = []
            for e in ev:
                try:
                    rows.append({
                        "Date": e.get("date"),
                        "Ticker/Company": e.get("entity_or_topic"),
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
                st.caption("Magnitude: low ≥0–5%, medium ≥5–10%, high ≥10% 1‑day moves. Confidence is a heuristic from the agent.")
            else:
                st.info("No spike rows to display.")
        else:
            st.info("No events detected by agent.")