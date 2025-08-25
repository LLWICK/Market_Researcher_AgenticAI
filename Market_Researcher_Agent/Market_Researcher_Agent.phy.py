#!/usr/bin/env -S uv run python
# ↑ This ensures the script always runs inside your uv-managed environment.

"""
Market Researcher Agent (manual web orchestration) -> JSON output

Adaptive to user intent (industry / product / company / generic topic),
optional timeframe, and region.

Workflow:
  1) Read user_request (later replaced by UI input)
  2) Build a topic string & smart search queries from user_request
  3) Search the web (DuckDuckGo HTML)
  4) Fetch & clean top results
  5) Summarize into structured JSON using an LLM
  6) Print JSON to terminal (no file writes)
"""

from __future__ import annotations

import json
import re
from typing import List, Dict, Any, Tuple

import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from phi.agent import Agent
from phi.model.ollama import Ollama



load_dotenv()


# ---------------------------
# User request placeholder
# ---------------------------
# Will be populated later using a frontend form
user_request: Dict[str, Any] = {
    "intent": "industry",               # "industry" | "product" | "company" | "topic"
    "query": "Sri Lanka construction",  # Industry / product class / company / generic topic
    "region": "Sri Lanka",              # Optional: e.g., "South Asia", "Global"
    "timeframe": {                      # Optional timeframe
        "start": "2023-01",
        "end": "2025-08"
    },
    # Optional downstream hints (not critical for this agent, but helps others)
    "focus": ["demand", "prices_costs", "projects_policy", "risks", "outlook"],
    "notes": "Emphasize government projects and financing constraints."
}


# ---------------------------
# Web search function
# ---------------------------
def web_search(query: str, n: int = 5) -> List[Dict[str, str]]:
    """
    Perform a DuckDuckGo HTML search for the given query.
    Returns a list of dictionaries: {title, url, snippet}.
    """
    url = f"https://duckduckgo.com/html/?q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html5lib")

    results: List[Dict[str, str]] = []
    # Collect top n results
    for res in soup.select(".result")[:n]:
        a = res.select_one("a.result__a")          # Result title link
        snippet = res.select_one(".result__snippet")  # Preview text
        if not a:
            continue
        title = a.get_text(" ", strip=True)
        link = a.get("href")
        text = snippet.get_text(" ", strip=True) if snippet else ""
        results.append({"title": title, "url": link, "snippet": text})
    return results


# ---------------------------
# Page fetch + clean function
# ---------------------------
def fetch_page(url: str, max_chars: int = 6000) -> Dict[str, str]:
    """
    Fetch a webpage, strip out noisy HTML, and return clean text.
    Truncates to max_chars to avoid overwhelming the LLM.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html5lib")

    # Page title if available
    title = (soup.title.string or "").strip() if soup.title else ""

    # Remove scripts, styles, navigation, ads, etc.
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()

    # Choose main content area (article > main > body fallback)
    container = soup.find(["article", "main"]) or soup.body or soup
    text = container.get_text("\n", strip=True)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return {"title": title, "text": text[:max_chars]}


# ---------------------------
# Topic & query builder
# ---------------------------
def build_topic_and_queries(req: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Build:
      - A 'topic' string to give the LLM full context
      - A set of search queries adapted to intent/timeframe/region
    """
    intent = (req.get("intent") or "topic").lower()
    q = (req.get("query") or "").strip()
    region = (req.get("region") or "").strip()
    tf = req.get("timeframe") or {}
    start, end = tf.get("start", ""), tf.get("end", "")

    # Build topic string (for prompt clarity)
    parts = []
    if intent == "industry":
        parts.append(f"Industry: {q}")
    elif intent == "product":
        parts.append(f"Product class: {q}")
    elif intent == "company":
        parts.append(f"Company: {q}")
    else:
        parts.append(f"Topic: {q or 'General market research'}")

    if region:
        parts.append(f"Region: {region}")
    if start or end:
        tf_label = f"Timeframe: {start or '...'} to {end or '...'}"
        parts.append(tf_label)

    parts.append("Focus: demand, prices/costs, projects/policy, risks, outlook")

    topic = " | ".join(parts)

    # Build timeframe hint for queries
    timeframe_hint = ""
    if start and end:
        timeframe_hint = f"{start}..{end}"
    elif start:
        timeframe_hint = f"since {start}"
    elif end:
        timeframe_hint = f"until {end}"

    base = q if q else "market research"

    # Intent-specific search boosters
    if intent == "company":
        boosters = [
            f"{base} annual report {timeframe_hint} {region}".strip(),
            f"{base} earnings outlook {timeframe_hint} {region}".strip(),
            f"{base} market share competitors {timeframe_hint} {region}".strip(),
        ]
    elif intent == "product":
        boosters = [
            f"{base} demand price trends {timeframe_hint} {region}".strip(),
            f"{base} supply chain costs {timeframe_hint} {region}".strip(),
            f"{base} regulations standards {timeframe_hint} {region}".strip(),
        ]
    elif intent == "industry":
        boosters = [
            f"{base} market size demand {timeframe_hint} {region}".strip(),
            f"{base} material prices costs {timeframe_hint} {region}".strip(),
            f"{base} government projects policy {timeframe_hint} {region}".strip(),
        ]
    else:
        boosters = [
            f"{base} latest report {timeframe_hint} {region}".strip(),
            f"{base} trends risks {timeframe_hint} {region}".strip(),
            f"{base} outlook {timeframe_hint} {region}".strip(),
        ]

    return topic, boosters[:3]  # Return topic + first 3 queries


