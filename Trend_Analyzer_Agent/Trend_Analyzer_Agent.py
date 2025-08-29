# trend_analyzer_phi.py
# Market-level NLP-first trend analyzer (phidata + DuckDuckGo, with robust ddgs fallback).
# Focus: aggregated market signals (sentiment/topics/NER/keywords). Finance = tiny snapshots only.

import os, json, random, time, re, warnings, math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Iterable

from dotenv import load_dotenv
DOTENV_PATH = Path(__file__).with_name(".env")
load_dotenv(DOTENV_PATH)

# Quiet the deprecation warning from phidata's duckduckgo wrapper
warnings.filterwarnings(
    "ignore",
    message="This package (`duckduckgo_search`) has been renamed to `ddgs`",
    category=RuntimeWarning,
)

# --- phidata ---
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
try:
    from groq import BadRequestError
except Exception:
    BadRequestError = Exception

# --- direct ddgs fallback (robust) ---
try:
    from ddgs import DDGS
    _DDGS_OK = True
except Exception:
    _DDGS_OK = False

# --- Optional NLP (graceful skips) ---
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    _NLTK_OK = True
except Exception:
    _NLTK_OK = False

try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    _SK_OK = True
except Exception:
    _SK_OK = False

try:
    import spacy
    _SPACY = spacy.load("en_core_web_sm")
except Exception:
    _SPACY = None

# ---------------- Config ----------------
DEFAULT_TOPIC = os.getenv("TOPIC", "Virtual Reality Technologies in Tech Sector")
DEFAULT_BRAND = os.getenv("BRAND", "APPL")
MAX_SUGGEST   = 6
MAX_USE       = 3
MARKET_NEWS_TARGET = 30      # aim for ~30 titles across all queries/fallbacks
PER_QUERY_MAX       = 10     # per-query cap
GROQ_MODEL    = "llama-3.3-70b-versatile"
RETRIES       = 2

# ---------------- Small utils ----------------
def only_text(resp) -> str:
    txt = getattr(resp, "content", None)
    if isinstance(txt, str) and txt:
        return txt
    return str(resp)

def parse_pairs(text: str, cap: int) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or "<function=" in line or "content='" in line:
            continue
        m = re.match(r"^\s*([A-Za-z0-9 .&'\"/\-\(\)]+)\s*\|\s*([A-Za-z0-9.\-:]+)\s*$", line)
        if not m: 
            continue
        name, tik = m.group(1).strip(), m.group(2).strip()
        if name.lower() == "company" or tik.lower() == "ticker":
            continue
        pairs.append((name, tik))
        if len(pairs) >= cap: 
            break
    return pairs

