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

""" def _load_cache(u: str) -> Optional[dict]:
    p = _cache_path(u)
    return json.load(open(p, "r", encoding="utf-8")) if os.path.exists(p) else None """

def _load_cache(u: str) -> Optional[dict]:
    p = _cache_path(u)
    if os.path.exists(p):
        log.info(f"Cache hit for {u}")
        return json.load(open(p, "r", encoding="utf-8"))
    log.info(f"Cache miss for {u}")
    return None


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
    if not _valid_url(url):
        raise ScrapeError("Invalid/disallowed URL")
    # disable robots.txt strictness if you want:
    # if not _robots_ok(url): log.warning(f"robots.txt disallows {url}, skipping")
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
    try:
        if not os.listdir(INDEX_DIR):
            return create_in(INDEX_DIR, schema)
        return open_dir(INDEX_DIR)
    except Exception as e:
        log.warning(f"Recreating index due to error: {e}")
        for f in os.listdir(INDEX_DIR):
            os.remove(INDEX_DIR / f)
        return create_in(INDEX_DIR, schema)


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
def collect_and_index(query: str, k_search: int = 10, k_index: int = 8) -> Dict:
    results = serper_news(query, num=k_search)
    docs = []
    for it in results[:k_index]:
        try:
            d = make_doc(str(it.url), title_hint=it.title, source=it.source, date_str=it.date)
            if d:
                docs.append(d)
                time.sleep(1.0)  # be polite
        except Exception as e:
            log.warning(f"Skip {it.url}: {e}")
    n = index_docs(docs)
    return {
        "indexed": n,
        "query": query,
        "docs": [d.dict() for d in docs],  # include full documents
        "examples": [d.title for d in docs[:5]]
    }



""" print(collect_and_index("Nvidia stock prices upto 2025 give me the response in jason format", k_search=10, k_index=6))
hits = ir_search("NVIDIA earnings GPU AI data center")
for h in hits[:5]:
    print(f"- {h['title']} -> {h['url']} [{h['source']}] (score={h['score']:.2f})") """


"""  # Step 1: Scrape and index relevant docs
result = collect_and_index(
    "Smart Phone market stats upto 2025",
    k_search=15, k_index=8
)
print(result)   # shows what was indexed

# Step 2: Search inside the indexed data
hits = ir_search("Competitors comparison in smartphone industry")
for h in hits[:5]:
    print(h) """  


""" results = serper_news("Smart Phone market stats upto 2025")
print("Results:", results)

docs = [make_doc(str(it.url), title_hint=it.title, source=it.source, date_str=it.date)
        for it in results[:8]]
print("Docs:", docs)

n = index_docs([d for d in docs if d])
print("Indexed:", n) """




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
