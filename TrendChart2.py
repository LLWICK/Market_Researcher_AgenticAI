from agent_protocol import AgentProtocol
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
import json
from utills.scope_utils import _salvage_json
from utills.ta_helpers import _agent_text

load_dotenv()

protocol = AgentProtocol()

# ---------------------------
# Agents
# ---------------------------

# CompetitorTrendAgent — keep it simple: accept upstream payload and figure it out
competitor_trend_agent = Agent(
    name="CompetitorTrendAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools()],
    instructions="""
Emit JSON ONLY.

INPUT (one of):
{
  "competitors": ["Company A", "Company B", "..."],   // optional
  "period": {"from":"YYYY","to":"YYYY"},              // optional
  "region": "global|country|region name",             // optional (default global)
  "rebase": "none|per_series|joint"                   // optional (default none = raw levels)
}
OR
{
  "query": "plain English subject (sector/product/region)", // optional
  "period": {"from":"YYYY","to":"YYYY"},              // optional
  "region": "global|country|region name",             // optional (default global)
  "rebase": "none|per_series|joint"                   // optional (default none = raw levels)
}
You may receive BOTH; if so, prefer 'competitors' when non-empty, otherwise infer from 'query'.

SCOPE DETECTION:
- Parse the query or inputs for an explicit time period and/or geographic scope.
- If none is specified, use:
  • period = {"from":"2019","to":"2025"}   // default 5‑year outlook window (inclusive)
  • region = "global"
- Include the `region` text verbatim in `notes` if inferred.

TASK:
- If 'competitors' is provided and non-empty:
    • Resolve a primary exchange-listed ticker for each competitor (skip if none).
- Else if 'query' is provided:
    • Infer 3–5 publicly listed, representative competitors for the subject implied by the query (sector/product/geo) and resolve their tickers.
- Build a YEARLY Adjusted Close price series for each resolved ticker over the selected period.
- REBASE policy:
    • If rebase == "none" (default): return raw annual levels; set unit to "level".
    • If rebase == "per_series": rebase each series to 100 at its first available year; set unit to "index".
    • If rebase == "joint": rebase all series to 100 at the first common year; set unit to "index".
- Keep input order for provided competitors; cap total at 5.

OUTPUT:
{
  "resolved_tickers": [
    {"name":"...", "ticker":"", "exchange":"", "confidence": 0.0}
  ],
  "timeseries": {
    "title": "Competitor price movement",
    "unit": "level|index",
    "frequency": "yearly",
    "x": ["YYYY", ...],
    "series": [
      {"name":"<Company>", "ticker":"<TICKER>", "data":[...]}
    ]
  },
  "notes": [],
  "data_gaps": []
}

Rules:
- If neither competitors nor a useful query is provided, return empty arrays and add a note like "no competitors provided or inferred".
- Do NOT output any text outside the JSON object.
  """
)

