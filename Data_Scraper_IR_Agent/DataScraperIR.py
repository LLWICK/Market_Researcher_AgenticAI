# Testing IR retrieve code base

# agents/data_scraper_ir.py
from __future__ import annotations
import os, time, json, hashlib, urllib.parse, logging, re, requests
from typing import List, Dict, Optional, Iterable
from datetime import datetime
from pydantic import BaseModel, HttpUrl, ValidationError
from dotenv import load_dotenv
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import MultifieldParser
import urllib.robotparser as robotparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
BASE = Path(os.getcwd())

# Use the / operator to join path components
INDEX_DIR = BASE / "storage" / "index"
CACHE_DIR = BASE / "storage" / "cache"
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DataScraperIR")

UA = "Mozilla/5.0 DataScraperIR/1.0"
TIMEOUT = 12
ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_DOMAINS: Optional[set[str]] = None   # e.g. {"reuters.com", "bloomberg.com"}

class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: Optional[str] = None
    source: Optional[str] = None
    date: Optional[str] = None

class Document(BaseModel):
    title: str
    url: HttpUrl
    content: str
    source: Optional[str] = None
    published_at: Optional[datetime] = None

def _valid_url(u: str) -> bool:
    try:
        p = urllib.parse.urlparse(u)
        if p.scheme not in ALLOWED_SCHEMES: return False
        if ALLOWED_DOMAINS:
            host = (p.netloc or "").lower()
            return any(host.endswith(d) for d in ALLOWED_DOMAINS)
        return True
    except: return False

def _robots_ok(u: str) -> bool:
    try:
        p = urllib.parse.urlparse(u)
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(UA, u)
    except: return False

def _cache_path(u: str) -> str:
    h = hashlib.sha256(u.encode()).hexdigest()[:24]
    return os.path.join(CACHE_DIR, f"{h}.json")

def _load_cache(u: str) -> Optional[dict]:
    p = _cache_path(u)
    return json.load(open(p, "r", encoding="utf-8")) if os.path.exists(p) else None

def _save_cache(u: str, d: dict) -> None:
    json.dump(d, open(_cache_path(u), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- Search with Serper (Google Search API)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(1, 2, 8), reraise=True)
def serper_news(query: str, num: int = 10) -> List[SearchResult]:
    if not SERPER_API_KEY:
        raise RuntimeError("SERPER_API_KEY missing")
    r = requests.post(
        "https://google.serper.dev/news",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": min(num, 20)},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    out = []
    for it in data.get("news", []):
        try:
            out.append(SearchResult(
                title=it.get("title", ""),
                url=it.get("link", ""),
                snippet=it.get("snippet"),
                source=it.get("source"),
                date=it.get("date"),
            ))
        except ValidationError:
            continue
    return out

# ---- Fetch & extract
class ScrapeError(Exception): pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(1, 2, 6), reraise=True)
def fetch_html(url: str) -> str:
    if not _valid_url(url): raise ScrapeError("Invalid/disallowed URL")
    if not _robots_ok(url): raise ScrapeError("robots.txt disallows")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_text(html: str, url: str) -> Optional[str]:
    txt = trafilatura.extract(html, url=url, include_comments=False, include_tables=False)
    return txt if txt and len(txt.split()) >= 60 else None

def make_doc(url: str, title_hint=None, source=None, date_str=None) -> Optional[Document]:
    cached = _load_cache(url)
    if cached:
        try: return Document(**cached)
        except ValidationError: pass
    html = fetch_html(url)
    content = extract_text(html, url)
    if not content: return None
    title = title_hint or content.splitlines()[0][:120]
    published_at = None
    if date_str:
        try: published_at = datetime.fromisoformat(re.sub("Z$", "+00:00", date_str))
        except: pass
    doc = Document(title=title, url=url, content=content, source=source, published_at=published_at)
    _save_cache(url, json.loads(doc.json()))
    return doc

# ---- Whoosh index
def _ensure_index():
    schema = Schema(
        url=ID(stored=True, unique=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        content=TEXT(stored=False, analyzer=StemmingAnalyzer()),
        source=TEXT(stored=True),
        published_at=DATETIME(stored=True),
    )
    if not os.listdir(INDEX_DIR):
        return create_in(INDEX_DIR, schema)
    return open_dir(INDEX_DIR)

def index_docs(docs: Iterable[Document]) -> int:
    ix = _ensure_index()
    w = ix.writer(limitmb=128)
    n = 0
    for d in docs:
        w.update_document(
            url=str(d.url),
            title=d.title,
            content=d.content,
            source=d.source or "",
            published_at=d.published_at
        ); n += 1
    w.commit()
    return n

def ir_search(query: str, limit: int = 10) -> List[Dict]:
    ix = _ensure_index()
    with ix.searcher() as s:
        q = MultifieldParser(["title", "content"], ix.schema).parse(query)
        rs = s.search(q, limit=limit)
        return [{
            "title": r.get("title"),
            "url": r.get("url"),
            "source": r.get("source"),
            "published_at": r.get("published_at").isoformat() if r.get("published_at") else None,
            "score": float(r.score),
        } for r in rs]

# ---- Orchestrate: search -> scrape -> index
import aiohttp, asyncio
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from whoosh.writing import AsyncWriter
import os, json
from trafilatura import extract

# 🔧 Schema (same as before)
schema = Schema(
    title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    url=ID(stored=True, unique=True)
)

INDEX_DIR = "indexdir"
CACHE_FILE = "cache.json"
TIMEOUT = 6  # faster fallback

# -----------------------
# ✅ Cache helpers
# -----------------------
def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

# -----------------------
# ✅ Async fetch
# -----------------------
async def fetch_async(url: str, session: aiohttp.ClientSession) -> str | None:
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT) as r:
            if r.status == 200:
                return await r.text()
            return None
    except Exception:
        return None

async def scrape_all_async(urls: list[str]) -> dict[str, str]:
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_async(url, session) for url in urls]
        html_list = await asyncio.gather(*tasks, return_exceptions=True)
        for url, html in zip(urls, html_list):
            if isinstance(html, Exception) or html is None:
                continue
            text = extract(html)  # trafilatura parse
            if text:
                results[url] = text
    return results

