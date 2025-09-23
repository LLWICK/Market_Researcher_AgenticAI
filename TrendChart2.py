from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
import json
import time
from utills.scope_utils import _cap5, _salvage_json, _fallback_extract
from utills.ta_helpers import _agent_text,_cap5_any,_extract_company_names_from_trend,_infer_period_from_trend, _slug_name, _default_event_period, build_top5_snapshot,_ensure_month_format
from utills.ticker_cache import get_cached, put_cached


load_dotenv()

protocol = AgentProtocol()

# Data Flow)
# 	•	QueryScopeAgent → publishes scope.
# 	•	MarketDataAgent → publishes resolved_tickers (for EventSpikeAgent) and performance (for Sector performance).
# 	•	AdoptionAgent / EventSpikeAgent / SectorPerfLLMAgent → read the published scope and (when needed) the published tickers/performance to produce their sections.
# ---------------------------
# Agents
# ---------------------------
# QueryScopeAgent
# 	•	Goal: Turn a messy user query into a clean, machine-usable scope.
query_scope_agent = Agent(
    name="QueryScopeAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
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

# MarketDataAgent
	# •	Goal: Convert scope → tradable tickers and price-index timeseries.

market_data_agent = Agent(
    name="MarketDataAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools()],
    instructions="""
Emit JSON ONLY.

INPUT:
{
  "scope": {...},                    // from QueryScopeAgent
  "company_names": ["...", "..."],   // ≤5; may be empty
  "period": {"from":"YYYY-MM","to":"YYYY-MM"},
  "pref_currency": "USD",
  "discovery": true|false            // if true, first identify top public companies in sector/geo
}

TASKS:
1) If company_names is empty or discovery=true:
   - Identify up to 5 **publicly listed** companies most relevant to scope.sectors[0] & geo (countries/regions).
   - Use tools where possible; prefer well-known leaders with clear tickers.
2) Resolve a primary exchange-listed ticker per company (leave "" ONLY if truly not listed).
3) For non-empty tickers, fetch YEARLY Adjusted Close over [from, to] (inclusive window).
4) For each ticker's YEARLY series, rebase to 100 at the first available point.
5) Return both the resolved tickers and the chart-ready timeseries.

RULES:
- Keep order of input company_names when provided; append any discovered names after to make ≤5 total.
- Avoid private/subsidiary-only names without a parent ticker; if a brand is a division, return the parent ticker.
- Do NOT output prose outside the JSON.

OUTPUT:
{
  "resolved_tickers": [
    {"name":"...", "ticker":"", "exchange":"", "confidence": 0.0}
  ],
  "timeseries": {
    "title": "Market performance (price-index)",
    "unit": "index",
    "frequency": "yearly",
    "x": ["YYYY", ...],
    "series": [
      {"name":"<Company>", "ticker":"<TICKER>", "data":[100, ...]}
    ]
  },
  "notes": [
    "Adj Close rebased to 100 at first available year"
  ],
  "data_gaps": []
}
"""
)

# SectorPerfLLMAgent
# 	•	Goal: Produce a sector-level index when needed.
sector_perf_llm_agent = Agent(
    name="SectorPerfLLMAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions="""
Emit JSON ONLY. Read the processed `scope` to identify the primary sector (scope.sectors[0]) and geography (use scope.countries if present, otherwise scope.regions, else "Global"). Use these to produce a sector-level market index movement.

Behavior:
- If company performance series are provided, compute a sector index by averaging them, then aggregate to YEARLY values.
- If no company series or tickers are provided, infer a reasonable sector proxy (e.g., sector ETF, commodity benchmark, or industry index) using available tools, prioritizing the specified geography; if none, use a global proxy. Then aggregate to YEARLY values.
- Period selection:
  • If scope.time_horizon specifies a period with explicit years, respect it.
  • Otherwise, return the current year and 5 full years back (total 6 years).
- Rebase the index to 100 at the first year in the period (i.e., first value = 100). Subsequent values reflect % movement vs. the base.
- Include one concise line explaining what proxy/index was used (if any).

Schema:
{
  "sector_performance": {
    "title": "«{Sector}» sector index — «{Geo}»",
    "unit": "index (rebased=100)",
    "frequency": "yearly",
    "x": ["YYYY", "YYYY", "..."],
    "series": [
      {"name": "sector_index", "data": [0.0]}
    ],
    "proxy_used": "e.g., XLE (US Energy Select Sector), global PC & laptop shipments index, Brent crude, etc."
  },
  "period": {"from": "YYYY", "to": "YYYY"},
  "notes": [],
  "data_gaps": []
}
Output only the JSON object above. If assumptions are made (e.g., proxy selection or ambiguous sector), briefly note them in `notes`.
  """
)

# AdoptionAgent - CUSTOMER BASE PATTERNS
# 	•	Goal: Identify who adopted early vs who dominates the customer base now in the scoped market.
adoption_agent = Agent(
    name="AdoptionAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions="""
Emit JSON ONLY. Input: processed scope JSON (received via AgentProtocol from QueryScopeAgent→TrendChartAgent). Goal: identify (a) the earliest notable commercial adopters in the query’s sector and geography; and (b) the dominant current players.

Definitions:
- "early_adopter": among the first movers to ship products, achieve commercial deployments, or secure meaningful market presence in the specified sector/region.
- "current_dominator": companies that currently lead by market share, revenue, active deployments, user base, or mindshare in the specified sector/region.

Scoring:
- Provide a 0–100 score for each company.
- For early_adopter score: weight (historical firsts, product launch year vs peers, early deployments, seminal partnerships).
- For current_dominator score: weight (recent revenue/share, deployments/users, growth trajectory, breadth of offerings).
- Scores are relative within the returned set.

Schema:
{
  "adoption": {
    "early_adopters_top3": [
      {"company":"...", "score":0, "why":"short rationale"}
    ],
    "current_adopters_top3": [
      {"company":"...", "score":0, "why":"short rationale"}
    ]
  },
  "score_meaning": "0–100 relative scale where ~100 = strongest within this set",
  "method": ["heuristics based on sector/geo in scope; label assumptions where uncertain"],
  "assumptions": [],
  "data_gaps": []
}
ONLY output the JSON object above. If scope is ambiguous, state assumptions and keep lists shorter.
Do NOT call any tools or functions. Never emit <function=...> blocks. Output JSON only.
  """
)

# EventSpikeAgent
# 	•	Goal: Surface the latest (≤5) notable events tied to the scoped tickers (earnings, product, M&A, etc.) with price context.
event_spike_agent = Agent(
    name="EventSpikeAgent",
    model= Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools()],
    instructions="""
Emit JSON ONLY. Input: processed `scope` JSON plus any `resolved_tickers` provided via AgentProtocol. Goal: detect the **latest** notable news/events for the specified sector/geo **for the given tickers**, and summarize associated price movements.
  
Company universe:
- **Prefer** the already-resolved tickers received via protocol (≤5). Do not search for more unless none are provided.
- Use YFinance tools **only** for symbols provided in 'resolved_tickers'.
- If 'resolved_tickers' is empty, do not call tools; you may still summarize recent events, leaving price_move_1d_pct as null.

Period & count:
- Use **current-year-to-date** (from Jan 1 of the current year up to today).
- Return **at most 5 events total**, **sorted newest → oldest**. If more exist, keep only the 5 most recent.

For each event, compute/estimate:
- 1-day price move (%) close→close around event date.
- Cumulative price move (%) from period start to the event date.
- Direction: "+" or "-". Magnitude: low | medium | high. Confidence: 0–1.

Schema:
{
  "companies": [ {"company":"...","ticker":"..."} ],
  "events_detected": [
    {
      "date":"YYYY-MM-DD",
      "type":"earnings|guidance|product|partnership|M&A|regulatory|macro|litigation|outage|leadership|other",
      "entity_or_topic":"COMPANY or TICKER",
      "direction":"+|-",
      "price_move_1d_pct": 0.0,
      "price_move_period_pct": 0.0,
      "magnitude":"low|medium|high",
      "confidence":0.0,
      "headline":"short headline",
      "blurb":"1–2 sentence reason/impact"
    }
  ],
  "period":{"from":"YYYY-MM-DD","to":"YYYY-MM-DD"},
  "method": ["resolved tickers via protocol", "YFinance tools for price context"],
  "assumptions": [],
  "notes": [],
  "data_gaps": []
}
Rules:
- **ONLY** output the JSON object above.
- Ensure `events_detected` is **sorted by date descending** and length ≤5.
"""
)


# ---------------------------
# Agent Functions
# ---------------------------

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

def MarketData_agent(scope: dict, trend_like: dict | None = None) -> dict:
    """
    One-hop data: resolve tickers (cache-first) + fetch yearly Adj Close via YFinanceTools + rebase.
    trend_like is optional; we only need company names & a period.
    """
    # 1) Decide companies (cap to 5 early)
    if trend_like:
        names = _extract_company_names_from_trend(trend_like)
    else:
        # fallback: use scope.companies if present (strings or dicts)
        raw = scope.get("companies", [])
        names = []
        for c in raw:
            if isinstance(c, str): names.append(c)
            elif isinstance(c, dict) and c.get("name"): names.append(c["name"])
        names = names[:5]

    if not names:
        print("[MarketData_agent] No company names provided by scope/trend; relying on discovery mode.")

    # 2) Period (prefer scope/trend helper)
    period = _infer_period_from_trend(scope, trend_like or {})
    if not period or not period.get("from") or not period.get("to"):
        # default last 5 full years ending this year
        from datetime import date
        today = date.today()
        period = {"from": f"{today.year-5}-01", "to": f"{today.year}-12"}

    # Normalize period to YYYY-MM bounds for the agent/tools
    period = _ensure_month_format(period)

    # 3) Apply cache before calling the agent
    pre_resolved = []
    unresolved = []
    for n in names:
        hit = get_cached(n)
        if hit:
            pre_resolved.append({"name": n, "ticker": hit["ticker"], "exchange": hit["exchange"], "confidence": 0.95})
        else:
            unresolved.append(n)

    # 4) Ask the single agent for everything (it will also fill time series)
    payload = {
        "scope": scope,
        "company_names": names,     # keep original order
        "period": period,
        "pref_currency": "USD",
        "discovery": False if names else True
    }
    try:
        raw = _agent_text(market_data_agent.run(json.dumps(payload)))
        out = _salvage_json(raw) or {}
    except Exception as e:
        out = {}

    # Retry once in discovery mode if nothing resolved
    if (not out.get("resolved_tickers")) and (scope.get("sectors") or scope.get("regions") or scope.get("countries")):
        try:
            print("[MarketData_agent] First pass returned no tickers; retrying with discovery=True…")
            payload_retry = dict(payload); payload_retry["discovery"] = True
            raw2 = _agent_text(market_data_agent.run(json.dumps(payload_retry)))
            out2 = _salvage_json(raw2) or {}
            # prefer second output if it resolved tickers
            if out2.get("resolved_tickers"):
                out = out2
        except Exception as _e:
            print(f"[MarketData_agent] Discovery retry failed: {_e}")

    # 5) Merge cache hits into resolved list (prefer agent’s values when present)
    resolved = out.get("resolved_tickers", []) if isinstance(out, dict) else []
    # backfill cached ones if agent left blanks
    if names and resolved:
        # build quick map
        by_name = { _slug_name(r.get("name","")): r for r in resolved }
        for item in pre_resolved:
            key = _slug_name(item["name"])
            r = by_name.get(key)
            if not r:
                resolved.append(item)
            elif not r.get("ticker"):
                r.update(item)

    # 6) Persist new resolutions to cache
    for r in (resolved or []):
        if r.get("name") and r.get("ticker"):
            put_cached(r["name"], r["ticker"], r.get("exchange",""))

    # 6.5) Share resolved tickers on the protocol for EventSpikeAgent (and others)
    try:
        protocol.send("MarketPerformanceAgent.tickers", "EventSpikeAgent", {"resolved_tickers": resolved or []})
        print("[MarketData_agent] Sent resolved tickers to EventSpikeAgent via protocol channel 'MarketPerformanceAgent.tickers'")
    except Exception as _e:
        print(f"[MarketData_agent] Protocol send (tickers) failed: {_e}")

    # 7) Final structure (timeseries comes from agent)
    result = {
        "resolved_tickers": resolved or [],
        "timeseries": (out.get("timeseries") if isinstance(out, dict) else {"x": [], "series": []}),
        "period": period,
        "notes": (out.get("notes") if isinstance(out, dict) else ["LLM fallback / empty"]),
        "data_gaps": out.get("data_gaps", [])
    }
    # quick one-line summary for logs
    try:
        tick_list = [r.get("ticker","") for r in (resolved or []) if r.get("ticker")]
        print(f"[MarketData_agent] Period {period['from']}→{period['to']} | Resolved {len(tick_list)}/{len(names)} tickers: {', '.join(tick_list) if tick_list else '(none)'}")
        ts_x = (result.get("timeseries") or {}).get("x") or []
        print(f"[MarketData_agent] Timeseries points: {len(ts_x)}")
    except Exception as _e:
        print(f"[MarketData_agent] Summary print failed: {_e}")
    # Optional: send to protocol for SectorPerformance use
    protocol.send("MarketPerformanceAgent.performance", "SectorPerformanceAgent", result)
    print("\n=== [MarketData_agent] Output ===")
    print(json.dumps(result, indent=2))
    print("\n=== [MarketData_agent] Output (Printed Block End) ===\n")
    return result

def Adoption_agent(scope: dict | None = None) -> dict:
    """
    Determine early adopters vs. current dominators for the sector/geo in the processed scope.
    - If `scope` is None, attempt to receive it from the AgentProtocol channel where QueryScopeAgent sent it to TrendChartAgent.
    - Returns a structured JSON dict per the AdoptionAgent schema.
    """
    # Get scope from protocol if not passed in
    if scope is None or not isinstance(scope, dict) or not scope:
        received = protocol.receive("TrendChartAgent") or protocol.receive("QueryScopeAgent") or {}
        if isinstance(received, dict) and received:
            scope = received
        else:
            scope = {}

    payload = {"scope": scope}

    try:
        raw = _agent_text(adoption_agent.run(json.dumps(payload)))
        out = _salvage_json(raw) or {
            "adoption": {"early_adopters_top3": [], "current_adopters_top3": []},
            "score_meaning": "0–100 relative scale",
            "method": ["LLM fallback"],
            "assumptions": [],
            "data_gaps": ["No structured output from LLM"]
        }
    except Exception as e:
        out = {
            "adoption": {"early_adopters_top3": [], "current_adopters_top3": []},
            "score_meaning": "0–100 relative scale",
            "method": ["error"],
            "assumptions": [],
            "data_gaps": [str(e)]
        }

    print("\n=== [Adoption_agent] Output ===")
    try:
        print(json.dumps(out, indent=2))
    except Exception:
        print(str(out))
    print("\n=== [Adoption_agent] Output (Printed Block End) ===\n")
    return out

def EventSpike_agent(scope: dict | None = None) -> dict:
    """Identify major news in top sector companies per scope and summarize price movements."""
    # Try to get scope from protocol if not given
    if scope is None or not isinstance(scope, dict) or not scope:
        received = protocol.receive("TrendChartAgent") or protocol.receive("QueryScopeAgent") or {}
        if isinstance(received, dict) and received:
            scope = received
        else:
            scope = {}

    # Try to get resolved tickers mapping (optional)
    mapping = protocol.receive("MarketPerformanceAgent.tickers") or {}
    if not isinstance(mapping, dict):
        mapping = {}
    import re
    resolved_list = mapping.get("resolved_tickers", []) if isinstance(mapping, dict) else []
    valid_resolved = []
    for r in (resolved_list or []):
        t = (r.get("ticker") or "").upper().strip()
        # allow common patterns like AAPL, GOOGL, BRK.B; reject 1-char or OTC weirds when tool fails
        if re.match(r"^[A-Z]{2,5}(\.[A-Z]{1,3})?$", t):
            rr = dict(r); rr["ticker"] = t
            valid_resolved.append(rr)
    if resolved_list and not valid_resolved:
        print("[EventSpike_agent] Resolved tickers present but none passed validation; skipping tool calls.")
    if mapping:
        try:
            r = mapping.get("resolved_tickers", [])
            print(f"[EventSpike_agent] Received {len(r)} resolved tickers via protocol; using {len(valid_resolved)} after validation.")
        except Exception:
            print("[EventSpike_agent] Mapping received but malformed; proceeding without detailed count.")
    else:
        print("[EventSpike_agent] No resolved tickers received via protocol; will infer leaders if needed.")
    if resolved_list and (len(valid_resolved) < len(resolved_list)):
        bad = [ (r.get("ticker") or "") for r in resolved_list if r not in valid_resolved ]
        print(f"[EventSpike_agent] Filtered out potentially invalid symbols for tools: {', '.join([b for b in bad if b])}")

    # Default event period (YTD)
    default_ep = _default_event_period()

    # If no valid tickers, try to discover up to 5
    if not valid_resolved:
        try:
            print("[EventSpike_agent] No valid resolved tickers; attempting discovery via MarketData_agent…")
            discovered = MarketData_agent(scope, trend_like=None) or {}
            cand = discovered.get("resolved_tickers") or []
            valid_resolved = [
                {"name": c.get("name"), "ticker": (c.get("ticker") or "").upper(), "exchange": c.get("exchange", ""), "confidence": c.get("confidence", 0.0)}
                for c in cand if c.get("ticker")
            ][:5]
            if valid_resolved:
                print(f"[EventSpike_agent] Discovery provided {len(valid_resolved)} tickers for spikes analysis.")
        except Exception as _e:
            print(f"[EventSpike_agent] Discovery path failed: {_e}")

    payload = {
        "scope": scope,
        "resolved_tickers": valid_resolved,
        "period": default_ep
    }

    try:
        raw = _agent_text(event_spike_agent.run(json.dumps(payload)))
        out = _salvage_json(raw) or {
            "companies": [],
            "events_detected": [],
            "period": {"from": "", "to": ""},
            "method": ["LLM fallback"],
            "assumptions": [],
            "notes": [],
            "data_gaps": ["No structured output"]
        }
        # Post-process: keep only the latest 5 events, sort by date desc
        try:
            ev = out.get("events_detected") or []
            def _key(e):
                d = str(e.get("date") or "")
                try:
                    y = int(d[:4]); m = int(d[5:7]) if len(d) >= 7 and d[4] == '-' else 1; dn = int(d[8:10]) if len(d) >= 10 and d[7] == '-' else 1
                    return (y, m, dn)
                except Exception:
                    return (-1, -1, -1)
            ev = [e for e in ev if e.get("date") and e.get("headline")]
            ev.sort(key=_key, reverse=True)
            out["events_detected"] = ev[:5]
        except Exception:
            pass
        # Ensure period present and correctly ordered
        per = out.get("period") or {}
        if not per.get("from") or not per.get("to"):
            per = default_ep
        f, t = str(per.get("from")), str(per.get("to"))
        if f and t and f > t:
            f, t = t, f
        out["period"] = {"from": f, "to": t}
    except Exception as e:
        out = {
            "companies": [],
            "events_detected": [],
            "period": {"from": "", "to": ""},
            "method": ["error"],
            "assumptions": [],
            "notes": [],
            "data_gaps": [str(e)]
        }

    print("\n=== [EventSpike_agent] Output ===")
    try:
        print(json.dumps(out, indent=2))
    except Exception:
        print(str(out))
    print("\n=== [EventSpike_agent] Output (Printed Block End) ===\n")
    return out

def SectorPerformance_agent(scope: dict, perf: dict) -> dict:
    """Compute sector-level YEARLY index from company series if possible; else ask LLM to synthesize/proxy."""
    from datetime import datetime
    import re
    # Helpers
    def _geo_title(sc: dict) -> str:
        geo = "Global"
        try:
            if (sc.get("countries") or []):
                geo = (sc["countries"][0] or "Global")
            elif (sc.get("regions") or []):
                geo = (sc["regions"][0] or "Global")
        except Exception:
            pass
        return geo
    def _sector_title(sc: dict) -> str:
        try:
            if (sc.get("sectors") or []):
                return sc["sectors"][0]
        except Exception:
            pass
        return "Market"

    # Attempt direct compute from provided series
    try:
        ts = (perf or {}).get("timeseries", {})
        x = ts.get("x") or []
        series = ts.get("series") or []
        # Derive requested period (years)
        th = (scope or {}).get("time_horizon") or {}
        # Force to 2021–2025 inclusive
        y_window = (2019, 2025)

        # Build per-year average across companies
        if x and series:
            # Map index of each point to its year
            years_map = []
            for xi in x:
                # Accept formats like 'YYYY-MM' or 'YYYY'
                try:
                    y = int(str(xi)[:4])
                except Exception:
                    y = None
                years_map.append(y)

            # Gather values per year per series
            per_year_vals = {}
            for si in series:
                data = si.get("data") or []
                for idx, val in enumerate(data):
                    y = years_map[idx] if idx < len(years_map) else None
                    if y is None:
                        continue
                    try:
                        fv = float(val)
                        if fv == fv:  # not NaN
                            per_year_vals.setdefault(y, []).append(fv)
                    except Exception:
                        continue

            # Average across companies for each year
            y_start, y_end = y_window
            years_out = [y for y in range(y_start, y_end + 1)]
            values = []
            for y in years_out:
                vals = per_year_vals.get(y, [])
                if vals:
                    values.append(sum(vals) / len(vals))
                else:
                    values.append(None)

            # Remove leading/trailing Nones
            # (but keep alignment to requested window; we will rebase on first non-None)
            # Rebase first non-None to 100
            base = None
            for v in values:
                if v is not None:
                    base = v
                    break
            rebased = []
            if base is not None and base != 0:
                for v in values:
                    if v is None:
                        rebased.append(None)
                    else:
                        rebased.append(round((v / base) * 100.0, 2))
            else:
                rebased = [None for _ in values]

            # Build output
            years_str = [str(y) for y in years_out]
            try:
                print(f"[SectorPerformance_agent] Computed yearly sector index from company series: years={y_window[0]}–{y_window[1]}")
            except Exception:
                pass
            out = {
                "sector_performance": {
                    "title": f"{_sector_title(scope)} sector index — {_geo_title(scope)}",
                    "unit": "index (rebased=100)",
                    "frequency": "yearly",
                    "x": years_str,
                    "series": [{"name": "sector_index", "data": rebased}],
                    "proxy_used": ""
                },
                "period": {"from": years_str[0], "to": years_str[-1]},
                "notes": ["Computed as yearly average of company indices, rebased to first year."],
                "data_gaps": []
            }
            print("\n=== [SectorPerformance_agent] Output ===")
            print(json.dumps(out, indent=2))
            print("\n=== [SectorPerformance_agent] Output (Printed Block End) ===\n")
            return out
    except Exception:
        pass

    # LLM synthesize/proxy fallback
    payload = {"scope": scope, "performance": perf}
    try:
        raw = _agent_text(sector_perf_llm_agent.run(json.dumps(payload)))
        out = _salvage_json(raw) or {
            "sector_performance": {
                "title": f"{_sector_title(scope)} sector index — {_geo_title(scope)}",
                "unit": "index (rebased=100)",
                "frequency": "yearly",
                "x": [],
                "series": [{"name": "sector_index", "data": []}],
                "proxy_used": ""
            },
            "period": {"from": "", "to": ""},
            "notes": ["LLM fallback"],
            "data_gaps": ["No structured output"]
        }
    except Exception as e:
        out = {
            "sector_performance": {
                "title": f"{_sector_title(scope)} sector index — {_geo_title(scope)}",
                "unit": "index (rebased=100)",
                "frequency": "yearly",
                "x": [],
                "series": [{"name": "sector_index", "data": []}],
                "proxy_used": ""
            },
            "period": {"from": "", "to": ""},
            "notes": ["error"],
            "data_gaps": [str(e)]
        }
    print("\n=== [SectorPerformance_agent] Output ===")
    try:
        print(json.dumps(out, indent=2))
    except Exception:
        print(str(out))
    print("\n=== [SectorPerformance_agent] Output (Printed Block End) ===\n")
    return out



# ---------------------------
# Pipeline Orchestrator
# ---------------------------
def run_pipeline_b(query: str):
    t0 = time.perf_counter()
    scope = analyze_query_scope(query)                 # 1 hop
    t1 = time.perf_counter()
    try:
        print(f"[Pipeline] Scope → scale={scope.get('scale')} | sectors={scope.get('sectors')} | geo={(scope.get('countries') or scope.get('regions') or ['Global'])[0] if isinstance(scope, dict) else 'Global'}")
    except Exception:
        print("[Pipeline] Scope summary print failed")
    print(f"[Timer] QueryScopeAgent took {(t1 - t0):.2f}s")

    market = MarketData_agent(scope, trend_like=None)  # 1 hop (tickers + timeseries)
    t2 = time.perf_counter()
    try:
        resolved = market.get("resolved_tickers", [])
        tickers = [r.get("ticker","") for r in resolved if r.get("ticker")]
        print(f"[Pipeline] MarketDataAgent → resolved {len(tickers)} tickers: {', '.join(tickers) if tickers else '(none)'}")
        tsx = (market.get("timeseries") or {}).get("x") or []
        print(f"[Pipeline] MarketDataAgent → timeseries length: {len(tsx)}")
    except Exception:
        print("[Pipeline] MarketDataAgent summary print failed")
    print(f"[Timer] MarketDataAgent took {(t2 - t1):.2f}s")

    # build a simple top-5 snapshot in Python (optional)
    trend = build_top5_snapshot(scope, market["resolved_tickers"])
    try:
        print(f"[Pipeline] Trend snapshot built with {len(market.get('resolved_tickers', []))} companies.")
    except Exception:
        pass

    # Adoption 
    ta = time.perf_counter()
    adoption = Adoption_agent(scope)
    tb = time.perf_counter()
    try:
        ea = (adoption.get("adoption") or {}).get("early_adopters_top3", [])
        ca = (adoption.get("adoption") or {}).get("current_adopters_top3", [])
        print(f"[Pipeline] Adoption (agent) → early={len(ea)} current={len(ca)}")
    except Exception:
        print("[Pipeline] Adoption summary print failed")
    print(f"[Timer] Adoption (agent) took {(tb - ta):.2f}s")

    # Event spikes (always on)
    te = time.perf_counter()
    price_spikes = EventSpike_agent(scope)
    tf = time.perf_counter()
    try:
        events = price_spikes.get("events_detected", [])
        print(f"[Pipeline] Events (agent) → events detected: {len(events)}")
    except Exception:
        print("[Pipeline] Events summary print failed")
    print(f"[Timer] Events (agent) took {(tf - te):.2f}s")

    # sector perf from timeseries (your existing Python logic, LLM only as fallback)
    sector_perf = SectorPerformance_agent(scope, market)
    t3 = time.perf_counter()
    try:
        sp = sector_perf.get("sector_performance", {})
        years = sp.get("x", [])
        print(f"[Pipeline] SectorPerformance → years={years[0]+'…'+years[-1] if years else '(none)'}")
    except Exception:
        print("[Pipeline] SectorPerformance summary print failed")
    print(f"[Timer] SectorPerformanceAgent + aggregation took {(t3 - tf):.2f}s")

    t_end = time.perf_counter()
    print(f"[Timer] Total pipeline time: {(t_end - t0):.2f}s")

    return {
        "scope": scope,
        "trend": trend,
        "performance": market,
        "adoption": adoption,
        "price_spikes": price_spikes,
        "sector_performance": sector_perf
    }


if __name__ == "__main__":
    test_queries = [
        #"Renewable energy storage market 2023",
        #"EV charging competitors in Asia",
        "Cloud security vendors in the US"
    ]
    for query in test_queries:
        print("\n" + "="*80)
        print(f"Running pipeline for query: {query}")
        results = run_pipeline_b(query)
        print(json.dumps(results, indent=2))