# MarketTrendAnalyzer (product vs sector + adoption)
market_trend_anlyzer_agent = Agent(
    name="MarketTrendAnalyzerAgent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools()],
    instructions="""
Emit JSON ONLY.

INPUT:
{
  "query": "plain English subject the user is asking about",  // REQUIRED
  "period": {"from":"YYYY","to":"YYYY"},                      // OPTIONAL
  "region": "global|country|region name",                     // OPTIONAL (default global)
  "rebase": "none|per_series"                                 // OPTIONAL (default none = raw levels)
}

GOAL:
- Using ONLY the provided 'query' as the subject, produce BOTH of the following when applicable:
  (1) Sector-level market index/level movement relevant to the query (yearly).
  (2) Adoption patterns: earliest notable adopters and current dominant players.

PRODUCT vs SECTOR RULE:
- If the query names a specific product or sub-industry (e.g., "EV vehicles", "lithium batteries", "genAI chips"),
  include TWO series in the same chart:
    • product_index_or_level  — proxy for the specific product/sub-industry
    • sector_index_or_level   — proxy for the parent sector that product belongs to
- If the query refers to a broad sector (e.g., "Automobiles", "Cloud Security"),
  include ONLY the sector series.

PERIOD & REGION:
- Detect explicit period/region from the query if present.
- If not specified, default to:
  • period = {"from":"2019","to":"2025"}   // default 5‑year outlook (inclusive)
  • region = "global"

INDEX BUILDING (use tools = YFinanceTools):
1) Proxy selection
   - Prefer a representative ETF or recognized industry index for the subject (product-level where applicable) and for the parent sector.
   - If no direct ETF/index exists, approximate with an equal-weighted basket of 3–5 exchange-listed leaders. State this in proxies_used.
2) Pricing
   - Fetch YEARLY Adjusted Close for each selected proxy over the chosen period.
3) Rebase mode
   - If rebase == "none" (default): return raw YEARLY levels; set unit to "level (Adj Close)".
   - If rebase == "per_series": rebase each series to 100 at its first available year; set unit to "index (rebased=100)".

OUTPUT SCHEMA (JSON ONLY):
{
  "sector_performance": {
    "title": "«{Subject inferred from query}» — price movement",
    "unit": "level (Adj Close)|index (rebased=100)",
    "frequency": "yearly",
    "x": ["YYYY", "..."],
    "series": [
      {"name":"product_index_or_level","data":[...]},   // include iff product-level requested or inferred
      {"name":"sector_index_or_level","data":[...]}     // always for sector; alongside product when applicable
    ],
    "proxies_used": {
      "product": "<ticker(s) or method>",
      "sector": "<ticker(s) or method>"
    }
  },
  "period": {"from":"YYYY","to":"YYYY"},
  "region": "global|country|region name",
  "adoption": {
    "early_adopters_top3": [
      {"company":"...","why":"...","score":0}
    ],
    "current_adopters_top3": [
      {"company":"...","why":"...","score":0}
    ]
  },
  "notes": [
    "State assumptions (e.g., proxy selection, parent sector mapping, inferred region)."
  ],
  "data_gaps": []
}

STRICT:
- Output exactly one JSON object matching the schema.
- No prose outside JSON. No tool/function call traces in output.
"""
)

# EventSpikeAgent — uses query + adoption outputs when available
event_price_spike_agent = Agent(
    name="EventSpikeAgent",
    model= Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools()],
    instructions="""
Emit JSON ONLY.

INPUT:
{
  "query": "plain English subject the user is asking about",   // REQUIRED
  "adoption": {                                                  // OPTIONAL
    "early_adopters_top3": [{"company":"...","why":"...","score":0}],
    "current_adopters_top3": [{"company":"...","why":"...","score":0}]
  }
}

GOAL:
Detect the **latest (≤5)** notable **price-move events** for companies most relevant to the query.
Prioritize companies as follows:
  1) `adoption.current_adopters_top3` (names only)
  2) If none, `adoption.early_adopters_top3`
  3) If still none, infer 3–5 **publicly listed** companies from the **query** (sector/geo) using tools

METHOD (tools = YFinanceTools):
- Resolve a **primary exchange-listed ticker** for each chosen company (skip if none exists).
- Pull **DAILY Adjusted Close** for **year-to-date** (from Jan 1 to today) for each ticker.
- Compute **1-day price change %** and detect **spikes** (absolute move ≥ 5% = medium, ≥ 10% = high; else low). 
- For each company, keep its **newest** spikes; return **≤5 total**, **sorted newest → oldest** across companies.
- For each event, compute:
  • `price_move_1d_pct` (close→close around event date)
  • `price_move_period_pct` (from period start to event date)
  • `direction` "+" or "-" ; `magnitude` low|medium|high; `confidence` 0–1 (heuristic)
- If no tickers can be resolved, return empty arrays and a note such as "no companies provided or inferred".

OUTPUT SCHEMA (JSON ONLY):
{
  "companies": [ {"company":"...","ticker":"..."} ],
  "events_detected": [
    {
      "date":"YYYY-MM-DD",
      "type":"price_spike",
      "entity_or_topic":"COMPANY or TICKER",
      "direction":"+|-",
      "price_move_1d_pct": 0.0,
      "price_move_period_pct": 0.0,
      "magnitude":"low|medium|high",
      "confidence":0.0,
      "headline":"Price spike detected",
      "blurb":"Detected via daily % move threshold; no headline lookup"
    }
  ],
  "period":{"from":"YYYY-MM-DD","to":"YYYY-MM-DD"},
  "method":["companies from adoption if available","query-inferred companies if needed","YFinance daily prices"],
  "assumptions":[],
  "notes":[],
  "data_gaps":[]
}

STRICT:
- Output **only** the JSON object above.
- Ensure `events_detected` length ≤ 5 and sorted by date desc.
  """
)

# ---------------------------
# Agent Functions
# ---------------------------

