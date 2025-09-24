# utills/ticker_cache.py
from pathlib import Path
import json, time

CACHE_PATH = Path(".cache/tickers.json")
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

def _slug(s): return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace()).strip()

def load_cache():
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}

def save_cache(d):
    CACHE_PATH.write_text(json.dumps(d, indent=2))

def get_cached(name, ttl_days=30):
    cache = load_cache()
    key = _slug(name)
    item = cache.get(key)
    if not item: return None
    if time.time() - item.get("ts", 0) > ttl_days*86400: return None
    return item

def put_cached(name, ticker, exchange):
    cache = load_cache()
    cache[_slug(name)] = {"ticker": ticker, "exchange": exchange, "ts": time.time()}
    save_cache(cache)