# ------------------------------------
# Agent (LLM wrapper for summarization)
# ------------------------------------
market_research_agent = Agent(
    model=Ollama(id="llama3.2"),  # LLM backend via Ollama
    markdown=False,   # Ensure JSON output, not markdown
    instructions=(
        "You are a Market Researcher. You will receive multiple sources of text content. "
        "Synthesize a concise, structured brief with sections for: Demand, Prices/Costs, "
        "Projects/Policy, Risks, and Outlook. Only use facts supported by the provided sources. "
        "Respond STRICTLY in JSON using the provided schema. Do NOT include any text outside JSON. "
        "Add bracketed citations like [S1], [S2] matching the numbered sources you were given."
    ),
)


# ----------------------------------------------------
# Orchestrator: search → fetch pages → summarize
# ----------------------------------------------------
def research_and_summarize_json(topic: str, search_queries: List[str], n_results: int = 5, n_open: int = 3) -> Dict[str, Any]:
    """
    End-to-end flow:
      1) Run primary search query (fallback to others if sparse)
      2) Fetch & clean text for top n_open results
      3) Build a structured prompt
      4) Call LLM for JSON summary
      5) Validate/fix JSON and return
    """
    # Step 1: Search
    primary_query = search_queries[0] if search_queries else topic
    results = web_search(primary_query, n=n_results)

    # Fallback: if too few results, try other queries
    if len(results) < n_open and len(search_queries) > 1:
        for q in search_queries[1:]:
            more = web_search(q, n=n_results)
            seen = {r["url"] for r in results}
            results.extend([m for m in more if m["url"] not in seen])
            if len(results) >= n_open:
                break

    opened: List[Dict[str, str]] = []

    # Step 2: Fetch text for top results
    for r in results[:n_open]:
        try:
            page = fetch_page(r["url"])
            opened.append({
                "title": page["title"] or r["title"],
                "url": r["url"],
                "snippet": r.get("snippet", ""),
                "text": page["text"]
            })
        except Exception as e:
            # Keep metadata even if fetch fails
            opened.append({
                "title": r["title"],
                "url": r["url"],
                "snippet": r.get("snippet", ""),
                "text": f"[Fetch failed: {e}]"
            })

    if not opened:
        return {"topic": topic, "sources": [], "summary": {}, "error": "No sources opened"}

    # Source metadata for structured JSON
    sources_meta = [{"id": f"S{i+1}", "title": s["title"], "url": s["url"]} for i, s in enumerate(opened)]

    # Combine sources into text block for the prompt
    sources_block = "\n\n".join(
        f"### Source {i+1} ({sources_meta[i]['id']}): {s['title']}\nURL: {s['url']}\n\n{s['text']}"
        for i, s in enumerate(opened)
    )

    # Build prompt for LLM
    prompt = f"""
You are a Market Researcher. Summarize the latest on:
{topic}

Use ONLY the facts from the sources provided below.

Respond STRICTLY in JSON with this exact schema (no extra text):

{{
  "topic": "...",
  "sources": [
    {{"id": "S1", "title": "...", "url": "..."}},
    {{"id": "S2", "title": "...", "url": "..."}}
  ],
  "summary": {{
    "demand": ["... [S1]"],
    "prices_costs": ["... [S1]"],
    "projects_policy": ["... [S2]"],
    "risks": ["... [S1]"],
    "outlook": ["... [S1][S2]"]
  }}
}}
Here are the sources:
{sources_block}
"""

    # Step 3: Call LLM agent
    resp = market_research_agent.run(prompt)
    raw = getattr(resp, "content", str(resp))

    # Step 4: Safe JSON parse
    obj = _safe_json_parse(raw)

    if obj is None:
        # If model failed to return JSON, wrap raw
        obj = {
            "topic": topic,
            "sources": sources_meta,
            "summary_raw": raw,
            "warning": "Model did not return valid JSON; raw text provided."
        }
    else:
        # Ensure schema completeness
        obj["topic"] = obj.get("topic", topic)
        obj["sources"] = sources_meta
        summary = obj.get("summary", {})
        for key in ["demand", "prices_costs", "projects_policy", "risks", "outlook"]:
            if key not in summary or summary[key] is None:
                summary[key] = []
        obj["summary"] = summary

    return obj


# ---------------------------
# Helper: safe JSON parser
# ---------------------------
def _safe_json_parse(text: str) -> Dict[str, Any] | None:
    """
    Try to parse text as JSON.
    If model output has extra text, attempt to extract the JSON substring.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    break
    return None


# -------------------------
# Main entrypoint
# -------------------------
def main() -> None:
    """
    Script entry:
      1) Build topic & queries from user_request
      2) Run search + fetch + summarize
      3) Print JSON result to terminal
    """
    topic, queries = build_topic_and_queries(user_request)

    n_results = 6  # Search results per query
    n_open = 3     # Pages fetched in full

    result = research_and_summarize_json(topic, queries, n_results=n_results, n_open=n_open)

    # ✅ Print structured JSON result
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