def dedup(seq: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        s = s.strip()
        if not s: 
            continue
        key = s.casefold()
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out

def sleep_backoff(i: int):
    time.sleep((2**i) + random.uniform(0, 0.5))

# ---------------- Build Agent ----------------
def build_agent() -> Agent:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY missing in .env next to this script.")
    return Agent(
        model=Groq(id=GROQ_MODEL),
        tools=[
            YFinanceTools(stock_price=False, stock_fundamentals=True, analyst_recommendations=False),
            DuckDuckGo()
        ],
        instructions=[
            "Be concise and data-driven.",
            "For discovery, do NOT call tools unless asked.",
            "For headlines, use duckduckgo_search once per query with max_results<=10; return titles only.",
        ],
        markdown=False,
        show_tool_calls=False,
        debug_mode=False
    )

def agent_no_tools(agent: Agent) -> Agent:
    return Agent(
        model=agent.model,
        tools=[],
        instructions=agent.instructions,
        markdown=agent.markdown,
        show_tool_calls=agent.show_tool_calls,
        debug_mode=agent.debug_mode
    )

# ---------------- 1) Companies (model-only; no tools) ----------------
def propose_companies(agent: Agent, topic: str, brand: str, cap: int) -> List[Tuple[str,str]]:
    discover = agent_no_tools(agent)
    p = f"""Return up to {cap} PUBLIC companies for:
Topic: "{topic}"
Brand (optional): "{brand or 'N/A'}"
Format: Company Name | TICKER (one per line). No extra words. No tools."""
    txt = only_text(discover.run(p))
    pairs = parse_pairs(txt, cap)
    if pairs: 
        return pairs

    txt2 = only_text(discover.run(
        f"Return 3 PUBLIC companies for '{topic}'. Lines only: Company | TICKER. No tools."
    ))
    pairs = parse_pairs(txt2, 3)
    if pairs:
        return pairs

    # Tiny fallback so pipeline continues
    fallbacks = {
        "clean energy": [("NextEra Energy","NEE"), ("First Solar","FSLR"), ("Vestas Wind Systems","VWS.CO")],
        "laptop":       [("Dell Technologies","DELL"), ("HP Inc","HPQ"), ("ASUSTeK Computer","ASUUY")]
    }
    for k,v in fallbacks.items():
        if k in topic.lower():
            return v[:cap]
    return [("Dell Technologies","DELL"), ("HP Inc","HPQ")][:cap]

# ---------------- 2) Market headlines (phidata tool first, ddgs fallback) ----------------
def _ddg_titles_from_agent(agent: Agent, query: str, limit: int) -> List[str]:
    q = f'Use duckduckgo_search to return up to {min(limit,10)} titles only (no links) for recent news about "{query}" in the past 90 days.'
    for i in range(RETRIES):
        try:
            out = only_text(agent.run(q))
            # agent often returns JSON list from the tool; parse if present
            titles = []
            t = out.strip()
            if t.startswith("[") or t.startswith("{"):
                try:
                    data = json.loads(t)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "title" in item:
                                titles.append(str(item["title"]).strip())
                except Exception:
                    pass
            if not titles:
                titles = [ln.strip("-• ").strip() for ln in t.splitlines() if ln.strip() and "<function=" not in ln and "content='" not in ln]
            return dedup(titles)[:min(limit,10)]
        except BadRequestError:
            sleep_backoff(i)
    return []

def _ddgs_news(query: str, max_results: int) -> List[str]:
    if not _DDGS_OK:
        return []
    titles = []
    try:
        with DDGS() as ddg:
            for item in ddg.news(query, max_results=max_results):
                title = item.get("title")
                if title:
                    titles.append(title.strip())
    except Exception:
        pass
    return dedup(titles)

def gather_market_headlines(agent: Agent, topic: str, companies: List[Tuple[str,str]]) -> List[str]:
    titles: List[str] = []

    # 1) Multi-angle market queries
    queries = [
        topic,
        f"{topic} market outlook",
        f"{topic} policy subsidies regulation",
        f"{topic} supply chain",
        f"{topic} price trend demand",
        f"{topic} investment financing M&A",
    ]

    # 2) Add one or two company context queries (brand-agnostic)
    for name, tik in companies[:2]:
        queries.append(f"{name} {tik} industry trend {topic}")

    # First try via phidata tool, then top-up via ddgs if thin
    for q in queries:
        titles.extend(_ddg_titles_from_agent(agent, q, PER_QUERY_MAX))
        if len(titles) >= MARKET_NEWS_TARGET:
            break

    if len(titles) < math.ceil(MARKET_NEWS_TARGET * 0.6):
        # top up via direct ddgs (more reliable)
        for q in queries:
            titles.extend(_ddgs_news(q, max_results=PER_QUERY_MAX))
            if len(titles) >= MARKET_NEWS_TARGET:
                break

    return dedup(titles)[:MARKET_NEWS_TARGET]

# ---------------- 3) Market-level NLP ----------------
def nlp_sentiment_market(texts: List[str]) -> Dict[str, Any]:
    if not texts or not _NLTK_OK:
        return {"mean": None, "pos%": None, "neg%": None, "n": len(texts), "note": "sentiment skipped"}
    try:
        sia = SentimentIntensityAnalyzer()
    except Exception:
        return {"mean": None, "pos%": None, "neg%": None, "n": len(texts), "note": "VADER missing"}
    scores = [sia.polarity_scores(t)["compound"] for t in texts if t.strip()]
    if not scores:
        return {"mean": None, "pos%": None, "neg%": None, "n": 0}
    pos = sum(s > 0.05 for s in scores)/len(scores)
    neg = sum(s < -0.05 for s in scores)/len(scores)
    return {"mean": round(sum(scores)/len(scores),3), "pos%": round(pos*100,1), "neg%": round(neg*100,1), "n": len(scores)}

def nlp_topics_market(texts: List[str], k: int=5, topn: int=6) -> List[List[str]]:
    if not texts or not _SK_OK:
        return []
    vec = CountVectorizer(stop_words="english", max_features=3000)
    X = vec.fit_transform(texts)
    lda = LatentDirichletAllocation(n_components=k, random_state=42).fit(X)
    terms = vec.get_feature_names_out()
    topics = []
    for comp in lda.components_:
        topics.append([terms[i] for i in comp.argsort()[:-topn-1:-1]])
    return topics

def nlp_entities_market(texts: List[str], max_items: int=12) -> List[str]:
    if not texts or _SPACY is None:
        return []
    from collections import Counter
    ents = []
    for t in texts:
        doc = _SPACY(t)
        ents += [e.text for e in doc.ents]
    return [txt for txt,_ in Counter(ents).most_common(max_items)]

# Keyword buckets – useful even without NLP libs
KEY_BUCKETS = {
    "solar":   ["solar","photovoltaic","PV","first solar","panel","module","inverter","enphase","microinverter"],
    "wind":    ["wind","turbine","vestas","offshore","onshore","orsted","siemens gamesa","blade"],
    "storage": ["battery","storage","lithium","lfp","solid-state","gigafactory","megapack"],
    "ev":      ["EV","electric vehicle","charging","charger","charging network","tesla","supercharger"],
    "policy":  ["subsidy","tariff","policy","tax credit","IRA","Inflation Reduction Act","FIT","PPA","auction","tender"],
    "china":   ["china","chinese","tariff","dumping","anticircumvention","import","export"],
    "rates":   ["interest rate","fed","ECB","financing","yield","bond","hike","cut"],
}

def bucket_counts(texts: List[str]) -> Dict[str,int]:
    counts = {k:0 for k in KEY_BUCKETS}
    low = [t.casefold() for t in texts]
    for k, terms in KEY_BUCKETS.items():
        for t in low:
            if any(term.casefold() in t for term in terms):
                counts[k] += 1
    return counts

# ---------------- 4) Tiny fundamentals snapshots (context only) ----------------
def fundamentals_once(agent: Agent, ticker: str) -> Dict[str, Any]:
    try:
        resp = agent.run(f"Call get_stock_fundamentals for symbol {ticker} and return the raw JSON only.")
        txt = only_text(resp).strip()
        data = json.loads(txt) if txt.startswith("{") else {}
        keep = {k:data.get(k) for k in ("symbol","company_name","sector","industry","market_cap","pe_ratio","pb_ratio","dividend_yield")}
        return {k:v for k,v in keep.items() if v is not None}
    except Exception:
        return {}

# ---------------- 5) Collect ----------------
def collect_market(agent: Agent, topic: str, pairs: List[Tuple[str,str]]) -> Dict[str, Any]:
    titles = gather_market_headlines(agent, topic, pairs)
    sentiment = nlp_sentiment_market(titles)
    topics = nlp_topics_market(titles, k=5, topn=6)
    entities = nlp_entities_market(titles, max_items=12)
    buckets = bucket_counts(titles)

    snapshots = []
    for name, tick in pairs[:MAX_USE]:
        snap = fundamentals_once(agent, tick)
        if snap:
            snap["label"] = f"{name} ({tick})"
            snapshots.append(snap)

    return {
        "topic": topic,
        "tickers": [{"company": n, "ticker": t} for n,t in pairs[:MAX_USE]],
        "headlines_analyzed": len(titles),
        "nlp_market": {
            "sentiment": sentiment,
            "topics": topics,
            "entities": entities,
            "keyword_buckets": buckets,
            "sample_headlines": titles[:12],
        },
        "company_snapshots": snapshots
    }

# ---------------- 6) Summarize ----------------
SUMMARY_PROMPT = """
You are the company's sole Market Trend Analyst.

Produce a professional, data-driven report for the market: "{topic}".
Use the structured metrics and bullet facts provided. No markdown.

Deliver these sections with concise paragraphs and bullet points:

1) Executive Summary
- One-line trend call for Short (weeks), Intermediate (months), Long (year+)
- Overall Trend Strength (0–100) and Confidence (0–100), with one-sentence rationale

2) Market Scope & Coverage
- Definition, segments, geographies
- Tracked universe (tickers/ETFs) and % market cap coverage (if known)

3) Market-wide Signals (last 60–90 days)
- Sentiment: mean, % positive/negative, change vs prior (if given)
- Topic Momentum: top 5 topics with prevalence %, and any notable rises/falls
- Entity Heat: top orgs/places/products
- Breadth: % of companies with positive sentiment; dispersion
- Policy/Regulatory Pulse: count & most-cited themes
- Innovation/Tech Pulse: launch/R&D/patent cues
- Optional: Interest Momentum (search trends) if provided

4) Competitive Landscape (quick)
- Top players (3–5) with a one-line signal each: sentiment, key topic, notable entity, share of voice (% of headlines)

5) Price & Risk Context (light)
- Sector proxy (ETF or basket) returns and realized vol (3/6/12m) if provided

6) Scenarios & Watchlist
- Base / Upside / Downside with qualitative likelihoods
- Reversal markers that would invalidate the current call
- What to watch next (3–5 items)

7) Method & Responsible AI Notes
- Data sources, sample size, obvious gaps/bias, and simple explainability of scores

Write clearly and crisply for executives. Avoid hype. Where data is missing, state it and proceed.
"""

def summarize(agent: Agent, data: Dict[str, Any]) -> str:
    return only_text(agent.run(SUMMARY_PROMPT + "\n\nContext:\n" + json.dumps(data, ensure_ascii=False))).strip()

# ---------------- Main ----------------
def main():
    topic = DEFAULT_TOPIC
    brand = DEFAULT_BRAND

    agent = build_agent()
    pairs = propose_companies(agent, topic, brand, cap=MAX_SUGGEST)
    print("Companies selected:", pairs)

    market_data = collect_market(agent, topic, pairs)
    print(f"Headlines analyzed: {market_data['headlines_analyzed']}")

    brief = summarize(agent, market_data)

    print("\n=== Market-Level NLP Trend Brief ===\n")
    print(brief)
    tickers_str = ", ".join(f"{t['company']} ({t['ticker']})" for t in market_data["tickers"])
    print(f"\nTickers included (context only): {tickers_str}")

    if not _DDGS_OK:
        print("\nNote: `ddgs` not installed. Install for stronger headline coverage: pip install ddgs")
    if not _NLTK_OK:
        print("Note: NLTK not installed; sentiment skipped. Install & download VADER to enable it.")
    if not _SK_OK:
        print("Note: scikit-learn not installed; topic modeling skipped.")
    if _SPACY is None:
        print("Note: spaCy/en_core_web_sm not installed; NER skipped.")

if __name__ == "__main__":
    main()