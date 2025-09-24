import json
import datetime
import re as _re
import altair as alt
import numpy as np
import json, re
import pandas as pd

from datetime import date

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

def _altair_timeseries_chart(timeseries: dict, title: str = ""):
    """Pretty Altair line chart with tooltips & series highlight."""
    df = _series_to_df(timeseries)
    if df.empty:
        return None
    long = df.reset_index().melt("index", var_name="Series", value_name="Value")
    long.rename(columns={"index": "Year"}, inplace=True)
    highlight = alt.selection_point(fields=["Series"], bind="legend")
    chart = (
        alt.Chart(long, title=title)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:N", title="Year"),
            y=alt.Y("Value:Q", title=timeseries.get("unit","index")),
            color=alt.Color("Series:N", legend=alt.Legend(title="Series")),
            opacity=alt.condition(highlight, alt.value(1), alt.value(0.25)),
            tooltip=[
                alt.Tooltip("Year:N"),
                alt.Tooltip("Series:N"),
                alt.Tooltip("Value:Q", format=".2f"),
            ],
        )
        .add_params(highlight)
        .properties(height=320)
        .interactive()
    )
    return chart


def _ensure_month_format(period: dict) -> dict:
    """Normalize {'from':'YYYY'|'YYYY-MM','to':'YYYY'|'YYYY-MM'} to 'YYYY-MM' bounds."""
    if not isinstance(period, dict):
        return {"from": "", "to": ""}
    p = dict(period)
    try:
        f = str(p.get("from", "")); t = str(p.get("to", ""))
        if len(f) == 4: p["from"] = f + "-01"
        if len(t) == 4: p["to"]   = t + "-12"
        # tolerate already-monthly strings
    except Exception:
        pass
    return p


def _default_event_period() -> dict:
    """Current-year-to-date window as {'from':'YYYY-01-01','to':'YYYY-MM-DD'} with from<=to."""
    today = date.today()
    return {"from": f"{today.year}-01-01", "to": today.strftime("%Y-%m-%d")}

def build_top5_snapshot(scope: dict, resolved: list[dict]) -> dict:
    sector = (scope.get("sectors") or ["Market"])[0]
    geo = (scope.get("countries") or scope.get("regions") or ["Global"])[0]
    title = f"Top 5 competitors in {geo} {sector}"
    names = [r["name"] for r in resolved][:5]
    # Market values (USD) can be added later if you decide to fetch caps via tools
    return {
        "charts": [{
            "id": "top5_competitors",
            "title": title,
            "type": "bar",
            "unit": "USD",
            "series": [{"name": "Market Value", "data": [[n, None] for n in names]}],
            "notes": "Values omitted (deployment constraint)"
        }],
        "period": {},
        "assumptions": [],
        "data_gaps": []
    }


# Robustly extract text from Agent.run(...) results across variants
def _agent_text(run_result) -> str:
    try:
        for attr in ("output_text", "content", "text"):
            v = getattr(run_result, attr, None)
            if isinstance(v, str) and v.strip():
                return v
        msgs = getattr(run_result, "messages", None)
        if msgs:
            try:
                last = msgs[-1]
                if isinstance(last, dict):
                    v = last.get("content", "")
                else:
                    v = getattr(last, "content", "")
                if isinstance(v, str) and v.strip():
                    return v
            except Exception:
                pass
        s = str(run_result)
        return s if isinstance(s, str) else ""
    except Exception:
        return ""

# Safe deduper/limiter that preserves dicts/lists
def _cap5_any(lst):
    out = []
    seen = set()
    for x in (lst or []):
        if not x:
            continue
        if isinstance(x, dict):
            key = x.get("name") or json.dumps(x, sort_keys=True)
        elif isinstance(x, (list, tuple)):
            key = json.dumps(x, sort_keys=True)
        else:
            key = str(x)
        if key in seen:
            continue
        seen.add(key)
        out.append(x)
        if len(out) >= 5:
            break
    return out

