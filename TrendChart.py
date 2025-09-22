from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
import json
from utills.scope_utils import _cap5, _salvage_json, _fallback_extract
from utills.ta_helpers import (
    _agent_text,
    _cap5_any,
    _extract_company_names_from_trend,
    _infer_period_from_trend,
    _slug_name,
)


load_dotenv()

protocol = AgentProtocol()


# ---------------------------
# Agents
# ---------------------------

# QueryScopeAgent
    # Goal: Parse a single natural-language market question into a normalized scope JSON:
    # 	•	scale: global / regional / country / company-specific / unknown
    # 	•	countries, regions, sectors, companies (with possible_tickers)
    # 	•	time_horizon (type + detail like “last 12 months”)
    # 	•	confidence, notes, ambiguities

    # Rules baked into its prompt:
    # Pick the scale deterministically; normalize names (“USA” → “United States”); keep lists ≤5.

query_scope_agent = Agent(
    name="QueryScopeAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions="""
Analyze ONE market query. Output ONLY JSON:

{
  "scale": "global"|"regional"|"country"|"company-specific"|"unknown",
  "countries": ["..."],   # ≤5
  "regions": ["..."],     # ≤5
  "sectors": ["..."],     # ≤5
  "companies": [          # ≤5
    {"name": "...", "possible_tickers": ["..."]}
  ],
  "time_horizon": {"type":"unspecified"|"past"|"current"|"future","detail":"..."},
  "confidence": 0.0,
  "notes": "",
  "ambiguities": []       # ≤5
}

Rules: "global" if no geo; region only→"regional"; any country→"country"; only companies→"company-specific". Normalize names ("USA"→"United States"). Keep lists ≤5.
"""
)
#-------------------
#Trend Anlyzer -> Maps top 5 comeptitors and market share -> bar chart
trend_chart_agent = Agent(
    name="TrendChartAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[YFinanceTools()],
    instructions="""
You receive a prior agent's SCOPE JSON via the protocol. Your job is to emit JSON ONLY for chart-ready data based on that scope.

INPUT (example):
{
  "scale": "global"|"regional"|"country"|"company-specific"|"unknown",
  "countries": ["..."],
  "regions": ["..."],
  "sectors": ["..."],
  "companies": [{"name":"...", "possible_tickers":["..."]}],
  "time_horizon": {"type":"past|current|future|unspecified","detail":"last 5 years|2019-2024|..."},
  "confidence": 0.0,
  "notes": "",
  "ambiguities": []
}

OUTPUT SCHEMA (emit JSON only; no prose):
{
  "charts": [
    {
      "id": "top5_competitors",
      "title": "Top 5 competitors in <scope>",
      "type": "bar",
      "unit": "USD",
      "series": [
        {"name": "Market Value", "data": [["Company A", 1234567890], ["Company B", 987654321], ...]}
      ],
      "notes": "Brief method/source notes"
    }
  ],
  "period": {"from":"<YYYY>", "to":"<YYYY>"},
  "assumptions": ["If tickers unknown, approximate via known parent tickers.", "If sector is unspecified, infer from query if possible."],
  "data_gaps": ["List missing items needing web research"]
}

RULES:
- DO NOT compute any market-share-over-time lines here. Only produce a snapshot Top-5 competitors bar chart.
- If scale is GLOBAL and a sector exists: output a Top-5 competitors bar chart (market value USD). Prefer public companies; otherwise include notable private firms without USD values (use null) and note the gap.
- If scale is REGIONAL/COUNTRY and a sector exists: output a Top-5 for that geography.
- Try to resolve tickers where possible to allow YFinanceTools to fetch market caps today (or as-of the end of the requested period). If a ticker is found, fill Market Value with current market cap (USD). If not, set null and add a gap note.
- NEVER output text outside the JSON object. Keep arrays ≤5 items. Use integers for USD values (round).
"""
)
#-------------------
# Ticker Resolver Agent (maps top 5 company names → listed tickers)
# ------------------
resolver_agent = Agent(
    name="TickerResolverAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[YFinanceTools()],
    instructions="""
You receive:
{
  "company_names": ["..."],
  "countries": ["..."],
  "regions": ["..."]
}
Resolve an exchange-listed ticker for each company name. Prefer the primary listing; if multiple share classes exist, choose the most liquid. If no credible match, return an empty ticker and add a data_gap.

OUTPUT JSON ONLY:
{
  "resolved_tickers": [
    {"name":"<Company>", "ticker":"<TICKER>", "exchange":"<EXCHANGE>", "confidence": 0.0}
  ],
  "data_gaps": ["<note>"]
}
Rules:
- Return at most 5 entries corresponding to the input names order.
- If a company is not publicly listed (or no ticker can be determined), include the name with "ticker":"" and a brief reason in data_gaps.
- No prose outside the single JSON object.
"""
)
#-------------------
# Market performance generator function (timeseries)
    # Goal: Produce a monthly price-index time series (Adj Close, rebased to 100) for up to 5 tickers, over an inferred period (scope/trend hint or default last 5 years).
    # Output JSON:
    #     {
    #         "timeseries": { title, unit:"index", frequency:"monthly", x:[YYYY-MM...],
    #                         series:[{name,ticker,data:[...]}] },
    #         "period": {from,to},
    #         "notes": [...],
    #         "data_gaps": [...]
    #     }
    # Rules: Use provided tickers exactly; skip missing months (don’t impute); ≤5 companies. If nothing resolvable, return empty series and list gaps.

market_performance_agent = Agent(
    name="MarketPerformanceAgent",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[YFinanceTools()],
    instructions="""
You receive the SCOPE JSON from QueryScopeAgent and the prior TrendChartAgent output via protocol. Produce JSON ONLY containing a multi-series time series of market PERFORMANCE (price-index), not market cap.

INPUT EXAMPLE:
{
  "scope": { ... },
  "trend": { ... },
  "company_names": ["...", "..."],
  "resolved_tickers": [{"name":"...","ticker":"...","exchange":"...","confidence":0.0}],
  "period": {"from":"YYYY","to":"YYYY"}
}

WHAT TO DO:
- Determine the working period: prefer the provided `period`; otherwise infer from trend or scope; if still unclear, default to last 5 calendar years ending today.
- Build the final list (≤5) of companies as objects {name, ticker}. Start from `company_names`; if `resolved_tickers` provides a ticker for a given name (case-insensitive, ignoring parentheses/suffixes), USE that ticker. If a name has no ticker, try to resolve; if still none, include the name with empty ticker and record a data_gap.
- Using YFinanceTools, fetch ADJUSTED CLOSE historical prices at monthly frequency across the chosen period for all entries with a non-empty ticker.
- Convert each price series to a performance index rebased to 100 at the first available point for that series. If a month has no data for a ticker, skip that point for that series (do not impute).

OUTPUT SCHEMA (JSON ONLY):
{
  "timeseries": {
    "title": "Market performance (price-index)",
    "unit": "index",
    "frequency": "monthly",
    "x": ["YYYY-MM", ...],
    "series": [
      {"name":"<Company>","ticker":"<TICKER>","data":[100, ...]}
    ]
  },
  "period": {"from":"YYYY-MM", "to":"YYYY-MM"},
  "notes": [
    "Adj Close rebased to 100 at period start",
    "Performance ≠ market cap; reflects stock return only"
  ],
  "data_gaps": ["Ticker not found for <Company>", "Insufficient history for <Ticker>"]
}

RULES:
- If `resolved_tickers` provides a ticker, you MUST use that ticker for the matching company name.
- NEVER output text outside the single JSON object.
- Keep at most 5 companies.
- If no companies are resolvable, output an empty series array and list data_gaps.
"""
)



# ---------------------------
# Agent Functions
# ---------------------------


#Goal: Turn the user’s free-text query into a clean, compact scope JSON (geo, sector, companies, time horizon).
def analyze_query_scope(query: str) -> dict:
    """Parse query → normalized scope (≤5 items per list) and send to TrendChartAgent."""
    try:
        raw = _agent_text(query_scope_agent.run(query.strip()))
    except Exception as e:
        print(f"[QueryScopeAgent] Model error: {e}")
        raw = ""

    data = _salvage_json(raw) or _fallback_extract(query)

    # Normalize + cap lists
    data.setdefault("countries", [])
    data.setdefault("regions", [])
    data.setdefault("sectors", [])
    data.setdefault("companies", [])
    data.setdefault("ambiguities", [])
    data.setdefault("time_horizon", {"type": "unspecified", "detail": ""})

    data["countries"]   = _cap5(data["countries"])
    data["regions"]     = _cap5(data["regions"])
    data["sectors"]     = _cap5(data["sectors"])
    data["companies"]   = _cap5_any(data["companies"])  # allow dicts or strings
    data["ambiguities"] = _cap5(data["ambiguities"])

    protocol.send("QueryScopeAgent", "TrendChartAgent", data)
    print("\n=== [QueryScopeAgent] Parsed Scope ===")
    print(json.dumps(data, indent=2))
    print("\n=== [QueryScopeAgent] Parsed Scope (Printed Block End) ===\n")
    return data

#Goal: Produce a Top-5 competitors snapshot (bar chart plan) from the scope.
def TrendChart_agent():
    """Scope → Top-5 competitors snapshot (bar). Forwards to MarketPerformanceAgent.trend."""
    scope = protocol.receive("TrendChartAgent") or {}
    if not scope:
        print("[TrendChartAgent] No scope received; did you call analyze_query_scope() first?")
        charts = {"charts": [], "period": {"from": "", "to": ""}, "assumptions": [], "data_gaps": ["No scope"]}
    else:
        try:
            raw = _agent_text(trend_chart_agent.run(json.dumps(scope)))
        except Exception as e:
            print(f"[TrendChartAgent] Model error: {e}")
            raw = ""
        charts = _salvage_json(raw)
        if not charts:
            # Minimal deterministic fallback
            title_scope = (scope.get("scale") or "unknown").upper()
            sector = (scope.get("sectors") or ["Sector"])[0]
            charts = {
                "charts": [{
                    "id": "top5_competitors",
                    "title": f"Top 5 competitors in {title_scope} {sector}",
                    "type": "bar",
                    "unit": "USD",
                    "series": [{"name": "Market Value", "data": []}],
                    "notes": "Placeholder"
                }],
                "period": {"from": "", "to": ""},
                "assumptions": ["Model fallback used"],
                "data_gaps": ["Need top-5 list and values"]
            }

    # Forward plan to performance chain
    protocol.send("TrendChartAgent", "MarketPerformanceAgent.trend", charts)
    print("\n=== [TrendChartAgent] Chart Plan ===")
    print(json.dumps(charts, indent=2))
    print("\n=== [TrendChartAgent] Chart Plan (Printed Block End) ===\n")
    return charts

#Goal: Map company names from the chart plan → exchange tickers (so performance can be fetched).
def TickerResolver_agent():
    """Resolve tickers for names in trend chart and forward to MarketPerformance."""
    scope = protocol.receive("TrendChartAgent") or {}
    trend = protocol.receive("MarketPerformanceAgent.trend") or {}
    names = _extract_company_names_from_trend(trend)

    if not names:
        payload = {"resolved_tickers": [], "data_gaps": ["No company names found in trend charts"]}
        protocol.send("TickerResolverAgent", "MarketPerformanceAgent.tickers", payload)
        print("\n=== [TickerResolverAgent] Resolved Tickers ===")
        print(json.dumps(payload, indent=2))
        print("\n=== [TickerResolverAgent] Resolved Tickers (Printed Block End) ===\n")
        return payload

    req = {"company_names": names, "countries": scope.get("countries", []), "regions": scope.get("regions", [])}
    try:
        raw = _agent_text(resolver_agent.run(json.dumps(req)))
    except Exception as e:
        print(f"[TickerResolverAgent] Model error: {e}")
        raw = ""

    mapping = _salvage_json(raw) or {"resolved_tickers": [], "data_gaps": ["Resolver returned no valid JSON"]}
    protocol.send("TickerResolverAgent", "MarketPerformanceAgent.tickers", mapping)
    print("\n=== [TickerResolverAgent] Resolved Tickers ===")
    print(json.dumps(mapping, indent=2))
    print("\n=== [TickerResolverAgent] Resolved Tickers (Printed Block End) ===\n")
    return mapping
#Goal: Build a monthly price-index timeseries (rebased to 100) for up to 5 tickers over the inferred period.
def MarketPerformance_agent():
    """Scope + Trend plan + Tickers → monthly price-index timeseries JSON."""
    scope = protocol.receive("TrendChartAgent") or {}
    trend = protocol.receive("MarketPerformanceAgent.trend") or {}
    ticks = protocol.receive("MarketPerformanceAgent.tickers") or {}
    resolved = ticks.get("resolved_tickers", []) if isinstance(ticks, dict) else []

    names = _extract_company_names_from_trend(trend)
    period = _infer_period_from_trend(scope, trend)
    rt_map = { _slug_name(x.get("name","")): x.get("ticker", "") for x in resolved }
    companies = [{"name": n, "ticker": rt_map.get(_slug_name(n), "")} for n in names]

    if not trend:
        print("[MarketPerformanceAgent] No TrendChart output; did you call TrendChart_agent() first?")
        result = {"timeseries": {"x": [], "series": []}, "period": {"from": "", "to": ""}, "notes": ["Missing trend plan"], "data_gaps": ["No trend plan"]}
        print("\n=== [MarketPerformanceAgent] Performance Plan ===")
        print(json.dumps(result, indent=2))
        print("\n=== [MarketPerformanceAgent] Performance Plan (Printed Block End) ===\n")
        return result

    payload = {
        "scope": scope,
        "trend": trend,
        "company_names": names,
        "resolved_tickers": resolved,
        "companies": companies,
        "period": period,
    }

    try:
        raw = _agent_text(market_performance_agent.run(json.dumps(payload)))
    except Exception as e:
        print(f"[MarketPerformanceAgent] Model error: {e}")
        raw = ""

    perf = _salvage_json(raw) or {
        "timeseries": {"title": "Market performance (price-index)", "unit": "index", "frequency": "monthly", "x": [], "series": [{"name": c["name"], "ticker": c["ticker"], "data": []} for c in companies]},
        "period": {"from": str(period.get("from", "")), "to": str(period.get("to", ""))},
        "notes": ["Fallback: empty series"],
        "data_gaps": ["No data from agent"]
    }

    print("\n=== [MarketPerformanceAgent] Performance Plan ===")
    print(json.dumps(perf, indent=2))
    print("\n=== [MarketPerformanceAgent] Performance Plan (Printed Block End) ===\n")
    return perf


# ---------------------------
# Pipeline Orchestrator
# ---------------------------
def run_pipeline(query: str, trend_out: str = "", perf_out: str = ""):
    """Linear pipeline: scope → trend_chart_agent → ticker_resolver → market_performance_agent."""
    scope = analyze_query_scope(query)
    print("\n=== Pipeline Step: Scope ===")
    print(json.dumps(scope, indent=2))
    print("\n=== End Pipeline Step: Scope ===\n")

    trend = TrendChart_agent()
    print("\n=== Pipeline Step: Trend Chart ===")
    print(json.dumps(trend, indent=2))
    print("\n=== End Pipeline Step: Trend Chart ===\n")

    tickers = TickerResolver_agent()
    print("\n=== Pipeline Step: Ticker Resolver ===")
    print(json.dumps(tickers, indent=2))
    print("\n=== End Pipeline Step: Ticker Resolver ===\n")

    perf = MarketPerformance_agent()
    print("\n=== Pipeline Step: Market Performance ===")
    print(json.dumps(perf, indent=2))
    print("\n=== End Pipeline Step: Market Performance ===\n")

    if trend_out:
        try:
            with open(trend_out, "w", encoding="utf-8") as f:
                json.dump(trend, f, indent=2)
        except Exception as e:
            print(f"[run_pipeline] Failed to write trend file: {e}")
    if perf_out:
        try:
            with open(perf_out, "w", encoding="utf-8") as f:
                json.dump(perf, f, indent=2)
        except Exception as e:
            print(f"[run_pipeline] Failed to write performance file: {e}")

    return {"scope": scope, "trend": trend, "tickers": tickers, "performance": perf}

if __name__ == "__main__":
    test_queries = [
        #"Renewable energy storage market 2023",
        #"EV charging competitors in Asia",
        "Cloud security vendors in the US"
    ]
    for query in test_queries:
        print("\n" + "="*80)
        print(f"Running pipeline for query: {query}")
        results = run_pipeline(query)
        print(json.dumps(results, indent=2))