def CompetitorTrend_agent(query: str | None = None):
    """
    Minimal receiver/runner:
    - Prefer payload from protocol channel 'CompetitorTrendAgent' when it includes competitors
    - Otherwise, if a query is provided, pass it so the agent can infer competitors
    - Return the agent's raw JSON text
    """
    payload = protocol.receive("CompetitorTrendAgent")
    if not isinstance(payload, dict):
        payload = {}
    # Prefer explicit competitors from protocol; else fall back to query
    has_competitors = bool(payload.get("competitors"))
    if not has_competitors:
        if query:
            payload = {"query": query}
        else:
            payload = {"competitors": []}
    # Apply defaults if not specified by upstream
    payload.setdefault("period", {"from": "2019", "to": "2025"})
    payload.setdefault("region", "global")
    payload.setdefault("rebase", "per_series")
    try:
        # Run the agent and capture raw text
        raw = _agent_text(competitor_trend_agent.run(json.dumps(payload)))
        # Print raw for debugging before salvage
        print("\n[CompetitorTrendAgent][raw]\n" + str(raw) + "\n")

        # Common fallback used if parsing fails or output is empty
        def _fallback(note: str):
            return json.dumps({
                "resolved_tickers": [],
                "timeseries": {
                    "title": "Competitor price movement",
                    "unit": "index (rebased=100)",
                    "frequency": "yearly",
                    "x": [],
                    "series": []
                },
                "notes": [note],
                "data_gaps": []
            })

        parsed = _salvage_json(raw)
        # If salvage returns nothing or an empty dict, emit fallback with a note
        if not parsed or (isinstance(parsed, dict) and len(parsed) == 0):
            text = _fallback("empty_or_invalid_output; raw was captured in log")
        else:
            # Accept either a dict or a JSON string; normalize to JSON text for downstream/UI
            text = parsed if isinstance(parsed, str) else json.dumps(parsed)
    except Exception as e:
        text = json.dumps({
            "resolved_tickers": [],
            "timeseries": {
                "title": "Competitor price movement",
                "unit": "index (rebased=100)",
                "frequency": "yearly",
                "x": [],
                "series": []
            },
            "notes": [f"error: {str(e)}"],
            "data_gaps": []
        })
    print("\n=== [CompetitorTrendAgent] Output ===")
    print(text)
    print("=== [CompetitorTrendAgent] Output End ===\n")
    return text

def MarketTrendAnalyzer_agent(query: str):
    """
    Minimal runner for MarketTrendAnalyzerAgent (keeps other agents intact).
    Input: query (string)
    Behavior: send {"query": query} to the agent and return raw JSON text.
    """
    try:
        payload = {"query": query, "period": {"from": "2019", "to": "2025"}, "region": "global", "rebase": "none"}
        raw = _agent_text(market_trend_anlyzer_agent.run(json.dumps(payload)))
        text = _salvage_json(raw) or {}
    except Exception as e:
        fallback = {
            "sector_performance": {
                "title": "",
                "unit": "index (rebased=100)",
                "frequency": "yearly",
                "x": [],
                "series": [{"name": "sector_index", "data": []}],
                "proxies_used": {"product": "", "sector": ""}
            },
            "period": {"from": "", "to": ""},
            "adoption": {
                "early_adopters_top3": [],
                "current_adopters_top3": []
            },
            "notes": [f"error: {str(e)}"],
            "data_gaps": []
        }
        text = json.dumps(fallback)
    print("\n=== [MarketTrendAnalyzerAgent] Output ===")
    print(text)
    print("=== [MarketTrendAnalyzerAgent] Output End ===\\n")
    return text

def EventPriceSpike_agent(query: str, adoption: dict | None = None):
    payload = {"query": query}
    if isinstance(adoption, dict):
        payload["adoption"] = adoption
    try:
        raw = _agent_text(event_price_spike_agent.run(json.dumps(payload)))
        text = _salvage_json(raw) or {}
    except Exception as e:
        fallback = {
            "companies": [],
            "events_detected": [],
            "period": {"from": "", "to": ""},
            "method": ["error"],
            "assumptions": [],
            "notes": [f"error: {str(e)}"],
            "data_gaps": []
        }
        text = json.dumps(fallback)
    # <- moved out of except so it runs on both paths
    print("\n=== [EventSpikeAgent] Output ===")
    print(text)
    print("=== [EventSpikeAgent] Output End ===\n")
    return text   

# Example usage:
# results = CompetitorTrend_agent("Electric Vehicle market trends")
# print(results)