# Extract up to 5 company names from TrendChart output (handles multiple chart ids)
def _extract_company_names_from_trend(trend: dict) -> list:
    names = []
    seen = set()
    charts = (trend or {}).get("charts", [])
    for ch in charts:
        cid = ch.get("id", "")
        # From a Top-5 competitors bar: series[0].data is [["Company", value], ...]
        if cid == "top5_competitors":
            for row in (ch.get("series", [])[:1] or []):
                for pair in row.get("data", []) or []:
                    if isinstance(pair, (list, tuple)) and pair:
                        nm = str(pair[0]).strip()
                        if nm and nm not in seen:
                            seen.add(nm); names.append(nm)
        # From a market-share timeseries: series is [{name:.., data:[..]}, ...]
        if cid == "market_share_timeseries":
            for s in ch.get("series", []) or []:
                nm = str(s.get("name", "")).strip()
                if nm and nm not in seen:
                    seen.add(nm); names.append(nm)
        if len(names) >= 5:
            break
    return names[:5]

# Infer a period (from, to) from TrendChart output or scope
def _infer_period_from_trend(scope: dict, trend: dict) -> dict:
    # Prefer explicit trend.period
    per = (trend or {}).get("period") or {}
    frm, to = per.get("from", ""), per.get("to", "")
    if frm and to:
        return {"from": str(frm), "to": str(to)}
    # Otherwise try x-axis of first chart with an array of years
    charts = (trend or {}).get("charts", [])
    for ch in charts:
        x = ch.get("x")
        if isinstance(x, list) and x:
            return {"from": str(x[0]), "to": str(x[-1])}
    # Otherwise try scope.time_horizon.detail to pick a range of years like "2020–2024"
    detail = str((scope or {}).get("time_horizon", {}).get("detail", ""))
    years = _re.findall(r"20\\d{2}", detail)
    if len(years) >= 2:
        return {"from": years[0], "to": years[1]}
    # Fallback: last 5 calendar years ending this year
    y = datetime.date.today().year
    return {"from": str(y-5), "to": str(y)}

# Normalize company names for matching (lowercase, strip punctuation/paren suffixes/common suffixes)
def _slug_name(name: str) -> str:
    s = (name or "").lower()
    # remove content in parentheses and brackets
    s = _re.sub(r"\\s*[\\(\\[].*?[\\)\\]]\\s*", " ", s)
    # drop common company suffixes
    s = _re.sub(r"\\b(incorporated|inc|corp|corporation|co|ltd|limited|plc|nv|sa|ag|llc|holdings|group)\\b\\.?", " ", s)
    # keep letters/numbers only
    s = _re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s

def _salvage_json_text(text: str) -> dict:
    """Extract first JSON-like object from an agent blob:
    - Valid JSON string
    - content='...JSON...' or content="...JSON..."
    - Python dict/list repr (single quotes) -> ast.literal_eval
    - Balanced braces fallback
    """
    import ast
    # Already dict
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return {}
    s = text.strip()
    # 1) Direct JSON
    try:
        return json.loads(s)
    except Exception:
        pass
    # 2) content='...'
    m = re.search(r"content=(['\"])(.*?)\\1", s, re.DOTALL)
    if m:
        inner = m.group(2).strip()
        # JSON try
        try:
            return json.loads(inner)
        except Exception:
            # Python literal try
            try:
                obj = ast.literal_eval(inner)
                if isinstance(obj, (dict, list)):
                    return obj
            except Exception:
                pass
    # 3) Python literal on whole string
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, (dict, list)):
            return obj
    except Exception:
        pass
    # 4) Balanced braces: extract {...} then JSON or literal
    start = s.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(s)):
            ch = s[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s[start:i+1]
                    # JSON try
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # Python literal try
                        try:
                            obj = ast.literal_eval(candidate)
                            if isinstance(obj, (dict, list)):
                                return obj
                        except Exception:
                            pass
                    break
    return {}
