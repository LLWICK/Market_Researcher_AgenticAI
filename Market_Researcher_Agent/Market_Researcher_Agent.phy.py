#!/usr/bin/env -S uv run python
# ↑ Ensures execution inside uv-managed virtual environment

#-----Calling Market Researcher Agent from another agent-----------
"""
from Market_Researcher_Agent import run_market_research
summary_result = run_market_research("EV battery market trends 2025")
print(summary_result["summary"]["demand"])
"""
#-------------------------------------------------------------------

#------Function of this agent---------------------------------------
"""
Market Researcher Agent (using Groq/OpenAI LLM backend)

- Collects data via DataScraperIR
- Summarizes current market condition using LLM via Groq Cloud
- Can be called via function OR run standalone
"""

import json
import os
import hashlib
from typing import Dict, Any
import sys
from dotenv import load_dotenv
from phi.agent import Agent
from phi.model.groq import Groq
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Data_Scraper_IR_Agent.DataScraperIR import collect_and_index, ir_search


# Load .env variables
load_dotenv()

# ---------------------------
# Groq/OpenAI LLM Configuration
# ---------------------------
market_research_agent = Agent(
    model=Groq(id="deepseek-r1-distill-llama-70b", api_key=os.getenv("GROQ_API_KEY")),
    markdown=False,
    instructions=(
        "You are a Market Researcher. You will receive documents related to a market topic. "
        "Summarize the current market condition with sections:\n"
        "- Demand\n- Prices/Costs\n- Projects/Policy\n- Risks\n- Outlook\n\n"
        "Respond STRICTLY in this JSON format:\n"
        "{\n"
        '  "summary": {\n'
        '    "demand": ["..."],\n'
        '    "prices_costs": ["..."],\n'
        '    "projects_policy": ["..."],\n'
        '    "risks": ["..."],\n'
        '    "outlook": ["..."]\n'
        "  }\n"
        "}"
    )
)

# ---------------------------
# Main Callable Function
# ---------------------------
def run_market_research(query: str, k_search: int = 10, k_index: int = 6, n_hits: int = 3) -> Dict[str, Any]:
    """
    Runs the Market Researcher agent:
    - Uses DataScraperIR to collect and index data
    - Retrieves top IR hits
    - Summarizes the current market condition
    Returns structured summary dict
    """
    # Step 1: Scrape and index documents
    collect_and_index(query, k_search=k_search, k_index=k_index)

    # Step 2: Retrieve relevant docs from Whoosh
    hits = ir_search(query, limit=n_hits)

    # Step 3: Load cached content
    doc_texts = []
    for h in hits:
        try:
            hsh = hashlib.sha256(h["url"].encode()).hexdigest()[:24]
            cache_path = f"storage/cache/{hsh}.json"
            with open(cache_path, "r", encoding="utf-8") as f:
                doc = json.load(f)
                doc_texts.append(f"### {doc['title']}\nURL: {doc['url']}\n\n{doc['content'][:2000]}")
        except Exception as e:
            continue

    if not doc_texts:
        return {"summary": {}, "error": "No usable documents retrieved"}

    # Step 4: Build LLM prompt
    prompt = f"""
Summarize the following documents related to the query:
"{query}"

Focus on current market conditions across:
- Demand
- Prices/Costs
- Projects/Policy
- Risks
- Outlook

Respond in JSON format:
{{
  "summary": {{
    "demand": ["..."],
    "prices_costs": ["..."],
    "projects_policy": ["..."],
    "risks": ["..."],
    "outlook": ["..."]
  }}
}}

Sources:
{chr(10).join(doc_texts)}
"""

    # Step 5: Run LLM
    response = market_research_agent.run(prompt)
    try:
        return json.loads(response.content)
    except Exception:
        return {"summary_raw": response.content, "error": "Failed to parse JSON"}


# ---------------------------
# CLI Entrypoint
# ---------------------------
def main() -> None:
    query = "Sri Lanka construction industry"
    result = run_market_research(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()