# -----------------------
# ✅ Collect + Index
# -----------------------
def collect_and_index(query: str, k_search: int = 10, k_index: int = 5):
    """
    1. Search via Serper (or your IR search tool)
    2. Async scrape + extract
    3. Cache + Whoosh indexing
    4. Return JSON summary
    """
    # 🔎 Step 1: search
    from DataScraperIR import serper_news   # import your search func
    results = serper_news(query, num=k_search)

    urls = [r["link"] for r in results if "link" in r][:k_index]
    cache = _load_cache()

    # Use cache if available
    fresh_urls = [u for u in urls if u not in cache]

    # 🔎 Step 2: scrape new docs
    if fresh_urls:
        scraped = asyncio.run(scrape_all_async(fresh_urls))
        cache.update(scraped)
        _save_cache(cache)

    # 🔎 Step 3: Whoosh indexing
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
        ix = index.create_in(INDEX_DIR, schema)
    else:
        ix = index.open_dir(INDEX_DIR)

    writer = AsyncWriter(ix)
    for url in urls:
        if url in cache:
            writer.update_document(title=url, content=cache[url], url=url)
    writer.commit()

    # 🔎 Step 4: return structured output
    return {
        "query": query,
        "indexed": len([u for u in urls if u in cache]),
        "docs": urls
    }




""" print(collect_and_index("Nvidia stock prices upto 2025 give me the response in jason format", k_search=10, k_index=6))
hits = ir_search("NVIDIA earnings GPU AI data center")
for h in hits[:5]:
    print(f"- {h['title']} -> {h['url']} [{h['source']}] (score={h['score']:.2f})") """


"""  # Step 1: Scrape and index relevant docs
result = collect_and_index(
    "Tesla stock market stats upto 2025 and competitors of tesla",
    k_search=15, k_index=8
)
print(result)   # shows what was indexed

# Step 2: Search inside the indexed data
hits = ir_search("Competitors of Tesla comparison")
for h in hits[:5]:
    print(h)   """



""" from phi.agent import Agent, Tool
from phi.model.groq import Groq
import os

# Initialize Phi LLM
llm = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

# Wrap Python functions as Tools
scrape_tool = Tool(
    type="python",
    name="ScrapeMarketingData",
    description="Scrapes & indexes marketing data based on user prompt",
    func=lambda prompt: collect_and_index(prompt, k_search=15, k_index=8)
)

search_tool = Tool(
    type="python",
    name="SearchIndex",
    description="Searches indexed documents for insights",
    func=lambda query: ir_search(query)[:5]
)

# Create the agent with tools
marketing_agent = Agent(
    name="Marketing Research Agent",
    model=llm,
    instructions=(
        "You are a marketing research assistant. "
        "Your job is to fetch and summarize the latest marketing data using the provided scraping & IR tools."
    ),
    tools=[scrape_tool, search_tool]
)

# Run the agent with a prompt
response = marketing_agent.run(
    "Get me the latest 2025 digital marketing spend forecasts in Asia "
    "and summarize the top insights."
)
print(response) """
